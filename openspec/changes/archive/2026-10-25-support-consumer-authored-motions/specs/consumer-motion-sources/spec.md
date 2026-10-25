# Spec Delta

## Purpose

Let an installed HML consumer supply and retain its own declarative movement intent, including variants of packaged fixtures, with explicit validation and attributable, portable generation inputs.

## ADDED Requirements

### Requirement: Consumer inputs have a closed declarative source contract

HML SHALL accept one versioned consumer-motion document per preparation, as an in-memory mapping or local YAML/JSON file. The document SHALL contain a complete definition in the supported diagnostic action language or a packaged-fixture variant, with description, license and provenance. Unknown fields, unsupported formats, executable content and unsupported composition SHALL fail before output creation.

#### Scenario: Submit equivalent source representations
- **Verification:** schema and installed API tests with mapping, YAML and JSON inputs.
- **WHEN** equivalent valid consumer documents are supplied in each supported representation
- **THEN** their canonical source identity, resolved movement, poses and exact timelines agree
- **AND** the source is copied before processing and the caller's mapping/file remains unchanged
- **AND** no Blender probe or process occurs during preparation.

#### Scenario: Reject unsupported or ambiguous documents
- **Verification:** parser/schema mutation matrix and filesystem/process interception.
- **WHEN** a document contains duplicate mapping keys, an unsupported version/constructor, unknown fields, non-finite or boolean numeric values, both source alternatives, Python expressions, unresolved references, or a general segment-composition request
- **THEN** preparation raises a catchable source-validation failure before creating output
- **AND** diagnostic schemas are resolved offline from the installed package, never from a caller-supplied URL.

### Requirement: Variants preserve explicit base identity and override meaning

A variant SHALL identify one packaged base fixture and its own distinct identifier, metadata and provenance. Its declared track scales and complete track replacements SHALL resolve deterministically without modifying the base. Unknown targets, duplicate or conflicting overrides, non-finite factors and implicit constructor changes SHALL fail. Base identity and inherited attribution SHALL remain available independently of the contribution's provenance.

#### Scenario: Scale explicit squat tracks
- **Verification:** numeric source-resolution comparison and package-resource hashes.
- **WHEN** a consumer scales both knee tracks and its explicitly selected ankle, pelvis-pitch and lumbar-flexion tracks of the packaged squat
- **THEN** each selected key value equals the base value multiplied by its supplied factor at the original beat and easing
- **AND** unspecified tracks, controls, rest policy, construction, contacts, root and duration retain their base values
- **AND** the original packaged squat remains at its approved 90-degree knee peak
- **AND** output identifies both the base source/hash and the consumer contribution/hash.

#### Scenario: Replace one track without hidden merging
- **Verification:** resolver tests for replacement order, unknown targets and conflicts.
- **WHEN** a variant replaces an existing track with an explicit complete track and leaves other tracks untouched
- **THEN** that replacement supplies its entire key/easing record and passes the same checks as a complete definition
- **AND** a track targeted by both scaling and replacement, or a requested base from another consumer document, is rejected.

### Requirement: Consumer motion semantics are checked before persistence

Consumer definitions SHALL obey the selected packaged profile, channel ownership, controls, supported constructor semantics, integer-beat events and existing units. Unsupported independent writes, duplicate writers, cyclic bases and unprovided hold/free context SHALL fail. Validation SHALL include constructor-derived writes and effective overrides, rather than schema shape alone.

#### Scenario: Reject a source that has valid shape but invalid semantics
- **Verification:** semantic mutation tests naming the source and field.
- **WHEN** a source has a profile mismatch, unsafe/colliding identifier, unknown channel/anchor, omitted moving body group, dependent-channel write, constructor-owned channel overwrite, invalid key ordering, fractional event, inconsistent constructor data, cyclic base, or unsupported rest context
- **THEN** preparation fails with its source identity and field path
- **AND** no prepared file, backend receipt or successful result is created.

#### Scenario: Preserve body groups and root intent
- **Verification:** source-to-solved ownership and rational timeline checks.
- **WHEN** a valid four-beat consumer definition uses the closed-chain squat constructor
- **THEN** its pelvis, torso, leg and arm writes remain inside its declared controls, and other groups follow its explicit base policy
- **AND** its declared root, contact intent and beat events survive resolution and stature scaling under the existing meter/degree conventions
- **AND** static and animation timelines share pose identities under the existing BPM sampling rule.

### Requirement: Parameter validation checks solved movement without correction

Preparation SHALL check consumer movement at every delivered sample, key/contact event and a dense grid spaced at most 0.01 beats. Existing mobility/coupling bounds and declared skeletal-contact tolerances SHALL apply. Invalid intent SHALL fail with time, channel/constraint, value/residual and allowed condition, without clamping, target changes, bone stretching or scene changes. This check SHALL NOT claim evaluated-mesh, clinical or human acceptance.

#### Scenario: Reject infeasible movement before rendering
- **Verification:** boundary, coupled-condition and unreachable-contact fault matrix.
- **WHEN** finite input requests an out-of-range action, an invalid coupled pose, a failure between delivered frames, or an unsatisfied foot contact
- **THEN** preparation fails before writing with the offending beat and measured or requested value and applicable bound/residual
- **AND** contact target and sliding checks use the existing 0.001-stature tolerance
- **AND** no floor/camera/root adjustment hides the failure.

### Requirement: Consumer preparation has explicit work bounds

