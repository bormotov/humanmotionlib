# Tasks

## 1. Build and test one wheel

- [ ] 1.1 Reconcile the existing implementation work with the approved workflow. Bind the package workflow to the triggering push or selected pull-request revision, build one wheel and upload it with its filename and SHA-256. Verify that a missing build or failed upload prevents tests, and that separate pushes cannot select each other's wheel.
- [x] 1.2 Install the received wheel in a fresh supported environment and run the host and character installation suites. Carry over the test build directory, separate caller directory and fixture restoration fixes. Verify that name or checksum mismatch, installation failure and test failure prevent a successful verification result. Confirm the suites still exercise their existing product checks and report their scope.
- [x] 1.3 Reconcile package, workflow and contributor tests with the revised CI contract. Verify that CI has no separate package-version, source-distribution or environment audit gates, and that local package and installed product behavior still follow the applicable specifications.

## 2. Publish from a tested main push

- [x] 2.1 Compare the declared versions from the original main push revisions after successful tests. Verify eligible single- and multi-commit bumps, same-version pushes, downgrades, unavailable predecessors and non-main events without gating ordinary CI.
- [x] 2.2 Wire the write-capable job to successful CI and use the original build artifact. Verify the checked commit, uploaded wheel, checksum and required notes in controlled release state. Cover failed tests or handoff, rerun of a downstream job, already published versions, conflicting tags, and denied writes.
- [x] 2.3 Preserve published history and archive attribution, and retire the legacy triggers and reservation writer. Test the first release boundary, an old unpublished reservation and overlapping publications. Update and check contributor guidance for the version and lock update, retry, and cutover.

## 3. Verify and review the candidate

- [ ] 3.1 Record the nonvisual gate and complete the joint pre-freeze review of the scenarios, documentation and evidence. Freeze the source and wheel identities and verify the recorded commit, filename and checksum agree with the candidate.
- [ ] 3.2 Run the integrated build and installed tests locally and verify the hosted workflow and publication handoff on the frozen candidate in a controlled run. Record the exact run, checked wheel, scope and any publication behavior covered by simulation.
- [ ] 3.3 Independently check the three delta specs, run evidence, permissions and source clearance in the review. Verify cleanup of role-owned run areas under the project path and activity rules, then record removed paths, bytes and pending failures.

## Workflow follow-up

- Follow the repository approval and archive flow after technical review. Confirm cutover has retired the legacy writer before enabling publication.
- When a contributor intentionally commits and pushes the next version to `main`, record the checked commit, workflow run, tag and published wheel checksum from that production release.
