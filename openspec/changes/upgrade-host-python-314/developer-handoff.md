# Developer hand-off

## Implementation

The host project now requires CPython `>=3.14,<3.15`; `.python-version` selects
`3.14`. Blender remains pinned to 5.2.2 LTS (`d13f752e3b9c`, Darwin arm64),
and its embedded interpreter is checked separately. `uv.lock` was regenerated
with uv 0.11.21 without a blanket upgrade. The direct dependency versions are
unchanged: attrs 26.1.0, jsonschema 4.26.0, jsonschema-specifications
2025.9.1, Pillow 12.3.0, PyYAML 6.0.3, referencing 0.37.0 and rpds-py
2026.9.1. The Python-3.14 resolution no longer includes transitive
typing-extensions 4.16.0; `referencing` does not require it on this target.

Added `tools/check_host.py` and focused host-check tests. The runner verifies
the actual interpreter and project metadata, checks direct dependency imports,
discovers all tests and excludes only the two declared real-backend modules.
The local sequence and Blender/host distinction are documented in
`tools/README.md`. The CI workflow and its source/licensing register entries
were supplied by the CI owner.

## Host validation

The final corrected run uses a fresh CPython 3.14.6 environment in
`build/upgrade-host-python-314_r2_dev_try-2_host/`. Lock check, locked offline
sync, `uv pip check` (7 packages), `tools/check_host.py --check-environment`,
direct imports and canonical source validation passed. Validation reported 180
structures, 67 actions, 3 placements and 32 fixtures. The r2 focused
classifier matrix passed 3/3 methods across Darwin/Linux (including all 26
subcases). The negative locked sync in
`build/upgrade-host-python-314_r1_dev_try-1_negative/` rejected Python 3.12.13;
metadata checks accept 3.14 and reject 3.12, 3.13 and 3.15.

