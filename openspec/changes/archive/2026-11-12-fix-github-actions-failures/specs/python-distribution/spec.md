# Python Distribution Spec Delta

## MODIFIED Requirements

### Requirement: CI builds and checks the distributable artifact

Push and pull-request CI SHALL build and upload one candidate wheel and source distribution before starting host and installed package verification. Both checks SHALL verify and install that exact wheel non-editably in separate fresh host environments outside the checkout. Successful CI SHALL retain the wheel and check evidence as downloadable artifacts. Host-only CI SHALL identify its unexecuted real-backend scope and SHALL NOT publish to a package index.

#### Scenario: Start verification after the candidate is available
- **Verification:** workflow dependency inspection and successful and failing build or upload cases.
- **WHEN** a push or pull request starts CI
- **THEN** the build job uploads the wheel and source distribution from the selected commit as a workflow artifact
- **AND** the host and installed package jobs start only after the upload succeeds, using the artifact from that build as input
- **AND** a build or upload failure makes the workflow fail and skips both verification jobs
- **AND** ordinary CI uploads a run artifact without creating a versioned release.

#### Scenario: Check the actual wheel in CI
- **Verification:** workflow inspection and successful GitHub Actions execution linked to the candidate commit.
- **WHEN** the installed package job receives the candidate wheel and source distribution
- **THEN** build/version/dependency consistency, runtime and license inventory, source-distribution rebuild parity, dependency consistency and installed CLI and API checks all pass before a successful artifact verdict
- **AND** the installed checks run with checkout imports disabled and exercise all canonical source validation and preparation
- **AND** a missing or mismatched artifact, missing resource, namespace leak, metadata mismatch, failed install or failed smoke command makes the job fail
- **AND** the uploaded wheel checksum, commit, workflow run, interpreter/build-tool versions and scoped results identify exactly the checked artifact
- **AND** existing locked host tests still run and host-only success does not imply real Blender acceptance.

#### Scenario: Prove the installed artifact has no checkout dependency
- **Verification:** CI external installed-workflow matrix and retained machine-readable results tied to the wheel checksum.
- **WHEN** CI validates the non-editably installed wheel
- **THEN** invocation directories and explicitly selected workspaces are outside the source checkout and wheel installation, with checkout imports disabled
- **AND** host coverage includes all-fixture validation/preparation, numeric report writing and available presentation-only modes using controlled evidence
- **AND** missing-workspace, workspace-relative path, write-escape, misleading-neighbor and integrity-tampering cases are exercised
- **AND** assertions prove runtime imports/resources come from the installation and HML writes stay under each caller-selected workspace's build tree
- **AND** synthetic presentation evidence and host-only checks are explicitly distinguished from real Blender and human visual acceptance.

#### Scenario: Allocate acceptance within the selected external workspace
- **Verification:** actual isolated acceptance execution with valid and rejected run layouts, filesystem snapshots and artifact audit.
- **WHEN** the package workflow launches installed acceptance for the current wheel
- **THEN** the harness and generated outputs use a fresh run under the selected workspace's `build/`, with the source checkout and read-only wheel installation disjoint from that workspace
- **AND** an escaping, symlinked or occupied acceptance location fails before generation
- **AND** a successful result includes the installed acceptance outcome and evidence from the existing character installation checks.

#### Scenario: Check the exact source revision selected by a reusable caller
- **Verification:** reusable-workflow contract check with the caller event SHA different from the checked revision, and an artifact identity audit.
- **WHEN** the release workflow invokes the CI chain for a reserved revision different from the event commit
- **THEN** checkout, build and both check results identify the reserved revision and the same wheel checksum
- **AND** the release consumer can retrieve the wheel supplied by the build after both checks pass, including when a failed downstream job is rerun against the successful build
- **AND** a missing artifact or any failed required stage prevents release publication.
