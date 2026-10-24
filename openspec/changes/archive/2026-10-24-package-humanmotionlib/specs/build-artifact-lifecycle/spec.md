# Spec Delta

## MODIFIED Requirements

### Requirement: Run identity is encoded in a flat directory name

Every new independently managed build, check or review run SHALL occupy a direct child of the selected workspace's `build/`. For repository use the checkout SHALL be that workspace; installed use SHALL select a writable caller-owned workspace independently of package resources. Its basename SHALL encode change, revision, role, attempt and kind in that order, separated by single underscores. Each component SHALL match `[a-z0-9]+(?:-[a-z0-9]+)*`. A new attempt SHALL use a fresh identity rather than overwrite an existing run.

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

