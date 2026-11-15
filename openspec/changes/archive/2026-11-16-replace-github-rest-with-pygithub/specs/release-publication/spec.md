# Spec Delta

## MODIFIED Requirements

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
