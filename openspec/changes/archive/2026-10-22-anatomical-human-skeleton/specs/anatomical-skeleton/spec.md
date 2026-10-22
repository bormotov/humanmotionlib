## Purpose

Provide a reusable, inspectable human skeleton whose anatomical structure and reference proportions are preserved when constructing an exercise animation rig from repository data.

## ADDED Requirements

### Requirement: Canonical skeletal description

The skeleton SHALL be defined by versioned, schema-validated repository data, independently of Blender session state. Each anatomical structure, articulation, and helper SHALL have a stable identifier and an explicit kind. Parent relationships, rest transforms, landmarks, dimensions, descriptions, and provenance SHALL be inspectable. Invalid data SHALL fail validation before scene generation.

#### Scenario: Reconstruct the skeleton from sources
- **WHEN** a clean headless process receives a valid skeleton profile
- **THEN** it constructs the complete declared skeleton without an existing GUI scene, downloaded runtime asset, or machine-specific path
- **AND** its report identifies the source profile and schema versions

#### Scenario: Reject inconsistent structure
- **WHEN** input contains a duplicate identifier, unresolved parent, parent cycle, non-finite coordinate, non-positive stature, or missing provenance
- **THEN** validation fails with the offending identifier and field before producing a successful build

### Requirement: Anatomical coverage and declared simplifications

The skeleton SHALL expose recognizable skeletal geometry and an inventory distinguishing individual, fused, grouped, and omitted structures. The inventory SHALL cover the head, spine, thorax, pelvis, shoulder girdles, arms, hands, legs, and feet. Grouping SHALL preserve the joint centers and articulated structures needed by `joint-mobility`; geometry SHALL NOT consist solely of animation-bone sticks.

#### Scenario: Inspect structural coverage
- **WHEN** the reference skeleton is shown in front, side, and rear views
- **THEN** the skull, spinal regions, rib cage and sternum, pelvis, clavicles, scapulae, humeri, radii and ulnae, femora, patellae, tibiae and fibulae, and hand and foot regions are identifiable and labeled
- **AND** paired long bones remain distinct in the geometry
- **AND** the inventory identifies which vertebrae, ribs, hand bones, and foot bones are individual geometry or documented groups

#### Scenario: Reject a simplification that removes required articulation
- **WHEN** grouping would immobilize the shoulder girdle, forearm rotation, knee, ankle, or forefoot articulation required by a diagnostic
- **THEN** the profile fails acceptance even if its rest silhouette resembles a person
- **AND** skeletal representation does not claim complete individual-bone fidelity for grouped structures

### Requirement: Differentiated thoracic geometry and anatomical connections

The thorax SHALL follow the revised numerical dossier in `design.md`, with twelve differentiated mirrored rib pairs, named sternal regions, and separate costal-cartilage guides. Rib depth, inferior inclination, posterior curvature, and anterior connections SHALL be explicit. Numerical shapes SHALL be identified as authored approximations, not source measurements.

#### Scenario: Inspect thoracic structures and connections
- **WHEN** the canonical profile and its generated thorax are inspected
- **THEN** each rib has named head, posterior-angle, lateral, anterolateral, and tip landmarks, and the rigid sternum identifies manubrium, body, sternal angle, and xiphoid
- **AND** ribs 1–7 have distinct costal-cartilage insertions on the sternum, with rib 2 at the sternal angle
- **AND** cartilages 8–10 join the preceding cartilage rather than the preceding bony rib tip
- **AND** ribs 11–12 have complete short curved paths with free tips and no sternal or intercostal connector

#### Scenario: Measure the neutral thoracic shape
- **WHEN** the reviewer measures neutral and rest T-pose thoraces on each supported stature
- **THEN** evaluated rib, sternal, and cartilage surfaces meet the dossier's envelope bounds, and every named landmark meets its nominal coordinate tolerance
- **AND** independent shape measurements verify upper-to-middle cage widening, posterior rib angles, increasing head-to-tip descent through ribs 1–7, true-rib overhang bounds relative to their sternal insertions, and the declared arc-length ratios for short ribs 11–12
- **AND** the report distinguishes control coordinates, evaluated centerline extrema, and actual mesh envelopes, including interpolation and thickness offsets
- **AND** the sternal SC landmarks coincide with the unchanged SC joint centers within `1e-4 H`, without moving the shoulder pivots or altering the spine's rest curvature

