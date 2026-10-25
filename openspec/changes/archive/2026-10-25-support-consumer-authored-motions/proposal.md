# Proposal

## Why

Python consumers can choose BPM and stature but can prepare only packaged diagnostic fixtures. A consumer that needs a shallower squat must supply its own movement intent without modifying HML resources, losing attribution, or bypassing the existing kinematic and workspace checks.

## What Changes

- Add an optional schema-validated consumer motion input to `humanmotionlib.api.prepare`, supplied as a local YAML/JSON file or an in-memory document. Existing diagnostic requests keep their defaults.
- Support a complete definition in the existing scoped `skeleton-diagnostic/v1` language and a declarative variant of a packaged fixture, with explicit track scales or replacements. This does not introduce the future general pose/segment/motion composition language.
- Validate finite parameters, source shape, profile/channel/group ownership, supported constructors, beat events, contacts, mobility and provenance before persisting prepared input or probing Blender.
- Seal the submitted source, its resolved definition and inherited attribution into prepared input; render from that snapshot without requiring the external project to remain available.
- Fully validate and replay consumer snapshots in host Python before starting Blender. Blender checks snapshot/package integrity and the exact host-validated identity using its own Python, without importing host parsing/schema dependencies.
- Document a consumer-supplied squat-depth verification example. Its test angles demonstrate parameter flow only; this change adds no canonical exercise or recommended depth.
- Provide installed-package contract checks, unchanged-diagnostic regression evidence and a focused front/side comparison pack for human visual review.

## Capabilities

### New Capabilities

- `consumer-motion-sources`: Versioned declarative consumer input, variant resolution, source validation, clearance records and self-contained prepared snapshots.

### Modified Capabilities

- `public-generation-api`: Permit explicit validated consumer sources, expose their identity/provenance, and preserve the existing import, result, error, rendering and diagnostic-default contracts.

## Impact

Affected areas are public preparation/result projection, source validation and schemas, diagnostic evaluation reuse, host snapshot validation, dependency-free backend integrity reading, supervised input-identity handoff, package resource inventory, installed acceptance tests, and usage/command documentation. Rendering keeps the pinned backend and fixed scene. Existing packaged fixture data, including the 90-degree squat diagnostic, remain the regression baseline. No new runtime dependency, compiled-reference index, custom profile/rig/scene input, arbitrary Python execution, CLI source-import option, bake/export format, or production exercise is proposed.
