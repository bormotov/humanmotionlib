# Implementation hand-off

## Authorization and scope

- Human Gate 1: the user invoked `$openspec-apply-change audit-project-tools` after reviewing and revising the proposal, design, specifications and tasks, including the three cleanup targets. This invocation authorizes implementation of that scope.
- The change is planned as nonvisual tooling work. An early visual preview is not applicable provided implementation does not change character, motion, scene or rendering behavior. Reassess if that changes.
- The user subsequently directed that explicit cleanup targets remove all contents within their defined build areas, including unknown files and historical R6 output, without ownership inventories or dependency preservation exceptions. The updated design and delta specs record this decision. This directs target behavior; it does not instruct this implementation session to run cleanup on the real workspace.
- `add-shared-body-characters` remains paused. Its accepted R6 preview currently exists at `build/add-shared-body-characters_r6_dev_try-1_visual-pack/index.html`; prepared SHA-256 `e3f83e70d8e7d3ac2a50c3fec59992de592a21296b370a66962f2311c5254df8`, render identity `29c4723c0f172b5cf739bcfd21d31c443b725df1c588181afb03e5e3281354ba`. No real character matrix, dense audit or final visual pack is authorized here.
- The approved command and audit inventory, including bounded positive/negative checks, is in `design.md` sections 1 and 6 and `tasks.md`. The four-role pre-freeze audit and independent checks are recorded below and in `review.md`.
- Existing uncommitted source changes and archived matrix work predate this implementation and must be preserved. Cleanup tests use disposable fixtures, not the real build tree.

## Progress and evidence

Implementation is complete for the owned Make orchestration, package/development workflow, cleanup integration, documentation and focused tests. Task 1.3 is complete with the bounded integrity evidence and explicit human decision recorded below.

### Baseline and environment

- A bounded retry in `build/audit-project-tools_r1_dev_try-8_baseline/` and `..._try-8_environment/` installed a wheel verified against the current source closure and locked dependencies, recorded pre-test diagnostics, and passed `uv pip check`. Read-only matrix listing succeeded and isolated `uv sync` reproduced the reported backend error. Before/after comparisons found no changes among 360 source-tree entries outside excluded areas, no changed direct `build/` entry except the two attempt roots, and no change to the R6 `index.html` hash. The approximately 184 GB of nested build contents were not fully hashed, so complete outside-area file integrity remains unverified. Details and snapshots: `build/audit-project-tools_r1_dev_try-8_baseline/attempt-report.md`.
- The reported Make failure is recorded in `build/audit-project-tools_r1_dev_try-1_baseline/make-matrix-list.log`: `/bin/sh: python: command not found`, exit 127.
- The reported legacy `uv sync` failure is recorded in `build/audit-project-tools_r1_dev_try-5_baseline/uv-sync.log`: the backend has no `build_editable`, exit 1.
- The isolated interpreter/settings report is `build/audit-project-tools_r1_dev_try-4_environment/pre-test-environment.json`; it records CPython 3.14.6, environment origin/prefix, dependency origins/versions, cache path, `.pth` contents and successful `uv pip check` at that point.
- No authentic pre-implementation source/R6 hash inventory was available. The fresh `try-7` attempt below therefore records only before/after integrity during that attempt; it does not infer an earlier historical comparison from later package identities.
- Fresh task-1.3 evidence: `build/audit-project-tools_r1_dev_try-7_baseline/` and `..._try-7_environment/`. This attempt built the exact wheel from the current checkout (SHA-256 `b8c5fcfdfac9f00bb25a8fdd8921257a8af3d131f9977d3204fed63034205197`), installed it and locked dependencies into a new uv environment, recorded interpreter/import origins/versions/`.pth`/cache/package identities, and passed `uv pip check`. Current `make matrix-list` succeeds; `uv sync` from the repository root, directed to the try-7 `sync-environment` and owned cache, reproduces the `build_editable` AttributeError. Command-only hashes cover regular files outside `.git`, `build`, `.venv` and `__pycache__`: 360 files, zero changed/added/removed. The excluded R6 visual-pack index currently matches its previously recorded post-check hash `97961f6803f53357b2cbdb8b9a128fb9241c680d322201f3555c2a6e5ed3064c`; no broader claim is made for other build entries. The failed package command created and retained its own diagnostic run `build/package-humanmotionlib_r1_dev_run-20261102t064839626385-10187_check/`. Exact scope and logs are in `build/audit-project-tools_r1_dev_try-7_baseline/task-1.3-results.md`. Earlier `try-1` through `try-5` runs had no complete baseline environment; try-4 and try-6 remain later candidates, not historical baseline evidence.

### Implemented behavior and historical evidence

Package and source identities in this section describe earlier runs and are not the final frozen candidate. See the pre-freeze audit record for the current identity.

- Make help/list are Python-, uv- and Blender-free. Help names GNU Make 3.81+, POSIX shell, uv 0.11.21+, first-run network needs, CPython 3.14, supported host evidence (macOS arm64 and Ubuntu 24.04 x64), native Windows limitation, and the pinned rendering-only Blender requirement. `env PATH=/usr/bin:/bin make` and `make matrix-list` passed; matrix listing also passed with a workspace path containing spaces.
- Tool preparation reads `tools-root` and `uv-minimum` from project settings, keeps uv cache/Python downloads/environment under the project build root, pins the Make workflow to that prepared interpreter, reuses a valid partial interpreter and safely recreates an invalid one. Path/symlink and ambient-interpreter override controls are in `tests/test_repository_workflow.py`.
- Package verification compares full canonical resource and Python-module closure with source, including backend-generated `_version.py`; source snapshots detect additions/edits/deletions and reject symlinks. Negative controls cover omitted resource and module entries.
- Successful `make dev` report: `build/package-humanmotionlib_r1_dev_run-20261031t120346386872-51645_stage/development-readiness.json` (status `ready`; wheel identity and source validation passed).
- Successful `make package` report: `build/package-humanmotionlib_r1_dev_run-20261031t124159009691-65117_package/package-result.json` (status `verified`). Direct wheel and sdist built; wheel rebuilt from sdist matched all 116 runtime files. Wheel SHA-256: `8669758d4ada490d81d1426c2edb0e87201ce3eb6c384ab0e3111fc3d827a01a`; runtime manifest SHA-256: `d4566be074f1bc68292648bfb37fe25bc1e0bc636936544e05895492a36f2e49`.
- Rechecked that exact wheel against the current canonical package inputs after the run: source closure digest `fab53ee256daf3d41fdfecf5fc70adb876851ae82b5d8ce0517f683db9c69c81` over 118 entries; full package closure verification passed (50 implementation modules, 64 runtime resources). This is a current/post identity, not a retroactive pre-build hash.
- Independent exact-wheel install and diagnostics: `build/package-humanmotionlib_r1_dev_run-20261031t124159824876-65117_check/installation.json` and `pre-test-environment.json`. Locked dependency install/check, console/module version, host check, installed source validation and one bounded neutral preparation all passed. Preparation is in sibling root `build/package-humanmotionlib_r1_dev_run-20261031t124208233220-65117_stage/input.json`. Blender and publication were explicitly not run.
- Focused suites passed: `tests.test_repository_workflow` (11), `tests.test_project_cleanup` (25 with one process-visibility skip), and `tests.test_matrix_workflow` (21 on the exact installed package environment). The matrix suite includes literal Make-route assertions, controlled build/check repetition, package-identity mismatch and no-generation failure cases. `sh -n`, workflow YAML parsing and `git diff --check` on owned paths passed.
- Cleanup policy is fixed-area, no markers/inventories/reference scans, with activity and containment checks. Synthetic disposable-tree tests cover levels, unknown/history removal, symlinks, incomplete activity visibility, interruptions and external `WORKSPACE` configuration. The literal `make clean WORKSPACE=<external workspace>` integration test passed with deliberately different workspace settings; real build cleanup was not run.
- CI now smoke-runs Make help/list with Python removed from PATH and invokes the standard `make dev` route. Contributor guides and AGENTS/role guidance describe matching defaults and cleanup.

### Task-range inventory for orchestration

- **1.3 — complete:** the human's explicit decision in the message “побайтно сравнивать не будем, считаем что пройдено” accepts the bounded try-8 comparison above. Byte-by-byte comparison of all nested build contents was skipped; their full integrity was not verified and no such claim is made. The occupied original roots were preserved and fresh sibling retry roots used. Earlier try-7 evidence and its interrupted full-build scan remain recorded above.
- **2.1 — complete:** existing help, documented prerequisites and defaults were checked with the bounded run `build/audit-project-tools_r1_dev_try-9_command-check/`. Literal `make`, `make help` and `make matrix-list` succeeded with no Python, uv or Blender on PATH; missing/invalid choices returned guidance before preparation. All nine table rows and paths matched the direct matrix listing, including in a checkout path with spaces. Snapshots showed no writes to the disposable checkout or source files. Logs and exit statuses are in that run; no code changes were needed for this task.
- **2.2 — complete:** disposable runs `build/audit-project-tools_r1_dev_try-10_integration/task-2.2-report.md` and `build/audit-project-tools_r1_dev_try-11_isolated-workspace/no-global-source-write-report.md` document initial preparation, network-assisted recovery from a DNS failure, successful reuse, locked dependencies and unchanged lock/configuration. Missing uv, wrong Python and controlled installation failure stop before later stages; 12 focused workflow tests passed. The isolated HOME/XDG directories remained empty and the 360-file source snapshot unchanged during the checked commands; imports resolved within the intended environment. These observations are limited to the documented snapshot scope. No implementation fix was needed.
- **2.3 — complete:** `build/audit-project-tools_r1_dev_try-12_source-refresh/task-2.3-report.md` records repeated package builds at unchanged version, disposable Python/YAML edits reaching installed source identities and prepared data, and a controlled build-time edit rejected before install. The rejection now also appears in the build log; its regression test and the focused workflow suite passed (13 tests). A controlled old-result fixture was rejected with the rebuild remedy while its recorded inputs and sentinel remained unchanged. No Blender or real rendering was run.
- **3.1 — complete:** `build/audit-project-tools_r1_dev_try-13_development-readiness/task-3.1-report.md` records literal `make dev` from an initially unprepared disposable checkout and a successful repeat after a Python source edit. Both reported readiness and next actions; the second rebuilt the changed package using the existing environment. The first DNS failure and network-assisted continuation are recorded. No Blender or full host, dense or render workload was run.
- **3.2 — complete:** `build/audit-project-tools_r1_dev_try-14_matrix-controlled/task-3.2-report.md` records automatic package preparation before the selected build, the one-pair neutral/rest/arm-raise BPM120 recipe and fixed paths, repeat, setup-failure preservation and late-failure diagnostics/cleanup. Controlled generation only; no Blender or visual acceptance. The full matrix workflow module passed 21 tests using the try-13 installed candidate (which includes a disposable Python comment); its host-dependent uv dry-run assertion was corrected to specify `UV=uv`. The report preserves the earlier stale-package errors and the exact tested identity.
- **3.3 — complete:** `build/audit-project-tools_r1_dev_try-15_matrix-check/task-3.3-report.md` records actual validators exercised on synthetic results, repeat and damaged-file controls, an empty unprepared workspace, and rejection of a stale package with the selected rebuild remedy. Original prepared input, build record and image/render sentinels remained unchanged. The matrix workflow module passed 21 tests using the documented try-13 installed candidate. No real rendering or visual acceptance was run; no implementation fix was needed.
- **3.4 — complete:** `build/audit-project-tools_r1_dev_try-16_package-fresh/task-3.4-report.md` records the initially unprepared disposable checkout, DNS failure and successful network-assisted literal `make package`. The direct and source-archive-rebuilt wheels matched, and the independent exact-wheel check passed diagnostics, CLI/module, tools, installed-source and bounded neutral preparation. A controlled dependency-install failure stopped the independent check and produced no verified package report. Blender and publication were not run.
- **4.1 — complete:** `build/audit-project-tools_r1_dev_try-17_cleanup-scope/task-4.1-report.md` records the fixed selector review, observed producer directory names and four passing disposable-tree checks, including nested unknown/hidden/history deletion and outside-area preservation. Selection does not depend on ownership inventories or historical references. No real workspace cleanup ran.
- **4.2 — complete:** `build/audit-project-tools_r1_dev_try-20_cleanup-minimal-path/results.json` and `run_checks.py` record literal Make cleanup and repeat calls on disposable checkouts with spaces, a minimal PATH without Python/uv, damaged tools, a custom tools root and exact removed paths/bytes (12, 13 and 16 bytes). Fixture configuration, lock, release and an external cache sentinel remained unchanged. The actual personal cache was not enumerated; the outside-area sentinel represents that boundary. Real process inspection was available for the successful run; an earlier sandbox attempt failed closed before deletion. No real workspace cleanup ran. Additional details are in `build/audit-project-tools_r1_dev_try-19_cleanup-targets/task-4.2-report.md` (its PATH included system Python 3).
- **4.3 — complete:** `build/audit-project-tools_r1_dev_try-21_cleanup-safety/task-4.3-report.md` records the disposable-tree suite (24 passing, one real-process test skipped in the restricted run) and a separate successful real-process rerun with process visibility. The tests cover active work and unavailable inspection, containment and no-follow behavior, unknown/history removal, and simulated permission/interruption with pending-work reporting. No actual power loss or kernel crash was simulated; no real project build area was cleaned.
- **4.4 — complete:** after the human approved the clarified missing-result preflight, `tools/matrix.py` and `tools/repository.sh` were updated and strict OpenSpec validation passed. `build/audit-project-tools_r1_dev_try-22_restoration/task-4.4-observations.md` records disposable cleanup and restoration after all three levels, no-write missing-result checks through both entry points, retained logs for existing invalid results, successful `make package` after distclean, and controlled selected-build checks without Blender. Matrix/repository tests passed 39/39. A selected external link was unlinked during clean without changing its target; the separate distclean link setup raced with cleanup, so that particular unlink was not independently proven. The earlier 3.3 missing-result logging evidence remains historical and is superseded by the clarified behavior and new checks.
- **5.1 — complete:** the durable `tooling-audit.md` maps the supported operations to commands, bounded evidence, concrete gaps and next actions; detailed logs are in `build/audit-project-tools_r1_dev_try-23_tool-audit/`. Installed help/validation/environment checks and read-only release planning succeeded, and 46 focused tests passed. Matrix/usage guides now describe the clarified no-write missing-result check. The audit explicitly leaves real Blender rendering, complete numerical/visual acceptance, full host suite and live release-state queries to their respective workflows; no publication ran.
- **5.2 — complete:** `build/audit-project-tools_r1_dev_try-24_docs-ci-alignment/task-5.2-report.md` records the guide/role/CI reconciliation. Host CI now uses `make dev`, the configured tools root and project-owned uv cache; local environment, dependency and source-validation smoke checks passed. The reviewer instruction was updated with authorized access to the three approved review roots and no archived-change exception; TOML and workflow YAML parse. Release gates remain unchanged. Local uv 0.11.21 was exercised; CI pins 0.13.5 but GitHub Actions and the full host suite were not run here.
- **5.3 — complete:** `build/audit-project-tools_r1_dev_try-1_integration/task-5.3-report.md` records the fresh disposable checkout, verified package, development and command routes, Python/YAML change controls and restoration after all cleanup levels. Focused suites passed, with one real-process test skipped in the restricted aggregate run; task 4.3 records its separate successful process-visible control. Lock/configuration remained unchanged and checksum comparison found only the two deliberate source edits in its stated scope. Controlled generation does not establish rendering/domain acceptance; no Blender, dense suite or character matrix ran. At that checkpoint, developer-owned run cleanup remained pending; it completed under task 6.3 with `exit 0` and `pending 0`.
- **5.4 — complete:** joint pre-freeze audit and candidate identity are recorded below. At the 5.4 checkpoint, independent reviewer build/review and final cleanup were pending under 6.x; the independent review is recorded in tasks 6.1–6.2 and the dev cleanup completed under 6.3.

### Four-role pre-freeze audit and candidate

- **Orchestrator:** reconciled approved scenarios, task evidence and outstanding actions; corrected obsolete pending statements and distinguished earlier package identities from the candidate. The human's decision to accept bounded integrity evidence for 1.3 remains recorded above.
- **Architect:** audited requirements, documentation, cleanup overrides and independent-review plan. The `mostlyclean` tools-root exception is now consistent in design and guidance; package CI uses uv-created environments and pre-test diagnostics. The reviewer plan separates a pristine source snapshot from a disposable selected workspace, with explicitly bounded subordinate Make outputs.
- **Developer:** reconciled the historical setup example, package CI environment/diagnostic steps, AGENTS and matrix guidance. Focused cleanup and guide checks passed; workflow YAML and shell steps were checked. GitHub Actions itself was not run locally.
- **Reviewer:** examined scenarios, controls, process-access requirements and the three reviewer roots. The previously conflicting reviewer workspace instruction was clarified; no remaining pre-freeze technical blocker was identified. This joint audit is not the independent review.
- **Visual gate:** not applicable to this nonvisual tooling change. The changes affect orchestration, cleanup, diagnostics, CI and guidance, not character, motion, scene or rendering behavior. Pre-existing character work and its R6 decision remain separate and paused; no visual acceptance is inferred.
- **Frozen source identity:** 328 regular in-scope files, aggregate SHA-256 `37b4e78367affe16a50e7a4b6030ccd02f1b1b0ef1da467e1f8e490929b27e8d`. Before/after package and current-workspace inventories match; exact scope, exclusions, individual file hashes and aggregate calculation are recorded in `build/audit-project-tools_r1_dev_try-27_clean-package/source-identity-before.json`, `source-identity-after.json` and `source-identity-workspace-current.json`. The scope includes source, tools, CI, documentation, role instructions, data and OpenSpec artifacts; it excludes generated state, environments and mutable hand-off/task/review reports. The exact inventory is preserved in this hand-off before role cleanup.
- **Candidate package:** unchanged source copy `build/audit-project-tools_r1_dev_try-27_clean-package/source/`; `make package` returned `verified`. Direct wheel SHA-256 `0b191e644a0734f2c35eac5bf80e7b4d8f232efa8bcaea3889ee9c0a4356d179`; sdist SHA-256 `f0c82e45f33082f1759e1bd0b1d8a9f07da4d484ed35fb2f207aad84c329a74d`; rebuilt wheel SHA-256 `86e5bb21b9db81244793c1dd05784e513f591260b660c6b27a56d9944cda5b5e`. The runtime closure comparison passed for 116 files with SHA-256 `f0822906c66fa10677683ac603b1e233875d5d7cb57afd3aff78c416c9812794`; the wheel archive hashes differ, so parity refers to the compared runtime closure, not byte-identical wheel archives. Full details and independent-install diagnostics are in `build/audit-project-tools_r1_dev_try-27_clean-package/package-audit-evidence.md`.
- **Technical-only reviewer retry amendment:** reviewer try-1 temporarily created staging and bytecode within the source snapshot; despite unchanged source hashes, that attempt does not satisfy disjoint input/output and is not credited. Fresh reviewer try-2 sibling roots were authorized in `.codex/agents/reviewer.toml` using the recorded planning patch. The amended current source identity is 329 files, aggregate SHA-256 `ae2cd22825b41fc76ac5f657264631570bd81657033751c21dfeca4c67ddd92b` under the same scope as above. Only the reviewer role instruction and the added retry patch differ from the previous inventory. All 116 current runtime-closure entries match the try-27 wheel; the amended inventory is preserved below. This process-only change does not alter visual scope; the independent rebuild and checks are recorded in tasks 6.1–6.2 and `review.md`.
- **Remaining at this checkpoint:** final reconciliation and validation are task 6.4. No Blender, dense or character matrix work is authorized here.
- **6.1 — complete:** the reviewer independently rebuilt the amended candidate in disjoint try-2 roots, installed its exact wheel with locked dependencies in a fresh uv environment, and recorded pre-test diagnostics and passing `uv pip check`. All 116 runtime files matched the candidate; the pristine source snapshot stayed unchanged. Independent wheel SHA-256 `721912360f5697bcf3ae6edbea88b10d8059bc75a3534b9111e741c9a8e07600`; evidence and the unaccepted try-1 attempt are documented in `review.md`. Independent scenario review and final verdict remain pending.
- **6.2 — complete:** `review.md` records independent package/dev and controlled selected-matrix walkthroughs, changed-source and failure controls, all disposable cleanup/recovery levels and process-visible active-work checks. The aggregate had 63 passes and one gated skip; the skipped real-process case passed separately, and 42 release/presentation/guide tests passed. Literal matrix generation used a documented reviewer-owned test hook with synthetic outputs and mocked validation; no Blender or visual acceptance ran. No finding was reported for the exercised scenarios; the final verdict remains pending, and role cleanup completed under task 6.3.

### Scope still pending for the orchestrator/reviewer

- The aggregate cleanup suite skipped its gated real-process test in the restricted environment; the separate successful process-visible test is recorded under 4.3. The independent reviewer verified process access and repeated the real-process test successfully, as recorded in `review.md`.
- No real selected matrix render/check was run: rendering is Blender-dependent and character verification remains paused. No Blender, dense, stature/tempo matrix, R6 or final acceptance work was started.
- Cleanup restoration and disposable-source integration were completed as recorded in 4.4 and 5.3. No broad cleanup ran against the real workspace. Dev role-assigned cleanup and its accounting completed under 6.3; final reconciliation remains under 6.4.
- The tool audit records bounded evidence and outstanding actions for general movement, rendering, numerical acceptance and release operations. Independent reviewer runs are recorded in `review.md`; final reconciliation remains task 6.4.

The source tree remains shared with paused character work. The frozen candidate and independent review above do not constitute character or visual acceptance.

## Task 6.4 final reconciliation

Independent review concludes **PASS WITH NOTES** for the approved nonvisual tooling scope; see `review.md` for its evidence and limitations. The amended candidate inventory records 329 files with aggregate SHA-256 `ae2cd22825b41fc76ac5f657264631570bd81657033751c21dfeca4c67ddd92b`; a final comparison found no changed or missing files among those entries. That comparison did not separately enumerate newly added files. The developer candidate wheel SHA-256 is `0b191e644a0734f2c35eac5bf80e7b4d8f232efa8bcaea3889ee9c0a4356d179`, the independent reviewer wheel is `721912360f5697bcf3ae6edbea88b10d8059bc75a3534b9111e741c9a8e07600`, and their 116 runtime entries matched (`f0822906c66fa10677683ac603b1e233875d5d7cb57afd3aff78c416c9812794`); the distinct archive hashes are not presented as identical wheels.

The user accepted task 1.3 without bytewise comparison of all existing build data and approved the missing-result check clarification. Task 6.3 recorded completed dev and reviewer cleanup with zero pending failures. Visual review is not applicable to this tooling change; character work and its visual decision remain separate. Controlled matrix generation used synthetic outputs and mocked validation, not Blender. Full host/dense suites, real rendering, and live publication were not run.

The earlier `tooling-audit.md` recommendation to run the full host suite before independent review was not fulfilled in this audit. The approved design and tasks call for selected bounded checks; the full host suite remains a separate follow-up, not completed evidence. The historical audit file remains part of the frozen candidate, so this clarification does not change the checked source identity. Other gap actions for general motion authoring, numerical/visual acceptance, real pack reuse and live release checking remain as recorded in the audit and review. Strict `openspec validate audit-project-tools --strict` passed.

## Task 6.3 dev cleanup evidence preservation

