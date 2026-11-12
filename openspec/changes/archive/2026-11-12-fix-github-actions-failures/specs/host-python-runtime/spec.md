# Host Python Runtime Spec Delta

## MODIFIED Requirements

### Requirement: CI enforces the host environment contract

Pull-request and push CI SHALL execute the supported host interpreter, validate version-selection consistency, check and install the committed lock without regeneration, validate canonical sources and run the complete host-only test scope. It SHALL expose failures and identify the backend scope excluded from that job. The host job SHALL depend on successful build artifact upload and use its wheel.

#### Scenario: Run the host job from a clean checkout
- **Verification:** workflow inspection and one successful CI execution, with failing-path assertions for version mismatch, stale lock and failed host tests.
- **WHEN** CI checks a candidate commit
- **THEN** it asserts the actual HML interpreter is Python 3.14, verifies metadata agreement and lock freshness, and executes validation and the host suite
- **AND** a wrong interpreter, stale lock, failed validation or failed host test prevents job success
- **AND** the job does not install or substitute a different Blender to make host checks pass
- **AND** its status is explicitly scoped to host checks rather than full backend acceptance.

#### Scenario: Check the uploaded candidate with Host Python
- **Verification:** downstream host job with a valid artifact and focused failure controls for artifact identity and checkout imports.
- **WHEN** the build job uploads the distribution artifacts for the selected commit
- **THEN** the host job checks out that commit for tests and contributor fixtures and installs the supplied wheel non-editably in a fresh environment outside the checkout
- **AND** the host suite imports HML from that installation and reports the commit, interpreter, installed package origin, wheel checksum and test outcome
- **AND** a missing or mismatched wheel or a checkout source import prevents test discovery and fails the job.
