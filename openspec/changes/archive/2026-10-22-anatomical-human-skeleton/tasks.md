# Tasks

Implementation prerequisite: the human must approve both capability specifications and the complete numerical dossier in `design.md` before implementation begins (AGENTS.md, Human gate 1). Planning completion does not constitute that approval. Implement the frozen dossier; missing values or failed acceptance criteria require a planning revision, not invented anatomy or relaxed tolerances.

Completed items retain their existing implementation and snapshot-specific verification evidence. The approved R3 implementation has independent numeric PASS WITH NOTES; human visual task 10.4 remains open. The human confirmed the four-artifact presentation planning refinement on 2026-10-22. New tasks 9.7–9.8 and 10.5 cover only that HTML presentation refinement and remain pending. Existing anatomical and numeric tasks are not reopened by this refinement. Developer checks accompany each implementation group. Independent review must use a fresh output directory and must not repair implementation code. No muscles, production motion library, or distribution exports are included.

## 1. Toolchain and licensing foundation

- [x] 1.1 Establish the uv-managed Python 3.12 project with PyYAML, jsonschema, Pillow, and a committed `uv.lock`; verify a clean `uv sync --locked` resolves the declared environment and records dependency versions.
- [x] 1.2 Pin Blender 5.2.2 LTS build `d13f752e3b9c` and the reference platform without machine-specific executable paths, ignore scratch binaries under `build/`, and establish the command contract in `tools/README.md`; verify version mismatch is reported and every planned entry point has documented inputs and outputs.
- [x] 1.3 Establish `LICENSE-DATA`, `LICENSE-CODE`, required third-party notices, and the source-to-output attribution contract using the existing used-materials register; verify the declared CC-BY-4.0/Apache-2.0 licenses and retained vocabulary notices cover the new data and code without treating permission-only figures as reusable inputs.

## 2. Canonical records, schemas, and validation

- [x] 2.1 Add closed Draft 2020-12 schemas for profile, mobility, body groups, humanoid mapping, diagnostic fixtures, and review scene sources; verify positive records and negative tests for unknown fields, invalid units/versions, non-finite numbers, non-positive stature, and missing descriptions/provenance.
- [x] 2.2 Encode `rig/profiles/adult-reference-v1.yaml` from the design's numeric dossier, including expanded landmarks, dimensions, bases, stable attachment IDs, and individual/fused/grouped/omitted inventory; verify every required structure and dossier value has units, a frame, bounds, and a cleared source locator or authored-approximation rationale.
- [x] 2.3 Encode `rig/mobility/adult-reference-v1.yaml` with action frames, offsets, independent/dependent/fixed channels, operating bounds, composition, closed coupling types, and separate reference observations; verify all required articulations are present and the Faisal cohort values remain unchanged and distinct from operating limits and targets.
- [x] 2.4 Add `rig/body-groups.yaml` and `rig/humanoid-map.yaml` with shoulder ownership, required VRM names, optional omissions, internal-only structures, and mapping losses; verify exactly one smallest group owns each channel, all required targets resolve, and no helper, absent MPFB/Rigify rig, or unperformed export is misrepresented.
- [x] 2.5 Implement `tools/validate.py` with schema and cross-record validation and document the source contracts; verify the documented validation command passes canonical records and reports offending IDs/fields for duplicate YAML keys/IDs, cycles, dangling references, conflicting writers, omitted controls, and source or license gaps.

- [x] 2.6 Expand the revised thoracic dossier without executable expressions, preserving stable body/attachment IDs while updating rib control landmarks, sternal midsurface/insertions/parent-local transforms, and twenty declarative cartilage guides; verify new binding schema positives/negatives, cleared O/H source locators, retained attribution, authored-coordinate rationale, and exact five-point/free-rib and insertion topology.

- [x] 2.7 Encode and validate the closed R3 16-segment whole-body mass model with exact weights, rigid local points, normalized fractions, three coefficient variants, mirrored records and cleared source/adaptation provenance; reject malformed, missing, nonpositive, asymmetric and unresolved records and verify scaling without changing fractions.

## 3. Transform conventions and mirrored evaluation

