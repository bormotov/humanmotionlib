## MODIFIED Requirements

### Requirement: CI builds and checks the distributable artifact

Push and pull-request CI SHALL build and upload one wheel from the selected revision. Verification SHALL install the uploaded wheel non-editably in a fresh environment and run the host and installed character tests. The wheel filename, SHA-256 and test results SHALL identify the checked artifact. CI SHALL report host-only scope and SHALL NOT publish to a package index.

#### Scenario: Start verification after the candidate is available
- **Verification:** inspect workflow dependencies and exercise successful and failing build or upload paths.
- **WHEN** a push or pull request starts CI
- **THEN** the build uses the exact pushed commit or the selected pull-request revision and uploads one wheel
- **AND** successful upload starts verification of that wheel regardless of whether the run is eligible to publish a release
- **AND** a failed build or upload fails CI and prevents verification.

#### Scenario: Check the actual wheel in CI
- **Verification:** fresh wheel installation and test execution with passing and failing controls.
- **WHEN** verification receives the wheel from the build
- **THEN** it verifies the expected filename and SHA-256 and installs that wheel outside the checkout
- **AND** the host and installed character tests exercise the installed package and its resources
- **AND** a missing or mismatched wheel, failed installation or failed test fails verification
- **AND** the test results identify skipped or excluded scope and host-only results do not establish real Blender or human visual acceptance.

#### Scenario: Prove the installed artifact has no checkout dependency
- **Verification:** run the installed character tests with an isolated environment and the existing misleading-neighbor fixture.
- **WHEN** CI runs the installed character tests
- **THEN** their assertions cover imports and resources from the wheel installation, explicit workspace use and runtime integrity
- **AND** a misleading source tree in the caller directory cannot supply runtime resources.

#### Scenario: Allocate acceptance within the selected external workspace
- **Verification:** run the installed character tests with an isolated environment and the existing misleading-neighbor fixture.
- **WHEN** the installed character tests launch the checked library
- **THEN** their invocation directory is disjoint from the virtual environment and package installation
- **AND** HML-controlled results stay in the selected workspace's `build/`.

#### Scenario: Check the exact source revision selected by a reusable caller
- **Verification:** exercise downstream success, failure and retry with same-run artifacts.
- **WHEN** a downstream job uses an already successful build, including after a failed downstream job is retried
- **THEN** it uses that build's selected source revision and checks the filename and SHA-256 of its wheel
- **AND** another push or a replacement build cannot supply the artifact for that verification result.
