# Design

## Context

See `proposal.md` for motivation and `specs/host-python-runtime/spec.md` for the acceptance contract. Read-only discovery found:

- `pyproject.toml` declares `>=3.12,<3.13`; `.python-version` selects `3.12`; `tools/README.md` describes that setup. The project uses uv without installing itself as a package.
- Direct dependencies are PyYAML, jsonschema and Pillow. `uv.lock` contains a Python 3.12-specific resolution and platform wheel records. Successful 3.14 installation has not been demonstrated by planning.
- There is no tracked CI workflow. The Git remote is GitHub, so a GitHub Actions host job is a new addition rather than an edit to an existing pipeline.
- Tests use standard-library unittest. Only `tests.test_blender_backend` and `tests.test_pipeline_faults` require a real backend: the former performs builds in `setUpClass`, and the latter has a real scene-fault harness. The runtime, launcher and review-pack supervision modules use synthetic children/mocks and belong in host CI.
- `tools/runtime.py` uses POSIX process groups, fcntl locks and feature-detected `waitid`, with a Darwin fallback. Its timeout, cancellation and orphan-handling tests must run on 3.14 without weakened assertions.
- Blender is pinned independently in `pyproject.toml` to version `5.2.2 LTS`, build `d13f752e3b9c`, reference platform `Darwin-arm64`. Blender-side scripts import some shared HML modules, making host-only syntax checks insufficient for those modules.

## Goals / Non-Goals

**Goals:** Make the supported host version, lock and executed checks agree; provide host CI without silently losing tests; preserve shared-code compatibility with the actual bundled Blender Python; produce independent reference-platform evidence.

**Non-Goals:** Supporting multiple host minors, experimental/free-threaded Python builds, introducing Windows process supervision, replacing Blender's interpreter, upgrading Blender/MPFB/Rigify, changing motion data/schema conventions, or renewing the entire anatomical acceptance dossier.

## Decisions

### 1. Preserve the single-minor support policy

Set `requires-python = ">=3.14,<3.15"` and `.python-version` to `3.14`. This follows the existing single-minor policy and makes future minor adoption explicit. Keep patch selection flexible, record the actual patch/executable in each run and use ordinary CPython. A broad `>=3.14` range would advertise unverified future minors; retaining 3.12/3.13 would change this request into multi-version maintenance.

This is a breaking environment migration, not a data-convention migration. Do not edit accepted historical OpenSpec records or protected evidence merely because they mention Python 3.12. Update active setup guidance and any current runtime-selection references.

### 2. Regenerate the lock with evidence-driven dependency changes

Use `uv lock` after updating the requirement, without blanket upgrade flags. Keep current direct dependency bounds unless the resolver or executed 3.14 tests establish a concrete incompatibility. Record old/new resolved versions and why each changed; do not hand-edit wheel URLs or hashes. Before every acceptance run use `uv lock --check`, `uv sync --locked`, `uv pip check`, direct import smoke checks and an assertion on the actual host interpreter. Record the uv version and before/after hashes of `pyproject.toml`, `.python-version` and `uv.lock`.

Use a fresh environment under each check run with `UV_PROJECT_ENVIRONMENT=<run-root>/environment` and a tool cache below that root where necessary. This avoids proving compatibility with an old `.venv`. Explicitly attempt `uv sync --locked --python 3.12` or `3.13` in a separate negative-check run/environment; use an available old interpreter or provision one with uv. It must fail on the declared requirement. Also evaluate metadata bounds for 3.12, 3.13, 3.14 and 3.15 without requiring all four interpreters to be installed. No application-startup version guard is required: this contract governs supported uv setup.

### 3. Centralize a complete, explicitly scoped host test command

Add and document `uv run --locked python tools/check_host.py` as the host-only test entry point. It uses unittest discovery from the repository's tests directory and filters only the exact module identities `tests.test_blender_backend` and `tests.test_pipeline_faults`. Resolve test identity consistently with top-level repository discovery. It reports selected test totals, the two exclusions with their real-backend reason, all skips and normal unittest failures; zero selected tests or discovery/import errors fail. Newly discovered test modules are included by default. Keep the existing full command `uv run --locked python -m unittest discover -s tests` unchanged in meaning and without filtering.

