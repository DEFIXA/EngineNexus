"""Blender background worker: procedural scaffold, UVs, LODs, export, technical QC.

This is an intentionally limited demonstrator, NOT an artist-quality dragon sculpt.
Run inside Blender only: blender --background --python blender_worker.py -- spec.json output/
"""
import bpy
import bmesh
import json
import math
import random
import sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dragon_geometry import make_leg as make_anatomical_leg, make_full_dragon


def material(name, rgba):
    m = bpy.data.materials.new(name)
    m.diffuse_color = rgba
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = 0.85
    return m


def tube(name, points, radii, mat, resolution=7):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 8
    curve.bevel_depth = 1
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for p, pos, radius in zip(spline.bezier_points, points, radii):
        p.co = pos
        p.handle_left_type = "AUTO"
        p.handle_right_type = "AUTO"
        p.radius = max(0.002, radius)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj.select_set(False)
    return bpy.context.view_layer.objects.active


def make_tree(seed):
    rng = random.Random(seed)
    bark = material("M_Bark_Gray", (0.24, 0.22, 0.20, 1))
    root = (0, 0, 0)
    trunk = [
        root, (0.15, 0.05, 0.7), (-0.12, 0.13, 1.65),
        (0.28, -0.12, 2.8), (-0.12, 0.1, 4.0),
        (0.15, 0.02, 5.0), (0.4, 0.12, 5.9),
    ]
    pieces = [tube("Trunk", trunk, [0.62, 0.56, 0.48, 0.36, 0.25, 0.16, 0.035], bark)]
    for i in range(13):
        z = rng.uniform(1.7, 5.3)
        angle = i * 2.39996
        reach = rng.uniform(1.1, 3.1)
        origin = (0.12 * math.sin(z), 0, z)
        path = [
            origin,
            (origin[0] + reach * 0.32 * math.cos(angle),
             reach * 0.32 * math.sin(angle), z + rng.uniform(0.3, 0.8)),
            (origin[0] + reach * 0.72 * math.cos(angle),
             reach * 0.72 * math.sin(angle), z + rng.uniform(0.8, 1.5)),
            (origin[0] + reach * math.cos(angle),
             reach * math.sin(angle), z + rng.uniform(1.0, 2.1)),
        ]
        pieces.append(tube(f"Branch_{i:02d}", path,
                           [rng.uniform(0.16, 0.26), 0.13, 0.065, 0.008], bark))
        for j in range(2):
            t = path[2]
            end = (t[0] + rng.uniform(-0.7, 0.7),
                   t[1] + rng.uniform(-0.7, 0.7),
                   t[2] + rng.uniform(0.4, 1.1))
            pieces.append(tube(f"Twig_{i}_{j}", [t, end], [0.07, 0.006], bark))
    for i in range(6):
        a = i * math.tau / 6
        pieces.append(tube(f"Root_{i}", [(0, 0, 0.5),
            (0.4 * math.cos(a), 0.4 * math.sin(a), 0.13),
            (1.2 * math.cos(a), 1.2 * math.sin(a), 0.02)],
            [0.3, 0.17, 0.015], bark))
    return pieces


def make_leg(seed):
    """Static anatomy scaffold; NO claims of deformation-ready edge loops."""
    skin = material("M_Dragon_Skin", (0.25, 0.26, 0.27, 1))
    keratin = material("M_Keratin", (0.12, 0.12, 0.13, 1))
    parts = []
    # The path bends backwards at the hock, giving a digitigrade silhouette.
    parts.append(tube("Leg_Muscle_Master", [
        (0, 0, 3.1), (0.22, 0, 2.7), (0.55, 0, 2.1),
        (0.18, 0, 1.45), (-0.18, 0, 0.75), (0.25, 0, 0.30)
    ], [0.48, 0.47, 0.36, 0.24, 0.14, 0.16], skin))
    for i, y in enumerate((-0.28, -0.09, 0.12, 0.32)):
        x = 0.27 + (i - 1.5) * 0.08
        toe = [(x, y, 0.31), (x + 0.28, y * 1.1, 0.15),
               (x + 0.48, y * 1.2, 0.12)]
        parts.append(tube(f"Toe_{i}", toe, [0.12, 0.095, 0.025], skin))
        tip = (x + 0.70 + i * 0.03, y * 1.23, 0.04)
        parts.append(tube(f"Claw_{i}", [toe[-1], tip], [0.08, 0.004], keratin))
    rng = random.Random(seed)
    for i in range(14):
        z = 0.7 + i * 0.15
        x = 0.17 + 0.13 * math.sin(i * 0.6)
        y = rng.choice([-0.22, 0.22])
        parts.append(tube(f"Scute_{i}", [(x, y, z),
            (x + rng.uniform(-0.1, 0.1), y * 1.4, z + 0.13)],
            [0.09, 0.005], keratin))
    return parts


