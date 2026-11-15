# Tasks

## 1. Publish the locally created tag

- [x] 1.1 Replace the GitHub ref writer with a local tag and single non-forced push in the release helper. Use a disposable bare Git remote to verify the exact ref and target, rejected push, same-commit reuse, and preservation of conflicting tags and other refs.
- [x] 1.2 Prepare and verify drafts for the pushed tag using the release ID. Exercise the publisher with a controlled Releases API that exposes a temporary tag name if a draft is created too early. Verify push precedes draft creation, no release writes follow a rejected push, and an interrupted publication resumes with the original wheel and checksum.
- [x] 1.3 Use the existing publish job checkout and job credential, update `tools/README.md`, and register any new external references used in `docs/used-materials.md`. Verify the checkout, write permissions, main-only eligibility and prior build and test dependencies in the workflow tests.

## 2. Verify and review

- [ ] 2.1 Record visual gates as not applicable and complete the joint candidate audit. Run strict OpenSpec validation and the focused release and workflow suites against the recorded source. Use separate fresh direct-child run roots under `build/` matching `push-release-tags-from-local-checkout_<revision>_<role>_<attempt>_<kind>/`. Record the independent review and cleanup outcome.
- [x] 2.2 Inspect the failed `0.3.1` publication read-only and record whether its original tested artifact, commit, tag state and draft evidence support the recovery described in the design.

## Workflow follow-up

- Verify the first intentional version increase with the new workflow by recording the checked commit, tag, release and wheel checksum. A one-off recovery of `0.3.1` is a separate operator action.
