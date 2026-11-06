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

The human's 2026-11-03 acceptance revision replaces the remaining real-backend character/stature cross-product with exactly three pairs: `skeleton` at H=1.50 m, `male` at H=1.70 m and `female` at H=1.90 m. Each pair retains full diagnostic numeric coverage and its focused visual/repeatability checks. The other six pairs, same-character native/render cross-stature scaling and complete-character batch pixel comparisons are outside this change's remaining live acceptance. Broad source/host/API/CLI contracts remain supported and tested. Reports and the human pack identify the reduced scope explicitly; prior full-matrix evidence retains its historical identity.

On 2026-11-05 the human approved the minimal repair of the two genuine surface findings: orient the leg cap fans consistently and derive the left shoulder bridge/refinement from the canonical right side. This corrects the existing oriented-manifold and mirror contracts while retaining the accepted R6 shape rules and numerical limits. Before further expensive verification, show one bounded before/after preview for male H1.70 and female H1.90: neutral, rest, complete arm-raise and complete squat at BPM90, fixed views and matching shoulder/leg details. The new preview's early visual decision is pending; historical R6 acceptance does not accept its new identity. No general silhouette improvement or other joint redesign is authorized.

## Capabilities

### New Capabilities

- `character-models`: First-class character definitions, shared procedural surfaces and deformation, source identity, synchronized regeneration, surface checks and human visual acceptance.

### Modified Capabilities

- `public-generation-api`: Add character selection/batches to `render`, expose character-linked results/provenance, and preserve skeleton defaults and CLI parity.
- `python-distribution`: Package the character registry, template, presets and schemas so the complete character set works from an installed wheel without runtime assets or checkout access.
- `backend-execution`: Simplify completion handling for task 9.4: after the direct child is reaped, perform no operations using its saved process-group identifier; keep bounded timeout/cancellation attempts while ownership remains anchored and report unconfirmed descendant cleanup honestly.

## Impact

Canonical additions will live in `characters/` with versioned schemas in `schema/`. Host validation, rendering, Blender construction, render manifests, result projections, package resource staging and review-pack generation will gain character-aware behavior. Existing anatomical profile/mobility/diagnostic sources, rotation conventions, public preparation semantics and scene settings remain preserved contracts. Following the human's 2026-11-03 decision, the current identified construction and rendering system is the starting point for subsequent work; equivalence to historical Blender-generated skeleton geometry or pixels is outside this change's remaining acceptance scope. No new dependency, external mesh, motion source, backend version, binary source asset or release publication is proposed. Implementation and human visual approval require their separate gates.

The diagonal acceptance revision requires explicit scoped inputs/reports in the existing `verify-skeleton` and `review-pack` commands and their documentation. It changes the remaining verification workload, not character construction, supported public character/stature combinations, batch semantics or numerical tolerances. A diagonal pass never claims that the full character/stature matrix, native batch isolation or cross-stature render equivalence was checked.
