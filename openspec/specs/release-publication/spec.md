# release-publication Specification

## Purpose

Publish checked, versioned HML wheels automatically from accepted OpenSpec changes, with reproducible version selection and identifiable immutable GitHub releases.

## Requirements

### Requirement: Accepted changes trigger release evaluation

Every newly archived OpenSpec change reaching `main` after the configured bootstrap boundary SHALL trigger automatic release evaluation, including `skip_specs` changes. Existing approval, independent review and applicable human visual acceptance SHALL precede archive. Publication SHALL require no additional human approval.

#### Scenario: Accept a change with or without specification deltas
- **Verification:** synthetic Git histories and workflow trigger inspection.
- **WHEN** a newly archived change reaches `main`, with ordinary deltas or `skip_specs: true`
- **THEN** release evaluation includes its archive identity and acceptance commit
- **AND** it relies on the existing accepted archive workflow rather than inventing an additional release approval.

#### Scenario: Ignore planning and release bookkeeping
- **Verification:** negative trigger matrix.
- **WHEN** a commit changes active planning artifacts, synchronizes canonical specifications without a newly archived change, edits an existing historical archive, or records automated release metadata
- **THEN** that commit alone causes no new release
- **AND** publication does not remove or replace the change-level approval and review gates.

### Requirement: Release version follows canonical specification changes

The release version SHALL have the form `0.MINOR.PATCH` with nonnegative integer components. Relative to the previous published release snapshot, any added, removed, renamed or byte-modified canonical `openspec/specs/**/spec.md` SHALL increment minor and reset patch; otherwise patch SHALL increment. One increment SHALL cover the release's complete pending change set.

#### Scenario: Choose minor for any specification change
- **Verification:** version-selection matrix against synthetic tagged snapshots.
- **WHEN** version `0.2.3` is followed by a release containing any canonical specification addition, removal, rename, requirement/scenario edit or editorial correction
- **THEN** the version is `0.3.0`, regardless of how many changes or specification files are included
- **AND** active or archived change delta files outside canonical specifications do not independently determine the increment.

#### Scenario: Choose patch without specification changes
- **Verification:** version-selection and no-op matrices.
- **WHEN** accepted changes follow version `0.2.3` without a canonical specification difference
- **THEN** the version is `0.2.4`
- **AND** an empty pending change set produces no version increment or release
- **AND** malformed versions or versions outside `0.x` fail explicitly rather than selecting an automatic major-version policy.

### Requirement: Publication covers pending accepted changes durably

Release processing SHALL serialize publication and discover pending accepted changes from durable repository/release boundaries rather than only the latest event. Closely spaced changes MAY share one release. Each accepted change SHALL be attributed to exactly one successful release. Failures or superseded jobs SHALL NOT lose pending work.

#### Scenario: Coalesce concurrent accepted changes safely
- **Verification:** synthetic histories with interleaved trigger delivery and compare-and-swap failures.
- **WHEN** two accepted archive commits arrive before a release snapshot is reserved
- **THEN** one release may cover both with a single version increment and notes naming both
- **AND** an advancing `main` before reservation causes recomputation instead of overwriting commits or using a stale snapshot
- **AND** newly accepted work after the reserved snapshot remains pending for the next release.

#### Scenario: Resume after an interruption
- **Verification:** fault injection before and after version commit, tag, asset upload and final publication.
- **WHEN** a release job fails, is superseded, or is rerun
- **THEN** the durable boundary identifies unfinished publication and still-pending accepted changes
- **AND** unfinished publication is reconciled before selecting a later version
- **AND** completed releases are not repeated or omitted from future version selection.

### Requirement: Bootstrap excludes historical archives

The first release SHALL use an explicit immutable bootstrap snapshot and its declared `0.2.0` as the prior version when no managed published release exists. Archives already present at that boundary SHALL be treated as historical. The `versioned-releases` change SHALL remain eligible when accepted after that boundary.

#### Scenario: Enable releases in the existing repository
- **Verification:** no-tag repository fixture containing existing archives and a subsequent archive of this change.
- **WHEN** release automation first evaluates this project's archive history
- **THEN** it does not emit releases for previously archived foundation, packaging or API changes
- **AND** accepting `versioned-releases` includes the new canonical release specification and produces `0.3.0`
- **AND** a missing, non-ancestor or conflicting bootstrap boundary fails without guessing a baseline.

### Requirement: Only the checked release wheel is published

A release SHALL publish only after the selected version commit passes existing locked host and package checks, including installed-wheel checks and source-distribution parity. The declared version, wheel metadata, Python and CLI versions SHALL agree. The Git tag, release notes and checksum SHALL identify that exact checked commit and wheel. Host success SHALL NOT imply renewed Blender or visual acceptance.

#### Scenario: Publish a verified wheel
- **Verification:** clean release-candidate build and install, metadata assertions and checksum/commit audit.
- **WHEN** all required host/package checks succeed on the selected version commit
- **THEN** `vX.Y.Z` references that commit and its published GitHub Release contains exactly the checked wheel and `SHA256SUMS` as uploaded assets
- **AND** notes identify the included archived changes, prior boundary, acceptance commits, release commit and verification run
- **AND** the uploaded wheel bytes equal the checked bytes, with no unverified rebuild substituted
- **AND** there is no package-index publication or additional manual release approval.

#### Scenario: Stop on failed verification
- **Verification:** failed host, package, installation, version and checksum cases.
- **WHEN** a required check fails or artifact identity cannot be established
- **THEN** no successful public release is published
- **AND** pending work and diagnostic evidence remain identifiable for retry.

### Requirement: Released identities are immutable and retries are safe

Automation SHALL never move a conflicting tag, overwrite a published asset or republish a version with different bytes. A retry SHALL reconcile the same reserved version/commit and checked artifact before resuming. A conflicting identity or missing evidence SHALL stop publication explicitly.

#### Scenario: Reconcile matching and conflicting identities
- **Verification:** mocked GitHub API and local Git tag/asset fixtures.
- **WHEN** a retry finds a tag or release for the reserved version
- **THEN** matching commit, asset checksum and completed publication result in a successful no-op, or matching incomplete publication resumes
- **AND** a different tag target, different wheel bytes, unrelated existing release or unavailable proof prevents overwrite and later-version publication until resolved.

### Requirement: Release permissions and evidence are bounded

Release automation SHALL use documented repository permissions without requiring a new permanent token or runtime dependency. A denied write or protected-branch conflict SHALL fail without bypassing protection. Release verification and cleanup SHALL follow `build-artifact-lifecycle`. External materials actually used SHALL satisfy existing commercial-use clearance and register requirements.

#### Scenario: Operate with configured or denied permissions
- **Verification:** workflow permission audit and denied-write simulation.
- **WHEN** repository policy permits or denies the required version-commit, tag or release write
- **THEN** configured automation completes within those permissions or reports the blocked operation without forcing a protected write or publishing an unverified fallback
- **AND** required repository settings and retry instructions are documented.

#### Scenario: Retain reviewable evidence and cleared sources
- **Verification:** reviewer source register audit, run inventory and cleanup receipt.
- **WHEN** implementation and independent release checks finish successfully or fail
- **THEN** every new external reference/tool/action actually used has verified commercial/derivative permission and a complete `docs/used-materials.md` entry, including no-attribution sources
- **AND** fresh flat build runs and dependency-aware cleanup preserve checked-artifact identity and required failure/retry evidence
- **AND** the durable hand-off records removed bytes/paths, retained reasons, dependency checks and pending cleanup.
