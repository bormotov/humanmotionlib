# Handoff

Early visual gate: not applicable; this change concerns release tooling only.

The joint pre-freeze audit covered the approved publication scenarios, Git tag and push behavior, artifact identity, retries, workflow permissions, documentation and recovery evidence. Architect findings concerning `target_commitish` and a moved remote tag were resolved and covered by focused tests. The developer reported 55 focused tests passing; independent review remains pending.

Frozen source identities (SHA-256):

- `tools/release.py`: `21e85ab6dd3a7f352eb4e59c78981463e7d37d1f69f1e36141e55a3103997075`
- `tests/test_release.py`: `da0afd57378cadc2276ff5ca7c14e9c935fa5cd4b55a6245a2569bf486d6b384`
- `tests/test_github_actions_workflows.py`: `8cd8c0410e263d0d9f089a3a5dedd98108db860a323ad6b68928752e7c8b082e`
- `.github/workflows/package.yml`: `407b4fcf8048542bc78e400a6d54b11ebe0fdaf5aad943a356b1f1d9a0e74abe`
- `tools/README.md`: `711afbe3045b21227ee821ca4964a9cb079aaf844aaf04508a3a23c024f2f1ce`
- `docs/used-materials.md`: `803ff0ebf3ad8ca9ebe9b40d8d45875e44df247c227757db4884a832b3deda32`

The original 0.3.1 artifact and draft were inspected read-only. No production tag or release was modified. Actual release recovery remains a separate operator action.

Developer run cleanup: removal was interrupted before completion. A follow-up
inspection found all seven run roots still present; no run root is recorded as
removed. Sizes reported by `du -sk` (filesystem usage in KiB):

- `build/push-release-tags-from-local-checkout_r1_dev_try-1_focused-tests/` — 18,792 KiB
- `build/push-release-tags-from-local-checkout_r1_dev_try-2_focused-tests/` — 11,840 KiB
- `build/push-release-tags-from-local-checkout_r1_dev_try-3_focused-tests/` — 11,836 KiB
- `build/push-release-tags-from-local-checkout_r1_dev_try-4_focused-tests/` — 11,836 KiB
- `build/push-release-tags-from-local-checkout_r1_dev_try-5_focused-tests/` — 12,000 KiB
- `build/push-release-tags-from-local-checkout_r1_dev_try-6_focused-tests/` — 12,400 KiB
- `build/push-release-tags-from-local-checkout_r1_dev_try-7_focused-tests/` — 12,800 KiB

Cleanup remains pending. The test process was confirmed absent and all seven
resolved paths were direct children of this checkout's `build/`; no active
test process was visible before the interrupted removal.