- [x] 3.1 Implement canonical vector, matrix, quaternion, and rest-relative FK operations with the dossier's explicit bases; verify right-handed orthonormal frames within `1e-6`, local positive X rotation mapping Y to Z, parent composition order, `q`/`-q` equivalence, and rejection of quaternion norm error above `1e-6`.
- [x] 3.2 Resolve neutral assembly and the solved rest T-pose separately, including shoulder and forearm offsets; verify identity deltas reproduce horizontal arms with anterior palms and that round trips between action frames, rest-local deltas, and world transforms meet the specified position/orientation tolerances.
- [x] 3.3 Implement side-ID exchange and geometric/rotation mirroring through X=0 without negative scale; verify unilateral positive-action directions, proper rotation determinants, mirrored triangle normals, and double-mirror errors no greater than `1e-4 H` and `0.1 degrees`.
- [x] 3.4 Establish `tools/prepare_skeleton.py` validated JSON output and independent transform measurements in `tools/verify_skeleton.py`; verify source/schema hashes, deterministic record order, and independently calculated expected transforms in unit tests, and document the transform and measurement contracts in `tools/README.md`.

## 4. Action bounds and validation states

- [x] 4.1 Implement joint action evaluation and the distinct valid, unsupported, out-of-range, and unsatisfied-constraint results; verify failures retain joint/action, measured value, bounds/condition, and fixture time without clamping actions or changing targets, geometry, or floor.
- [x] 4.2 Implement hip and wrist composition and sign-specific multiaxis envelopes, plus elbow and forearm independent bounds; verify lower/mid/upper samples and `0.5 degrees` outside each limit with `0.1 degrees` measurement tolerance, and reject individually bounded combinations outside an envelope.
- [x] 4.3 Implement shoulder elevation-plane limits, canonical zero-elevation azimuth, twist envelope, and dependent glenohumeral guards; verify sector knots/intermediate planes, angle wrapping, valid conditional boundaries, and rejected combinations, reporting total and glenohumeral motion separately.
- [x] 4.4 Implement regional spinal envelopes and combined thoracic/lumbar budgets, pelvis placement bounds, primary knee and ankle/hindfoot/MTP bounds, and fixed-control rejection; verify all boundaries in floating context, unsupported independent knee varus/valgus at 10 degrees, and rejection of extra jaw/digit/foot-yaw controls.
- [x] 4.5 Add per-action axis-direction and limit coverage to the verifier and document reference means versus supported envelopes; verify absolute bilateral hip/toe, forearm/thumb, and medial tibial landmark directions reject former reversed signs, every supported action has identified positive, boundary, unsupported/invalid cases on both sides and no unreferenced channel receives a generic range.

## 5. Dependent anatomical articulation

- [x] 5.1 Implement clavicle/scapula/GH closure from the exact shoulder formulas; verify the dossier's elevation samples and intermediate planes, AC-to-glenoid positions, and independent measurements that fail when the scapula is deliberately frozen.
- [x] 5.2 Implement radius rotation about the declared radioulnar axis and the moving wrist/hand frame while retaining a rigid ulna; verify the five specified pronation samples, preserved shaft dimensions, distal trajectories, and rejection of a wrist-twist substitute.
- [x] 5.3 Implement dependent knee twist/translation and patellar tracking/tilt interpolation; verify all reference knots and intermediate samples against independent expected values, preserved tibia/fibula/patella dimensions, and failure of a frozen-patella mutation.
- [x] 5.4 Implement regional vertebral action distribution with rigid vertebra-carried ribs, a T1-carried sternum, and explicitly non-rigid cartilage guides; implement closed rigid-point, solved-guide-control, and endpoint-midpoint bindings with dependency validation and ordered evaluation; verify each regional axis/composition, per-vertebra contributions, total budgets, unchanged rigid-body lengths, SC closure, and current-pose cartilage closure.
- [x] 5.5 Implement the canonical oblique hindfoot axis and MTP/toe-group articulation with permanently attached ball witnesses; verify axis-direction cosines, independent ankle/hindfoot motion, rocker orientation cancellation, and that witnesses are never reassigned to obtain contact.
- [x] 5.6 Extend coupling verification and document approximation limits for all families; verify endpoint/every-15-degree reference samples plus input steps at most `0.25 degrees`, and diagnostic samples at most `0.01 beat` with origin changes at most `0.02 H` and orientation changes at most 5 degrees, retaining failures and measured maxima.

## 6. Reproducible Blender skeleton construction

