## MODIFIED Requirements

### Requirement: Only the checked release wheel is published

Eligible publication SHALL depend on the successful build, upload and required installed tests for the pushed commit. It SHALL publish the verified wheel from that build. The release tag, notes and checksum SHALL identify the checked commit and artifact.

#### Scenario: Publish a verified wheel
- **Verification:** controlled publication with an audit of the local and remote tag, run, wheel filename and checksum.
- **WHEN** an eligible run succeeds and publication receives its original wheel with the expected name and SHA-256
- **THEN** the publisher creates a missing version tag in its local Git checkout at the checked push commit and pushes only that tag to the release repository without force
- **AND** the GitHub Release is prepared against the existing remote version tag, which resolves to the checked push commit
- **AND** the GitHub Release contains the tested wheel and `SHA256SUMS` as uploaded assets
- **AND** its notes identify the included archives and acceptance commits, prior boundary, checked commit and verification run
- **AND** publication uses the received bytes without rebuilding or publishing to a package index.

#### Scenario: Stop on failed verification
- **Verification:** build, upload, test and artifact handoff failure controls.
- **WHEN** a required stage is unsuccessful or the expected wheel is missing or differs by filename or SHA-256
- **THEN** the publisher creates no remote tag and publishes no release.

#### Scenario: Stop when the tag push is rejected
- **Verification:** controlled Git remote rejecting the single tag push.
- **WHEN** Git rejects the version tag push
- **THEN** publication reports the rejection and performs no GitHub Release writes.

### Requirement: Released identities are immutable and retries are safe

Automation SHALL never move a conflicting tag, overwrite a published asset or republish an existing version. Reruns SHALL use the original push and its tested artifact. A conflicting publication state SHALL stop the affected release without modifying existing conflicting objects.

#### Scenario: Reconcile matching and conflicting identities
- **Verification:** controlled state for a matching incomplete release, a published version and a conflicting tag or asset.
- **WHEN** an eligible run or its retry finds existing publication state
- **THEN** an already published version is skipped with a diagnostic
- **AND** a matching incomplete publication can resume with the checked commit and wheel
- **AND** a conflicting tag, draft or existing asset is left intact.

#### Scenario: Retry after pushing the tag
- **Verification:** controlled interruption between tag push and draft creation, followed by a retry of the same eligible input.
- **WHEN** the version tag already exists on the remote at the checked commit and the version has no release record
- **THEN** the publisher reuses the tag and can create the release with the original tested wheel
- **AND** the tag alone does not advance the published release boundary.

#### Scenario: Reconsider a version after waiting to publish
- **Verification:** two overlapping eligible push fixtures and controlled release state.
- **WHEN** another run publishes the same or a higher version before a waiting release starts
- **THEN** the waiting release skips publication using the current published state
- **AND** its build and tests remain attributable to its original push.
