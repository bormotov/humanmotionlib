# Independent review — add-shared-body-characters

## Pre-freeze audit — diagonal focused visual input

**Historical finding 9.4-PF1 (major; design §7, focused diagonal visual pack): corrected in the focused 17.2 host/synthetic review below, not yet verified with real Blender.** At the time of discovery, static inspection showed that the diagonal `review-pack` preflight called `verify_character_output` on each visual input and required `numeric_status == pass` (`review_pack.py` around 1625–1631). For a surface, that verifier required fixture coverage for all diagnostics listed in the prepared source (`character_verification.py` around 239–247 and 1314–1318); `_prepare_sources` retained all canonical diagnostics in the source even when a focused fixture subset was selected (`prepare_skeleton.py` around 25–47). Consequently a focused male/female input was incomplete at this boundary. The same input was passed without filtering into each of two managed render passes (`review_pack.py` around 1762–1769), so using a complete numeric input rendered its complete sample set twice rather than the focused visual set. This historical finding was source-level evidence, not an executed Blender result. Subsequent correction and exact candidate scope are recorded below; do not relabel earlier synthetic evidence.

### Focused retry interim evidence, not final verdict

Reviewer installed preliminary wheel SHA-256 `bd28a7f04c246aad73135f6caee190374a7d50ddcaf95fc4e87b85a57cd873b5` in fresh `build/add-shared-body-characters_r10_reviewer_try-2_focus-preflight-check/environment`; the uv-created interpreter, dependency origins, `.pth`, cache and passing `uv pip check` are recorded in that run's `environment-preflight.json`. Seven focused tests passed in 612.050 seconds, including the actual `_preflight_diagonal_inputs` route on synthetic canonical eleven-fixture/BPM90 data, an unchanged positive and a coherent altered male surface/receipt negative; native surface DQ and dense kernels ran without replacement. `check_blender_version` and skeletal `verify_backend` were mocked, and a pass-through verifier wrapper captured reports; this is not an unmocked Blender or complete real-native check. The test source was last modified before the run began, but was subsequently changed during execution; no immutable test snapshot was captured before import, so this run's loaded test bytes cannot be proven byte-for-byte from a preserved snapshot. Its outcome remains scoped to the preliminary wheel and is not final acceptance of a later candidate.

A separate source inspection found a report-label defect in this preliminary wheel: the focused `verification_scope` was overwritten later by `selected-character-numeric-leaf`, which the pack propagated. A corrected package and identity-bound review are pending. The earlier extra sampling-fixture key failure was identified on a still earlier preliminary wheel and developer reports its correction; neither preliminary result is a final 17.2 verdict.

### Task 17.2 independent focused review — corrected candidate

**Verdict: PASS WITH NOTES in host/synthetic scope.** Reviewer installed exact developer wheel SHA-256 `1f56fb6929d9b7663cb7b0d8fb391f9c1f5a631f99354422bb57c859e14d7a35` in a fresh uv-created Python 3.14.6 environment, with locked dependency origins inside that environment, `_virtualenv.pth` only, writable run-local cache, `uv pip check` pass and no unexpected external import paths. Installed `character_verification.py` SHA-256 `d31c3bfbbd41b549d7670d915b00c548b155f860521564f8c076e30fde0eedf6` and `review_pack.py` SHA-256 `b684d3a664b0519352c8a7d5d8d4622f998955fb76b37c23bb8788287d9bb239` matched the current corresponding source files. Exact wheel and dependency hashes/origins were checked before tests.

An independently owned immutable test snapshot was taken before running: `test_focused_visual_preflight.py` SHA-256 `9efe698675a10241b7f047b2f2a71461bd7230e0df6cd15ee97e15807759b7a3`, `test_character_verification.py` `aed3ec5d05c76f05d4de7c7ca4e5765821f029782c7fe079ff1dd8dfc152ae04`, `test_selected_numeric_fixture.py` `9a0a144eca5a463530d3bce06a9ddaa41fcde512a410c146e85c925a596bf922`, `run_roots.py` `16255100fe8aae2b969ea8b7c1521e5476e1c1c0dc0140a8c88c6f149c23e8eb`; post-test hashes matched. Imports of those tests resolved from this snapshot and imports of `humanmotionlib` from the installed wheel.

Eight tests passed in 594.310 seconds: canonical focused BPM90 sample coverage and missing/extra sample/fixture/tempo controls; actual diagonal `_preflight_diagonal_inputs` positive using three canonical synthetic pair inputs and unchanged DQ/dense verifier, then a coherent male vertex/receipt mutation reaching a `surface-evidence` reported-DQ-residual failure before output allocation; an unexpected midpoint rejection at BPM90, a separate nonempty BPM60 midpoint-kernel positive, exact focused dense-grid membership, one-event dense sole/contact positive and lifted-foot failure, and top-level focused verification-scope label regression. The preflight test uses synthetic artifacts and mocks Blender version and skeletal `verify_backend` while a pass-through wrapper captures the real character-verifier reports. It does not execute Blender or prove native skeleton measurements. The coherent DQ test asserts the failure code and diagnostic class; exact measured residual/context values were not independently logged by this test. A separate independent helper control confirmed an extra-only sampling fixture that passed preliminary bdf7 is rejected by corrected 1f56.

Five additional installed visual-pack tests passed in 83.656 seconds: synthetic positive CLI/assembler report, focused preflight identity/selection/extra-sampling negative controls, overlapping input/output rejection, explicit `--characters skeleton` rejection in diagonal mode, and media/skeleton-mode completeness. The copied test's source loader was replaced solely with an installed-package import; original test SHA-256 `d15df8588baec2c813552ae5a252c6f3cb05d386b7180f26d081878c72cb5ad3`, adapted test SHA-256 `012d40dc70b12c7a5986072807f567203bccdfb2b2112c6aff89a7061ce40c37`. These tests use mocks in the synthetic assembler and preflight controls; they do not replace the real scoped dense preflight above or 9.4.

The pre-freeze focused-input finding 9.4-PF1, the preliminary extra sampling-fixture key failure and focused report-label defect are corrected in this scoped review. Full 32-fixture/default-tempo numeric acceptance, process-supervised Blender constructions/renders, source/package/API/CLI parity, visual pack and human Gate 2 remain unassessed and belong to 9.4/8.6. No full character matrix or Blender was run. Reviewer cleanup remains pending until owner process and containment checks and removal are recorded below.

Cleanup attempt: reviewer confirmed no matching test processes, checked all three reviewer-owned roots are nonsymlink direct children of the resolved build directory, and measured regular-file bytes without traversing links: try-1 `42,086,104`, try-2 `43,395,672`, try-3 `43,032,021`. The requested removal of these three exact roots was interrupted; completion is not established. A subsequent read-only check found each root still present with the same regular-file byte count, but this does not exclude partial removal of other entries. No retry has been issued; cleanup remains pending.

Cleanup completion: the orchestrator subsequently removed those three exact roots under approved escalation (exit 0), and the reviewer confirmed all three absent without following links. The recorded byte counts are the inventory before either removal attempt; any division between the interrupted and completed attempts is unknown. No cleanup failure remains pending for these reviewer-owned roots. The independent 17.2 verdict remains **PASS WITH NOTES** for the host/synthetic scope above; 9.4 and Human Gate 2 remain pending.

### Updated pre-freeze reviewer audit — task 9.4

The human-approved diagonal consists only of skeleton H1.50, male H1.70 and female H1.90; it does not constitute a full character/stature matrix and is compatible with the reviewer's prohibition on starting that full matrix. Recorded R6 early acceptance remains in `approvals.md`; it does not replace the final human decision. The focused 17.2 checks above do not establish real Blender or 9.4 acceptance.

Read-only candidate inspection independently rehashed wheel SHA-256 `1f56fb6929d9b7663cb7b0d8fb391f9c1f5a631f99354422bb57c859e14d7a35` and its runtime manifest SHA-256 `da4d59d70d3f71f5138a7ae9d3311680be974ed8f9be34b71841ef898ad602a0`. All 50 implementation and 64 resource bytes in the wheel match their manifest hashes; all 49 existing checkout implementation sources and all 64 checkout resources match those hashes. `_version.py` is generated and has no checkout source file. This is not an independent rebuild or a full repository/test snapshot identity; those remain required for 9.4. Candidate identity must include the actual tests used, including the untracked focused test source.

All 38 explicitly authorized task 9.4 reviewer roots were checked read-only and absent, including symlink entries; their common build parent resolved inside the workspace. Available space was approximately 435 GiB at this audit, and `blender` resolves via `/Users/bormotov/.local/bin/blender` to `/Applications/Blender.app/Contents/MacOS/Blender`; the installed backend version/build has not yet been established here. Recheck root freshness, space, process activity and containment immediately before allocation, and perform same-privilege owned-child process-visibility and pinned backend preflight before supervised execution. These observations do not freeze the candidate or authorize a full matrix.

The approved producer graph separates full diagnostic numeric constructions from focused visual preparations and evaluated inputs. It also provides separate default skeleton evaluation and source/API/CLI parity outputs; do not infer separate invocation provenance from a normalized selection or one untraced output. The review still requires independent source/package and installed closure, host/source and negative controls, three selected full numeric leaves plus aggregate, three selected consumer checks, explicit/default skeleton geometry comparison, focused two-pass pair renders, fixed scene and decoded-pixel repeatability, provenance and the standalone human pack. No earlier full-matrix or synthetic result is relabeled. `cleanup_pending` remains failure/pending ownership, not success. No Blender/native, final verdict or Gate 2 decision has been obtained in this audit.

### Task 9.4 independent execution checkpoint

Independent reviewer candidate is frozen wheel SHA-256 `1f56fb6929d9b7663cb7b0d8fb391f9c1f5a631f99354422bb57c859e14d7a35`, source snapshot v4 aggregate `fc193e52c9eebc98237e92beabb9b427f6e96dc99d3655533f3bc1aec48c9afc`, and separately identified execution plan v6 aggregate `1874d5259ef0e878bff026ae17eb18a87cedcc3d405f92b263fad07bc61aaf53`. Reviewer direct wheel and sdist-rebuilt wheel matched all 123 non-RECORD frozen-wheel entries; source snapshot files and path membership remained unchanged after build. Evidence is in `build/add-shared-body-characters_r10_reviewer_try-4_candidate/package-closure.json` and the reviewer source v4 inventory. The exact frozen wheel and locked dependencies were installed with uv in a new reviewer environment; interpreter/origins/`.pth`/cache and passing `uv pip check` are recorded in its `environment-preflight.json`.

Owned-child process visibility preflight was performed by the orchestrator under the same elevated privilege: PID/PGID 91403, `ps` exit 0 and child reaped -15. The subsequent supervised `version-probe` receipt `53f5db383ca046dba66e6db6124074f2` reports succeeded/exit 0, Blender 5.2.2 LTS build `d13f752e3b9c`, Darwin-arm64 and the frozen runtime-manifest identity. This is a backend version probe, not a construction or render.

Independent installed host suite is running from reviewer snapshot tests with checkout source-root binding and output under `build/add-shared-body-characters_r10_reviewer_try-1_host-check/`, unified session `10527`, PID `93193` at launch. Its `host.log` has already recorded an ERROR in `test_custom_render_dir_uses_shared_complete_receipt_contract` and a FAIL in `test_shared_arm_radius_propagates_to_both_appearances_only`; tracebacks and classification await suite completion. The source-loader behavior of the review-pack test means a full-suite result must not automatically be labeled exclusively installed-import evidence. Snapshot/checkout identity needs rechecking after the run. No independent native numeric, real visual pack or human verdict has yet been established.

## Task 16.2 independent diagonal review — candidate wheel 5, 2026-11-03

### Corrected candidate retry — 2026-11-03

**Verdict: PASS WITH NOTES for task 16.2's focused host/synthetic scope.** Findings 16-R1, 16-R2 and 16-R3 below are corrected for the exercised scope. Wheel SHA-256 `714bbef1f79b4d9546e4f6c2d290f22b281e6f8d59d394ffb042aea363238740`; independently queried installed runtime manifest SHA-256 `ea606a3632662ca024709cc54e6eecf6002077e78cac182e1970d4ccc5a457b9`. Source and installed module hashes matched: `review_pack.py` `7cb132ed37596f5cec77a6b322c2c2657d4745aa89e83f211fcaf421d9f4841a`, `verify_skeleton.py` `79874fd22d33d799d42495d24858c6dfc27dd10ccf0cba03f30fb25cf1b92364`, `character_verification.py` `f2bb60dadd60706b82fe912b6ec0b9e675553ca5217aca9d05f0ecbef65c9c33`. Test hashes: `test_character_review_pack.py` `db536123b8bf7b56252d37a91a4b5f64d514439817745de96343c0fe3683e0f4`, `test_selected_numeric_fixture.py` `98bc22e06dd1e8078c39e166892203dc879aadc445ced035eea9c11e032283bd`. These hashes were rechecked after tests.