- [x] 6.1 Implement `tools/build_skeleton.py` from factory startup and prepared JSON with separate Anatomy, Controls, Humanoid, and Review collections and stable body-local attachments; verify independent collection visibility, attachment resolution, unit object/bone scales, and absence of GUI-state or downloaded-asset dependencies.
- [x] 6.2 Generate skull/mandible, pelvis, all declared vertebrae/processes, ribs/sternum/guides, and shoulder-girdle meshes using the dossier's fixed resolutions and parameters; verify evaluated landmark/envelope bounds within `1e-4 H`, complete labeled inventory, and distinct rigid versus guide classification.
- [x] 6.3 Generate humeri, separate radii/ulnae, hands and fixed digits, femora/patellae, separate tibiae/fibulae, tarsal groups, metatarsals, and toe groups; verify required articulation survives grouping and measured geometry matches the dossier, including floor-relative foot envelopes and fixed contact attachments.
- [x] 6.4 Export evaluated body, landmark, attachment, scale, and topology measurements for every diagnostic sample; verify center-to-center limb ratios and stature scaling at H=1.50/1.70/1.90 m within `1e-6 H`, and posing rigidity within `1e-6 H`, distinguishing permitted joint-center translation from stretching.
- [x] 6.5 Add clean-build comparison and construction documentation; verify two isolated builds agree in sorted topology/IDs, positions within `1e-6 H`, and rotation-matrix elements within `1e-6`, with source hashes, actual versions/settings, and MPFB/Rigify recorded as not used, excluding incidental binary ordering/timestamps.

- [x] 6.6 Add independent thoracic shape and connectivity measurements at all three statures: actual surface envelopes, posterior angles, upper-to-middle widening, head-to-tip descents, sternal insertions and overhang, 1024-interval floating-rib arc-length ratios, and posed SC/cartilage endpoint/midpoint closure; verify the old uniform rib construction, bony-tip lower connections, missing metrics, and stale posed controls fail the specified scenarios independently of exact-coordinate goldens.

- [x] 6.7 Export actual native mass-point observations from evaluated carrier bones and independently verify local offsets, weights, COM and measured support margins on all three statures; reject absent/forged evidence without accepting prepared COM metadata.

## 7. Diagnostic fixtures, contacts, and solving

- [x] 7.1 Implement the scoped `skeleton-diagnostic/v1` evaluator and named rest/neutral fixtures under `rig/diagnostics/`; verify descriptions/provenance, beats, controls, base/hold/free semantics, mirrored variants, conflicting-writer rejection, and procedural noise/follow-through disabled, with fixture authoring documented.
- [x] 7.2 Implement scaled foot-local anchors, fixed world targets, half-open contact intervals and terminal states, and deterministic bounded contact solving with the dossier's seed/order/damping/iteration budget; verify endpoint semantics and an unreachable target fails with original target, limits, and residuals preserved.
- [x] 7.3 Implement independent contact, sliding, and complete evaluated-mesh floor measurements; verify flat support checks heel and both ball witnesses, rolling support checks only declared pins, target/slide errors are at most `1e-3 H`, and no visible geometry falls below `-1e-4 H`, regardless of solver flags.
- [x] 7.4 Encode the exact four-beat squat and analytic construction without amplitude selection by the implementer; verify the seven matrix-audit samples, bottom knee flexion `90 ± 2 degrees`, R3 ankle/pelvis/lumbar construction, explicit pelvis/torso/leg/arm ownership, planted feet, fixed world root, and loop closure within `0.1 degrees`/`1e-4 H`.
- [x] 7.5 Encode the exact four-beat forward arm raise; verify bilateral total elevation `160 ± 2 degrees`, elbows within 2 degrees of extension, prescribed girdle coupling, planted feet, trunk/pelvis orientation within 1 degree, root position within `1e-4 H`, and loop closure.
- [x] 7.6 Encode the corrected eight-beat walking-in-place fixture using the design's derived hip/hindfoot flat-orientation construction; verify its reference table, dense and delivered-frame floor clearance, joint envelopes, left/right swing and support intervals, opposing arms, each apex's complete-sole clearance at least `0.02 H` and knee flexion at least 45 degrees, full-flat double-support phases, fixed world root, and loop closure; retain the original penetrating construction as a rejected negative regression without retuning the dossier if a check fails.
- [x] 7.7 Encode the exact four-beat forefoot rocker and isolated action sweeps for every joint family, including full forearm mobility; verify rocker pelvis/ankle construction, permanent ball-witness support and terminal flat state, floating sweep stage placement with no contacts, dense continuity/limit coverage, and documented authored-diagnostic limitations.

