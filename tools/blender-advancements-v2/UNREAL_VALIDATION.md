# Unreal Engine 5 game-asset validation

## Import
- Use the FBX candidate for static meshes requiring UCX collision; verify the UCX_ prefix matches the visible mesh exactly. Blender's simple tree trunk cylinder is only an approximation.
- GLB is useful for preview and exchange; Interchange import behavior varies by UE version and plugins.
- LOD1..N are exported as separate GLBs; they are NOT automatically wired into Unreal's LOD chain. Import/assign manually or extend the UE Python helper for the installed UE version.
- Static mesh assets should have sensible pivot, metre-based scale (Blender 1m = Unreal 100cm by default conversion), smoothing/normals, materials and lightmap strategy. Inspect imported size.
- Skeletal assets need a reviewed skeleton, weights, bone orientation, animation test poses and deformation topology. Do not use the static GLB postprocess on a rigged asset.

## Optimization decision rules
- Triangles: set per-platform target based on projected size, number of instances, animation and target frame time. There is no single universal poly budget.
- Nanite: test on static high-poly meshes; UE-version-specific skeletal and foliage capabilities exist but need feature/quality/performance checks. Masked foliage, WPO, overdraw and many material slots can dominate cost.
- LODs: test screen-size transitions, silhouette preservation and total memory. HLOD and ISM/HISM for repeated static assets.
- Materials: reduce slots, atlas/trim sheets, PBR maps, pack roughness/metallic/AO channels where compatible, use appropriate texture compression and virtual texturing only when justified.
- Texture: choose 512/1K/2K/4K by screen size and texel density, not just by model prestige.
- Collision: use simple convex primitives or UCX meshes for runtime physics, not render geometry; review navmesh and trace settings.
- Rigged creatures: budget skinning, bone count, influences, morph targets, material complexity, animation and physics separately.
- World scale: test open-world streaming, foliage clustering, PCG placement and HLODs, and measure draw calls, GPU time, memory and streaming hitches.

## Performance acceptance report (fill in from actual UE session)
{
  "unreal_version": null,
  "target_platform": "PC",
  "scene": null,
  "asset": null,
  "instance_count": null,
  "triangles_lod0": null,
  "materials": null,
  "draw_calls": null,
  "gpu_ms": null,
  "memory_mb": null,
  "nanite_enabled": null,
  "collision_verified": false,
  "lods_verified": false,
  "rig_pose_verified": false,
  "visual_reference_approved": false,
  "engine_validated": false
}

No value may be invented. Technical Blender QC is necessary but not sufficient for engine validation.

Sources:
- https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine
- https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-static-meshes-using-fbx-in-unreal-engine
- https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python
- https://dev.epicgames.com/documentation/en-us/unreal-engine/pcg-development-guides