This record preserves the dev evidence needed for final reconciliation after role cleanup. The parent-run cleanup has completed successfully; its final receipt is recorded below. The concrete integration assignment for task 5.3 is `build/audit-project-tools_r1_dev_try-1_integration/` (55,276 KiB); the complete set of direct dev-labeled runs for this change is listed below because earlier task evidence and retries also reside there. All are direct children of `build/`; no reviewer or other-role roots are included.

### Durable task 5.3 result

The disposable checkout package route completed with status `verified`; the candidate was HML 0.3.0, runtime manifest `24927ddcb35108895eb9c53be0f2b466ae9596e63c7abab721c93f500ff60260`, wheel SHA-256 `135204c0ab7a0affcf4b90c7b063c100c62f89162f29cbf7f399705a9c2dd0c0`. Argument-free `make`/`make help` and matrix listing passed; missing matrix selections and absent-result check returned guidance without preparing or writing a result. Disposable Python and YAML edits reached installed package identities `56b21f5a17c731fca2b2a7f4ce19893c8979fd1efdcefea797250a801daf137b` and `00ede8dd7e38820b9f72e1a2989fb95b4d93e141b2b01866500653171ca7557f`; the lock hash stayed `a47b8d29266ffb83a8d22135bb8d724780b2ee71097b0943fe427bc44bd47225`. The focused aggregate passed with one gated process-visibility skip; the preserved summaries disagree on its exact test count; a separate process-visible check passed under task 4.3. All three cleanup/recovery routes passed in the disposable checkout, with no pending failures. The full detailed report was removed with its dev run root; this summary preserves its decision-relevant results.

### Dev-root cleanup accounting

The initial `du -sk` preparation snapshot covered 37 direct dev roots and 916,000 KiB (937,984,000 bytes). The parent-run cleanup completed successfully (`exit 0`, `pending 0`). The root listing below is an initial preparation snapshot, not a cleanup selection manifest or current remaining-size report. Earlier sandbox inspection could not read the full process table; the cleanup runner completed its own process and path checks before removal. All `build/audit-project-tools_r1_dev_*` citations elsewhere in this hand-off are historical references: their report files were removed during task 6.3 cleanup, and the decision-relevant summaries and source inventories are preserved here. No R6/history exception is introduced; any inactive objects within an assigned run root are disposable under the approved cleanup policy.

#### Cleanup receipt

Cleanup status: **complete** (`exit 0`, `pending 0`). All 37 dev roots were removed. Logical regular-file bytes counted immediately before removal total 848,558,602 bytes. The table records every removed root; the final 13 entries completed the earlier partial receipt.

| Removed dev root | Logical bytes |
|---|---:|
| `build/audit-project-tools_r1_dev_try-10_integration` | 48,317,050 |
| `build/audit-project-tools_r1_dev_try-11_isolated-workspace` | 45,174,886 |
| `build/audit-project-tools_r1_dev_try-12_source-refresh` | 58,265,976 |
| `build/audit-project-tools_r1_dev_try-13_development-readiness` | 55,112,597 |
| `build/audit-project-tools_r1_dev_try-14_matrix-controlled` | 8,597 |
| `build/audit-project-tools_r1_dev_try-15_matrix-check` | 4,294 |
| `build/audit-project-tools_r1_dev_try-16_package-fresh` | 140,482,669 |
| `build/audit-project-tools_r1_dev_try-17_cleanup-scope` | 2,738 |
| `build/audit-project-tools_r1_dev_try-18_cleanup-targets` | 31,038 |
| `build/audit-project-tools_r1_dev_try-19_cleanup-targets` | 87,736 |
| `build/audit-project-tools_r1_dev_try-1_baseline` | 69 |
| `build/audit-project-tools_r1_dev_try-1_environment` | 33,437 |
| `build/audit-project-tools_r1_dev_try-1_integration` | 51,043,139 |
| `build/audit-project-tools_r1_dev_try-20_cleanup-minimal-path` | 85,700 |
| `build/audit-project-tools_r1_dev_try-21_cleanup-safety` | 6,584 |
| `build/audit-project-tools_r1_dev_try-22_restoration` | 109,697,346 |
| `build/audit-project-tools_r1_dev_try-23_tool-audit` | 8,468,604 |
| `build/audit-project-tools_r1_dev_try-24_docs-ci-alignment` | 26,327 |
| `build/audit-project-tools_r1_dev_try-25_package-ci-venv` | 33,219 |
| `build/audit-project-tools_r1_dev_try-26_freeze-preparation` | 61,839 |
| `build/audit-project-tools_r1_dev_try-27_clean-package` | 106,531,087 |
| `build/audit-project-tools_r1_dev_try-28_review-retry-identity` | 65,496 |
| `build/audit-project-tools_r1_dev_try-2_baseline` | 0 |
| `build/audit-project-tools_r1_dev_try-2_environment` | 6,792,330 |
| `build/audit-project-tools_r1_dev_try-3_baseline` | 0 |
| `build/audit-project-tools_r1_dev_try-3_environment` | 33,437 |
| `build/audit-project-tools_r1_dev_try-4_baseline` | 0 |
| `build/audit-project-tools_r1_dev_try-4_environment` | 42,266,801 |
| `build/audit-project-tools_r1_dev_try-5_baseline` | 1,043 |
| `build/audit-project-tools_r1_dev_try-5_cleanup-tests` | 5,236 |
| `build/audit-project-tools_r1_dev_try-5_environment` | 6,792,330 |
| `build/audit-project-tools_r1_dev_try-6_recovery` | 68,968,725 |
| `build/audit-project-tools_r1_dev_try-7_baseline` | 571,659 |
| `build/audit-project-tools_r1_dev_try-7_environment` | 48,911,316 |
| `build/audit-project-tools_r1_dev_try-8_baseline` | 813,482 |
| `build/audit-project-tools_r1_dev_try-8_environment` | 49,638,022 |
| `build/audit-project-tools_r1_dev_try-9_command-check` | 223,793 |

| Initial dev-root size snapshot before cleanup | KiB |
|---|---:|
| `build/audit-project-tools_r1_dev_try-10_integration` | 52,216 |
| `build/audit-project-tools_r1_dev_try-11_isolated-workspace` | 48,644 |
| `build/audit-project-tools_r1_dev_try-12_source-refresh` | 62,980 |
| `build/audit-project-tools_r1_dev_try-13_development-readiness` | 59,728 |
| `build/audit-project-tools_r1_dev_try-14_matrix-controlled` | 20 |
| `build/audit-project-tools_r1_dev_try-15_matrix-check` | 8 |
| `build/audit-project-tools_r1_dev_try-16_package-fresh` | 150,176 |
| `build/audit-project-tools_r1_dev_try-17_cleanup-scope` | 8 |
| `build/audit-project-tools_r1_dev_try-18_cleanup-targets` | 64 |
| `build/audit-project-tools_r1_dev_try-19_cleanup-targets` | 176 |
| `build/audit-project-tools_r1_dev_try-1_baseline` | 4 |
| `build/audit-project-tools_r1_dev_try-1_environment` | 84 |
| `build/audit-project-tools_r1_dev_try-1_integration` | 55,276 |
| `build/audit-project-tools_r1_dev_try-20_cleanup-minimal-path` | 172 |
| `build/audit-project-tools_r1_dev_try-21_cleanup-safety` | 12 |
| `build/audit-project-tools_r1_dev_try-22_restoration` | 117,672 |
| `build/audit-project-tools_r1_dev_try-23_tool-audit` | 12,456 |
| `build/audit-project-tools_r1_dev_try-24_docs-ci-alignment` | 32 |
| `build/audit-project-tools_r1_dev_try-25_package-ci-venv` | 80 |
| `build/audit-project-tools_r1_dev_try-26_freeze-preparation` | 64 |
| `build/audit-project-tools_r1_dev_try-27_clean-package` | 113,680 |
| `build/audit-project-tools_r1_dev_try-28_review-retry-identity` | 72 |
| `build/audit-project-tools_r1_dev_try-2_baseline` | 0 |
| `build/audit-project-tools_r1_dev_try-2_environment` | 8,132 |
| `build/audit-project-tools_r1_dev_try-3_baseline` | 0 |
| `build/audit-project-tools_r1_dev_try-3_environment` | 84 |
| `build/audit-project-tools_r1_dev_try-4_baseline` | 0 |
| `build/audit-project-tools_r1_dev_try-4_environment` | 45,272 |
| `build/audit-project-tools_r1_dev_try-5_baseline` | 4 |
| `build/audit-project-tools_r1_dev_try-5_cleanup-tests` | 16 |
| `build/audit-project-tools_r1_dev_try-5_environment` | 8,132 |
| `build/audit-project-tools_r1_dev_try-6_recovery` | 74,164 |
| `build/audit-project-tools_r1_dev_try-7_baseline` | 580 |
| `build/audit-project-tools_r1_dev_try-7_environment` | 52,028 |
| `build/audit-project-tools_r1_dev_try-8_baseline` | 824 |
| `build/audit-project-tools_r1_dev_try-8_environment` | 52,864 |
| `build/audit-project-tools_r1_dev_try-9_command-check` | 276 |

### Preserved source inventories

The following are exact JSON inventories copied from the frozen package run and the amended reviewer-retry identity run. The first records the 328-file package candidate (`37b4e78367affe16a50e7a4b6030ccd02f1b1b0ef1da467e1f8e490929b27e8d`); the second records the 329-file current identity (`ae2cd22825b41fc76ac5f657264631570bd81657033751c21dfeca4c67ddd92b`). The amended scope adds `openspec/changes/audit-project-tools/reviewer-retry-permissions.patch` and changes `.codex/agents/reviewer.toml`; the 116-file runtime closure remains identical (`f0822906c66fa10677683ac603b1e233875d5d7cb57afd3aff78c416c9812794`). These JSON bodies retain included/excluded scope, per-file paths, byte lengths and SHA-256 values for independent reproduction.

<details>
<summary>Frozen 328-file source inventory (before package build)</summary>