def box_piece(name, location, dimensions, mat, rotation_y=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    obj.rotation_euler.y = rotation_y
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def make_structure(spec):
    """Simple modular house scaffold with a real door opening, not a final building."""
    extra = spec.get("extra", {})
    width = max(3.0, min(30.0, float(extra.get("width_m", 6.0))))
    depth = max(3.0, min(30.0, float(extra.get("depth_m", 4.0))))
    height = max(2.5, min(20.0, float(extra.get("height_m", 3.2))))
    thick = 0.24
    door_w, door_h = 1.25, 2.2
    stone = material("M_Stone_Plaster", (0.43, 0.42, 0.39, 1))
    timber = material("M_Timber", (0.18, 0.12, 0.08, 1))
    slate = material("M_Slate_Roof", (0.11, 0.12, 0.14, 1))
    parts = [box_piece("Floor", (0, 0, -0.12), (width, depth, 0.24), stone)]
    side_w = (width - door_w) / 2
    parts.append(box_piece("Front_Left", (-(door_w + side_w)/2, -depth/2, height/2),
                           (side_w, thick, height), stone))
    parts.append(box_piece("Front_Right", ((door_w + side_w)/2, -depth/2, height/2),
                           (side_w, thick, height), stone))
    parts.append(box_piece("Front_Lintel", (0, -depth/2, (height + door_h)/2),
                           (door_w, thick, height - door_h), stone))
    parts.append(box_piece("Back", (0, depth/2, height/2),
                           (width, thick, height), stone))
    for x, side in ((-width/2, "Left"), (width/2, "Right")):
        # Side window void: lower wall, upper wall and left/right piers.
        win_w, win_h, sill = 1.2, 0.95, 1.05
        parts.append(box_piece(side+"_Sill", (x, 0, sill/2),
                               (thick, win_w, sill), stone))
        parts.append(box_piece(side+"_Top", (x, 0, (height+sill+win_h)/2),
                               (thick, win_w, height-sill-win_h), stone))
        pier_d = (depth-win_w)/2
        for sign in (-1, 1):
            y = sign*(win_w+ pier_d)/2
            parts.append(box_piece(side+f"_Pier_{sign}", (x, y, height/2),
                                   (thick, pier_d, height), stone))
    pitch = math.radians(25)
    rise = (width/4) * math.tan(pitch)
    for sign in (-1, 1):
        parts.append(box_piece("Roof_"+str(sign),
            (sign*width/4, 0, height+rise/2),
            (width/2+0.6, depth+0.8, 0.18), slate,
            rotation_y=-sign*pitch))
    for sign in (-1, 1):
        parts.append(box_piece("Door_Frame_"+str(sign),
            (sign*door_w/2, -depth/2-0.12, door_h/2),
            (0.13, 0.18, door_h), timber))
    return parts


def make_rock(seed):
    rng = random.Random(seed)
    stone = material("M_Rock", (0.32, 0.33, 0.34, 1))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0)
    obj = bpy.context.object
    obj.name = "Rock_Source"
    for v in obj.data.vertices:
        p = v.co
        wobble = (1.0 + 0.13*math.sin(4*p.x+2*p.y) +
                  0.10*math.cos(5*p.z-p.x) + rng.uniform(-0.07, 0.07))
        p.x *= 1.65*wobble
        p.y *= 1.1*wobble
        p.z *= 0.85*wobble
    obj.data.materials.append(stone)
    return [obj]


