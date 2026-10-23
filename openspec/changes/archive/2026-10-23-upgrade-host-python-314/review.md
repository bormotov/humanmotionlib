# Independent review — upgrade-host-python-314

## Verdict

**PASS** for candidate **`3dc9126c59db0b3dac7b4fa702250f97205f0f28`**. All required host, hosted Ubuntu CI and independent pinned reference-backend scenarios pass. No open findings or cleanup remain. This does not approve anatomical visual correctness or archive the change.

Review date: 2026-10-23. `/AGENTS.md` is absent; repository `AGENTS.md`, reviewer instructions, apply instructions, proposal, delta spec, design (including corrective §5a), tasks and applicable backend/lifecycle specifications were read. No implementation, source, spec or test was edited by the reviewer.

Evidence roots below are repository-relative. [Final evidence index](../../../../build/upgrade-host-python-314_r3_reviewer_try-1_archive/index.md).

## Requirement/scenario checklist

| Requirement or scenario | Check class | Verdict and evidence |
|---|---|---|
| HML selects one supported host Python minor | Automatable | PASS: project `>=3.14,<3.15`, selector `3.14`, equivalent generated lock `==3.14.*`; Blender pins independent and unchanged. |
| Select the supported host | Automatable | PASS: fresh locked reviewer CPython 3.14.6, executable recorded; hosted actual CPython 3.14.8. |
| Reject an unsupported host selection | Automatable | PASS: explicit 3.12.13 locked sync exits 2; bounds reject 3.12/3.13/3.15 and accept 3.14. |
| Locked host dependencies reproduce a usable environment | Automatable | PASS: fresh host and reference lock check/sync/import/pip checks; identical before/after setup hashes. |
| Recreate the host environment from the committed lock | Automatable | PASS: dependency identities/diff explained below; no setup or lock rewrite. |
| Host checks retain existing HML behavior | Automatable / numeric | PASS: final host 163 tests, reference 170 tests; original source/numerical/timing/process limits preserved. |
| Verify the complete host scope | Automatable | PASS: source validation, 163 selected tests, zero skips, only exact backend exclusions 6+1. New-module/broken-import/empty-suite/failure paths verified. |
| CI enforces the host environment contract | Automatable | PASS: workflow audit and independently queried successful candidate job; all required steps succeed and failure evidence is retained. |
| Run the host job from a clean checkout | Automatable | PASS: hosted run 39980051076; actual Python 3.14.8, uv 0.13.5, 163 passing tests; stale-lock/interpreter/test failure paths checked. |
| Blender compatibility is verified independently | Automatable / numeric | PASS: pinned version/build/platform, separate embedded interpreter and original full discovery verified in a fresh reviewer environment. |
| Run the complete suite on the reference backend | Automatable / numeric | PASS: 170 tests in 123.154 s, no skips/exclusions, five native builds plus actual scene-fault harness and supervised receipts. |
| Preserve visual contracts if a compatibility correction affects rendering | Human visual judgement, conditional | NOT TRIGGERED: final runtime correction concerns process liveness only; no visible scene/render/shared math/source change. No human visual correctness claim. |

## Independent execution

Final runs:

- `build/upgrade-host-python-314_r2_reviewer_try-1_host/`
- `build/upgrade-host-python-314_r2_reviewer_try-1_negative/`
- `build/upgrade-host-python-314_r2_reviewer_try-1_reference/`

Both supported runs started empty and used their own uv environment/cache, never an existing `.venv`. `uv 0.11.21` executed `uv lock --check`, `uv sync --locked`, `uv run --locked python tools/check_host.py --check-environment`, and `uv pip check --python <owned-environment>/bin/python`; all exit 0. Actual CPython is **3.14.6** on **Darwin-arm64**, with full executable paths in `environment.log`/`identities.json`.

Installed versions: attrs 26.1.0, jsonschema 4.26.0, jsonschema-specifications 2025.9.1, Pillow 12.3.0, PyYAML 6.0.3, referencing 0.37.0 and rpds-py 2026.9.1. Independent old/new lock comparison finds no new package or changed retained package version. `typing-extensions` 4.16.0 is removed because referencing's installed metadata requires it only when `python_version < '3.13'`; wheel records otherwise change for the new minor. Direct bounds are unchanged.

`uv run --locked python tools/validate.py --profile adult-reference-v1` exits 0: **180 structures, 67 actions, 3 placements, 32 fixtures**. `uv run --locked python tools/check_host.py` passes **163 tests in 90.239 s, zero skips**, excluding only `tests.test_blender_backend` (6) and `tests.test_pipeline_faults` (1), with explicit reasons. Runtime, wrapper, presentation and synthetic render supervision tests execute.

