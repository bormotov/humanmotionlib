# Developer hand-off

## Approval and baseline

- Human gate 1: approved by the user's explicit `$openspec-apply-change public-python-generation-api` request after the proposal/specification was presented.
- Change/source identity before implementation: `public-python-generation-api`; repository HEAD `b86ab77efc13b2c1ec89f1ae9f0a5709d5286164`; `openspec validate public-python-generation-api` passed.
- Host: CPython 3.14.6, Darwin arm64. Backend: Blender 5.2.2 LTS, build `d13f752e3b9c`, Darwin arm64. MPFB and Rigify are not used.
- Existing CLI baseline commands:
  ```sh
  python -m humanmotionlib --workspace "$PWD" prepare-skeleton --profile adult-reference-v1 --stature 1.70 --fixtures neutral rest arm-raise --output build/public-python-generation-api_r1_dev_try-2_baseline-prepare/input.json
  python -m humanmotionlib --workspace "$PWD" run-blender --input build/public-python-generation-api_r1_dev_try-2_baseline-prepare/input.json --output build/public-python-generation-api_r1_dev_try-3_baseline-render --render-dir build/public-python-generation-api_r1_dev_try-3_baseline-render/frames
  ```
- Baseline preparation: `build/public-python-generation-api_r1_dev_try-2_baseline-prepare/`; 31 samples across neutral/rest/arm-raise; 51 source hashes; prepared SHA256 `196470f5c6ee930b62cdd85d41fcb2d1e3a16262f0b53cbf06f3c8826c9262d0`.
- Baseline render: `build/public-python-generation-api_r1_dev_try-3_baseline-render/`; supervised receipt state `succeeded`; prepared hash matched; 31 evaluated samples; all 76 expected manifest images passed decoding and supervisor output validation. Run metadata records the pinned backend identity.
- First render attempt (`build/public-python-generation-api_r1_dev_try-2_baseline-render/`) failed during the version probe under the sandbox with `orphaned-descendant` / cleanup-pending evidence. A privileged process inventory confirmed its recorded process group absent; the next fresh attempt recovered the slot and passed. Reconsider/remove this diagnostic root after reviewer hand-off confirms no dependency remains.

## Materials and limits

- No new external text, dataset, example, asset or anatomical reference was used to inform or author content. Work used repository sources and the already-pinned Blender executable to produce baseline outputs. Existing source attribution and `docs/used-materials.md` remain unchanged.
- No new anatomical claims were introduced.

## Final candidate and verification

- Frozen runtime manifest SHA256: `6ba4bc665af9902dcbcf7c87e9e03707337e0dc65089225749662362756f1d56`.
- Candidate wheel: `build/public-python-generation-api_r1_dev_try-1_distribution/dist/humanmotionlib-0.2.0-py3-none-any.whl`, SHA256 `c6e44fb366193ce615acc727708f25e91f603027413619d2429b2ec2af808907`, 246,464 bytes. Candidate sdist: `build/public-python-generation-api_r1_dev_try-1_distribution/dist/humanmotionlib-0.2.0.tar.gz`, SHA256 `b4e8bd55bab06502edf5cc6ce71793b88c66573e485ec1e2b6e6e05e7598dfc9`, 204,057 bytes. Inventory: `build/public-python-generation-api_r1_dev_try-1_distribution/distribution-inventory.json` (102 wheel files, 122 sdist entries; API, host-only render-contract module, packaged docs, data and licenses present; no `tools` namespace; existing four runtime dependencies unchanged).
- Public API render: `build/public-python-generation-api_r1_dev_try-3_api-prepare/` and `build/public-python-generation-api_r1_dev_try-3_api-render/`. It prepared `neutral`, `rest` and `arm-raise` at H=1.70 m and 60/120/180 BPM, then returned 31 pose samples, 18 timelines and 76 readable images. Receipt `build/public-python-generation-api_r1_dev_try-3_api-render/processes/501c18f5181740f88758ec88ca5bc891/outcome.json` records success, Blender 5.2.2 LTS build `d13f752e3b9c`, 31 evaluated samples, 76 decoded image outputs and confirmed cleanup. The structured result JSON is in each run root. Baseline/API prepared `samples`, `sampling`, `sources`, `units` and `limitations` are identical; only package identity and source hashes changed with the implementation.
- Final locked host check used `HUMANMOTIONLIB_TEST_RUN_ROOT="$PWD/build/public-python-generation-api_r1_dev_try-10_host" HUMANMOTIONLIB_SOURCE_ROOT="$PWD" uv run --locked --offline --no-sync python -m humanmotionlib.check_host --test-root "$PWD/tests"`: 204 selected, 204 passed, 0 skipped. The only exclusions remain the six real-backend tests in `tests.test_blender_backend` and the single real-pipeline fault test in `tests.test_pipeline_faults`.
- Installed acceptance used the candidate wheel non-editably in `build/public-python-generation-api_r1_dev_try-1_installed-host/environment` from CPython 3.14.6, outside-checkout workspace `/private/tmp/build/public-python-generation-api_r1_dev_try-1_installed-workspace`; evidence is `build/public-python-generation-api_r1_dev_try-1_installed-host/installed-acceptance.json`. It reports source validation pass (180 structures, 67 actions, 3 placements, 32 fixtures), numeric host verification pass (900 samples), public preparation/serialization, structured missing-Blender failure, CLI parity, read-only installation and workspace-contained writes. The acceptance scope explicitly excludes a real Blender render; the public API render above supplies that separate developer evidence.
- OpenSpec validation passed after task updates. Reviewer-owned tasks 5.1–5.7 and Human gate 2 remain unchecked.

