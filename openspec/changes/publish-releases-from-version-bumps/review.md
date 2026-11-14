# Independent review

Verdict: **PASS WITH NOTES** for the reviewed candidate and the evidence described below. Production release creation remains a later version-bump operation; the legacy publisher must be confirmed inactive at cutover.

## Scope and identity

- Nonvisual change: early and final visual gates are not applicable.
- Reviewer built a wheel from a source copy in `build/publish-releases-from-version-bumps_r1_reviewer_try-1_checks/source/`: `humanmotionlib-0.3.0-py3-none-any.whl`, SHA-256 `03bc7682673c28857739ef3a7096709902b71b9c1a519470149038495addbe93`.
- At the time of the focused test, the copied `tools/release.py`, `tests/test_release.py` and `.github/workflows/package.yml` matched their working-tree counterparts by SHA-256. The source was not a frozen commit; no identity is inferred for later modifications.
- The repeat run used a new uv-created CPython 3.14.6 environment in `build/publish-releases-from-version-bumps_r1_reviewer_try-2_checks/environment/`, the reviewer-built wheel, a reviewer-owned cache and an absolute interpreter path. `uv pip check` reported all eight installed packages compatible. Import origins, interpreter paths, dependency versions and `.pth` contents are recorded in `environment-audit.txt` in that run root.
- `tests.test_release` and `tests.test_github_actions_workflows`: **51 passed** in 20.331 s, without the relative-interpreter warning from the preliminary first attempt. The second run log is `build/publish-releases-from-version-bumps_r1_reviewer_try-2_checks/focused-tests.log`.

## Requirement checklist

- Host runtime and installed wheel scenarios: automatable; focused handoff and failure controls passed. Full installed host and character suites passed in the hosted candidate run described below.
- Build/upload, isolated installation and original-artifact retry scenarios: automatable; workflow dependency and artifact identity are inspected structurally, and shell controls cover wrong name/hash, install failure and a failing host test. Hosted upload failure and downstream rerun have not been independently reproduced.
- Main version-bump eligibility and no-publication cases: automatable; synthetic Git-history and event tests passed locally. Actual hosted `main` event remains unverified.
- Published archive attribution and bootstrap boundary: automatable; synthetic tests include published A/B/C removal and restoration and bootstrap removal/restoration, and passed locally.
- Checked wheel publication, immutable identities, collision handling and denied writes: automatable; local controlled release-state tests passed. Actual GitHub Release creation was not attempted.
- Permissions, evidence, external material clearance and cleanup: inspected as described below. Reviewer-owned try-1 and try-2 roots were removed and their allocated sizes recorded below.

## Findings and limitations

No new blocking defect was established in the focused repeat. Previous bootstrap archive restoration defect has a regression test that passed. The first run used a noncanonical relative interpreter path and emitted `sys.prefix` warnings; the repeat used an absolute path and passed without those warnings. These checks do not establish final acceptance or successful publication.

## Hosted evidence follow-up

Independently inspected GitHub Actions run [43591485884](https://github.com/bormotov/humanmotionlib/actions/runs/43591485884), which completed successfully for branch `codex/release-pipeline-control` and commit `9196ce5f914054d3dc0b3ee59b57f7b5af97c6b3`. The build and test logs both identify `humanmotionlib-0.3.0-py3-none-any.whl` with SHA-256 `eec21c0fd323c55c6491fd51f529bf1e049bba867c73f1488e998a38a6987df6`. Upload, download and installation succeeded. The host suite reported 553 tests, eight skipped; character installation reported seven tests and its step succeeded. The publication job was skipped on the non-main branch. This hosted wheel is distinct from the locally built wheels above; their evidence is not interchangeable.

The branch run does not exercise an actual GitHub Release. Release scenarios and handoff failures were covered by the focused controlled tests described above. The separate full local verification is documented in the hand-off and was not independently rerun in this review. The approved design reserves real publication for a later authorized version increase, so it is not a prerequisite to merging this change.

An independently inspected negative GitHub Actions run [43608671109](https://github.com/bormotov/humanmotionlib/actions/runs/43608671109) used temporary commit `54fd09cfab668d49d968935b95ad5e4638bf7a91` with an intentionally missing upload path. The build succeeded, `upload-artifact` failed with `if-no-files-found: error`, and the test and publication jobs were skipped. This was a modified control on a non-main branch, not the unchanged candidate or a main publication attempt. The remote control branch no longer exists. Failure of the build itself and overlapping pushes were not separately reproduced in this control.

Reviewer cleanup: after verifying both roots resolved beneath the checkout's build directory and checking open files with elevated `lsof`, removed `build/publish-releases-from-version-bumps_r1_reviewer_try-1_checks` (68,648,960 allocated bytes) and `build/publish-releases-from-version-bumps_r1_reviewer_try-2_checks` (60,252,160 allocated bytes). No other areas were removed. Cutover confirmation remains necessary before enabling publication.

## Permissions and source clearance

Reviewed the candidate workflow permissions: workflow default is `contents: read`; only `publish` requests `contents: write` and `actions: read`, and it depends on build and tests and is conditioned on a main push. The controlled denied-write tests are included in the independently rerun 51 focused tests; actual repository write permissions and the GitHub release lifecycle were not exercised by the branch run.

Inspected the change to `docs/used-materials.md` and the candidate action references. The existing action sources are recorded with MIT terms; the GitHub documentation used for release and concurrency semantics is recorded under CC BY 4.0 with source, license link and attribution. The upstream [GitHub Docs license](https://github.com/github/docs/blob/main/LICENSE), [download-artifact license](https://github.com/actions/download-artifact/blob/v4.3.0/LICENSE), and [upload-artifact license](https://github.com/actions/upload-artifact/blob/v4.6.2/LICENSE) were checked. No copied external source or new visual material was identified in this scope.

The full hosted run is independently inspected evidence for the exact committed candidate, not a fresh reviewer-run full suite. The reviewer independently built and ran the focused release/workflow tests in a fresh environment before the commit; their source-copy identity was recorded above and does not imply a byte-identical wheel. No additional long suite was repeated solely for the review. The missing-build path and overlapping pushes were not separately reproduced in the hosted negative control; job dependencies and per-run artifact naming were inspected, while the actual missing-upload path was exercised. Real Release creation and repository write configuration remain unverified until the first authorized production release.