```json
{
  "status": "source-copy identity before make package",
  "included_scope": "Regular non-symlink source/configuration files including tools, CI, docs, .codex, library source, tests, schemas, canonical data and OpenSpec artifacts.",
  "excluded": [
    ".git/**",
    "build/**",
    ".venv/**",
    "**/venv/**",
    "**/__pycache__/**",
    "**/node_modules/**",
    "**/.pytest_cache/**",
    "**/hand-off.md",
    "**/tasks.md",
    "**/review.md",
    "mutable task-/audit-report/review-report markdown files"
  ],
  "files": [
    {
      "path": ".DS_Store",
      "sha256": "c8aade81421352f28d9f0597dbbec6e494aa23a51b8a80a60f892e823333f8b6",
      "size_bytes": 8196
    },
    {
      "path": ".agents/skills/.openspec-target",
      "sha256": "243b0dc9b847e66c440dca985e10fe0ce9e29c379b018ddd5747ba8948f84cc8",
      "size_bytes": 6
    },
    {
      "path": ".agents/skills/openspec-apply-change/SKILL.md",
      "sha256": "03e9c7f88580bc0fe0015f40cbdb1834bf1d56597bdf0b593e98e7a0857fbb4b",
      "size_bytes": 11384
    },
    {
      "path": ".agents/skills/openspec-archive-change/SKILL.md",
      "sha256": "0b0a3e43dd6d1d3b7c3b23527b8d50976b527ba294eef9649696600f584df032",
      "size_bytes": 16645
    },
    {
      "path": ".agents/skills/openspec-continue-change/SKILL.md",
      "sha256": "232f9092e4dc79d8d23d5674aa930af28ce0e00349177a490c438b4f7252ec39",
      "size_bytes": 9862
    },
    {
      "path": ".agents/skills/openspec-explore/SKILL.md",
      "sha256": "31a4c7543ceb40a2c4b45a184de87f4cb2921a1f98a69688acc51de3ac3e177f",
      "size_bytes": 23134
    },
    {
      "path": ".agents/skills/openspec-ff-change/SKILL.md",
      "sha256": "59f8d7a6a3a8c10bc8ee00ba88f4596edf8039b0aac51bfcfd70f4eb15b3641a",
      "size_bytes": 11247
    },
    {
      "path": ".agents/skills/openspec-new-change/SKILL.md",
      "sha256": "46e2a8bd1d1e17fe55608b91819580bf20810ab23408c5981e23d3cc836fb344",
      "size_bytes": 5894
    },
    {
      "path": ".agents/skills/openspec-propose/SKILL.md",
      "sha256": "bd3d2fef6701ef39e5181e54a258f43a3b58a67369f4dfac8926b9b7e9229a26",
      "size_bytes": 16312
    },
    {
      "path": ".agents/skills/openspec-sync-specs/SKILL.md",
      "sha256": "0631ef731343aaa75d6466fe36ce3f2deecd57cc07e135026159fcdec93f2eb8",
      "size_bytes": 15826
    },
    {
      "path": ".agents/skills/openspec-update-change/SKILL.md",
      "sha256": "2e214729f6e75a07fd753219315447909fa8e4c0837fdbbee62d9b1c4cf46c40",
      "size_bytes": 11524
    },
    {
      "path": ".codex/agents/architect.toml",
      "sha256": "936240dc877abd8822c2d301a5c9b5fe71c361435ea9d9615f08087d02ab286a",
      "size_bytes": 4470
    },
    {
      "path": ".codex/agents/dev.toml",
      "sha256": "e006eca3e3190ea7a85c541c2f3ffeeecd4224a3d467807c3391da3ce8bf92f9",
      "size_bytes": 6030
    },
    {
      "path": ".codex/agents/reviewer.toml",
      "sha256": "442ce58ea2ed9c96578d792f0e5578d56cf66c78ea4bf0e4bc5c530bc89e9b35",
      "size_bytes": 8439
    },
    {
      "path": ".codex/config.toml",
      "sha256": "da7af8ca8c679e3e90c32370b0a0bfa4137b1712f77f4871d8bd59741e7f36e1",
      "size_bytes": 380
    },
    {
      "path": ".codex/rules/default.rules",
      "sha256": "2a4c7c0c70307d2b7481cbd5bb12291cb3429b9e5537f4492cd1321ed01f6416",
      "size_bytes": 270
    },
    {
      "path": ".github/workflows/host-python.yml",
      "sha256": "965687e6268cfbfc755ad565f46e65ecadb670af3d1ce34fa999efb799cd1a51",
      "size_bytes": 5384
    },
    {
      "path": ".github/workflows/package.yml",
      "sha256": "d490a6eda7ce5f8e1d3ff8e63b140181b45c59a2a1043d8302b3aea4b84ca58e",
      "size_bytes": 26241
    },
    {
      "path": ".github/workflows/release.yml",
      "sha256": "1f65cf0c62415ecec09331a3ff9300d8b6846456c9f163e7dc6f19ded985f381",
      "size_bytes": 9312
    },
    {
      "path": ".gitignore",
      "sha256": "6a8d4b2377a13484efecd853ea1ff02f5239ae41512d6dbca3f8a9b5c3ae0ff6",
      "size_bytes": 49
    },
    {
      "path": ".python-version",
      "sha256": "a876e0b10411037a012498b9fe18d9bc1df32ed8b722a13564dc944ddcfd9135",
      "size_bytes": 5
    },
    {
      "path": "AGENTS.md",
      "sha256": "6262f5187fa29172ac381b97c91b5c2ce5ae22ceed86058bb4d5ba758a5bfe81",
      "size_bytes": 22136
    },
    {
      "path": "LICENSE-CODE",
      "sha256": "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
      "size_bytes": 11358
    },
    {
      "path": "LICENSE-DATA",
      "sha256": "6b2a8a413077dd73e8ed564471875c2b9634ca3b76dcbe608b8094090d4392ce",
      "size_bytes": 859
    },
    {
      "path": "MANIFEST.in",
      "sha256": "07856c95409fa1956fdc075e2d2b648afe8ffcec12a48b00bd326274b353c8ff",
      "size_bytes": 322
    },
    {
      "path": "Makefile",
      "sha256": "72ffbda0d4a2e3296a89497e8321d94a7cd12504c2d64ea594c5d25a4fb8cbeb",
      "size_bytes": 3214
    },
    {
      "path": "THIRD-PARTY-NOTICES.md",
      "sha256": "a5facb0a8d7eca51ad5d667d3f4f8469fc6cf157f06f443962571d2dd3cf40a4",
      "size_bytes": 7331
    },
    {
      "path": "characters/README.md",
      "sha256": "dc6f9f0305b8c204a40698f27b5084b51340b7d1c6f6725c417c4d9068decf2f",
      "size_bytes": 1069
    },
    {
      "path": "characters/appearances/female-v1.yaml",
      "sha256": "3c4253cae9d7a08362c64be568c0eb1531bc442ba5952f4d74fe6d11efb1ebe1",
      "size_bytes": 925
    },
    {
      "path": "characters/appearances/male-v1.yaml",
      "sha256": "bfa1aa9bf27a24c4450b04ef81dc3fd8e4225d27ab385bb0f12c9d813f2dc89c",
      "size_bytes": 834
    },
    {
      "path": "characters/definitions/female.yaml",
      "sha256": "21f58bd393e92375d268168aef59bd7b03628ecc1032daae9e0c09b05ebe779b",
      "size_bytes": 667
    },
    {
      "path": "characters/definitions/male.yaml",
      "sha256": "ab58396f7aa7eb7d493126a907b9368efb43f725be512d8cf724bfb29c0eab96",
      "size_bytes": 661
    },
    {
      "path": "characters/definitions/skeleton.yaml",
      "sha256": "787f6a8c3cd43b9d17ec23c03a9d96d6eb966d5d31a9dd4a66034138dec784d7",
      "size_bytes": 813
    },
    {
      "path": "characters/registry.yaml",
      "sha256": "41965c69c390b7e64d5ce269490eed7a5bf8ffb9e7ead77def104eb37aae6fe0",
      "size_bytes": 581
    },
    {
      "path": "characters/templates/exercise-mannequin-v1.yaml",
      "sha256": "2818a3e4d2fd6075b08b42b31a574b5ed7a7f4e4df96e2a34f1589916ec00f57",
      "size_bytes": 9233
    },
    {
      "path": "docs/anatomical-human-skeleton-preflight.md",
      "sha256": "19a0cece534051397f180d2a7df37ccd16550258ab7419694bf546a8b3ffa4c2",
      "size_bytes": 6855
    },
    {
      "path": "docs/anatomical-skeleton-acceptance.md",
      "sha256": "7da928ed2dd8ce6ad0b3a8c330592c17566bac979fea2eb3ed9ef0c63640acb1",
      "size_bytes": 10809
    },
    {
      "path": "docs/backend-crash-triage.md",
      "sha256": "17700d6b2a078ddd5e6d92dab9c71deb47c04690b55a27a98be832449fc4350e",
      "size_bytes": 4825
    },
    {
      "path": "docs/build-matrix.md",
      "sha256": "4009fe64ff81aae06919ef789a550b8534fad0d1103aa4e1821044ae4aa2fbba",
      "size_bytes": 5962
    },
    {
      "path": "docs/character-models.md",
      "sha256": "7848fa384dd799ad0d6a3613f8d292a6d2e8257cc1c95f9971412aa7e522efdb",
      "size_bytes": 9254
    },
    {
      "path": "docs/usage.md",
      "sha256": "ecbc1d5e067ae5425aa341154aaa58c247e9cc01a6bf789f835a911094830b05",
      "size_bytes": 25802
    },
    {
      "path": "docs/used-materials.md",
      "sha256": "fe889173dd82c97772a7fd6e96a2f5e7df6d503fd9c43c557c73661cdd330dec",
      "size_bytes": 35602
    },
    {
      "path": "hml_build_backend.py",
      "sha256": "3883076ad43e21f77f534fd645095eeae4f600353deec27c4b7952a8483e8aeb",
      "size_bytes": 15589
    },
    {
      "path": "openspec/changes/add-shared-body-characters/.openspec.yaml",
      "sha256": "d002983090acfe222597827aa3c481b59d3a566c704a6e91e0d50bb1d209297d",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/add-shared-body-characters/approvals.md",
      "sha256": "144fe7ada5b4c0da42dd4394465f37a930dbee6b5b7106dae78093ea706c8a1f",
      "size_bytes": 8814
    },
    {
      "path": "openspec/changes/add-shared-body-characters/blocker.md",
      "sha256": "d808fd0e5463bfaecc371e02ee53bd5d23c1dc4ec2f3eaefb899ef45fcbd658e",
      "size_bytes": 8251
    },
    {
      "path": "openspec/changes/add-shared-body-characters/cleanup-inventory.md",
      "sha256": "2e2ee16eb70d0a3672a635109c3a80224c488340391aac933098ac96b9e6b8cd",
      "size_bytes": 26542
    },
    {
      "path": "openspec/changes/add-shared-body-characters/design.md",
      "sha256": "578252262ecb3dc6f299b3fe70fee7f363204b371c293c20e216d2d81272adc0",
      "size_bytes": 97703
    },
    {
      "path": "openspec/changes/add-shared-body-characters/developer-handoff.md",
      "sha256": "b367b7f8fdafa9dd25ae27fbcffbe1d11fb770ded5bdc4a567fba2cb785bcc4a",
      "size_bytes": 88042
    },
    {
      "path": "openspec/changes/add-shared-body-characters/documentation-check.md",
      "sha256": "73de5c8f30a48cee102a8ae24aabd19699a2581a8bec8ffe91d6c075b0f2af8f",
      "size_bytes": 2609
    },
    {
      "path": "openspec/changes/add-shared-body-characters/execution-notes.md",
      "sha256": "eedbf794a2077958c782830bda3c369a2c01563ecc73ed1a616f02c3e09f761c",
      "size_bytes": 3036
    },
    {
      "path": "openspec/changes/add-shared-body-characters/historical-baseline-check.md",
      "sha256": "3ddfa3b229c092778f6986b98bcb50d75fe142863d3874e48a6de5df35a1398f",
      "size_bytes": 3700
    },
    {
      "path": "openspec/changes/add-shared-body-characters/installation-check.md",
      "sha256": "c91d00211b6e4d2e43c8caa3b0b3554137fc6e018f3ff7f06affd1615966cf0d",
      "size_bytes": 17465
    },
    {
      "path": "openspec/changes/add-shared-body-characters/midpoint-check.json",
      "sha256": "fdc4d319233a1943f54b565b70635e701777542c094954d90aa938737bb23b36",
      "size_bytes": 1531
    },
    {
      "path": "openspec/changes/add-shared-body-characters/native-checks.md",
      "sha256": "0d7dc5bc03738879fcde7278fb8a39b20d5988d9938ab69291b9aad1053f097b",
      "size_bytes": 7181
    },
    {
      "path": "openspec/changes/add-shared-body-characters/orchestration-status.md",
      "sha256": "874ec6f2652c4a427479445549576f44049dab606556f2c51286fe291806ec85",
      "size_bytes": 11613
    },
    {
      "path": "openspec/changes/add-shared-body-characters/packaging-check.md",
      "sha256": "7db025d78acbe76117d1b96dbf87b64480050bce2aa98264497a54a2b2574e73",
      "size_bytes": 14032
    },
    {
      "path": "openspec/changes/add-shared-body-characters/proposal.md",
      "sha256": "2ae592d4b251a13a73a17a86a5c43e15b7c3523869806825eb01321603acc7a0",
      "size_bytes": 4205
    },
    {
      "path": "openspec/changes/add-shared-body-characters/specs/character-models/spec.md",
      "sha256": "7dda6afd124b784065adab08fd8ae9f72e17d8e957d7f88333c1cc39c043715c",
      "size_bytes": 19715
    },
    {
      "path": "openspec/changes/add-shared-body-characters/specs/public-generation-api/spec.md",
      "sha256": "fdcff17180050efd524f658f4d6cd646526984c267d35c9039af18a89ef077ce",
      "size_bytes": 15880
    },
    {
      "path": "openspec/changes/add-shared-body-characters/specs/python-distribution/spec.md",
      "sha256": "503623434e212afa29f2a5f4d0d97bd913a22061b9495ff2b3eef2237fb7756d",
      "size_bytes": 4668
    },
    {
      "path": "openspec/changes/archive/.gitkeep",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "size_bytes": 0
    },
    {
      "path": "openspec/changes/archive/2026-10-22-anatomical-human-skeleton/.openspec.yaml",
      "sha256": "ff4326f8b42dcf8851877f4f3989c7fecb8f97d8154686d7d74b7281b70e6b9b",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-22-anatomical-human-skeleton/design.md",
      "sha256": "622709e838b9c126c3da7256fa403e6d56feb6af362faaf29faafe8be33a900a",
      "size_bytes": 83161
    },
    {
      "path": "openspec/changes/archive/2026-10-22-anatomical-human-skeleton/proposal.md",
      "sha256": "cccd77099825e64a6b9790413a8656d48fe92d3f7041c24db2ec0c4f99d2d8fb",
      "size_bytes": 9769
    },
    {
      "path": "openspec/changes/archive/2026-10-22-anatomical-human-skeleton/specs/anatomical-skeleton/spec.md",
      "sha256": "7d5b282a2998ddbb727a8ce4b40c27e7450d786fc3f230a2d91884d9e65e211d",
      "size_bytes": 18861
    },
    {
      "path": "openspec/changes/archive/2026-10-22-anatomical-human-skeleton/specs/joint-mobility/spec.md",
      "sha256": "ce25e4f91df7de2c1b8a3d9e3148c9eebe84ebbb63195aeb887a1dd0841a46e9",
      "size_bytes": 24712
    },
    {
      "path": "openspec/changes/archive/2026-10-22-flat-build-workflow/.openspec.yaml",
      "sha256": "0ad492a63d87e00a8bc135b0a1a2b19270dbb9ffd997a69b89fd4ab72015a944",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-22-flat-build-workflow/design.md",
      "sha256": "16e810f386c812ea47e7b2fca3e36ea01001b1151999962b676889f771ca1955",
      "size_bytes": 9962
    },
    {
      "path": "openspec/changes/archive/2026-10-22-flat-build-workflow/proposal.md",
      "sha256": "72aa47f81217beb0ce28e6745f22c9d8d698888749f494d2f8ee37bdd71eaf87",
      "size_bytes": 2359
    },
    {
      "path": "openspec/changes/archive/2026-10-22-flat-build-workflow/specs/anatomical-skeleton/spec.md",
      "sha256": "91204147c32167084ae0e9c3f4dbe718c8427c2642366881fed64e17bb2385fe",
      "size_bytes": 2435
    },
    {
      "path": "openspec/changes/archive/2026-10-22-flat-build-workflow/specs/build-artifact-lifecycle/spec.md",
      "sha256": "557097f5d24edec8c8c19622e14c0f21037bca165924eb5f5380c9f16c9d0011",
      "size_bytes": 6331
    },
    {
      "path": "openspec/changes/archive/2026-10-22-flat-build-workflow/specs/joint-mobility/spec.md",
      "sha256": "7c7e0d80fd288fb4e1db7f46b11986e583030fab819afbccde090200095aa5f9",
      "size_bytes": 2441
    },
    {
      "path": "openspec/changes/archive/2026-10-22-harden-backend-process-execution/.openspec.yaml",
      "sha256": "0ad492a63d87e00a8bc135b0a1a2b19270dbb9ffd997a69b89fd4ab72015a944",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-22-harden-backend-process-execution/design.md",
      "sha256": "5428bd128c0184f11c4c0c63b617869bb7311b03367385e5e3e9890e8c1e791c",
      "size_bytes": 22303
    },
    {
      "path": "openspec/changes/archive/2026-10-22-harden-backend-process-execution/dev-handoff.md",
      "sha256": "df27fa1d624d376fc482b9412262dea878ec9626829e5bfed871434ac6705b64",
      "size_bytes": 17051
    },
    {
      "path": "openspec/changes/archive/2026-10-22-harden-backend-process-execution/operator-decisions.md",
      "sha256": "d569ac616c3d1766d507b9f5809b3345613112d0d73f03fe06da95ad15d4e5b4",
      "size_bytes": 10298
    },
    {
      "path": "openspec/changes/archive/2026-10-22-harden-backend-process-execution/proposal.md",
      "sha256": "cc0ae953e1d1fde1da126003aa8405a6e2e4ae0fc5d71ffc67807ace30241ff2",
      "size_bytes": 2949
    },
    {
      "path": "openspec/changes/archive/2026-10-22-harden-backend-process-execution/runner-tests-handoff.md",
      "sha256": "f3049aab4eef9543e5040e3649fb4dc37b3901df695bdfa3e80ed87027ef9933",
      "size_bytes": 1672
    },
    {
      "path": "openspec/changes/archive/2026-10-22-harden-backend-process-execution/specs/backend-execution/spec.md",
      "sha256": "0b803fd1ac482cb695cf7605050cc81a99ea56f14d989d45f6609af8e14bc369",
      "size_bytes": 10423
    },
    {
      "path": "openspec/changes/archive/2026-10-22-project-instructions-alignment/design.md",
      "sha256": "aaedddb000b5c4bae92702ad16e01c94e243f2650e459229fad8d8fb77202c6f",
      "size_bytes": 5609
    },
    {
      "path": "openspec/changes/archive/2026-10-22-project-instructions-alignment/proposal.md",
      "sha256": "6d9692baab8e4c0ad0bba6a9ee248970cb2ce4a45e62a2e0603010c2a8dc4db8",
      "size_bytes": 2497
    },
    {
      "path": "openspec/changes/archive/2026-10-22-project-instructions-alignment/specs/project-governance/spec.md",
      "sha256": "06558fae04f773e11c9b2dff8ba6d63ae1a4ff0a6bfc70f68bfd84a05f206065",
      "size_bytes": 7570
    },
    {
      "path": "openspec/changes/archive/2026-10-23-upgrade-host-python-314/.openspec.yaml",
      "sha256": "54c2a6955b514abf783374521da3b6364c1d6b221970ad9faa7124a7e1124528",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-23-upgrade-host-python-314/ci-handoff.md",
      "sha256": "7e2108b02b06024d4ef6ccc186d319dd4f9f657542e584de081626c02038e531",
      "size_bytes": 6212
    },
    {
      "path": "openspec/changes/archive/2026-10-23-upgrade-host-python-314/design.md",
      "sha256": "694aa08afbb4e5adf411f5ebe6639d7fe3c62f12d994bbf9b5a9338af995a1bc",
      "size_bytes": 18700
    },
    {
      "path": "openspec/changes/archive/2026-10-23-upgrade-host-python-314/developer-handoff.md",
      "sha256": "23e2b18f6c363cbd9b4ceac26ea1408eeda1fd7b7f1cde7354dc233acad88a0d",
      "size_bytes": 8833
    },
    {
      "path": "openspec/changes/archive/2026-10-23-upgrade-host-python-314/proposal.md",
      "sha256": "3418c77d1829d8666f6acf43502c7e57411bddc0dc855af98bd1b025a7146b2a",
      "size_bytes": 2551
    },
    {
      "path": "openspec/changes/archive/2026-10-23-upgrade-host-python-314/specs/host-python-runtime/spec.md",
      "sha256": "672690cc94bb2f1338409a6e4faafc6389eeebc833cca5547e017d19502ca4b9",
      "size_bytes": 6955
    },
    {
      "path": "openspec/changes/archive/2026-10-24-package-humanmotionlib/.openspec.yaml",
      "sha256": "54c2a6955b514abf783374521da3b6364c1d6b221970ad9faa7124a7e1124528",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-24-package-humanmotionlib/design.md",
      "sha256": "a501c3f9882c49cdd20d0688d973759bb25fc3d7fb44b1a2856aa49498f3518d",
      "size_bytes": 23367
    },
    {
      "path": "openspec/changes/archive/2026-10-24-package-humanmotionlib/developer-handoff.md",
      "sha256": "5f9bd6a2f7669faf7c5a3038e7416012a77cd9fdad12055d5e481c1cfef3acdf",
      "size_bytes": 11830
    },
    {
      "path": "openspec/changes/archive/2026-10-24-package-humanmotionlib/proposal.md",
      "sha256": "57823a1352f303d0fc2666f96d8baa85585028dae6e4d440202a4407fcf74d3d",
      "size_bytes": 3038
    },
    {
      "path": "openspec/changes/archive/2026-10-24-package-humanmotionlib/specs/backend-execution/spec.md",
      "sha256": "f8485e7028f83ccbf79264d84c5144035efd92edeb486f9a222c8d97e168e0b0",
      "size_bytes": 6979
    },
    {
      "path": "openspec/changes/archive/2026-10-24-package-humanmotionlib/specs/build-artifact-lifecycle/spec.md",
      "sha256": "64220a5ccafb27669c144c3fa9b87add71e007878c12669fb7562878f74adfd6",
      "size_bytes": 2372
    },
    {
      "path": "openspec/changes/archive/2026-10-24-package-humanmotionlib/specs/host-python-runtime/spec.md",
      "sha256": "2ca175f69796c83ccb7e9e6eff905a981403d92994ccd397621a8f492c78c233",
      "size_bytes": 2071
    },
    {
      "path": "openspec/changes/archive/2026-10-24-package-humanmotionlib/specs/python-distribution/spec.md",
      "sha256": "bc9ecc1dd1e1fe562c59cdaa319d05113ff257e4d71f820d72aabd79ddc05ee5",
      "size_bytes": 11311
    },
    {
      "path": "openspec/changes/archive/2026-10-24-portable-installed-runtime/.openspec.yaml",
      "sha256": "e2ebaebee255ccc1e09b64ba38d9b09c360a7392fc110a48ca2525e1ea49fa46",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-24-portable-installed-runtime/design.md",
      "sha256": "76806f19f7c852890aa9346fb08b0467b38acc4387be15f9cfa719d82d8abb18",
      "size_bytes": 25150
    },
    {
      "path": "openspec/changes/archive/2026-10-24-portable-installed-runtime/implementation.md",
      "sha256": "9371d9f6667cf117c67c9375d5386dd6f0a36fa274e28d96d823fb7546302ae5",
      "size_bytes": 17120
    },
    {
      "path": "openspec/changes/archive/2026-10-24-portable-installed-runtime/proposal.md",
      "sha256": "7078d7258b630f8cac90aaf2967d5e4028aec563515ed6f2d4844c0acab571c4",
      "size_bytes": 2634
    },
    {
      "path": "openspec/changes/archive/2026-10-24-portable-installed-runtime/specs/backend-execution/spec.md",
      "sha256": "eae2f4e5bf8e07ca74cdcbc71d5a2c7da92c8d55389de12a56fa38214ab6d89a",
      "size_bytes": 9158
    },
    {
      "path": "openspec/changes/archive/2026-10-24-portable-installed-runtime/specs/build-artifact-lifecycle/spec.md",
      "sha256": "c21b27f9049482c94efa87e6bc79514ccf26721070facced5ee4334ff626532f",
      "size_bytes": 3995
    },
    {
      "path": "openspec/changes/archive/2026-10-24-portable-installed-runtime/specs/python-distribution/spec.md",
      "sha256": "9269372b37a7b17e82cfb3f2c41750d3eb742f7671e0ca2c139a0e3526c4a702",
      "size_bytes": 9431
    },
    {
      "path": "openspec/changes/archive/2026-10-24-public-python-generation-api/.openspec.yaml",
      "sha256": "e2ebaebee255ccc1e09b64ba38d9b09c360a7392fc110a48ca2525e1ea49fa46",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-24-public-python-generation-api/design.md",
      "sha256": "7fd2c61a11abe1f75af9913d14c38739d5a9926fce81d8edd058a1d5f5390232",
      "size_bytes": 18955
    },
    {
      "path": "openspec/changes/archive/2026-10-24-public-python-generation-api/developer-handoff.md",
      "sha256": "2f89c5bb207391f1cd246c80940ac50d16f08da7dfc6350b4b41af635d3d870d",
      "size_bytes": 8298
    },
    {
      "path": "openspec/changes/archive/2026-10-24-public-python-generation-api/proposal.md",
      "sha256": "ecd271cd5b230b55d8e7708fac70614ce48fafced1f00826b030b51ff313e9a5",
      "size_bytes": 2373
    },
    {
      "path": "openspec/changes/archive/2026-10-24-public-python-generation-api/specs/public-generation-api/spec.md",
      "sha256": "f5e6c22200b4f68d7c50791e3106797dec768a7429fd70613b2856fd6e3d4476",
      "size_bytes": 14631
    },
    {
      "path": "openspec/changes/archive/2026-10-25-support-consumer-authored-motions/.openspec.yaml",
      "sha256": "d002983090acfe222597827aa3c481b59d3a566c704a6e91e0d50bb1d209297d",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-25-support-consumer-authored-motions/design.md",
      "sha256": "449f5789ad33537c37b9855215f77a6ea3e2a3fe035aedb152cb11d67646f44d",
      "size_bytes": 31935
    },
    {
      "path": "openspec/changes/archive/2026-10-25-support-consumer-authored-motions/developer-handoff.md",
      "sha256": "dbd03e26fb428020b339e86ed94332b0ad5a20b07d319bba82c3a16ce6ca000f",
      "size_bytes": 18181
    },
    {
      "path": "openspec/changes/archive/2026-10-25-support-consumer-authored-motions/proposal.md",
      "sha256": "a2ee60bcc4eb3ac6beff384be44d4bba5f4eb0ef3c0d51067c63f305459d3ba0",
      "size_bytes": 2847
    },
    {
      "path": "openspec/changes/archive/2026-10-25-support-consumer-authored-motions/specs/consumer-motion-sources/spec.md",
      "sha256": "308013bcd03c98000869d6ddcd7f6a9b55d2ed5d8c27da1f6150b42b8dd036af",
      "size_bytes": 13222
    },
    {
      "path": "openspec/changes/archive/2026-10-25-support-consumer-authored-motions/specs/public-generation-api/spec.md",
      "sha256": "4d0a80d7b75e3d2ea4863d61df147371cc3703ea659ea7eca88adf18a9fdc2a5",
      "size_bytes": 8351
    },
    {
      "path": "openspec/changes/archive/2026-10-25-versioned-releases/.openspec.yaml",
      "sha256": "e2ebaebee255ccc1e09b64ba38d9b09c360a7392fc110a48ca2525e1ea49fa46",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-25-versioned-releases/design.md",
      "sha256": "ac444427fa114135724ab362ca95713f03b7c3d500deece5409ab2d9b51ece65",
      "size_bytes": 7311
    },
    {
      "path": "openspec/changes/archive/2026-10-25-versioned-releases/developer-handoff.md",
      "sha256": "8d15ad35e66f39b4878fddca10f4c2edc8646d3d634bacdc9fa63241d97c17e2",
      "size_bytes": 8489
    },
    {
      "path": "openspec/changes/archive/2026-10-25-versioned-releases/proposal.md",
      "sha256": "3e187c6fb5152f375d6a556c2541ef0e9d8f43d8b2f8e65b75c932edc55b7576",
      "size_bytes": 2469
    },
    {
      "path": "openspec/changes/archive/2026-10-25-versioned-releases/specs/python-distribution/spec.md",
      "sha256": "66fbd3f671d850b506758d00886e68db20af51cf31e647a0ed5e1d7f7be82979",
      "size_bytes": 1923
    },
    {
      "path": "openspec/changes/archive/2026-10-25-versioned-releases/specs/release-publication/spec.md",
      "sha256": "40865e1690f96f86a7cc67c675c7ed8258127a11bb2d7abd38abe4cea1593c83",
      "size_bytes": 9325
    },
    {
      "path": "openspec/changes/archive/2026-10-28-add-early-visual-gate/.openspec.yaml",
      "sha256": "9e0a467e3934b14a2d9c9175305310e9359d34e2484a458af3d182c2956b9e2d",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-28-add-early-visual-gate/approvals.md",
      "sha256": "a83ac37bb7c7673784a961fff25dd002b777924e6fcb38670c6a62997f221d4b",
      "size_bytes": 388
    },
    {
      "path": "openspec/changes/archive/2026-10-28-add-early-visual-gate/design.md",
      "sha256": "572950efff37e915861b7cc29e20bf85ecd7108e2b15e65cf0cbd142a835a3c0",
      "size_bytes": 10627
    },
    {
      "path": "openspec/changes/archive/2026-10-28-add-early-visual-gate/developer-handoff.md",
      "sha256": "b868772149c2463ae114c3d84d580fbe9182effbde56557f1b5cd6a03cd30506",
      "size_bytes": 5959
    },
    {
      "path": "openspec/changes/archive/2026-10-28-add-early-visual-gate/proposal.md",
      "sha256": "bcd91ba3c2bc2f9eb6fad5fe3ef94d62e22a389564570a2134194ed8aaa5e5a3",
      "size_bytes": 1788
    },
    {
      "path": "openspec/changes/archive/2026-10-28-add-early-visual-gate/specs/project-governance/spec.md",
      "sha256": "eb80166d9e8fd78bd3dd4575e9bf99d79dd85c0ebd03086bee9146215b930acd",
      "size_bytes": 6999
    },
    {
      "path": "openspec/changes/archive/2026-10-31-automate-build-and-verification-matrix/.openspec.yaml",
      "sha256": "9e0a467e3934b14a2d9c9175305310e9359d34e2484a458af3d182c2956b9e2d",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-31-automate-build-and-verification-matrix/design.md",
      "sha256": "c73697ee18bf728371c2cde1c8b7ed3c14783c2d34656377096963415f384074",
      "size_bytes": 9599
    },
    {
      "path": "openspec/changes/archive/2026-10-31-automate-build-and-verification-matrix/proposal.md",
      "sha256": "d62690e2db9904870dae51796f48c71a911684a091f319accd666386fa648555",
      "size_bytes": 3293
    },
    {
      "path": "openspec/changes/archive/2026-10-31-automate-build-and-verification-matrix/reviewer-authority-proposal.md",
      "sha256": "ff275208ac8f92c92232f86f33971deb57443f21f13f6e0f389513b9ce55094f",
      "size_bytes": 8993
    },
    {
      "path": "openspec/changes/archive/2026-10-31-automate-build-and-verification-matrix/reviewer-inventory.md",
      "sha256": "cc4a0676fb3c607059f87d46962f444811abe751fca09214d3396a6f03f6534a",
      "size_bytes": 7517
    },
    {
      "path": "openspec/changes/archive/2026-10-31-automate-build-and-verification-matrix/specs/build-artifact-lifecycle/spec.md",
      "sha256": "d3f7b61f781951b7d6e3879ce1a71b5de08569cb4229e090af49650f88b371e3",
      "size_bytes": 10612
    },
    {
      "path": "openspec/changes/archive/2026-10-31-automate-build-and-verification-matrix/specs/build-verification-matrix/spec.md",
      "sha256": "dade61e054f286d2c29238e97b133b42da9c2e34c76d2a3ce3c5fbed03d2563a",
      "size_bytes": 8044
    },
    {
      "path": "openspec/changes/archive/2026-10-31-automate-build-and-verification-matrix/specs/public-generation-api/spec.md",
      "sha256": "564778d9d3ed6e79314a0e19cd4060a24c1a18238d167ef9f6b5bb31f2398774",
      "size_bytes": 2386
    },
    {
      "path": "openspec/changes/audit-project-tools/.openspec.yaml",
      "sha256": "c6ab3a95d8d0fd469ca8750ef79234025bf4a8356d5d57856e97d7e47fc8b6c2",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/audit-project-tools/design.md",
      "sha256": "778d06518942201b509fd715c7f4777c54ea6154941212288db47c7a6a92fc02",
      "size_bytes": 23353
    },
    {
      "path": "openspec/changes/audit-project-tools/proposal.md",
      "sha256": "a65f725c748d26c2619a8a352d2e4f604dc678ae4c05c57e071586c6f186f71a",
      "size_bytes": 3952
    },
    {
      "path": "openspec/changes/audit-project-tools/reviewer-workspace-permissions.patch",
      "sha256": "9a7ad332d7c649953abd990fe60e80d4b68eabdded471263df4e949db6e81cf5",
      "size_bytes": 2160
    },
    {
      "path": "openspec/changes/audit-project-tools/specs/build-artifact-lifecycle/spec.md",
      "sha256": "475a71c5766cb84f6f36a175446843e6f4a1609bf0c9858ed3a0595af7bbf80b",
      "size_bytes": 17986
    },
    {
      "path": "openspec/changes/audit-project-tools/specs/build-verification-matrix/spec.md",
      "sha256": "5ce19407238eb4577f681eb3c4a4fad1431a1d23338f870e7f82026fac3ee2a0",
      "size_bytes": 11908
    },
    {
      "path": "openspec/changes/audit-project-tools/specs/host-python-runtime/spec.md",
      "sha256": "55600642554823b22ab77e457460a787433de9cf77310c407870bb83d7cd8e7f",
      "size_bytes": 5409
    },
    {
      "path": "openspec/changes/audit-project-tools/specs/project-governance/spec.md",
      "sha256": "2251ec226de45366915e2829e3da6dd977ff5fcfb4454c2f9beaadf214c20aae",
      "size_bytes": 7074
    },
    {
      "path": "openspec/changes/audit-project-tools/specs/python-distribution/spec.md",
      "sha256": "e98234d04bbfc1064a36b08e7f5a4d2a7a29057440c887d951ea04a757274bf5",
      "size_bytes": 3442
    },
    {
      "path": "openspec/changes/audit-project-tools/tooling-audit.md",
      "sha256": "9338bf5afc32e9f011694a5933e3cb84e00ac7ef5cc6aefd46aa04f49c85730e",
      "size_bytes": 8289
    },
    {
      "path": "openspec/config.yaml",
      "sha256": "f0082e9c22e8ce1d611c0f3b4d4915ce445e7ff2553cda6b713b6c25f390984c",
      "size_bytes": 998
    },
    {
      "path": "openspec/specs/.gitkeep",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "size_bytes": 0
    },
    {
      "path": "openspec/specs/anatomical-skeleton/spec.md",
      "sha256": "1d7b6d685cf033540d79c6f695671ad7714ab68a012279cf0fcdab5ec523cbe2",
      "size_bytes": 19522
    },
    {
      "path": "openspec/specs/backend-execution/spec.md",
      "sha256": "289dd12463f4940afeedcf95271b6e7a9688d2d8499282d5a55ff1dc05b34449",
      "size_bytes": 14965
    },
    {
      "path": "openspec/specs/build-artifact-lifecycle/spec.md",
      "sha256": "9a5678145daf9bfcc8cb04ceb2037efabff4f8150f74c2df4332af9bede71bfa",
      "size_bytes": 10786
    },
    {
      "path": "openspec/specs/build-verification-matrix/spec.md",
      "sha256": "34f4d2b6090d47fe1f632d879c5942c509183d7e3647559bb439c1fca7e43434",
      "size_bytes": 8062
    },
    {
      "path": "openspec/specs/consumer-motion-sources/spec.md",
      "sha256": "fec5bd1d92de1dc601c6d38294a17d60019fa1ae4dc77669ab44499854fe483b",
      "size_bytes": 13243
    },
    {
      "path": "openspec/specs/host-python-runtime/spec.md",
      "sha256": "11c6bb95f215348b4e542d59a0480d40835b4720a8f72cfb95ca67d347ea3cc0",
      "size_bytes": 7917
    },
    {
      "path": "openspec/specs/joint-mobility/spec.md",
      "sha256": "c5f2c1f3c95dcfe6eba7117a59022ddc853d68e84b764a8c7ffa608613115c6e",
      "size_bytes": 25225
    },
    {
      "path": "openspec/specs/project-governance/spec.md",
      "sha256": "95dd60c14deedd85c77941a4faad37d4742e8065932d96bfd8bb631e78d0a2d7",
      "size_bytes": 13345
    },
    {
      "path": "openspec/specs/public-generation-api/spec.md",
      "sha256": "4e560cf53205cec31e55a649ee3e7688436e34e1ac274f258f9010ba0c291b78",
      "size_bytes": 18031
    },
    {
      "path": "openspec/specs/python-distribution/spec.md",
      "sha256": "11717d79c5616ac95ab4d58593dec05e941e8c45b33cdc8f867aad8582ee1e1d",
      "size_bytes": 15769
    },
    {
      "path": "openspec/specs/release-publication/spec.md",
      "sha256": "05effb983aab2f84fbb119f094a640ce8615e026eebca53b8d7d2c8402403d5b",
      "size_bytes": 9342
    },
    {
      "path": "pyproject.toml",
      "sha256": "0795170881715598b9fd59e7a89be7f884f43de7599e37cf58823a8456069800",
      "size_bytes": 1055
    },
    {
      "path": "rig/README.md",
      "sha256": "6b286cc7c7f75ee2f507fcacb0bc71c3b407f6631713b9aa70a3a049224f36f6",
      "size_bytes": 5120
    },
    {
      "path": "rig/body-groups.yaml",
      "sha256": "9bf0c47fcf8064d3e36b7d826bb5cb514b1570952d7990f51ae6179b2a945056",
      "size_bytes": 7711
    },
    {
      "path": "rig/diagnostics/arm-raise.yaml",
      "sha256": "960ffd672d1de4ee238cb47b38d007ddb0c0f4fc0a7d61c1859e1c750b8f68d9",
      "size_bytes": 1921
    },
    {
      "path": "rig/diagnostics/forefoot-rocker.yaml",
      "sha256": "7143a4ad7b9a0c88e0e116753b59ca2ef6a32409211fbd59d4e52a16bc2fed71",
      "size_bytes": 2128
    },
    {
      "path": "rig/diagnostics/neutral.yaml",
      "sha256": "a074d838828b89725d59d16162034806a19bcfae7eed453d105a056200e5d3df",
      "size_bytes": 1554
    },
    {
      "path": "rig/diagnostics/rest.yaml",
      "sha256": "ee4896046c49d8034b78377bdda2ef84ebd135f34b9184a81140b1fe219eb9d4",
      "size_bytes": 1532
    },
    {
      "path": "rig/diagnostics/squat.yaml",
      "sha256": "7e736f1011ea74e6516b1354681053fab31f1cd2b5877878ea03fb01dcd8784e",
      "size_bytes": 3496
    },
    {
      "path": "rig/diagnostics/sweep-ankle-bilateral-dorsiflexion.yaml",
      "sha256": "2bd0b7c6c016e26223d30cfd02ca676487010f7306746f4a583b4684ed7127a8",
      "size_bytes": 1433
    },
    {
      "path": "rig/diagnostics/sweep-cervical-flexion.yaml",
      "sha256": "517446ca8c4e76cd7449ffdb84691f5183e8ace01e28c0ac2603813f15220cbb",
      "size_bytes": 1236
    },
    {
      "path": "rig/diagnostics/sweep-cervical-lateral_flexion.yaml",
      "sha256": "e55c9dd82a9b3591c24e151b701a21a5c57344aeaccdc73ed676036b4444ac7a",
      "size_bytes": 1260
    },
    {
      "path": "rig/diagnostics/sweep-cervical-rotation.yaml",
      "sha256": "6fef0dd66a705d8d463d5b8864c3de6f4ee590f83b321c9defe653c5ebda0649",
      "size_bytes": 1239
    },
    {
      "path": "rig/diagnostics/sweep-elbow-bilateral-flexion.yaml",
      "sha256": "1ae1b7e75332fb3b852c3bd72175853069d42be9a8932cd627e8f7dfe7be19ed",
      "size_bytes": 1411
    },
    {
      "path": "rig/diagnostics/sweep-forearm-bilateral-pronation.yaml",
      "sha256": "734947613b3293d37aa07264a8885a626dc974d16d7108577a28603b04bddced",
      "size_bytes": 1437
    },
    {
      "path": "rig/diagnostics/sweep-hindfoot-bilateral-inversion.yaml",
      "sha256": "c7e929604d452452af3af1122ced2d5bb6650ff9117580e03e67edc4ef20af2a",
      "size_bytes": 1433
    },
    {
      "path": "rig/diagnostics/sweep-hip-bilateral-adduction.yaml",
      "sha256": "41b5c361a1b2687f124e038a35230fe34606c36f44442310de8ab32881d41a2a",
      "size_bytes": 1413
    },
    {
      "path": "rig/diagnostics/sweep-hip-bilateral-external_rotation.yaml",
      "sha256": "9352fa9e58891fee3e0058dce088b37557b14b7fe93353e9a6e3065ff4c252cb",
      "size_bytes": 1445
    },
    {
      "path": "rig/diagnostics/sweep-hip-bilateral-flexion.yaml",
      "sha256": "7ba3fcc71072a3a7052d5e51b378f49ff97d7878024754d2f7c795c48e0f50fe",
      "size_bytes": 1407
    },
    {
      "path": "rig/diagnostics/sweep-knee-bilateral-flexion.yaml",
      "sha256": "7a8823aa482621534e3babd86c9bcd608098c6ef3e903c417389fef659aa4af4",
      "size_bytes": 1407
    },
    {
      "path": "rig/diagnostics/sweep-lumbar-flexion.yaml",
      "sha256": "a8000f18ac5968bd2de4ddfde3c19c83e4615c4b34fad03213f57dd9dce6990b",
      "size_bytes": 1226
    },
    {
      "path": "rig/diagnostics/sweep-lumbar-lateral_flexion.yaml",
      "sha256": "5228afe5909840fe68eaff90eb80b348949b0504cc3d345219e15d46e33e85b8",
      "size_bytes": 1250
    },
    {
      "path": "rig/diagnostics/sweep-lumbar-rotation.yaml",
      "sha256": "4321a0ff258722e15037258cff5606d588e5d087b82445eb1a23c9959cbe3338",
      "size_bytes": 1229
    },
    {
      "path": "rig/diagnostics/sweep-mtp-bilateral-extension.yaml",
      "sha256": "4590f8f428640e6d6d2ebdfb824d5bee72b509afcf26a3eb21514aabecdb1fca",
      "size_bytes": 1413
    },
    {
      "path": "rig/diagnostics/sweep-pelvis-lateral_tilt.yaml",
      "sha256": "abcd3a1414837fb04395fca467db56eb243f2d81777a4714c4c5e506a1a86eb3",
      "size_bytes": 1242
    },
    {
      "path": "rig/diagnostics/sweep-pelvis-pitch.yaml",
      "sha256": "70c13c92600fd2fccca0b63d03e8e456c2eeeb432f09662e491d220e36b7c426",
      "size_bytes": 1221
    },
    {
      "path": "rig/diagnostics/sweep-pelvis-yaw.yaml",
      "sha256": "4ee6b9279d5d2c9fb59712d579fa282a7803377355b0c2b5f83208144e4370ba",
      "size_bytes": 1215
    },
    {
      "path": "rig/diagnostics/sweep-shoulder-bilateral-elevation.yaml",
      "sha256": "20d15b66d61cb6bd78d30439dc4676d4428205036d97ffeaa38a72a85310c1ff",
      "size_bytes": 1431
    },
    {
      "path": "rig/diagnostics/sweep-shoulder-bilateral-external_twist.yaml",
      "sha256": "5791602483c3dfd911af0d07094d25601e848d33b1c694b3a83c8446ec1d5e56",
      "size_bytes": 1453
    },
    {
      "path": "rig/diagnostics/sweep-shoulder-bilateral-plane.yaml",
      "sha256": "5f216fbe240f5d7f92e58751bfbf116ccb757a089ad93ab9260cacfb8b396b6f",
      "size_bytes": 1958
    },
    {
      "path": "rig/diagnostics/sweep-thoracic-flexion.yaml",
      "sha256": "1f799e2d4516876b6c676ee88eb9b1585a9d979ded7eb3b4767f31c72e760cae",
      "size_bytes": 1232
    },
    {
      "path": "rig/diagnostics/sweep-thoracic-lateral_flexion.yaml",
      "sha256": "1d99cf8b57c0cc874ef4dc88a05e41d523c6c58178d90ce237095e9bb9ac9c9b",
      "size_bytes": 1256
    },
    {
      "path": "rig/diagnostics/sweep-thoracic-rotation.yaml",
      "sha256": "5959ffdb10c27e41740dec770d833c9ee5ba889170dd81b061400adae5b09d41",
      "size_bytes": 1235
    },
    {
      "path": "rig/diagnostics/sweep-wrist-bilateral-flexion.yaml",
      "sha256": "869ef6af54654927ecc48101ba569256a22a8766090d34985dc4c5ae36f506bc",
      "size_bytes": 1413
    },
    {
      "path": "rig/diagnostics/sweep-wrist-bilateral-ulnar_deviation.yaml",
      "sha256": "659dc258e1b962c307d2a4d028871dc30df3a8df04cca40979b8c839efa20cf2",
      "size_bytes": 1445
    },
    {
      "path": "rig/diagnostics/walking-in-place.yaml",
      "sha256": "7648d551c47422ca780817a753ce83003b3469d5fbdcc7ff74118a924a937a00",
      "size_bytes": 2384
    },
    {
      "path": "rig/humanoid-map.yaml",
      "sha256": "b973ea08b4daab35d2f022c05db51d6e57ab08edf36108cfa3f37e87801729f2",
      "size_bytes": 9662
    },
    {
      "path": "rig/mobility/adult-reference-v1.yaml",
      "sha256": "9d3316fd6ed72a645ceb4a0e88bb748ee07b58c19bfa7def8a8d18bdee6108cc",
      "size_bytes": 81898
    },
    {
      "path": "rig/profiles/adult-reference-v1.yaml",
      "sha256": "e93d232f8b2f64a06f8a8064b6fe0dcdcbd0afc3050f27faa67799906fd94e41",
      "size_bytes": 645437
    },
    {
      "path": "scenes/skeleton-review.yaml",
      "sha256": "69a3060ebfc75951563f2c811b7224b5004303fd038953ac8fb1cbc79b1e6a9e",
      "size_bytes": 1863
    },
    {
      "path": "schema/README.md",
      "sha256": "d3097d222b4a7ab7f92a1c28a0afe6a77b687162764e33ee5d844245f4dcf73e",
      "size_bytes": 5438
    },
    {
      "path": "schema/body-groups.schema.json",
      "sha256": "f6358ef3f2a0b6ec410e21885fcbd3b6e4cc98b6a3664c85ab604b2e34e3aecb",
      "size_bytes": 1552
    },
    {
      "path": "schema/character-appearance.schema.json",
      "sha256": "80f38bf36e817c8259ef8a677943360c35cdb4a37ed6471c317b3ac96f475604",
      "size_bytes": 3078
    },
    {
      "path": "schema/character-definition.schema.json",
      "sha256": "0bcd91cb93a751e394c805c76dcd026e3baacb4642c3b6b0489123b8a0fd8892",
      "size_bytes": 2208
    },
    {
      "path": "schema/character-registry.schema.json",
      "sha256": "97e295e91223646eddd3e30b568afee150223c68bc4074d3327cac2c75b84577",
      "size_bytes": 1751
    },
    {
      "path": "schema/character-template.schema.json",
      "sha256": "613cdfd4317932f23b533dec9c6712f18b9696d4b98ed9c2240f562489b4edea",
      "size_bytes": 27372
    },
    {
      "path": "schema/common.schema.json",
      "sha256": "964a9b1f158d49bb50023061f7d12455534eac122be36af92e18c9146ca48a48",
      "size_bytes": 3959
    },
    {
      "path": "schema/consumer-motion-snapshot.schema.json",
      "sha256": "b1d0493bfc50c2bdc1ede0ea092b1e850d50e59d74018bef2b651b4e6c0386db",
      "size_bytes": 2024
    },
    {
      "path": "schema/consumer-motion.schema.json",
      "sha256": "b3cf6a3663a754a40513beed747fe30d60be88254180bc543e12b20a69a3e4f2",
      "size_bytes": 5272
    },
    {
      "path": "schema/diagnostic.schema.json",
      "sha256": "13eac9ccf9cfd1422bf72aa7bd58a5a59929327edb21fd47649a6b7f8053fe52",
      "size_bytes": 9985
    },
    {
      "path": "schema/humanoid-map.schema.json",
      "sha256": "57ca8e6849689a08a4f86f5adbe56f1b0b8816ae4fecc2021ae85a6715ac054c",
      "size_bytes": 2579
    },
    {
      "path": "schema/mobility.schema.json",
      "sha256": "a0e842c216ebdbeff485979e6cf37e983e5277bf728ad617d88b109b2ba996be",
      "size_bytes": 26132
    },
    {
      "path": "schema/profile.schema.json",
      "sha256": "65c27eb924b635db055b6a83fc2a9dc8a30acb7ebf043b29c21374b2bb487104",
      "size_bytes": 21477
    },
    {
      "path": "schema/review-scene.schema.json",
      "sha256": "0985a5e486816bc8e5211b2f43ac9207ffda29a7ecb62195fe6d24c91a992ff4",
      "size_bytes": 5334
    },
    {
      "path": "src/humanmotionlib/__init__.py",
      "sha256": "05d9ef5d14140d291b7892decba7383961eafdf9d8c9d11b937452ae8f73f7cd",
      "size_bytes": 217
    },
    {
      "path": "src/humanmotionlib/__main__.py",
      "sha256": "1f77725f6172d53f109ae9023a9f85c5bc1b0afd96f9a3cbb45f252a59237e4d",
      "size_bytes": 100
    },
    {
      "path": "src/humanmotionlib/actions.py",
      "sha256": "76c283516c7830276fcda8db2b06cd4736376f38c748f2a8c2748db92e71a2eb",
      "size_bytes": 6375
    },
    {
      "path": "src/humanmotionlib/api.py",
      "sha256": "5da55121155628d84521c515df6b1dcf3c6fa3ff9d58a13cd455b3bc035144a0",
      "size_bytes": 47289
    },
    {
      "path": "src/humanmotionlib/articulation.py",
      "sha256": "ac9dac52b4d32fa5dc68c465672bbcaa37d7962cfd748f5dce04cb5d079c993f",
      "size_bytes": 4149
    },
    {
      "path": "src/humanmotionlib/backend_measurements.py",
      "sha256": "24c86df6937c8815b99bfa2ff5e8dba6cc94dbf4743b26af9bb4a52c99896987",
      "size_bytes": 10675
    },
    {
      "path": "src/humanmotionlib/balance.py",
      "sha256": "d52e7e2d39783f1ac90171092f7cf6da17a2a7fbda6a5946a01fd86992e4a579",
      "size_bytes": 8976
    },
    {
      "path": "src/humanmotionlib/balance_review.py",
      "sha256": "926ae4f43b6639676a8684049cdf6b0d991b1cbc9e7f83177c37c4e19fd49f02",
      "size_bytes": 4730
    },
    {
      "path": "src/humanmotionlib/blender_backend.py",
      "sha256": "af969319b497505c9294ddf7b4a48e2e669cb471cdc3afa48087df358312dbc7",
      "size_bytes": 46586
    },
    {
      "path": "src/humanmotionlib/build_skeleton.py",
      "sha256": "5d1ed6db1b79288938f3695af9ec7369a0b6cba1eb12e44c832247ab7f982e4c",
      "size_bytes": 23873
    },
    {
      "path": "src/humanmotionlib/character_midpoints.py",
      "sha256": "fd1ec5c602957cbdf10b54305d541e900a237408189dc74ba00c07f9ed051996",
      "size_bytes": 5561
    },
    {
      "path": "src/humanmotionlib/character_paths.py",
      "sha256": "5dd634405b34d42cdaf22777d3f53c0bf78b3d77cb4855e4a38d030576cf478c",
      "size_bytes": 674
    },
    {
      "path": "src/humanmotionlib/character_skinning.py",
      "sha256": "6fd93d392e53bd9035ede37d4155fe3b1bd9fa58f1ef679eea8c55900073054e",
      "size_bytes": 14652
    },
    {
      "path": "src/humanmotionlib/character_surface.py",
      "sha256": "b4eeaa0fbcfccdb5ab87a6efcc3eeb4650710e20a743fb865ada546f8b1b9df9",
      "size_bytes": 58791
    },
    {
      "path": "src/humanmotionlib/character_verification.py",
      "sha256": "911f513ed5648da7fbf27b63411187706ccee8eccae2b327f7dc727b53a806be",
      "size_bytes": 87525
    },
    {
      "path": "src/humanmotionlib/characters.py",
      "sha256": "7888eb0bfb317c92999bc2a817b542d7c6f6d626842607101d309f16bf3f3b9d",
      "size_bytes": 14491
    },
    {
      "path": "src/humanmotionlib/check_host.py",
      "sha256": "a2f146163be6aef57a5d37353b5483e509c161ec2cd3f0846c39b27819be973a",
      "size_bytes": 30994
    },
    {
      "path": "src/humanmotionlib/cli.py",
      "sha256": "3d7bd445d91f9df65450c0e82a0d91402dbf44fc3eea7b1b1f62251c4bb8aba6",
      "size_bytes": 2390
    },
    {
      "path": "src/humanmotionlib/consumer_motion.py",
      "sha256": "9e825adc9c57ff8a60595e2c6435661273f1f14a22ff91e5ba7c37916412d7b4",
      "size_bytes": 33599
    },
    {
      "path": "src/humanmotionlib/consumer_prepared_validation.py",
      "sha256": "f316283c6ec469d4fc6c4ece6dcd1b6b6fd837b1086b7484353c47e619f935af",
      "size_bytes": 1923
    },
    {
      "path": "src/humanmotionlib/contacts.py",
      "sha256": "ed62f8d251f84fda88c0d7f53457d6e2d46eb4af440dee11b3586e2771181604",
      "size_bytes": 6527
    },
    {
      "path": "src/humanmotionlib/coverage.py",
      "sha256": "1be2c882e13594dc1db8a1675e10d5d9c5ce6469942413161fbf8c5a27e3e6ca",
      "size_bytes": 5202
    },
    {
      "path": "src/humanmotionlib/dense_floor.py",
      "sha256": "48db1587b533739ed746d857e4b69dd9145e27342cbfd7f7d42863127005d913",
      "size_bytes": 5107
    },
    {
      "path": "src/humanmotionlib/dense_verification.py",
      "sha256": "db0531424ecdf641d041706b21e70889ba5373a671a1ca20ebfa23c493edfd70",
      "size_bytes": 11899
    },
    {
      "path": "src/humanmotionlib/diagnostics.py",
      "sha256": "fc27a472abcdae18ca28c44b0463ac8ed5e917992ff2f819424d7f3b45d5beb5",
      "size_bytes": 7995
    },
    {
      "path": "src/humanmotionlib/finite.py",
      "sha256": "5025d1a89810c24c6069f5190620c8a0e7adb81e551c3478d69585d1f20cd0f1",
      "size_bytes": 906
    },
    {
      "path": "src/humanmotionlib/geometry.py",
      "sha256": "e8f676adfacff586799c7861d10b84fe41926bdba4d010e5f1948f330f6e8a96",
      "size_bytes": 5556
    },
    {
      "path": "src/humanmotionlib/guides.py",
      "sha256": "d6c9d8f97967c19ec38247d0fbcae72458def65ac46323cf47b50bbfd497f093",
      "size_bytes": 4687
    },
    {
      "path": "src/humanmotionlib/kinematics.py",
      "sha256": "603e08baee60881af19aac7da8248ed187d3be3f591d2cc907b23666859ac9b4",
      "size_bytes": 7684
    },
    {
      "path": "src/humanmotionlib/math3d.py",
      "sha256": "d8d172905f0d3be1f1372433a564ae8f7626e82c0b48fd602ff3dda3cb7309e4",
      "size_bytes": 4645
    },
    {
      "path": "src/humanmotionlib/measurements.py",
      "sha256": "436def5b9e4057fdd732a275f203fe54bf417b95d355e010aaf58b4fd573e969",
      "size_bytes": 16662
    },
    {
      "path": "src/humanmotionlib/mirror.py",
      "sha256": "d21106b5f26bbdb03f720ac37f2e5c4eb2bd1fc2de3c75b88c9b0d0aa2951198",
      "size_bytes": 3648
    },
    {
      "path": "src/humanmotionlib/package_resources.py",
      "sha256": "77361cd32d35410af94186b91cffa04d0c141f1244997a479d56bc047a66fea1",
      "size_bytes": 5074
    },
    {
      "path": "src/humanmotionlib/poses.py",
      "sha256": "af49add6256d4523ed7e60662a9d6a6cb002cd9464fec848413d5303f2ee025e",
      "size_bytes": 4108
    },
    {
      "path": "src/humanmotionlib/prepare_skeleton.py",
      "sha256": "831cb21092498987cd3b2e0381ad7277c87030ffa1db3c353aaff28f393c7d3e",
      "size_bytes": 6667
    },
    {
      "path": "src/humanmotionlib/prepared.py",
      "sha256": "2e6e39aa67272f45c7cebc66eef165c345dec57cf39651aea46146a3a266d59d",
      "size_bytes": 8843
    },
    {
      "path": "src/humanmotionlib/presentation.py",
      "sha256": "39104fdde05104eb3ef0a3a0d4b3035899c118e46670d26a7df4a2759277fec1",
      "size_bytes": 28560
    },
    {
      "path": "src/humanmotionlib/render_contract.py",
      "sha256": "7b648e0effeaaed191ea19596ba4a5882c51764834d9e7100b4d7741b9cf342d",
      "size_bytes": 13984
    },
    {
      "path": "src/humanmotionlib/review_graphics.py",
      "sha256": "08ca13a0928d8cda4d2a88a2e93a861b714918c50296adf1ee58330c64115c31",
      "size_bytes": 5542
    },
    {
      "path": "src/humanmotionlib/review_pack.py",
      "sha256": "14016d609e8c18abeeed9b3e9e71710aafbf7f33cf298fc246503a9a45de1a1d",
      "size_bytes": 99464
    },
    {
      "path": "src/humanmotionlib/run_blender.py",
      "sha256": "999163ef4e60fdf998df8717bbd5e5418283ba09a7de8d49404b5182178b4164",
      "size_bytes": 21580
    },
    {
      "path": "src/humanmotionlib/runtime.py",
      "sha256": "6d8ac058bdda5d353ccfdf5da080c1a19052962761b722c7a9834cf3aaf8c1c8",
      "size_bytes": 38234
    },
    {
      "path": "src/humanmotionlib/sampling.py",
      "sha256": "135135cea23ccf653d2d6f443bc60d76bb9720ebd322b1f4969c17a6589d1964",
      "size_bytes": 1247
    },
    {
      "path": "src/humanmotionlib/source_validation.py",
      "sha256": "db55de216fc04820313d1c4cd547db34a04dc76b126810b159b4455121b3d51d",
      "size_bytes": 3195
    },
    {
      "path": "src/humanmotionlib/stature_comparison.py",
      "sha256": "77e2176045d41b62b628bb6eac7c4387993c71739b371d2815f3727a06997f53",
      "size_bytes": 5373
    },
    {
      "path": "src/humanmotionlib/thorax_measurements.py",
      "sha256": "9d1ba1f285c1232927888463124e07f2df345c79e381d9bdae0a72b4740fe516",
      "size_bytes": 10083
    },
    {
      "path": "src/humanmotionlib/validate.py",
      "sha256": "15c5e8347edf6cb3b515b4fe030bac622d190a5922cea25e8f7a7076488f05c2",
      "size_bytes": 18169
    },
    {
      "path": "src/humanmotionlib/verification_run.py",
      "sha256": "8943d3f0ceb1e9fa683e3fa8d12a94b1b79fd038a46f48662b8910bc0a0491e0",
      "size_bytes": 9171
    },
    {
      "path": "src/humanmotionlib/verify_skeleton.py",
      "sha256": "bcbe29dceac7e8f3fa0538daaa94983c1e41903ae6b0de1fc84b17bba910243e",
      "size_bytes": 24986
    },
    {
      "path": "tests/blender_fault_harness.py",
      "sha256": "3b9177d49755a07910bd5b0c5adfe0f903e2cb7a656615f134906a7c7ac689ea",
      "size_bytes": 4938
    },
    {
      "path": "tests/installed_acceptance/run.py",
      "sha256": "5d9449975e705c4e1a1ef535b4184915f6d5f774206bafe2a400aeb6079c9219",
      "size_bytes": 48568
    },
    {
      "path": "tests/run_roots.py",
      "sha256": "16255100fe8aae2b969ea8b7c1521e5476e1c1c0dc0140a8c88c6f149c23e8eb",
      "size_bytes": 3129
    },
    {
      "path": "tests/test_action_transforms.py",
      "sha256": "e3cd177586ee2499a6cd63608ce8042cc87843c02cdd3fc8e8aa2e8194c7e886",
      "size_bytes": 5845
    },
    {
      "path": "tests/test_actions.py",
      "sha256": "e499b3d14a94d8c338add321a803e3e1b3b3121e27cca2b3270ecd231bd95af3",
      "size_bytes": 7017
    },
    {
      "path": "tests/test_api.py",
      "sha256": "4aed8afc2e16350ba51e93242839caaf3a2751414ca6e9485b634ddf754c12a1",
      "size_bytes": 36270
    },
    {
      "path": "tests/test_balance.py",
      "sha256": "ecdc1c81bf7c26bd9408dc9c8d7d663098654c3e415fbfb2983b4dbc2d439247",
      "size_bytes": 13244
    },
    {
      "path": "tests/test_blender_backend.py",
      "sha256": "ffcc5395cce213e7761e5833067b13f4d780205cbfdc0d4ea2969ca0dc9e1060",
      "size_bytes": 9172
    },
    {
      "path": "tests/test_blender_bootstrap.py",
      "sha256": "2462a1eec6683b0db87c1b09cb1981a522760beff4cdc0282d4c53c42a13c8d0",
      "size_bytes": 2368
    },
    {
      "path": "tests/test_build_adapter.py",
      "sha256": "ac288fa316a98d90caa44aa37106de89c50d7cab7f2fded39f4b625e9a863d50",
      "size_bytes": 7658
    },
    {
      "path": "tests/test_build_skeleton_paths.py",
      "sha256": "c5daf96586ded9612de1cf8e7e28ae814cd170aa215bd3587c2ef7af124e406d",
      "size_bytes": 2702
    },
    {
      "path": "tests/test_character_api_results.py",
      "sha256": "dcea602513ee81f374f07943160b8b63a9bee334fe09a5673a9603d19f69f04c",
      "size_bytes": 15428
    },
    {
      "path": "tests/test_character_backend_reference.py",
      "sha256": "8363dac8e6424010522bd1b0e37c9c05a76d203a9bf9e6ec2b6da62aa97eb7b1",
      "size_bytes": 6806
    },
    {
      "path": "tests/test_character_compiled_skinning.py",
      "sha256": "2029ea3d0f0aa9aa4770503e2ebfaea3317fa1a9b359dd206b11f47cf80e46da",
      "size_bytes": 5471
    },
    {
      "path": "tests/test_character_installation.py",
      "sha256": "28c39510575a1c89c6c2ad4d18d6e7f3936d8bdccbd1d5d61c6bcea7b589801b",
      "size_bytes": 15217
    },
    {
      "path": "tests/test_character_integrity_faults.py",
      "sha256": "db6fc4b6d879a631083f87d6c70895c2252e4dfb02304290aaaaf6f138690a43",
      "size_bytes": 16925
    },
    {
      "path": "tests/test_character_propagation.py",
      "sha256": "cc00a28a4366302d2dcbe9f5d1a31dee18f4e7f22a2ce5e54ec487bcd16aed93",
      "size_bytes": 10473
    },
    {
      "path": "tests/test_character_review_pack.py",
      "sha256": "4d575a4468cdc579dbc773c6003a2f2a4ff0decfe58b885594f5738276833902",
      "size_bytes": 16629
    },
    {
      "path": "tests/test_character_skinning.py",
      "sha256": "31525f597f290b145be6b624585653fa1d24d5190ac6c193ffee5ea5042ac055",
      "size_bytes": 7698
    },
    {
      "path": "tests/test_character_surface.py",
      "sha256": "b226190280129fe671f5d1769ba9d9b0521618fef57e63b177afab70d73a11cb",
      "size_bytes": 27074
    },
    {
      "path": "tests/test_character_verification.py",
      "sha256": "2ea7d4be4eaf2d844da8a3c1fdc16eca1c9a636d63f61d1bcd4ea442c36e76e1",
      "size_bytes": 38402
    },
    {
      "path": "tests/test_characters.py",
      "sha256": "59fc56dc2c50cd0f53ce0296f25c962d75c71c7753a568c57189dc5bd084ebf8",
      "size_bytes": 17855
    },
    {
      "path": "tests/test_check_host.py",
      "sha256": "87052556d1a605cac4e04b446828054d36376de603ad624c07350bf33db563a3",
      "size_bytes": 4362
    },
    {
      "path": "tests/test_cli.py",
      "sha256": "3b1b186544b12b0ef0a07b5cb9b7829ed364e3e0b13fd9c2da03b2ec02f10064",
      "size_bytes": 4425
    },
    {
      "path": "tests/test_consumer_motion.py",
      "sha256": "bed2813d7865ff21c78a47a28b26a8eff38a418839ee5d778ccdf043c3c16677",
      "size_bytes": 42086
    },
    {
      "path": "tests/test_coupling_measurements.py",
      "sha256": "4c2d97d5a490a58b887ba9ed4a35bc81563cf9126ceec952295eb0b75177f841",
      "size_bytes": 8787
    },
    {
      "path": "tests/test_dense_floor.py",
      "sha256": "791573d71a8559561b6ec654626e097fcceb4e3c8f668abace02ebab26881896",
      "size_bytes": 2081
    },
    {
      "path": "tests/test_diagnostics.py",
      "sha256": "7c5feeec1bee1f2ee80f343ef4eead05c99454e295e01060f240b2dce4f53641",
      "size_bytes": 10839
    },
    {
      "path": "tests/test_geometry.py",
      "sha256": "d23b94e80398323e505b436161e83fb0c796b47ffa05a093c43e4205c844979b",
      "size_bytes": 2248
    },
    {
      "path": "tests/test_guides_and_coverage.py",
      "sha256": "98fff7e69b68060ecf93fd1554d216de1f7f84cdd6ca491ce77e190d503b4fd8",
      "size_bytes": 4834
    },
    {
      "path": "tests/test_kinematics.py",
      "sha256": "1d59b6fea3368b947e7de5b454739c6a7f65f70eadc36200f74d6016866ad132",
      "size_bytes": 3354
    },
    {
      "path": "tests/test_mapping_dossier.py",
      "sha256": "51b5c7b52a63c725670a0f883c6390aa83e7138efbf291598321576294d0f97f",
      "size_bytes": 3244
    },
    {
      "path": "tests/test_math3d.py",
      "sha256": "25db58833b90555a559b7938a612de070217cfb76b22f3fc99c3e8c6dbad41e2",
      "size_bytes": 2633
    },
    {
      "path": "tests/test_matrix_presentation.py",
      "sha256": "a4741376fac9774abef54f76a6a93404fc34d1a996fcd35c84c9a1fc9f355c7a",
      "size_bytes": 14793
    },
    {
      "path": "tests/test_matrix_test_outcomes.py",
      "sha256": "6719d785d9eb80087b1144f75a415d4fb1ae74e39a1ee9883d33b38318698a54",
      "size_bytes": 17204
    },
    {
      "path": "tests/test_matrix_workflow.py",
      "sha256": "e10b738c56dd4859149e30f2d0bfdc2306cd352c65135ffc723ad063dfc7fe92",
      "size_bytes": 48118
    },
    {
      "path": "tests/test_mirror.py",
      "sha256": "d5566c6d2f2b381490cdfbc477d04e5acfa3d6ef9e3a031b599f546251abb5f0",
      "size_bytes": 4270
    },
    {
      "path": "tests/test_mobility_dossier.py",
      "sha256": "6162c44a7991802585e77192bd1cb025643b66cbccec9777ec4f3cb03ff1993e",
      "size_bytes": 4867
    },
    {
      "path": "tests/test_pipeline_faults.py",
      "sha256": "c30fa6295afcb9f892278a5629c05e6a7800963d0299b453000bc25713bf3ac4",
      "size_bytes": 4697
    },
    {
      "path": "tests/test_poses.py",
      "sha256": "16b1c76b1069e6be0b4cb73ac58b51f5f36a453410310495090071b3cae791e5",
      "size_bytes": 3230
    },
    {
      "path": "tests/test_prepared_contract.py",
      "sha256": "5838293b644ddfae2a31b58cb2dc4056f8835adc726b8aaeffd27326d9389818",
      "size_bytes": 2493
    },
    {
      "path": "tests/test_profile_dossier.py",
      "sha256": "c1c74cab545feb4dd5f3397bf87ab088966fb089f39edc25f17014258a9730b3",
      "size_bytes": 5646
    },
    {
      "path": "tests/test_project_cleanup.py",
      "sha256": "68f33a69c6f49eea7c4e42662f7c3d7efde577976dae77f0a61c72f8b08ee824",
      "size_bytes": 23276
    },
    {
      "path": "tests/test_release.py",
      "sha256": "231f9a0463da3f97643d522ec84c595578b284223d7f09087dde4659d92b10e7",
      "size_bytes": 24460
    },
    {
      "path": "tests/test_repository_workflow.py",
      "sha256": "cb19672d987f7b12dc7e9fc3466dde7f1a6790923c7bb26ec7a80cd51d649d6e",
      "size_bytes": 24507
    },
    {
      "path": "tests/test_review_aspect.py",
      "sha256": "c3e296323124de65d4ce420103c5ad43f369a0272c7084fb724f3239c8385350",
      "size_bytes": 1391
    },
    {
      "path": "tests/test_review_graphics.py",
      "sha256": "bcc217837280d4bce1c10bde1d78fcd51c16291f37da1cff837765d4d4f2b448",
      "size_bytes": 1819
    },
    {
      "path": "tests/test_review_pack_supervision.py",
      "sha256": "10505ac3a68af5e2d99523ad1634386a5281afa1eb1f2f9cc4706a19e66af721",
      "size_bytes": 42770
    },
    {
      "path": "tests/test_review_presentation.py",
      "sha256": "6afb86c2ca0fd4b2e01dac6faaf6216c85bd5d9a899a675d0d755b425b895753",
      "size_bytes": 15210
    },
    {
      "path": "tests/test_run_blender.py",
      "sha256": "e4652ff63060b5d3670b3de0ef0d3309feda5d4b1db8b5f0aa71b9262844582b",
      "size_bytes": 24522
    },
    {
      "path": "tests/test_runtime.py",
      "sha256": "13ac6e9c0e595cb0f23389e31895cc2e42b5079a7e3e946312bf43bc978a0774",
      "size_bytes": 21419
    },
    {
      "path": "tests/test_runtime_workspace.py",
      "sha256": "b0f48a665377f6e06f79bce0e03f50739b9c102bd42316574f6b8fe0abdad290",
      "size_bytes": 3501
    },
    {
      "path": "tests/test_selected_numeric_fixture.py",
      "sha256": "c2d9f0e19f93f7e054a863ad48f8877279d4a8a8375a4382e3744f0056cb8feb",
      "size_bytes": 30011
    },
    {
      "path": "tests/test_source_integrity.py",
      "sha256": "199afad1a758dc3ca1e6b0ca8e0a36d9605339ef0a19c7c60fa1ef701b760339",
      "size_bytes": 4050
    },
    {
      "path": "tests/test_source_schemas.py",
      "sha256": "26f41d7fada239c765285525c8674508857c3a5775d95974c7c5be1abe5da2b4",
      "size_bytes": 9718
    },
    {
      "path": "tests/test_thorax.py",
      "sha256": "67333f68bffef9e6824ee702f25955502d93a92ed82c44605a2e62ffe9fd3a0e",
      "size_bytes": 7394
    },
    {
      "path": "tests/test_verification_workspace.py",
      "sha256": "85806171989d6b5c8fdc34b5ff094e78c5c908a1142e1ab571b08b7f5de6690f",
      "size_bytes": 14762
    },
    {
      "path": "tests/test_version_builds.py",
      "sha256": "468a8c4c0b7582b9bec22f1b31098d318efd7fbf9d721907d612a88de382ada0",
      "size_bytes": 4684
    },
    {
      "path": "tests/test_walking_dossier.py",
      "sha256": "af6e16e23290684fee25d00bdaf4b0ecd421f2334929dc996e3456ead933fab5",
      "size_bytes": 7514
    },
    {
      "path": "tools/README.md",
      "sha256": "3f1b9c174c684a529ecd74b9880f88bf37a920f22a22549920a7973090a696a3",
      "size_bytes": 75157
    },
    {
      "path": "tools/matrix.py",
      "sha256": "85102545fb4e12d4fd346e2082656e9cd5630390ef0a79ed9604355dc48f9563",
      "size_bytes": 36017
    },
    {
      "path": "tools/matrix_presentation.py",
      "sha256": "b8fba964e3a0904501d408ce7054b7e9e5ff1f4048735d4fb6d692d63a58f251",
      "size_bytes": 26586
    },
    {
      "path": "tools/project_cleanup.sh",
      "sha256": "e3a7a5a34e6e2033d35cc3812828c709c0e92181813b1d9a7b6fb7e1a163064b",
      "size_bytes": 12666
    },
    {
      "path": "tools/release-config.toml",
      "sha256": "75d222949b06db4d1a831bf1e79626fa0e345988c11652479e1862c8e7c62d75",
      "size_bytes": 204
    },
    {
      "path": "tools/release.py",
      "sha256": "3d0245a67a8c993f374b636065a6ecedf0d4ca66a697cbaab97d416b1fe385b7",
      "size_bytes": 36793
    },
    {
      "path": "tools/repository.sh",
      "sha256": "d3b4d77ce6a41f13e7318c2db03aa54bff6e1b0b91c140730ab22ffb8e4223ac",
      "size_bytes": 8021
    },
    {
      "path": "tools/repository_workflow.py",
      "sha256": "d90951400810bd7dca8c04a1fd922d05b62503526a8f6e6f73ad52ef1cbed792",
      "size_bytes": 27868
    },
    {
      "path": "uv.lock",
      "sha256": "a47b8d29266ffb83a8d22135bb8d724780b2ee71097b0943fe427bc44bd47225",
      "size_bytes": 27594
    }
  ],
  "file_count": 328,
  "aggregate_sha256_path_nul_sha256_newline": "37b4e78367affe16a50e7a4b6030ccd02f1b1b0ef1da467e1f8e490929b27e8d"
}
```
</details>

