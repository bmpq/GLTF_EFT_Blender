import bpy

import bpy

def _disable_shadows_for_object(obj, reason):
    if not (obj.visible_shadow or obj.visible_diffuse):
        return

    print(
        f"Disabling shadow and indirect contribution for '{obj.name}' "
        f"({reason})."
    )
    obj.visible_shadow = False
    obj.visible_diffuse = False


def disable_shadows_by_material_property(prop_name="disabledShadow"):
    for obj in bpy.data.objects:
        if not obj.material_slots:
            continue

        all_materials_have_prop = all(
            slot.material and prop_name in slot.material
            for slot in obj.material_slots
        )

        if all_materials_have_prop:
            reason = f"all materials on {obj.name} have the '{prop_name}' property"
            _disable_shadows_for_object(obj, reason)


def disable_shadows_by_object_name(name_substring="PaintCrack"):
    for obj in bpy.context.scene.objects:
        if name_substring in obj.name:
            reason = f"name contains '{name_substring}'"
            _disable_shadows_for_object(obj, reason)


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
            



def find_brightest_light():
    brightest_light_object = None
    max_power = -1.0

    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            light_data = obj.data
            if light_data.energy > max_power:
                max_power = light_data.energy
                brightest_light_object = obj

    return brightest_light_object


def multiply_light_intensity(value):
    modified = set()
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            if obj.data in modified:
                continue

            obj.data.energy *= value
            modified.add(obj.data)



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


disable_shadows_by_material_property()
disable_shadows_by_object_name("PaintCrack")
set_empty_max_viewport_size(0.1)

remove_lights_by_name()




brightest_light = find_brightest_light()
if brightest_light:
    power_value = brightest_light.data.energy
    if power_value < 30: # means light multiplication hasn't been run yet
        multiply_material_emission_intensity(50)
        multiply_light_intensity(50)
    else:
        print('Light intensity multiplication has already been done!')
        
        
        
def delete_empty_objects_without_children():
    bpy.ops.object.select_all(action='DESELECT')
    
    parents = set()
    for obj in bpy.data.objects:
        if obj.parent is not None:
            parents.add(obj.parent)

    empties_to_delete = []
    for obj in bpy.data.objects:
        if obj.type == 'EMPTY' and obj not in parents:
            empties_to_delete.append(obj)

    with bpy.context.temp_override():
        for obj in empties_to_delete:
            print(f"selecting {obj}")
            obj.select_set(True)
        print(f"BIG delete...")
        bpy.ops.object.delete()
        print(f"Iteration deleted {len(empties_to_delete)} objects!")
        return len(empties_to_delete)

limit = 16
amount_deleted = 999
while amount_deleted > 0 and limit > 0:
    amount_deleted = delete_empty_objects_without_children()
    limit -= 1