# Anatomical skeleton acceptance evidence map

Change: `anatomical-human-skeleton`. A passing developer check is not an
independent review or a human visual verdict. Executable checks below retain
their numeric outputs; visual criteria stay explicitly pending until approved.
Run the command contract in `tools/README.md` from a clean checkout/output area.

| Capability / scenario | Executable evidence or explicit human criterion |
|---|---|
| anatomical-skeleton / Reconstruct the skeleton from sources | `test_source_integrity.test_complete_source_validation`; `test_blender_backend.test_all_statures_have_valid_evaluated_geometry_frames_and_scene`; prepared source hashes and `evaluated.json` |
| Reject inconsistent structure | `test_source_schemas`; `test_source_integrity` cycle, dangling, duplicate, frame, provenance and writer mutations |
| Inspect structural coverage | `test_profile_dossier.test_schema_inventory_frames_and_references`; backend inventory and regional structural sheets; human anatomical plausibility |
| Reject a simplification that removes required articulation | `test_action_transforms`, `test_coupling_measurements`; actual frozen-body scene faults in `test_pipeline_faults` |
| Inspect thoracic structures and connections | `test_thorax`; five measured controls per rib, sternal shell rows/insertions and current-pose cartilage topology in `thorax_measurements.py`; labeled inspection views |
| Measure the neutral thoracic shape | `test_thorax.test_three_statures_and_spinal_motion_meet_independent_shape_and_closure`; native evaluated ring/shell measurements, independent Hermite arc/extrema, actual surface bounds and nominal dossier checks at three statures |
| Reject the former uniform thoracic construction | `test_thorax.test_old_uniform_geometry_fails_relational_checks`, `test_bony_arch_and_stale_midpoint_fail_even_with_valid_transforms`, `test_missing_native_evidence_fails`; backend fault evidence |
| Measure the reference limbs | `test_profile_dossier.test_mechanical_segment_ratios`; per-sample evaluated mechanical-length metrics |
| Change stature without changing the profile | `test_geometry.test_every_source_primitive_closed_and_stature_linear`; three clean Blender stature builds; `test_diagnostics.test_three_statures_scale_contact_targets_and_analytic_frames` |
| Review the profile before building it | Approved proposal/design and explicit apply request; authorized walking and aggregate foot-envelope corrections recorded in the design/preflight |
| Verify geometry against the approved dossier | `test_geometry`, `test_profile_dossier`; evaluated primitive bounds, landmarks, foot envelopes, floor minima, topology and scale metrics |
| Resolve rest and posed transforms | `test_math3d`, `test_poses`, `test_kinematics.test_neutral_and_t_pose_match_frozen_frames`; independent frozen-frame backend measurements |
| Validate quaternion semantics | `test_math3d` near-pi/sign/rest composition and invalid quaternion tests; source/frame validators |
| Inspect the mapping contract | `test_mapping_dossier`; required semantics/helper exclusion tests; actual native and semantic inventories in build metadata |
| Check posing invariants | Evaluated local-vertex rigidity and scale metrics at every delivered pose; stretched-shank fault; fixed-body/distribution checks |
| Mirror and mirror again | `test_mirror`; `test_kinematics.test_finite_rigid_rotations_and_mirrored_actions`; mirrored walking apex test |
| Repeat a clean build | `test_blender_backend.test_two_clean_builds_agree_in_topology_positions_and_rotations`; two clean full render passes with exact decoded-pixel comparison |
| Inspect attachment readiness | Source/actual attachment inventories and positions; permanent witness identity checks; negative attachment reassignment test |
| Audit an anatomical claim or asset | `docs/used-materials.md`, `THIRD-PARTY-NOTICES.md`, record provenance and source-integrity license gap tests; independent reviewer must audit the actual permissions |
| Review the skeleton before muscles | Front/rear/side neutral/T-pose, regional crops and local axes in the pack; human verdict on anatomical plausibility, declared simplifications and readability |
| Inspect the revised thorax closely | Focused preview and final front/side/three-quarter context/isolated sheets from fixed source cameras; explicit renewed human visual approval after independent review |
| joint-mobility / Inspect the required action inventory | `test_mobility_dossier`, `test_mapping_dossier`; all 70 action/placement entries in numeric coverage |
| Check axis directions independently of the backend | `test_action_transforms`, `test_mirror.test_named_positive_actions_keep_anatomical_direction`; floating full-axis sheets/GIFs |
| Explicit joint action model / Verify absolute anatomical directions | `tests/test_guides_and_coverage.py::test_absolute_anatomical_directions_and_reversed_sign_mutations`; metrics action coverage `absolute_anatomical_directions` (eight physical witnesses, old-sign mutations rejected). |
| Preserve the initial reference observations | `test_mobility_dossier.test_reference_means_remain_separate`; unchanged cohort rows distinct from limits/targets |
| Freeze the complete mobility dossier before implementation | Approved design plus expanded source action/coupling records; `test_mobility_dossier` |
| Check boundaries of an independent action | `test_actions.test_all_independent_boundaries_and_outside_samples`; `coverage.py` measured lower/interior/upper/positive/outside cases on both sides |
| Reject unsupported knee motion | `test_actions` unsupported/fixed/coupled writes; knee varus/axial input rejection; coverage records no pose for invalid writers |
| Report an unreachable contact target | `test_diagnostics.test_bounded_contact_solver_seed_order_and_unreachable_target`; original targets, operating limits and residuals retained with no accepted solution |
| Verify coupled reference samples | `test_coupling_measurements`; `dense_verification.py` exact reference and every-15-degree inputs; frozen scapula/patella and wrong-axis mutations |
| Verify continuity through the diagnostic domain | `verify_skeleton.py --dense`: <=0.01-beat samples, <=0.25-degree scalar driving steps, recorded <=0.02 H origin and <=5-degree orientation steps; no failure removal |
| Preserve thoracic attachments during motion | `test_thorax`; native mesh-ring endpoints/midpoints and sternal SC midsurface closure in every delivered sample; dense data-side cartilage checks and closed binding graph validation with negative cycle/cross-side/stale-point cases |
| Inspect a diagnostic fixture | `test_diagnostics` masks/base/hold/free/conflicting layers, mirror and terminal semantics; validated YAML descriptions/provenance; procedural layers disabled |
| Verify a complete squat | Seven independent matrix audit rows in `test_diagnostics`; measured 90-degree bottom, prescribed pelvis/lumbar/arms, actual pins/complete-mesh floor checks and loop metrics; human movement readability |
| Verify arm elevation without torso compensation | Independent action measurements at all delivered poses, 160-degree apex, source/actual root and frozen trunk, pins/floor and loop checks; human shoulder coordination judgement |
| Verify the alternating stepping cycle | `test_walking_dossier`; actual complete-sole apex metric, >=45-degree knee, half-open support events, mirrored opposing arms, fixed root, double support and loop checks; human stepping readability |
| Measure planted and rolling foot support | `test_diagnostics.test_half_open_events_and_rocker_terminal_state`; actual permanent heel/ball witness positions, target/sliding residuals, complete evaluated-mesh floor minima, rocker and floating foot sweeps |
| Verify samples from the same animation | `test_diagnostics.test_exact_sampling_contract` and `test_prepared_modes_refer_to_one_animation_and_exact_events`; rational timing and shared sample IDs; GIF cumulative duration metrics |
| Verify rendering stability and determinism | Direct per-sample camera/floor/light/render-setting measurements; exact decoded-pixel clean-pass comparison; fixed scene source and pinned actual Blender/GPU metadata |
| Review a completed implementation | All numeric/visual evidence linked in the pack. Independent clean rebuild and `review.md`, then explicit human visual acceptance; these gates cannot be inferred from passing tests |