The first hosted Ubuntu 24.04 / CPython 3.14.8 job passed setup, lock,
dependency checks and source validation, then exposed a Linux portability bug
in existing process supervision. With `waitid(WNOWAIT)`, the completed leader
remains a zombie as a PGID anchor; Linux `killpg(pgid, 0)` still reports the
zombie group as present. Ordinary exits were consequently called
`orphaned-descendant`, and output validation did not run. The exact failing
run is [GitHub Actions run 39977052957](https://github.com/bormotov/humanmotionlib/actions/runs/39977052957),
with the CI-owned artifact in
`build/upgrade-host-python-314_r1_ci_try-3_hosted-failure/`. This was the
observed compatibility gap; no test or tolerance was changed.

The approved correction extends the existing bounded `ps` snapshot
classification from Darwin to Linux. Zombie-only groups are absent; a live
member is present; missing anchor, malformed/unreadable/timed-out snapshot or
unconfirmed empty group remains ambiguous. `EPERM` is not absence. The WNOWAIT
anchor, cleanup order, timeout budgets, lock behavior and output checks are
unchanged. The sandboxed try-3 failure and a first r2 focused-test mock error
were both summarized and their obsolete runs removed; neither indicates a
runtime compatibility defect. Hosted retry
[39980051076](https://github.com/bormotov/humanmotionlib/actions/runs/39980051076)
passed on the corrected candidate; exact candidate and interpreter details are
in `ci-handoff.md`.

The corrected r2 Darwin host-only suite passed all 163 selected tests in
90.679 seconds, 0 skips, and only the named 6+1 backend exclusions. Its
setup hashes before and after preflight match those below. The complete
unfiltered reference suite passed all 170 tests in 437.702 seconds with 0
skips. The reviewer independently reported its r2 classifier truth-table tests
passing; final independent full-suite verification is in progress.

## Reference platform and visual impact

The final successful reference run is
`build/upgrade-host-python-314_r2_dev_try-1_reference/`. Its bounded supervised
probe reported host CPython 3.14.6 from the run environment and Blender 5.2.2
LTS build `d13f752e3b9c` embedding CPython 3.13.13 from Blender's own
`/Applications/Blender.app/Contents/Resources/5.2/python` prefix. The probe
removed host `PYTHON*`, `UV_*` and `VIRTUAL_ENV` variables from the Blender
child and verified no host environment or venv path appeared in its report.

The complete unfiltered `uv run --locked python -m unittest discover -s tests`
passed on Darwin arm64 in this r2 run: 170 tests in 437.702 seconds, 0 skips. This
includes all 6 real-backend tests and the scene-fault test; no exclusions were
applied. The run has 38 supervised invocation receipts, including successful
version probes and real builds/fault harness, expected failed negative tests,
and the deliberately unfinished parent-death receipt. There are no
`cleanup_pending` receipts; the two queued-cancellation tests confirm cleanup.
All backend outputs validate and builds reach `script_complete`. The full test
log, embedded identity JSON, probe receipts, process logs and generated
outputs provide the evidence. No Blender-shared Python module needed a
compatibility change.

No visual data, rendering, scene or shared numeric behavior changed; the
migration is configuration and host-check tooling only, so no new visual pack
is indicated. Human visual approval is not applicable to the current diff.

## Setup integrity, materials and cleanup

The r2 host and reference setup hashes before/after checks match:

| File | SHA-256 |
|---|---|
| `pyproject.toml` | `a91558939f1d25589c900c1dac77b066bbe2d124f719ab4b932a48e9560a48f9` |
| `.python-version` | `a876e0b10411037a012498b9fe18d9bc1df32ed8b722a13564dc944ddcfd9135` |
| `uv.lock` | `73f5da418577394cc68c3a1ee31deb693782bf11cf1ef6cbc81ae960c2854179` |

All externally sourced action and uv materials used are listed in
`docs/used-materials.md`, with commercial-use permissions and license evidence
checked 2026-10-23. No external exercise or pose references were used.

Cleanup before CI follow-up:

| Removed developer path | Recorded bytes | Reason |
|---|---:|---|
| `build/upgrade-host-python-314_r1_dev_try-1_host/` | 33,032,441 | Lost-handle attempt; replaced by the passing try-4 host run. |
| `build/upgrade-host-python-314_r1_dev_try-1_lock/` | 5,859,196 | Lock result retained in change record and try-4 lock check. |
| `build/upgrade-host-python-314_r1_dev_try-2_host/` | 35,232 | Failed DNS setup attempt; superseded by clean try-4 setup. |
| `build/upgrade-host-python-314_r1_dev_try-1_reference/` | 15,810,025 | Probe launcher failed before Blender launch; corrected and rerun in try-2. |
| `build/upgrade-host-python-314_r1_dev_try-3_host/` | 33,070,122 | Resolved sandbox process-observation failure; escalated try-4 passed. |
| try-4 host `environment/` and `cache/` | 33,005,940 | Temporary runtime/cache removed after recording the successful logs and hashes. |
| try-2 reference `environment/` and `cache/` | 33,004,183 | Temporary runtime/cache removed after recording full backend receipts and outputs. |
| superseded r1 try-4 host and try-2 reference roots, plus failed r2 try-1 host root | 139,609,246 | Replaced by corrected r2 host/reference evidence; the focused-test fixture was fixed and rerun. |
| final r2 host `environment/` and `cache/` | 33,002,009 | Removed temporary setup after successful tests and hashes were recorded. |
| final r2 reference `environment/` and `cache/` | 33,007,009 | Removed temporary setup after successful tests and receipts were recorded. |

Total removed entry bytes: 359,435,403. Counts are the sum of `lstat().st_size`
for entries beneath removed paths (including symlink and descendant-directory
entries, excluding each removed root directory's own metadata). Before
deletion, cache symlinks resolved inside their respective run roots; fixture
symlinks resolved to sibling fixture files inside the same root; Python links
resolved to `/opt/homebrew/opt/python@3.14/bin/python3.14`. Removal did not
follow links. The reviewer released all developer roots, and no project files
refer to deleted run outputs as inputs. Post-cleanup inventory retains only
`build/upgrade-host-python-314_r1_dev_try-1_negative/` (unsupported-version
rejection evidence), `build/upgrade-host-python-314_r2_dev_try-2_host/`
(successful host log, validator output and hashes), and
`build/upgrade-host-python-314_r2_dev_try-1_reference/` (successful unfiltered
suite, embedded identity, receipts and generated evidence). The host and
negative roots have no symlinks; the reference root's Blender fixture link
resolves within that root. Environments and caches have been removed. There is
no developer cleanup pending. The CI owner and reviewer are responsible for
their own roots and artifacts.

## Remaining acceptance

- Developer tasks 2.3 and 4.1–4.5 are complete, including developer cleanup.
- Hosted CI has a successful corrected run; the CI owner is recording its
  exact interpreter and check totals in `ci-handoff.md`.
- Independent review tasks 5.x remain with the reviewer.