The final negative run executes `uv sync --locked --python /opt/homebrew/bin/python3.12`: **exit 2**, explicitly rejecting CPython 3.12.13; it does not select a replacement interpreter. The unchanged runner/bounds have supplemental independently executed evidence from the original candidate, preserved with explicit baseline provenance in the final host root: new discovered module included automatically, real broken import fails, bounds exclude unsupported minors, and actual copied stale lock exits 1 with an explicit needs-updating diagnostic while lock bytes remain unchanged. The runner's focused regressions execute empty-suite, wrong interpreter/metadata and test-failure rejection.

Setup SHA-256 values are identical before/after both final setups and suites:

| File | SHA-256 |
|---|---|
| `pyproject.toml` | `a91558939f1d25589c900c1dac77b066bbe2d124f719ab4b932a48e9560a48f9` |
| `.python-version` | `a876e0b10411037a012498b9fe18d9bc1df32ed8b722a13564dc944ddcfd9135` |
| `uv.lock` | `73f5da418577394cc68c3a1ee31deb693782bf11cf1ef6cbc81ae960c2854179` |

`snapshot-before.json`/`snapshot-after.json` additionally establish unchanged runtime, runtime tests, host runner/tests and workflow bytes at the final candidate during verification.

## Hosted CI and corrective delta