Fresh reviewer-owned `build/add-shared-body-characters_r9_reviewer_try-3_diagonal-check/` contained a uv-created CPython 3.14.6 environment and writable uv cache. Exact wheel and locked dependencies were installed with `uv pip`; `uv pip check` passed. Interpreter and `sys.prefix` were in that environment; humanmotionlib and dependencies imported from its site-packages, standard library came from the pinned interpreter, and the only `.pth` was `_virtualenv.pth` importing `_virtualenv`. The checkout working directory appeared on `sys.path` for test modules. Dependency versions: PyYAML 6.0.3, jsonschema 4.26.0, Pillow 12.3.0, referencing 0.37.0, attrs 26.1.0, rpds-py 2026.9.1, jsonschema-specifications 2025.9.1. Sandbox dependency resolution failed DNS, followed by successful installation with approved network access. No process-supervision test was run.

In a separate interpreter, four installed numeric tests passed in 297.413 s: synthetic full default-BPM aggregate and selected skeleton positives, BPM90-only aggregate rejection, and neutral/rest-only skeleton leaf rejection. Five installed review-pack tests passed in 36.797 s after substituting only their source-module loader with an installed-package import: explicit `--characters skeleton` rejection, synthetic assembler/report positive, pair parser/coverage controls, and input preflight positive plus wrong height, stale, failed, source/package/backend/sampling negatives. The assembler mocks renders and numeric leaves; aggregate positives use synthetic passing leaf reports; the skeleton fixture has synthetic receipt and mocked backend measurement. No Blender, real native diagonal or visual acceptance was performed. Independent real-backend review and Human Gate 2 remain open under 9.4/8.6.

The previous reviewer try-1 remains untouched. Try-2 is retained as explicitly required evidence for the earlier findings; no prior result is relabeled. Try-3 cleanup: before removal the resolved root was a nonsymlink direct child of workspace `build/`, process inspection found no matching active process, and regular files totaled 42,941,258 bytes. Cleanup completion is recorded below after removal.

Try-3 cleanup completed: the first removal request was interrupted and may have partially removed files; the orchestrator subsequently removed the same exact root successfully. Reviewer verified the root is absent. The 42,941,258 regular-file bytes are the original pre-removal inventory, not a measured byte count for either individual removal attempt. No cleanup failure remains pending for try-3; try-2 remains retained under the task's explicit evidence instruction, and try-1 was not touched. The focused verdict remains **PASS WITH NOTES** as stated above.

**Verdict: FAIL; corrections and renewed exact-candidate review are required.** Candidate wheel SHA-256 `bac0ae5d6583ac3976b68fca2f873a8ff1f2afe4546e0278d2c02c5cf450fc87`; source/installed `review_pack.py` SHA-256 `39ba7df3c7c426eaae92b0aa7026246340db8a017831dfbb609e5f2d02ec6d62` and `verify_skeleton.py` SHA-256 `a206a06053d80140f5a91f2f6405b230562f157c0526385288fb539d11200025`. Test source hashes: `test_character_review_pack.py` `c93093ac018aee1a654143a9a1632aff7daa28f47bb2c15ed41be065991b0bd5`, `test_selected_numeric_fixture.py` `1f6daf43178215b262cb350b2b1a1ef474c461f0c20aaf15e24fae8ac9157295`.

| ID | Severity | Requirement and scenario | Evidence and suggested direction |
|---|---|---|---|
| 16-R1 | Major | Design §7, diagonal numeric leaf: full 32 diagnostics and default tempos for each approved pair | Exact installed `test_diagonal_skeleton_leaf_cli_uses_real_scoped_numeric_verifier` prepares only neutral/rest and returns successful leaf/exit 0. Skeleton branch of `verify_character_output` sets `numeric_status=pass` without requiring full fixture/tempo coverage. A scoped positive transform result must not be reported as complete required numeric leaf; retain honest incomplete reporting and test missing coverage. |
| 16-R2 | Major | Design §7, exact diagonal scope: BPM60/120/180 required separately for each pair | In an independent host-only control, three real canonical preparations using only BPM90 plus synthetic passing leaf reports yielded `_diagonal_numeric_aggregate` status `pass`, no failures; observed BPM set was `[90]`. Comparing sampling among pairs is insufficient to establish required tempo membership. Require full default sampling and test a valid positive and equally incomplete matching inputs. No actual native leaf is claimed by this synthetic control. |
| 16-R3 | Minor | Design §7, diagonal review-pack rejects mixed diagonal/full-character options before output/render | Exact installed CLI with `--acceptance-scope diagonal-v1 --characters skeleton` and three diagonal operands bypassed the mixed-option guard and reached missing-input validation; explicitly supplying the default-valued full-mode selector must still be distinguished from omitting it. No output or render was created in this control. |

The reviewer independently installed the exact wheel in a fresh uv-created Python 3.14.6 environment with locked dependencies under `build/add-shared-body-characters_r9_reviewer_try-2_diagonal-check/`, writable cache in that root, and `uv pip check` passed. Interpreter, prefix, dependency/module origins and versions were inspected: package and dependencies resolve inside the reviewer environment, standard library under CPython, only `_virtualenv.pth` is present. `sys.path` also contains the checkout current directory, used for test modules. No process-supervision tests or Blender were launched.

Four diagonal pack tests passed against the installed `review_pack` by replacing only their source-loader harness with the installed import; three diagonal numeric tests passed in a separate clean interpreter against installed package. The pack controls exercise actual synthetic assembly/report and preflight with mocked managed render and numeric leaves; numeric aggregate positive also uses synthetic passing leaves, whereas the partial skeleton test exercises the actual selected numeric verifier with a synthetic receipt and mocked backend measurement. These results are scoped host evidence, not native/render acceptance. An earlier combined 7-test pass loaded source modules because the pack test changes `humanmotionlib.__path__`; it is not represented as installed-package evidence. No visual approval is implied. The initial reviewer try-1 belongs to another reviewer and was not touched; try-2 is retained pending correction and identity-aware review/cleanup.

## Task 15.2 independent runtime review — 2026-11-03

**Verdict: PASS WITH NOTES for the focused process-supervision scope.** This is not a full character, native, render or visual verdict. The reviewed installed wheel SHA-256 was `6274dabdd72dba7fee0bc50ba50da11367813327ff2040ce39fbc05289f09ded`; source and installed `runtime.py` SHA-256 both `d31ca8203cf9a7ce71c9140b060601083901eabf229ec53f43ec2dd222271605`; `tests/test_runtime.py` SHA-256 `9c0a1632294928059776e86d459b63835daef902e9cd3ce1c4f53058eb536f3f`. Rechecked hashes after testing were unchanged. The supplied package manifest identity was `09aa0c7e69239ab911ca7037d1f9bf69907d694849700aee604252483d7c1117`; this focused review verified runtime source/wheel contents, not independently the full package manifest closure.

Reviewer created a fresh uv environment under `build/add-shared-body-characters_r7_reviewer_try-1_runtime-check/`, installed the exact wheel and locked dependencies via `uv pip`, and ran `uv pip check` successfully. CPython 3.14.6 interpreter and prefix resolved inside this environment; humanmotionlib/runtime, PyYAML 6.0.3, jsonschema 4.26.0, Pillow 12.3.0, referencing 0.37.0, attrs 26.1.0 and rpds-py 2026.9.1 imported from its site-packages. `sys.path` included the checkout working directory and the interpreter's standard-library paths but no other package environment; the sole `.pth` was `_virtualenv.pth` importing `_virtualenv`. Writable uv cache was within this reviewer root. Network installation initially failed in the sandbox, then succeeded with approved elevated access. Sandbox owned-child process inspection failed with `PermissionError`; under the privileges used for the tests an owned child PID/PGID was visible via `ps` and was terminated and reaped (`-15`). The initially spawned sandbox child had a bounded 20-second lifetime; subsequent process inspection found no matching reviewer processes.

The exact installed candidate ran `tests.test_runtime` under the same elevated process-visibility privileges: **26/26 passed in 23.263 s**. This covers zero/nonzero exits, late interruption after reap, controlled group-call interception, TERM/KILL-before-reap ordering, timeout with a resistant descendant and unrelated sentinel, cancellation, missing/spawn failure, and output/ownership controls. Independently, a live own-session sentinel was used as the simulated reused saved PGID with a reaped-child double: `_cleanup_owned_group` returned `not-attempted-after-reap`, the instrumented `killpg` call count was zero, the sentinel remained alive, and it was then terminated/reaped. This is controlled simulation, not proof of actual OS identifier reuse. Timeout/cancellation tests accept either safely confirmed or `cleanup_pending`; this review does not assert descendant termination on every platform. Normal completion deliberately does not inspect or clean independently surviving descendants.

No Blender, full matrix, character verification or visual judgment was run. No new external materials were used. A no-follow count before cleanup found 42,194,154 regular-file bytes in the sole reviewer-owned root; root resolved inside workspace build and was not a symlink. Process inspection found no reviewer-root processes. Cleanup status is recorded below after the removal attempt.

Reviewer cleanup completed: removed `build/add-shared-body-characters_r7_reviewer_try-1_runtime-check/` (42,194,154 regular-file bytes before removal); its absence was verified. No cleanup failures remain in this reviewer scope. No other run was touched.

## Task 14.1 focused independent review — 2026-11-03

**Superseding focused recheck:** after the original review, optional historical comparisons were amended so valid evidence with partial overlap or changed geometry/pixels reports its own incomplete/fail status without gating the current visual pack. Independent rerun passed **24/24** focused tests, including actual synthetic pack assembly with a preflighted baseline record, partial views and differing pixels, plus malformed/stale evidence controls. The synthetic preflight record is not a real historical render. Current source SHA-256 `3c75eb1647fcc7c8d19753a48277eee30281d8c6c0f4c366deeb6a243d67d6ad`; tests SHA-256 `7472f57b130e8d0d3b842654ab14feda7e220517699dde23ed698214f9a09641`. Reviewer run `build/add-shared-body-characters_r7_reviewer_try-2_check/` was empty after transient tests and removed (0 bytes); no cleanup failure. Verdict remains **PASS WITH NOTES**, limited to this host/source and controlled-fixture scope. Prior hashes and test count below are historical, not evidence for these amended bytes. Full independent review and human Gate 2 remain pending.

**Verdict: PASS WITH NOTES for the bounded host/source scope only.** The historical baseline is optional for visual-pack completeness; current mode comparisons, stature, fixture coverage, decoded repeatability and GIF timing remain required. The output identifies its scope as `visual-comparison-pack`, marks full change acceptance `not-assessed`, and lists external source/package, API/CLI, numerical, review and human gates. Supplied historical evidence remains subject to preflight. The primary evaluated-candidate preflight now runs before output allocation or render, independently of the optional baseline.

Reviewed source SHA-256: `src/humanmotionlib/review_pack.py` `b43cae767f800efa95c345ca3abf17c0e74bb922c6cf62dcd86cf100aa5a2265`; `tests/test_character_review_pack.py` `bccaf0533a4a011cbc7e8b6bf8331426d8e744c6419afdbf6d2b2e8022e3035a`. Independent focused execution using the existing project environment and reviewer-owned temporary root passed **22/22**. It includes a controlled synthetic-image assembly without baseline and its actual output reports, missing stature/mode, failed mode, malformed historical evidence and stale prepared/package identities. A separate reviewer-authored check passed positive, missing, duplicate and failed current-mode rows. An initial direct source import failed because checkout lacks generated `_version.py`; the successful run used the existing installed package with the test's explicit source module loading, and is not installed-package acceptance. No Blender, process-supervision, full numeric matrix or visual acceptance was run. The controlled assembly mocks some coverage/stature helpers and is not an independently rendered final pack; task 9.4 and Human Gate 2 remain pending.

Reviewer-owned `build/add-shared-body-characters_r7_reviewer_try-1_check/` held only transient temporary test files; after tests it was empty and removed (0 retained bytes). No cleanup failures remain in this focused scope. No external materials were used for this review. No findings within this bounded scope.

## Final independent assessment — 2026-10-28

**Verdict: PASS WITH NOTES for the independently measured technical scope; human visual Gate 2 is pending.** This verdict does not approve visual correctness or make an incomplete consumer report pass. The requirements/scenarios and their check classes are enumerated in the verification checklist below; the dated continuation is historical evidence, not the current status. The identity-bound evidence below is for candidate try294 only.

