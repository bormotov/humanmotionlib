# Proposal

## Why

HML currently declares project metadata but disables packaging; its `tools.*` imports, source lookup, Blender launch paths and output ownership require the checkout. A wheel must supply the complete HML runtime so installed users can validate, prepare, build, verify and present the supported anatomical skeleton diagnostics from their own workspace.

## What Changes

- Build an installable `humanmotionlib` distribution with explicit build requirements, runtime dependencies, version `0.2.0` and documented installed commands under the `hml` console entry point.
- **BREAKING**: move implementation imports from `tools.*` to `humanmotionlib.*` and checkout script commands to `hml <subcommand>` (also available through `python -m humanmotionlib`); document the migration without publishing a generic `tools` package.
- Include the supported procedural skeleton profile, mobility, body groups, humanoid map, all diagnostic fixtures, schemas, fixed scene, Blender scripts, backend contract, acceptance documentation and license/provenance closure in the wheel and source distribution.
- Separate immutable package resources from a caller-selected writable workspace; preserve flat `build/` run roots and supervised backend execution with a workspace-owned execution slot.
- Identify installed resources and implementation in prepared inputs and output evidence without requiring Git, the project file or the development lock at runtime; retain locked development setup.
- Build and test the wheel in GitHub Actions on push and pull request, retain the checked wheel as an artifact and preserve existing host checks.

## Capabilities

### New Capabilities

- `python-distribution`: installable namespace, commands, complete runtime resources, distribution identity and licenses, installed-workflow parity and wheel CI.

### Modified Capabilities

- `backend-execution`: use installed backend scripts and workspace-owned locking, and report installed package/resource identity without relaxing supervision or backend isolation.
- `host-python-runtime`: support both locked contributor setup and dependency-complete wheel installation, including the directly imported schema-registry dependency and build tooling.
- `build-artifact-lifecycle`: scope `build/` to the selected writable workspace while retaining repository behavior and historical evidence paths.

## Impact

Implementation affects `pyproject.toml`, `uv.lock`, the `tools/` modules and their tests, new package/build configuration, canonical resource inclusion, command documentation and `.github/workflows/`. Canonical YAML/schema/scene bytes, anatomical and timing conventions, numerical tolerances and Blender pins remain unchanged. Blender 5.2.2 LTS build `d13f752e3b9c` remains an external system prerequisite on the existing Darwin arm64 reference platform; the wheel supplies all HML-owned inputs and performs no runtime downloads. This change does not add new exercise motions, general export support, a Blender binary, or package-index publishing.