def make_terrain(seed):
    """Open grid terrain. Boundary edges are expected and audited separately."""
    rng = random.Random(seed)
    ground = material("M_Ground", (0.28, 0.27, 0.22, 1))
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=64, y_subdivisions=64, size=12)
    obj = bpy.context.object
    obj.name = "Terrain_Source"
    for v in obj.data.vertices:
        x, y = v.co.x, v.co.y
        v.co.z = (0.55*math.sin(x*0.47)*math.cos(y*0.42) +
                  0.18*math.sin(x*1.23+y*0.61) + rng.uniform(-0.045, 0.045))
    obj.data.materials.append(ground)
    return [obj]


def join_meshes(parts, name):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in parts:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    return obj


def apply_voxel_remesh(obj, voxel_size=0.06):
    """Fuses overlapping pieces for static scaffold; destroys deformation topology."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new("Fuse_Organic_Forms", "REMESH")
    mod.mode = "VOXEL"
    mod.voxel_size = voxel_size
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def add_uv(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")


def triangles(obj):
    return sum(len(poly.vertices) - 2 for poly in obj.data.polygons)


def reduce_to_budget(obj, target):
    before = triangles(obj)
    if before <= target:
        return before, before
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new("Runtime_Triangle_Budget", "DECIMATE")
    mod.ratio = max(0.001, min(1.0, 0.97 * target / before))
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return before, triangles(obj)


def make_collision(obj, category):
    if category not in {"tree", "root", "foliage"}:
        return None
    # Intentionally simple trunk-only physics; branch collisions need game design review.
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.62,
                                        depth=5.8, location=(0, 0, 2.9))
    collision = bpy.context.object
    collision.name = f"UCX_{obj.name}_00"
    collision.hide_render = True
    return collision


def make_lods(obj, count):
    results = []
    for index in range(1, count + 1):
        lod = obj.copy()
        lod.data = obj.data.copy()
        bpy.context.collection.objects.link(lod)
        lod.name = f"{obj.name}_LOD{index}"
        lod.hide_render = True
        mod = lod.modifiers.new("LOD_Decimate", "DECIMATE")
        mod.ratio = max(0.07, 0.55 ** index)
        bpy.context.view_layer.objects.active = lod
        bpy.ops.object.modifier_apply(modifier=mod.name)
        results.append(lod)
    return results


def mesh_components(obj):
    """Count connected mesh islands, including floating debris."""
    mesh = obj.data
    parent = list(range(len(mesh.vertices)))
    sizes = [1] * len(parent)

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for edge in mesh.edges:
        a, b = find(edge.vertices[0]), find(edge.vertices[1])
        if a != b:
            if sizes[a] < sizes[b]:
                a, b = b, a
            parent[b] = a
            sizes[a] += sizes[b]
    counts = {}
    for poly in mesh.polygons:
        root = find(poly.vertices[0])
        counts[root] = counts.get(root, 0) + max(1, len(poly.vertices) - 2)
    total = sum(counts.values())
    return len(counts), max(counts.values(), default=0) / max(1, total), sorted(counts.values(), reverse=True)[:20]


def prune_micro_islands(obj, *, max_fraction=0.005, total_limit=0.015):
    """Remove only isolated tiny artifacts; never discard a major anatomical part."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    unseen = set(bm.verts)
    groups = []
    while unseen:
        seed = unseen.pop()
        stack = [seed]
        group = [seed]
        while stack:
            v = stack.pop()
            for e in v.link_edges:
                other = e.other_vert(v)
                if other in unseen:
                    unseen.remove(other)
                    stack.append(other)
                    group.append(other)
        groups.append(group)
    if len(groups) <= 1:
        bm.free()
        return 0, 0
    counts = [(len({f for v in group for f in v.link_faces}), group)
              for group in groups]
    total = sum(n for n, _ in counts)
    biggest = max(counts, key=lambda pair: pair[0])[1]
    tiny = [(n, group) for n, group in counts
            if group is not biggest and n / max(1, total) < max_fraction]
    discarded = sum(n for n, _ in tiny)
    if discarded / max(1, total) > total_limit:
        bm.free()
        return 0, 0
    for n, group in tiny:
        bmesh.ops.delete(bm, geom=group, context="VERTS")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return len(tiny), discarded