- Submitted wheel SHA-256 `3aa76e1b2aab46963eb2c168c917d8cf85817557d6d2ef5307a99175e1d13fbd`; runtime manifest SHA-256 `7f21ef2ff07c9ebf3ef63e08bd8269dc5a9720de34380c6996a833ee80449454`. The wheel hash was independently rechecked in `build/add-shared-body-characters_r1_reviewer_try-14_final-check/standalone-identity-audit.json`; the package rebuild, byte closure and manifest checks are in reviewer try11/try12 evidence below. Documentation-only changes after freezing are not represented as a new package identity.
- Installed source/schema validation returned `valid-sources`: 180 structures, 67 actions, 3 placements and 32 diagnostic fixtures. Host tests passed 380 with 7 explicit installed-harness skips; those 7 passed separately in the installed harness. See `build/add-shared-body-characters_r1_reviewer_try-12_host-check/`.
- Independent installed verifier on reviewer-owned three-height constructions returned a **complete** aggregate numeric pass: 5,714,431 measurements, 32 diagnostics at each of H=1.50, 1.70, 1.90 m, 60/60 native midpoints per body and no matrix failures. Evidence: `build/add-shared-body-characters_r1_reviewer_try-12_numeric-matrix/metrics.json` and scalar summary in reviewer try12 host-check. Worst observed native residual 1.06649e-6 m, minimum surface floor -1.68086e-7 m and maximum sole distance 1.66521e-7 m; strictest H=1.50 m limits are 1.5e-5, -1.5e-4 and 1.5e-3 m respectively. See the detailed result below for scope, dense coverage, positive controls and provenance of the uv-only environment.
- The separate consumer-motion report `build/add-shared-body-characters_r1_reviewer_try-12_consumer-check/metrics.json` is **not an aggregate pass**: its top-level status and numeric status are `fail`, with failed diagnostic fixture coverage (32 missing) and tempo coverage (one observed tempo); the character matrix is incomplete because H=1.50 and 1.90 m are absent. All 17 supplied H=1.70 samples pass their scoped sample checks and native/dense character checks. Rendering is `not-run`, visual is `not-assessed`. The complete three-height diagnostic aggregate above is a different report; it does not change the consumer report's status. This limited custom-input result is consistent with the consumer-specific verification scope and is not evidence of complete diagnostic coverage.
- Independent visual packs are `build/add-shared-body-characters_r1_reviewer_try-12_visual-pack/index.html` and the distinct try13 pack. All 1,044 cross-pack clean images matched in decoded RGBA; camera/floor/light scene properties matched across three stature scenes. A new independent parser rechecked the primary standalone pack: 12 HTML pages, 1,377 local links and no missing or escaping targets; output in reviewer try14 `standalone-identity-audit.json`. The fixed scene audit compares configured world matrices and settings; pixel comparisons are separate evidence.
- Provenance/clearance: the reviewer inventory resolved 770 provenance records and 14 inherited materials. See reviewer try5 `clearance-review.md` for the checked scopes, conditions and limitations of live retrieval; no additional external surface reference was used. Kudzia and Kasahara are attributed by author/title/DOI in `THIRD-PARTY-NOTICES.md`, although their literal material IDs do not occur there. Some unchanged publishers could not be re-fetched live; the audit does not claim otherwise.

### Final reviewer-owned cleanup record

The original owner checked its own obsolete runs and removed these six whole roots (prefix `build/add-shared-body-characters_r1_reviewer_`), totaling **4,200,255,633 regular-file bytes**, counted before the first deletion pass:

| Root suffix | Regular bytes |
|---|---:|
| `try-9_numeric-h150` | 4,042,845,369 |
| `try-10_candidate-check` | 23,301,479 |
| `try-10_fault-build` | 27,098,156 |
| `try-10_fault-check` | 105,287,764 |
| `try-10_fault-input` | 1,452,283 |
| `try-10_host-check` | 270,582 |

Before removal there were no matching active processes and no inbound symlinks from outside these roots; four symlinks were internal to an obsolete environment/cache. The first pass encountered self-imposed read-only environment directories; the owner restored permissions only inside its own root and completed removal. A post-removal no-follow scan found zero external inbound symlinks and confirmed all six roots absent. The owner checked references and retained the historical outcomes in this record, with final-candidate replacements available. Inventory and completion record: `build/add-shared-body-characters_r1_reviewer_try-12_host-check/superseded-runs-inventory.json` and `superseded-cleanup-result.json`. No cleanup remains pending from this operation.

The owner of try6–8 additionally removed three obsolete try251 visual preparations (same reviewer prefix): `try-8_visual-input-h150` 4,232,909 bytes, `try-8_visual-input-h170` 27,071,130 bytes and `try-8_visual-input-h190` 4,218,480 bytes, totaling **35,522,519 regular-file bytes**. Before removal no matching reviewer try5–8 or related Blender/verifier process was observed, internal symlinks were zero, and a no-follow scan found zero inbound symlinks. After removal all three roots were absent and inbound links remained zero; no review.md text pointed to those exact removed paths. Owner retained try5 inputs/host as dependencies of try6, try6 numeric/visual/aggregate for the documented R3 diagnostic and historical evidence, try7 for diagnostic freeze, and try8 candidate/numeric inputs for `independent-matrix.json` and the scoped audit. No pending cleanup was reported for those three removed roots.

The original owner independently inventoried its 20 early try1–5 roots, totaling 1,350,686,445 regular-file bytes, and removed **0 roots / 0 bytes** because each has a recorded dependency or protected diagnostic purpose. Before/after inventories match; a no-follow build-wide scan found no external inbound symlinks and process inspection found no matching processes before or after. Exact per-root reasons and revisit triggers, inventories and procedure: `build/add-shared-body-characters_r1_reviewer_try-15_early-cleanup/cleanup-result.json`, `inventory-before.json`, `inventory-after.json` and `audit.py`. The try1 check and try2/3 preserve original R1/R2 evidence; try4 is linked by try6 outcomes; try5 host contains the cited current source-clearance review and its inputs are linked by try6 outcomes. The try1 stature inputs are linked from the retained try1 check's `numeric-inputs.json`; retaining those inputs does not promote them to native acceptance evidence. The owner reported no pending cleanup in its scope.

Retained: reviewer try11 native/input/package/fault results, try12 environment/host/numeric/consumer and visual pack, try13 independent comparison pack, and reviewer try14 standalone link/identity audit: these are required for frozen identity, reproducibility, diagnostics or the pending human visual gate. The protected historical baseline and other agents' roots were not removed. Earlier partial cleanups and byte counts are recorded chronologically below; they do not overlap the six roots above. Reviewer-owned dependency-aware cleanup is complete for the inspected owners; retained roots have concrete evidence dependencies or revisit triggers, and no failed or interrupted cleanup remains pending in their scopes. Any developer-owned cleanup remains that owner's responsibility and is not represented as completed by this review.

### Findings disposition

| ID | Original severity / requirement and scenario | Final independent disposition and evidence |
|---|---|---|
| R1 | Major — Surface variants reuse one construction and binding contract / Verify surface sharing | Corrected; shared template and bounded appearance differences checked on try294; host and complete numeric evidence above. |
| R2 | Major — Characters are first-class selectable library outputs / Select each character independently | Corrected; skeleton-only construction, selection and missing surface collection audit pass on try294. |
| R3 | Major — Authored appearance has a frozen testable dossier / Measure and visually identify the authored characters | Corrected numeric stature scaling; independent complete three-height aggregate passes. Visual identification remains a human decision. |
| R4 | Minor — Public generation API documentation and supported construction modes | Corrected in try294; installed host/API mode coverage passed. |
| R5 | Major — Supporting surfaces preserve contact and floor constraints / Check the sole beyond a rest-pose appearance | Corrected diagnostics reproduced using independent synthetic topology, stale, floor and sole faults; matching unmodified control exists in the full try294 aggregate. Synthetic failures are not claims about accepted native output. |

No unresolved measured technical finding is asserted above. The checklist's **H** parts are unverified until the human reviews the pack. Suggested visual review: inspect neutral front/side silhouettes, shoulder/waist/hip and joint close-ups, squat and walking GIF/onion-skin transitions, forefoot rocker and sole contact, and the three-stature comparisons. The reviewer observed subtle surface differences and no obvious fixed-scene shift at the displayed scale; the small figures require zoomed inspection and this observation is not visual approval.

## Historical final-candidate continuation — reviewer try9 onward

### Corrected package try294 — chronological review record

The reviewer independently rebuilt frozen try294 (submitted wheel SHA-256
`3aa76e1b2aab46963eb2c168c917d8cf85817557d6d2ef5307a99175e1d13fbd`,
runtime manifest `7f21ef2ff07c9ebf3ef63e08bd8269dc5a9720de34380c6996a833ee80449454`):
direct/sdist/rebuilt logical closure matched all 116 files and canonical
sources in `build/add-shared-body-characters_r1_reviewer_try-11_candidate-check/`.
Separate reviewer full inputs at all three heights each contain 900 samples;
focused visual inputs are independently prepared (171 at H170, 18 each at
H150 and H190). A fresh neutral-only supervised build was used to rerun four
synthetic full-verifier diagnostic faults in
`build/add-shared-body-characters_r1_reviewer_try-11_fault-check/`: topology,
stale request, floor and detached sole all produced the required context. The
floor case measured -0.001000089 m versus -0.00017 m; the sole case measured
0.009999925 m versus 0.0017 m. These are intentionally synthetic cases with
consistent test receipt inventories, not accepted native output. The full
independent H150 native run is in progress; the remaining numeric, host,
visual and human checks are pending.

The H150 native run subsequently completed with supervised `succeeded`, 900
delivered samples and 60 midpoint samples in
`build/add-shared-body-characters_r1_reviewer_try-11_numeric-h150/`. A fresh
independent H170 build has started. This remains a construction-only result;
numeric, complete matrix, visual and human checks are not yet established.

The reviewer subsequently completed the independent H170 and H190 native
construction runs under `..._reviewer_try-11_numeric-h170/` and
`..._reviewer_try-11_numeric-h190/`. Each supervised build receipt is
`succeeded`, exit 0, with output validation `pass`; all three each delivered
900 samples and 60 native midpoints. They used the reviewer try11 venv,
created with `uv venv` and with the reviewer-built wheel installed by uv;
its dependencies were copied with byte-hash verification from the existing
environment. They remain construction results, not numeric acceptance.

The human subsequently requested that newly created environments be created
and populated with uv without copying. The new separate
`build/add-shared-body-characters_r1_reviewer_try-12_environment/venv/` was
created with `uv venv`, independently rebuilt wheel installed with `uv pip`,
and all seven locked dependencies installed with `uv pip --offline` from the
existing uv cache. `uv pip check` passed eight packages and runtime integrity
confirmed manifest `7f21ef2ff07c9ebf3ef63e08bd8269dc5a9720de34380c6996a833ee80449454`.
All imported package and dependency origins resolve inside this new venv.
The 378 non-pycache files across HML and seven dependency trees were compared
with try11: zero differences. No earlier result or receipt was reassigned to
the new environment. Future independent host/numeric/visual checks will use
the uv-only environment; numeric, visual and human verdicts remain pending.

The independent full host suite on the uv-only try12 environment completed
with 380 tests, zero failures/errors and seven explicit installed-harness
skips in 1,034.93 s; the frozen source snapshot remained unchanged. The seven
installed-only checks passed separately 7/7 in the reviewer-owned decoy
workspace. Independent source/schema/nested provenance inventory passed for
14 inherited material references and 770 provenance records. Evidence:
`build/add-shared-body-characters_r1_reviewer_try-12_host-check/host-tests.json`,
`installed-tests.json`, `source-provenance.json`, and accompanying logs.
These are host/package results, not native, visual or human acceptance.

The independently built wheel contains 124 files: 116 under the
`humanmotionlib/` runtime tree and eight dist-info files (including RECORD).
The runtime tree comprises 50 Python implementation files, 64 canonical
resources and two runtime metadata files. This matches the developer's
independent 124/116/50/64 inventory; archive byte hashes need not match
because of build metadata.

### Independent three-stature numeric matrix — try294

The reviewer ran the ordinary installed `verify-skeleton --numeric-only`
entry point with `--action-coverage --dense-floor --stature-builds` on its own
three complete try11 native builds. The exact report is
`build/add-shared-body-characters_r1_reviewer_try-12_numeric-matrix/metrics.json`.
It completed `status=pass`, `numeric_status=pass`, 5,714,431 measurements,
with `matrix_complete=true`, no matrix failures, all three leaf numeric
statuses `pass`, and the evaluated cross-stature comparison `pass`. Required
and observed statures are 1.50, 1.70 and 1.90 m. All three generation and
verifier identities match manifest
`7f21ef2ff07c9ebf3ef63e08bd8269dc5a9720de34380c6996a833ee80449454`;
each registry contains skeleton, male and female with no missing/extra IDs.
Each leaf reports 60 expected and 60 observed native midpoints per body.
The input preparations contain 900 samples and 32 fixtures per stature.

A streaming scalar audit of the large report (not a second verifier) found
maximum recorded native residual 1.06649e-6 m, minimum recorded floor
-1.68086e-7 m and maximum recorded sole distance 1.66521e-7 m. Even the
strictest absolute bounds at the smallest H=1.50 m are respectively 1.5e-5 m,
-1.5e-4 m and 1.5e-3 m. The report's own per-stature checks use each height's
actual H and remain authoritative (`numeric-scalar-summary.json`). Dense
floor and squat-balance steps passed, including 2,181 squat-balance samples
per height. Rendering was deliberately `not-run` for this numeric command and
human visual acceptance was not assessed.

The full, unmodified aggregate is also an independent positive control for
the synthetic fault branches: the exact-candidate input at each height has
both `neutral/00000` and `walking-in-place/00000` at beat 0, matching the
reviewer and developer fault fixtures; the six walking-in-place rows are
present for male/female across the three successful native leaves. Identity,
fixture, beat and sample evidence are recorded in
`..._reviewer_try-12_host-check/control-coverage.json`. The negative synthetic
reports retain their own altered paths and are not relabeled as native output.

### Independent visual comparison — try294

