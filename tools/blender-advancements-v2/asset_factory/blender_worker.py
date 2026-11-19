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


def audit(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    loose = sum(1 for v in bm.verts if not v.link_edges)
    nonmanifold = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()
    return {"name": obj.name, "triangles": triangles(obj),
            "loose_vertices": loose, "non_manifold_edges": nonmanifold,
            "has_uv": bool(obj.data.uv_layers),
            "negative_scale": any(v < 0 for v in obj.scale)}


def export_mesh(obj, lods, collision, output):
    # Main GLB contains only the visible runtime mesh.
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(output / "asset.glb"),
                              export_format="GLB", use_selection=True)
    # UE FBX contains main mesh plus a UCX collision primitive when available.
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    if collision is not None:
        collision.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(filepath=str(output / "asset.fbx"),
                             use_selection=True, object_types={"MESH"},
                             apply_unit_scale=True, bake_anim=False,
                             add_leaf_bones=False)
    for index, lod in enumerate(lods, start=1):
        bpy.ops.object.select_all(action="DESELECT")
        lod.select_set(True)
        bpy.context.view_layer.objects.active = lod
        bpy.ops.export_scene.gltf(filepath=str(output / f"lod{index}.glb"),
                                  export_format="GLB", use_selection=True)


def render_reference_views(obj, output):
    """Fixed orthographic technical previews, not a reference-similarity score."""
    from mathutils import Vector
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    camera_data = bpy.data.cameras.new("QC_Ortho")
    camera = bpy.data.objects.new("QC_Ortho", camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = "ORTHO"
    dims = obj.dimensions
    span = max(dims.x, dims.y, dims.z, 1.0)
    camera_data.ortho_scale = span * 1.65
    center = obj.matrix_world @ Vector((0.0, 0.0, 0.0))
    # Use evaluated world-space bounds for a robust camera target.
    center = sum((obj.matrix_world @ Vector(c) for c in obj.bound_box), Vector()) / 8.0
    directions = {
        "front": Vector((0.0, -1.0, 0.25)),
        "side": Vector((1.0, 0.0, 0.25)),
        "three_quarter": Vector((1.0, -1.0, 0.45)),
    }
    for name, direction in directions.items():
        camera.location = center + direction.normalized() * span * 2.5
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(output / f"qc_{name}.png")
        bpy.ops.render.render(write_still=True)


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
    elif category in {"creature", "animal"}:
        parts = make_leg(spec["seed"])
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
    apply_voxel_remesh(obj, voxel_size=0.055 if category == "tree" else 0.035)
    add_uv(obj)
    original_triangles, optimized_triangles = reduce_to_budget(obj, spec["target_triangles"])
    lods = make_lods(obj, spec["max_lod_count"] if not spec["animated"] else 0)
    collision = make_collision(obj, category) if not spec["animated"] else None
    report = {
        "asset_id": spec["asset_id"],
        "objects": [audit(obj)],
        "runtime_triangles": triangles(obj),
        "triangles_before_budget_optimization": original_triangles,
        "lods": [{"name": x.name, "triangles": triangles(x)} for x in lods],
        "collision_object": collision.name if collision else None,
        "errors": [],
        "warnings": [
            "Procedural/imported candidate, not reference-validated",
            "Automatic remesh is not deformation topology",
            "No high-to-low texture bake or UE profiling performed",
            "UCX collision is an approximate trunk primitive; verify gameplay fit",
            "LODs are exported separately and require Unreal LOD assignment",
        ],
    }
    (output / "qc.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    export_mesh(obj, lods, collision, output)
    render_reference_views(obj, output)
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "master.blend"))


if __name__ == "__main__":
    main()
