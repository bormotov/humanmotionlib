# Proposal

## Why

Build and review attempts currently encode their identity as nested directories, making obsolete runs difficult to distinguish and remove. Cleanup has retained scattered logs and JSON without a clear continuing need; future runs need a consistent location and a required completion cleanup.

## What Changes

- Require new independently managed build/check/review runs to be direct children of `build/`, with identifying components joined by `_`; components use lowercase kebab-case and cannot contain `_`.
- Distinguish run identity from necessary artifact content directories such as `frames/`, `assets/` and a tool's internal render passes. Independent retries and review packs must not be nested inside another run.
- Add mandatory cleanup after developer and reviewer checks, with dependency-aware retention, an explicit explanation for retained diagnostics, and a compact completion record.
- Align `AGENTS.md`, all three custom-agent instructions and current `tools/README.md` commands with the same rule, including reviewer write/cleanup scope.
- Update two existing specification path requirements for future packs. Existing accepted and expressly protected historical outputs remain unchanged; this change does not migrate or delete them.

## Capabilities

### New Capabilities

- `build-artifact-lifecycle`: Identifiable flat run directories and a verifiable cleanup/retention procedure for generated build and verification artifacts.

### Modified Capabilities

- `anatomical-skeleton`: Locate future structural review packs under the flat build convention instead of the fixed nested review path; preserve all existing pack content and visual gates.
- `joint-mobility`: Link future independent review reports to the flat pack location without changing diagnostic acceptance or historical preservation obligations.

## Impact

Documentation and agent workflow instructions only: `AGENTS.md`, `.codex/agents/{architect,dev,reviewer}.toml`, and `tools/README.md`. Main-spec changes occur through normal delta sync. Existing command entry points, flags, artifact formats, source data, Python/Blender implementation, poses, segments, motions, contacts, frame timing, cameras and licenses do not change. No dependencies or external references are needed. Historical archived specifications and generated evidence are not rewritten.
