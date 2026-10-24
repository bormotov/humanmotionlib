# Developer hand-off

## Approved scope

Human gate 1 was approved by the user's explicit `$openspec-apply-change package-humanmotionlib` invocation. During this implementation, the user also approved replacing the proposed setuptools pin `80.9.0` with `83.0.0` after the architect identified the former's GHSA-h35f-9h28-mq5c / CVE-2026-59890 issue. The intended installed import namespace remains `humanmotionlib.*`; the installed console command is `hml`.

## Pre-migration baseline

Captured before implementation edits at commit `b9dc38d74b60e839e41446a1e08264f5153cb34c` on Darwin arm64 with host CPython 3.14.6 and Blender 5.2.2 LTS build `d13f752e3b9c`. MPFB and Rigify were not used. The coordinated run roots are:

- `build/package-humanmotionlib_r1_dev_try-1_baseline/` — prepared input, evaluated build, backend receipts, source hashes and numeric evidence.
- `build/package-humanmotionlib_r1_dev_try-1_baseline-pack/` — two clean render passes and focused comparison media. It is a sibling because existing supervision requires input and output roots to be disjoint.

The full source validator passed: 180 structures, 67 actions, 3 placements and 32 fixtures. The focused input contains `neutral`, `rest` and all 29 samples of `arm-raise`; the build completed at `script_complete`. All 31 evaluated body-transform checks passed. The general collection verifier also ran, but its top-level result is `fail` solely because its full-fixture coverage check expects the entire 32-fixture set; it reports the intentional focused subset as 3/32. This is retained as a scope limitation and is not reported as a full collection pass.

The review pack's decoded clean-pass comparison passed all 76 image comparisons. GIF timing passed for front and side previews at 60, 120 and 180 BPM. The pack contains 223 readable PNGs and 6 readable GIFs. The `arm-raise` timing audit passed: 5 intervals/beat and 21 samples at 60 BPM, 3 intervals/beat and 13 samples at 120 BPM, and 3 intervals/beat and 13 samples at 180 BPM. Each plan contains five static count samples; maximum animation intervals are at most 200 ms.

Evidence and source/implementation hashes are in `build/package-humanmotionlib_r1_dev_try-1_baseline/evidence/baseline-evidence.json`; individual source validation, evaluated transform and collection-verifier reports are beside it. The review pack contains `render-repeatability.json`, `gif-timing.json`, `sample-timing.json`, fixed-view PNGs, and the two sets of process receipts. All generated media was opened and decoded successfully.

Exact successful commands:

```sh
uv run --locked python tools/validate.py --profile adult-reference-v1
uv run --locked python tools/prepare_skeleton.py --profile adult-reference-v1 --fixtures neutral rest arm-raise --output build/package-humanmotionlib_r1_dev_try-1_baseline/input.json
uv run --locked python tools/run_blender.py --input build/package-humanmotionlib_r1_dev_try-1_baseline/input.json --output build/package-humanmotionlib_r1_dev_try-1_baseline
uv run --locked python tools/verify_skeleton.py --input build/package-humanmotionlib_r1_dev_try-1_baseline --output build/package-humanmotionlib_r1_dev_try-1_baseline/evidence/metrics.json
uv run --locked python tools/review_pack.py --input build/package-humanmotionlib_r1_dev_try-1_baseline --output build/package-humanmotionlib_r1_dev_try-1_baseline-pack
```

The focused evaluated transform report was produced by calling `tools.prepared.read_prepared` and `tools.verify_skeleton.verify_transforms` on the 31 samples in `evaluated.json`. The run used the host's installed uv 0.11.21. This records the tool identity for the pre-migration baseline; implementation and packaging checks were performed later with the approved uv 0.13.5 as described below.

## Implementation and verification

