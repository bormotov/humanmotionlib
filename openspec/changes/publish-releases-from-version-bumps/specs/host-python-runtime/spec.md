## MODIFIED Requirements

### Requirement: CI enforces the host environment contract

Pull-request and push CI SHALL run the complete host-only test scope on supported CPython against the uploaded wheel in a fresh environment outside the checkout. CI SHALL report test failures and excluded backend scope. CI verification SHALL use the candidate wheel's declared runtime dependencies. Contributor locked setup remains subject to the committed lock requirements.

#### Scenario: Run the host job from a clean checkout
- **Verification:** inspect the workflow and run the host suite with an installed candidate in a fresh supported environment.
- **WHEN** the build successfully uploads the wheel for the triggering revision
- **THEN** CI runs the host tests with supported CPython and tests the package from the non-editable wheel installation
- **AND** the result reports failed, skipped or excluded tests within the host scope
- **AND** the test result claims no real Blender or visual acceptance.

#### Scenario: Check the uploaded candidate with Host Python
- **Verification:** use focused missing-artifact, failed-install and failed-test controls.
- **WHEN** CI cannot receive the expected wheel, install it on the supported host or successfully execute the required host tests
- **THEN** verification fails and the workflow exposes the failing stage.
