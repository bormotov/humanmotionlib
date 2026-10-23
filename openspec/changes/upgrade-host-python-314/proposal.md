# Proposal

## Why

HML currently selects and accepts only host Python 3.12, so its environment, dependency lock and automated checks do not establish that the requested Python 3.14 runtime works. The host interpreter that runs HML must be upgraded without conflating it with Blender's independently supplied embedded Python.

## What Changes

- **BREAKING**: Replace the supported host minor version 3.12 with CPython 3.14 (`>=3.14,<3.15`), updating project requirements, `.python-version`, the generated `uv.lock` and active setup documentation together.
- Resolve and correct demonstrated Python 3.14 incompatibilities in HML and its dependencies, keeping changes limited to the migration and preserving existing data and numerical contracts.
- Add host Python checks to GitHub Actions: this checkout currently contains no CI workflow. Check the actual interpreter, locked environment, source validation and all tests that do not require real Blender.
- Keep the existing complete unittest discovery as a required independent reference-platform check with the pinned Blender. Report host-only exclusions explicitly rather than treating them as backend acceptance.
- Preserve Blender version/build/platform pins and let Blender choose its own embedded Python. Check backend execution separately using the existing supervised path.

## Capabilities

### New Capabilities

- `host-python-runtime`: Supported HML host interpreter, reproducible locked setup, interpreter/dependency checks, host-only CI coverage and independent Blender compatibility evidence.

### Modified Capabilities

None. Existing `backend-execution`, animation, source-permission and build-lifecycle contracts remain applicable; no bone, rotation, contact or time convention changes.

## Impact

Expected implementation locations: `pyproject.toml`, `.python-version`, `uv.lock`, `tools/README.md`, a new `.github/workflows/host-python.yml`, an explicitly documented host-check entry point and focused regression tests. Existing `tools/` or tests may need narrow compatibility fixes based on observed failures. Dependency bounds change only when required for 3.14; no blanket dependency upgrade is intended.

Python 3.12/3.13 host environments must be recreated for 3.14. Blender is not upgraded, its Python is not replaced, and neither the host environment nor its requirements are injected into Blender. Local independent verification still needs the pinned backend on Darwin arm64. Planning does not execute this migration or run its tests; implementation follows Human gate 1.
