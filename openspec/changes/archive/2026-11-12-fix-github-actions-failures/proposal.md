# Proposal

## Why

Build the candidate once and give both verification jobs the same wheel so CI can report build, host and installed package results separately.

## What Changes

- Start a single CI chain on push or pull request. The first job builds the wheel and source distribution from the selected commit and uploads them as a GitHub Actions artifact.
- Start the Host Python and installed CLI/API checks only after that upload succeeds. Each job installs the artifact's wheel in its own fresh environment and reports its result separately.
- Place the installed acceptance run inside its selected external workspace. Retain each check's diagnostics with the commit and wheel identity.
- Have Versioned release call the same chain for the reserved commit and publish the checked wheel after both checks succeed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `host-python-runtime` binds host checks to the wheel supplied by the build job.
- `python-distribution` defines the artifact handoff, downstream verification and workspace boundary.

## Impact

The change affects GitHub Actions job dependencies, the release handoff, the installed acceptance harness and focused contributor tests and guidance. It is a nonvisual change.
