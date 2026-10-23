# CI implementation hand-off

## Workflow implementation

`.github/workflows/host-python.yml` runs for `push` and `pull_request` on
`ubuntu-24.04` with a 30-minute job timeout. It uses immutable, verified action
commits and uv `0.13.5`, selects Python from `.python-version`, and creates a
fresh `build/upgrade-host-python-314_commit-<short-sha>_ci_run-<run-id>-<attempt>_checks/`
root. The job checks the committed lock, performs `uv sync --locked`, asserts
the host interpreter and metadata, checks the installed environment, validates
canonical sources, then runs host-only tests. It never calls a lock-generation
command. Each command has `set -euo pipefail`; job/step outcomes, interpreter
versions, test totals and named backend exclusions are retained in the run
summary and uploaded on success or failure for 90 days.

Action refs:

- `actions/checkout@08c6903cd8c0fde910a37f88322edcfb5dd907a8` (`v5.0.0`)
- `actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97` (`v7.0.0`)
- `astral-sh/setup-uv@07a047e608db84b3d8c06cd9a7c7dcc9c355c18e` (`v10.3.2`)
- `actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02` (`v4.6.2`)

Commercial and distribution permissions for the pinned actions and uv versions
were checked against their MIT license files and recorded in
`docs/used-materials.md` on 2026-10-23.

## Local validation evidence

- `build/upgrade-host-python-314_r1_ci_try-1_checks/`: inspected triggers,
  runner, timeout, immutable action SHAs, fresh run naming, lock immutability,
  summary/artifact steps and documented local command alignment; `bash -n`
  passed for all seven multiline workflow shell blocks.
- `build/upgrade-host-python-314_r1_ci_try-1_stale-lock/`,
  `build/upgrade-host-python-314_r1_ci_try-1_interpreter-mismatch/`, and
  `build/upgrade-host-python-314_r1_ci_try-1_failed-tests/`: initial controlled
  failure checks, retained as iteration history.
- `build/upgrade-host-python-314_r1_ci_try-2_stale-lock/`: controlled stale
  lock returned status 1 before `uv sync --locked` could run.
- `build/upgrade-host-python-314_r1_ci_try-2_interpreter-mismatch/`: controlled
  interpreter mismatch returned status 1 at the environment assertion.
- `build/upgrade-host-python-314_r1_ci_try-2_failed-tests/`: controlled host
  test failure returned status 1 through the `tee` pipeline.
- For all controlled cases, SHA-256 hashes of `pyproject.toml`,
  `.python-version` and `uv.lock` were unchanged. The failure logs include
  exact mock command order and the failing diagnostic.
- `git diff --check` passed.

The seven local controlled-check roots above were fresh direct children of
`build/`, with valid five-component names and no symlinks. The independent
reviewer confirmed they were not dependencies, so they were removed after their
results were summarized here. Removed paths and inventoried bytes:

- `build/upgrade-host-python-314_r1_ci_try-1_checks/` — 6,933 bytes.
- `build/upgrade-host-python-314_r1_ci_try-1_stale-lock/` — 438 bytes.
- `build/upgrade-host-python-314_r1_ci_try-1_interpreter-mismatch/` — 526 bytes.
- `build/upgrade-host-python-314_r1_ci_try-1_failed-tests/` — 633 bytes.
- `build/upgrade-host-python-314_r1_ci_try-2_stale-lock/` — 438 bytes.
- `build/upgrade-host-python-314_r1_ci_try-2_interpreter-mismatch/` — 526 bytes.
- `build/upgrade-host-python-314_r1_ci_try-2_failed-tests/` — 633 bytes.

Total removed for the controlled checks: 10,127 bytes. At that stage the
downloaded hosted-failure root was retained for core diagnosis; its later
release and removal are recorded under hosted-run acceptance below.

## Hosted-run acceptance

GitHub access was restored by the orchestrator. The initial hosted run
[39977052957](https://github.com/bormotov/humanmotionlib/actions/runs/39977052957)
checked candidate commit `b3bba12c25b365c26a88da7ccf7c6729475deaaa` on
Ubuntu 24.04.5 with CPython 3.14.8 x64 and uv 0.13.5. Setup, lock, interpreter,
dependency and source checks passed. Host selection reported 160 tests,
excluded `tests.test_blender_backend` (6) and `tests.test_pipeline_faults` (1),
and skipped none. The suite failed after 376.695 seconds with 3 failures and 5
errors in process supervision. The uploaded failure artifact remains available
as ID `12512196945` at
https://github.com/bormotov/humanmotionlib/actions/runs/39977052957/artifacts/12512196945
(35,218,718 bytes; ZIP SHA-256
`9278b9e11f56a918db5608e2839657c04d33b2cc36262fdfbcb5059f66c35cf8`). Its
failure symptoms and correction are summarized in the developer hand-off.

The corrective candidate succeeded in hosted run
[39980051076](https://github.com/bormotov/humanmotionlib/actions/runs/39980051076)
on commit `3dc9126c59db0b3dac7b4fa702250f97205f0f28`. Job
`120504663290` completed successfully on Ubuntu 24.04.5 with CPython 3.14.8
x64 at `/opt/hostedtoolcache/Python/3.14.8/x64/bin/python3.14`, uv 0.13.5,
PyYAML 6.0.3, jsonschema 4.26.0 and Pillow 12.3.0. Lock validation, locked
sync, interpreter/metadata/import checks, dependency consistency and canonical
source validation all passed. Host-only discovery selected 163 tests, excluded
`tests.test_blender_backend` (6) and `tests.test_pipeline_faults` (1), and
reported zero skips; all 163 passed in 315.095 seconds. Successful-run evidence
was uploaded as artifact ID `12513217111` at
https://github.com/bormotov/humanmotionlib/actions/runs/39980051076/artifacts/12513217111
(35,219,366 bytes; ZIP SHA-256
`23811c4bbce77f8c807448f97147639fef206028ac8cbf72574b0bdb187b8d4f`).

The earlier downloaded failure artifact root was released by the core developer
and reviewer after their independent hand-off retained the finding and fix.
Its local copy `build/upgrade-host-python-314_r1_ci_try-3_hosted-failure/`
contained 100,835,802 file bytes and no symlinks; it was removed after both
agents confirmed no dependency. Post-cleanup checks confirmed the path is absent.
The hosted failure artifact remains available as noted above. All seven mock
roots and the downloaded failure root are absent; no CI-owned cleanup is
pending. Retained evidence is limited to the hosted success/failure artifacts
and this hand-off record. Task 3.3 is complete based on the successful hosted
candidate run.
