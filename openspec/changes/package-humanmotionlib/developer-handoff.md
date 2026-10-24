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

The focused evaluated transform report was produced by calling `tools.prepared.read_prepared` and `tools.verify_skeleton.verify_transforms` on the 31 samples in `evaluated.json`. The run used the host's installed uv 0.11.21. The required implementation and packaging checks have not started yet.

## Implementation and verification

The installed distribution uses `humanmotionlib.*`, the `hml` console command and `python -m humanmotionlib`. The corrected F1/F4 implementation preflights existing render passes before reuse and requires each render receipt's package version, runtime-manifest hash, resource hashes, backend contract hash and implementation hashes to match the active installed package. The receipt also snapshots the selected workspace before child launch. F3 preserves parser arguments for `check-environment`. The active contributor guide uses installed commands; historical `tools/*.py` examples remain only in the explicit migration table.

The latest frozen developer candidate is built with CPython 3.14.6, uv 0.13.5 and setuptools 83.0.0:

- `build/package-humanmotionlib_r1_dev_try-6_wheel/artifacts/humanmotionlib-0.2.0-py3-none-any.whl` — SHA-256 `4953912362473e56d42783b0593f148f1dd70cd25813c65c6f2d8d1c45bf2ed5`.
- `build/package-humanmotionlib_r1_dev_try-6_wheel/artifacts/humanmotionlib-0.2.0.tar.gz` — SHA-256 `dc4b0bc9cfe5342b83686a525bde7b3ce5ec26f36f4eb8b368eb547fbcd33af9`.
- Fresh wheel environment: `build/package-humanmotionlib_r1_dev_try-6_install/venv/`.

The candidate installs with all declared runtime dependencies; `hml --version` reports 0.2.0 and `hml check-environment --not-an-option` exits 2. The focused installed-wheel review-pack and CLI tests pass 12/12. A broader attempted focused run including `test_runtime` is not accepted as passing: the shared workspace `build/.backend-execution-state.json` was ambiguous, so the runtime cases were blocked before launch; the state was left untouched for ownership/liveness review. This candidate is ready for independent reviewer replay and the actual GitHub Actions run. Final host suite, archive parity replay, installed real-backend review pack, workflow execution, cleanup inventory and review remain pending.

## Cleanup

Pending final developer-owned run inventory and dependency checks. The two baseline roots are retained as comparison dependencies for the reviewer pack. Try-5 and try-6 build/install roots remain available for diagnosis until reviewer dependency checks; obsolete earlier roots and any generated caches still need a full inventory. The ambiguous workspace backend state was not removed or altered. No cleanup is claimed complete.

## Reviewer hand-off

Candidate try-6 and its hashes are supplied to the parent/reviewer for independent replay. Remote CI, final review findings, final cleanup and human gate 2 remain pending.
