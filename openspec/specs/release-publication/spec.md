# release-publication Specification

## Purpose

Publish checked, versioned HML wheels automatically from accepted OpenSpec changes, with reproducible version selection and identifiable immutable GitHub releases.

## Requirements

### Requirement: Publication covers pending accepted changes durably

Publication SHALL serialize writes and use the current published or bootstrap boundary to attribute included accepted archives. Each accepted archive SHALL be attributed to at most one successful release and SHALL remain eligible until its containing snapshot is published.

#### Scenario: Coalesce concurrent accepted changes safely
- **Verification:** synthetic history with multiple archives, a later push and overlapping eligible runs.
- **WHEN** a checked snapshot is published
- **THEN** its notes include the eligible archives between the prior published or bootstrap boundary and the released commit, including `skip_specs` archives
- **AND** archives outside that snapshot remain eligible for a later release
- **AND** a newer snapshot uses its own tested wheel and may include previously unpublished accepted archives.

#### Scenario: Resume after an interruption
- **Verification:** controlled interrupted or superseded publication with an earlier published release.
- **WHEN** the job ends before a release is public
- **THEN** the published boundary remains the same
- **AND** unpublished accepted archives remain eligible.

### Requirement: Bootstrap excludes historical archives

When no managed release has been published, the configured immutable bootstrap commit and version `0.2.0` SHALL define the prior boundary. Archives already included in that boundary are historical. An unpublished legacy reservation SHALL NOT advance the boundary or select the candidate.

#### Scenario: Enable releases in the existing repository
- **Verification:** synthetic history with bootstrap archives, a historical unpublished reservation and later accepted changes.
- **WHEN** the first eligible checked push is published
- **THEN** its notes include accepted archives after bootstrap that are present at the checked commit
- **AND** the selected commit and wheel come from that push
- **AND** a missing or conflicting bootstrap boundary prevents publication.

#### Scenario: Continue from an existing public release
- **Verification:** controlled state containing a public managed release from the legacy publisher.
- **WHEN** a prior managed release has already been published
- **THEN** its published commit defines the prior boundary and older attributed archives are omitted from new release notes.

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

#### Scenario: Recheck a draft by its numeric release ID
- **Verification:** controlled GitHub client responses with a stable release ID and matching, missing or conflicting follow-up responses.
- **WHEN** creation returns a draft for the expected version tag and a subsequent read by ID returns a different tag, including an `untagged-*` value
- **THEN** publication stops before promoting the draft or altering its tag
- **AND** the diagnostic identifies the expected tag, returned tag and release ID
- **AND** the equivalent matching read allows the ordinary publication path to continue.

### Requirement: Release permissions and evidence are bounded

Only the publication job SHALL require tag and release write permission. Automation SHALL use documented repository permissions without a new permanent token. Release verification and cleanup SHALL follow the project build-artifact lifecycle. External materials actually used SHALL meet the existing source clearance rules. Project-authored GitHub API operations SHALL use the approved locked Python client.

#### Scenario: Operate with configured or denied permissions
- **Verification:** workflow permission inspection and a denied-write control.
- **WHEN** publication requires a GitHub write
- **THEN** the permitted operation succeeds or the denied write is reported without publishing an unchecked fallback.

#### Scenario: Retain reviewable evidence and cleared sources
- **Verification:** inspect the recorded run, artifact identity, source register and cleanup outcome.
- **WHEN** the candidate is independently reviewed
- **THEN** the evidence identifies the checked commit, run, wheel filename, SHA-256 and test outcomes
- **AND** new external materials are recorded and role-owned cleanup follows the project rules.

#### Scenario: Run GitHub operations through the approved client
- **Verification:** tracked source audit and controlled release history, creation, update and asset operations through the locked client interface.
- **WHEN** project tooling lists or reads GitHub releases, creates or updates a release, or lists, uploads or downloads its assets
- **THEN** the approved client performs the API operation
- **AND** project code has no direct HTTP fallback for GitHub API calls
- **AND** logs distinguish the requested release identity from the returned release identity and omit credentials and raw asset bytes.

### Requirement: A version increase in a push requests release publication

Only a fast-forward push to `main` that increases the declared project version SHALL request publication. The decision SHALL use the original push's before and after revisions. An already published or superseded version SHALL be skipped. Ordinary CI SHALL run for the selected revision regardless of release eligibility.

#### Scenario: Push an intentional increase to main
- **Verification:** synthetic single-commit and multi-commit push histories.
- **WHEN** a fast-forward push to `main` increases the declared version and that version exceeds the published baseline
- **THEN** the checked push tip becomes eligible for publication after its required tests succeed
- **AND** the rule applies whether or not the push archives a change.

#### Scenario: Run CI without publishing
- **Verification:** event and version fixtures for same-version, downgrade, initial, forced, missing-history, non-main and pull-request cases.
- **WHEN** an event with a checkoutable commit is not a qualifying main push or a valid increase cannot be established
- **THEN** normal CI runs and no release or tag is created
- **AND** a same-version push cannot request release of an earlier unpublished version.

### Requirement: The declared version controls publication

The contributor SHALL declare the release version as `0.MINOR.PATCH` with nonnegative integer components and commit the corresponding lock update. Publication SHALL use the version and commit verified by the push workflow without writing a version, reservation or new source commit.

#### Scenario: Release the authored version
- **Verification:** controlled publication and inspection of tag, release and branch writes.
- **WHEN** the workflow publishes an eligible checked push
- **THEN** its release version is the version declared at the tested push tip
- **AND** the workflow leaves source version, lock and branch history untouched.