- [x] 7.8 Implement independent static COM/support-hull checks for every delivered and dense squat sample, with reference margin >=0.010H and minimum variant margin minus0.005H >=0.005H; retain all observations/extrema and verify the historical squat fails despite valid pins/floor, with missing/forged/equalized mass and target-substitution negatives.

## 8. Shared animation and timing

- [x] 8.1 Implement one beat-keyed animation evaluation path with exact rational beat/second metadata and frame IDs for static and animated outputs; verify both modes share transforms within `0.1 degrees`/`1e-4 H` at common times and BPM changes preserve beat-relative geometry.
- [x] 8.2 Implement the sampling rule at BPM 60/120/180 with integer fixture/contact events on the delivered grid; verify four-beat outputs have 5 static and 21/13/13 animated samples, eight-beat outputs have 9 static and 41/25/25 animated samples, endpoints occur once, and every count interval has at least two in-betweens and no step above 200 ms.
- [x] 8.3 Integrate sampling metadata with prepared inputs and document timing/terminal-state behavior; verify count, contact-event, mirrored, and dense verification samples use the same keyed source without image interpolation or separate static poses.

## 9. Fixed rendering and review pack

- [x] 9.1 Add `scenes/skeleton-review.yaml` and its headless scene construction with the exact full-body and additional fixed thoracic inspection cameras, floor, resolution, Workbench settings, colors, and overlays in the revised design; verify those settings remain identical across every frame/stature and that no automatic reframing conceals clipping or motion.
- [x] 9.2 Implement `tools/review_pack.py` structural views and reports; verify `build/review/anatomical-human-skeleton/index.html` links readable front/rear/side neutral/T-pose and regional sheets, local axes, measurements, simplifications, and attribution/approximation limitations using the fixed underlying views.
- [x] 9.3 Add front/side count and animation contact sheets, GIFs, and onion-skin overlays for the main diagnostics and every action family; verify floor/contact markers, exact PNG timestamps, GIF cumulative duration error below 10 ms, and links from each failed metric to its relevant image.
- [x] 9.4 Complete machine-readable metrics, action/coupling coverage, and render metadata and document pack generation; verify every measurement includes its expected bound and status, missing checks cannot pass, camera/floor/light state is measured directly, and two clean reference-platform renders have identical decoded PNG pixels.

- [x] 9.5 Produce the focused neutral/T-pose thoracic preview through the documented existing prepare/build/review commands before rerendering the full diagnostic set; verify fixed front/side/three-quarter context and isolated views, readable rib/sternum/cartilage labels, source hashes, all nominal and relational shape metrics, and SC/guide closure; expose failures and preserve the early preview as development evidence rather than final acceptance.

- [x] 9.6 Generate an early squat-only R3 front/side pack through existing documented commands with unannotated and COM/support overlays at60/120/180 BPM, then regenerate the complete diagnostic set and two clean render passes with matching hashes; preserve historical R2 outputs and expose static-only limitations, margin values and renewed independent-review links.

- [x] 9.7 Update diagnostic HTML generation with the shared wrapping navigation and BPM-grouped Front/Side preview layout; verify the Diagnostic HTML requirement's complete inventory, destination/current-marker checks and browser layout at 1024/1200/390 CSS px, including isolated sweeps and squat overlay variants.

- [x] 9.8 Document and implement the existing review-pack command's HTML-only regeneration mode and produce a fresh developer presentation derivative; verify all local links, unchanged media/timing/numeric-evidence hashes, preserved predecessor manifests, explicit presentation provenance and deterministic HTML regeneration without Blender or image/GIF re-encoding.

## 10. Integrated acceptance and independent review

- [x] 10.1 Run all documented validation/build/verification/pack commands and `uv run python -m unittest discover -s tests` as an integrated developer check; verify every scenario in both delta specs maps to an executable check or explicit human visual criterion and retain the resulting reports.
- [x] 10.2 Exercise the complete pipeline with deliberate frozen-scapula/patella, wrong-side-sign, stretched-shank, unreachable-pin, undeclared world-root-offset, former constant-offset rib geometry, bony-tip costal-arch binding, and stale guide-midpoint faults; verify each fault fails the intended requirement/scenario and no success flag or missing measurement masks it.
- [x] 10.3 Have an independent reviewer rebuild from canonical sources into fresh outputs, audit provenance and all acceptance measurements, and write `review.md` in this change folder; verify the report links the review pack, cites violated requirements/scenarios, and withholds acceptance for missing evidence/checks or unresolved failures, with fixes returned to development and re-reviewed.
- [x] 10.4 After task 10.5, present the independently verified presentation derivative with its original numeric/render evidence and record the human's verdict for anatomical plausibility, movement readability, direct navigation and paired front/side comparison; verify explicit approval before completion and resolve rejection notes through development or planning with renewed checks appropriate to the affected scope.
- [x] 10.5 After tasks 9.7–9.8, have an independent reviewer regenerate the presentation derivative into the fresh independent directory and record a scoped presentation verdict; verify every page/BPM pair, navigation and responsive-layout scenarios, media/evidence hash preservation and snapshot lineage, retaining desktop/narrow browser captures and keeping the original numerical verdict scoped to its original snapshot.

