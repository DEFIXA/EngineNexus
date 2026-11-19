# ChatGPT prompt -> AssetSpec contract

This skill should work from arbitrary prompts by **choosing a suitable backend**, not pretending Blender's primitive tools can interpret all descriptions.

## Prompt parsing
1. Identify asset class: creature/human/animal, vegetation/tree/root, rock/terrain, structure, prop/weapon, vehicle or other.
2. Detect static vs animated. If the asset bends, walks, flaps, or has a skeleton, animated=true.
3. Extract proportions in metres, silhouette landmarks, anatomy, material language, weathering, pose, modularity and physical gameplay constraints.
4. Treat attached images as references, not as files accessible to a local subprocess unless their real paths are known. Never invent a path.
5. Set platform and triangle target from actual game requirements. If unknown, default to PC and use the spec's illustrative budget, then request a benchmark.
6. Prefer a single- or multi-view Meshy candidate for reference-conditioned creatures/props (paid consent). For organic procedural nature, prefer Blender/Infinigen. For buildings, use modular parametric Blender and kitbashing. If a local 3D AI backend is installed, it can be selected explicitly.
7. Output a valid JSON AssetSpec. Run plan before any paid create. Use build only after consent for cloud and after the environment has Blender or Meshy installed.

## Reference sculpt quality checklist
- Dragon legs: accurate digitigrade proportions, hock/knee placement, asymmetrical toes, tendon masses, joint clearance, claw roots and dorsal/ventral scute direction.
- Dragon wings: skeletal finger supports, membrane attachment and fold-safe deformation topology.
- Dragon heads: readable skull silhouette, jaw hinge, eye sockets, horn bases, nostrils, mouth interior and non-uniform surface detail.
- Twisted trees: tapered branching, real junctions, root buttressing, irregular negative spaces, bark direction, silhouette variation and sensible trunk collision.
- Humanoid: face/shoulder/elbow/hip/knee deformation loops, appropriate density distribution, neutral pose and tested skin weights.
- Buildings: modular grid, trim sheets, doors/stairs sized in metres, pivot/instancing, collision and material batching.

## Structured prompt example
"Generate a 6m twisted dead tree with exposed roots, 8 major branches and dark bark for a UE5 PC open-world forest. It is static, repeated 500 times. Target 12k triangles and 2k materials."

Result (illustrative):
{
  "asset_id": "dead_tree_001",
  "category": "tree",
  "prompt": "6m twisted dead tree, exposed roots, eight major branches, dark bark, asymmetrical negative space, suitable for repeated UE5 forest instances",
  "animated": false,
  "platform": "pc",
  "target_triangles": 12000,
  "texture_size": 2048,
  "backend": "blender",
  "seed": 1337,
  "max_lod_count": 3,
  "extra": {"height_m": 6.0, "instance_count": 500}
}

## Candidate iteration loop
- Render three orthographic views from the generated candidate.
- Compare each with a reference view of the same camera orientation. Compare silhouette first, then secondary forms, then surface details.
- If the silhouette fails, change the source shape, not the texture.
- If topology fails, retopologize before rigging; decimation is not an acceptable substitute for deforming anatomy.
- If UV/bakes fail, inspect seams, texel density, tangent basis, cage distances and overlapping islands.
- If engine performance fails, change materials, LODs, Nanite policy, instancing, collision and shader complexity before just lowering triangles.
- Repeat until artist approval and actual engine measurements pass. Never label this "perfect" automatically.