Two separate reviewer-owned complete comparison packs were generated from the
reviewer's fresh try294 focused preparations and evaluated builds, using the
uv-only try12 installation:
`build/add-shared-body-characters_r1_reviewer_try-12_visual-pack/index.html`
and `build/add-shared-body-characters_r1_reviewer_try-13_visual-pack/index.html`.
Each pack's coverage, baseline, character regression, within-pack clean-pass
repeatability, stature, GIF timing and complete-pack reports passed. Each covers
171 samples and the three registered characters, with 192 character composites
plus four stature strips, 54 GIFs, and 12 HTML pages. Arm raise and squat each
contain 17 animation and five count samples; walking contains 33 and nine.
Each pack has default/explicit skeleton and male/female singleton passes in
addition to two separately managed clean batch passes. Historical baseline
was the protected supplemental BPM90 render under its own pre-change identity.

Each pack reports 1,044 exact decoded-RGBA clean-pass comparisons and 1,552
default/explicit/batch/singleton/baseline comparisons, with no failures.
The separately authored cross-pack audit compared all 1,044 clean-a decoded
RGBA images from the two disjoint pack roots: zero pixel differences
(`..._reviewer_try-12_host-check/cross-pack-pixels.json`). Independent HTML
parsing of each pack found 12 pages and 1,377 local links, with zero missing
or escaping targets (`visual-link-audit.json`, `visual-link-audit-pack2.json`
in the same host-check run). The pinned Blender scene audit compared the
world matrices and settings of six cameras and Floor, plus render engine,
shading, resolution and color settings, across all three saved reviewer
stature scenes: exact equality (`scene-audit-expanded.json`). The selected
surface collections and skeletal/control collections could be toggled
independently in the saved H170 scene without saving modifications
(`collection-audit.json`). A fresh skeleton-only no-image construction and
headless saved-scene inspection found no surface collections or surface
objects while preserving skeletal geometry (`skeleton-only-audit.json`).

Reviewer visual observation is not acceptance: the two featureless silhouettes
show modest torso-shape differences while the skeleton remains a separate
representation. Squat and forefoot rocker appear synchronized in the viewed
front/side sheets, with no obvious scene shift at their displayed scale; the
figures are small, so the human should inspect the joint and sole close-ups as
well as GIFs/onion skins. Human Gate 2 remains explicitly pending.

The four disposable synthetic fault case directories `topology`, `stale`,
`floor` and `sole` under `..._reviewer_try-11_fault-check/` were removed after
the successful assertions: 104,441,913 regular-file bytes, zero internal
symlinks. A no-follow scan before and after found zero inbound symlinks. The
independent neutral native source run, test scripts and fault result JSONs
remain, allowing exact regeneration; no accepted or other agent's run was
touched. This is partial cleanup only. Complete review cleanup remains pending
until the aggregate and any unresolved findings have finished.

After the corrected candidate's independent matrix passed and its diagnostic
faults were reproduced, ten obsolete reviewer-owned roots were removed:
`try-9_control`, `try-9_host-check`, `try-9_numeric-h170`,
`try-10_numeric-h150`, `try-10_input-h150`, `try-10_input-h170`,
`try-10_input-h190`, and `try-10_visual-input-h150/h170/h190` (all prefixed
`build/add-shared-body-characters_r1_reviewer_`). The inventory at
`..._reviewer_try-12_host-check/obsolete-runs-inventory.json` records each
path and byte count: 460,888,683 regular-file bytes total. The old H170 and
H150 build receipts recorded `cancelled` / -15 after coordinator-initiated
interruptions, not successful builds; their triggering findings are fixed
and reproduced by the final candidate. The obsolete try251 host source audit
is superseded by the try294 source/provenance audit. Current reviewer native,
packs, scripts, fault reports, candidate and protected baseline were retained.
Before removal there were zero internal or inbound symlinks and no matching
active process; a no-follow scan after removal found zero inbound symlinks.
This does not yet claim complete reviewer cleanup: consumer verification is
still running and current evidence must remain available through the human
gate.

### Corrected diagnostic context — try286, scoped fault audit

The reviewer independently rebuilt try286 (submitted wheel SHA-256
`eb1097d1c4943993ae03ca30c066252e8524a9d9050bdb04908774f7fea8d6b6`, manifest
`1f6a45f29018d07d71cec82b123c3256a8a339f0dc02575fbef1cd160d35134f`).
Direct wheel, sdist and rebuilt wheel match the submitted candidate and
canonical sources on 116 logical files. Fresh, independent neutral-only
construction in the former reviewer try10 fault-build returned successful supervised build/postflight; that obsolete run has since been removed after the final candidate reproduced the scoped checks. This is a single-sample
test construction, not the required complete native matrix.

The reviewer confirmed a separate documentation discrepancy in
`docs/character-models.md`: its unqualified claims that `images=False` builds
produce evaluated geometry and `render_only=True` produces images do not
describe the supported combination `images=False, render_only=True`, which
returns no images and no evaluated geometry (see `tests/test_api.py`,
`test_no_image_build_modes_and_prepared_path_input`). Since correcting the
packaged documentation changes the package identity, the reviewer stopped
its own try286 H150 full build with Ctrl-C: launcher exited 130 and its receipt
records cancelled/-15; no matching process remained. The try286 inputs, archive closure and scoped fault checks were historical evidence and are not final-candidate results; obsolete owned roots were later removed as recorded in the cleanup section.

Four independent synthetic full `verify_character_output` fault cases were run under the now-removed reviewer try10 fault-check; final-candidate equivalents are retained in reviewer try11 fault-check.
They copy that reviewer-owned real output into disposable cases and recompute
receipt output inventories for the intentionally changed synthetic files;
they do not claim that the synthetic in-memory pose was a sealed preparation.
No verifier or oracle is mocked. A forged vertex ID yielded a topology failure
identifying male, neutral, beat 0, component and missing/extra IDs; a stale
prepared hash yielded request artifact, field and expected/observed SHA-256,
with beat not applicable. A coherent -0.001 m synthetic world translation
yielded floor-bound failures for both bodies, measured minimum -0.001000089 m
against -0.00017 m. A synthetic calcaneus.L anchor-carrier offset, leaving
skin carrier frames and vertices unchanged, yielded sole-contact failures for
both bodies at heel.L, measured 0.009999925 m against 0.0017 m. Each failure
contains its fixture and authoritative beat 0. These checks address the
previous diagnostic-context finding only; they do not establish complete
native/dense, determinism, rendering or human visual acceptance.

The present reviewer resumed the independent review of frozen try251. The
reviewer-owned try8 package reconstruction and preparations are retained;
the installed runtime manifest remains `de3ffa80c5f0622b7a0bb7ab7fd9d8186da28c4f4268d6fbe55346528a857b93`.
The source and nested provenance audit was repeated with the reviewer-installed
try251 package in the since-removed obsolete reviewer try9 host-check run:
source/schema validation passed, 14 inherited materials and 770 provenance
records resolved. The full host suite and H170 native build were subsequently
interrupted, not accepted; no numeric, image or human verdict follows from
this historical audit. The separate reviewer H=1.50 m native build
in the former reviewer try9 numeric-h150 root returned supervised `succeeded` after 900 delivered and 60 midpoint samples; its root was subsequently removed and its result is historical construction evidence only.

The architect subsequently confirmed a diagnostic-context defect against the
approved character-models requirement: native delivered floor/contact failure
messages do not consistently include beat, measurement and bound. Correction
changes the packaged verifier and package identity. At coordinator direction,
the reviewer stopped its own in-progress try251 H170 build and host suite with
Ctrl-C; the H170 receipt records cancelled/-15 and both launcher sessions
exited 130. A process-list check found no remaining matching reviewer process.
Neither interrupted run is a pass. The completed H150 try251 build and source audit are scoped historical results; their obsolete roots were later removed. The H170 receipt and interrupted host
log were later removed as resolved diagnostics after final-candidate checks;
the cancellation outcomes are retained in this review record.

## Historical status checkpoint

At this checkpoint, review was in progress on corrected try294. Independent package, host, complete
three-stature numeric and two visual packs have passed within the scopes
recorded above. Independent consumer-motion reconstruction and final
dependency-aware cleanup remain in progress. No final verdict or human visual
approval is recorded.

### Historical status — try206 (superseded)

R1 host/source correction passed independently on try196, and R2 small actual
default/reuse compatibility plus negative checks passed independently on
try206. Final frozen try206 host/package/source/installed checks are complete;
full native/character-pack review and human Gate 2 remain pending. Earlier snapshot findings below
are retained with their exact identities, not relabeled current evidence.

The then-reviewed source was frozen submitted candidate try206, version 0.3.0.
The reviewer independently rebuilt the canonical checkout into direct wheel,
sdist and rebuilt wheel in
`build/add-shared-body-characters_r1_reviewer_try-4_r2-check/`.
All 116 logical package files match canonical bytes and the submitted wheel;
the archive byte hashes differ legitimately with build metadata. Reviewer
direct/rebuilt wheel SHA-256 is
`76f7224d46824bd93270a993e68740c77f99adb1941bf4027137c9a74d6d8bd8`.
Reviewer sdist SHA-256 is
`88c87767440facf1c31417418fa8c811739f8d4a30a3f4409d4439b4157bd179`.
Runtime manifest SHA-256 is
`739c6f975d2e7f04fb05dbfd2a6984a1d86667d96ab587697ec397bae7836573`.
The manifest covers 50 Python implementation files and 64 canonical resources.

The private CPython 3.14 environment contains the reviewer's own non-editable
wheel and offline, hash-checked dependencies from the lock. HML and dist-info
are read-only. The final full host suite completed with 372 tests: 365 passed,
zero failures/errors, and seven explicit installed-harness cases were skipped.
Those separate installed cases passed 7/7. The runtime source snapshot remained
unchanged throughout the full run. Native construction is waiting only for the
developer's sequential matrix to release the shared Blender slot.

## Verification checklist

Types: **A** = automatable host/source/package contract; **N** = native or
numeric measurement; **H** = human visual decision. Items are evaluated against the recorded technical evidence; H portions remain pending
until the human visual decision. Developer logs do not establish
reviewer acceptance.

### Character models

| Requirement / scenario | Type | Independent check |
|---|---|---|
| Characters are first-class selectable library outputs / Select each character independently | A,N | Installed selection matrix, scene inventory, default skeleton laziness |
| Character definitions are canonical declarative sources / Reconstruct and reject character data | A | Closed schemas and hostile source-copy fault matrix before writes/probe |
| All current characters share skeletal movement semantics / Compare the common movement across characters | A,N | Exact shared source/pose/timeline identities; all native frames; consumer squat |
| Surface variants reuse one construction and binding contract / Verify surface sharing and separate inspection | A,N | Shared vertex/face/weight identities; independent scene collections |
| Authored appearance has a frozen testable dossier / Measure and visually identify the authored characters | N,H | Independent table/ring/extrema/slice measurements at three heights; silhouette decision |
| Surface deformation follows the common posed skeleton / Verify deformation throughout existing movement coverage | N | All delivered vertices and nonempty native midpoint schedule versus independent DQ oracle |
| Supporting surfaces preserve contact and floor constraints / Check the sole beyond a rest-pose appearance | N | Full-vertex minima, dense <=0.01-beat audit, actual posed sole-to-anchor and skeletal sliding |
| Character rendering preserves deterministic fixed-scene output / Compare singleton, batch and repeated output | N | Exact decoded RGBA comparisons, native vertices <=1e-6H, fixed scene matrices |
| Common library changes propagate through the registered set / Demonstrate single-source edits and isolated appearance edits | A,N | Disposable shared key/radius/female waist source-copy checks and complete membership |
| Bind-significant skeletal changes require coherent compatibility renewal / Reject a stale bind instead of drifting silently | A | Shoulder-rest mutation rejected for surfaces without requiring a surface for skeleton |
| Appearance and future body proportions remain separate concerns / Inspect the extension boundary | A | Closed data dependencies and unsupported selector rejection |
| Character provenance and reference clearance remain resolvable / Audit original surfaces and inherited attribution | A | Every nested source/material/license resolves; register and notices audit |
| Independent character review precedes visual acceptance / Review the shared character set | A,N,H | Own clean evidence and standalone pack; separate explicit human Gate 2 |

### Public generation API

