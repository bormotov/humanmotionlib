# Developer hand-off

Implementation and developer verification for `harden-backend-process-execution` are complete. The independent reviewer has passed the current-source tests, numeric builds and paired render checks; human visual gate 2 remains pending. This hand-off distinguishes historical developer evidence from the current independent review outputs.

## Implementation and verification

The shared supervisor in `tools/runtime.py` now owns finite-deadline child execution, receipts/logs, serialized backend ownership and conservative process-group cleanup. `tools/run_blender.py` is the normal supervised build entry point; version probes, backend tests and review-pack render passes use the same boundary. `tools/build_skeleton.py` flushes phase markers and only marks completion after outputs are saved and validated. Pack reuse checks successful current receipts and unchanged output hashes; HTML-only generation does not probe or launch Blender. Backend/fault tests were migrated to owned roots and preserve the existing fault contract.

Developer checks completed:

- `./.venv/bin/python -m unittest -f tests.test_runtime tests.test_run_blender tests.test_review_pack_supervision tests.test_review_presentation tests.test_review_graphics tests.test_review_aspect tests.test_source_integrity tests.test_source_schemas`: 54 passed in the outside-sandbox context. A sandboxed attempt had `ps` return EPERM; this was recorded as an environment limitation. After fixing owner-death test correlation to the current invocation ID and adding owned-ID-only `finally` cleanup, the focused owner-death case passed 1/1. The synthetic runtime suite had passed 19/19 before that test-only race correction.
- `./.venv/bin/python -m unittest -f tests.test_blender_backend`: 6 passed, with backend operations serialized through the supervisor.
- `./.venv/bin/python -m unittest -f tests.test_pipeline_faults`: 1 passed; the harness completed all ten fault rows with the expected output contract.
- `./.venv/bin/python tools/validate.py --profile adult-reference-v1`: `valid-sources`, 180 structures, 67 actions, 32 fixtures.
- The separately authorized one-shot diagnostic in `build/harden-backend-process-execution_r1_dev_try-6_checks/` passed its pinned probe and harness using the same prepared input hash as sandboxed try-4. It is evidence of different observed outcomes in those two recorded launch contexts, not proof of a sandbox defect or of a common cause with the original user reports. The try-4 native failure remains unresolved diagnostic evidence; no further crash retry was made.

The grouped synthetic/HTML/source run and focused backend/fault runs were recorded in the r2 checks roots. Those outputs were retained during implementation and have since been removed after the independent reviewer reproduced the required checks from a clean current-source snapshot. Historical counts and outcomes remain summarized below; they are not dependencies of the reviewer report.

## Numeric build and developer pack

The developer smoke build was formerly `build/harden-backend-process-execution_r2_dev_try-1_build/`. It used the frozen neutral/rest/arm-raise subset, H=1.70 m and BPM 60/120/180. Prepared identity was `8418ec846de10fcd84b5fe93e71775dae30d368d3b8c6482369c4826bd1cc411`; metrics SHA-256 was `842933558aadc999ac5260ee5cea0b7066f061197f4281b62a4c26fa711a067d`. All 31 samples passed backend and transform checks. The verifier's raw aggregate remained `fail` only because 29 diagnostic fixtures were intentionally omitted; complete diagnostic coverage was not claimed. The output root was removed after independent numeric builds superseded it.

The two-pass developer pack was formerly `build/harden-backend-process-execution_r2_dev_try-1_pack/`. Both passes used pinned Blender 5.2.2 LTS build `d13f752e3b9c`, matching prepared hashes and successful supervised receipts. Exact decoded RGBA comparison passed for 76/76 images in the recorded comparison set; all six GIF timing checks passed. It included the requested 4×2 neutral/rest and 5×4 arm-raise paired sheets, front/side animation sheets at BPM 60/120/180, six GIFs and front/side BPM-120 onion overlays. Generated HTML and metrics were not hand-edited. The pack root was removed after the independent reviewer produced and verified its own current-source pack.