A short dedicated runner is preferable to duplicating a long static module allowlist in workflow YAML and documentation. Keep unittest's ordinary error behavior, including failed imports. Add meaningful selection regression cases covering a newly discovered host module, a loader error, failure exit propagation and exclusion of real-backend modules while retaining mixed synthetic supervision modules. Do not add a global skip-on-missing-Blender policy to the full suite.

CI version/metadata consistency checks belong in this documented check entry point or clearly named documented command, and must execute before test discovery. Test their failing paths so a CI YAML exit-zero typo or omitted check is detectable. Centralize the actual check commands in `tools/README.md`; workflow YAML invokes them rather than maintaining different test lists.

### 4. Introduce host CI without requiring a Blender installation

Create `.github/workflows/host-python.yml` for `push` and `pull_request`, using one Ubuntu runner and CPython 3.14 selected from the repository version file. Install uv with an explicitly pinned version, retain that version in the setup documentation, and pin third-party actions to reviewed immutable revisions. Cache use may improve setup, but every run still validates and synchronizes the committed lock and asserts the actual interpreter. This host job establishes Python/tool compatibility on POSIX Linux; the pinned Blender reference platform remains Darwin arm64.

The job runs the lock check, locked setup, dependency consistency/import checks, source validation (`tools/validate.py --profile adult-reference-v1`) and host test command. It records the candidate commit, interpreter and uv/dependency versions, command outcomes, test count and excluded backend scope. It never regenerates or commits `uv.lock`. Preserve relevant failure evidence even after failed commands; do not hide failures behind unconditional success or a skipped required step.

Use fresh CI run names such as `build/upgrade-host-python-314_commit-<short-sha>_ci_run-<run-id>-<attempt>_checks/`; each placeholder must resolve to a lowercase-kebab component. A job timeout bounds the check. Record the successful hosted run URL in the review report when available. If hosting/permissions prevent dispatch, the reviewer reports that CI execution remains unverified and does not substitute a YAML audit for an executed-job verdict.

### 5. Keep backend compatibility a separate required result

On Darwin arm64, create a separate fresh environment/run and execute the entire existing unittest suite using Python 3.14 with the pinned Blender on PATH. This covers clean real builds and repeatability at reference statures plus deliberate scene faults using existing numerical criteria; it is sufficient baseline backend coverage for a host-only migration. Missing Blender, pin mismatch, skipped real backend tests or unresolved process cleanup block complete acceptance.

Record host interpreter identity separately from Blender's actual embedded Python identity. Obtain the latter with a small bounded background/factory-startup probe after the existing pinned-executable check, through the existing supervisor, emitting and validating a current-invocation JSON result plus completion marker. Store the probe script/result as check-run content if a script file is needed; it is diagnostic evidence, not a new public command or backend pin. Do not require Blender's version to equal 3.14, change its installation, inject host site-packages or propagate the host environment's Python path into Blender. Confirm shared-module compatibility by running the actual existing Blender-side scripts, not by compiling them solely with host 3.14.

Compatibility fixes are allowed only where demonstrated by these checks. A failing regression must be explained and corrected, not removed or given wider tolerances. New dependencies, conventions or changed output behavior outside this migration return to the architect before implementation proceeds.

### 5a. Correct Linux zombie-only process-group classification

Observed Ubuntu 24.04 / CPython 3.14 CI run `39977052957` at commit `b3bba12` passed setup, lock, dependencies and source validation, then failed supervised-process checks. The host migration's Ubuntu job exposes a portability defect: `_wait_child_unreaped()` intentionally retains the exited leader using `waitid(..., WNOWAIT)`, while Linux `_group_state()` currently treats successful `killpg(pgid, 0)` as live work. The unreaped zombie leader therefore makes an ordinary completed child appear to have a live descendant. That false orphan outcome also prevents expected output validation from running. This is an observed compatibility correction under the approved host-check and CI requirements; acceptance criteria do not change.