| Requirement / scenario | Type | Independent check |
|---|---|---|
| Public generation has a small importable contract / Import and call from a Python application | A | Installed no-side-effect import/signature tests outside checkout |
| Rendering returns complete validated image results / Render a prepared subset | A,N | Pinned native image inventory/decoding and exact pose/time joins |
| Rendering returns complete validated image results / Preserve existing construction modes | A,N | No-images and render-only inventories; incompatible options before launch |
| Rendering returns complete validated image results / Render a complete character batch | A,N | Full explicit membership, typed result joins, singleton pixel parity, batch faults |
| Generation exposes resolvable provenance / Follow generated-data attribution | A | Source/result/license/register traversal |
| Generation exposes resolvable provenance / Follow a consumer variant's inherited attribution | A,N | Sealed consumer lineage survives deletion of original caller source |
| Generation exposes resolvable provenance / Reject uncleared new reference use | A | Material inventory and exact commercial derivative basis |
| Generation exposes resolvable provenance / Follow appearance and inherited skeletal attribution | A | Selected closure and portable union of character/consumer/profile provenance |
| CLI generation delegates to the public contract / Compare Python and command callers | A,N | API/console/module equivalence, paths, finite deadlines/cancellation and failure class |
| CLI generation delegates to the public contract / Compare explicit and omitted character selection | A,N | Default/explicit/single/batch matrix and invalid-selection preflight |
| Public results have a documented portable projection / Consume and serialize a result safely | A | Standard JSON, deterministic order, exact fractions and deep mutation isolation |
| Public results have a documented portable projection / Join consumer poses with existing result types | A,N | Consumer fixture IDs and lineage preserve all timeline/image joins |
| Public results have a documented portable projection / Join several appearances to one exact timeline | A,N | No duplicated pose IDs; registry order; per-character image joins and detached projections |
| API integration preserves generation output and visual review / Compare API generation with the existing workflow | N,H | Own clean focused pixels/geometry versus immutable historical baseline; human pack |
| API integration preserves generation output and visual review / Preserve default behavior while reviewing the added characters | A,N,H | Existing skeleton/workspace semantics, separate surface/numeric/render/human verdicts |
| Render character selection is validated and integrity-bound / Validate selection before allocating output | A | String/empty/duplicate/unknown/incompatible/schema/bind faults without writes/probe |
| Render character selection is validated and integrity-bound / Reject render selection substitution | A,N | External expected seals, source closure, receipt/manifest replacement/reseal faults; isolated backend imports |

### Python distribution

| Requirement / scenario | Type | Independent check |
|---|---|---|
| Supported generation resources are complete / Audit both distribution resource closures | A | Independent direct/sdist/rebuilt logical and canonical bytes |
| Supported generation resources are complete / Reject an incomplete or altered installation | A | Disposable missing/corrupt resource/implementation copies fail before backend |
| Supported generation resources are complete / Audit the complete character resource closure | A | All descriptors/template/presets/schemas/docs/host/backend present; no generated assets/downloads |
| Packaging preserves generation output / Compare the package regression pack | N,H | Two own focused wheel renders, baseline geometry/pixels, exact timing and human review |
| Packaging preserves generation output / Generate all characters from an installed artifact | A,N,H | Read-only installed API/CLI, complete source/numeric/image identities, parity and independent human gate |

### Numerical dossier and presentation acceptance

- All 32 diagnostics, BPM60/120/180 and all three heights must be independently regenerated; scoped developer builds do not satisfy this gate.
- Source expansion tolerance 1e-9H; native rest/ring/extrema and DQ tolerance 1e-5H; waist/hip slice tolerance 1e-4H.
- Canonical weights sum within 1e-12, native weights within 1e-6, at most two influences; triangle area strictly greater than 1e-12H squared.
- Every surface vertex z >= -1e-4H; actual posed sole-to-contact anchor distance <=1e-3H; original skeletal contact/frame limits remain unchanged.
- Verify the approved hindfoot-to-MTP blend band 0.065H..0.075H, not the superseded band.
- Native undelivered key midpoints must be nonempty in the BPM60 matrix and independently reconstructed; no YAML/schema dependency injected into Blender.
- Dense grid includes delivered/key/contact events with spacing <=0.01 beats; separate native/dense scopes and worst IDs/values.
- Three-height numeric aggregate must preserve the complete expected height/fixture/BPM/character membership and source/package identity.
- Consumer squat depth 60 degrees/BPM90, appearance-independent, with source lineage and actual native geometry.
- Focused visual H=1.70/BPM90: neutral/rest; arm-raise and squat 17 animation/5 count samples; walking33/9; rocker and all required shoulder/forearm/knee sweeps.
- Full historical baseline join: exact `(fixture, Fraction beat)` for all69 core samples, independent old/new IDs and views; no counts-only intersection.
- Standalone pack: three-character sheets, silhouettes/joint centers, GIF timing, onion skins, joint/sole close-ups, three-height neutral/squat-bottom strips, local links and complete inventory.
- Independent repeated batches, singleton/batch and default/explicit/batch skeleton decoded pixels must be exact; native repeat vertices <=1e-6H; no byte-identical .blend requirement.
- The reviewer will inspect images and state observations as opinion; silhouette identity, readable motion, continuous junctions and planted feet require the human's explicit decision.

## Evidence recorded so far

- `build/add-shared-body-characters_r1_reviewer_try-1_check/package-audit.json`: independent archive/source closure PASS.
- `build/add-shared-body-characters_r1_reviewer_try-1_check/source-snapshot.json`: frozen canonical source hashes.
- `build/add-shared-body-characters_r1_reviewer_try-1_check/dependency-copy.json`: locked offline dependency hashes.
- `build/add-shared-body-characters_r1_reviewer_try-1_check/installation.json`: own non-editable wheel/interpreter/installed hash inventory.
- `build/add-shared-body-characters_r1_reviewer_try-1_check/host-tests.json`: full host suite, 364 tests, zero assertion failures, one error (R2), seven expected installed-harness skips, 713.857 seconds; natural private interpreter, unchanged source snapshot.
- `build/add-shared-body-characters_r1_reviewer_try-1_check/installed-tests.json`: explicit installed acceptance PASS 7/7 in 41.966 seconds from a valid decoy CWD, no Blender and no package mutation.
- `build/add-shared-body-characters_r1_reviewer_try-1_check/source-provenance.json`: source/schema and nested register inventory PASS, 32 diagnostics, 14 inherited materials, 770 provenance records. Live permission and attribution review is separately scoped below.

## Findings

| ID | Severity | Requirement / scenario | Evidence | Suggested direction |
|---|---|---|---|---|
| R1 | major, corrected and independently verified for provisional try196 host/source scope | Surface variants reuse one construction and binding contract; frozen design §4.2 | Original try191 used separate absolute torso tables rather than the required base/delta representation. The scoped independent follow-up below verifies template `radius_h` plus appearance `torso_radii_delta_h`, frozen shapes, propagation/isolation and fail-closed invalid inputs. | Preserve this correction in the unified final candidate and renew package-bound native/render review; the scoped host result is not final acceptance. |
| R2 | major, corrected and independently verified for scoped try206 compatibility | Character rendering preserves deterministic fixed-scene output; public API/CLI backward compatibility; design §7 normal skeleton-only/default workflow | Original try191 omitted the API creation claim; actual try199 then exposed the sealed-request inventory omission and operation-unfiltered receipt discovery. The separate try206 actual/default/reuse and host negative matrix below now pass. | Preserve strict claims, complete-union equality and operation-specific receipt checks in the unified final snapshot; full host/native/character review remains required. |
| R3 | major, corrected and independently verified on try294 | Design §7, three-stature numeric matrix | Reviewer try206 matrix reported incomplete because scaled metre-valued mobility/diagnostic fields were compared as identical. Try294 canonical-scaling comparator, negative cases and full independent three-stature aggregate now pass. | Preserve exact source/package identity and stature scaling; do not infer pass from individual leaf reports. |
| R4 | minor, corrected on try294 | Character review-pack documentation / supported generation modes | Try206 examples passed `input.json` where the CLI requires a run directory; try286 docs also made unqualified claims about `images=False` and `render_only=True`. Current examples and mode descriptions match the checked contract. | Keep examples and documented image/evidence distinctions aligned with API/CLI. |
| R5 | major, corrected and independently verified on try294 | Character models / supporting surfaces / check the sole beyond a rest-pose appearance | Earlier delivered native floor/contact failures omitted authoritative beat or measured/bound context. Independent try11 synthetic full-verifier cases now exercise topology, stale identity, floor and detached sole; try12 complete numeric matrix provides unmodified neutral and walking beat-0 positive control. | Preserve fail-closed behavior, character/fixture/beat/vertex-or-anchor and measured/bound diagnostics without changing tolerances. |

The original archive tests alone do not establish numeric/render/human acceptance.
R2 was independently reproduced using only the reviewer's installed wheel,
without importing the canonical review-pack module or launching Blender:
`build/add-shared-body-characters_r1_reviewer_try-1_check/reproduce-default-pack.json`.
Both module origins are inside the private reviewer venv; the backend probe
was not reached and `clean-a` was not created.
The submitted developer handoff still names older try177 and requires final reconciliation with try191; this is tracked as pending process documentation rather than a final verdict.

## R1 independent follow-up — provisional try196

This follow-up is HOST/SOURCE ONLY. R2 and the full final-candidate native/render
review remain open. No developer test harness, acceptance output or native mesh
was reused. Fresh run:
`build/add-shared-body-characters_r1_reviewer_try-2_r1-check/`.

The reviewer independently rebuilt direct wheel, sdist and rebuilt wheel from
the frozen canonical sources. Their 116 logical package files match one
another, canonical bytes and the submitted provisional wheel SHA-256
`cff54359a150cc91f5cb46e5712b6631424366461b7866c3a5eb5fe0d3694b8b`.
Runtime manifest SHA-256 is
`63351e7294bf3820c7209fc19076024b891cb95204ad2fa9cad4b93773e53048`.
Checks ran using the reviewer's own non-editable read-only wheel/private
interpreter. The canonical runtime source snapshot remained unchanged.

Reviewer-authored checks passed **7/7 in 6.734 seconds**:

| Check | Independent result |
|---|---|
| Actual shared source representation | All 10 shared template rings own positive `radius_h` pairs; appearances contain only required signed delta pairs; male deltas all zero; all frozen female pairs match the approved dossier. |
| Frozen control rings at three heights | All 1920 literal control-ring vertices at H=1.50/1.70/1.90 checked; maximum normalized residual `1.8504e-17H` versus bound `1e-9H`. |
| Unchanged analytic geometry | Compared 55776 vertices at three heights against the reviewer's independently built prior try191 analytic source, not developer meshes; maximum normalized change `2.0688e-17H`; component/vertex/face IDs, material assignments and weights exactly unchanged. |
| Common torso edit | Physical disposable source-copy base waist rx +0.001H propagated to both variants at all 3 heights; every affected/interpolated vertex checked; other components, topology, weights, appearances and skeleton closure unchanged. |
| Female isolation | Physical disposable female delta +0.001H changed only female torso at all 3 heights; all expected vertex displacements, unchanged other components/topology/weights and unchanged male/skeleton closures checked. |
| Invalid inputs before allocation/backend | All 12 physical source-copy cases rejected before output creation, allocation boundary or backend call: zero/negative effective radius, NaN/Inf delta/base, zero base, malformed delta count/shape, nonzero male delta, legacy absolute table and legacy radii_source. |
| Packaged docs/schema closure | Canonical and packaged character docs/schema bytes agree; delta/base fields required; legacy absolute/source fields closed; no fallback documented or accepted. |

Evidence: `package-audit.json`, `source-snapshot.json`, `r1-tests.log`,
`r1-tests.json`, and the independent reproducible `check_r1.py` in that run.
Command:

```text
uv run --no-project build/add-shared-body-characters_r1_reviewer_try-2_r1-check/environment/bin/python build/add-shared-body-characters_r1_reviewer_try-2_r1-check/check_r1.py
```

The retained old reviewer191 wheel is a concrete dependency of the analytic
regression check. No native Blender work, full host rerun or final visual
approval is claimed by this provisional result.

## R2 independent actual smoke — docs-inclusive try199

This is a SMALL DEFAULT SKELETON compatibility check, not full character or
diagnostic acceptance. The reviewer independently rebuilt and installed the
canonical source in
`build/add-shared-body-characters_r1_reviewer_try-3_r2-check/`.
Direct wheel, sdist and rebuilt wheel have the same 116 logical package files
and match the submitted try199 reference wheel SHA-256
`da4d6758d708278d13849744a5ebdb2a83802d9d34d85e16ceca729eb57ec9d3`.
Runtime manifest SHA-256 is
`d04f7e51aef3e2921eea2441daa4abcfee9eb90c659ff2e02d557cee7a165538`.

The reviewer's explicit private interpreter, pinned headless Blender and public
API created fresh disjoint direct-child runs:

- `..._reviewer_try-3_r2-input`: neutral/rest, H=1.70, BPM90, two prepared samples.
- `..._reviewer_try-3_r2-eval`: actual supervised no-images skeleton evaluation, succeeded.
- `..._reviewer_try-3_r2-pack`: actual default `review_pack.main`, with no character option; clean-a native rendering succeeded, then wrapper postflight failed.

`run_actual.py` completed with a failure in 9.959 seconds and preserved its full
traceback in `actual-r2.json`. Source snapshot was unchanged. The actual native
render receipt reports Blender 5.2.2 LTS/build `d13f752e3b9c`, succeeded state
and 18 readable neutral/rest PNGs. The public API accepted its complete output.
The review-pack wrapper then rejected that same output at
`review_pack.py:61` with
`Render receipt output inventory does not match the complete render output set`.

Read-only diagnosis of the retained real pass establishes:

| Observation | Actual result |
|---|---|
| Legacy `_validate_manifest` expected set | 22 files |
| Sealed successful render receipt | 23 files |
| Difference | Exactly `character-render-request.json`; zero missing files |
| Sealed request identity/content | Exactly equals the current expected skeleton render-only request |
| Documented complete union hashes | PASS when independently checked read-only; no output altered and no failed invocation relabeled successful |
| Actual outcome operations | `version-probe` and `render-pass`, both legitimate |
| Actual `reuse_render_pass` | Fails before accepting the pass: `Expected one nonsymlink supervised receipt`; implementation counts both operations without filtering |

