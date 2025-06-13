import bpy

def disable_decal_shadows():
    processed_objects = set()
    for obj in bpy.data.objects:
        if obj in processed_objects or obj.type != 'MESH':
            continue

        if obj.material_slots:
            for slot in obj.material_slots:
                if slot.material:
                    mat = slot.material
                    
                    if "disabledShadow" in mat:
                        print(f"Found material '{mat.name}' on object '{obj.name}'. Disabling shadow for this object.")
                    
                        obj.visible_shadow = False
                        obj.visible_diffuse = False
                        processed_objects.add(obj)
                        break 

    print("shadows on decals disabled!")


def disable_decal_shadows_by_name():
    for obj in bpy.context.scene.objects:
        if "PaintCrack" in obj.name:
            obj.visible_shadow = False
            obj.visible_diffuse = False

            print(f"Disabled shadows for object: {obj.name}")


import re
def remove_lights_by_name():
    print("-- Removing lights by name start --")

    # The pattern for 'gi'. It looks for 'gi' followed by a specific boundary.
    # r'' makes it a raw string, which is best practice for regex.
    # (?=...) is a "positive lookahead", which checks what comes next without
    # being part of the actual match.
    # [\s\.\d_] matches a whitespace, a literal dot, a digit, or an underscore.
    # |$ means OR the end of the string.
    gi_pattern = r'gi(?=[\s\.\d_]|$)'

    lights_to_remove = [
        obj for obj in bpy.data.objects
        if obj.type == 'LIGHT' and (
            'ambient' in obj.name.lower() or
            'volume' in obj.name.lower() or
            re.search(gi_pattern, obj.name.lower())
        )
    ]

    if not lights_to_remove:
        print("No lights found to remove.")
        print("-- Removing lights by name complete --")
        return

    for light in lights_to_remove:
        print(f"- Removing: {light.name}")
        bpy.data.objects.remove(light, do_unlink=True)

    print("-- Removing lights by name complete --")


def set_empty_max_viewport_size(max_size):
    for obj in bpy.context.scene.objects:
        if obj.type == 'EMPTY':
            obj.empty_display_size = max_size



def multiply_light_intensity(value):
    for obj in bpy.context.scene.objects:
        if obj.type == 'LIGHT':
            obj.data.energy *= value
            


def modify_emission_strength(material, factor):
    if material.use_nodes:
        modified = False
        # Get the material's node tree
        nodes = material.node_tree.nodes
        
        # Look for Principled BSDF node
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                if hasattr(node.inputs['Emission Strength'], 'default_value'):
                    # Get current emission strength
                    current_strength = node.inputs['Emission Strength'].default_value
                    # Multiply by factor
                    node.inputs['Emission Strength'].default_value = current_strength * factor
                    modified = True
                    print(f"Modified Principled BSDF emission in material: {material.name}")
        
        # If no Principled BSDF emission was found, look for Emission shader nodes
        if not modified:
            for node in nodes:
                if node.type == 'EMISSION':
                    # Get current emission strength
                    current_strength = node.inputs['Strength'].default_value
                    # Multiply by factor
                    node.inputs['Strength'].default_value = current_strength * factor
                    modified = True
                    print(f"Modified Emission node in material: {material.name}")
        
        if not modified:
            print(f"No emission nodes found in material: {material.name}")
    else:
        print(f"Material {material.name} doesn't use nodes")



def multiply_material_emission_intensity(factor):
    for material in bpy.data.materials:
        if material:
            modify_emission_strength(material, factor)

    print("\nEmission strength modification complete!")


disable_decal_shadows()
disable_decal_shadows_by_name()
set_empty_max_viewport_size(0.1)
#multiply_material_emission_intensity(100)
#multiply_light_intensity(1000)

remove_lights_by_name()