Extend the existing bounded Darwin process-table classifier to Linux, preserving the unreaped leader as the process-group identity anchor until all necessary signals have been sent. A complete, valid snapshot with only `Z` entries in the group establishes no executable work; any non-zombie member establishes live work. Preserve `ambiguous` for a required missing anchor, malformed/unreadable/timed-out snapshots, or an empty snapshot not independently confirmed absent by kernel `ESRCH`. `EPERM` alone remains uncertainty. Other platform behavior, deadlines, signal escalation, advisory locking, fresh evidence and output validation remain unchanged. Reaping the leader earlier or treating all successful exits as clean is rejected because either would weaken descendant ownership checks.

The developer adds focused classifier tests for Darwin and Linux covering zombie-only, live descendant, missing anchor, invalid/unavailable snapshot and empty-group ESRCH/EPERM cases. Existing actual-child tests must still distinguish normal zero/nonzero/signal exits from genuine live descendants, validate fresh outputs, clean cancellation/timeouts and serialize callers. Repeat the complete Ubuntu host job and independently rerun the affected runtime suite on Darwin in fresh owned runs; review the previous reference result against the final patch and repeat broader checks only if that review identifies further impact. No scene, pose, sampling or rendering behavior changes, so this correction alone does not trigger a visual pack.

### 6. Scope the visual gate to actual visual impact

For configuration, lock, CI and host-only compatibility fixes with no visible behavior change, the reviewer records the affected-scope audit and a reason that Human gate 2 is inapplicable. No new full render dossier is required merely because the host interpreter changed.

If fixes touch scene/render behavior or shared code that affects visible output, use the existing source fixtures `neutral`, `rest` and `arm-raise`, H=1.70 m, BPM 60/120/180. Prepare using the existing fixture selection, build through `tools/run_blender.py`, verify with current numerical checks and use `tools/review_pack.py` for its two tool-managed clean render passes. No protected historical pack is overwritten. If the observed affected behavior needs a different diagnostic, return to the architect to revise the scope before proceeding.

The focused acceptance pack includes:

- Neutral/rest front and side images with stable floor/camera framing.
- Arm-raise static sheets with two labeled rows (Front, Side) and five beat columns 0–4, plus animation sheets for each BPM with the same two-view arrangement and exact beat/time labels.
- Front/side GIF pairs for each BPM: 21/13/13 animation samples respectively, at least two in-betweens per beat, no sample interval over 200 ms, and timing consistent with the same keyed animation as the static frames.
- Front/side onion-skin overlays at beats 0/1/2/3/4 with floor/contact markers; no camera adjustment to improve apparent stability.
- Decoded-pixel equality between the two clean passes, current numerical results and clearly labeled comparison to the protected previous pack when a matching subset exists. Historical comparison is explanatory; this change does not demand cross-host-version pixel identity when dependency versions differ. Any visible change must be explained and receive explicit human acceptance.

The human checks upward/downward direction, shoulder coordination, planted feet, stable framing and consistency of static poses with GIF endpoints. This pack is a focused compatibility regression, not renewed complete anatomical/mobility acceptance.

### 7. Clearance and provenance remain mandatory

Planning uses only repository files and the human request, with no new external reference material. During implementation, verify commercial use, intended derivative permission and distribution compatibility before using any external documentation, package/action source or other material to inform a fix. Record every actually used material, including permissive/no-attribution sources, in `docs/used-materials.md` with material/part used, source URL, license/version/license URL, permission basis, conditions/attribution, check date and related outputs. Check changed dependencies/actions and follow their conditions; ambiguous or incompatible permission blocks use. Reuse existing entries only when they cover the precise material and use. No new pose, segment or motion is authored; existing provenance stays intact.

## Risks / Trade-offs