Evidence: `actual-r2.json`, `actual-pack.log`, `actual-pass-diagnosis.json`,
`run_actual.py` and `audit_actual_pass.py` in the fresh check run, plus the
unmodified native receipts/images in its separate pack run. The actual pack
never reached clean-b, final assembly or successful sealed reuse. Missing/
changed request, extra/symlink and legacy reuse acceptance checks are not
reported as passing while a valid real pass itself is rejected. The native
slot was released; no live reviewer process remains.

## R2 independent repeat — corrected try206

The reviewer independently rebuilt and installed canonical try206 in
`build/add-shared-body-characters_r1_reviewer_try-4_r2-check/`.
Its direct wheel, sdist and rebuilt wheel contain identical 116 logical files
and match the submitted reference wheel SHA-256
`6f2389268cf59ee29e71bec00b659100483e199dd7a3ac520adb6806714a215f`.
Runtime manifest SHA-256 is
`739c6f975d2e7f04fb05dbfd2a6984a1d86667d96ab587697ec397bae7836573`.
All native work used the explicit private installed interpreter and the
supervised pinned Blender; canonical runtime bytes remained unchanged.

Actual positives passed in **16.662 seconds** through fresh direct-child
`..._reviewer_try-4_r2-input`, `..._reviewer_try-4_r2-eval`, and
`..._reviewer_try-4_r2-pack` runs:

- Real neutral/rest two-sample skeleton evaluation succeeded.
- Actual default skeleton `review_pack.main` completed clean-a, clean-b and assembly.
- Each real pass contains 18 readable PNGs, the sealed request and both legitimate version-probe/render-pass receipts.
- All 18 corresponding decoded RGBA comparisons passed exactly.
- Actual `--reuse-renders` completed successfully while new rendering and backend calls were patched to fail if attempted.

A separately authored HOST-ONLY reuse matrix passed **20/20 in 2.655 seconds**.
It used disposable copies of the real complete pack and never changed that
native pack. Three positive controls establish meaningful rejection tests:
the valid sealed pack and two explicitly **synthetic current-package legacy
compatibility fixtures**, with and without an optional valid probe. These
legacy fixtures test the reader contract and are not claimed as native legacy
generation. The 17 negative cases reject missing/changed/symlinked/broken-link
requests; extra pass/pack entries; unknown, missing or duplicate render/probe
operations; failed/stale probes; symlinked process directories; omitted request
hash membership; extra receipt outputs; and a failed probe in legacy form.
Every case forbids new rendering/backend invocation.

Evidence: `actual-r2.json`, `actual-pack.log`, `actual-reuse.log`,
`reuse-matrix.json`, `run_actual.py`, and `check_reuse.py` in the fresh check
run. Exact R1 source/schema/data/character-doc hash continuity from the reviewer's
independently checked try196 to try206 passed in `r1-source-continuity.json`;
this does not relabel old results as new native evidence.

All 20 temporary fixture workspaces were inventoried and removed after their
expected results: 995,198,197 regular-file bytes and three symlinks were removed
without following link targets. The exact removed fixture paths/counts are in
`reuse-matrix.json`; the original real native pack's complete file-hash map
remained unchanged. Successful actual input/evaluation/pack roots, environment,
archive/source hashes, harnesses and logs are retained as the dependency
closure. Native slot was released; no reviewer process remains active.

This closes R2 for the scoped corrected default/reuse contract. It is not a
full diagnostic, all-character, full-host, licensing or human visual verdict.

## Final unified-candidate execution — frozen try206 (in progress)

Fresh final host run:
`build/add-shared-body-characters_r1_reviewer_try-5_host-check/`.
It consumes the reviewer's own independently built/non-editable try206 wheel
and private interpreter from the retained try4 environment; no developer
installation or acceptance evidence is consumed. Its copied source snapshot
is the exact verified try206 snapshot, guarded before and after checks.

- Full canonical host suite PASS: 372 tests, 365 passed, zero failures/errors and seven explicit installed-harness skips, in 873.353 seconds. Only the documented real-Blender modules were excluded (six backend tests and one pipeline fault test); their native scope remains separate. The canonical source snapshot was unchanged.
- Explicit installed acceptance PASS 7/7 in 109.383 seconds from a fresh decoy fixture workspace and read-only install, with no Blender. These are the seven cases skipped in ordinary host discovery, not untested coverage.
- Source/schema and nested provenance inventory passed: 32 diagnostics, 14 referenced inherited materials, 770 records.
- Independent fresh full preparations at H=1.50/1.70/1.90 are complete in `..._reviewer_try-5_input-h150`, `input-h170` and `input-h190`: 900 samples at each height, BPM60/120/180. Old try191 inputs remain explicitly stale and are not reused.
- Full native work is not yet launched: the developer currently owns the shared Blender slot. The reviewer will use only these new independent preparations after slot release.

Exact final host/source evidence:

- `build/add-shared-body-characters_r1_reviewer_try-5_host-check/host-tests.json` and `host-tests.log`: final complete host result, exact interpreter/origin/manifest, exclusions/skips, source guard and full trace log.
- `build/add-shared-body-characters_r1_reviewer_try-5_host-check/installed-tests.json` and `installed-tests.log`: final seven installed cases, direct venv origin, valid decoy CWD and unchanged read-only package.
- `build/add-shared-body-characters_r1_reviewer_try-5_host-check/source-provenance.json`: source/schema validation and all nested source/register identities.
- `build/add-shared-body-characters_r1_reviewer_try-5_host-check/clearance-review.md`: independent portion/permission/attribution audit and scoped live-retrieval limits; no new external material and no missing/contradictory clearance found.
- `build/add-shared-body-characters_r1_reviewer_try-4_r2-check/package-audit.json`: independent canonical direct/sdist/rebuilt closure, each logical file hash and candidate match.
- `build/add-shared-body-characters_r1_reviewer_try-4_r2-check/installation.json` and `dependency-copy.json`: reviewer wheel/interpreter/installed-file identity and exact locked offline dependency hashes.
- `build/add-shared-body-characters_r1_reviewer_try-5_host-check/source-snapshot.json`: exact frozen runtime sources used for the final checks.
- `build/add-shared-body-characters_r1_reviewer_try-5_host-check/numeric-inputs.json` and `visual-inputs.json`: independently prepared final numeric/focused inputs and seals, not developer generation evidence.

The full host log independently repeats the common arm-raise edit, shared
surface-radius edit, isolated female waist edit, stale shoulder bind rejection,
new torso-base/delta propagation, selection and complete request/manifest
integrity scenarios. R1's stronger reviewer-authored three-height all-vertex
source-copy checks and R2's actual default/reuse checks remain explicitly
linked above rather than replaced by developer logs.

## Provenance audit scope

All14 nested inherited material IDs resolve to complete canonical register
entries. New surface/appearance sources declare original authorship and contain
no third-party mesh/texture asset; skeleton descriptor attribution remains
separate from those authored surfaces. No dependency or convention changes
appear in `pyproject.toml`/`uv.lock` for this patch. The unchanged notice sections
retain author/title/DOI/portion/license/modification information.
Scoped live permission checks and retrieval limits are recorded in
`build/add-shared-body-characters_r1_reviewer_try-1_check/live-license-review.md`.
This is not a claim that every inherited remote license was reverified live.

## Cleanup and pending work

Only the exact reviewer-owned check run and this review record have been written.
No developer, protected baseline, or other review root was modified or removed.
The first host launcher assertion rejected uv's project-interpreter selection
before HML import/test execution; the corrected command explicitly names the
private venv executable with `uv run --no-project`.
No cleanup is claimed complete while review corrections remain unresolved. Build artifacts,
environment, logs and source/dependency hashes are retained as current evidence.
Native/render reproduction, visual pack, code scope/licensing audit and final
cleanup/verdict remain pending.
The full three-height preparation is complete (900 samples at each height),
but native construction is temporarily held for R1's source/design decision;
the host tests completed under their already captured frozen identity.
R1's provisional host/source correction has now been independently checked.
The try191 source snapshot, own archives,
private installation, logs and prepared inputs are retained as prior evidence;
they must not be relabeled as the corrected candidate. The new provisional R1
run is retained with its dependency closure; no roots were removed. The full
native matrix was never launched. The separate try199 small actual compatibility
smoke is retained as unresolved R2 evidence with its input/evaluation/render
dependency closure. No roots were removed. Final acceptance awaits a unified frozen R1/R2 candidate and renewed
affected/whole-host/installed/native/render evidence.

## Independent native construction continuation — try6

The reviewer independently generated all three no-images character builds from
its own try5 preparations and try4 non-editable wheel. Each request asserted
900 prepared samples and runtime manifest SHA-256
`739c6f975d2e7f04fb05dbfd2a6984a1d86667d96ab587697ec397bae7836573`
before invoking the installed public API. All three API calls returned after
supervised Blender and complete output postflight; each backend emitted 900
samples and 60 sealed midpoint samples. The fresh runs are:

- `build/add-shared-body-characters_r1_reviewer_try-6_numeric-h150/`: render identity `956c22b76d04063189d1b3ac2cef2b261240021c1e76582c65135754ee1e5ba2`.
- `build/add-shared-body-characters_r1_reviewer_try-6_numeric-h170/`: render identity `689c741e8735bbf28a46918d1de466071c288bdef6394d0a0be4e52e9673cbda`.
- `build/add-shared-body-characters_r1_reviewer_try-6_numeric-h190/`: render identity `3d4d66376b7a8e6f81d3a1e6eb789dd4115a74b8855eaebf20de1392a042dbfb`.

These are construction results only, not numeric conformance, rendering or
human visual approval. The outputs and their prepared inputs, installed wheel,
process receipts and logs are retained as dependencies for the pending
independent dense verification. Blender was released for developer work.

The independent H=1.50m full verifier subsequently completed with `status=pass`,
`numeric_status=pass`, and 5,714,431 measurements in
`build/add-shared-body-characters_r1_reviewer_try-6_check-h150/metrics.json`.
The invocation used the reviewer's installed interpreter and `verify-skeleton`
with `--action-coverage --dense-floor --character-output <own H150 run>
--numeric-only`; all 900 delivered skeleton samples and all listed dense-floor
fixtures completed. This is one-stature numeric scope only: the H=1.70/1.90
runs, three-stature aggregate, rendering and human visual review remain
pending. The reviewer-run native inputs, per-sample evidence and report are
retained for the pending aggregate and reproducibility.

The independent H=1.70m full verifier also returned `status=pass`,
`numeric_status=pass`, 5,714,431 measurements, with all 900 skeleton samples
and dense-floor scenarios complete:
`build/add-shared-body-characters_r1_reviewer_try-6_check-h170/metrics.json`.
It used the same installed reviewer interpreter and flags as the H150 check,
but its own H170 native input and fresh output. This is still a scoped numeric
result; H190, three-height aggregation and visual acceptance remain pending.

### Read-only inspection of developer consumer evidence

The developer's try231 input and try230 report were inspected as a separate
consumer-specific technical case, not as independent native generation. The
prepared content identity is
`f42b24b2c191d2cd386c18746b8813521214ab5e4e56c4eb8138ca7d62e8b0ce`, and
try230 identifies render request
`c7db00674e2eea22caf89f16bcc2a6079cb1bc5474ef13a9f8766d45968c19c2`.
The preparation has 17 shared consumer samples, a maximum left-knee flexion of
60 degrees, and a BPM90 timeline with 17 animation and five static samples.
Its `primary_bpm` is 120; the separately stored BPM90 timeline must not be
misrepresented as its primary rate. The registry reports all three character
IDs. The leaf native checks report pass for 17 male and 17 female samples,
with maximum residuals 7.47295e-7m and 7.34574e-7m respectively; the scoped
consumer dense rows report 401 points per body, minimum z about -2.24e-16m,
and maximum sole distance about 1.56e-16m.

The original try230 overall report remains `fail` and its character leaf
`incomplete`: diagnostic-fixture/tempo coverage and the other two heights are
not supplied by this consumer-only input. Its leaf native/dense pass is not a
full-matrix pass. Independent reconstruction of the consumer case, source and
shared-frame/contact comparison, and complete independent numeric/visual
review remain pending.

The independent H=1.90m verifier also returned `status=pass`,
`numeric_status=pass`, and 5,714,431 measurements, with 900 skeleton samples
and the complete dense-floor list:
`build/add-shared-body-characters_r1_reviewer_try-6_check-h190/metrics.json`.
All three individual numeric reports now pass independently, but the required
three-height aggregate and rendering/human visual review remain pending.

### Independent three-height aggregate — finding pending

The reviewer's installed CLI `verify-skeleton --numeric-only --stature-builds`
was run against all three independently generated try6 native runs. The
result is preserved at
`build/add-shared-body-characters_r1_reviewer_try-6_numeric-matrix/metrics.json`.
All three leaf numeric results are `pass`, the three evaluated-stature
comparison is `pass`, and dense squat balance passed 2181 samples at each
height. Nevertheless, the aggregate is `incomplete` / `numeric_status:
incomplete` and `matrix_complete: false` because it reports mobility and
diagnostic definition differences for both H170 and H190 against H150. This
is not relabeled a pass.

