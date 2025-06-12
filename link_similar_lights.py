import bpy
import math

# --- Configuration ---
# Adjust this tolerance for comparing float values (color, energy, spot_size)
# Smaller value = stricter comparison
TOLERANCE = 0.01
# --- End Configuration ---

def compare_floats(f1, f2, tolerance):
    """Compares two floats within a given tolerance."""
    return abs(f1 - f2) <= tolerance

def are_lights_similar(data1, data2, tolerance):
    """
    Checks if two light data-blocks have similar properties.
    Properties compared: 'type', 'color', 'energy', 'spot_size' (if applicable).
    """
    if not data1 or not data2:
        return False

    # 1. Compare Type (must be exact)
    if data1.type != data2.type:
        return False

    # 2. Compare Energy
    if not compare_floats(data1.energy, data2.energy, tolerance):
        return False

    # 3. Compare Color (component-wise)
    for i in range(3): # Compare R, G, B
        if not compare_floats(data1.color[i], data2.color[i], tolerance):
            return False

    # 4. Compare Spot Size (only if both are SPOT lights)
    if data1.type == 'SPOT':
        # Ensure data2 is also SPOT (already checked by type comparison)
        if not compare_floats(data1.spot_size, data2.spot_size, tolerance):
            return False
    # Add elif blocks here for other type-specific properties if needed (e.g., AREA size)
    # elif data1.type == 'AREA':
        # compare area properties...
        # pass # Example

    # If all checks passed, the lights are similar
    return True

def link_similar_lights():
    """
    Iterates through scene lights and links objects with similar light data
    to use the same data-block.
    """
    print("-" * 40)
    print("Starting Light Linking Process...")

    scene = bpy.context.scene
    if not scene:
        print("Error: No active scene found.")
        return

    # Get all light objects in the current scene
    all_lights = [obj for obj in scene.objects if obj.type == 'LIGHT']

    if len(all_lights) < 2:
        print("Found less than 2 lights. No linking needed.")
        print("-" * 40)
        return

    print(f"Found {len(all_lights)} light objects to process.")

    # Store the data-blocks that represent unique light configurations
    representative_data_blocks = []
    linked_count = 0
    processed_count = 0

    for light_obj in all_lights:
        processed_count += 1
        current_data = light_obj.data
        if not current_data:
            print(f"Warning: Light object '{light_obj.name}' has no data-block. Skipping.")
            continue

        found_match = False
        # Compare current light's data with existing representatives
        for representative_data in representative_data_blocks:
            if are_lights_similar(current_data, representative_data, TOLERANCE):
                # Found a similar light data-block!
                # Check if it's not already linked
                if current_data != representative_data:
                    print(f"  Linking '{light_obj.name}' ({current_data.name}) -> uses data from '{representative_data.name}'")
                    # Link the object's data to the representative data-block
                    light_obj.data = representative_data
                    linked_count += 1
                # else:
                #     print(f"  '{light_obj.name}' already uses representative data '{representative_data.name}'")

                found_match = True
                break # No need to check other representatives for this light

        # If no match was found after checking all representatives,
        # this light's data becomes a new representative
        if not found_match:
            # Check if this exact data block is already a representative (can happen if script run multiple times)
            is_already_representative = any(current_data == rep_data for rep_data in representative_data_blocks)
            if not is_already_representative:
                 print(f"-> '{light_obj.name}' uses unique data '{current_data.name}'. Adding as representative.")
                 representative_data_blocks.append(current_data)
            # else: already covered by the check inside the loop

    print("-" * 40)
    print("Light Linking Summary:")
    print(f"  Processed {processed_count} light objects.")
    print(f"  Linked {linked_count} objects to existing data-blocks.")
    print(f"  Found {len(representative_data_blocks)} unique light configurations.")
    print("-" * 40)

# --- Run the main function ---
if __name__ == "__main__":
    link_similar_lights()