Reviewer independently queried GitHub using `gh run view`; final `hosted-job.json` confirms **success** and exact candidate SHA. [Hosted run 39980051076](https://github.com/bormotov/humanmotionlib/actions/runs/39980051076), job `120504663290`, executes on Ubuntu 24.04 with actual **CPython 3.14.8 x64**, **uv 0.13.5**, PyYAML 6.0.3, jsonschema 4.26.0 and Pillow 12.3.0. Lock check, locked setup, actual interpreter/imports, dependency consistency and source validation all pass. The retained minimal job-log extract shows **163 tests in 315.095 s**, zero skips and only named 6+1 exclusions. `ci-handoff.md` records the success artifact ID `12513217111`, size and checksum.

Workflow audit confirms push/pull-request triggers, Ubuntu runner, 30-minute timeout, immutable action revisions, pinned uv, fresh five-component CI roots, `set -euo pipefail` pipelines, no lock regeneration/Blender installation, and `if: always()` outcome/artifact retention. An earlier real hosted run [39977052957](https://github.com/bormotov/humanmotionlib/actions/runs/39977052957) failed process tests after passing setup, demonstrating failures do prevent job success; it is superseded, not waived.

That failure exposed a Linux process-group classification defect: an intentionally unreaped `waitid(WNOWAIT)` leader is a zombie, but `killpg(..., 0)` reported the group present. Architect design §5a extends the existing bounded Darwin `ps` classifier to Linux. Independent delta audit confirms preservation of the unreaped ownership anchor, complete group observation, zombie/live distinction, ambiguity for missing anchor/malformed/unreadable/timed-out/nonzero snapshots, kernel ESRCH requirement for empty unanchored snapshots, and uncertainty for EPERM. Deadlines, signal escalation, locking and fresh-output validation are unchanged. Independent `classifier_audit.json` passes **18 Darwin/Linux snapshot cases plus 8 observation-error/missing-ps cases**. The full final actual-child suites also pass.

## Independent pinned Blender evidence

Existing supervised version probe observes **Blender 5.2.2 LTS**, build **d13f752e3b9c**, **Darwin-arm64**. A separately supervised 30-second background/factory-startup diagnostic emits a current random token, valid JSON and `script_complete`; output/completion/token validation succeeds. Actual embedded interpreter is **CPython 3.13.13**, separate from host 3.14.6. Probe environment removes host Python/venv injection variables; observed embedded `sys.path` contains no host environment path (`identities.json`, `embedded.json`, receipts).

Original unfiltered `uv run --locked python -m unittest discover -s tests`: **170 tests in 123.154 s, OK, zero skips/exclusions** (`full-suite.log`, `full-suite.json`). This includes all six real-backend tests and the real scene-fault test. Fresh native neutral/rest builds cover 1.50/1.70/1.90 m and an independent repeated 1.70 m build; a fifth build covers six articulated deep-chain samples. All ten scene faults are rejected by the intended unchanged measurement. Current script outputs/completion hashes are validated; build/fault/probe operations succeed. Synthetic cancellation cleanup is confirmed within unchanged 5-second TERM/5-second KILL limits; no real pending process cleanup remains.

Independent measured native values (`numeric-summary.json`):

| Metric | Actual | Unchanged tolerance |
|---|---|---|
| Maximum object/bone scale residual, five builds | 2.384185791015625e-7 | <= 1e-6 |
| Minimum geometry floor coordinate | 0 H | >= -1e-4 H |
| Repeat 1.70 m maximum body position residual | 0 m | < 1.7e-6 m |
| Repeat maximum rotation-matrix element residual | 0 | < 1e-6 |
| Repeat maximum geometry-bounds residual | 0 m | < 1.7e-6 m |
| Repeat topology digests and vertex counts | identical | exact equality |

These are the approved migration baseline, not renewed complete anatomical/contact/render/bake acceptance. No new rendered visual pack is required: the diff changes host configuration/checks, CI and process liveness; camera, floor, light, motion data, sampling and render implementation are unchanged. Visual correctness remains with the human; no new visual decision is requested.

## Scope and provenance

Scope audit finds no unrelated source/dependency/convention changes. MPFB/Rigify remain unused; Blender pins unchanged. The only additional compatibility correction is the observed, architect-designed process classifier change above. Original R1 host/reference passes were 160/167 and are superseded by final 163/170 execution, not presented as final-candidate evidence.

`docs/used-materials.md` lists all four new actions and both uv releases with specific license URLs, commercial/derivative permission and notice conditions. Reviewer independently read MIT grants for checkout v5.0.0, setup-python v7.0.0, upload-artifact v4.6.2, uv 0.11.21/0.13.5, and setup-uv at exact pinned SHA (retained license in final host root). Commercial modification/distribution is permitted with notices retained in copies; HML copies none of their implementation source. Existing dependency licenses/provenance are unchanged. No external exercise reference, new asset or pose material was used.

## Findings

**No open findings.**

| ID | Severity when found | Requirement/scenario | Evidence and resolution | Suggested direction |
|---|---|---|---|---|
| R1 | blocker | CI host contract / clean-checkout job | Initial hosted job failed Linux process tests. Architect design §5a and candidate 3dc9126 correction pass independent final suites and hosted run 39980051076. CLOSED. | Preserve fail-closed group observation and classifier regression coverage. |
| R2 | minor | Host checks retain behavior / regression checks | Initial new malformed-snapshot fixture passed CompletedProcess as mock side_effect, causing TypeError. Developer corrected fixture before final candidate; all three regression methods and independent matrix pass. CLOSED. | Keep snapshot return values distinct from simulated exceptions. |

## Cleanup and retained evidence

Reviewer cleanup is complete: **239,451,106 file/symlink bytes removed** across both revisions (no symlink target followed). `cleanup.json` in the final host root records exact current removal paths/bytes and retained dependency checks. Earlier cleanup removed the first DNS-failed host root plus initial temporary environments/caches/fixtures: 69,023,819 bytes. Final cleanup removed superseded R1 accepted host/reference/negative whole roots and R2 temporary environments/caches: 170,427,287 bytes. Unique baseline supplemental evidence was explicitly labeled and retained before removing obsolete runs; no obsolete native duplicate or temporary environment remains.

Retained direct children and reasons:

- `build/upgrade-host-python-314_r2_reviewer_try-1_host/`: final host/CI/classifier evidence and synthetic receipt closure, plus labeled unique baseline supplemental checks. **24 receipts / 48 required log/success-output references**, all present.
- `build/upgrade-host-python-314_r2_reviewer_try-1_negative/`: final explicit unsupported-interpreter rejection evidence.
- `build/upgrade-host-python-314_r2_reviewer_try-1_reference/`: final independent identities, full tests, numeric measurements, fresh source inputs, native blends, fault outputs and complete supervised receipt/output closure. **38 receipts / 98 required references**, all present.

Revisit these retained acceptance dependencies after migration acceptance and an explicit evidence-retention decision. Removed interpreter paths remain historical observations only. Reviewer released all developer/CI roots, never deleted them, and read final owner records: `developer-handoff.md` records 359,435,403 bytes removed with no pending developer cleanup; `ci-handoff.md` records 10,127 controlled-fixture bytes plus 100,835,802 downloaded-failure bytes removed and no pending CI cleanup. Hosted evidence remains at the recorded artifact URLs. Protected history/unrelated roots were untouched. Final evidence-index links and retained receipt dependencies resolve.

## Unverified requirements

None within this change's specified acceptance scope. The conditional human visual gate is inapplicable to this final diff. No anatomical visual approval or archive action is granted by this review.
