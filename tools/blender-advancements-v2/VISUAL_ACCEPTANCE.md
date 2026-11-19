# Mesh-first dragon reference acceptance

## Non-negotiable rules
- **Full mesh** means a complete quadruped dragon: head and jaws, torso and neck, four articulated legs, toes and attached claws, two wing membranes, a tapered tail and a coherent spine.
- **200,000 triangles maximum for the complete exported LOD0 asset**, not per part. Preserve primary form before decimating. Lower is better only when the silhouette survives.
- **Clay geometry first**. Texture, shader and material passes cannot rescue incorrect geometry.
- **Render the actual Blender mesh** as front, side and three-quarter PNGs, not an intended design or an AI-generated 2D concept.
- A disconnected cluster of claws, a melted blobby silhouette, a partial leg instead of a full dragon, or an unrecognizable body FAILS, regardless of unit tests.
- Keep source master and audit runtime mesh. Connected components = 1 is the default for procedural creatures. A multi-part rigged asset needs a reviewed exception, not a silent exemption.
- Technical tests do not establish sculpt quality or reference similarity.

## Compare against the supplied reference images
The user provided several different dragon designs, not consistent views of one dragon. These establish a quality bar, not a single pixel-perfect reconstruction target. Choose a specific design and synchronized views for close reconstruction.

1. **Hindleg collage**: broad hip and thigh, knee/hock, tendons, heel, four attached toes, curved claws, asymmetrical plates. Reject detached claws.
2. **Pale quadruped**: weight-bearing four-leg stance, arched back and neck, long tail, believable muscle volumes.
3. **Dark dragon**: organic neck/shoulder, supported wings, detailed horns and spine.
4. **Red dragon**: complete body, coherent head, feet, wing span and long tail, all readable from multiple angles.
5. **Gray head sculpt**: brow, jaws, teeth, nostrils, horn roots, neck spines and dense skin relief.

## Visual reviewer checklist
Mark PASS, FAIL or NOT ASSESSED, with notes:
- Full body present and visually recognizable
- Silhouette matches the chosen reference family
- No floating/disconnected fragments
- Four correctly placed, weight-bearing limbs
- Joint transitions and muscle anatomy
- Claws rooted in toes and continuous tapering tail
- Wing bones support membranes and connect to shoulders
- Head with jaw, eyes, nostrils, horns and convincing skull volumes
- Sculpted secondary ridges, scales, wrinkles and spines
- Total LOD0 at or below 200k triangles
- Real front/side/three-quarter Blender PNGs opened and compared

## Status
generated_candidate -> technical_qc_pass -> visual_review_pending -> visual_reference_approved -> retopology_and_rig_review -> unreal_engine_validated.

The CLI deliberately reports awaiting_visual_review, not finished, after technical QC. Only a reviewer who actually inspected the renders can approve the shape. Record visual failures and correct them.

## Privacy and costs
Cloud image-to-3D may provide higher fidelity than the procedural blockout. Do not upload private references or spend Meshy credits without the user's explicit consent. Request untextured geometry for this phase.
