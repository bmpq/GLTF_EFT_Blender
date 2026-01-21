import bpy
import os
import ast
import re

def sanitize_name(name):
    # Replace non-alphanumeric with _
    clean = re.sub(r'[^a-zA-Z0-9]', '_', name)
    return clean.lower()

def get_image_by_name(image_name):
    if image_name in bpy.data.images:
        return bpy.data.images[image_name]
    
    for img in bpy.data.images:
        if img.name == image_name:
            return img
    
    # (In case the image is loaded as "matress_DM(2)" but requested as "matress_DM_2_")
    target_sanitized = sanitize_name(image_name)
    for img in bpy.data.images:
        if sanitize_name(img.name) == target_sanitized:
            return img

    blend_path = bpy.path.abspath("//")
    extensions = ['.png', '.jpg', '.jpeg', '.tga', '.tif', '.tiff', '.webp'] 
    
    for ext in extensions:
        filename = image_name + ext
        filepath = os.path.join(blend_path, filename)
        if os.path.exists(filepath):
            try:
                return bpy.data.images.load(filepath)
            except:
                continue

    # 5. FUZZY FILE SEARCH (The Fix)
    # If we are here, exact file doesn't exist.
    # We list all files in the directory, sanitize their names, and compare.
    try:
        if not os.path.exists(blend_path):
            return None
            
        files_in_dir = os.listdir(blend_path)
        
        for f in files_in_dir:
            f_name, f_ext = os.path.splitext(f)
            
            if f_ext.lower() not in extensions:
                continue
            
            f_name_sanitized = sanitize_name(f_name)
            
            if f_name_sanitized == target_sanitized:
                filepath = os.path.join(blend_path, f)
                print(f"  [Fuzzy Match] Found '{f}' for requested '{image_name}'")
                try:
                    return bpy.data.images.load(filepath)
                except:
                    continue

    except Exception as e:
        print(f"  [Error] searching directory: {e}")

    return None

def process_materials():
    DEFAULT_SRGB_SLOTS = ['_MainTex', '_EmissionMap', '_Albedo', '_Aldebo', '_MainTex0', '_MainTex1', '_MainTex2']
    
    for mat in bpy.data.materials:
        if "shaderName" not in mat or "properties" not in mat:
            continue
        
        srgb_slots = DEFAULT_SRGB_SLOTS.copy()
        
        shader_name = mat["shaderName"]

        if shader_name == "MK4/Rock":
            srgb_slots.append('_MaskRGBA')
            srgb_slots.append('_Detail')
            
        print(f"Reconstructing: {mat.name} | Shader: {shader_name}")
        
        shader_name = mat["shaderName"]
        raw_properties = mat["properties"]

        if isinstance(raw_properties, str):
            try:
                properties = ast.literal_eval(raw_properties)
            except Exception as e:
                print(f"  Error parsing properties: {e}")
                continue
        else:
            properties = raw_properties.to_dict() if hasattr(raw_properties, "to_dict") else raw_properties

        if shader_name not in bpy.data.node_groups:
            print(f"  [Warning] Node Group '{shader_name}' missing.")
            continue
        
        node_group_data = bpy.data.node_groups[shader_name]

        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        output_node.location = (300, 0)

        group_node = nodes.new(type='ShaderNodeGroup')
        group_node.node_tree = node_group_data
        group_node.location = (0, 0)
        group_node.width = 250

        if group_node.outputs:
            links.new(group_node.outputs[0], output_node.inputs['Surface'])

        for prop_name, prop_data in properties.items():
            
            p_type = prop_data.get('type')
            p_val = prop_data.get('value')
            
            if prop_name in group_node.inputs:
                socket = group_node.inputs[prop_name]
                if p_type in ['Float', 'Range', 'Int'] and p_val is not None:
                    socket.default_value = float(p_val)
                elif p_type == 'Vector' and p_val is not None:
                    if socket.type == 'VECTOR': socket.default_value = p_val[:4]
                    else: socket.default_value = p_val
                elif p_type == 'Color' and p_val is not None:
                    socket.default_value = p_val

            # Textures
            if p_type == 'TexEnv':
                tex_name = prop_data.get('textureName')
                if tex_name:
                    image = get_image_by_name(tex_name)
                    if image:
                        image.alpha_mode = 'CHANNEL_PACKED'
                        
                        tex_node = nodes.new(type='ShaderNodeTexImage')
                        tex_node.image = image
                        tex_node.location = (-400, group_node.location.y - (len(nodes)*100))
                        
                        try:
                            if prop_name in srgb_slots:
                                image.colorspace_settings.name = 'sRGB'
                            else:
                                image.colorspace_settings.name = 'Non-Color'
                        except Exception as e:
                            print(f"  [Info] Could not set colorspace for {tex_name}: {e}")
                        
                        # Handle Tiling/Offset (not sure if correct yet)
                        tiling = prop_data.get('tiling', [1.0, 1.0])
                        offset = prop_data.get('offset', [0.0, 0.0])
                        
                        if tiling != [1.0, 1.0] or offset != [0.0, 0.0]:
                            mapping = nodes.new(type='ShaderNodeMapping')
                            mapping.location = (tex_node.location.x - 200, tex_node.location.y)
                            coord = nodes.new(type='ShaderNodeTexCoord')
                            coord.location = (mapping.location.x - 200, mapping.location.y)
                            
                            mapping.inputs['Scale'].default_value = (tiling[0], tiling[1], 1.0)
                            mapping.inputs['Location'].default_value = (offset[0], offset[1], 0.0)
                            links.new(coord.outputs['UV'], mapping.inputs['Vector'])
                            links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])

                        # Color texture output
                        if prop_name in group_node.inputs:
                            links.new(tex_node.outputs['Color'], group_node.inputs[prop_name])
                        
                        # Connect Alpha if a suffixed input exists in the group node
                        possible_alpha_names = [f"{prop_name}_A", f"{prop_name}_Alpha", f"{prop_name}_a", "Alpha", "A"]
                        
                        found_alpha = False
                        for a_name in possible_alpha_names:
                            if a_name in group_node.inputs:
                                links.new(tex_node.outputs['Alpha'], group_node.inputs[a_name])
                                found_alpha = True
                                break
                                
                    else:
                        print(f"  [Missing Texture] {tex_name}")

    print("Done.")

process_materials()