Read-only comparison finds expected stature-scaled meter-valued examples:
`mobility/couplings/1/parameters/glenoid_m/0` 0.1575 versus 0.1785, and
`diagnostics/0/contacts/0/targets_m/0/0` -0.0825 versus -0.0935 (H150 versus
H170). The frozen design requires equality except intentional stature scaling;
these observations require architect/developer diagnosis and a corrected
aggregate with the identity and all applicable checks intact. This finding
blocks the required all-stature numeric pass. The three scoped reports remain
valid for their separate heights and do not substitute for the aggregate.

### Independent review-pack documentation discrepancy

The `tools/README.md` character pack example passes `<run>/input.json` to
`--input` and `--stature-input`. The exact installed try206 CLI rejected the
first such path before allocating an output, reporting that the existing input
must be a direct-child build run; the same invocation using run directories
was subsequently started. The documentation example should be reconciled
with the supported interface and retested. This is separate from visual review.

### Independent visual pack — try206 only

The reviewer generated H170 (171 samples) and H150/H190 (18 samples each)
from its own try5 prepared inputs in fresh try6 visual-eval runs, using the
reviewer-installed try206 manifest `739c6f975d2e7f04fb05dbfd2a6984a1d86667d96ab587697ec397bae7836573`.
The standalone pack is
`build/add-shared-body-characters_r1_reviewer_try-6_visual-pack/index.html`.
Its command completed with `complete_pack_status`, baseline, regression,
repeatability, stature, GIF and coverage all `pass`: 171 samples, 192
composites, all three character IDs, arm-raise/squat 17 animation and five
count samples, walking 33 animation and nine count samples. Two clean batch
passes and separate default/explicit skeleton and male/female singleton passes
completed. This is evidence for try206 only; applicability to a subsequent
candidate requires source/package and renderer equivalence to be established
explicitly. No artifact was resealed or relabeled.

Reviewer visual observation, not human acceptance: in neutral side and front
sheets the figures are stylized mannequin silhouettes; the two surface variants
are similar, with visibly different torso outlines, while the skeleton remains
separate. In the squat count sheet all three follow the same sequence, but the
figures occupy a small part of the composed sheet, so close-up pages should be
used to assess junctions and the soles. Human judgment on silhouette identity,
movement readability, continuous junctions and planted/rolling feet remains
mandatory.

## Corrected candidate try251 — independent follow-up in progress

The earlier try206 aggregate finding is under correction, not yet closed.
The architect required comparison against canonical sources after intentional
stature scaling, while preserving complete source/package identity and failing
closed for independently invalid changes. The submitted try251 wheel SHA-256
is `2fd71010dd78fadfca4078d841ab37394b180eb62a8a379df0310a2b1571f98a`;
the runtime manifest SHA-256 is
`de3ffa80c5f0622b7a0bb7ab7fd9d8186da28c4f4268d6fbe55346528a857b93`.
Fresh independent reviewer package reconstruction and private installation:
`build/add-shared-body-characters_r1_reviewer_try-8_candidate-check/`.
Direct wheel, sdist and rebuilt wheel matched canonical and submitted
candidate across 116 logical package files.

The independently authored comparator check used three newly prepared,
package-validated inputs and passed six cases: valid 1.50/1.70/1.90 definitions
plus individually changed profile, mobility, diagnostic contact, scene and a
consumer snapshot without resolver. Evidence is `independent-matrix.json` and
`check_matrix.py` in that run. This is scoped host-only evidence; it does not
assert success of the public aggregate or native rendering. New separate
reviewer inputs under `..._reviewer_try-8_input-h150`, `input-h170` and
`input-h190` each contain 900 samples and use try251's package identity.
Focused reviewer visual inputs are also separately prepared at all three
heights. The earlier try206 native and visual outputs were not resealed, and
are historical comparisons only; fresh final-candidate native, numeric,
consumer and visual outputs remain required.

The earlier try248 independent package/comparator attempt remains historical.
The subsequently changed source was detected by the reviewer's source
snapshot guard before any try248 input was generated; no mixed-identity input
or successful full check is claimed from that attempt.

### Additional try251 host-only checks and current cleanup inventory

Using the reviewer's own read-only try251 installation, the three targeted
matrix-workspace tests passed 3/3 with an explicit test workspace and reviewer
owned run root; the surface, scalar skinning and compiled-skinning modules
passed 35/35. No Blender or process inspection was used in those 38 tests.
The separate six reviewer-authored comparator cases remain in
`..._reviewer_try-8_candidate-check/independent-matrix.json`. A prior direct
unittest invocation failed all seven at fixture setup because an installed
package has no implicit repository root; it did not exercise any test body.
The targeted repeat used `HUMANMOTIONLIB_SOURCE_ROOT`,
`HUMANMOTIONLIB_TEST_RUN_ROOT` and a reviewer-local `UV_CACHE_DIR`, and the
result above does not claim a complete host suite or process supervision.

Inventory was taken without following links over reviewer-owned try6/try7/try8
roots. No root was removed in this pass: try6 contains the current unresolved
three-height finding, native/visual comparison and its dependencies; try7
contains the interrupted freeze diagnostic and audit needed to reconcile that
history; try8 contains the current installed candidate, tests and fresh
resumable numeric/visual inputs. The largest retained try6 roots include three
native runs (4,042,845,104; 4,039,251,975; 4,039,505,671 regular-file bytes),
three scoped checks (2,760,630,763; 2,727,168,476; 2,732,391,275 bytes), the
aggregate (3,732,766,431 bytes) and visual pack (3,505,007,398 bytes); each
has zero symlinks. The try7 and try8 candidate roots contain respectively
23,009,804 and 23,014,783 regular-file bytes and four links each; these links
were inventoried, not followed or removed. The six resumable try8 input roots
contain 448,369,557 regular-file bytes total and zero links. Their own current
candidate/evidence dependencies are retained. Removed: zero paths, zero bytes.
Full dependency-aware cleanup is pending after final-candidate results and the
resolution of the try206 aggregate finding; no other agent's run was touched.

## R13 focused managed-owner review — 2026-11-06

**Scoped verdict: PASS WITH NOTES** for synthetic task 19.2 controls only; no native Blender, final package-closure reconstruction, numeric diagonal, determinism, final visual pack, or Human Gate 2 is claimed. Reviewer-owned run: `build/add-shared-body-characters_r13_reviewer_try-1_focus-check/`. Tested installed wheel SHA-256 `ac43ac83ab55bd7aa7348c129f98505c96531753e76b8767d6c9b04ff2d7c873`; installed runtime manifest `ec5f1a7c010e90477a113e66a2c25e3765acca804ea5dae193e4007870819838`; Python 3.14.6, fresh uv venv/cache inside this reviewer root, `uv pip check` PASS, installed package/dependency origins within reviewer venv, only generated `_virtualenv.pth`, standard-library paths outside prefix. Process visibility probe under elevated execution was run by orchestrator: child PID 23519 visible, exit 0. No real supervised backend was invoked in this focused review.

Reviewer independently reran 12 focused tests with the exact installed package: the diagonal main → real managed helper → private API → real runner reaches all eight routes and verifies owner/selection/request with synthetic preflight, version probe, execution and receipts; API claims; allowed paths and symlink negatives; nested claim; replaced/symlinked request, replaced directory and post-probe mutation controls; matrix nonallowlisted/symlink path, matrix opt-in and undeclared/overlap preflight, invalid selection, and sealed reuse receipt/request/inventory. Test copies under the reviewer run came from the developer's identified snapshot. The review-pack test loader was changed in this reviewer-only copy to import the installed package instead of loading source directly; the installed origin was confirmed. A missing test-class name in the first invocation and missing local `tools/matrix.py` on the first reuse invocation produced two unittest loader errors, not product failures; both were corrected in the reviewer harness and the intended tests passed on rerun. The original runtime/runner test code was not altered. These are host/synthetic checks and do not establish actual Blender behavior.

Read-only SHA-256 comparison of the 118 R11 frozen package-source inputs with the R13 source snapshot found only `src/humanmotionlib/api.py`, `run_blender.py`, `runtime.py`, and `review_pack.py` changed. Inspection of those diffs found managed-owner propagation/path validation and documentation changes; geometry, scene, canonical motion, sampling and backend construction source are unchanged. The accepted R11 early preview remains applicable, subject to confirming the corrected final freeze matches this snapshot; the new runtime identity is not the old one and prior package-bound evidence must not be relabeled.

**Pending:** retain this reviewer run and its evidence until role-scoped cleanup is possible; record removed paths/bytes and pending failures before a completed handoff. Independent full acceptance and final reviewer pack remain separate. Crop-order procedural deviation remains explicitly recorded in the existing handoff; early acceptance does not make the original ordering compliant.

## R13 independent reconstruction and report-size inspection — in progress

After rechecking the accepted R11 early decision and R13 freeze, the reviewer copied and SHA-256 verified 201 unique source/test/plan inputs into `build/add-shared-body-characters_r13_reviewer_try-1_source/snapshot/` (118 source, 60 tests and 23 execution-plan paths; overlaps count once). Before/after package-build hash comparison found no changed frozen inputs. Independent direct wheel and wheel rebuilt from the independent sdist match the frozen submitted wheel on all **123 non-RECORD archive files**; all 118 frozen source inputs occur in the sdist with matching hashes, with canonical resource paths mapped into `src/humanmotionlib/resources/`. The independent wheel is installed in a fresh reviewer uv environment under `..._r13_reviewer_try-1_candidate/`; `uv pip check` and runtime integrity pass, manifest SHA-256 `ec5f1a7c010e90477a113e66a2c25e3765acca804ea5dae193e4007870819838`. `hml validate --profile adult-reference-v1` reports valid sources, 180 structures, 67 actions, three placements and 32 fixtures; the initial command without required `--profile` returned a usage error, not a source-validation result. Same-privilege process probe by orchestrator saw child PID 28955, exit 0. Twelve independent inputs were generated; native and final acceptance remain in progress.

Read-only streaming inspection of developer `build/add-shared-body-characters_r13_dev_try-1_numeric-diagonal` (7,445,280,375 bytes; SHA-256 `5bbc3fe225cbbfd141d485c9e17bae423d7e52a96f6b0eae769b433049eeea84`) found skeleton `backend` and `transforms` values are byte-identical, each exactly 3,720,096,811 bytes and each SHA-256 `f7e4e83603db1cbe2a1a5800c516438554544b9e343a807f4c1db1a78b4f6069`; this duplication explains nearly all report size. Three small dense sections were separately decoded by byte offsets: they contain beat-grid membership, aggregate extrema and failures; no full posed-vertex array per dense step was observed. This is an efficiency note, not a numerical or dense-streaming failure. The report was not loaded wholesale or rewritten.

**Procedural path finding, developer numeric evidence:** `build/add-shared-body-characters_r13_dev_try-1_numeric-diagonal` is a regular file, not a directory. AGENTS.md §5 requires a fresh independent run to be a direct-child run directory. The CLI accepts this file operand, so its numeric contents and verdict remain identifiable, but the allocation did not meet the required run-root layout. Do not move, reseal or relabel the evidence. The reviewer aggregate is planned at `build/add-shared-body-characters_r13_reviewer_try-1_numeric-diagonal/report.json` within its own fresh run directory; final disposition remains open.

## R13 independent diagonal visual pack — generated; technical review pending

The independent pack is `build/add-shared-body-characters_r13_reviewer_try-1_visual-a/index.html`. Its diagonal report records the approved three pairs, 171 focused samples per pair, 108 composites per pair, coverage/timing/GIF and two-clean-pass repeatability `pass`, skeleton default/explicit decoded pixels `pass`, and six unassessed character-height pairs. It explicitly retains external numeric, workflow parity, independent review and human Gate 2 as separate; the individual ordinary complete-pack statuses remain `incomplete` under this scoped diagonal invocation. A reviewer HTML audit found 37 pages, 1,640 local href/src links, zero missing or escaping targets. This check does not by itself establish native numeric or full change acceptance.

Reviewer visual opinion, not human acceptance: the mixed-height overview shows all three selected characters on the same apparent floor line and fixed framing; the human should use the separate close-up and motion pages because the figures are small in the overview. In the male side squat sheet the descent and ascent are legible and the feet appear on the ground line at the displayed count poses; in the female front arm-raise sheet arms rise and return symmetrically at count poses. These observations do not establish contact tolerances, continuous deformation, or correctness of motion between counts. Human Gate 2 remains pending until the final independently checked pack and all required supporting evidence are ready.

**R13 independent affected-host batch:** `build/add-shared-body-characters_r13_reviewer_try-1_host-check/test-results.json` records **97 tests, 97 passed, 0 failures/errors/skips**, 0 subtest failures; detailed output is `tests.log`. This uses the independent installed R13 wheel and reviewer-owned copy of frozen tests. The 96 reconstructed R11/R12 corrected test IDs in the developer's `host-dependency-inventory.json` are all present, plus the new R13 diagonal-owner API control; their original failed runs remain failed. Process/environment preflight passed under the same elevated privilege route. This establishes the six affected-module batch, not the rest of the old 512-test suite: unchanged dependency applicability, dynamic/subprocess cases, excluded backend cases and independent numeric/visual evidence still require their respective resolution.

