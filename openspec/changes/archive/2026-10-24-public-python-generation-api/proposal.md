# Proposal

## Why

Installed HML can already prepare anatomical diagnostics and supervise external Blender, but library callers must combine internal dictionaries, manifests and receipts themselves. A small public Python API will make this supported workflow callable directly and return image paths together with their pose, timing and provenance context.

## What Changes

- Add synchronous `humanmotionlib.api.prepare(...)` and `render(...)` with documented keyword parameters, typed result objects and JSON-compatible result projections.
- Return validated prepared-input identity, pose samples, exact per-BPM static/animation timelines, rendered images, artifact/evidence paths and resolvable provenance without requiring callers to parse internal files.
- Keep Blender an external, pinned prerequisite invoked through HML's existing supervised backend; preparation and imports require no Blender.
- Route `prepare-skeleton` and `run-blender` CLI operations through the same generation API, preserving existing command options, outputs and nonzero failures.
- Verify the non-editably installed API outside the checkout, failure behavior, CLI parity and focused visual regression.

The first API covers the existing packaged skeleton profiles and diagnostic fixtures. Text-to-exercise generation, arbitrary pose/segment/motion source input, bake/export, asynchronous jobs, automatic downloads and a new rendering backend are outside this change.

## Capabilities

### New Capabilities

- `public-generation-api`: A supported Python preparation/render contract with structured pose, timing, image and provenance results, errors and CLI parity.

### Modified Capabilities

None. The API composes the existing distribution, workspace, backend-execution, diagnostic timing and source-clearance contracts without changing their requirements or conventions.

## Impact

Affected areas are the public package surface, preparation and supervised construction adapters, CLI dispatch, installed acceptance checks, usage documentation and package resource closure. Existing source formats, backend/version pins, geometry, body groups, controls, rest policies, contacts, beat sampling and fixed scene remain applicable. Standard-library result types require no new dependency. Reviewer evidence includes a focused API/CLI comparison pack and human visual approval before archive.