The numeric verifier does not import solver/articulation routines in its
measurement path. It reconstructs actions from measured body matrices and
compares independently transcribed relationships. Geometry evidence comes from
Blender's evaluated dependency graph. Required inventories are checked so a
missing record cannot become a passing metric. Detailed per-sample metric files
include measured/expected values, units, tolerances, statuses and image links.


## Squat R3 additional scenarios

| Requirement/scenario | Executable evidence / human criterion |
|---|---|
| Whole-body mass metadata / Validate and scale the mass model | `test_balance`: closed-source mutations, fixed coefficient inventory, explicit normalization, mirror involution and three-stature scaling; source validation rejects unknown/nonfinite/missing/nonpositive/asymmetric/unresolved records |
| Whole-body mass metadata / Measure actual posed mass observations | Native `mass_points` from posed bone matrices; independent binding checks in `measure_balance` on every delivered frame; missing/forged point regressions |
| Squat / Verify a complete squat | Seven frozen R3 matrix rows in `test_diagnostics`; ankle20/pelvis25/lumbar10/knee90 bottom, flat pins and original rigidity/floor/loop limits; complete new native builds |
| Squat / Measure squat static balance independently | `test_balance` 401 beat samples at each stature, dense output retains every body frame, mass point, measured support anchor, check and full three-variant assessment with extrema and contextual render references, delivered native COM/support edge and perturbation metrics; whole-body regional weights include unrendered tissues; no dynamic claim |
| Squat / Reject the former squat despite planted feet | Data regression preserves valid pins and fails COM margin; actual Blender `former-squat` and `rearward-upper-body` faults fail `balance.reference_margin`; missing/forged/equalized mass/support regressions |
| Timing/render / COM/support inspection | Native render-pass evidence in `squat-balance.json`; six additional timed GIFs and separate fixed-crop front/side sheets alongside unannotated views; raw and derived pixel repeat comparisons |
| Human gate 2 | Human inspects thorax plus corrected squat and exercises; static mass-point margins do not prove anatomical accuracy or dynamic balance |
