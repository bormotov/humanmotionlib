# Developer native numeric checks

## Coordinate-space diagnosis — resolved

The early try65 and try69 runs exposed an actual world-space skinning mismatch: `0.2250002502 m` and `0.3181983223 m` at the first ankle-sweep sample. These failures are closed, not current native defects. The architect's exact matrix-chain audit established the modifier-local chain `M_obj^-1 · M_rig · P · B^-1 · M_rig^-1 · M_obj`; canonical world-reference positions are computed separately from the profile hierarchy and prepared world-space frames. The try70 implementation adopted these distinct oracles without changing the dossier, geometry, motion, root intent, or tolerances. The focused try73 build then passed native/reference vertex, root-placement, bone-frame, and floor checks. The full try70 matrix below completed successfully.

The old failed try65/try69 logs are no longer needed to diagnose the resolved issue; the error values and resolution are retained here. Their run roots and their now-obsolete harness/input roots were removed after checking that the try70/try73 results supersede them and that no other retained run consumes them. No links were followed. The corresponding old try60/try66 candidate wheel roots remain because retained host-suite logs cite those exact installed identities.

## Focused native ankle-sweep confirmation (candidate try70)

- Candidate wheel SHA-256 `72052555f15d502f567de45d8fa1bb9da808dedf86c5cc7633e156fd50447d37`; runtime manifest SHA-256 `0720c383b567a41776e36fdd31cf921bea6acd48e29f140d2d30cb0127bfaa4d`.
- H=1.50 m input `build/add-shared-body-characters_r1_dev_try-71_h150-input/input.json`, content seal `07c209c1cadd7411dbd61372001576d598493bb595037db654eb33451fae293b`, 21 ankle-sweep samples. Output `build/add-shared-body-characters_r1_dev_try-73_h150-native/`; Blender 5.2.2 LTS, IDs skeleton/male/female, no images, build mode.
- Independent audit: `build/add-shared-body-characters_r1_dev_try-73_h150-native/native-world-audit.json`. Maximum source-world DQ residual was `5.987890077413839e-7 m` (both surfaces below `1e-5H=1.5e-5 m`); root translation residual `5.960464483090178e-9 m`; 3,696 source/native bone-frame comparisons had maximum translation/basis residuals `8.926193569901235e-8 m` / `1.853748585745052e-7`. Native minimum Z was `0.1252637803554535 m`; source-world minimum Z was `0.1252639264983439 m`; both exceed the `-0.00015 m` bound.
- The generic collection verifier is not a verdict for this images-disabled construction-only output: it requires a render manifest, which that run intentionally does not emit. The native and independent numerical evidence above is retained separately.

## Full native generation matrix (historical generator try70)

All three statures were generated with the exact try70 wheel and manifest above. Each input contains the same 32 diagnostic IDs at BPM 60/120/180 (900 delivered samples), and the native build checks 60 sealed midpoint samples. Each invocation selected skeleton/male/female and completed successfully in Blender 5.2.2 LTS. This is a historical generator matrix, not a claim that try177 or a later candidate generated these outputs.

| Height | Input and seal | Native output | Render identity |
|---|---|---|---|
| 1.50 m | `build/add-shared-body-characters_r1_dev_try-74_all-h150-input/input.json`; seal `be4869f7ecec44d5bc3a48e96bb4abe2fb4af1659b34ebe28296b5f56f87002a` | `build/add-shared-body-characters_r1_dev_try-79_h150-native/` | `a59653e015ca4504bbad67c194212b54a63bce849473c8eb292eed30ce98da96` |
| 1.70 m | `build/add-shared-body-characters_r1_dev_try-76_h170-input/input.json`; seal `ec51bb34466c308a2a50e8e041cbbc3bf323a141ed5f132767e0c04fc1d8c3f5` | `build/add-shared-body-characters_r1_dev_try-80_h170-native/` | `d2170c3367c09be6fa5746901b09a3d2d62a184729d699d64b90676c430ec814` |
| 1.90 m | `build/add-shared-body-characters_r1_dev_try-78_h190-input/input.json`; seal `d27bcc58cd65681ea97bbe57b5b8b08660e4b632183f080ed4f8d73ec2564d17` | `build/add-shared-body-characters_r1_dev_try-81_h190-native/` | `f4b8b58116ff2a64cb97bd66035961d686b4d4c852ed2690e8da7c663ea7434a` |

The authoritative run index is `build/add-shared-body-characters_r1_dev_try-82_native-matrix/native-runs.json`. The outputs are dependencies of the anchored read-only verifier: H=1.50 report `build/add-shared-body-characters_r1_dev_try-140_numeric-audit/report.json`; H=1.70 and H=1.90 reports are in `build/add-shared-body-characters_r1_dev_try-141_numeric-audit/report.json`. All three have `numeric_status=pass`; male and female dense fixture summaries pass at each stature (409 dense samples per fixture/character). The anchored reports identify try70 as the generator and record the verifier identity separately. They do not replace current-candidate native checks or independent review.

## Focused current-candidate numeric report (try147)

`build/add-shared-body-characters_r1_dev_try-147_numeric-verification/report.json` covers 86 samples at H=1.70 and 549,843 metric records. Geometry, floor, sole, midpoint, and native-reference measurements in this scope pass. The aggregate is incomplete/fail because the focused input does not contain the complete fixture/tempo set. Its seven failed checks are coverage-only: `diagnostic_fixture_coverage`, `arm-raise.tempo_coverage`, `forefoot-rocker.tempo_coverage`, `neutral.tempo_coverage`, `rest.tempo_coverage`, `squat.tempo_coverage`, and `walking-in-place.tempo_coverage`. Do not count this as full three-stature acceptance.

## Current try177 construction and visual renders

Fresh try180 inputs were evaluated against try177 by native render-only-false no-images passes in try183:

| Height | Content seal | Samples | Render identity |
|---|---|---:|---|
| 1.50 m | `e560f00341092ed2fd8d838320b0a8084f72d190f8b1dcae364c2149b8c11088` | 18 | `03f19e9b74ea0e9a8db86b98ab604f9376bcd0a3250c9f359fccdd06d04f9138` |
| 1.70 m | `ab628c648b9ecda25e38fd11fda8e6c1ec951c7807affa57bdb6c8c0beddb1ed` | 171 | `1edadf1c9d2e6129888a0b6a014e94d46d90b8a97a6839d750dd8a9edfab8dde` |
| 1.90 m | `227657c4c944449bd5bc9a684daa3cab6e0d8b22a01921230746aa96ff830da6` | 18 | `61601da82a3efa97bf35051f1f63dda48142ce4c75b018daa58056a52454601d` |

Each wrote source and evaluated surface evidence for all three IDs. The now-removed try179 supervised visual pass completed eight native render operations, including clean-a/clean-b, default/explicit skeleton, male/female singleton, and H=1.50/H=1.90 stature passes; all receipts reported success. This exercised the managed-pass claim. Its first pack assembly exposed a marker lookup bug (`ankle.L/R` versus canonical profile IDs `talus.L/R`). That bug was resolved by later pack generation, including try247, which passed complete-pack validation. Try179 was superseded by later managed passes and removed during selective cleanup; it established render-operation success but was not a complete accepted pack or visual gate. Exact removal is recorded in `cleanup-inventory.md`.

The try174 consumer squat report is scoped to an older try168 candidate and is not current try177 evidence. A current identity-bound consumer check remains required if it is part of the final task criteria.
