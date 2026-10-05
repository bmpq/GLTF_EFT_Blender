import bpy
import math
from mathutils import Vector

def sync_sun_to_sky_texture():
    # 1. Validate selected object
    obj = bpy.context.active_object
    if not obj or obj not in bpy.context.selected_objects:
        raise RuntimeError("No object selected. Please select a Sun light.")

    if obj.type != 'LIGHT' or obj.data.type != 'SUN':
        raise TypeError(f"Selected object '{obj.name}' is not a light or not of type 'SUN'.")

    # 2. Validate World and Sky Texture node
    if "World" not in bpy.data.worlds:
        raise KeyError("World named 'World' does not exist.")

    world = bpy.data.worlds["World"]
    if not world.use_nodes or not world.node_tree:
        raise ValueError("World 'World' does not use nodes.")

    if "Sky Texture" not in world.node_tree.nodes:
        raise KeyError("World node tree does not have a node named 'Sky Texture'.")

    sky_node = world.node_tree.nodes["Sky Texture"]

    # Warn if a Mapping node is connected to the Sky Texture Vector input
    vector_socket = sky_node.inputs.get("Vector")
    if vector_socket and vector_socket.is_linked:
        print("Warning: 'Sky Texture' has an input connected to its Vector socket. "
              "Any rotation on that node will offset the sky.")

    # 3. Sun vector in world space (source is along the light's local +Z axis)
    sun_vector = (obj.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()

    # 4. Elevation (-pi/2 to pi/2)
    elevation = math.asin(max(-1.0, min(1.0, sun_vector.z)))

    # 5. Rotation: Standard compass azimuth (0 = North/+Y, pi/2 = East/+X)
    rotation = math.atan2(sun_vector.x, sun_vector.y) % (2.0 * math.pi)

    # 6. Apply to Sky Texture
    sky_node.sun_elevation = elevation
    sky_node.sun_rotation = rotation

    print(f"Synced successfully -> Elevation: {math.degrees(elevation):.2f}°, Rotation: {math.degrees(rotation):.2f}°")

sync_sun_to_sky_texture()