#### Scenario: Reject the former uniform thoracic construction
- **WHEN** the earlier three-point rib curves with constant `0.100 H` anterior offsets are substituted for the revised rib paths
- **THEN** relational overhang and envelope checks fail even if the substituted geometry matches its own source records exactly
- **AND** replacing cartilage 8–10 connections with neighboring bony-tip connections fails the connection check
- **AND** missing relational checks cannot be replaced by a nominal-coordinate or global success flag

### Requirement: Documented adult proportion profile

The reference profile SHALL use stature `H = 1.70 m` and bilateral segment-to-stature ratios of `0.1605` upper arm, `0.1365` forearm, `0.2340` thigh, and `0.2155` shank. These are a symmetric adaptation of adult DXA means in material `wang-2024-segment-lengths`, not universal human proportions. Rest center-to-center lengths SHALL match these ratios within `1e-6 H`.

#### Scenario: Measure the reference limbs
- **WHEN** the reviewer measures both sides in the rest pose
- **THEN** upper-arm length runs from humeral-head center to elbow center, forearm from elbow center to wrist center, thigh from femoral-head center to knee center, and shank from knee center to ankle center
- **AND** their ratios match the specified targets
- **AND** the report explains the source's projected mechanical-axis measurements and the project's symmetric 3D adaptation instead of equating these lengths with whole-bone mesh bounding boxes

#### Scenario: Change stature without changing the profile
- **WHEN** the same profile is generated at `H = 1.50 m`, `1.70 m`, and `1.90 m`
- **THEN** all rest distances and geometry dimensions scale by the stature ratio within `1e-6 H`
- **AND** angles, topology, and normalized proportions remain unchanged
- **AND** the output is described as a scaled adult reference, not a child or population-specific model

### Requirement: Approval-ready anatomical reference dossier

Before implementation, the planning artifacts SHALL contain a complete numerical reference dossier for all rest landmarks, dimensions, joint centers, and local bases. Each anatomical claim SHALL link to a cleared material and locator; each authored approximation SHALL be identified with its rationale and numerical acceptance bounds. An unfilled dossier SHALL block implementation approval.

#### Scenario: Review the profile before building it
- **WHEN** the specifications and design are submitted for the first human gate
- **THEN** the dossier includes skull, neck and trunk dimensions, spinal rest curvature, thorax and pelvis dimensions, shoulder and hip spacing, hand and foot dimensions, all joint-center coordinates, and landmark-to-geometry relationships
- **AND** it contains no unresolved values, unnamed reference body, or claim that unmeasured coordinates are verified anatomy
- **AND** each landmark and dimension has an identifier, units, reference frame, nominal value, source or authored rationale, and acceptance bounds

#### Scenario: Verify geometry against the approved dossier
- **WHEN** generated geometry and joint centers are measured independently
- **THEN** each measurement satisfies the frozen dossier bounds
- **AND** declared generated landmark positions differ from their canonical coordinates by no more than `1e-4 H`
- **AND** a missing or out-of-bound measurement causes acceptance to fail

### Requirement: Whole-body mass metadata is explicit and separate from skeletal appearance

The canonical reference profile SHALL contain the R3 closed 16-segment point-mass model, separate from bone geometry and animation controls. Positive finite regional weights, rigid carrier-local points, reference normalization, mass-weight variants and source/adaptation provenance SHALL be inspectable. Geometry volume or the number of bones SHALL NOT stand in for whole-body mass. This introduces no muscle geometry or force solver.

