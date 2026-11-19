"""Optional Blender Cycles high-to-low normal bake.

Run inside Blender. Requires an actual reviewed high-poly source and UV-unwrapped
runtime mesh. This is NOT called by the default worker, which lacks an approved cage.
"""
from pathlib import Path

def bake_normal_map(high_obj, low_obj, output_png, *, resolution=2048,
                    cage_extrusion=0.04, margin=16):
    import bpy
    if high_obj.type != "MESH" or low_obj.type != "MESH":
        raise ValueError("Both bake objects must be meshes")
    if not low_obj.data.uv_layers:
        raise ValueError("Runtime mesh requires reviewed UVs")
    if resolution not in (512, 1024, 2048, 4096, 8192):
        raise ValueError("Unsupported texture resolution")
    image = bpy.data.images.new("BAKED_Normal", width=resolution,
                                height=resolution, alpha=False)
    image.colorspace_settings.name = "Non-Color"
    if not low_obj.data.materials:
        mat = bpy.data.materials.new("M_Bake_Target")
        low_obj.data.materials.append(mat)
    for mat in low_obj.data.materials:
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        for node in nodes:
            node.select = False
        tex = nodes.new("ShaderNodeTexImage")
        tex.name = "BAKE_Normal_Target"
        tex.image = image
        tex.select = True
        nodes.active = tex

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16
    scene.render.bake.use_selected_to_active = True
    scene.render.bake.cage_extrusion = cage_extrusion
    scene.render.bake.margin = margin
    bpy.ops.object.select_all(action="DESELECT")
    high_obj.hide_set(False)
    low_obj.hide_set(False)
    high_obj.select_set(True)
    low_obj.select_set(True)
    bpy.context.view_layer.objects.active = low_obj
    bpy.ops.object.bake(type="NORMAL")
    target = Path(output_png)
    target.parent.mkdir(parents=True, exist_ok=True)
    image.filepath_raw = str(target.resolve())
    image.file_format = "PNG"
    image.save()
    return str(target.resolve())
