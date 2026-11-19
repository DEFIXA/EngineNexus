# Source sculpt -> Blender geometry-only validation

The user's Safi Dragon screenshot is a rendered Blender viewport, not a mesh file. Exact sculpt fidelity requires the original mesh or a suitable AI-generated source. Existing Meshy models can be used after the user approves any applicable download quota; new paid generations and image uploads need separate explicit permission.

Export the original Safi Dragon from Blender to GLB, place it alongside examples/imported_safi_dragon.json as SafiDragon.glb, then run:

python -m asset_factory.cli build examples/imported_safi_dragon.json --blender /usr/bin/blender

The imported source is retained as SOURCE_HIGH, and the candidate is reduced to 180k triangles if needed. The import path now deliberately preserves original UVs and avoids voxel remesh or synthetic noise by default. A forced repair is opt-in because it destroys fine sculpt detail. A static GLB is NOT a rig; retopology and rigging are later phases.

The worker exports real Blender front, side, three-quarter, head and wing PNGs for human reference review. Technical pass does not imply artistic similarity. A high-quality source may contain intentional separate eyes, teeth or plates; connectivity QC will flag multiple components for explicit review rather than silently delete them.

The procedural tree test now preserves its branch tubes instead of using destructive voxel fusion by default. It still needs visual inspection for gaps. The procedural cottage has corrected roof pitch and geometric shingles. These are incremental upgrades, not claims of reference-level completion.