#### Scenario: Validate and scale the mass model
- **WHEN** canonical mass records are validated and the profile is scaled to H=1.50/1.70/1.90 m
- **THEN** all 16 required IDs resolve to rigid carriers with normalized fractions summing to one within 1e-12, matching the R3 raw weights and point dossier
- **AND** point positions scale with stature while mass fractions and topology remain unchanged
- **AND** mirrored point records and reference/male/female coefficient variants preserve the declared source adaptation
- **AND** missing, extra, duplicate, nonfinite, zero/negative, unresolved, asymmetric or unprovenanced records fail before building

#### Scenario: Measure actual posed mass observations
- **WHEN** the backend evaluates each delivered squat pose
- **THEN** it exports each mass point using the actual posed carrier bone matrix and the declared local point
- **AND** independent verification recomputes source-bound point locations, normalization and weighted COM without substituting prepared control values or success flags
- **AND** absent or forged evidence fails acceptance and COM remains labeled an approximation including unrendered tissues

### Requirement: Coordinate and rotation conventions

Canonical space SHALL be right-handed, in meters, with `+X` the subject's right, `+Y` anterior, `+Z` superior, and floor `Z = 0`. Rotations SHALL be active unit quaternions ordered `[w,x,y,z]`. For each child, local orientation SHALL equal `q_rest * q_delta`; world orientation SHALL equal `q_parent_world * q_local`. `q_delta` acts in the bone's rest-local basis.

#### Scenario: Resolve rest and posed transforms
- **WHEN** every `q_delta` is identity
- **THEN** the documented T-pose is reproduced with an upright trunk, extended elbows and knees, arms horizontal, palms anterior, and feet facing anterior
- **AND** anatomical neutral and T-pose offsets are provided separately for interpreting mobility angles
- **AND** each local basis is explicitly recorded as an orthonormal right-handed basis with determinant `+1` within `1e-6`

#### Scenario: Validate quaternion semantics
- **WHEN** a declared local basis is subjected to a positive 90-degree rotation about its local X axis
- **THEN** local Y maps to local Z under the active right-hand rule
- **AND** parent rotation changes the world result according to the documented composition order
- **AND** `q` and `-q` are treated as the same orientation
- **AND** non-unit quaternions exceeding `1e-6` norm error are rejected rather than silently reinterpreted

### Requirement: Body groups and humanoid mapping

Every animation channel SHALL belong to exactly one smallest body group: `pelvis`, `torso`, `head_neck`, `arm_L`, `arm_R`, `leg_L`, or `leg_R`. The anatomical and control inventories SHALL map explicitly to versioned VRM humanoid semantics. Internal helpers SHALL remain separate from public humanoid bones; unavailable and many-to-one mappings SHALL be reported.

#### Scenario: Inspect the mapping contract
- **WHEN** the mapping is validated
- **THEN** all required humanoid entries resolve to existing animation bones, all required reference bones have a declared mapping or documented internal-only role, and no helper is misrepresented as a public humanoid bone
- **AND** hands belong to their arm groups and feet to their leg groups in this change
- **AND** shoulder-girdle controls have explicit ownership and a rule for coupling across groups
- **AND** no MPFB/Rigify mapping is asserted unless those actual backend bones were inspected and mapped

### Requirement: Rigid structure and bilateral mirroring

Rigid skeletal structures SHALL preserve their dimensions during posing; generated bone scale SHALL remain one. Left and right reference structures SHALL be mirrored through `X = 0`. Mirroring SHALL transform positions and orientations, swap side identifiers, preserve anatomical action meanings, and produce valid rotations rather than negative-scale bones.

#### Scenario: Check posing invariants
- **WHEN** all accepted diagnostic frames are measured
- **THEN** every rigid structure's dimensions and its attachment-to-attachment length differ from rest by no more than `1e-6 H`
- **AND** joint-center movement permitted by an explicit coupled-articulation model is checked against that model rather than mistaken for bone stretching
- **AND** no structure uses non-unit scale to satisfy an unreachable pose

