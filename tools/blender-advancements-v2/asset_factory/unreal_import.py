"""Unreal Editor Python helpers. Run inside an actual UE project with Python enabled.

FBX is preferred for static meshes with UCX collision. LOD files are NOT
automatically assigned here; engine validation is still mandatory.
"""
from __future__ import annotations
from pathlib import Path


def _import_file(source_path: str, destination="/Game/Generated", options=None):
    import unreal
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(source)
    task = unreal.AssetImportTask()
    task.filename = str(source.resolve())
    task.destination_path = destination
    task.automated = True
    task.save = True
    task.replace_existing = False
    if options is not None:
        task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = list(task.imported_object_paths)
    if not imported:
        raise RuntimeError("Unreal import returned no assets; check Editor import logs")
    for asset_path in imported:
        if not unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            raise RuntimeError(f"Imported asset path missing: {asset_path}")
    return imported


def import_static_fbx(source_path: str, destination="/Game/Generated"):
    """Import static FBX; UCX naming is expected to create custom collision."""
    import unreal
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("import_materials", True)
    options.set_editor_property("import_textures", True)
    static_data = options.static_mesh_import_data
    static_data.set_editor_property("combine_meshes", False)
    static_data.set_editor_property("auto_generate_collision", False)
    return _import_file(source_path, destination, options=options)


def import_glb(source_path: str, destination="/Game/Generated"):
    """GLB import requires the appropriate Unreal Interchange pipeline/plugins."""
    return _import_file(source_path, destination)


def import_candidate_folder(folder: str, destination="/Game/Generated"):
    folder = Path(folder)
    fbx = folder / "asset.fbx"
    if fbx.exists():
        return import_static_fbx(str(fbx), destination)
    glb = folder / "asset.glb"
    if glb.exists():
        return import_glb(str(glb), destination)
    raise FileNotFoundError(f"No asset.fbx or asset.glb in {folder}")
