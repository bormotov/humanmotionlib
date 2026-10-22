# Spec Delta

## ADDED Requirements

### Requirement: Beat sampling is explicit
The project instructions SHALL define one beat as the timing unit, require static samples at every beat boundary, and define animation subdivision using the duration of one beat.

#### Scenario: Sampling a full-beat transition
- **WHEN** a segment spans one beat of duration `T_beat`
- **THEN** animation sampling uses `n = max(3, ceil(T_beat / 200 ms))` intervals for that beat, with segment boundaries on frame boundaries
- **AND** static sampling includes the beat boundary
- **Verification:** timing specification review and numeric sampling checks in a later implementation change.

### Requirement: Project licenses and motion provenance are explicit
The project instructions SHALL assign Apache-2.0 to project code and CC-BY-4.0 to library data and authored assets, and SHALL require provenance for each pose, segment, and motion.

#### Scenario: A motion is authored or composed
- **WHEN** a motion is added to the library
- **THEN** its source or derivation is recorded in provenance, and the applicable library data license is identified
- **Verification:** schema validation and provenance review in a later implementation change.

#### Scenario: An external reference or input is considered
- **WHEN** an agent plans to use a textbook, paper, illustration, description, video, dataset, web page, or third-party asset to perform a task or inform a project output
- **THEN** the agent verifies that the specific material's license explicitly permits commercial use of the resulting work and is compatible with the intended distribution before using it
- **AND** if permission is missing, ambiguous, non-commercial, prohibits the intended derivative, or has incompatible conditions, the material is not used
- **Verification:** reviewer checks the license evidence and the change's actual source usage.

#### Scenario: A cleared source informs project work
- **WHEN** any external material actually informs a task or project output
- **THEN** it is listed in `docs/used-materials.md` with its specific material, source link, license/version and license link, commercial/derivative permission basis, conditions, check date, and related outputs
- **AND** it is listed even when it is CC0/public domain or attribution is not required
- **AND** related pose, segment, or motion provenance refers to the register entry
- **Verification:** reviewer cross-checks source use, register entries, provenance, and license conditions.

### Requirement: Open IK representation remains unresolved until scoped
The project instructions SHALL leave IK target coordinate space, normalization, and units open until a concrete contact requirement is specified.

#### Scenario: A contact feature is proposed
- **WHEN** an OpenSpec change introduces IK targets or contacts
- **THEN** that change defines the target representation and its verification criteria before implementation
- **Verification:** review of the change specification.

### Requirement: OpenSpec lifecycle stays ordered while independent tasks may run in parallel
The project workflow SHALL require an approved OpenSpec change before implementation and review before archive, while allowing independent implementation tasks within that approved change to run in parallel.

#### Scenario: Independent implementation tasks
- **WHEN** tasks in an approved change are independent and have non-conflicting ownership
- **THEN** they may be delegated concurrently, while the change still follows the architect, implementation, review, and archive lifecycle
- **Verification:** review of project and subagent instructions.

### Requirement: Reviewer cleanup is bounded
The reviewer SHALL clean prior outputs only within its review-output scope and SHALL request developer cleanup when verification requires deleting other build outputs.

#### Scenario: Existing review pack is present
- **WHEN** a reviewer starts verification for a change with existing files in `build/review/<change-id>/`
- **THEN** the reviewer may remove or replace those files as part of producing a clean review pack
- **AND** if other build outputs must be removed, the reviewer asks the developer to clean them and waits before continuing
- **Verification:** review of reviewer instructions and resulting file changes.
