# Proposal: Anatomical human skeleton for exercise animation

## Why

The project needs a reusable human skeleton before it can produce credible walking, squatting, and arm-raising animations. Documented proportions, joint placement, and joint-specific mobility must provide a verifiable foundation for natural movement and for adding muscles in later changes.

## What Changes

- Introduce a canonical, data-driven skeleton with a documented adult reference proportion profile, anatomical landmarks, bone lengths, joint centers, and parent relationships. Make overall stature configurable while preserving the reference proportions; document the supported profile rather than implying that one body represents all humans.
- Define skeletal geometry that makes the skull, spine, rib cage, pelvis, and limbs recognizable and allows joint placement and articulation to be inspected. State the anatomical detail and each simplification explicitly; distinguish anatomical structures, animation bones, and helper controls.
- Differentiate the twelve rib pairs with curved posterior, lateral, and anterior paths, graded depth and inferior inclination, explicit costosternal insertions, a connected costal-cartilage arch for ribs 8–10, and short free ribs 11–12. Represent the manubrium, sternal body, and xiphoid within one rigid sternum and close its sternoclavicular landmarks without relocating the shoulder joints. Verify thoracic shape relationships in addition to matching source coordinates.
- Describe each supported joint's local axes, degrees of freedom, permitted motion, and relevant coupled behavior. Establish evidence-backed numerical ranges and tolerances during specification, distinguish reference mobility from exercise targets, and make unsupported movement and limit violations detectable.
- Cover the coordinated motion needed for the diagnostic exercises, including the shoulder girdle, torso and pelvis, forearm rotation, and foot articulation. Do not treat every joint as an unrestricted rotation or claim anatomical accuracy solely from matching a silhouette.
- Define the skeleton's units, coordinate frames, rest T-pose, rotation representation, body-group membership, and explicit mapping to the project's VRM humanoid vocabulary. Preserve anatomical detail internally without introducing a replacement interchange skeleton standard; document any mapping limitations.
- Generate the inspectable skeleton and animation rig reproducibly through headless Blender from repository sources. Keep skeletal structure separate from controls so muscles and other geometry can be added later without redefining the canonical skeleton.
- Verify absolute landmark directions as well as formulas: hip external rotation turns toes laterally, forearm midrotation after elbow flexion places the radial/thumb side upward, and initial dependent knee twist turns the tibia medially.
- Add a source-backed whole-body point-mass approximation and measured contact-support hull for squat static plausibility. Correct the squat to 20-degree ankle dorsiflexion and 25-degree pelvis pitch at 90-degree knee flexion; explicitly revise the prior authored 12-degree ankle operating ceiling to 20 while retaining cohort observations. Reject the old backward-balanced construction independently of pins/floor success; expose COM and support in review overlays. This does not add tissue geometry or a dynamic/force solver.
- Verify proportions, joint axes and limits, bilateral mirroring, bone-length preservation, and reproducible generation numerically. Produce a visual review pack with labeled orthographic views, joint-axis and mobility demonstrations, and short diagnostic walking, squatting, and arm-raising sequences, including planted-foot checks where contacts are declared. Use fixed scene settings and the project's frame-timing rule; define exact exercises and acceptance tolerances in the specifications before implementation.
- Include fixed front, side, and three-quarter thoracic close-ups with rib numbers, separate bone/cartilage labels, posterior angles, and sternal insertions. Inspect these early in development before regenerating the complete review pack; final independent and human review still cover the complete skeleton and diagnostics.
- Improve generated diagnostic HTML for direct comparison: every diagnostic page exposes the same horizontal, wrapping navigation to all sibling diagnostics and the pack index; each BPM groups its labeled front and side animation previews in one row on desktop. Preserve existing media and numeric evidence through an explicitly identified presentation derivative.
- Require commercially usable, derivative-compatible references for every externally informed anatomical value or asset. Record sources, permission checks, attribution, and related outputs in `docs/used-materials.md`; do not insert unverified numerical anatomy into the model.

