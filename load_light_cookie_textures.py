import bpy
import os

def load_cookie_textures():
    """
    Finds all lights in the scene with a 'cookieTexName' custom property.
    The property should contain the filename WITHOUT the extension.
    The script searches for the file in the same directory as the .blend file,
    trying common image extensions, and then sets up the light's shader nodes
    to use it as a cookie texture (gobos).
    """
    # Get the directory of the current .blend file
    blend_file_dir = bpy.path.abspath("//")

    # Check if the file has been saved.
    if not blend_file_dir:
        print("Error: Please save your .blend file first. Cannot determine texture path.")
        bpy.context.window_manager.popup_menu(
            lambda self, context: self.layout.label(text="Please save the .blend file first!"),
            title="Error",
            icon='ERROR'
        )
        return

    # Define the image extensions to search for, in order of preference
    supported_extensions = (".png", ".webp", ".jpeg", ".jpg")
    print(f"Searching for textures in: {blend_file_dir}")
    setup_count = 0

    # Iterate through all objects in the active scene
    for obj in bpy.context.scene.objects:
        # Check if the object is a light and has the custom property
        if obj.type == 'LIGHT' and "cookieTexName" in obj.data:
            light_data = obj.data
            base_texture_name = light_data["cookieTexName"]
            
            # --- Search for the texture file with different extensions ---
            texture_filepath = None
            for ext in supported_extensions:
                potential_filename = base_texture_name + ext
                potential_filepath = os.path.join(blend_file_dir, potential_filename)
                
                if os.path.exists(potential_filepath):
                    texture_filepath = potential_filepath
                    print(f"Found match for '{base_texture_name}': {potential_filename}")
                    break # Found the file, stop searching for other extensions

            # --- Check if a texture file was found ---
            if not texture_filepath:
                print(f"Warning: Texture file not found for light '{obj.name}'. "
                      f"Searched for base name '{base_texture_name}' "
                      f"with extensions {supported_extensions}")
                continue # Skip to the next light

            # --- Node Setup ---
            light_data.use_nodes = True
            node_tree = light_data.node_tree
            nodes = node_tree.nodes
            links = node_tree.links

            nodes.clear()

            output_node = nodes.new(type='ShaderNodeOutputLight')
            emission_node = nodes.new(type='ShaderNodeEmission')
            image_tex_node = nodes.new(type='ShaderNodeTexImage')
            coord_node = nodes.new(type='ShaderNodeTexCoord')
            mapping_node = nodes.new(type='ShaderNodeMapping')

            coord_node.location = (-600, 0)
            mapping_node.location = (-400, 0)
            image_tex_node.location = (-200, 0)
            emission_node.location = (100, 0)
            output_node.location = (300, 0)

            # Load the found image into the image texture node
            image_tex_node.image = bpy.data.images.load(texture_filepath, check_existing=True)
            
            # Link nodes: Normal output projects from the light's direction
            links.new(coord_node.outputs['Normal'], mapping_node.inputs['Vector'])
            links.new(mapping_node.outputs['Vector'], image_tex_node.inputs['Vector'])
            links.new(image_tex_node.outputs['Alpha'], emission_node.inputs['Strength'])
            links.new(emission_node.outputs['Emission'], output_node.inputs['Surface'])
            
            print(f"Successfully set up cookie texture for light '{obj.name}'")
            setup_count += 1
            
    if setup_count > 0:
        print(f"\nFinished. Set up {setup_count} light(s).")
    else:
        print("\nFinished. No lights with a valid 'cookieTexName' property were found.")


# --- Run the function ---
if __name__ == "__main__":
    load_cookie_textures()