#### Scenario: Mirror and mirror again
- **WHEN** a unilateral diagnostic is mirrored and the result is mirrored again
- **THEN** the first mirror swaps sides with landmark error at most `1e-4 H` and orientation error at most `0.1 degrees`
- **AND** the second mirror reproduces the original within the same bounds

### Requirement: Reproducible build and extensible attachments

A documented headless build SHALL generate skeletal geometry, animation controls, stable attachment identifiers, and verification metadata from canonical sources. Controls and geometry SHALL be distinguishable and separately hideable. Adding a future muscle attachment SHALL NOT require renaming the canonical skeleton or changing its rest transforms.

#### Scenario: Repeat a clean build
- **WHEN** two isolated builds use identical sources, settings, and the pinned Blender version
- **THEN** sorted skeletal topology, rest transforms, dimensions, and attachment identifiers agree within `1e-6 H` for positions and `1e-6` for rotation-matrix elements
- **AND** reports record source hashes, Blender and dependency versions, build settings, and comparison results
- **AND** the comparison excludes incidental binary-file ordering and timestamps

#### Scenario: Inspect attachment readiness
- **WHEN** the reviewer hides controls or geometry independently and resolves a declared attachment
- **THEN** the remaining representation is inspectable and the attachment resolves to a stable structure identifier and local frame
- **AND** muscles and soft-tissue simulation are absent from this change

### Requirement: Cleared references and provenance

Every external reference used for anatomy, dimensions, geometry, or backend construction SHALL have verified commercial and derivative permission compatible with project distribution and an entry in `docs/used-materials.md`. Source data SHALL carry provenance pointing to those entries; outputs SHALL preserve applicable attribution and identify modifications.

#### Scenario: Audit an anatomical claim or asset
- **WHEN** the reviewer follows a source identifier from a profile, fixture, or reference dossier
- **THEN** the register provides the specific material and portion, source and license URLs, permission basis, conditions, check date, and related outputs
- **AND** materials with ambiguous, non-commercial, or incompatible derivative terms fail clearance
- **AND** an illustration marked as used by permission is not assumed covered by the surrounding textbook license

### Requirement: Structural visual review pack

The build SHALL produce a structural review pack under `build/review/anatomical-human-skeleton/` containing labeled front, rear, and side orthographic views, rest and anatomical-neutral comparisons, local-axis overlays, and measurement and simplification reports. The pack SHALL support independent numeric checks and human visual judgment.

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

## Reference basis

- `hands-on-anatomy-2024`: Jacqueline Phillips and Michael O'Hara, *Hands-on Anatomy*, North Broad Press, 2024, authored skeletal-landmark and anatomical-movement text in chapters 1–9. CC BY 4.0; third-party permission-only illustrations are excluded. [Publisher and chapters](https://temple.manifoldapp.org/projects/hands-on-anatomy).
- `openstax-1e-thoracic-cage`: OpenStax, *Anatomy and Physiology*, first edition, section 7.4 text on sternal regions, posterior rib anatomy, and rib/cartilage classifications, retained by LibreTexts under an explicit CC BY 4.0 notice. No figures or measured contours used; this clearance is specific to the retained first-edition text. [Section and license notice](https://med.libretexts.org/Bookshelves/Anatomy_and_Physiology/Anatomy_and_Physiology_1e_(OpenStax)/Unit_2:_Support_and_Movement/07:_Axial_Skeleton/7.04:_The_Thoracic_Cage).
- `wang-2024-segment-lengths`: Shiou-An Wang et al., *Performance of Microsoft Azure Kinect DK as a tool for estimating human body segment lengths*, Scientific Reports 14, 15811 (2024), adult DXA rows of Table 1 and mechanical-axis definitions. CC BY 4.0. The four profile ratios average the published adult left/right means; other dimensions are not inferred from this study. [Article PDF](https://www.nature.com/articles/s41598-024-66798-0.pdf).

Numerical build tolerances and the supported stature checks are project acceptance choices, not estimates of biological variation. Remaining profile measurements must satisfy the reference-dossier gate above.
