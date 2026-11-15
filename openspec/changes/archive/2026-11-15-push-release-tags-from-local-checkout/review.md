# Review

## Recovery evidence (read-only, preliminary)

- GitHub Actions run [43634934284](https://github.com/bormotov/humanmotionlib/actions/runs/43634934284) checked commit `a13ae579002344908c3c0c59446ab9a1d44c864b`. Its build, wheel installation, host tests and character installation tests succeeded; the publication step failed.
- The original build artifact `14130130571` was available and unexpired during review, with expiry `2026-11-21T19:58:22Z`. Downloaded wheel `humanmotionlib-0.3.1-py3-none-any.whl` independently hashes to `de789b7fc594cf03925173e20a6e4e23f1ba360c4b6037bd1c2f1adb9d28859a`; its included `wheel.sha256` contains that filename and digest.
- Draft release `445697550` remains unpublished, has temporary tag `untagged-feae9e41217729dcc2af`, and targets the same commit. Its notes name the same run, commit and wheel digest. GitHub reports the draft wheel asset digest as the same SHA-256, and the `SHA256SUMS` asset digest as `8a16443f133b24f92693ccebd565f58fc975cb64ea951734ed832fff2340d697`, matching the downloaded original `wheel.sha256` bytes.
- `git ls-remote --tags origin refs/tags/v0.3.1` returned no ref. The available evidence supports preparing a separate, explicitly reviewed recovery for the original wheel; it does not itself authorize a tag push or publication. Recheck the live state and artifact availability before that operation.
- Reviewer-owned downloaded evidence root `build/push-release-tags-from-local-checkout_r1_reviewer_try-1_recovery/` was removed after process, open-file and containment checks; 389,120 allocated bytes removed, no pending cleanup for this run.

This is not a verdict on the implementation, which was under development during this read-only inspection.

## Independent implementation review

Verdict: **PASS WITH NOTES**; no blocking findings in the reviewed scope. This change only affects CI and release tooling, so visual gates do not apply.

| Requirement or scenario | Check and result |
| --- | --- |
| Publish a verified wheel | Automated focused publisher tests passed; they exercise a local tag push, draft creation after the tag, and the checked wheel and checksum. |
| Stop on failed verification | Automated artifact and workflow tests passed for failure and identity gates. |
| Stop when the tag push is rejected | Automated disposable-remote rejection test passed with no release writes. |
| Reconcile matching and conflicting identities | Automated same-commit retry and conflict tests passed. |
| Retry after pushing the tag | Automated interruption and resume test passed with the original wheel and checksum. |
| Reconsider a version after waiting to publish | Automated prior-publication and stale-candidate tests passed. |

The focused independent suite ran from a fresh reviewer-owned source copy and CPython 3.14.6 environment: `tests.test_release tests.test_github_actions_workflows`, **55 tests passed** in 24.610 seconds. Installation and `uv pip check` passed; package and dependency imports resolved inside the reviewer environment; only the standard `_virtualenv.pth` was present. The source identities at review matched the pre-freeze record: `tools/release.py` SHA-256 `21e85ab6dd3a7f352eb4e59c78981463e7d37d1f69f1e36141e55a3103997075`; `tests/test_release.py` `da0afd57378cadc2276ff5ca7c14e9c935fa5cd4b55a6245a2569bf486d6b384`; workflow test `8cd8c0410e263d0d9f089a3a5dedd98108db860a323ad6b68928752e7c8b082e`; `package.yml` `407b4fcf8048542bc78e400a6d54b11ebe0fdaf5aad943a356b1f1d9a0e74abe`.

The positive publisher fixture uses `target_commitish=main` with an existing tag, and succeeds. The remote-tag movement fixture changes the tag after upload; publication rejects it before changing the draft to published. The actual new GitHub publication path has not yet run; the `0.3.1` recovery above is a separate operation.

Reviewer root `build/push-release-tags-from-local-checkout_r1_reviewer_try-1_checks/` was removed after process, open-file and containment checks; 39,040 KiB allocated before removal, no pending reviewer cleanup for this run.