Consumer preparation SHALL support integer durations from 0 through 256 beats and at most 100000 unique delivered pose samples per request. It SHALL reject requests exceeding either bound before allocating sample collections, dense evaluation or output. These consumer limits SHALL NOT change existing packaged-diagnostic defaults or BPM semantics.

#### Scenario: Reject an excessive source or sampling request
- **Verification:** limit-boundary tests with allocation/evaluation/write interception.
- **WHEN** a consumer definition exceeds 256 beats or its requested BPM union would exceed 100000 delivered pose samples
- **THEN** preparation fails before solving, sample allocation or output creation, with the offending duration or sample budget
- **AND** finite very small BPM values are checked by their computed cardinality rather than allocating an excessive timeline first.

### Requirement: Consumer clearance records remain resolvable and additive

Every external material referenced by consumer provenance SHALL resolve to a packaged clearance entry or a complete supplied clearance record with commercial, derivative and distribution permission. Conflicting identifiers and missing, ambiguous, non-commercial, no-derivatives or incompatible terms SHALL fail. Authored contributions without external sources SHALL be allowed; inherited base/profile attribution SHALL remain mandatory.

#### Scenario: Retain a consumer's cleared reference
- **Verification:** nested provenance traversal, clearance-schema tests and portable projection audit.
- **WHEN** a consumer document references a material absent from the packaged register and supplies a complete supported clearance record
- **THEN** the prepared/result provenance includes material/part, source and license URLs, permission basis, conditions/attribution, checked date and related outputs
- **AND** base, profile and mobility materials remain present and unmodified
- **AND** validation is described as offline checking of supplied declarations, without claiming independent legal verification.

#### Scenario: Reject unresolved or incompatible attribution
- **Verification:** missing-entry, duplicate-ID, conflicting-ID, incomplete-evidence and NC/ND mutation tests.
- **WHEN** referenced clearance is missing or incomplete, uses an unsupported/incompatible license, or a supplied identifier collides with a packaged material
- **THEN** preparation fails before output creation and identifies the affected material
- **AND** an empty source list is accepted only for a contribution explicitly marked authored.

### Requirement: Prepared consumer inputs are self-contained and integrity checked

Prepared inputs SHALL seal the submitted consumer document, clearance records, resolved definition and base lineage separately from installed-package resource hashes. Host rendering SHALL validate and replay the persisted snapshot against the active package before starting Blender, without rereading consumer files or trusting mutable result metadata. Invalid lineage or stale source-to-resolution identity SHALL fail with an integrity error.

#### Scenario: Render after the source project is unavailable
- **Verification:** installed-wheel preparation/render test with deleted source file, unrelated working directory and snapshot mutation faults.
- **WHEN** a valid consumer source is prepared and its original mapping/file is later changed or removed
- **THEN** rendering the prepared file still uses its sealed submitted and resolved content
- **AND** all writes stay in the existing disjoint caller-workspace runs
- **AND** altered snapshot hashes, base identities, resolved definitions or sample references prevent rendering before Blender launches.

### Requirement: Source validation and backend integrity have explicit boundaries

Host preparation and rendering SHALL perform consumer schema, provenance, lineage, resolution and solved-sample checks. Blender SHALL verify the prepared seal, active package/source hashes, sample references and the exact host-validated prepared identity using only its standard library and HML. Blender SHALL NOT import host YAML/schema dependencies or claim independent source validation.

#### Scenario: Validate on host before entering the backend
- **Verification:** installed API tamper/reseal matrix with probe/process interception and dependency-isolated backend reading.
- **WHEN** a consumer snapshot is passed to rendering
- **THEN** host Python reparses installed sources, validates the persisted consumer schema/provenance, resolves base lineage and repeats dense preflight/sample/timeline reconstruction before any Blender probe or launch
- **AND** missing or invalid semantic/provenance evidence, including a resealed inconsistent payload, fails at that host stage
- **AND** Blender's integrity reader works without importing YAML, JSON Schema, schema-registry or host site-packages and does not repeat those source checks.

#### Scenario: Reject replacement after host validation
- **Verification:** controlled mutation between host validation and backend input reading, plus missing/mismatched expected-identity cases.
- **WHEN** prepared content changes after host validation, even if it is given a new internally consistent content seal
- **THEN** Blender rejects it before constructing the scene because its canonical prepared identity differs from the identity supplied by the validated host invocation
- **AND** a missing expected identity cannot authorize a consumer snapshot
- **AND** successful receipt, script-phase and output identities all refer to the same host-validated prepared content.

### Requirement: Consumer examples distinguish parameter support from exercise acceptance

Documentation and independent verification SHALL demonstrate consumer-selected squat depth and a complete consumer definition through the installed public API. Technical test values SHALL be labeled as verification inputs. The change SHALL add no production exercise or prescribed amplitude. Existing diagnostic regression, numeric evidence and the focused visual pack SHALL be reported separately.

#### Scenario: Review externally selected depth
- **Verification:** installed example, numeric assertions, clean backend comparisons and explicit human visual review.
- **WHEN** the documented example is called with explicit test depths 30 and 60 degrees at BPM 90
- **THEN** each four-beat variant reaches its supplied knee peak at beat 2 within 0.1 degrees and has five static and seventeen animation entries
- **AND** the packaged 90-degree diagnostic is unchanged
- **AND** the human receives front/side count and in-between sheets, timed GIFs and descent/ascent onion-skin comparisons for all three depths
- **AND** no test value, numeric pass or successful render is labeled a recommended exercise or human visual approval.
