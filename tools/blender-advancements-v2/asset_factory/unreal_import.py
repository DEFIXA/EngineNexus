"""Optional Unreal Editor Python import helper; run inside UE Editor only."""
from __future__ import annotations

def import_glb(source_path: str, destination="/Game/Generated"):
    import unreal
    task = unreal.AssetImportTask()
    task.filename = source_path
    task.destination_path = destination
    task.automated = True
    task.save = True
    task.replace_existing = False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = list(task.imported_object_paths)
    if not imported:
        raise RuntimeError("Unreal import returned no assets; check Interchange/plugin logs")
    return imported
