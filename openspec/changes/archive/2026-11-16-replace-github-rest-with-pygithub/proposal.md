# Proposal

## Why

Release tooling currently constructs GitHub REST requests and interprets HTTP responses itself. Use the requested PyGithub library to maintain these integrations through its supported Python interface while preserving the project's release and verification contracts.

## What Changes

- Replace project-authored direct GitHub REST calls with PyGithub throughout the repository, including release and asset operations; leave Git operations and GitHub Actions themselves in their existing roles.
- Add and provision the library for every supported execution path that uses the integration, with compatible locked dependencies and documented licensing.
- Preserve actionable logging, token confidentiality, existing publication behavior and independently verified artifact identity.
- Exercise the observed draft-release behavior explicitly; do not assume that changing clients alone changes GitHub's server-side responses or automatically repairs the existing unpublished release.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `release-publication`: use the maintained Python client for GitHub API operations while preserving publication, recovery and diagnostics contracts.
- `host-python-runtime`: make the new release-tool dependency available in the supported locked environments and CI execution path.

## Impact

Release tooling, tests, dependency declarations and lock, CI provisioning, contributor documentation and third-party license records. No change to the wheel publication trigger or the requirement that tests pass before publication is intended.