The historical paired-sheet recipe used `tools.review_graphics.sheet` with the fixed-camera cells in the design's stated order and regenerated the index with `tools.review_pack.write_html`. Metrics were copied from the build verifier output. Those generated sources and outputs were removed with the superseded developer pack; the independent reviewer pack is the current visual evidence.

## Source audit and incident evidence

No external material was consulted or used for implementation or the acceptance pack; no `docs/used-materials.md` entry was required. The user-supplied crash reports remain outside repository outputs. `docs/backend-crash-triage.md` summarizes their evidence and uncertainty. `operator-decisions.md` records the authorized single diagnostic attempt and the later supplemental macOS report, correlated to the same try-4 incident. Neither the crash evidence nor the successful try-6 outcome establishes an upstream, Metal, OOM or sandbox cause.

## Run inventory and cleanup

The initial r1 checks baseline `build/harden-backend-process-execution_r1_dev_try-1_checks/` was removed after independent review superseded it. The r1 `try-4_checks` root remains because it contains unresolved native-failure evidence; the r1 `try-6_checks` root remains because it contains the authorized one-shot diagnostic and successful comparison. Those two protected roots remain linked from `operator-decisions.md` and are intentional dependencies.

The following obsolete r1 checks roots were confirmed absent after whole-root cleanup: `try-2`, `try-3`, `try-5`, and `try-7` through `try-14`. Their pre-cleanup regular-file inventory totaled 214,928 bytes. The independent wrapper-test helper removed its obsolete `build/harden-backend-process-execution_r2_dev_runner-1_checks/` (empty) and `build/harden-backend-process-execution_r2_dev_try-1_checks/` (805-byte stale snapshot); see `runner-tests-handoff.md`. The helper confirmed both were direct, non-symlink children with no retained consumers. No symlinks were followed. The linked primary integration and pack evidence was checked before retaining it.

The r2 checks roots `try-2` through `try-11`, numeric build and developer pack were retained during implementation and then removed after current-source independent review superseded them. The r3 checks roots `try-7` through `try-9` were likewise removed after independent synthetic/backend/fault tests, numeric builds and render pack superseded their evidence. Before removal, a repository search found no reviewer or operator-decision dependency on any of these developer roots. The checkout coordination files `build/.backend-execution.lock` and `build/.backend-execution-state.json` remain in place by protocol; state was `finished` at inventory time. No other agent's active run or protected history was removed. No cleanup remains pending for developer-owned obsolete roots.

## Handoff boundary

The source is frozen. The reviewer has completed independent checks and output generation; the developer pack was not used as independent proof. Human visual acceptance remains pending. Developer tasks 3.2, 3.3 and 3.6 are complete.

## R3 follow-up after independent review

The earlier r1/r2 sections above are historical implementation and acceptance-pack evidence. The independent review at `review.md` found that a zero-exit leader could leave a live group descendant while the supervisor released the slot, and that stock suites were tied to developer roots. Both findings were addressed before this source freeze; the reviewer must independently recheck them against this revision.

For F1, the direct child remains unreaped as a process-group identity anchor until group observation and any TERM/KILL cleanup finish. The Python 3.12 reference runtime does not expose `os.waitid`, so Darwin uses a bounded `/bin/ps` snapshot. A matching leader PID+PGID in zombie state proves that the leader exited; a matching group with only zombie entries has no live work, while any non-zombie entry remains present. An empty/malformed/unreadable snapshot while the leader is anchored is ambiguous. Without an anchor, an empty Darwin snapshot is absent only if `killpg(..., 0)` independently returns ESRCH; EPERM stays ambiguous. Signals are sent only to the current invocation's anchored group; unconfirmed cleanup keeps ownership pending. The r3 try-4 failure receipt captured the issue that drove this correction: `ps` showed the owned leader as `Z`, but the earlier raw `killpg(..., 0)` check returned ambiguous before the readable snapshot could be used. That diagnostic root is superseded by the passing try-7 synthetic suite and is inventoried below, not retained as an unresolved native incident.