def audit(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    loose = sum(1 for v in bm.verts if not v.link_edges)
    nonmanifold = sum(1 for e in bm.edges if not e.is_manifold)
    boundary = sum(1 for e in bm.edges if e.is_boundary)
    bm.free()
    components, fraction, island_sizes = mesh_components(obj)
    return {"name": obj.name, "triangles": triangles(obj),
            "connected_components": components,
            "largest_component_triangle_fraction": round(fraction, 6),
            "component_triangle_sizes": island_sizes,
            "loose_vertices": loose, "non_manifold_edges": nonmanifold,
            "boundary_edges": boundary,
            "has_uv": bool(obj.data.uv_layers),
            "negative_scale": any(v < 0 for v in obj.scale)}


def export_mesh(obj, lods, collision, output):
    """GLB always. FBX only when Blender exposes a complete compatible exporter."""
    warnings = []
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(output / "asset.glb"),
                              export_format="GLB", use_selection=True)
    if collision is not None:
        bpy.ops.object.select_all(action="DESELECT")
        collision.select_set(True)
        bpy.context.view_layer.objects.active = collision
        bpy.ops.export_scene.gltf(filepath=str(output / "collision.glb"),
                                  export_format="GLB", use_selection=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    if collision is not None:
        collision.select_set(True)
    bpy.context.view_layer.objects.active = obj

    fbx_props = {p.identifier for p in bpy.ops.export_scene.fbx.get_rna_type().properties}
    selection_key = next((key for key in
        ("use_selection", "export_selected_objects", "selected_only")
        if key in fbx_props), None)
    if selection_key and "use_space_transform" in fbx_props:
        options = {"filepath": str(output / "asset.fbx"), selection_key: True}
        optional = {"object_types": {"MESH"}, "apply_unit_scale": True,
                    "bake_anim": False, "add_leaf_bones": False}
        options.update({key: value for key, value in optional.items()
                        if key in fbx_props})
        try:
            bpy.ops.export_scene.fbx(**options)
        except Exception as exc:
            warnings.append(f"FBX exporter failed: {type(exc).__name__}; use GLB")
    else:
        # Ubuntu's Blender 5.0.1 packaged FBX addon exposes only four operator
        # properties and crashes with missing use_space_transform. Do not call it.
        warnings.append("FBX exporter incomplete in this Blender build; use GLB")
    for index, lod in enumerate(lods, start=1):
        bpy.ops.object.select_all(action="DESELECT")
        lod.select_set(True)
        bpy.context.view_layer.objects.active = lod
        bpy.ops.export_scene.gltf(filepath=str(output / f"lod{index}.glb"),
                                  export_format="GLB", use_selection=True)
    return warnings


def render_reference_views(obj, output):
    """Create GPU-free, depth-sorted SVG technical previews in headless Blender.

    Painter sorting is approximate and not a substitute for proper reference renders.
    Avoids EGL/OpenGL crashes on headless CI runners.
    """
    from mathutils import Vector
    preview = obj.copy()
    preview.data = obj.data.copy()
    bpy.context.collection.objects.link(preview)
    preview.name = "QC_TEMP"
    # Keep the SVG small enough to inspect and store.
    face_count = max(1, triangles(preview))
    if face_count > 6000:
        bpy.ops.object.select_all(action="DESELECT")
        preview.select_set(True)
        bpy.context.view_layer.objects.active = preview
        mod = preview.modifiers.new("QC_Simplify", "DECIMATE")
        mod.ratio = max(0.005, 6000 / face_count)
        bpy.ops.object.modifier_apply(modifier=mod.name)

    verts = [preview.matrix_world @ v.co for v in preview.data.vertices]
    center = sum(verts, Vector((0.0, 0.0, 0.0))) / max(1, len(verts))
    span = max(float(v) for v in obj.dimensions)
    span = max(span, 1.0)
    views = {
        "front": Vector((0.0, -1.0, 0.25)),
        "side": Vector((1.0, 0.0, 0.25)),
        "three_quarter": Vector((1.0, -1.0, 0.45)),
    }
    light = Vector((0.5, -0.4, 1.0)).normalized()
    for name, direction in views.items():
        forward = direction.normalized()
        right = forward.cross(Vector((0.0, 0.0, 1.0))).normalized()
        up = right.cross(forward).normalized()
        faces = []
        for poly in preview.data.polygons:
            pts = [verts[i] for i in poly.vertices]
            if len(pts) < 3:
                continue
            coords = []
            for point in pts:
                v = point - center
                x = 256 + 410 * v.dot(right) / span
                y = 256 - 410 * v.dot(up) / span
                coords.append((x, y))
            normal = (pts[1] - pts[0]).cross(pts[2] - pts[0])
            if normal.length_squared > 0:
                normal.normalize()
            shade = int(135 + 95 * abs(normal.dot(light)))
            shade = max(50, min(245, shade))
            depth = sum((point - center).dot(forward) for point in pts) / len(pts)
            coords_str = " ".join(f"{x:.2f},{y:.2f}" for x, y in coords)
            faces.append((depth, f'<polygon points="{coords_str}" fill="rgb({shade},{shade},{shade})" stroke="#505050" stroke-width="0.22"/>'))
        faces.sort(key=lambda pair: pair[0])
        svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">',
               '<rect width="512" height="512" fill="#f0f0f0"/>',
               '<g stroke-linejoin="round">']
        svg.extend(shape for _, shape in faces)
        svg.extend(['</g>', '</svg>'])
        (output / f"qc_{name}.svg").write_text("\n".join(svg), encoding="utf-8")
    bpy.data.objects.remove(preview, do_unlink=True)