**GIF timing detail:** The front arm-raise/squat GIFs for each pair contain 16 encoded display intervals of 160–170 ms (the loop-closing still is coalesced), while walking GIFs contain fewer encoded frames and some longer holds. For the male front walking source PNGs, 33 samples exist and the source frame runs at indices 8–16 and 24–31 are respectively pixel-identical, explaining the 1.5 s and subsequent merged hold without dropping distinct sampled views; full GIF duration is 5,330 ms versus the expected 5,333.33 ms. This checks the representative encoded timeline, not numerical motion/contact acceptance.

## R13 independent diagonal technical review — 2026-11-06

**Verdict: FAIL — acceptance remains incomplete.** The implemented selected-pair numerical, focused rendering, consumer and workflow parity checks described below pass in their stated scope, but the host-coverage requirement and role cleanup are not closed. This verdict does not imply a geometry/numeric failure. Human Gate 2 is pending and must not be inferred from these checks. The early crop chronology issue remains explicitly disclosed; it is not retroactively corrected by visual acceptance.

| ID | Severity | Requirement / scenario | Evidence and direction |
|---|---|---|---|
| R13-HOST-1 | major | Character models, `Remaining real-backend acceptance uses the approved diagonal`, host/source product contracts; task 9.4 and resource-conscious coverage plan | Reviewer exact-R13 affected batch covers 97 methods including all 96 reconstructed corrected IDs. The historic two 512-test runs failed and cannot be relabeled. `host-dependency-inventory.json` still classifies 379 old cases with changed static dependency closure and 75 requiring dynamic/subprocess review, plus three changed methods and 23 old failures/errors; its candidate carry-forwards are a screening result, not proven per-method applicability. Supply and independently review a function-level dependency/identity ledger for all remaining relevant cases and run any unresolved methods, or run one independent current-R13 full host suite and separately account for installed-only skips and intentionally excluded real-Blender cases. No duplicate developer full suite is needed. |
| R13-PROC-1 | minor | AGENTS.md §5 fresh independent run root | Developer numeric output `build/add-shared-body-characters_r13_dev_try-1_numeric-diagonal` is a regular file instead of the required run directory. Preserve its existing SHA and result; do not move or relabel it. Reviewer wrote the new report inside a fresh directory. Explicitly disposition the historical layout deviation. |
| R13-PROC-2 | minor | R11 preview plan requires pixel crop rectangles before rendering | The rectangles were computed after the four preview renders. The human was told before accepting, and the 72-crop/36-pair post-audit established selected pixels and common before/after bounds; this does not change the historical order. Task 18.2 stays unchecked pending explicit disposition, and rerendering cannot repair history. |
| R13-CLEAN-1 | blocker | AGENTS.md §4–5 and reviewer cleanup hand-off | No reviewer-owned runs were removed in this review; removed paths/bytes: none/0. Activity, containment and symlink checks, role-owned removal and recorded bytes/pending failures remain required when the human-visible pack and dependencies can safely be retired. Never delete another role's work. |

**Independent numeric:** `build/add-shared-body-characters_r13_reviewer_try-1_numeric-diagonal/report.json` is 7.4 GB and has SHA-256 `2a1f8836732d707ba0cf09e472c08902275c1544433cf355de1d3decf2a2429a`. Bounded streaming inspection confirms `status=pass`, `numeric_status=pass`, diagonal-v1 exact skeleton 1.50, male 1.70 and female 1.90 and six unassessed pairs; individual leaf `status=incomplete` correctly keeps nonnumeric scopes unassessed while each leaf `numeric_status=pass`. Numeric rendering is `not-run`. Male/female dense each records 12,680 sampled character-beat pairs and `pass`, native and midpoint `pass`, no failures. Male worst native reference residual `1.0517143e-6 m` <= `1.7e-5 m`, floor `-8.94070e-8 m` >= `-1.7e-4 m`, sole distance `8.94070e-8 m` <= `1.7e-3 m`. Female worst residual `1.0027199e-6 m` <= `1.9e-5 m`, floor `-1.44243e-7 m` >= `-1.9e-4 m`, sole distance `1.44243e-7 m` <= `1.9e-3 m`. Skeleton surface-only checks are not applicable, while its selected numeric leaf passes. These bounds are respectively 1e-5H, -1e-4H and 1e-3H.

**Independent consumer:** `build/add-shared-body-characters_r13_reviewer_try-1_consumer-check/summary.json` and individual reports record both knees at 60 degrees at beat 2, the 17 animation/5 static BPM90 schedule and exact beat-to-seconds fractions. All three selected constructions have no failures; skeleton native pass with surface-only midpoint/dense not applicable, male/female native/midpoint/dense pass. Their consumer-only overall statuses remain `incomplete`, correctly, because this is not the 32-fixture diagnostic scope. No full acceptance is inferred from these reports.

**Independent workflow parity:** `build/add-shared-body-characters_r13_reviewer_try-1_workflow-parity/reviewer-parity-report.json` records separately traced source-built-wheel API, frozen-wheel API and frozen-wheel CLI producers for each pair, 19 samples per pair, matching prepared/request/metadata/manifest/evaluated/geometry/surface bytes and matching decoded images: skeleton 52, male 40, female 40 per route. Default/explicit skeleton input, request, metadata, geometry and evaluated bytes match; `.blend` bytes are not claimed identical. Reviewer separately checked 19 numeric/consumer/visual/parity construction roots: every version-probe and build/render receipt succeeded with return code 0 and frozen runtime manifest `ec5f1a7c010e90477a113e66a2c25e3765acca804ea5dae193e4007870819838`. The reviewer source snapshot retained all 201 frozen unique source/test/plan entries with zero changes on recheck.

**Provenance:** Character appearance/template YAMLs identify original authored CC-BY-4.0 work with no external character mesh. Skeleton definition inherits `hands-on-anatomy-2024` and `wang-2024-segment-lengths`, both registered with CC-BY-4.0 and attribution/derivative conditions. The publisher's Wang page explicitly confirms CC BY 4.0: https://www.nature.com/articles/s41598-024-66798-0. The indexed publisher project page states the Hands-on Anatomy authors and CC BY 4.0: https://temple.manifoldapp.org/projects/hands-on-anatomy; a direct recheck of its specific copyright-section URL timed out, so the previously recorded section-specific clearance and exclusion of separately licensed images remain the basis. No claim is made that unrelated third-party images are cleared.

**Human review after technical blockers:** Open `build/add-shared-body-characters_r13_reviewer_try-1_visual-a/index.html`, with each pair's arm-raise, squat, walking and shoulder/sole detail pages. Decide whether silhouettes, continuous junctions, movement direction/readability and planted/rolling feet are acceptable. The mixed-height overview is not a same-height shape comparison. Do not archive until the host decision, required role cleanup and explicit final Human Gate 2 are resolved.

### R13 full host coverage continuation — prepared, not yet run

Independent reviewer preflight at `build/add-shared-body-characters_r13_reviewer_try-1_host-fix-check/preflight.json` found 521 current host cases. Its ID inventory excludes the exact 97 current-R13 cases already independently passed, leaving 424 cases to run once; it separately records the seven ordinary host exclusions: six real-Blender backend tests and one real-Blender scene fault test. The prior 97-case receipt is SHA-256 `87c2cec93f6fa2770f5a5b56120b39037f82342a6aabd38f24297c7a83a54afb`. Installed-only and other skips will be recorded by individual case and remain unverified unless independently covered. The runner flushes per-case events to JSONL and records final summary and log; running, interrupted or skipped is never equated to pass.

During test discovery the frozen character-review-pack test intentionally loads its source-derived module and changes `humanmotionlib.__path__`. The first harness preflight detected six subsequently imported modules outside the candidate venv and stopped without running tests; the revised reviewer harness preloads their installed copies, restores package routing after discovery, checks all loaded package module origins and passed the same preflight. The source-derived test module remains bound to its frozen identical source file and is not claimed to be an installed-package import. These are reviewer harness observations, not production test failures. The 424-case execution, resulting coverage reconciliation and reviewer cleanup are pending.

## R13 independent host coverage closure — 2026-11-07

**R13-HOST-1 resolved for the approved host scope.** The exact R13 snapshot discovery contained 521 host case IDs; the previously documented independent 97 and the remaining 424 are disjoint and their union is exactly 521, with no missing/extra IDs. `..._r13_reviewer_try-1_host-fix-check/summary.json` records 424 run, 416 pass, 8 skips, 0 failures/errors; `events.jsonl` SHA-256 `17fd59c269ad96931a1147bb2ff36c69ab9112aa0f84f439071e3bf0c536a46e` has 424 start/stop pairs and exactly one pass/skip outcome for every selected ID. The two historical R10 suites remain failed under their old identities.

The eight skip reasons were examined individually. Seven `test_character_installation.InstalledCharacterAcceptance` cases were independently run with the frozen installed wheel in a decoy cwd and disposable workspace under `build/add-shared-body-characters_r13_reviewer_try-1_host-fix-source/`; all seven passed, with no Blender and simulated backend boundary. Identity, case names and scope are in `installed-acceptance-result.json`. The eighth, `test_project_cleanup.ProjectCleanupTests.test_real_process_cwd_and_open_file_block_cleanup`, was rerun by the orchestrator under elevated process-visibility access with `HML_TEST_REAL_PROCESS_VISIBILITY=1`, using only the reviewer-owned disposable tmp fixture; 1 test passed in 7.616 s. These reruns account for the skipped scenarios without changing the historical host report.

The host runner deliberately excluded six `tests.test_blender_backend` cases and one `tests.test_pipeline_faults` case. Their exact tests were **not run or claimed passed**: they include the full three-stature skeleton matrix, outside the human-approved remaining diagonal, and a separate real-scene fault harness. For the current change the independent selected-pair native/numeric constructions and two clean render passes per approved pair, plus focused semantic and integrity fault controls, supply the approved replacement scope; historical cross-stature/fault test verdicts retain their own identities. This is not a full backend matrix claim. The reviewer source/test/plan snapshot was rechecked after execution: 201 frozen entries, zero hash mismatches.

**Updated scoped technical verdict: PASS WITH NOTES** for the approved diagonal and host scope, subject to the two documented procedural deviations R13-PROC-1/2. The independent pack is `build/add-shared-body-characters_r13_reviewer_try-1_visual-a/index.html`. This does not confer human Gate 2. **Overall completion remains pending**: R13-CLEAN-1 is still open; no reviewer cleanup was performed because the pack and its dependencies are needed for human review, and removed paths/bytes remain none/0. After the human decision, conduct the required owner-scoped cleanup checks and record removal/bytes or explicit pending failures before declaring the hand-off complete. Do not archive before an explicit final visual decision and required cleanup.

## Final R13 reviewer verdict and role cleanup — 2026-11-07

**Final reviewer verdict: PASS WITH NOTES** for the approved diagonal and host scope. The human's final visual decision is recorded in `approvals.md`: “да, принимается”, bound to `build/add-shared-body-characters_r13_reviewer_try-1_visual-a/index.html`. The six other character/stature pairs, full native batch parity, native cross-stature comparison and the seven explicitly excluded real-Blender test methods remain unassessed, not passed. Notes R13-PROC-1/2 remain true as historical procedural deviations; accepting the result does not make the original crop ordering or developer numeric output path compliant. No fresh numeric or visual pass is represented as the old identity.

**R13-CLEAN-1 resolved for this reviewer run.** After Gate 2, the orchestrator ran the reviewer-owned bounded cleanup script; its durable receipt is `build/add-shared-body-characters_r13_reviewer_try-1_host-check/cleanup-transient.json`. Fresh `ps` and `lsof` checks passed, selected roots/parents were real and inside build, 301 links were checked without traversal and no inbound links were found. Only the following reviewer-owned obsolete extraction/temporary synthetic areas were removed; byte counts refer to regular-file apparent bytes, not disk allocation:

- `build/add-shared-body-characters_r13_reviewer_try-1_focus-check/`: 42,307,646 bytes.
- `build/add-shared-body-characters_r13_reviewer_try-1_sdist-source/`: 1,959,190 bytes.
- `build/add-shared-body-characters_r13_reviewer_try-1_host-fix-check/cases/`: 4,564,399,292 bytes.
- `build/add-shared-body-characters_r13_reviewer_try-1_host-fix-check/build/`: 273,276 bytes.
- `build/add-shared-body-characters_r13_reviewer_try-1_host-fix-source/disposable/`: 8,622,686 bytes.
- `build/add-shared-body-characters_r13_reviewer_try-1_host-fix-source/workspace/`: 141,321,900 bytes.

Total removed: **4,758,883,990 regular-file bytes**, 3,044 files, and 26 symlink entries unlinked without following targets. All six paths were absent after cleanup; a post-removal no-follow scan found zero inbound links. Pending reviewer cleanup failures: **none**. The accepted final pack, numeric and consumer reports and source inputs, parity runs/report, source snapshot, candidate and package closure, per-case host events and installed-acceptance result remain because they substantiate the final review; the developer's frozen wheel and all developer/other-reviewer runs were untouched. Prior references to the removed `focus-check` and extracted sdist root remain historical: their scoped results and identities are recorded above, and those intermediate trees no longer exist. The removed extracted sdist can be reconstructed from the retained reviewer candidate archive if needed.
