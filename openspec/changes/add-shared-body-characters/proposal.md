# Proposal

## Why

HML already separates skeletal movement intent from rendering, but offers only the anatomical skeleton character. Adding male and female characters through one shared construction and deformation contract will let a movement or common body fix reach the complete character set in one library change, without maintaining three animation libraries.

## What Changes

- Keep `skeleton` as a complete, independently selectable character and the backward-compatible default; it requires no surface model.
- Add equally selectable `male` and `female` characters using one authored procedural surface template, shared topology and binding rules, and separate declarative appearance parameters.
- Keep identical skeletal proportions, joint centers, rig, action limits, movement sources, contacts and timing for all three characters in this iteration. Visual selection does not select mass coefficients or sex-specific mobility.
- Add additive character selection and a complete-character batch to rendering, with explicit character identities, integrity-bound source closure, collision-free outputs and portable provenance.
- Define deterministic regeneration and checks for the entire character set, including a shared-edit propagation test and an independent visual comparison pack.
- Preserve a separation between skeletal profile, surface template, appearance preset and motion intent so future proportion/body-type branches can be introduced explicitly. Different skeletal proportions, athletic/other body types, retargeting and new movements are outside this change.
- Use original stylized, matte, featureless exercise mannequins rather than external assets. Freeze authored silhouette and deformation approximations in the design dossier; do not claim measured or universal male/female anatomy.

The 2026-10-28 visual follow-up replaces the separate closed arm-root/torso overlaps with connected shoulder surfaces and smoothly blended skinning, as explicitly selected by the human after the R3 preview. Preserve R3's improved neck and the shared shoulder envelope, skeletal movement and lower body. Both shoulders use one mirrored topology and weighting rule across male/female. Only shoulder junctions are joined; torso/leg-junction redesign is deferred. A fresh bounded preview precedes renewed expensive acceptance checks. Following the R4 feedback that the connected result is nearly good but angular, R5 increases only local shoulder density and applies bounded local smoothing while retaining the chosen envelope, narrow neck and smooth binding.

The R5 follow-up requests a more horizontal shoulder line with lowered arms while retaining the improved smoothness. R6 changes only the upper shoulder rest shape through one neutral-reference authoring operation; it preserves R5 topology and weights, the neck and common skeletal movement. A fresh bounded R5/R6 comparison remains subject to the early human visual gate.

## Capabilities

### New Capabilities

- `character-models`: First-class character definitions, shared procedural surfaces and deformation, source identity, synchronized regeneration, surface checks and human visual acceptance.

### Modified Capabilities

- `public-generation-api`: Add character selection/batches to `render`, expose character-linked results/provenance, and preserve skeleton defaults and CLI parity.
- `python-distribution`: Package the character registry, template, presets and schemas so the complete character set works from an installed wheel without runtime assets or checkout access.

## Impact

Canonical additions will live in `characters/` with versioned schemas in `schema/`. Host validation, rendering, Blender construction, render manifests, result projections, package resource staging and review-pack generation will gain character-aware behavior. Existing anatomical profile/mobility/diagnostic sources, rotation conventions, public preparation semantics, scene settings and skeleton output geometry remain the regression baseline. No new dependency, external mesh, motion source, backend version, binary source asset or release publication is proposed. Implementation and human visual approval require their separate gates.
