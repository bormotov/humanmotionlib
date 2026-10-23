# Tasks

Implementation starts only after Human gate 1 approval and a new apply request. Use the fresh run roots and cleanup policy in `design.md`; no tests or build runs were executed during proposal creation.

## 1. Host requirements and locked setup

- [x] 1.1 Set `pyproject.toml` host support to `>=3.14,<3.15`, `.python-version` to `3.14`, and update active setup/migration instructions in `tools/README.md`, explicitly distinguishing Blender's embedded Python. Verify all three agree and Blender version/build/platform pins are unchanged; preserve historical records.
- [x] 1.2 Regenerate `uv.lock` using uv without blanket upgrades; change dependency bounds only for demonstrated incompatibilities. Verify `uv lock --check`; record the uv version and old/new dependency versions with reasons in the developer hand-off.
- [x] 1.3 In `build/upgrade-host-python-314_r1_dev_try-1_host/`, perform fresh `uv sync --locked` using its own environment, assert actual CPython `(3,14)`, run `uv pip check`, and import all direct dependencies. Verify setup succeeds and tracked requirements/version/lock hashes do not change during checks; record interpreter/executable and dependency versions.
- [x] 1.4 In `build/upgrade-host-python-314_r1_dev_try-1_negative/`, attempt locked sync with explicitly selected 3.12 or 3.13. Verify nonzero rejection and metadata exclusion of 3.12/3.13/3.15, without rewriting tracked files or sharing the supported environment.

## 2. Host checks and compatibility

- [x] 2.1 Add the documented `tools/check_host.py` entry point with actual interpreter and metadata agreement checks, discovery of all tests, exact exclusion of only the two real-backend modules, explicit totals/exclusions/skips, and nonzero failure for errors or an empty suite. Verify selection includes runtime/wrapper/review-pack synthetic tests and new discovered host modules while excluding `tests.test_blender_backend` and `tests.test_pipeline_faults` for their documented backend reason.
- [x] 2.2 Add focused host-check regression tests for wrong interpreter/metadata, discovery errors, test failures, zero selected tests and exact backend classification; document the host-only and complete commands together in `tools/README.md`. Verify the regression cases detect each failure and the full discovery command retains its original unfiltered behavior.
- [ ] 2.3 Run canonical source validation and the complete host-only command on 3.14 in a fresh developer host run (increment attempt if the earlier root has already run tests). Correct observed incompatibilities with focused regressions, without relaxing tolerances or skipping failures. Verify both commands pass and record selected/skipped/excluded counts and unchanged tracked setup hashes; repeat only after fixes.

## 3. GitHub Actions host job

- [x] 3.1 Add `.github/workflows/host-python.yml` for push/pull requests on Ubuntu, with reviewed pinned action revisions and a pinned uv version. Invoke the centralized actual-interpreter/metadata, lock, dependency, source-validation and host-test checks. Verify workflow triggers, bounded execution, valid fresh CI run naming and failure propagation; document the local equivalent, uv pin and host-only scope in `tools/README.md`.
- [x] 3.2 Verify CI failing paths for stale lock, interpreter mismatch and failed host tests using focused tests or controlled workflow-command execution in fresh owned check runs; verify no failing path can report success and no CI command regenerates the committed lock.
- [ ] 3.3 Obtain one successful hosted job on the candidate commit and record its URL, actual interpreter and check summary. Verify backend exclusions are named and evidence is retained on failure. If no hosted run can be dispatched, record the specific blocker and keep this task and CI execution acceptance open.

## 4. Complete reference-platform compatibility

- [ ] 4.1 Allocate `build/upgrade-host-python-314_r1_dev_try-1_reference/` with its own fresh locked 3.14 environment and caller-owned test root. Probe the pinned Blender through the existing supervisor and record its embedded Python identity separately using the bounded diagnostic described in design. Verify pins match, both identities are observed, and no host Python paths/packages are injected into Blender.
- [ ] 4.2 Run `uv run --locked python -m unittest discover -s tests` completely on Darwin arm64 with that pinned backend. Correct evidenced 3.14/shared-module incompatibilities and add focused regressions where needed. Verify all tests pass, the two real-backend modules execute without skip/exclusion, and receipts establish fresh completed outputs and confirmed process cleanup under unchanged numerical limits.
- [ ] 4.3 Audit actual changed files and resulting behavior for visual impact. Verify configuration/host-only changes have a documented reason for no new visual gate. If scene/render or visible shared-code behavior changes, use fresh sibling `..._dev_try-1_build/`, `..._dev_try-1_numeric/` and `..._dev_try-1_pack/` roots for the focused pack in design; verify timing, numerical checks and two-pass decoded-pixel equality and leave Human gate 2 explicitly pending.
- [ ] 4.4 Audit every external material actually used, including dependency/action source or external technical references. Verify commercial/derivative/distribution permission before use and complete matching `docs/used-materials.md` entries, including no-attribution sources; record no-new-reference use explicitly when applicable and preserve existing source provenance.
- [ ] 4.5 Complete developer cleanup and hand-off. Verify dependency/link inventories before and after removal; record removed paths/bytes, retained paths with acceptance or named diagnostic reasons, and pending cleanup. Remove obsolete owned whole runs and temporary environment/cache content after recording needed evidence; preserve protected history, another agent's roots and dependencies of any required pack.

## 5. Independent review and acceptance

- [ ] 5.1 Reviewer repeats fresh locked setup, imports, constraint rejection, source validation and complete host-only checks in `build/upgrade-host-python-314_r1_reviewer_try-1_host/` and `..._reviewer_try-1_negative/`. Verify every host scenario with actual 3.14 execution, immutable setup hashes and explicit test/exclusion totals; review executed CI evidence separately.
- [ ] 5.2 Reviewer repeats complete unfiltered unittest discovery and interpreter/backend observations in `build/upgrade-host-python-314_r1_reviewer_try-1_reference/` on the pinned reference platform. Verify real-backend execution and existing numerical/process contracts; cite any failure by requirement/scenario rather than treating host-only success as full acceptance.
- [ ] 5.3 Reviewer verifies visual-impact classification; if triggered, independently generates the design's focused pack using fresh reviewer build/numeric/pack siblings and presents it for Human gate 2. Verify exact frame/timing/layout comparisons and explicit human approval; otherwise record why this migration has no new visual gate.
- [ ] 5.4 Write `review.md` with per-requirement verdicts, interpreter/dependency identities, commands/counts, CI URL or blocker, provenance audit, evidence links and visual-gate status. Complete reviewer-owned dependency-aware cleanup, request any developer-owned cleanup and verify retained references. Record removed paths/bytes, retained reasons and pending work; unresolved required checks or cleanup prevent a completion verdict.

## Workflow follow-up

- Apply fixes through the developer and re-review affected checks if findings remain.
- Archive only after required checks and review are complete, plus Human gate 2 when the visual-impact condition applies. Proposal creation does not authorize implementation or archive.
