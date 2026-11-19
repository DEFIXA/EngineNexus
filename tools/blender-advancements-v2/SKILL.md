---
name: blender-advancements-v2
description: ChatGPT-orchestrated Blender and Unreal Engine game-asset factory. Plans assets from prompts and references, routes procedural, Infinigen, Meshy, or external image-to-3D generation, runs Blender production and QC, and exports Unreal-ready candidates. Never calls a candidate game-ready without topology, UV, rig, visual and engine validation.
---

# Blender Advancements V2: Game Asset Factory

## Purpose
Upgrade the existing Blender Advancements toolkit without deleting its original modules. The user's grayscale fantasy-dragon limbs, heads, wings, twisted trees, and human edge-loop sheet define the quality bar. Match silhouette and anatomy before detailing. An image-conditioned 3D model is a starting candidate, not automatically an animation-ready game asset.

## Operating procedure
1. Parse the user prompt and optional reference images into an AssetSpec. Record category, animated/static, target hardware, triangle budget, desired materials, references, provenance and spending permission.
2. Select a backend with asset_factory.router: Blender/anatomy for controllable creatures, procedural tree generation or Infinigen for nature, modular Blender for structures, Meshy for reference-conditioned candidates only with explicit paid-generation permission, or a separately configured local 3D AI provider.
3. Preserve the high-poly master. Validate primary silhouette, joint placement, asymmetry, claw/horn transitions and branch taper before fine detail.
4. Build a runtime derivative. For animated creatures, automated decimation/remesh is NOT deformation retopology. Require reviewed edge loops and test poses. For static assets, use configurable LODs or Nanite when benchmarked.
5. Check mesh connectivity, normals, UVs, material slots, textures, tri budget, scale, transforms, collision and exported files. Render fixed front, side, three-quarter comparison sheets.
6. Report the true status: planned, candidate, QC-pass, needs-human-review or engine-validated. Do not claim a model was tested in Blender or Unreal without logs from those programs.
7. Record generator, source refs, seeds, version pins, license, paid API spend and UE performance results in manifest.json.

## Run
- Planning without Blender: python -m asset_factory.cli plan examples/dragon_leg.json
- Build procedural candidate: python -m asset_factory.cli build examples/twisted_tree.json --blender /path/to/blender
- Audit a Blender-produced QC JSON: python -m asset_factory.cli audit work/tree/qc.json
- Merge with user's original archive: python install_upgrade.py /path/to/blenderadvancements101.zip --output blenderadvancements101_v2.zip

## Backend boundaries
- Blender procedural: local, deterministic starter geometry and automated static mesh QA; cannot magically match complex high-poly reference art.
- Infinigen: procedural environments, trees, rocks and nature; verify installed factory names and CLI against the checked-out version.
- Meshy: cloud image/text-to-3D. API keys only via environment. Requires user permission for paid calls. Downloads promptly; retopology still required for deforming anatomy.
- TRELLIS.2 / Pixal3D / other local AI: opt-in external adapter. No invented installation or execution commands; user supplies verified command and model weights.
- UE: optional Unreal Editor Python import. UE validation/performance must be measured in an actual project.

## Existing toolkit integration
Look for existing modules asset_specs.py, creature_forms.py, anatomy_tools.py, adaptive_topology.py, reference_qc.py, tree_growth.py, game_bakes.py, rig_tools.py, production_metrics.py and form_pipeline.py. Keep them unchanged; import only after verifying their actual functions/signatures. The V2 controller never assumes an undocumented muscle_loft signature.

## Reference policy
User-supplied references are private project inputs. Never upload them to Meshy or other cloud providers without user authorization. A single perspective image is ambiguous; request multiple consistent views for exact anatomy when available. Never treat a visual similarity score as proof of anatomical correctness.

## Quality policy
No universal polygon budget. Choose budgets per platform, screen size, draw count, animation and materials. Validate LODs, UV stretch, normal bakes, deformation, collision and performance. Do not enable skeletal Nanite or foliage Nanite by default; gate by UE version and benchmark.

## Files
- asset_factory/spec.py: typed specs
- asset_factory/router.py: backend decision
- asset_factory/cli.py: planning/build/audit CLI
- asset_factory/meshy.py: paid API adapter
- asset_factory/infinigen.py: procedural factory wrapper
- asset_factory/blender_worker.py: headless Blender mesh creation and validation
- asset_factory/quality.py: technical quality gates
- asset_factory/unreal_import.py: optional UE Editor import
- install_upgrade.py: safe ZIP merger
- tests/: offline unit tests
