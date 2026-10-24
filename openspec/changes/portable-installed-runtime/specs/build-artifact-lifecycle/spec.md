# Spec Delta

## MODIFIED Requirements

### Requirement: Run identity is encoded in a flat directory name

Every new independently managed build, check or review run SHALL occupy a direct child of the selected workspace's `build/`. All writing callers SHALL explicitly select an absolute writable workspace independently of package resources; repository use SHALL explicitly select its checkout when intended. Its basename SHALL encode change, revision, role, attempt and kind in that order, separated by single underscores. Each component SHALL match `[a-z0-9]+(?:-[a-z0-9]+)*`. A new attempt SHALL use a fresh identity rather than overwrite an existing run.

#### Scenario: Allocate an identifiable review attempt
- **Verification:** documented-path audit and filesystem inspection.
- **WHEN** a reviewer allocates revision `r3`, attempt `fix-try`, kind `pack` for `anatomical-human-skeleton`
- **THEN** the run root is `build/anatomical-human-skeleton_r3_reviewer_fix-try_pack/`
- **AND** splitting the basename on `_` recovers exactly the five original components
- **AND** a retry uses a different attempt component and does not create a run below this directory or overwrite its contents

#### Scenario: Reject ambiguous or nested run identity before writing
- **Verification:** workflow dry run with invalid path examples.
- **WHEN** allocation of a new independent run uses a component containing `_`, omits a component, reuses an occupied run root, or encodes stage/attempt identity as nested directories
- **THEN** the operator corrects the destination before launching a generating command
- **AND** a new independent output run inside a separate input/predecessor run tree, or containing that tree, is rejected before writing

#### Scenario: Allocate an installed-workflow run
- **Verification:** installed command path assertions and immutable-package filesystem audit.
- **WHEN** an installed user selects a workspace and allocates a build or review attempt
- **THEN** its run is a direct child of that workspace's build directory using the same five-component identity
- **AND** output ownership, input/output separation, symlink checks, fresh attempts and dependency-aware cleanup follow the same rules as repository runs
- **AND** selecting a different workspace does not relocate or modify accepted/protected legacy inputs, and no run is allocated beneath installed resources.

#### Scenario: Validate destinations before creating filesystem state
- **Verification:** CLI/API matrix with traversal, symlink escape, occupied run, overlapping input/output and invalid workspace cases.
- **WHEN** a caller requests a new independently managed run or numerical report output
- **THEN** relative operands are resolved against the explicit workspace and all generated artifacts are confined to its permitted build runs after symlink resolution
- **AND** the input and independent output roots are disjoint, fresh run allocation retains its five-component convention and report content may live inside its owning run
- **AND** invalid destinations fail before HML creates temporary files, logs, lock state or output directories.

#### Scenario: Read protected predecessors without lexical checkout inference
- **Verification:** installed HTML-only and reuse tests with protected external predecessor paths, missing build components and multiple ancestor build components.
- **WHEN** a caller explicitly identifies a compatible existing predecessor outside the output workspace
- **THEN** HML checks its required identity, hashes, evidence and dependency links using the actual predecessor location and evidence
- **AND** it does not infer a checkout or workspace from the first path component named build or from a neighboring directory
- **AND** missing or incompatible evidence still fails closed and HTML-only operation launches no Blender
- **AND** historical inputs remain unchanged, the independent output run remains disjoint, and existing presentation asset/link rules apply.
