# Spec Delta

## Purpose

Keep project and agent instructions consistent about timing, source permissions, scoped contact decisions, workflow gates and safe reviewer cleanup authority.

## ADDED Requirements

### Requirement: Beat sampling is explicit
The project instructions SHALL define one beat as the timing unit, require static samples at every beat boundary, and define animation subdivision using the duration of one beat.

#### Scenario: Sampling a full-beat transition
- **WHEN** a segment spans one beat of duration `T_beat`
- **THEN** animation sampling uses `n = max(3, ceil(T_beat / 200 ms))` intervals for that beat, with segment boundaries on frame boundaries
- **AND** static sampling includes the beat boundary
- **Verification:** local instruction-policy audit and arithmetic checks at BPM 60/120/180; runtime sampling remains verified by its owning implementation change.

### Requirement: Project licenses and motion provenance are explicit
The project instructions SHALL assign Apache-2.0 to project code and CC-BY-4.0 to library data and authored assets, and SHALL require provenance for each pose, segment, and motion.

#### Scenario: A motion is authored or composed
- **WHEN** a motion is added to the library
- **THEN** its source or derivation is recorded in provenance, and the applicable library data license is identified
- **Verification:** audit of project/role licensing and provenance instructions; runtime schema enforcement remains verified by its owning implementation change.

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
The project instructions SHALL defer IK target coordinate space, normalization and units to the change introducing each concrete contact feature. They SHALL preserve representation contracts already established by accepted feature specifications rather than treating every IK/contact representation as globally unresolved.

#### Scenario: A contact feature is proposed
- **WHEN** an OpenSpec change introduces IK targets or contacts
- **THEN** that change defines the target representation and its verification criteria before implementation
- **Verification:** audit of the general glossary/role instructions and the scoped feature specification.

#### Scenario: A scoped contact contract already exists
- **WHEN** governance instructions are reconciled after anatomical contact requirements have been accepted
- **THEN** the general open-question wording does not override `anatomical-skeleton` coordinate conventions or `joint-mobility` contact intent and floor measurements
- **AND** this instruction alignment does not alter those feature contracts or require their existing diagnostics to be rebuilt
- **Verification:** comparison with the accepted `anatomical-skeleton` and `joint-mobility` requirements and scope audit of this change.

### Requirement: OpenSpec lifecycle stays ordered while independent tasks may run in parallel
The project workflow SHALL require an approved OpenSpec change before implementation and review before archive, while allowing independent implementation tasks within that approved change to run in parallel.

#### Scenario: Independent implementation tasks
- **WHEN** tasks in an approved change are independent and have non-conflicting ownership
- **THEN** they may be delegated concurrently, while the change still follows the architect, implementation, review, and archive lifecycle
- **Verification:** review of project and subagent instructions.

#### Scenario: Implementation and acceptance use separate responsibilities
- **WHEN** an approved change is implemented and reviewed
- **THEN** the main agent orchestrates and manages OpenSpec artifacts while implementation and independent verification are delegated to their respective roles
- **AND** review precedes archive and a change affecting poses, motions, scene or rendering also requires the human's visual approval before archive
- **Verification:** audit of project and role instructions and their change-level gates.

### Requirement: Reviewer cleanup is bounded
The reviewer SHALL clean only its own unprotected flat run outputs under `build-artifact-lifecycle`. It SHALL preserve accepted outputs, required dependencies, protected history and other agents' active or owned runs, and SHALL request developer cleanup for other roots. Its durable review report SHALL record cleanup and any pending work.

#### Scenario: Start a fresh owned review run
- **WHEN** a reviewer starts verification for a change with earlier build or review outputs
- **THEN** it allocates a fresh direct child of `build/` named `<change>_<revision>_reviewer_<attempt>_<kind>/` with exactly five underscore-separated lowercase-kebab components
- **AND** prior review packs, accepted legacy paths and protected predecessor evidence are not removed, replaced or relocated merely because they belong to the same change
- **Verification:** audit of reviewer instructions, accepted lifecycle requirements and the recorded run path.

#### Scenario: Complete checks and clean owned outputs
- **WHEN** review checks finish successfully, fail or are interrupted
- **THEN** the reviewer inventories its owned outputs and required dependencies before cleanup, removes obsolete unprotected whole run roots or unnecessary internal diagnostics, and checks retained references afterward
- **AND** it does not follow symlinks outside `build/`, remove another agent's outputs, or use a JSON/log extension alone as a retention reason
- **AND** `review.md` records removed paths/bytes, retained paths/reasons, dependency-check results and pending cleanup; unresolved cleanup prevents a completion claim
- **Verification:** role-instruction audit and review of the independent check run's cleanup receipt against `build-artifact-lifecycle`.

#### Scenario: Verification needs cleanup outside reviewer ownership
- **WHEN** required cleanup concerns developer-owned or other out-of-scope build output
- **THEN** the reviewer reports exact paths and reasons to the developer rather than deleting the output
- **AND** cleanup remains pending and obstructed verification waits until the developer reports resolution
- **Verification:** review of reviewer/developer hand-off instructions and any cleanup hand-off recorded for this review.