def render_clay_png(obj, output, *, resolution=640, full_creature=False):
    """Real Cycles CPU PNG renders of LOD0 geometry for manual reference review."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 12
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (0.10, 0.10, 0.10)
    clay = bpy.data.materials.new("QC_Clay")
    clay.diffuse_color = (0.55, 0.55, 0.55, 1.0)
    clay.use_nodes = True
    shader = clay.node_tree.nodes.get("Principled BSDF")
    if shader:
        shader.inputs["Base Color"].default_value = (0.52, 0.52, 0.52, 1)
        shader.inputs["Roughness"].default_value = 0.85
    bpy.context.view_layer.material_override = clay
    camera_data = bpy.data.cameras.new("QC_Camera")
    camera = bpy.data.objects.new("QC_Camera", camera_data)
    scene.collection.objects.link(camera)
    camera_data.type = "ORTHO"
    scene.camera = camera
    from mathutils import Vector
    center = sum((obj.matrix_world @ Vector(c) for c in obj.bound_box), Vector()) / 8.0
    span = max(0.2, *[float(x) for x in obj.dimensions])
    camera_data.ortho_scale = span * 1.35
    light_data = bpy.data.lights.new("QC_Key", type="AREA")
    light = bpy.data.objects.new("QC_Key", light_data)
    scene.collection.objects.link(light)
    light_data.energy = 1200 * max(1.0, (span / 3.0) ** 2)
    light_data.shape = "DISK"
    light_data.size = span * 1.8
    light.location = center + Vector((span * 0.8, -span, span * 1.5))
    light.rotation_euler = (center - light.location).to_track_quat("-Z", "Y").to_euler()
    views = {"front": Vector((0, -1, 0.18)),
             "side": Vector((1, 0, 0.18)),
             "three_quarter": Vector((1, -1, 0.4))}
    files = []
    for name, direction in views.items():
        camera.location = center + direction.normalized() * span * 2.6
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        path = output / ("clay_" + name + ".png")
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        if not path.is_file() or path.stat().st_size < 1000:
            raise RuntimeError("Blender failed to render " + str(path))
        files.append(path.name)
    if full_creature:
        closeups = {
            "head": (Vector((3.4, 0.0, 3.0)), Vector((0.5, -1.0, 0.18)), 2.6),
            "wings": (Vector((-0.5, 0.0, 3.0)), Vector((0.0, -0.20, 1.0)), 11.0),
        }
        for name, (focus, direction, scale) in closeups.items():
            camera_data.ortho_scale = scale
            camera.location = focus + direction.normalized() * scale * 2.6
            camera.rotation_euler = (focus - camera.location).to_track_quat("-Z", "Y").to_euler()
            path = output / ("clay_" + name + ".png")
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            if not path.is_file() or path.stat().st_size < 1000:
                raise RuntimeError("Blender failed to render " + str(path))
            files.append(path.name)
    bpy.context.view_layer.material_override = None
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.objects.remove(light, do_unlink=True)
    return files


def main():
    if "--" not in sys.argv:
        raise RuntimeError("Expected -- spec.json output_dir")
    args = sys.argv[sys.argv.index("--") + 1:]
    spec = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    output = Path(args[1]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    category = spec["category"]
    name = ("MASTER_" if spec["animated"] else "SM_") + spec["asset_id"]
    source_glb = spec.get("extra", {}).get("source_glb")
    if source_glb:
        if spec["animated"]:
            raise ValueError("Animated GLB needs rig-aware retopology; do not flatten its skeleton")
        source = Path(source_glb)
        if not source.is_absolute():
            source = (Path(args[0]).resolve().parent / source).resolve()
        if source.suffix.lower() != ".glb":
            raise ValueError("Source must be a GLB file")
        bpy.ops.import_scene.gltf(filepath=str(source))
        parts = [x for x in bpy.context.scene.objects if x.type == "MESH"]
        if not parts:
            raise ValueError("Imported GLB contains no mesh")
    elif category in {"tree", "root", "foliage"}:
        parts = make_tree(spec["seed"])
    elif category in {"creature", "animal"} and "dragon" in spec["prompt"].lower() and ("full" in spec["prompt"].lower() or spec.get("extra", {}).get("full_creature")):
        parts = make_full_dragon(spec["seed"])
    elif category in {"creature", "animal"} and "leg" in spec["prompt"].lower():
        parts = make_anatomical_leg(spec["seed"])
    elif category == "structure":
        parts = make_structure(spec)
    elif category == "rock":
        parts = make_rock(spec["seed"])
    elif category == "terrain":
        parts = make_terrain(spec["seed"])
    else:
        raise ValueError(f"No built-in geometry builder for category {category}; supply extra.source_glb or a backend")
    obj = join_meshes(parts, name)
    # Keep an unmodified high-poly source in the .blend for future artistic work.
    master = obj.copy()
    master.data = obj.data.copy()
    bpy.context.collection.objects.link(master)
    master.name = "SOURCE_HIGH_" + spec["asset_id"]
    master.hide_render = True
    master.hide_set(True)
    if source_glb or category in {"tree", "root", "foliage", "creature", "animal"}:
        voxel = 0.052 if spec.get("extra", {}).get("full_creature") else (0.055 if category == "tree" else 0.035)
        apply_voxel_remesh(obj, voxel_size=voxel)
    pruned_count, pruned_faces = (prune_micro_islands(obj) if category in {"creature", "animal"} else (0, 0))
    add_uv(obj)
    original_triangles, optimized_triangles = reduce_to_budget(obj, spec["target_triangles"])
    lods = make_lods(obj, spec["max_lod_count"] if not spec["animated"] else 0)
    collision = make_collision(obj, category) if not spec["animated"] else None
    report = {
        "asset_id": spec["asset_id"],
        "blender_version": bpy.app.version_string,
        "target_engine": spec.get("target_engine", "UE5"),
        "target_platform": spec.get("platform", "pc"),
        "bounding_dimensions_m": [round(float(v), 4) for v in obj.dimensions],
        "objects": [audit(obj)],
        "runtime_triangles": triangles(obj),
        "pruned_micro_islands": pruned_count,
        "pruned_micro_faces": pruned_faces,
        "triangles_before_budget_optimization": original_triangles,
        "lods": [{"name": x.name, "triangles": triangles(x)} for x in lods],
        "collision_object": collision.name if collision else None,
        "errors": [],
        "warnings": [
            "Procedural/imported candidate, not reference-validated",
            "Automatic remesh is not deformation topology",
            "No high-to-low texture bake or UE profiling performed",
            "UCX collision is only supplied for tree-like assets; verify gameplay fit",
            "Structures/rocks/terrain require collision setup in Unreal",
            "LODs are exported separately and require Unreal LOD assignment",
        ],
    }
    report["warnings"].extend(export_mesh(obj, lods, collision, output))
    render_reference_views(obj, output)
    if category in {"creature", "animal"}:
        report["clay_render_files"] = render_clay_png(obj, output,
            full_creature=bool(spec.get("extra", {}).get("full_creature")) )
    print("GEOMETRY_QC " + json.dumps({"asset_id": spec["asset_id"],
        "triangles": report["runtime_triangles"],
        "components": report["objects"][0]["component_triangle_sizes"],
        "pruned_islands": pruned_count, "pruned_faces": pruned_faces}))
    (output / "qc.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "master.blend"))


if __name__ == "__main__":
    main()