## Thoracic visual-rejection follow-up (2026-10-21)

- Human gate 2 rejected the earlier rib-cage silhouette: excessive anterior projection, insufficient differentiation of upper ribs, and an implausible lower edge. The human confirmed revising proposal/design/specs/tasks. This confirmation authorizes the planning revision; it does not mark the revised geometry implemented or visually accepted.
- Complete the revised source/schema/guide work and task 6.6, then task 9.5's focused preview, before the full multi-stature diagnostic/pack rerun and tasks 10.1–10.3. Keep all preceding action-direction, contact, timing, and floor regressions active with their existing bounds.
- The existing `review.md` and independent pack are historical evidence for their recorded source hashes. The new thoracic geometry requires a fresh developer run, independent reconstruction/review, and an explicit new human visual verdict. Do not edit the old reviewer verdict merely to describe planned work or count it as acceptance of revised sources.
- Reopened tasks intentionally invalidate earlier completion evidence in affected areas. Preserve previous outputs; write fresh results without mixing source snapshots. Task 10.4 remains incomplete until the rejection has been resolved and the human explicitly accepts the renewed pack.

## Workflow follow-up

- Archive only after all tracked work is complete, independent review accepts the result, and the human has explicitly approved the visual pack (AGENTS.md, Human gate 2).
- Preserve the approved conventions and attachment IDs for later changes that add muscles, production motions, or baking/export; do not commit scratch binaries or populate `dist/` in this change.

## Squat visual-rejection follow-up R3 (2026-10-21)

- The human identified inadequate knee advance and apparent rearward imbalance and requested correction. Planning arithmetic found the former bottom's approximate COM behind support. Request approval of the complete new numerical dossier before implementation under Human gate 1; a generic request to fix the issue is not a claim of numerical implementation acceptance.
- Reopen affected source, mirror/scaling, ankle-bound/sweep, squat, evidence and report tasks. Preserve the complete R2 independent pack/report and source snapshot before renewed work. R2 numeric PASS remains historical evidence for its own source hashes.
- Add the exact closed mass source contract and actual native observations, then R3 squat/ankle bounds and independent balance checks. Produce the focused squat preview before full developer and independent reconstruction into fresh R3 output paths. Do not invent mass data, relax floor/rigidity/angle/contact limits or change unrelated amplitudes to obtain acceptance.
- The new check is static plausibility for a documented whole-body approximation, not dynamic stability, measured tissue anatomy or muscle-force simulation. Retain complete source/algorithm limitations and sensitivity bounds in the pack.
- Human gate 2 remains pending for the thorax and corrected squat. No archive until explicit visual acceptance.

R3 approval recorded (2026-10-21): the human explicitly approved the complete numerical squat/mass/ankle revision and authorized implementation, full regeneration and independent review. Human visual gate 2 remains pending.

Presentation planning approval recorded (2026-10-22): the human confirmed the proposed updates to proposal, joint-mobility spec, design and tasks. Preserve all 52 previously completed tasks and historical R3 evidence. Implement and independently verify tasks 9.7–9.8 and 10.5 before presenting the derivative for task 10.4; approval of this planning update does not complete those tasks or human visual gate 2.

## Human visual acceptance — 2026-10-22

The human explicitly accepted visual gate 2 after confirming that the obvious errors had been corrected. This closes task 10.4 for the independently verified presentation derivative at `build/review/anatomical-human-skeleton/presentation-r1/independent/linked-assets-fix/pack/`, with scoped presentation evidence in `build/review/anatomical-human-skeleton/presentation-r1/independent/review.md` and the retained original R3 numerical/render evidence. This records human acceptance of the presented anatomy, movement readability, navigation and paired comparison; it does not claim additional automated Safari/Firefox file-URL execution or change the scope of historical numerical verdicts. Archiving has not been performed.
