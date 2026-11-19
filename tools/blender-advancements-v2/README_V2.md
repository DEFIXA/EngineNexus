# Blender Advancements V2: upgrade overlay

This is an **additive, installable upgrade** for the existing blenderadvancements101 archive, designed from the supplied research and reference images. It does not claim to have inspected the original archive source files in this execution environment. The research describes 47 original files; this overlay keeps those files and adds an independent V2 controller.

## What it does
- Prompt/JSON asset specifications and deterministic backend routing.
- Procedural Blender candidate for a dragon hind leg and a twisted dead tree.
- Static mesh cleanup, UV projection, configurable LODs, convex collision, FBX/GLB export, and JSON QC.
- Meshy image-to-3D candidate download, guarded by explicit paid-cloud consent.
- Infinigen individual asset factory wrapper, version-dependent.
- Unreal Editor Python import starter.
- Offline unit tests and safe ZIP merge with the original skill.

## What it does not pretend to do
- Automatically match the uploaded sculpt references at hero quality without artistic iteration.
- Automatically deliver production deformation retopology, rigging, or a correct PBR bake from an arbitrary generated mesh.
- Run Blender/UE in ChatGPT without a connected execution environment.
- Guarantee the compatibility of unknown original module function signatures.

## Install
1. Download this directory, and retain the original blenderadvancements101 ZIP.
2. From this directory run:
   python install_upgrade.py /path/to/blenderadvancements101.zip --output blenderadvancements101_v2.zip
3. Inspect the merged ZIP. It includes all original files and the V2 overlay. Run:
   python -m unittest discover -s tests -v
4. Install Blender 4.x (version-pin per project) and test a reference tree:
   python -m asset_factory.cli plan examples/twisted_tree.json
   python -m asset_factory.cli build examples/twisted_tree.json --blender /path/to/blender
5. For Meshy, set MESHY_API_KEY in your environment and pass --allow-paid only after approving cost and cloud upload.

## Workflow
prompt + images -> JSON spec -> route -> backend candidate -> Blender master -> silhouette QC -> runtime mesh -> UV/bake -> rig if animated -> export -> UE Editor validation -> manifest.

Outputs are **candidates** until visual and engine checks pass. Check work/<asset_id>/qc.json, work/<asset_id>/manifest.json and exported files.

## Important production limitations
The demo leg is anatomical scaffolding. Sculpting, reference-matching, deformation loops and rigging require additional reviewed work. The demo tree has curve-derived fused branches and is intended to demonstrate procedural control, not a final hero sculpt. A high-to-low bake must be done with an actual approved high-poly source; the worker does not invent normal maps.

## Dependencies
- Planning, routing, tests and archive merge: Python 3.10+ standard library.
- Procedural build: Blender with Python and bpy, installed separately.
- Meshy: network access and API key.
- Infinigen: an independently installed, compatible checkout.
- Unreal import: Unreal Editor Python plugin enabled in an actual UE project.

## Security
No shell=True. Untrusted ZIPs are checked for path traversal and symlinks. API keys never appear in manifests. Paid requests and cloud reference uploads require --allow-paid. Existing toolkit files are never deleted by the installer.

## Source links
- Blender Python API: https://docs.blender.org/api/current/
- Infinigen: https://github.com/princeton-vl/infinigen
- Meshy API: https://docs.meshy.ai/
- Unreal Python: https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python
