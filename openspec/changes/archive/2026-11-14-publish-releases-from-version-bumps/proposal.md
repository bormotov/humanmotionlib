# Publish releases from version bumps

## Why

The existing release workflow can select an older reserved commit even though the workflow definition comes from a newer push. The control branch demonstrated a simpler pipeline that builds the pushed commit, tests the uploaded wheel and hands that wheel to publication.

## What Changes

- Build one wheel for each push or pull-request run. Install the uploaded wheel in a fresh environment and run the host and installed character tests. Use the filename and SHA-256 to identify the wheel at each handoff.
- **BREAKING** Publish a GitHub Release only after an intentional version increase in a push to `main` passes the required tests for that push. The contributor commits the new declared version and updates the lock as usual.
- **BREAKING** Retire automatic version selection, release reservations and the independent archive, manual and pending-publication triggers. Keep existing published releases and archive attribution.
- Carry over the test fixture and working-directory fixes verified on the control branch. Test parallelization is a separate change.

## Capabilities

### Modified Capabilities

- `python-distribution` defines CI around one wheel and its installed tests.
- `host-python-runtime` defines the supported interpreter, isolated wheel installation and host test scope in CI.
- `release-publication` defines version-bump publication from the tested push and preserves published identities and archive attribution.

## Impact

Changes affect the GitHub Actions workflows, release tooling and guidance, and relevant tests. Visual preview and visual acceptance are not applicable because this change concerns package CI and release publication.
