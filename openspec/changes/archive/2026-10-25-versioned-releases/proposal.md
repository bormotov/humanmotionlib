# Proposal

## Why

HML already builds and verifies an installable wheel, but accepted changes have no automatic versioned GitHub release. A repeatable release policy will make each accepted change installable by version without manually maintaining tags or choosing version increments.

## What Changes

- Release automatically after each newly accepted OpenSpec change is archived on `main`, including changes with `skip_specs`; planning edits and specification synchronization alone do not release.
- Keep one version in `pyproject.toml` for the runtime and bundled data. During `0.x`, increment minor and reset patch when any canonical specification content/path changes since the preceding release boundary; otherwise increment patch. Editorial specification changes also count.
- Publish an immutable `vX.Y.Z` Git tag and GitHub Release containing the checked wheel, SHA-256 checksum and change notes. Closely spaced accepted changes may share a release; every pending change is covered once, with safe retries and exact commit/artifact identity.
- Reuse existing host/package checks, generalize current-version assertions and require no additional human release approval. Existing change approval, independent review and applicable visual acceptance still precede archive.
- Bootstrap from the current `0.2.0` source baseline without replaying historical archives. PyPI, independent data versions, automatic `1.0` promotion and new visual rendering are out of scope.

## Capabilities

### New Capabilities

- `release-publication`: accepted-change detection, automatic pre-1.0 version selection, ordered release processing and immutable checked GitHub publication.

### Modified Capabilities

- `python-distribution`: replace the fixed current-version acceptance of `0.2.0` with consistency against the declared release version, preserving the namespace migration's historical identity.

## Impact

Release orchestration and GitHub Actions, existing package/host verification reuse, `pyproject.toml` and `uv.lock` version updates, version-related tests, release notes and documented repository permissions/recovery commands are affected. No runtime API, source data, pose, timing, scene, backend pin or generation algorithm changes are intended. The repository must permit the workflow's scoped tag/release writes and documented version synchronization; blocked permissions fail without publication. No new runtime dependency or permanent credential is assumed.