- [A resolved package lacks a usable 3.14 build on a target platform] → Prove a clean locked install on Ubuntu CI and Darwin arm64; adjust only incompatible dependency bounds and record the evidence.
- [Host-only CI obscures backend regression] → Name exclusions, preserve full discovery and require a separate reference-platform result.
- [New host syntax breaks Blender-shared modules] → Keep shared code compatible with the observed bundled interpreter and exercise actual Blender scripts.
- [Process supervision behaves differently under the new interpreter] → Run existing synthetic timeout, cancellation, contention and orphan tests without relaxed bounds, plus actual backend tests.
- [CI configuration exists but has never executed] → Report hosted execution independently and keep that acceptance item open until an actual run is available.

## Migration Plan

1. Obtain Human gate 1 approval for these artifacts. No implementation is authorized by the proposal workflow itself.
2. Update host selection and active instructions, regenerate the lock, add the scoped host runner and CI workflow, then fix evidenced compatibility issues.
3. Run developer host and complete reference checks; independent reviewer repeats in new environments and records per-requirement verdicts in `review.md`.
4. If the affected-scope audit triggers the focused visual pack, obtain explicit Human gate 2 approval before archive. Otherwise document why no visual change occurred.
5. Contributors recreate their local uv environment from the committed lock; Blender installation remains as pinned. To roll back a failed migration, restore requirements, version file, lock, compatibility changes, CI and setup documentation together from the prior commit and recreate the host environment; never roll back only the selector or lock.

### Run allocation, evidence and cleanup

Each independent check/build/review attempt is a new direct child of `build/`. Initial names are:

| Activity | Developer root | Reviewer root |
|---|---|---|
| Host setup and host suite | `upgrade-host-python-314_r1_dev_try-1_host/` | `upgrade-host-python-314_r1_reviewer_try-1_host/` |
| Unsupported-interpreter setup | `upgrade-host-python-314_r1_dev_try-1_negative/` | `upgrade-host-python-314_r1_reviewer_try-1_negative/` |
| Complete reference suite and interpreter probe | `upgrade-host-python-314_r1_dev_try-1_reference/` | `upgrade-host-python-314_r1_reviewer_try-1_reference/` |
| Conditional focused build | `upgrade-host-python-314_r1_dev_try-1_build/` | `upgrade-host-python-314_r1_reviewer_try-1_build/` |
| Conditional numerical check | `upgrade-host-python-314_r1_dev_try-1_numeric/` | `upgrade-host-python-314_r1_reviewer_try-1_numeric/` |
| Conditional two-pass visual pack | `upgrade-host-python-314_r1_dev_try-1_pack/` | `upgrade-host-python-314_r1_reviewer_try-1_pack/` |

Prepend `build/` to each basename. Increment the attempt or revision for every retry. Environments, test `cases/`, receipts, scripts and tool-required clean passes stay inside their owning run. Set `HUMANMOTIONLIB_TEST_RUN_ROOT` to that fresh caller-owned root before tests. Separate independently initiated input/output roots are disjoint after symlink resolution; preparation/build may share their single build root as already supported.

Developer hand-off and reviewer `review.md` inventory created roots, hashes, commands, outcomes, interpreter identities, test/skipped/excluded counts, and retained evidence. Keep final host/reference reports and necessary receipts to substantiate the runtime verdict; keep a triggered pack and its linked build/numerical dependencies for human acceptance. Temporary environments/caches, superseded successful duplicates and resolved failure runs are obsolete after their useful evidence is summarized. Retain unresolved failure evidence only for a named finding and reconsider after its resolution.

Before hand-off on success or failure, inventory dependencies and local links, remove obsolete owned whole run roots and unnecessary internal content, then recheck retained references. Never follow symlinks outside `build/`, change protected history or clean another agent's active/owned roots. Reviewers request developer cleanup for developer-owned roots. Record removed paths/bytes, retained paths/reasons, dependency results and pending cleanup in the existing hand-off or `review.md`; pending cleanup prevents a completion claim. Planning itself creates no build runs.