<details>
<summary>Amended 329-file current source inventory</summary>

```json
{
  "status": "current workspace identity after reviewer-only patch",
  "included_scope": "Regular non-symlink source/configuration files including tools, CI, docs, .codex, library source, tests, schemas, canonical data and OpenSpec artifacts.",
  "excluded": [
    ".git/**",
    "build/**",
    ".venv/**",
    "**/venv/**",
    "**/__pycache__/**",
    "**/node_modules/**",
    "**/.pytest_cache/**",
    "**/hand-off.md",
    "**/tasks.md",
    "**/review.md",
    "mutable task-/audit-report/review-report markdown files"
  ],
  "files": [
    {
      "path": ".DS_Store",
      "sha256": "c8aade81421352f28d9f0597dbbec6e494aa23a51b8a80a60f892e823333f8b6",
      "size_bytes": 8196
    },
    {
      "path": ".agents/skills/.openspec-target",
      "sha256": "243b0dc9b847e66c440dca985e10fe0ce9e29c379b018ddd5747ba8948f84cc8",
      "size_bytes": 6
    },
    {
      "path": ".agents/skills/openspec-apply-change/SKILL.md",
      "sha256": "03e9c7f88580bc0fe0015f40cbdb1834bf1d56597bdf0b593e98e7a0857fbb4b",
      "size_bytes": 11384
    },
    {
      "path": ".agents/skills/openspec-archive-change/SKILL.md",
      "sha256": "0b0a3e43dd6d1d3b7c3b23527b8d50976b527ba294eef9649696600f584df032",
      "size_bytes": 16645
    },
    {
      "path": ".agents/skills/openspec-continue-change/SKILL.md",
      "sha256": "232f9092e4dc79d8d23d5674aa930af28ce0e00349177a490c438b4f7252ec39",
      "size_bytes": 9862
    },
    {
      "path": ".agents/skills/openspec-explore/SKILL.md",
      "sha256": "31a4c7543ceb40a2c4b45a184de87f4cb2921a1f98a69688acc51de3ac3e177f",
      "size_bytes": 23134
    },
    {
      "path": ".agents/skills/openspec-ff-change/SKILL.md",
      "sha256": "59f8d7a6a3a8c10bc8ee00ba88f4596edf8039b0aac51bfcfd70f4eb15b3641a",
      "size_bytes": 11247
    },
    {
      "path": ".agents/skills/openspec-new-change/SKILL.md",
      "sha256": "46e2a8bd1d1e17fe55608b91819580bf20810ab23408c5981e23d3cc836fb344",
      "size_bytes": 5894
    },
    {
      "path": ".agents/skills/openspec-propose/SKILL.md",
      "sha256": "bd3d2fef6701ef39e5181e54a258f43a3b58a67369f4dfac8926b9b7e9229a26",
      "size_bytes": 16312
    },
    {
      "path": ".agents/skills/openspec-sync-specs/SKILL.md",
      "sha256": "0631ef731343aaa75d6466fe36ce3f2deecd57cc07e135026159fcdec93f2eb8",
      "size_bytes": 15826
    },
    {
      "path": ".agents/skills/openspec-update-change/SKILL.md",
      "sha256": "2e214729f6e75a07fd753219315447909fa8e4c0837fdbbee62d9b1c4cf46c40",
      "size_bytes": 11524
    },
    {
      "path": ".codex/agents/architect.toml",
      "sha256": "936240dc877abd8822c2d301a5c9b5fe71c361435ea9d9615f08087d02ab286a",
      "size_bytes": 4470
    },
    {
      "path": ".codex/agents/dev.toml",
      "sha256": "e006eca3e3190ea7a85c541c2f3ffeeecd4224a3d467807c3391da3ce8bf92f9",
      "size_bytes": 6030
    },
    {
      "path": ".codex/agents/reviewer.toml",
      "sha256": "476766c9e0123cbe80a33df206e43808d1d0c65f7648304c296de7c36aa5ce64",
      "size_bytes": 9648
    },
    {
      "path": ".codex/config.toml",
      "sha256": "da7af8ca8c679e3e90c32370b0a0bfa4137b1712f77f4871d8bd59741e7f36e1",
      "size_bytes": 380
    },
    {
      "path": ".codex/rules/default.rules",
      "sha256": "2a4c7c0c70307d2b7481cbd5bb12291cb3429b9e5537f4492cd1321ed01f6416",
      "size_bytes": 270
    },
    {
      "path": ".github/workflows/host-python.yml",
      "sha256": "965687e6268cfbfc755ad565f46e65ecadb670af3d1ce34fa999efb799cd1a51",
      "size_bytes": 5384
    },
    {
      "path": ".github/workflows/package.yml",
      "sha256": "d490a6eda7ce5f8e1d3ff8e63b140181b45c59a2a1043d8302b3aea4b84ca58e",
      "size_bytes": 26241
    },
    {
      "path": ".github/workflows/release.yml",
      "sha256": "1f65cf0c62415ecec09331a3ff9300d8b6846456c9f163e7dc6f19ded985f381",
      "size_bytes": 9312
    },
    {
      "path": ".gitignore",
      "sha256": "6a8d4b2377a13484efecd853ea1ff02f5239ae41512d6dbca3f8a9b5c3ae0ff6",
      "size_bytes": 49
    },
    {
      "path": ".python-version",
      "sha256": "a876e0b10411037a012498b9fe18d9bc1df32ed8b722a13564dc944ddcfd9135",
      "size_bytes": 5
    },
    {
      "path": "AGENTS.md",
      "sha256": "6262f5187fa29172ac381b97c91b5c2ce5ae22ceed86058bb4d5ba758a5bfe81",
      "size_bytes": 22136
    },
    {
      "path": "LICENSE-CODE",
      "sha256": "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
      "size_bytes": 11358
    },
    {
      "path": "LICENSE-DATA",
      "sha256": "6b2a8a413077dd73e8ed564471875c2b9634ca3b76dcbe608b8094090d4392ce",
      "size_bytes": 859
    },
    {
      "path": "MANIFEST.in",
      "sha256": "07856c95409fa1956fdc075e2d2b648afe8ffcec12a48b00bd326274b353c8ff",
      "size_bytes": 322
    },
    {
      "path": "Makefile",
      "sha256": "72ffbda0d4a2e3296a89497e8321d94a7cd12504c2d64ea594c5d25a4fb8cbeb",
      "size_bytes": 3214
    },
    {
      "path": "THIRD-PARTY-NOTICES.md",
      "sha256": "a5facb0a8d7eca51ad5d667d3f4f8469fc6cf157f06f443962571d2dd3cf40a4",
      "size_bytes": 7331
    },
    {
      "path": "characters/README.md",
      "sha256": "dc6f9f0305b8c204a40698f27b5084b51340b7d1c6f6725c417c4d9068decf2f",
      "size_bytes": 1069
    },
    {
      "path": "characters/appearances/female-v1.yaml",
      "sha256": "3c4253cae9d7a08362c64be568c0eb1531bc442ba5952f4d74fe6d11efb1ebe1",
      "size_bytes": 925
    },
    {
      "path": "characters/appearances/male-v1.yaml",
      "sha256": "bfa1aa9bf27a24c4450b04ef81dc3fd8e4225d27ab385bb0f12c9d813f2dc89c",
      "size_bytes": 834
    },
    {
      "path": "characters/definitions/female.yaml",
      "sha256": "21f58bd393e92375d268168aef59bd7b03628ecc1032daae9e0c09b05ebe779b",
      "size_bytes": 667
    },
    {
      "path": "characters/definitions/male.yaml",
      "sha256": "ab58396f7aa7eb7d493126a907b9368efb43f725be512d8cf724bfb29c0eab96",
      "size_bytes": 661
    },
    {
      "path": "characters/definitions/skeleton.yaml",
      "sha256": "787f6a8c3cd43b9d17ec23c03a9d96d6eb966d5d31a9dd4a66034138dec784d7",
      "size_bytes": 813
    },
    {
      "path": "characters/registry.yaml",
      "sha256": "41965c69c390b7e64d5ce269490eed7a5bf8ffb9e7ead77def104eb37aae6fe0",
      "size_bytes": 581
    },
    {
      "path": "characters/templates/exercise-mannequin-v1.yaml",
      "sha256": "2818a3e4d2fd6075b08b42b31a574b5ed7a7f4e4df96e2a34f1589916ec00f57",
      "size_bytes": 9233
    },
    {
      "path": "docs/anatomical-human-skeleton-preflight.md",
      "sha256": "19a0cece534051397f180d2a7df37ccd16550258ab7419694bf546a8b3ffa4c2",
      "size_bytes": 6855
    },
    {
      "path": "docs/anatomical-skeleton-acceptance.md",
      "sha256": "7da928ed2dd8ce6ad0b3a8c330592c17566bac979fea2eb3ed9ef0c63640acb1",
      "size_bytes": 10809
    },
    {
      "path": "docs/backend-crash-triage.md",
      "sha256": "17700d6b2a078ddd5e6d92dab9c71deb47c04690b55a27a98be832449fc4350e",
      "size_bytes": 4825
    },
    {
      "path": "docs/build-matrix.md",
      "sha256": "4009fe64ff81aae06919ef789a550b8534fad0d1103aa4e1821044ae4aa2fbba",
      "size_bytes": 5962
    },
    {
      "path": "docs/character-models.md",
      "sha256": "7848fa384dd799ad0d6a3613f8d292a6d2e8257cc1c95f9971412aa7e522efdb",
      "size_bytes": 9254
    },
    {
      "path": "docs/usage.md",
      "sha256": "ecbc1d5e067ae5425aa341154aaa58c247e9cc01a6bf789f835a911094830b05",
      "size_bytes": 25802
    },
    {
      "path": "docs/used-materials.md",
      "sha256": "fe889173dd82c97772a7fd6e96a2f5e7df6d503fd9c43c557c73661cdd330dec",
      "size_bytes": 35602
    },
    {
      "path": "hml_build_backend.py",
      "sha256": "3883076ad43e21f77f534fd645095eeae4f600353deec27c4b7952a8483e8aeb",
      "size_bytes": 15589
    },
    {
      "path": "openspec/changes/add-shared-body-characters/.openspec.yaml",
      "sha256": "d002983090acfe222597827aa3c481b59d3a566c704a6e91e0d50bb1d209297d",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/add-shared-body-characters/approvals.md",
      "sha256": "144fe7ada5b4c0da42dd4394465f37a930dbee6b5b7106dae78093ea706c8a1f",
      "size_bytes": 8814
    },
    {
      "path": "openspec/changes/add-shared-body-characters/blocker.md",
      "sha256": "d808fd0e5463bfaecc371e02ee53bd5d23c1dc4ec2f3eaefb899ef45fcbd658e",
      "size_bytes": 8251
    },
    {
      "path": "openspec/changes/add-shared-body-characters/cleanup-inventory.md",
      "sha256": "2e2ee16eb70d0a3672a635109c3a80224c488340391aac933098ac96b9e6b8cd",
      "size_bytes": 26542
    },
    {
      "path": "openspec/changes/add-shared-body-characters/design.md",
      "sha256": "578252262ecb3dc6f299b3fe70fee7f363204b371c293c20e216d2d81272adc0",
      "size_bytes": 97703
    },
    {
      "path": "openspec/changes/add-shared-body-characters/developer-handoff.md",
      "sha256": "b367b7f8fdafa9dd25ae27fbcffbe1d11fb770ded5bdc4a567fba2cb785bcc4a",
      "size_bytes": 88042
    },
    {
      "path": "openspec/changes/add-shared-body-characters/documentation-check.md",
      "sha256": "73de5c8f30a48cee102a8ae24aabd19699a2581a8bec8ffe91d6c075b0f2af8f",
      "size_bytes": 2609
    },
    {
      "path": "openspec/changes/add-shared-body-characters/execution-notes.md",
      "sha256": "eedbf794a2077958c782830bda3c369a2c01563ecc73ed1a616f02c3e09f761c",
      "size_bytes": 3036
    },
    {
      "path": "openspec/changes/add-shared-body-characters/historical-baseline-check.md",
      "sha256": "3ddfa3b229c092778f6986b98bcb50d75fe142863d3874e48a6de5df35a1398f",
      "size_bytes": 3700
    },
    {
      "path": "openspec/changes/add-shared-body-characters/installation-check.md",
      "sha256": "c91d00211b6e4d2e43c8caa3b0b3554137fc6e018f3ff7f06affd1615966cf0d",
      "size_bytes": 17465
    },
    {
      "path": "openspec/changes/add-shared-body-characters/midpoint-check.json",
      "sha256": "fdc4d319233a1943f54b565b70635e701777542c094954d90aa938737bb23b36",
      "size_bytes": 1531
    },
    {
      "path": "openspec/changes/add-shared-body-characters/native-checks.md",
      "sha256": "0d7dc5bc03738879fcde7278fb8a39b20d5988d9938ab69291b9aad1053f097b",
      "size_bytes": 7181
    },
    {
      "path": "openspec/changes/add-shared-body-characters/orchestration-status.md",
      "sha256": "874ec6f2652c4a427479445549576f44049dab606556f2c51286fe291806ec85",
      "size_bytes": 11613
    },
    {
      "path": "openspec/changes/add-shared-body-characters/packaging-check.md",
      "sha256": "7db025d78acbe76117d1b96dbf87b64480050bce2aa98264497a54a2b2574e73",
      "size_bytes": 14032
    },
    {
      "path": "openspec/changes/add-shared-body-characters/proposal.md",
      "sha256": "2ae592d4b251a13a73a17a86a5c43e15b7c3523869806825eb01321603acc7a0",
      "size_bytes": 4205
    },
    {
      "path": "openspec/changes/add-shared-body-characters/specs/character-models/spec.md",
      "sha256": "7dda6afd124b784065adab08fd8ae9f72e17d8e957d7f88333c1cc39c043715c",
      "size_bytes": 19715
    },
    {
      "path": "openspec/changes/add-shared-body-characters/specs/public-generation-api/spec.md",
      "sha256": "fdcff17180050efd524f658f4d6cd646526984c267d35c9039af18a89ef077ce",
      "size_bytes": 15880
    },
    {
      "path": "openspec/changes/add-shared-body-characters/specs/python-distribution/spec.md",
      "sha256": "503623434e212afa29f2a5f4d0d97bd913a22061b9495ff2b3eef2237fb7756d",
      "size_bytes": 4668
    },
    {
      "path": "openspec/changes/archive/.gitkeep",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "size_bytes": 0
    },
    {
      "path": "openspec/changes/archive/2026-10-22-anatomical-human-skeleton/.openspec.yaml",
      "sha256": "ff4326f8b42dcf8851877f4f3989c7fecb8f97d8154686d7d74b7281b70e6b9b",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-22-anatomical-human-skeleton/design.md",
      "sha256": "622709e838b9c126c3da7256fa403e6d56feb6af362faaf29faafe8be33a900a",
      "size_bytes": 83161
    },
    {
      "path": "openspec/changes/archive/2026-10-22-anatomical-human-skeleton/proposal.md",
      "sha256": "cccd77099825e64a6b9790413a8656d48fe92d3f7041c24db2ec0c4f99d2d8fb",
      "size_bytes": 9769
    },
    {
      "path": "openspec/changes/archive/2026-10-22-anatomical-human-skeleton/specs/anatomical-skeleton/spec.md",
      "sha256": "7d5b282a2998ddbb727a8ce4b40c27e7450d786fc3f230a2d91884d9e65e211d",
      "size_bytes": 18861
    },
    {
      "path": "openspec/changes/archive/2026-10-22-anatomical-human-skeleton/specs/joint-mobility/spec.md",
      "sha256": "ce25e4f91df7de2c1b8a3d9e3148c9eebe84ebbb63195aeb887a1dd0841a46e9",
      "size_bytes": 24712
    },
    {
      "path": "openspec/changes/archive/2026-10-22-flat-build-workflow/.openspec.yaml",
      "sha256": "0ad492a63d87e00a8bc135b0a1a2b19270dbb9ffd997a69b89fd4ab72015a944",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-22-flat-build-workflow/design.md",
      "sha256": "16e810f386c812ea47e7b2fca3e36ea01001b1151999962b676889f771ca1955",
      "size_bytes": 9962
    },
    {
      "path": "openspec/changes/archive/2026-10-22-flat-build-workflow/proposal.md",
      "sha256": "72aa47f81217beb0ce28e6745f22c9d8d698888749f494d2f8ee37bdd71eaf87",
      "size_bytes": 2359
    },
    {
      "path": "openspec/changes/archive/2026-10-22-flat-build-workflow/specs/anatomical-skeleton/spec.md",
      "sha256": "91204147c32167084ae0e9c3f4dbe718c8427c2642366881fed64e17bb2385fe",
      "size_bytes": 2435
    },
    {
      "path": "openspec/changes/archive/2026-10-22-flat-build-workflow/specs/build-artifact-lifecycle/spec.md",
      "sha256": "557097f5d24edec8c8c19622e14c0f21037bca165924eb5f5380c9f16c9d0011",
      "size_bytes": 6331
    },
    {
      "path": "openspec/changes/archive/2026-10-22-flat-build-workflow/specs/joint-mobility/spec.md",
      "sha256": "7c7e0d80fd288fb4e1db7f46b11986e583030fab819afbccde090200095aa5f9",
      "size_bytes": 2441
    },
    {
      "path": "openspec/changes/archive/2026-10-22-harden-backend-process-execution/.openspec.yaml",
      "sha256": "0ad492a63d87e00a8bc135b0a1a2b19270dbb9ffd997a69b89fd4ab72015a944",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-22-harden-backend-process-execution/design.md",
      "sha256": "5428bd128c0184f11c4c0c63b617869bb7311b03367385e5e3e9890e8c1e791c",
      "size_bytes": 22303
    },
    {
      "path": "openspec/changes/archive/2026-10-22-harden-backend-process-execution/dev-handoff.md",
      "sha256": "df27fa1d624d376fc482b9412262dea878ec9626829e5bfed871434ac6705b64",
      "size_bytes": 17051
    },
    {
      "path": "openspec/changes/archive/2026-10-22-harden-backend-process-execution/operator-decisions.md",
      "sha256": "d569ac616c3d1766d507b9f5809b3345613112d0d73f03fe06da95ad15d4e5b4",
      "size_bytes": 10298
    },
    {
      "path": "openspec/changes/archive/2026-10-22-harden-backend-process-execution/proposal.md",
      "sha256": "cc0ae953e1d1fde1da126003aa8405a6e2e4ae0fc5d71ffc67807ace30241ff2",
      "size_bytes": 2949
    },
    {
      "path": "openspec/changes/archive/2026-10-22-harden-backend-process-execution/runner-tests-handoff.md",
      "sha256": "f3049aab4eef9543e5040e3649fb4dc37b3901df695bdfa3e80ed87027ef9933",
      "size_bytes": 1672
    },
    {
      "path": "openspec/changes/archive/2026-10-22-harden-backend-process-execution/specs/backend-execution/spec.md",
      "sha256": "0b803fd1ac482cb695cf7605050cc81a99ea56f14d989d45f6609af8e14bc369",
      "size_bytes": 10423
    },
    {
      "path": "openspec/changes/archive/2026-10-22-project-instructions-alignment/design.md",
      "sha256": "aaedddb000b5c4bae92702ad16e01c94e243f2650e459229fad8d8fb77202c6f",
      "size_bytes": 5609
    },
    {
      "path": "openspec/changes/archive/2026-10-22-project-instructions-alignment/proposal.md",
      "sha256": "6d9692baab8e4c0ad0bba6a9ee248970cb2ce4a45e62a2e0603010c2a8dc4db8",
      "size_bytes": 2497
    },
    {
      "path": "openspec/changes/archive/2026-10-22-project-instructions-alignment/specs/project-governance/spec.md",
      "sha256": "06558fae04f773e11c9b2dff8ba6d63ae1a4ff0a6bfc70f68bfd84a05f206065",
      "size_bytes": 7570
    },
    {
      "path": "openspec/changes/archive/2026-10-23-upgrade-host-python-314/.openspec.yaml",
      "sha256": "54c2a6955b514abf783374521da3b6364c1d6b221970ad9faa7124a7e1124528",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-23-upgrade-host-python-314/ci-handoff.md",
      "sha256": "7e2108b02b06024d4ef6ccc186d319dd4f9f657542e584de081626c02038e531",
      "size_bytes": 6212
    },
    {
      "path": "openspec/changes/archive/2026-10-23-upgrade-host-python-314/design.md",
      "sha256": "694aa08afbb4e5adf411f5ebe6639d7fe3c62f12d994bbf9b5a9338af995a1bc",
      "size_bytes": 18700
    },
    {
      "path": "openspec/changes/archive/2026-10-23-upgrade-host-python-314/developer-handoff.md",
      "sha256": "23e2b18f6c363cbd9b4ceac26ea1408eeda1fd7b7f1cde7354dc233acad88a0d",
      "size_bytes": 8833
    },
    {
      "path": "openspec/changes/archive/2026-10-23-upgrade-host-python-314/proposal.md",
      "sha256": "3418c77d1829d8666f6acf43502c7e57411bddc0dc855af98bd1b025a7146b2a",
      "size_bytes": 2551
    },
    {
      "path": "openspec/changes/archive/2026-10-23-upgrade-host-python-314/specs/host-python-runtime/spec.md",
      "sha256": "672690cc94bb2f1338409a6e4faafc6389eeebc833cca5547e017d19502ca4b9",
      "size_bytes": 6955
    },
    {
      "path": "openspec/changes/archive/2026-10-24-package-humanmotionlib/.openspec.yaml",
      "sha256": "54c2a6955b514abf783374521da3b6364c1d6b221970ad9faa7124a7e1124528",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-24-package-humanmotionlib/design.md",
      "sha256": "a501c3f9882c49cdd20d0688d973759bb25fc3d7fb44b1a2856aa49498f3518d",
      "size_bytes": 23367
    },
    {
      "path": "openspec/changes/archive/2026-10-24-package-humanmotionlib/developer-handoff.md",
      "sha256": "5f9bd6a2f7669faf7c5a3038e7416012a77cd9fdad12055d5e481c1cfef3acdf",
      "size_bytes": 11830
    },
    {
      "path": "openspec/changes/archive/2026-10-24-package-humanmotionlib/proposal.md",
      "sha256": "57823a1352f303d0fc2666f96d8baa85585028dae6e4d440202a4407fcf74d3d",
      "size_bytes": 3038
    },
    {
      "path": "openspec/changes/archive/2026-10-24-package-humanmotionlib/specs/backend-execution/spec.md",
      "sha256": "f8485e7028f83ccbf79264d84c5144035efd92edeb486f9a222c8d97e168e0b0",
      "size_bytes": 6979
    },
    {
      "path": "openspec/changes/archive/2026-10-24-package-humanmotionlib/specs/build-artifact-lifecycle/spec.md",
      "sha256": "64220a5ccafb27669c144c3fa9b87add71e007878c12669fb7562878f74adfd6",
      "size_bytes": 2372
    },
    {
      "path": "openspec/changes/archive/2026-10-24-package-humanmotionlib/specs/host-python-runtime/spec.md",
      "sha256": "2ca175f69796c83ccb7e9e6eff905a981403d92994ccd397621a8f492c78c233",
      "size_bytes": 2071
    },
    {
      "path": "openspec/changes/archive/2026-10-24-package-humanmotionlib/specs/python-distribution/spec.md",
      "sha256": "bc9ecc1dd1e1fe562c59cdaa319d05113ff257e4d71f820d72aabd79ddc05ee5",
      "size_bytes": 11311
    },
    {
      "path": "openspec/changes/archive/2026-10-24-portable-installed-runtime/.openspec.yaml",
      "sha256": "e2ebaebee255ccc1e09b64ba38d9b09c360a7392fc110a48ca2525e1ea49fa46",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-24-portable-installed-runtime/design.md",
      "sha256": "76806f19f7c852890aa9346fb08b0467b38acc4387be15f9cfa719d82d8abb18",
      "size_bytes": 25150
    },
    {
      "path": "openspec/changes/archive/2026-10-24-portable-installed-runtime/implementation.md",
      "sha256": "9371d9f6667cf117c67c9375d5386dd6f0a36fa274e28d96d823fb7546302ae5",
      "size_bytes": 17120
    },
    {
      "path": "openspec/changes/archive/2026-10-24-portable-installed-runtime/proposal.md",
      "sha256": "7078d7258b630f8cac90aaf2967d5e4028aec563515ed6f2d4844c0acab571c4",
      "size_bytes": 2634
    },
    {
      "path": "openspec/changes/archive/2026-10-24-portable-installed-runtime/specs/backend-execution/spec.md",
      "sha256": "eae2f4e5bf8e07ca74cdcbc71d5a2c7da92c8d55389de12a56fa38214ab6d89a",
      "size_bytes": 9158
    },
    {
      "path": "openspec/changes/archive/2026-10-24-portable-installed-runtime/specs/build-artifact-lifecycle/spec.md",
      "sha256": "c21b27f9049482c94efa87e6bc79514ccf26721070facced5ee4334ff626532f",
      "size_bytes": 3995
    },
    {
      "path": "openspec/changes/archive/2026-10-24-portable-installed-runtime/specs/python-distribution/spec.md",
      "sha256": "9269372b37a7b17e82cfb3f2c41750d3eb742f7671e0ca2c139a0e3526c4a702",
      "size_bytes": 9431
    },
    {
      "path": "openspec/changes/archive/2026-10-24-public-python-generation-api/.openspec.yaml",
      "sha256": "e2ebaebee255ccc1e09b64ba38d9b09c360a7392fc110a48ca2525e1ea49fa46",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-24-public-python-generation-api/design.md",
      "sha256": "7fd2c61a11abe1f75af9913d14c38739d5a9926fce81d8edd058a1d5f5390232",
      "size_bytes": 18955
    },
    {
      "path": "openspec/changes/archive/2026-10-24-public-python-generation-api/developer-handoff.md",
      "sha256": "2f89c5bb207391f1cd246c80940ac50d16f08da7dfc6350b4b41af635d3d870d",
      "size_bytes": 8298
    },
    {
      "path": "openspec/changes/archive/2026-10-24-public-python-generation-api/proposal.md",
      "sha256": "ecd271cd5b230b55d8e7708fac70614ce48fafced1f00826b030b51ff313e9a5",
      "size_bytes": 2373
    },
    {
      "path": "openspec/changes/archive/2026-10-24-public-python-generation-api/specs/public-generation-api/spec.md",
      "sha256": "f5e6c22200b4f68d7c50791e3106797dec768a7429fd70613b2856fd6e3d4476",
      "size_bytes": 14631
    },
    {
      "path": "openspec/changes/archive/2026-10-25-support-consumer-authored-motions/.openspec.yaml",
      "sha256": "d002983090acfe222597827aa3c481b59d3a566c704a6e91e0d50bb1d209297d",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-25-support-consumer-authored-motions/design.md",
      "sha256": "449f5789ad33537c37b9855215f77a6ea3e2a3fe035aedb152cb11d67646f44d",
      "size_bytes": 31935
    },
    {
      "path": "openspec/changes/archive/2026-10-25-support-consumer-authored-motions/developer-handoff.md",
      "sha256": "dbd03e26fb428020b339e86ed94332b0ad5a20b07d319bba82c3a16ce6ca000f",
      "size_bytes": 18181
    },
    {
      "path": "openspec/changes/archive/2026-10-25-support-consumer-authored-motions/proposal.md",
      "sha256": "a2ee60bcc4eb3ac6beff384be44d4bba5f4eb0ef3c0d51067c63f305459d3ba0",
      "size_bytes": 2847
    },
    {
      "path": "openspec/changes/archive/2026-10-25-support-consumer-authored-motions/specs/consumer-motion-sources/spec.md",
      "sha256": "308013bcd03c98000869d6ddcd7f6a9b55d2ed5d8c27da1f6150b42b8dd036af",
      "size_bytes": 13222
    },
    {
      "path": "openspec/changes/archive/2026-10-25-support-consumer-authored-motions/specs/public-generation-api/spec.md",
      "sha256": "4d0a80d7b75e3d2ea4863d61df147371cc3703ea659ea7eca88adf18a9fdc2a5",
      "size_bytes": 8351
    },
    {
      "path": "openspec/changes/archive/2026-10-25-versioned-releases/.openspec.yaml",
      "sha256": "e2ebaebee255ccc1e09b64ba38d9b09c360a7392fc110a48ca2525e1ea49fa46",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-25-versioned-releases/design.md",
      "sha256": "ac444427fa114135724ab362ca95713f03b7c3d500deece5409ab2d9b51ece65",
      "size_bytes": 7311
    },
    {
      "path": "openspec/changes/archive/2026-10-25-versioned-releases/developer-handoff.md",
      "sha256": "8d15ad35e66f39b4878fddca10f4c2edc8646d3d634bacdc9fa63241d97c17e2",
      "size_bytes": 8489
    },
    {
      "path": "openspec/changes/archive/2026-10-25-versioned-releases/proposal.md",
      "sha256": "3e187c6fb5152f375d6a556c2541ef0e9d8f43d8b2f8e65b75c932edc55b7576",
      "size_bytes": 2469
    },
    {
      "path": "openspec/changes/archive/2026-10-25-versioned-releases/specs/python-distribution/spec.md",
      "sha256": "66fbd3f671d850b506758d00886e68db20af51cf31e647a0ed5e1d7f7be82979",
      "size_bytes": 1923
    },
    {
      "path": "openspec/changes/archive/2026-10-25-versioned-releases/specs/release-publication/spec.md",
      "sha256": "40865e1690f96f86a7cc67c675c7ed8258127a11bb2d7abd38abe4cea1593c83",
      "size_bytes": 9325
    },
    {
      "path": "openspec/changes/archive/2026-10-28-add-early-visual-gate/.openspec.yaml",
      "sha256": "9e0a467e3934b14a2d9c9175305310e9359d34e2484a458af3d182c2956b9e2d",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-28-add-early-visual-gate/approvals.md",
      "sha256": "a83ac37bb7c7673784a961fff25dd002b777924e6fcb38670c6a62997f221d4b",
      "size_bytes": 388
    },
    {
      "path": "openspec/changes/archive/2026-10-28-add-early-visual-gate/design.md",
      "sha256": "572950efff37e915861b7cc29e20bf85ecd7108e2b15e65cf0cbd142a835a3c0",
      "size_bytes": 10627
    },
    {
      "path": "openspec/changes/archive/2026-10-28-add-early-visual-gate/developer-handoff.md",
      "sha256": "b868772149c2463ae114c3d84d580fbe9182effbde56557f1b5cd6a03cd30506",
      "size_bytes": 5959
    },
    {
      "path": "openspec/changes/archive/2026-10-28-add-early-visual-gate/proposal.md",
      "sha256": "bcd91ba3c2bc2f9eb6fad5fe3ef94d62e22a389564570a2134194ed8aaa5e5a3",
      "size_bytes": 1788
    },
    {
      "path": "openspec/changes/archive/2026-10-28-add-early-visual-gate/specs/project-governance/spec.md",
      "sha256": "eb80166d9e8fd78bd3dd4575e9bf99d79dd85c0ebd03086bee9146215b930acd",
      "size_bytes": 6999
    },
    {
      "path": "openspec/changes/archive/2026-10-31-automate-build-and-verification-matrix/.openspec.yaml",
      "sha256": "9e0a467e3934b14a2d9c9175305310e9359d34e2484a458af3d182c2956b9e2d",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/archive/2026-10-31-automate-build-and-verification-matrix/design.md",
      "sha256": "c73697ee18bf728371c2cde1c8b7ed3c14783c2d34656377096963415f384074",
      "size_bytes": 9599
    },
    {
      "path": "openspec/changes/archive/2026-10-31-automate-build-and-verification-matrix/proposal.md",
      "sha256": "d62690e2db9904870dae51796f48c71a911684a091f319accd666386fa648555",
      "size_bytes": 3293
    },
    {
      "path": "openspec/changes/archive/2026-10-31-automate-build-and-verification-matrix/reviewer-authority-proposal.md",
      "sha256": "ff275208ac8f92c92232f86f33971deb57443f21f13f6e0f389513b9ce55094f",
      "size_bytes": 8993
    },
    {
      "path": "openspec/changes/archive/2026-10-31-automate-build-and-verification-matrix/reviewer-inventory.md",
      "sha256": "cc4a0676fb3c607059f87d46962f444811abe751fca09214d3396a6f03f6534a",
      "size_bytes": 7517
    },
    {
      "path": "openspec/changes/archive/2026-10-31-automate-build-and-verification-matrix/specs/build-artifact-lifecycle/spec.md",
      "sha256": "d3f7b61f781951b7d6e3879ce1a71b5de08569cb4229e090af49650f88b371e3",
      "size_bytes": 10612
    },
    {
      "path": "openspec/changes/archive/2026-10-31-automate-build-and-verification-matrix/specs/build-verification-matrix/spec.md",
      "sha256": "dade61e054f286d2c29238e97b133b42da9c2e34c76d2a3ce3c5fbed03d2563a",
      "size_bytes": 8044
    },
    {
      "path": "openspec/changes/archive/2026-10-31-automate-build-and-verification-matrix/specs/public-generation-api/spec.md",
      "sha256": "564778d9d3ed6e79314a0e19cd4060a24c1a18238d167ef9f6b5bb31f2398774",
      "size_bytes": 2386
    },
    {
      "path": "openspec/changes/audit-project-tools/.openspec.yaml",
      "sha256": "c6ab3a95d8d0fd469ca8750ef79234025bf4a8356d5d57856e97d7e47fc8b6c2",
      "size_bytes": 40
    },
    {
      "path": "openspec/changes/audit-project-tools/design.md",
      "sha256": "778d06518942201b509fd715c7f4777c54ea6154941212288db47c7a6a92fc02",
      "size_bytes": 23353
    },
    {
      "path": "openspec/changes/audit-project-tools/proposal.md",
      "sha256": "a65f725c748d26c2619a8a352d2e4f604dc678ae4c05c57e071586c6f186f71a",
      "size_bytes": 3952
    },
    {
      "path": "openspec/changes/audit-project-tools/reviewer-retry-permissions.patch",
      "sha256": "bbbce8df552ccfeb58cfcba9c17c2338d04e9631ca95cf62f703660243709b99",
      "size_bytes": 3007
    },
    {
      "path": "openspec/changes/audit-project-tools/reviewer-workspace-permissions.patch",
      "sha256": "9a7ad332d7c649953abd990fe60e80d4b68eabdded471263df4e949db6e81cf5",
      "size_bytes": 2160
    },
    {
      "path": "openspec/changes/audit-project-tools/specs/build-artifact-lifecycle/spec.md",
      "sha256": "475a71c5766cb84f6f36a175446843e6f4a1609bf0c9858ed3a0595af7bbf80b",
      "size_bytes": 17986
    },
    {
      "path": "openspec/changes/audit-project-tools/specs/build-verification-matrix/spec.md",
      "sha256": "5ce19407238eb4577f681eb3c4a4fad1431a1d23338f870e7f82026fac3ee2a0",
      "size_bytes": 11908
    },
    {
      "path": "openspec/changes/audit-project-tools/specs/host-python-runtime/spec.md",
      "sha256": "55600642554823b22ab77e457460a787433de9cf77310c407870bb83d7cd8e7f",
      "size_bytes": 5409
    },
    {
      "path": "openspec/changes/audit-project-tools/specs/project-governance/spec.md",
      "sha256": "2251ec226de45366915e2829e3da6dd977ff5fcfb4454c2f9beaadf214c20aae",
      "size_bytes": 7074
    },
    {
      "path": "openspec/changes/audit-project-tools/specs/python-distribution/spec.md",
      "sha256": "e98234d04bbfc1064a36b08e7f5a4d2a7a29057440c887d951ea04a757274bf5",
      "size_bytes": 3442
    },
    {
      "path": "openspec/changes/audit-project-tools/tooling-audit.md",
      "sha256": "9338bf5afc32e9f011694a5933e3cb84e00ac7ef5cc6aefd46aa04f49c85730e",
      "size_bytes": 8289
    },
    {
      "path": "openspec/config.yaml",
      "sha256": "f0082e9c22e8ce1d611c0f3b4d4915ce445e7ff2553cda6b713b6c25f390984c",
      "size_bytes": 998
    },
    {
      "path": "openspec/specs/.gitkeep",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "size_bytes": 0
    },
    {
      "path": "openspec/specs/anatomical-skeleton/spec.md",
      "sha256": "1d7b6d685cf033540d79c6f695671ad7714ab68a012279cf0fcdab5ec523cbe2",
      "size_bytes": 19522
    },
    {
      "path": "openspec/specs/backend-execution/spec.md",
      "sha256": "289dd12463f4940afeedcf95271b6e7a9688d2d8499282d5a55ff1dc05b34449",
      "size_bytes": 14965
    },
    {
      "path": "openspec/specs/build-artifact-lifecycle/spec.md",
      "sha256": "9a5678145daf9bfcc8cb04ceb2037efabff4f8150f74c2df4332af9bede71bfa",
      "size_bytes": 10786
    },
    {
      "path": "openspec/specs/build-verification-matrix/spec.md",
      "sha256": "34f4d2b6090d47fe1f632d879c5942c509183d7e3647559bb439c1fca7e43434",
      "size_bytes": 8062
    },
    {
      "path": "openspec/specs/consumer-motion-sources/spec.md",
      "sha256": "fec5bd1d92de1dc601c6d38294a17d60019fa1ae4dc77669ab44499854fe483b",
      "size_bytes": 13243
    },
    {
      "path": "openspec/specs/host-python-runtime/spec.md",
      "sha256": "11c6bb95f215348b4e542d59a0480d40835b4720a8f72cfb95ca67d347ea3cc0",
      "size_bytes": 7917
    },
    {
      "path": "openspec/specs/joint-mobility/spec.md",
      "sha256": "c5f2c1f3c95dcfe6eba7117a59022ddc853d68e84b764a8c7ffa608613115c6e",
      "size_bytes": 25225
    },
    {
      "path": "openspec/specs/project-governance/spec.md",
      "sha256": "95dd60c14deedd85c77941a4faad37d4742e8065932d96bfd8bb631e78d0a2d7",
      "size_bytes": 13345
    },
    {
      "path": "openspec/specs/public-generation-api/spec.md",
      "sha256": "4e560cf53205cec31e55a649ee3e7688436e34e1ac274f258f9010ba0c291b78",
      "size_bytes": 18031
    },
    {
      "path": "openspec/specs/python-distribution/spec.md",
      "sha256": "11717d79c5616ac95ab4d58593dec05e941e8c45b33cdc8f867aad8582ee1e1d",
      "size_bytes": 15769
    },
    {
      "path": "openspec/specs/release-publication/spec.md",
      "sha256": "05effb983aab2f84fbb119f094a640ce8615e026eebca53b8d7d2c8402403d5b",
      "size_bytes": 9342
    },
    {
      "path": "pyproject.toml",
      "sha256": "0795170881715598b9fd59e7a89be7f884f43de7599e37cf58823a8456069800",
      "size_bytes": 1055
    },
    {
      "path": "rig/README.md",
      "sha256": "6b286cc7c7f75ee2f507fcacb0bc71c3b407f6631713b9aa70a3a049224f36f6",
      "size_bytes": 5120
    },
    {
      "path": "rig/body-groups.yaml",
      "sha256": "9bf0c47fcf8064d3e36b7d826bb5cb514b1570952d7990f51ae6179b2a945056",
      "size_bytes": 7711
    },
    {
      "path": "rig/diagnostics/arm-raise.yaml",
      "sha256": "960ffd672d1de4ee238cb47b38d007ddb0c0f4fc0a7d61c1859e1c750b8f68d9",
      "size_bytes": 1921
    },
    {
      "path": "rig/diagnostics/forefoot-rocker.yaml",
      "sha256": "7143a4ad7b9a0c88e0e116753b59ca2ef6a32409211fbd59d4e52a16bc2fed71",
      "size_bytes": 2128
    },
    {
      "path": "rig/diagnostics/neutral.yaml",
      "sha256": "a074d838828b89725d59d16162034806a19bcfae7eed453d105a056200e5d3df",
      "size_bytes": 1554
    },
    {
      "path": "rig/diagnostics/rest.yaml",
      "sha256": "ee4896046c49d8034b78377bdda2ef84ebd135f34b9184a81140b1fe219eb9d4",
      "size_bytes": 1532
    },
    {
      "path": "rig/diagnostics/squat.yaml",
      "sha256": "7e736f1011ea74e6516b1354681053fab31f1cd2b5877878ea03fb01dcd8784e",
      "size_bytes": 3496
    },
    {
      "path": "rig/diagnostics/sweep-ankle-bilateral-dorsiflexion.yaml",
      "sha256": "2bd0b7c6c016e26223d30cfd02ca676487010f7306746f4a583b4684ed7127a8",
      "size_bytes": 1433
    },
    {
      "path": "rig/diagnostics/sweep-cervical-flexion.yaml",
      "sha256": "517446ca8c4e76cd7449ffdb84691f5183e8ace01e28c0ac2603813f15220cbb",
      "size_bytes": 1236
    },
    {
      "path": "rig/diagnostics/sweep-cervical-lateral_flexion.yaml",
      "sha256": "e55c9dd82a9b3591c24e151b701a21a5c57344aeaccdc73ed676036b4444ac7a",
      "size_bytes": 1260
    },
    {
      "path": "rig/diagnostics/sweep-cervical-rotation.yaml",
      "sha256": "6fef0dd66a705d8d463d5b8864c3de6f4ee590f83b321c9defe653c5ebda0649",
      "size_bytes": 1239
    },
    {
      "path": "rig/diagnostics/sweep-elbow-bilateral-flexion.yaml",
      "sha256": "1ae1b7e75332fb3b852c3bd72175853069d42be9a8932cd627e8f7dfe7be19ed",
      "size_bytes": 1411
    },
    {
      "path": "rig/diagnostics/sweep-forearm-bilateral-pronation.yaml",
      "sha256": "734947613b3293d37aa07264a8885a626dc974d16d7108577a28603b04bddced",
      "size_bytes": 1437
    },
    {
      "path": "rig/diagnostics/sweep-hindfoot-bilateral-inversion.yaml",
      "sha256": "c7e929604d452452af3af1122ced2d5bb6650ff9117580e03e67edc4ef20af2a",
      "size_bytes": 1433
    },
    {
      "path": "rig/diagnostics/sweep-hip-bilateral-adduction.yaml",
      "sha256": "41b5c361a1b2687f124e038a35230fe34606c36f44442310de8ab32881d41a2a",
      "size_bytes": 1413
    },
    {
      "path": "rig/diagnostics/sweep-hip-bilateral-external_rotation.yaml",
      "sha256": "9352fa9e58891fee3e0058dce088b37557b14b7fe93353e9a6e3065ff4c252cb",
      "size_bytes": 1445
    },
    {
      "path": "rig/diagnostics/sweep-hip-bilateral-flexion.yaml",
      "sha256": "7ba3fcc71072a3a7052d5e51b378f49ff97d7878024754d2f7c795c48e0f50fe",
      "size_bytes": 1407
    },
    {
      "path": "rig/diagnostics/sweep-knee-bilateral-flexion.yaml",
      "sha256": "7a8823aa482621534e3babd86c9bcd608098c6ef3e903c417389fef659aa4af4",
      "size_bytes": 1407
    },
    {
      "path": "rig/diagnostics/sweep-lumbar-flexion.yaml",
      "sha256": "a8000f18ac5968bd2de4ddfde3c19c83e4615c4b34fad03213f57dd9dce6990b",
      "size_bytes": 1226
    },
    {
      "path": "rig/diagnostics/sweep-lumbar-lateral_flexion.yaml",
      "sha256": "5228afe5909840fe68eaff90eb80b348949b0504cc3d345219e15d46e33e85b8",
      "size_bytes": 1250
    },
    {
      "path": "rig/diagnostics/sweep-lumbar-rotation.yaml",
      "sha256": "4321a0ff258722e15037258cff5606d588e5d087b82445eb1a23c9959cbe3338",
      "size_bytes": 1229
    },
    {
      "path": "rig/diagnostics/sweep-mtp-bilateral-extension.yaml",
      "sha256": "4590f8f428640e6d6d2ebdfb824d5bee72b509afcf26a3eb21514aabecdb1fca",
      "size_bytes": 1413
    },
    {
      "path": "rig/diagnostics/sweep-pelvis-lateral_tilt.yaml",
      "sha256": "abcd3a1414837fb04395fca467db56eb243f2d81777a4714c4c5e506a1a86eb3",
      "size_bytes": 1242
    },
    {
      "path": "rig/diagnostics/sweep-pelvis-pitch.yaml",
      "sha256": "70c13c92600fd2fccca0b63d03e8e456c2eeeb432f09662e491d220e36b7c426",
      "size_bytes": 1221
    },
    {
      "path": "rig/diagnostics/sweep-pelvis-yaw.yaml",
      "sha256": "4ee6b9279d5d2c9fb59712d579fa282a7803377355b0c2b5f83208144e4370ba",
      "size_bytes": 1215
    },
    {
      "path": "rig/diagnostics/sweep-shoulder-bilateral-elevation.yaml",
      "sha256": "20d15b66d61cb6bd78d30439dc4676d4428205036d97ffeaa38a72a85310c1ff",
      "size_bytes": 1431
    },
    {
      "path": "rig/diagnostics/sweep-shoulder-bilateral-external_twist.yaml",
      "sha256": "5791602483c3dfd911af0d07094d25601e848d33b1c694b3a83c8446ec1d5e56",
      "size_bytes": 1453
    },
    {
      "path": "rig/diagnostics/sweep-shoulder-bilateral-plane.yaml",
      "sha256": "5f216fbe240f5d7f92e58751bfbf116ccb757a089ad93ab9260cacfb8b396b6f",
      "size_bytes": 1958
    },
    {
      "path": "rig/diagnostics/sweep-thoracic-flexion.yaml",
      "sha256": "1f799e2d4516876b6c676ee88eb9b1585a9d979ded7eb3b4767f31c72e760cae",
      "size_bytes": 1232
    },
    {
      "path": "rig/diagnostics/sweep-thoracic-lateral_flexion.yaml",
      "sha256": "1d99cf8b57c0cc874ef4dc88a05e41d523c6c58178d90ce237095e9bb9ac9c9b",
      "size_bytes": 1256
    },
    {
      "path": "rig/diagnostics/sweep-thoracic-rotation.yaml",
      "sha256": "5959ffdb10c27e41740dec770d833c9ee5ba889170dd81b061400adae5b09d41",
      "size_bytes": 1235
    },
    {
      "path": "rig/diagnostics/sweep-wrist-bilateral-flexion.yaml",
      "sha256": "869ef6af54654927ecc48101ba569256a22a8766090d34985dc4c5ae36f506bc",
      "size_bytes": 1413
    },
    {
      "path": "rig/diagnostics/sweep-wrist-bilateral-ulnar_deviation.yaml",
      "sha256": "659dc258e1b962c307d2a4d028871dc30df3a8df04cca40979b8c839efa20cf2",
      "size_bytes": 1445
    },
    {
      "path": "rig/diagnostics/walking-in-place.yaml",
      "sha256": "7648d551c47422ca780817a753ce83003b3469d5fbdcc7ff74118a924a937a00",
      "size_bytes": 2384
    },
    {
      "path": "rig/humanoid-map.yaml",
      "sha256": "b973ea08b4daab35d2f022c05db51d6e57ab08edf36108cfa3f37e87801729f2",
      "size_bytes": 9662
    },
    {
      "path": "rig/mobility/adult-reference-v1.yaml",
      "sha256": "9d3316fd6ed72a645ceb4a0e88bb748ee07b58c19bfa7def8a8d18bdee6108cc",
      "size_bytes": 81898
    },
    {
      "path": "rig/profiles/adult-reference-v1.yaml",
      "sha256": "e93d232f8b2f64a06f8a8064b6fe0dcdcbd0afc3050f27faa67799906fd94e41",
      "size_bytes": 645437
    },
    {
      "path": "scenes/skeleton-review.yaml",
      "sha256": "69a3060ebfc75951563f2c811b7224b5004303fd038953ac8fb1cbc79b1e6a9e",
      "size_bytes": 1863
    },
    {
      "path": "schema/README.md",
      "sha256": "d3097d222b4a7ab7f92a1c28a0afe6a77b687162764e33ee5d844245f4dcf73e",
      "size_bytes": 5438
    },
    {
      "path": "schema/body-groups.schema.json",
      "sha256": "f6358ef3f2a0b6ec410e21885fcbd3b6e4cc98b6a3664c85ab604b2e34e3aecb",
      "size_bytes": 1552
    },
    {
      "path": "schema/character-appearance.schema.json",
      "sha256": "80f38bf36e817c8259ef8a677943360c35cdb4a37ed6471c317b3ac96f475604",
      "size_bytes": 3078
    },
    {
      "path": "schema/character-definition.schema.json",
      "sha256": "0bcd91cb93a751e394c805c76dcd026e3baacb4642c3b6b0489123b8a0fd8892",
      "size_bytes": 2208
    },
    {
      "path": "schema/character-registry.schema.json",
      "sha256": "97e295e91223646eddd3e30b568afee150223c68bc4074d3327cac2c75b84577",
      "size_bytes": 1751
    },
    {
      "path": "schema/character-template.schema.json",
      "sha256": "613cdfd4317932f23b533dec9c6712f18b9696d4b98ed9c2240f562489b4edea",
      "size_bytes": 27372
    },
    {
      "path": "schema/common.schema.json",
      "sha256": "964a9b1f158d49bb50023061f7d12455534eac122be36af92e18c9146ca48a48",
      "size_bytes": 3959
    },
    {
      "path": "schema/consumer-motion-snapshot.schema.json",
      "sha256": "b1d0493bfc50c2bdc1ede0ea092b1e850d50e59d74018bef2b651b4e6c0386db",
      "size_bytes": 2024
    },
    {
      "path": "schema/consumer-motion.schema.json",
      "sha256": "b3cf6a3663a754a40513beed747fe30d60be88254180bc543e12b20a69a3e4f2",
      "size_bytes": 5272
    },
    {
      "path": "schema/diagnostic.schema.json",
      "sha256": "13eac9ccf9cfd1422bf72aa7bd58a5a59929327edb21fd47649a6b7f8053fe52",
      "size_bytes": 9985
    },
    {
      "path": "schema/humanoid-map.schema.json",
      "sha256": "57ca8e6849689a08a4f86f5adbe56f1b0b8816ae4fecc2021ae85a6715ac054c",
      "size_bytes": 2579
    },
    {
      "path": "schema/mobility.schema.json",
      "sha256": "a0e842c216ebdbeff485979e6cf37e983e5277bf728ad617d88b109b2ba996be",
      "size_bytes": 26132
    },
    {
      "path": "schema/profile.schema.json",
      "sha256": "65c27eb924b635db055b6a83fc2a9dc8a30acb7ebf043b29c21374b2bb487104",
      "size_bytes": 21477
    },
    {
      "path": "schema/review-scene.schema.json",
      "sha256": "0985a5e486816bc8e5211b2f43ac9207ffda29a7ecb62195fe6d24c91a992ff4",
      "size_bytes": 5334
    },
    {
      "path": "src/humanmotionlib/__init__.py",
      "sha256": "05d9ef5d14140d291b7892decba7383961eafdf9d8c9d11b937452ae8f73f7cd",
      "size_bytes": 217
    },
    {
      "path": "src/humanmotionlib/__main__.py",
      "sha256": "1f77725f6172d53f109ae9023a9f85c5bc1b0afd96f9a3cbb45f252a59237e4d",
      "size_bytes": 100
    },
    {
      "path": "src/humanmotionlib/actions.py",
      "sha256": "76c283516c7830276fcda8db2b06cd4736376f38c748f2a8c2748db92e71a2eb",
      "size_bytes": 6375
    },
    {
      "path": "src/humanmotionlib/api.py",
      "sha256": "5da55121155628d84521c515df6b1dcf3c6fa3ff9d58a13cd455b3bc035144a0",
      "size_bytes": 47289
    },
    {
      "path": "src/humanmotionlib/articulation.py",
      "sha256": "ac9dac52b4d32fa5dc68c465672bbcaa37d7962cfd748f5dce04cb5d079c993f",
      "size_bytes": 4149
    },
    {
      "path": "src/humanmotionlib/backend_measurements.py",
      "sha256": "24c86df6937c8815b99bfa2ff5e8dba6cc94dbf4743b26af9bb4a52c99896987",
      "size_bytes": 10675
    },
    {
      "path": "src/humanmotionlib/balance.py",
      "sha256": "d52e7e2d39783f1ac90171092f7cf6da17a2a7fbda6a5946a01fd86992e4a579",
      "size_bytes": 8976
    },
    {
      "path": "src/humanmotionlib/balance_review.py",
      "sha256": "926ae4f43b6639676a8684049cdf6b0d991b1cbc9e7f83177c37c4e19fd49f02",
      "size_bytes": 4730
    },
    {
      "path": "src/humanmotionlib/blender_backend.py",
      "sha256": "af969319b497505c9294ddf7b4a48e2e669cb471cdc3afa48087df358312dbc7",
      "size_bytes": 46586
    },
    {
      "path": "src/humanmotionlib/build_skeleton.py",
      "sha256": "5d1ed6db1b79288938f3695af9ec7369a0b6cba1eb12e44c832247ab7f982e4c",
      "size_bytes": 23873
    },
    {
      "path": "src/humanmotionlib/character_midpoints.py",
      "sha256": "fd1ec5c602957cbdf10b54305d541e900a237408189dc74ba00c07f9ed051996",
      "size_bytes": 5561
    },
    {
      "path": "src/humanmotionlib/character_paths.py",
      "sha256": "5dd634405b34d42cdaf22777d3f53c0bf78b3d77cb4855e4a38d030576cf478c",
      "size_bytes": 674
    },
    {
      "path": "src/humanmotionlib/character_skinning.py",
      "sha256": "6fd93d392e53bd9035ede37d4155fe3b1bd9fa58f1ef679eea8c55900073054e",
      "size_bytes": 14652
    },
    {
      "path": "src/humanmotionlib/character_surface.py",
      "sha256": "b4eeaa0fbcfccdb5ab87a6efcc3eeb4650710e20a743fb865ada546f8b1b9df9",
      "size_bytes": 58791
    },
    {
      "path": "src/humanmotionlib/character_verification.py",
      "sha256": "911f513ed5648da7fbf27b63411187706ccee8eccae2b327f7dc727b53a806be",
      "size_bytes": 87525
    },
    {
      "path": "src/humanmotionlib/characters.py",
      "sha256": "7888eb0bfb317c92999bc2a817b542d7c6f6d626842607101d309f16bf3f3b9d",
      "size_bytes": 14491
    },
    {
      "path": "src/humanmotionlib/check_host.py",
      "sha256": "a2f146163be6aef57a5d37353b5483e509c161ec2cd3f0846c39b27819be973a",
      "size_bytes": 30994
    },
    {
      "path": "src/humanmotionlib/cli.py",
      "sha256": "3d7bd445d91f9df65450c0e82a0d91402dbf44fc3eea7b1b1f62251c4bb8aba6",
      "size_bytes": 2390
    },
    {
      "path": "src/humanmotionlib/consumer_motion.py",
      "sha256": "9e825adc9c57ff8a60595e2c6435661273f1f14a22ff91e5ba7c37916412d7b4",
      "size_bytes": 33599
    },
    {
      "path": "src/humanmotionlib/consumer_prepared_validation.py",
      "sha256": "f316283c6ec469d4fc6c4ece6dcd1b6b6fd837b1086b7484353c47e619f935af",
      "size_bytes": 1923
    },
    {
      "path": "src/humanmotionlib/contacts.py",
      "sha256": "ed62f8d251f84fda88c0d7f53457d6e2d46eb4af440dee11b3586e2771181604",
      "size_bytes": 6527
    },
    {
      "path": "src/humanmotionlib/coverage.py",
      "sha256": "1be2c882e13594dc1db8a1675e10d5d9c5ce6469942413161fbf8c5a27e3e6ca",
      "size_bytes": 5202
    },
    {
      "path": "src/humanmotionlib/dense_floor.py",
      "sha256": "48db1587b533739ed746d857e4b69dd9145e27342cbfd7f7d42863127005d913",
      "size_bytes": 5107
    },
    {
      "path": "src/humanmotionlib/dense_verification.py",
      "sha256": "db0531424ecdf641d041706b21e70889ba5373a671a1ca20ebfa23c493edfd70",
      "size_bytes": 11899
    },
    {
      "path": "src/humanmotionlib/diagnostics.py",
      "sha256": "fc27a472abcdae18ca28c44b0463ac8ed5e917992ff2f819424d7f3b45d5beb5",
      "size_bytes": 7995
    },
    {
      "path": "src/humanmotionlib/finite.py",
      "sha256": "5025d1a89810c24c6069f5190620c8a0e7adb81e551c3478d69585d1f20cd0f1",
      "size_bytes": 906
    },
    {
      "path": "src/humanmotionlib/geometry.py",
      "sha256": "e8f676adfacff586799c7861d10b84fe41926bdba4d010e5f1948f330f6e8a96",
      "size_bytes": 5556
    },
    {
      "path": "src/humanmotionlib/guides.py",
      "sha256": "d6c9d8f97967c19ec38247d0fbcae72458def65ac46323cf47b50bbfd497f093",
      "size_bytes": 4687
    },
    {
      "path": "src/humanmotionlib/kinematics.py",
      "sha256": "603e08baee60881af19aac7da8248ed187d3be3f591d2cc907b23666859ac9b4",
      "size_bytes": 7684
    },
    {
      "path": "src/humanmotionlib/math3d.py",
      "sha256": "d8d172905f0d3be1f1372433a564ae8f7626e82c0b48fd602ff3dda3cb7309e4",
      "size_bytes": 4645
    },
    {
      "path": "src/humanmotionlib/measurements.py",
      "sha256": "436def5b9e4057fdd732a275f203fe54bf417b95d355e010aaf58b4fd573e969",
      "size_bytes": 16662
    },
    {
      "path": "src/humanmotionlib/mirror.py",
      "sha256": "d21106b5f26bbdb03f720ac37f2e5c4eb2bd1fc2de3c75b88c9b0d0aa2951198",
      "size_bytes": 3648
    },
    {
      "path": "src/humanmotionlib/package_resources.py",
      "sha256": "77361cd32d35410af94186b91cffa04d0c141f1244997a479d56bc047a66fea1",
      "size_bytes": 5074
    },
    {
      "path": "src/humanmotionlib/poses.py",
      "sha256": "af49add6256d4523ed7e60662a9d6a6cb002cd9464fec848413d5303f2ee025e",
      "size_bytes": 4108
    },
    {
      "path": "src/humanmotionlib/prepare_skeleton.py",
      "sha256": "831cb21092498987cd3b2e0381ad7277c87030ffa1db3c353aaff28f393c7d3e",
      "size_bytes": 6667
    },
    {
      "path": "src/humanmotionlib/prepared.py",
      "sha256": "2e6e39aa67272f45c7cebc66eef165c345dec57cf39651aea46146a3a266d59d",
      "size_bytes": 8843
    },
    {
      "path": "src/humanmotionlib/presentation.py",
      "sha256": "39104fdde05104eb3ef0a3a0d4b3035899c118e46670d26a7df4a2759277fec1",
      "size_bytes": 28560
    },
    {
      "path": "src/humanmotionlib/render_contract.py",
      "sha256": "7b648e0effeaaed191ea19596ba4a5882c51764834d9e7100b4d7741b9cf342d",
      "size_bytes": 13984
    },
    {
      "path": "src/humanmotionlib/review_graphics.py",
      "sha256": "08ca13a0928d8cda4d2a88a2e93a861b714918c50296adf1ee58330c64115c31",
      "size_bytes": 5542
    },
    {
      "path": "src/humanmotionlib/review_pack.py",
      "sha256": "14016d609e8c18abeeed9b3e9e71710aafbf7f33cf298fc246503a9a45de1a1d",
      "size_bytes": 99464
    },
    {
      "path": "src/humanmotionlib/run_blender.py",
      "sha256": "999163ef4e60fdf998df8717bbd5e5418283ba09a7de8d49404b5182178b4164",
      "size_bytes": 21580
    },
    {
      "path": "src/humanmotionlib/runtime.py",
      "sha256": "6d8ac058bdda5d353ccfdf5da080c1a19052962761b722c7a9834cf3aaf8c1c8",
      "size_bytes": 38234
    },
    {
      "path": "src/humanmotionlib/sampling.py",
      "sha256": "135135cea23ccf653d2d6f443bc60d76bb9720ebd322b1f4969c17a6589d1964",
      "size_bytes": 1247
    },
    {
      "path": "src/humanmotionlib/source_validation.py",
      "sha256": "db55de216fc04820313d1c4cd547db34a04dc76b126810b159b4455121b3d51d",
      "size_bytes": 3195
    },
    {
      "path": "src/humanmotionlib/stature_comparison.py",
      "sha256": "77e2176045d41b62b628bb6eac7c4387993c71739b371d2815f3727a06997f53",
      "size_bytes": 5373
    },
    {
      "path": "src/humanmotionlib/thorax_measurements.py",
      "sha256": "9d1ba1f285c1232927888463124e07f2df345c79e381d9bdae0a72b4740fe516",
      "size_bytes": 10083
    },
    {
      "path": "src/humanmotionlib/validate.py",
      "sha256": "15c5e8347edf6cb3b515b4fe030bac622d190a5922cea25e8f7a7076488f05c2",
      "size_bytes": 18169
    },
    {
      "path": "src/humanmotionlib/verification_run.py",
      "sha256": "8943d3f0ceb1e9fa683e3fa8d12a94b1b79fd038a46f48662b8910bc0a0491e0",
      "size_bytes": 9171
    },
    {
      "path": "src/humanmotionlib/verify_skeleton.py",
      "sha256": "bcbe29dceac7e8f3fa0538daaa94983c1e41903ae6b0de1fc84b17bba910243e",
      "size_bytes": 24986
    },
    {
      "path": "tests/blender_fault_harness.py",
      "sha256": "3b9177d49755a07910bd5b0c5adfe0f903e2cb7a656615f134906a7c7ac689ea",
      "size_bytes": 4938
    },
    {
      "path": "tests/installed_acceptance/run.py",
      "sha256": "5d9449975e705c4e1a1ef535b4184915f6d5f774206bafe2a400aeb6079c9219",
      "size_bytes": 48568
    },
    {
      "path": "tests/run_roots.py",
      "sha256": "16255100fe8aae2b969ea8b7c1521e5476e1c1c0dc0140a8c88c6f149c23e8eb",
      "size_bytes": 3129
    },
    {
      "path": "tests/test_action_transforms.py",
      "sha256": "e3cd177586ee2499a6cd63608ce8042cc87843c02cdd3fc8e8aa2e8194c7e886",
      "size_bytes": 5845
    },
    {
      "path": "tests/test_actions.py",
      "sha256": "e499b3d14a94d8c338add321a803e3e1b3b3121e27cca2b3270ecd231bd95af3",
      "size_bytes": 7017
    },
    {
      "path": "tests/test_api.py",
      "sha256": "4aed8afc2e16350ba51e93242839caaf3a2751414ca6e9485b634ddf754c12a1",
      "size_bytes": 36270
    },
    {
      "path": "tests/test_balance.py",
      "sha256": "ecdc1c81bf7c26bd9408dc9c8d7d663098654c3e415fbfb2983b4dbc2d439247",
      "size_bytes": 13244
    },
    {
      "path": "tests/test_blender_backend.py",
      "sha256": "ffcc5395cce213e7761e5833067b13f4d780205cbfdc0d4ea2969ca0dc9e1060",
      "size_bytes": 9172
    },
    {
      "path": "tests/test_blender_bootstrap.py",
      "sha256": "2462a1eec6683b0db87c1b09cb1981a522760beff4cdc0282d4c53c42a13c8d0",
      "size_bytes": 2368
    },
    {
      "path": "tests/test_build_adapter.py",
      "sha256": "ac288fa316a98d90caa44aa37106de89c50d7cab7f2fded39f4b625e9a863d50",
      "size_bytes": 7658
    },
    {
      "path": "tests/test_build_skeleton_paths.py",
      "sha256": "c5daf96586ded9612de1cf8e7e28ae814cd170aa215bd3587c2ef7af124e406d",
      "size_bytes": 2702
    },
    {
      "path": "tests/test_character_api_results.py",
      "sha256": "dcea602513ee81f374f07943160b8b63a9bee334fe09a5673a9603d19f69f04c",
      "size_bytes": 15428
    },
    {
      "path": "tests/test_character_backend_reference.py",
      "sha256": "8363dac8e6424010522bd1b0e37c9c05a76d203a9bf9e6ec2b6da62aa97eb7b1",
      "size_bytes": 6806
    },
    {
      "path": "tests/test_character_compiled_skinning.py",
      "sha256": "2029ea3d0f0aa9aa4770503e2ebfaea3317fa1a9b359dd206b11f47cf80e46da",
      "size_bytes": 5471
    },
    {
      "path": "tests/test_character_installation.py",
      "sha256": "28c39510575a1c89c6c2ad4d18d6e7f3936d8bdccbd1d5d61c6bcea7b589801b",
      "size_bytes": 15217
    },
    {
      "path": "tests/test_character_integrity_faults.py",
      "sha256": "db6fc4b6d879a631083f87d6c70895c2252e4dfb02304290aaaaf6f138690a43",
      "size_bytes": 16925
    },
    {
      "path": "tests/test_character_propagation.py",
      "sha256": "cc00a28a4366302d2dcbe9f5d1a31dee18f4e7f22a2ce5e54ec487bcd16aed93",
      "size_bytes": 10473
    },
    {
      "path": "tests/test_character_review_pack.py",
      "sha256": "4d575a4468cdc579dbc773c6003a2f2a4ff0decfe58b885594f5738276833902",
      "size_bytes": 16629
    },
    {
      "path": "tests/test_character_skinning.py",
      "sha256": "31525f597f290b145be6b624585653fa1d24d5190ac6c193ffee5ea5042ac055",
      "size_bytes": 7698
    },
    {
      "path": "tests/test_character_surface.py",
      "sha256": "b226190280129fe671f5d1769ba9d9b0521618fef57e63b177afab70d73a11cb",
      "size_bytes": 27074
    },
    {
      "path": "tests/test_character_verification.py",
      "sha256": "2ea7d4be4eaf2d844da8a3c1fdc16eca1c9a636d63f61d1bcd4ea442c36e76e1",
      "size_bytes": 38402
    },
    {
      "path": "tests/test_characters.py",
      "sha256": "59fc56dc2c50cd0f53ce0296f25c962d75c71c7753a568c57189dc5bd084ebf8",
      "size_bytes": 17855
    },
    {
      "path": "tests/test_check_host.py",
      "sha256": "87052556d1a605cac4e04b446828054d36376de603ad624c07350bf33db563a3",
      "size_bytes": 4362
    },
    {
      "path": "tests/test_cli.py",
      "sha256": "3b1b186544b12b0ef0a07b5cb9b7829ed364e3e0b13fd9c2da03b2ec02f10064",
      "size_bytes": 4425
    },
    {
      "path": "tests/test_consumer_motion.py",
      "sha256": "bed2813d7865ff21c78a47a28b26a8eff38a418839ee5d778ccdf043c3c16677",
      "size_bytes": 42086
    },
    {
      "path": "tests/test_coupling_measurements.py",
      "sha256": "4c2d97d5a490a58b887ba9ed4a35bc81563cf9126ceec952295eb0b75177f841",
      "size_bytes": 8787
    },
    {
      "path": "tests/test_dense_floor.py",
      "sha256": "791573d71a8559561b6ec654626e097fcceb4e3c8f668abace02ebab26881896",
      "size_bytes": 2081
    },
    {
      "path": "tests/test_diagnostics.py",
      "sha256": "7c5feeec1bee1f2ee80f343ef4eead05c99454e295e01060f240b2dce4f53641",
      "size_bytes": 10839
    },
    {
      "path": "tests/test_geometry.py",
      "sha256": "d23b94e80398323e505b436161e83fb0c796b47ffa05a093c43e4205c844979b",
      "size_bytes": 2248
    },
    {
      "path": "tests/test_guides_and_coverage.py",
      "sha256": "98fff7e69b68060ecf93fd1554d216de1f7f84cdd6ca491ce77e190d503b4fd8",
      "size_bytes": 4834
    },
    {
      "path": "tests/test_kinematics.py",
      "sha256": "1d59b6fea3368b947e7de5b454739c6a7f65f70eadc36200f74d6016866ad132",
      "size_bytes": 3354
    },
    {
      "path": "tests/test_mapping_dossier.py",
      "sha256": "51b5c7b52a63c725670a0f883c6390aa83e7138efbf291598321576294d0f97f",
      "size_bytes": 3244
    },
    {
      "path": "tests/test_math3d.py",
      "sha256": "25db58833b90555a559b7938a612de070217cfb76b22f3fc99c3e8c6dbad41e2",
      "size_bytes": 2633
    },
    {
      "path": "tests/test_matrix_presentation.py",
      "sha256": "a4741376fac9774abef54f76a6a93404fc34d1a996fcd35c84c9a1fc9f355c7a",
      "size_bytes": 14793
    },
    {
      "path": "tests/test_matrix_test_outcomes.py",
      "sha256": "6719d785d9eb80087b1144f75a415d4fb1ae74e39a1ee9883d33b38318698a54",
      "size_bytes": 17204
    },
    {
      "path": "tests/test_matrix_workflow.py",
      "sha256": "e10b738c56dd4859149e30f2d0bfdc2306cd352c65135ffc723ad063dfc7fe92",
      "size_bytes": 48118
    },
    {
      "path": "tests/test_mirror.py",
      "sha256": "d5566c6d2f2b381490cdfbc477d04e5acfa3d6ef9e3a031b599f546251abb5f0",
      "size_bytes": 4270
    },
    {
      "path": "tests/test_mobility_dossier.py",
      "sha256": "6162c44a7991802585e77192bd1cb025643b66cbccec9777ec4f3cb03ff1993e",
      "size_bytes": 4867
    },
    {
      "path": "tests/test_pipeline_faults.py",
      "sha256": "c30fa6295afcb9f892278a5629c05e6a7800963d0299b453000bc25713bf3ac4",
      "size_bytes": 4697
    },
    {
      "path": "tests/test_poses.py",
      "sha256": "16b1c76b1069e6be0b4cb73ac58b51f5f36a453410310495090071b3cae791e5",
      "size_bytes": 3230
    },
    {
      "path": "tests/test_prepared_contract.py",
      "sha256": "5838293b644ddfae2a31b58cb2dc4056f8835adc726b8aaeffd27326d9389818",
      "size_bytes": 2493
    },
    {
      "path": "tests/test_profile_dossier.py",
      "sha256": "c1c74cab545feb4dd5f3397bf87ab088966fb089f39edc25f17014258a9730b3",
      "size_bytes": 5646
    },
    {
      "path": "tests/test_project_cleanup.py",
      "sha256": "68f33a69c6f49eea7c4e42662f7c3d7efde577976dae77f0a61c72f8b08ee824",
      "size_bytes": 23276
    },
    {
      "path": "tests/test_release.py",
      "sha256": "231f9a0463da3f97643d522ec84c595578b284223d7f09087dde4659d92b10e7",
      "size_bytes": 24460
    },
    {
      "path": "tests/test_repository_workflow.py",
      "sha256": "cb19672d987f7b12dc7e9fc3466dde7f1a6790923c7bb26ec7a80cd51d649d6e",
      "size_bytes": 24507
    },
    {
      "path": "tests/test_review_aspect.py",
      "sha256": "c3e296323124de65d4ce420103c5ad43f369a0272c7084fb724f3239c8385350",
      "size_bytes": 1391
    },
    {
      "path": "tests/test_review_graphics.py",
      "sha256": "bcc217837280d4bce1c10bde1d78fcd51c16291f37da1cff837765d4d4f2b448",
      "size_bytes": 1819
    },
    {
      "path": "tests/test_review_pack_supervision.py",
      "sha256": "10505ac3a68af5e2d99523ad1634386a5281afa1eb1f2f9cc4706a19e66af721",
      "size_bytes": 42770
    },
    {
      "path": "tests/test_review_presentation.py",
      "sha256": "6afb86c2ca0fd4b2e01dac6faaf6216c85bd5d9a899a675d0d755b425b895753",
      "size_bytes": 15210
    },
    {
      "path": "tests/test_run_blender.py",
      "sha256": "e4652ff63060b5d3670b3de0ef0d3309feda5d4b1db8b5f0aa71b9262844582b",
      "size_bytes": 24522
    },
    {
      "path": "tests/test_runtime.py",
      "sha256": "13ac6e9c0e595cb0f23389e31895cc2e42b5079a7e3e946312bf43bc978a0774",
      "size_bytes": 21419
    },
    {
      "path": "tests/test_runtime_workspace.py",
      "sha256": "b0f48a665377f6e06f79bce0e03f50739b9c102bd42316574f6b8fe0abdad290",
      "size_bytes": 3501
    },
    {
      "path": "tests/test_selected_numeric_fixture.py",
      "sha256": "c2d9f0e19f93f7e054a863ad48f8877279d4a8a8375a4382e3744f0056cb8feb",
      "size_bytes": 30011
    },
    {
      "path": "tests/test_source_integrity.py",
      "sha256": "199afad1a758dc3ca1e6b0ca8e0a36d9605339ef0a19c7c60fa1ef701b760339",
      "size_bytes": 4050
    },
    {
      "path": "tests/test_source_schemas.py",
      "sha256": "26f41d7fada239c765285525c8674508857c3a5775d95974c7c5be1abe5da2b4",
      "size_bytes": 9718
    },
    {
      "path": "tests/test_thorax.py",
      "sha256": "67333f68bffef9e6824ee702f25955502d93a92ed82c44605a2e62ffe9fd3a0e",
      "size_bytes": 7394
    },
    {
      "path": "tests/test_verification_workspace.py",
      "sha256": "85806171989d6b5c8fdc34b5ff094e78c5c908a1142e1ab571b08b7f5de6690f",
      "size_bytes": 14762
    },
    {
      "path": "tests/test_version_builds.py",
      "sha256": "468a8c4c0b7582b9bec22f1b31098d318efd7fbf9d721907d612a88de382ada0",
      "size_bytes": 4684
    },
    {
      "path": "tests/test_walking_dossier.py",
      "sha256": "af6e16e23290684fee25d00bdaf4b0ecd421f2334929dc996e3456ead933fab5",
      "size_bytes": 7514
    },
    {
      "path": "tools/README.md",
      "sha256": "3f1b9c174c684a529ecd74b9880f88bf37a920f22a22549920a7973090a696a3",
      "size_bytes": 75157
    },
    {
      "path": "tools/matrix.py",
      "sha256": "85102545fb4e12d4fd346e2082656e9cd5630390ef0a79ed9604355dc48f9563",
      "size_bytes": 36017
    },
    {
      "path": "tools/matrix_presentation.py",
      "sha256": "b8fba964e3a0904501d408ce7054b7e9e5ff1f4048735d4fb6d692d63a58f251",
      "size_bytes": 26586
    },
    {
      "path": "tools/project_cleanup.sh",
      "sha256": "e3a7a5a34e6e2033d35cc3812828c709c0e92181813b1d9a7b6fb7e1a163064b",
      "size_bytes": 12666
    },
    {
      "path": "tools/release-config.toml",
      "sha256": "75d222949b06db4d1a831bf1e79626fa0e345988c11652479e1862c8e7c62d75",
      "size_bytes": 204
    },
    {
      "path": "tools/release.py",
      "sha256": "3d0245a67a8c993f374b636065a6ecedf0d4ca66a697cbaab97d416b1fe385b7",
      "size_bytes": 36793
    },
    {
      "path": "tools/repository.sh",
      "sha256": "d3b4d77ce6a41f13e7318c2db03aa54bff6e1b0b91c140730ab22ffb8e4223ac",
      "size_bytes": 8021
    },
    {
      "path": "tools/repository_workflow.py",
      "sha256": "d90951400810bd7dca8c04a1fd922d05b62503526a8f6e6f73ad52ef1cbed792",
      "size_bytes": 27868
    },
    {
      "path": "uv.lock",
      "sha256": "a47b8d29266ffb83a8d22135bb8d724780b2ee71097b0943fe427bc44bd47225",
      "size_bytes": 27594
    }
  ],
  "file_count": 329,
  "aggregate_sha256_path_nul_sha256_newline": "ae2cd22825b41fc76ac5f657264631570bd81657033751c21dfeca4c67ddd92b",
  "try27_diff": {
    "added": [
      "openspec/changes/audit-project-tools/reviewer-retry-permissions.patch"
    ],
    "removed": [],
    "changed": [
      ".codex/agents/reviewer.toml"
    ]
  }
}
```
</details>

