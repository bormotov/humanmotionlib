# Developer hand-off

## Unchanged installed baseline

The baseline source is commit `e42d6b19b6f4f96241d91ec9acd4afb18620afd3` (`0.2.0`); the following OpenSpec proposal commit changes planning artifacts only. The exact pre-change wheel is retained at `/private/tmp/hml-portable-runtime-caller-baseline/build/portable-installed-runtime_e42d6b_dev_try-2_baseline/humanmotionlib-0.2.0-py3-none-any.whl`, SHA-256 `4953912362473e56d42783b0593f148f1dd70cd25813c65c6f2d8d1c45bf2ed5`. Its runtime manifest is `695183b3e0de7135ff422c7a1c08972da7484a97e015ec014d09080c7597e026`; all 50 packaged resources and 39 non-generated implementation files match the unchanged source tree. The build-generated `_version.py` is the remaining implementation inventory entry.

The installed baseline ran from `/private/tmp/hml-portable-runtime-caller-baseline/cwd-a` with explicit workspace `/private/tmp/hml-portable-runtime-caller-baseline`. `validate --profile adult-reference-v1` passed with 32 fixtures, 180 structures, 67 actions, and 3 placements. Explicit-workspace preparation of `neutral`, `rest`, and `arm-raise` produced 31 samples with prepared content SHA-256 `db0b56b7704a03d214c2fea6704942642d804e04f841688fc31bdfa481ceb645`.

The unchanged reference backend is Blender `5.2.2 LTS`, build `d13f752e3b9c`, on `Darwin-arm64`; MPFB and Rigify are unused. The protected rendering baseline is `build/package-humanmotionlib_r1_dev_try-23_pack/`, with source build `build/package-humanmotionlib_r1_dev_try-23_build/`. Its package manifest matches the external installed wheel. The protected pack has 259 files and is hashed in the external run's `baseline-evidence.json`; no historical file was changed. The same record retains the package source identities, exact wheel, prepared identity, and backend pins.

The protected pack contains neutral/rest front, rear and side frames and arm-raise front/side static and animation sheets. Its 60/120/180 BPM GIF timing audit passes for all six front/side pairs; maximum duration error is 3.34 ms. Sampling is 5 intervals per beat at 60 BPM and 3 at 120/180 BPM. Two clean passes have exact decoded RGBA equality. The focused numeric report has 1,288 passing checks and one `diagnostic_fixture_coverage` failure because this deliberate three-fixture regression subset does not claim full 32-fixture acceptance; there are no other failed numeric checks. `render-repeatability.json`, `sample-timing.json`, `gif-timing.json`, prepared inputs, build outputs, and every protected pack file are covered by the retained hash inventory.

## Run and cleanup inventory

- Retain `/private/tmp/hml-portable-runtime-caller-baseline/build/portable-installed-runtime_e42d6b_dev_try-2_baseline/` as the exact pre-change wheel, installed validation/preparation logs, prepared input and baseline identity record until reviewer baseline comparison is complete.
- Retain `build/package-humanmotionlib_r1_dev_try-23_build/` and `build/package-humanmotionlib_r1_dev_try-23_pack/` as protected render/numeric comparison dependencies. Their whole-tree file hashes are recorded in the external baseline identity record; these protected inputs remain unchanged.
- The first setup attempt at `/private/tmp/hml-portable-runtime-caller-baseline/build/portable-installed-runtime_e42d6b_dev_try-1_baseline/` failed because log/cache files occupied the prepared run root. It has no dependent outputs and is scheduled for removal after the baseline evidence copy is verified.
- The external uv cache at `/private/tmp/hml-portable-runtime-caller-baseline/build/.uv-cache/` is setup state used to install the retained baseline wheel; it is not an HML run. Remove it after verifying the retained wheel and baseline files are sufficient. No other agent-owned run roots were inspected for cleanup or removed.

Pending cleanup is limited to the failed setup root and install cache above. The hand-off is not complete until those paths are removed or a concrete dependency is recorded.

## Implementation and verification

### Frozen development candidate

The try-4 development wheel was built offline from the integrated working tree:
`build/portable-installed-runtime_e3dcbf_dev_try-4_candidate/artifacts/humanmotionlib-0.2.0-py3-none-any.whl`, SHA-256 `ab4ec683c55d36ce3994a1136439bbc59e3d3cc8b709669713f7d8ada5ab24e4`. It includes the fix allowing validated nested prepared inputs to remain read-only inputs. This is an intermediate candidate; rebuild after any source changes and use the final wheel for CI and independent acceptance.

Verified against extracted wheel contents with a Python 3.14 environment and explicit external caller workspace `/private/tmp/hml-runtime-suite-try4`:

- `tests.test_runtime_workspace`: 4/4 pass in `build/portable-installed-runtime_e3dcbf_dev_try-1_core-tests/` (this initial batch also included the then-failing core supervision tests; its 4 workspace tests passed).
- `tests.test_review_pack_supervision` and `tests.test_review_presentation`: 20/20 pass in `/private/tmp/hml-runtime-suite-try4/build/portable-installed-runtime_e3dcbf_dev_try-1_review-tests/`.
- `tests.test_cli`: 2/2 pass in `/private/tmp/hml-runtime-suite-try4/build/portable-installed-runtime_e3dcbf_dev_try-2_cli-tests/`.
- `tests.test_build_adapter`, `tests.test_prepared_contract`, `tests.test_source_integrity`, and `tests.test_source_schemas`: 23/23 pass in `/private/tmp/hml-runtime-suite-try4/build/portable-installed-runtime_e3dcbf_dev_try-1_data-tests/`.
- `tests.test_blender_bootstrap`: 1/1 pass in `/private/tmp/hml-runtime-suite-try4/build/portable-installed-runtime_e3dcbf_dev_try-1_bootstrap-tests/`.
- The full core supervision/path suite passed 34/34 in 12.713 seconds in `/private/tmp/hml-runtime-suite-try4/build/portable-installed-runtime_e3dcbf_dev_central-1_core-tests/`; complete stdout/stderr are in `core-tests.log`. This was run with actual process-table visibility and the exact try-4 wheel payload. The earlier sandbox-only try-2 run remains a diagnostic failure from restricted process-table visibility and is not counted.

The corrected installed acceptance harness passed against the exact try-4 wheel (SHA above) in `/private/tmp/hml-portable-acceptance-try4/build/portable-installed-runtime_e3dcbf_dev_try-4-acceptance`, caller workspace `/private/tmp/hml-portable-acceptance-try4/workspace`. It verified installed resource origins and read-only package state, validation counts (67 actions, 32 fixtures, 3 placements, 180 structures), 900 prepared samples from two unrelated cwd locations, console/module/direct writer parity, numeric verification, six resource/implementation/prepared/reuse integrity negatives, and unchanged synthetic HTML-only predecessor evidence. Real Blender was not run by this host acceptance.

Actual candidate CI, the privileged core supervision rerun, and independent reviewer verification remain outstanding.

The final acceptance attempt currently retains its 23 MB evidence run, 762 MB installed caller workspace, and 43 MB copied uv cache under `/private/tmp/hml-portable-acceptance-try4/`. The evidence run and caller venv are retained for reviewer inspection/reproduction until the reviewer has established its own clean install; the cache is setup-only and remains pending removal after dependency checks. No symlinks were found in that acceptance root. No cleanup is claimed complete yet.