Muscles, skin and soft-tissue deformation, muscle-driven simulation, a production exercise library, and distribution-format baking/export are outside this change. Diagnostic poses and sequences exist to verify this skeleton, not to deliver those later capabilities.

## Capabilities

### New Capabilities

- `anatomical-skeleton`: Canonical skeletal structure and proportions, anatomical visualization, coordinate and rest conventions, body groups, humanoid mapping, reproducible Blender construction, and structural verification.
- `joint-mobility`: Joint axes, degrees of freedom, reference motion ranges, coupled articulation, limit validation, and numerical and visual exercise diagnostics for the supported skeleton.

### Modified Capabilities

None. The project currently has no published capability specifications.

## Impact

Introduces scoped skeleton and mobility data under `rig/`, corresponding validation schemas under `schema/`, headless generation and verification tools under `tools/`, and checks under `tests/`. Adds reproducible review-scene definitions under `scenes/` and generated review outputs under the gitignored `build/review/anatomical-human-skeleton/` directory. Document commands in `tools/README.md` and pin the Blender version; any third-party rig or asset dependency requires an explicit design choice and license clearance before use.

This change establishes the minimum foundation conventions needed by the skeleton. Later pose/segment/motion schema, timing, contact, scene/render, and export changes must reuse or explicitly migrate those conventions; their full implementations are not implicitly included here. Diagnostic fixture storage and timing must be specified within this change rather than depend on an unimplemented backlog item.

Authored skeletal data and assets use CC-BY-4.0, and tooling uses Apache-2.0; third-party materials retain their verified terms. Implementation starts only after the human approves the specifications and design. Independent review and human approval of the visual pack are required before archiving.

Earlier approved refinement (2026-10-21): correct the three action-axis signs in the unreleased mobility dossier and regenerate derived squat/walking reference tables, canonical evaluation, cached inputs, renders, and metrics. That refinement preserved geometry; the subsequent thoracic revision below supersedes that preservation only for the thoracic structures it names.

Confirmed planning revision (2026-10-21): the human rejected the rib-cage shape at visual gate 2 and confirmed revision of this dossier. The uniform anterior rib offset, nearly horizontal three-point paths, equal-fraction sternal connections, and connections from ribs 8–10 to adjacent bony tips are replaced by the numerical thoracic dossier in `design.md`. The sternum follows T1 to maintain its SC landmark closure; SC/AC/GH centers, vertebral rest curvature, limb proportions, action signs and limits, diagnostic amplitudes, and coordinate conventions remain fixed. The retained CC BY 4.0 first-edition OpenStax text informs anatomical relationships; all new coordinates are explicitly authored approximations. The watermarked comparison illustration is not a geometry source. The previous independent PASS WITH NOTES applies to the previous source snapshot and does not accept the revised thorax or override the human rejection. Implementation and renewed independent/visual review remain pending.

Squat R3 planning revision (2026-10-21): the human identified inadequate forward knee travel and requested correction after investigation found no COM measurement. The new numeric dossier and acceptance scenarios supersede only squat construction, the ankle positive operating bound/sweep, mass metadata and related evidence. Thorax R2 and all unrelated geometry, action signs, observations, stepping/arm-raise/rocker amplitudes, cameras and floor remain fixed. Human approval of the new numerical dossier is required before implementation; old R2 PASS does not accept R3.

R3 approval recorded (2026-10-21): the human explicitly approved the complete numerical squat/mass/ankle revision and authorized implementation, full regeneration and independent review. Human visual gate 2 remains pending.

Presentation refinement approved (2026-10-22): the human confirmed the four-artifact planning update for review-pack HTML navigation and layout. Anatomical data, poses, mass metadata, measurements, camera/floor settings, sampling and media content remain unchanged. The existing R3 PASS WITH NOTES remains evidence for its recorded snapshot; it does not certify revised HTML. A fresh presentation derivative requires independent presentation verification, followed by the still-pending human visual gate. This records planning approval; the presentation implementation and its verification remain pending.
