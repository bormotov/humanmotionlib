# Spec Delta

## MODIFIED Requirements

### Requirement: Structural visual review pack

The build SHALL produce a structural review pack in a direct child of `build/` named according to `build-artifact-lifecycle`, containing labeled front, rear, and side orthographic views, rest and anatomical-neutral comparisons, local-axis overlays, and measurement and simplification reports. The pack SHALL support independent numeric checks and human visual judgment. Existing accepted and expressly protected historical packs SHALL retain their established paths.

#### Scenario: Review the skeleton before muscles
- **WHEN** the reviewer rebuilds the pack from sources
- **THEN** the views show the same reference skeleton at the same stature with readable structure and landmark identifiers
- **AND** a machine-readable report records each acceptance measurement and its threshold, rather than only a global pass flag
- **AND** anatomical plausibility and movement readability remain subject to human visual approval before archive

#### Scenario: Inspect the revised thorax closely
- **WHEN** the developer prepares a focused neutral/T-pose thoracic preview and the reviewer later regenerates the final pack
- **THEN** both contain labeled front, side, and anterior three-quarter close-ups using the dossier's fixed inspection cameras, with context and isolated-thorax views
- **AND** rib numbers, posterior angles, bone/cartilage distinctions, sternal regions and insertions, and lower cartilage-arch connections are inspectable alongside their shape metrics
- **AND** the full-body diagnostic cameras remain unchanged and inspection cameras are never fitted separately to a pose or stature
- **AND** a human rejection of the thoracic silhouette remains unresolved until revised source geometry has renewed independent review and explicit human visual approval; the previous source snapshot's numeric verdict does not satisfy this gate

#### Scenario: Locate a future structural pack without migrating history
- **Verification:** path and documentation audit.
- **WHEN** a new structural pack is generated after adoption of the flat convention
- **THEN** its run root is a direct child of `build/` with the five identifying components required by `build-artifact-lifecycle`
- **AND** the previously accepted `build/review/anatomical-human-skeleton/` history remains at its established location, with its preservation requirements unchanged
