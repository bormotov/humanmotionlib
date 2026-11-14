# Preliminary independent review

Verdict: **INCOMPLETE**. Focused local checks passed; integrated and hosted verification, publication handoff, final source/package identity and cleanup have not been independently verified.

## Scope and identity

- Nonvisual change: early and final visual gates are not applicable.
- Reviewer built a wheel from a source copy in `build/publish-releases-from-version-bumps_r1_reviewer_try-1_checks/source/`: `humanmotionlib-0.3.0-py3-none-any.whl`, SHA-256 `03bc7682673c28857739ef3a7096709902b71b9c1a519470149038495addbe93`.
- At the time of the focused test, the copied `tools/release.py`, `tests/test_release.py` and `.github/workflows/package.yml` matched their working-tree counterparts by SHA-256. The source was not a frozen commit; no identity is inferred for later modifications.
- The repeat run used a new uv-created CPython 3.14.6 environment in `build/publish-releases-from-version-bumps_r1_reviewer_try-2_checks/environment/`, the reviewer-built wheel, a reviewer-owned cache and an absolute interpreter path. `uv pip check` reported all eight installed packages compatible. Import origins, interpreter paths, dependency versions and `.pth` contents are recorded in `environment-audit.txt` in that run root.
- `tests.test_release` and `tests.test_github_actions_workflows`: **51 passed** in 20.331 s, without the relative-interpreter warning from the preliminary first attempt. The second run log is `build/publish-releases-from-version-bumps_r1_reviewer_try-2_checks/focused-tests.log`.

## Requirement checklist

- Host runtime and installed wheel scenarios: automatable; focused handoff and failure controls passed. Full installed host and character suites for this candidate remain pending.
- Build/upload, isolated installation and original-artifact retry scenarios: automatable; workflow dependency and artifact identity are inspected structurally, and shell controls cover wrong name/hash, install failure and a failing host test. Hosted upload failure and downstream rerun have not been independently reproduced.
- Main version-bump eligibility and no-publication cases: automatable; synthetic Git-history and event tests passed locally. Actual hosted `main` event remains unverified.
- Published archive attribution and bootstrap boundary: automatable; synthetic tests include published A/B/C removal and restoration and bootstrap removal/restoration, and passed locally.
- Checked wheel publication, immutable identities, collision handling and denied writes: automatable; local controlled release-state tests passed. Actual GitHub Release creation was not attempted.
- Permissions, evidence, external material clearance and cleanup: automatable/document inspection; final independent verification remains pending. Reviewer-owned try-1 and try-2 roots remain present; cleanup and removed-byte accounting are pending.

## Findings and limitations

No new blocking defect was established in the focused repeat. Previous bootstrap archive restoration defect has a regression test that passed. The first run used a noncanonical relative interpreter path and emitted `sys.prefix` warnings; the repeat used an absolute path and passed without those warnings. These checks do not establish final acceptance or successful publication.