The installed distribution uses `humanmotionlib.*`, the `hml` console command and `python -m humanmotionlib`. The corrected F1/F4 implementation preflights existing render passes before reuse and requires each render receipt's package version, runtime-manifest hash, resource hashes, backend contract hash and implementation hashes to match the active installed package. The receipt also snapshots the selected workspace before child launch. F3 preserves parser arguments for `check-environment`. The active contributor guide uses installed commands; historical `tools/*.py` examples remain only in the explicit migration table.

The latest frozen developer candidate is built with CPython 3.14.6, uv 0.13.5 and setuptools 83.0.0:

- `build/package-humanmotionlib_r1_dev_try-6_wheel/artifacts/humanmotionlib-0.2.0-py3-none-any.whl` — SHA-256 `4953912362473e56d42783b0593f148f1dd70cd25813c65c6f2d8d1c45bf2ed5`.
- `build/package-humanmotionlib_r1_dev_try-6_wheel/artifacts/humanmotionlib-0.2.0.tar.gz` — SHA-256 `dc4b0bc9cfe5342b83686a525bde7b3ce5ec26f36f4eb8b368eb547fbcd33af9`.
- The fresh non-editable wheel environment was used for the installed checks and developer pack, then removed during cleanup; the exact candidate archive remains above.

The candidate installed with all declared runtime dependencies; `hml --version` reported 0.2.0 and `hml check-environment --not-an-option` exited 2. A non-editable external-cwd import confirmed 50 resources/40 implementation modules, no installed `tools` namespace and no eager `bpy` import. Build-adapter, review-pack and CLI focused tests passed 16/16. The focused installed runtime receipt test passed 1/1 under escalated process-group visibility. The shared workspace backend state was safely recovered by the existing supervisor after an escalated liveness check confirmed the prior group had ended; recovery and receipt probes left the slot state finished with no pending cleanup. The temporary try-6 install environment was removed after verification.

Archive verification in `build/package-humanmotionlib_r1_dev_try-2_sdist/archive-audit.json` confirms the try-6 sdist lock/selector closure, no test/tool/history/environment/cache roots, 92 logical wheel members with exact direct/rebuilt payload parity, and manifest closure (50 resources/40 implementation files). The independent reviewer final locked host suite passed 174 tests with zero skips and installed relocation/read-only/corruption audits passed. Developer installed acceptance evidence is in `build/package-humanmotionlib_r1_dev_try-23_build/` and `build/package-humanmotionlib_r1_dev_try-23_pack/`: the focused 31-sample build completed, all 76 repeatability comparisons and six 60/120/180 timing previews passed, and installed render reuse completed without spawning Blender. The collection verifier's top-level status is `fail` solely because this intentionally focused build covers 3/32 fixtures; the 31 body-transform samples and action-coverage checks passed, and this is not represented as a full-collection pass. Reviewer embedded-runtime evidence in `build/package-humanmotionlib_r1_reviewer_try-2_checks/backend-isolation.json` records Blender 5.2.2 LTS build `d13f752e3b9c`, embedded Python 3.13.13 and host CPython 3.14.6, with host `sys.path` unchanged and no neighbor host module visible. Real GitHub Actions runs on commit `e5f36cf` passed: [package run 40049069576](https://github.com/bormotov/humanmotionlib/actions/runs/40049069576) and [host run 40049069483](https://github.com/bormotov/humanmotionlib/actions/runs/40049069483). Reviewer artifact audit `build/package-humanmotionlib_r1_reviewer_try-2_checks/ci-artifact-audit.json` confirms downloaded wheel SHA-256 `6711a6352c2e2c169565fbee0555eab54bf262ff74d822e735960c813dce2938`, all 92 payload-member bytes and 50 resource identities match the local candidate, and installed before/after hashes match the wheel. Human gate 2 remains pending.

## Cleanup

The backend supervisor state was checked after reviewer and developer processes completed: `build/.backend-execution-state.json` is `finished`, invocation `210e754207a6448398b9d7bae3b821aa`, and has no `cleanup_pending`. Before cleanup, developer-owned root links were inventoried without following them; all run roots were real directories, links were internal fixture aliases or Python environment aliases, and no process was active. Tracked-file dependency search found only the try-6 install path in this hand-off; that reference was updated to note its removal. Removed obsolete developer roots: 33 roots totaling 2,037,193,900 bytes of regular-file contents, including superseded wheel/install/check attempts and the try-1 extracted sdist. Symlink targets were not followed or removed. The retained developer roots are:

- `build/package-humanmotionlib_r1_dev_try-1_baseline/` and `...try-1_baseline-pack/` — source and decoded-pixel comparison dependencies.
- `build/package-humanmotionlib_r1_dev_try-2_backend-smoke/` — exact approved build backend/CPython 3.14 synthetic archive smoke evidence.
- `build/package-humanmotionlib_r1_dev_try-2_sdist/` — final direct/rebuilt archive parity and closure audit evidence.
- `build/package-humanmotionlib_r1_dev_try-6_wheel/` — exact verified wheel/sdist candidate and hashes.
- `build/package-humanmotionlib_r1_dev_try-23_build/` and `...try-23_pack/` — developer installed-backend acceptance build, renders and presentation evidence.
- `build/package-humanmotionlib_r1_main_try-1_ci/` — parent-owned downloaded successful Actions artifact, retained for reviewer checksum/identity audit.

Exact removed developer-owned run roots:

```text
build/package-humanmotionlib_r1_dev_try-1_checks/
build/package-humanmotionlib_r1_dev_try-1_install/
build/package-humanmotionlib_r1_dev_try-1_sdist/
build/package-humanmotionlib_r1_dev_try-1_wheel/
build/package-humanmotionlib_r1_dev_try-2_checks/
build/package-humanmotionlib_r1_dev_try-2_install/
build/package-humanmotionlib_r1_dev_try-2_wheel/
build/package-humanmotionlib_r1_dev_try-3_checks/
build/package-humanmotionlib_r1_dev_try-3_install/
build/package-humanmotionlib_r1_dev_try-3_wheel/
build/package-humanmotionlib_r1_dev_try-4_checks/
build/package-humanmotionlib_r1_dev_try-4_install/
build/package-humanmotionlib_r1_dev_try-4_wheel/
build/package-humanmotionlib_r1_dev_try-5_checks/
build/package-humanmotionlib_r1_dev_try-5_install/
build/package-humanmotionlib_r1_dev_try-5_wheel/
build/package-humanmotionlib_r1_dev_try-6_checks/
build/package-humanmotionlib_r1_dev_try-6_install/
build/package-humanmotionlib_r1_dev_try-7_checks/
build/package-humanmotionlib_r1_dev_try-8_checks/
build/package-humanmotionlib_r1_dev_try-9_checks/
build/package-humanmotionlib_r1_dev_try-10_checks/
build/package-humanmotionlib_r1_dev_try-11_checks/
build/package-humanmotionlib_r1_dev_try-12_checks/
build/package-humanmotionlib_r1_dev_try-13_checks/
build/package-humanmotionlib_r1_dev_try-14_checks/
build/package-humanmotionlib_r1_dev_try-15_checks/
build/package-humanmotionlib_r1_dev_try-16_checks/
build/package-humanmotionlib_r1_dev_try-17_checks/
build/package-humanmotionlib_r1_dev_try-18_checks/
build/package-humanmotionlib_r1_dev_try-20_checks/
build/package-humanmotionlib_r1_dev_try-21_checks/
build/package-humanmotionlib_r1_dev_try-22_checks/
```

Reviewer-owned runs remain untouched by developer cleanup. After cleanup, retained paths still exist, removed run-root paths resolve nowhere, and no tracked file refers to a removed developer path. The reviewer reports technical review and cleanup complete with verdict PASS WITH NOTES; only explicit Human gate 2 visual approval remains pending.

## Reviewer hand-off

Candidate try-6 and its hashes were supplied to the parent/reviewer for independent replay. Real CI, downloaded wheel checksum/identity audit, technical review and reviewer cleanup are complete; only Human gate 2 approval remains pending.