For F2, `tests/run_roots.py` accepts `HUMANMOTIONLIB_TEST_RUN_ROOT` as an existing, fresh five-component direct child of `build/`, and places suite cases below `cases/<module>/`. Importing the runtime, wrapper, backend and fault test modules does not allocate roots. With the variable unset, each suite allocates a developer-owned root lazily. The same caller-owned root was used for the grouped runtime/wrapper/presentation checks and the backend/fault checks; no developer root was written by the reviewer run.

R3 verification on the current implementation:

- `build/harden-backend-process-execution_r3_dev_try-7_checks/`: `tests.test_runtime`, `tests.test_run_blender` and `tests.test_review_pack_supervision` passed 33/33 in 14.03 seconds. This includes direct-child zero/nonzero exit with live descendants, cleanup and unrelated sentinel survival; queued SIGINT/SIGTERM ownership; slot serialization, owner-death recovery, contention and ambiguous-owner handling; the complete invocation receipt/output contract; import-side-effect and caller-root checks. Its source snapshot records `tools/runtime.py` SHA-256 `f16e43c626a8212f0c7079f7d20a9745405e912e0e93de089659ff27910db574` and exact test/module hashes. This root was removed after independent tests superseded it.
- `build/harden-backend-process-execution_r3_dev_try-8_checks/`: fail-fast source-integrity, presentation, graphics/aspect and backend integration completed 25 tests successfully, including six backend tests and the supervised pinned Blender 5.2.2 LTS build `d13f752e3b9c`. The run then exposed a test-declaration error (`@staticmethod` on a method that uses `self`) before the fault harness could launch. No native failure occurred. The root was removed after independent outputs superseded it.
- The test declaration was corrected by removing that decorator. `build/harden-backend-process-execution_r3_dev_try-9_checks/` passed `tests.test_pipeline_faults` 1/1 in 9.92 seconds. The supervised harness produced all ten expected fault rows, the `faults.json` completion contract and ordered `faults_written`/`script_complete` phases. No automatic retry was performed. This root was removed after independent fault testing superseded it.
- `./.venv/bin/python -m py_compile` passed on the changed runtime and test modules; `git diff --check` passed. The direct launch-site search found no routine Blender subprocess outside `tools/runtime.py`; low-level commands documented in `tools/README.md` remain diagnostics only. No dependencies, backend pins, renderer or environment settings changed.

The r3 source snapshots identified the exact tested sources before cleanup. The checkout slot state was `finished` after the last supervised operation. No Blender child, test command or approval request remained active. The r2 numeric smoke build and paired developer pack were not regenerated after the r3 correction because it changed process ownership and test setup, not sampling, geometry or rendering; the reviewer generated current-source numeric and render outputs independently.

## Independent reviewer result

The final independent current-source review passed 64/64 tests: 57 source/runtime/presentation checks, six backend tests and one fault-harness test. Two independent numeric builds each passed all 31 samples with maximum repeat difference 0. Two clean render passes matched on 76/76 decoded RGBA images; all six GIF timing checks passed. The reviewer also verified 236 pack links, 170 output hashes and 28 original paired cells. Evidence is in `review.md` and reviewer-owned roots `build/harden-backend-process-execution_r3_reviewer_try-1_checks/`, `build/harden-backend-process-execution_r3_reviewer_try-1_build/` and `build/harden-backend-process-execution_r3_reviewer_try-1_pack/`. The earlier `build/harden-backend-process-execution_r2_reviewer_try-1_checks/` was removed by its owner after `review.md` durably summarized the F1/F2 reproduction and resolution; no current report link depends on it. No reviewer output depends on developer-owned roots. The human visual gate is still pending; no visual acceptance is claimed.

R3 run inventory and cleanup:

| Path | Decision | Regular-file bytes |
|---|---|---:|
| `build/harden-backend-process-execution_r3_dev_try-1_checks/` | Removed; empty allocation. | 0 |
| `build/harden-backend-process-execution_r3_dev_try-2_checks/` | Removed; stale source snapshot was superseded before any test. | 954 |
| `build/harden-backend-process-execution_r3_dev_try-3_checks/` | Removed; initial narrow regressions were superseded by try-7 after Darwin observation correction. | 10,245 |
| `build/harden-backend-process-execution_r3_dev_try-4_checks/` | Removed after recording the resolved EPERM/zombie diagnostic above; its failed 33-test run was superseded by try-7. It contained one local symlink, which was not followed. | 38,579 |
| `build/harden-backend-process-execution_r3_dev_try-5_checks/` | Removed; focused pass superseded by full try-7 synthetic suite. | 14,202 |
| `build/harden-backend-process-execution_r3_dev_try-6_checks/` | Removed; call-site test failure superseded by corrected full try-7 suite. It contained one local symlink, which was not followed. | 38,334 |
| `build/harden-backend-process-execution_r3_dev_try-7_checks/` | Removed after independent 64/64 test pass superseded the developer suite. | 39,974 |
| `build/harden-backend-process-execution_r3_dev_try-8_checks/` | Removed after independent backend/build checks superseded its successful outputs; the isolated test declaration error had already been corrected and separately passed. | 95,572,691 |
| `build/harden-backend-process-execution_r3_dev_try-9_checks/` | Removed after independent fault-harness testing superseded it. | 11,608,801 |

After reviewer completion, the following whole developer-owned roots were removed. The table records pre-removal regular-file bytes; no symlinks were followed.

| Removed path | Regular-file bytes |
|---|---:|
| `build/harden-backend-process-execution_r1_dev_try-1_checks/` | 22,012 |
| `build/harden-backend-process-execution_r2_dev_try-2_checks/` | 25,298 |
| `build/harden-backend-process-execution_r2_dev_try-3_checks/` | 29,556 |
| `build/harden-backend-process-execution_r2_dev_try-4_checks/` | 4,692 |
| `build/harden-backend-process-execution_r2_dev_try-5_checks/` | 16,780,392 |
| `build/harden-backend-process-execution_r2_dev_try-6_checks/` | 16,768,556 |
| `build/harden-backend-process-execution_r2_dev_try-7_checks/` | 16,756,740 |
| `build/harden-backend-process-execution_r2_dev_try-8_checks/` | 16,768,421 |
| `build/harden-backend-process-execution_r2_dev_try-9_checks/` | 6,723,528 |
| `build/harden-backend-process-execution_r2_dev_try-10_checks/` | 21,776,888 |
| `build/harden-backend-process-execution_r2_dev_try-11_checks/` | 11,607,907 |
| `build/harden-backend-process-execution_r2_dev_try-1_build/` | 136,083,084 |
| `build/harden-backend-process-execution_r2_dev_try-1_pack/` | 161,728,012 |
| `build/harden-backend-process-execution_r3_dev_try-7_checks/` | 39,974 |
| `build/harden-backend-process-execution_r3_dev_try-8_checks/` | 95,572,691 |
| `build/harden-backend-process-execution_r3_dev_try-9_checks/` | 11,608,801 |

Total removed: 512,296,552 regular-file bytes. Pre-removal symlink inventory found one local `cases/resolved-probe/blender-link` fixture in r2 try-2 and try-3 and one local `cases/runtime/resolved-probe/blender-link` fixture in r3 try-7; each pointed to its sibling `blender-real` file. No symlink was followed during whole-root removal. Before cleanup, the reviewer confirmed no reviewer output depended on any developer root. The r1 try-4 native-failure root and r1 try-6 authorized-comparison root remain intentionally protected and were not included in this inventory. Post-cleanup checks confirmed every listed root is absent, protected roots remain present, and the checkout lock/state coordination files were not altered. No developer-owned cleanup remains pending.
