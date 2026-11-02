# Task 5.1 supported-tool audit

This audit maps the supported command surface in design section 6 to the
current guides, commands and available bounded evidence. It is not a claim of
full library or visual acceptance.

## Operation map

| Operation and goal | Supported command / requirements | Evidence and outcome | Remaining gap and next action |
|---|---|---|---|
| Start from a clone; get oriented | `make` / `make help`; Make and POSIX shell. `make package` and `make dev` additionally require uv and first-use network access. | Tasks 2.1, 2.2, 3.1 and 3.4 have literal clean-copy runs. Current `hml --help` and `hml check-environment` exited 0 from the exact package-check environment: HML 0.3.0, CPython 3.14.6, locked dependencies. | No gap in the documented entry route. |
| Validate and prepare canonical sources | `hml validate --profile adult-reference-v1`; `make dev` performs project setup, current package install and source/readiness checks. `hml prepare-skeleton` requires a profile and output; Blender is not needed for preparation. | Current packaged `hml validate` exited 0 (`valid-sources`, 180 structures, 67 actions, 32 fixtures). `make dev` clean/repeat and Python/YAML source-refresh evidence is in tasks 2.3 and 3.1. | The existing prepared source model is the skeleton diagnostic profile. There is no canonical `poses/`, `segments/`, or `motions/` library route for arbitrary exercise YAML. For that goal, propose a separate OpenSpec change defining canonical motion data and its build recipe; do not invent a format in this audit. |
| Build and inspect a selected preview | `make matrix-list`, `make matrix-build CHARACTER=... HEIGHT=...`, `make matrix-check ...`; Blender only for build/render. | Tasks 3.2 and 3.3 plus their reports verify one selected neutral/rest/arm-raise pair at BPM 120 with controlled generation, retry/failure order, actual result validators and the clarified read-only missing-result behavior. No real Blender render is claimed. | Real visual output remains subject to the separate character change and its human gate. Resume only under that approved visual scope. |
| General rendering / consumer-authored motion | Installed API `humanmotionlib.api.prepare/render` and `hml run-blender`; fixed Blender 5.2.2 LTS build d13f752e3b9c on the documented macOS arm64 reference host. `tools/README.md` includes an explicit bounded API route and source/render identity contracts. | Help for `prepare-skeleton` and `run-blender` succeeded from the checked package. The consumer motion docs and prior consumer-motion tests describe source snapshot validation, supervised rendering and outputs. | There is no one-command Make goal for an arbitrary newly authored exercise because the library has no canonical motion-source tree or general recipe yet. Next action: approved OpenSpec change for canonical exercise/motion authoring and a default build route. No custom exercise or real render was attempted here. |
| Numeric verification | `hml verify-skeleton` supports scoped transforms, selected-character numeric mode, dense checks and cross-stature comparison; the required input is evaluated or explicitly scoped evidence. | Current help enumerates modes. `SelectedSkeletonNumericFixtureTests`: 4/4 passed against synthetic evidence with backend measurements mocked; the report correctly remains globally incomplete. The docs distinguish scoped checks from complete backend acceptance. | Full evaluated-mesh, dense-floor and cross-stature checks require built Blender evidence and are not established by these host fixtures. Next action: run the documented verifier on the candidate builds in the separately approved visual/acceptance workflow. |
| Result reuse and presentation | `hml review-pack --reuse-renders` reassembles hash-matched existing render passes; `--html-only-from` rebuilds HTML from a verified pack without Blender/media rewrites. Matrix check validates existing results. | Help confirmed both modes. `tests.test_release`, `tests.test_matrix_presentation`, and `tests.test_review_presentation` passed 38/38 controlled tests. Prior matrix checks exercise repeat/no-mutation and task 4.4 verifies missing results do not recreate logs while started checks of existing invalid results retain diagnostics. | Actual review-pack reuse and HTML-only regeneration need a real verified pack, which is absent from this bounded nonvisual audit. Next action: exercise them against the independently verified pack when the relevant change reaches that gate. |
| Host tests | `humanmotionlib.check_host --test-root tests`; ordinary contributor command documented in `tools/README.md`. It excludes the two explicit real-Blender modules and checks installed interpreter/package identity. | The package route recorded an exact independent installation and `uv pip check`; tasks 2.2, 3.2, 3.3 and 4.4 record focused test runs. This audit ran 38 presentation/release tests, 4 selected numeric fixture tests and 4 guide/coverage tests (46 total). | Full contributor host suite was not run as part of this command-surface audit. Next action: run `hml check-environment` plus the documented host suite against the frozen candidate before independent review. |
| Cleanup | `make mostlyclean`, `make clean`, `make distclean`; Make, POSIX shell and `ps`/`lsof` plus filesystem utilities. | Tasks 4.1–4.4 verify fixed areas, exact bytes, missing Python/uv, process activity, link behavior, failed checks and recovery on disposable trees. Never applied to the real project build. | No scope gap. Distclean's specific symlink fixture timing was inconclusive; clean's separately verified unlink preserved the outside target (see task 4.4 report). |
| Read-only release planning | `python tools/release.py plan --boundary <commit> --target main` or `--help`; Git and Python standard library. `plan` reads Git history and canonical specs. | `plan --help` exited 0. `plan --repo <checkout> --target HEAD` exited 0 and returned a JSON plan for version 0.3.0 from the configured bootstrap boundary; `tools/release.py`'s `build_plan` uses read-only Git queries. `tests.test_release` contributed to the 38 passing tests. | `pending` also consults live GitHub release state and was not called; it needs network/token context. Next action: run it in CI/release context with the configured repository and token. `reserve`, `set-version`, `publish`, and `dispatch-pending` mutate Git/GitHub and are explicitly outside read-only planning. |

## Focused command evidence

The exact independent package-check environment used for installed HML help,
source validation and environment inspection was:

`build/audit-project-tools_r1_dev_try-22_restoration/checkout/build/package-humanmotionlib_r1_dev_run-20261102t152434031221-71593_check/environment/`

It records a successful pre-test environment report and `uv pip check` in the
4.4 observations. The separate earlier try-13 environment was used for the
controlled source/numeric/presentation/release tests. The tests wrote only in
this audit's owned run root. The exact report and test run are not Blender
acceptance evidence.

Commands run directly for this audit:

- Installed HML `--help`, `validate --profile adult-reference-v1`,
  `check-environment`, and `--help` for `prepare-skeleton`, `run-blender`,
  `verify-skeleton`, and `review-pack`: each exited 0.
- `tools/release.py plan --help`: exit 0.
- `tools/release.py plan --repo /Users/bormotov/work/humanmotionlib --target HEAD`:
  exit 0, JSON plan only.
- Tests: `tests.test_release tests.test_matrix_presentation
  tests.test_review_presentation` — 38 passed; `SelectedSkeletonNumericFixtureTests`
  — 4 passed; `tests.test_guides_and_coverage` — 4 passed.

## Documentation correction

The 4.4 read-only refusal rule was implemented and validated in code, but the
user-facing matrix and usage guides did not yet explain it. Updated
`docs/build-matrix.md` and `docs/usage.md`: a missing result root/build record
returns the selected build command without filesystem writes; an attempt
against an existing result retains its log and report, including validation
failure. `tests.test_guides_and_coverage` passed 4/4 after this edit.

No Blender render, full dense/stature acceptance, publication or cleanup of the
real `build/` was performed.