## Cleanup and retained dependencies

- Removed obsolete developer roots: `try-1_api-prepare` (5,944,061 bytes), `try-1_api-render` (107,863,779), `try-2_api-prepare` (5,944,061), failed `try-2_baseline-render` (14,387), and host attempts `try-3_host` (199,341), `try-4_host` (315,238), `try-5_host` (0), `try-6_host` (0), `try-7_host` (0), `try-8_host` (315,238) and `try-9_host` (0), all under `build/public-python-generation-api_r1_dev_`. Total regular-file bytes removed: 120,596,105 across 367 files. Six symlink entries in removed host-test roots were unlinked without following their targets. Each removed root was confirmed absent afterward.
- The failed baseline receipt recorded PGID 66309 and `cleanup_pending`; a privileged process-table check later found no rows for PGID 66309 or the stale repository ownership PGID 67551, and the ordinary supervised slot was subsequently recovered and finished. The failed baseline root was removed only after that absence check and the independent successful baseline render were retained.
- Retained baseline comparison roots: `build/public-python-generation-api_r1_dev_try-2_baseline-prepare/` (5,943,962 bytes) and successful `build/public-python-generation-api_r1_dev_try-3_baseline-render/` (107,864,564 bytes). Retained API evidence: `try-3_api-prepare` (8,302,879 bytes) and `try-3_api-render` (110,419,071 bytes). Retained final host evidence: `try-10_host` (318,064 bytes; two test symlinks retained as test fixtures and never followed). Retained distribution and installed acceptance roots: `try-1_distribution` (451,696 bytes), `try-1_installed-host` (19,852,530 bytes), and its external installed workspace (801,044,576 bytes).
- `build/public-python-generation-api_r1_dev_try-2_host/` (51,938,913 bytes) remains the sealed noneditable environment/cache dependency for baseline, API and host receipts whose backend commands reference its installed `build_skeleton.py`; it was also the reviewer static-test environment. Reconsider removal after independent review and receipt dependencies end. The installed acceptance workspace remains protected by its machine-readable report and should be reconsidered after reviewer hand-off. No developer cleanup action remains pending.
- A bounded process-table scan found no active Blender/HML/host-suite process; its only filtered matches were the `ps`/`rg` commands themselves. No symlink targets were followed during inventories or cleanup. The existing ignored checkout `.venv` was left untouched because its ownership predates and is unrelated to these named build runs.

## Pending reviewer / human gates

- Independent reviewer owns tasks 5.1–5.6 and its separate run roots.
- Human Gate 2 was explicitly approved by the human on 2026-10-24 after reviewing the focused pack; no visual errors were reported. The decision is recorded in `review.md` separately from generation and numeric success.
