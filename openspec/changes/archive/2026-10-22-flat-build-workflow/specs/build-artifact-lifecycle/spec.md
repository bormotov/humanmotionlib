# Spec Delta

## Purpose

Keep generated build and verification runs identifiable and removable without losing accepted outputs or the evidence needed to verify them.

## ADDED Requirements

### Requirement: Run identity is encoded in a flat directory name

Every new independently managed build, check or review run SHALL occupy a direct child of `build/`. Its basename SHALL encode change, revision, role, attempt and kind in that order, separated by single underscores. Each component SHALL match `[a-z0-9]+(?:-[a-z0-9]+)*`. A new attempt SHALL use a fresh identity rather than overwrite an existing run.

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

### Requirement: Artifact content is distinct from independently managed runs

A run SHALL allow necessary internal content directories without encoding additional independent run identities in them. Existing accepted and explicitly protected historical outputs SHALL retain their paths and contents unless a separately approved migration changes them. Future path guidance SHALL distinguish this legacy exception from the rule for new runs.

#### Scenario: Keep required internal structure
- **Verification:** documentation comparison and filesystem inspection.
- **WHEN** a review command creates its frames, assets, reference data and tool-managed clean render passes inside one run
- **THEN** those content directories remain valid and are not flattened into thousands of files or independent sibling runs
- **AND** a separately initiated revision, reviewer attempt or derivative pack receives its own direct child of `build/`

#### Scenario: Continue work without relocating accepted history
- **Verification:** historical-path and requirement audit.
- **WHEN** the convention is adopted after `anatomical-human-skeleton` has been archived
- **THEN** its accepted pack, required predecessor evidence and expressly protected historical packs are not moved, regenerated or deleted by adoption
- **AND** examples consuming those historical paths identify them as existing inputs, while newly generated outputs follow the flat convention

### Requirement: Verification completion includes cleanup

Developer and reviewer hand-offs SHALL include cleanup after their checks finish, on success or failure. Cleanup SHALL remove obsolete generated runs and unnecessary residual files, including logs and JSON, while retaining accepted outputs, their required dependencies, active work and explicitly protected evidence. A skipped or interrupted cleanup SHALL be recorded as pending and completed before a completion claim.

#### Scenario: Finish a successful verification
- **Verification:** before/after inventory and link/evidence audit.
- **WHEN** checks complete and the accepted output and required evidence are identified
- **THEN** obsolete retries, redundant copies, temporary outputs and residual diagnostics without a continuing reason are removed
- **AND** the retained pack's required image, timing, provenance and numerical-evidence references still resolve
- **AND** every retained run or exceptional residual has a specific reason; a JSON/log extension alone is not a retention reason

#### Scenario: Finish failed or interrupted verification
- **Verification:** workflow dry run and hand-off record inspection.
- **WHEN** checks fail or a run is interrupted
- **THEN** only evidence needed to diagnose the failure, resume active work, satisfy an explicit preservation requirement, or support accepted outputs is retained
- **AND** the hand-off identifies the retained failure evidence, its reason and the event after which its necessity must be reconsidered
- **AND** an interruption that prevents cleanup leaves an explicit pending item rather than a statement that cleanup is complete

### Requirement: Cleanup respects ownership and records its result

Cleanup SHALL act only on identified generated outputs inside `build/`, without following symlinks outside it or deleting another active run. Reviewers SHALL remove only their own unprotected run outputs and request developer cleanup for other roots. The hand-off SHALL record removed paths and bytes, retained paths and reasons, and remaining pending work in an existing durable review or hand-off record.

#### Scenario: Remove a complete obsolete run safely
- **Verification:** controlled filesystem exercise and receipt inspection.
- **WHEN** an obsolete run has no retained dependent output and belongs to the cleaning agent
- **THEN** its entire run root is removed, rather than leaving unneeded JSON/log fragments and empty identity directories
- **AND** bytes removed and the retained dependency check are recorded with the cleanup result
- **AND** active, protected, external and out-of-scope paths remain unchanged

#### Scenario: Reviewer encounters obsolete developer output
- **Verification:** role-instruction audit and workflow dry run.
- **WHEN** a reviewer identifies obsolete developer output outside the reviewer's own run roots
- **THEN** the reviewer reports the exact paths and reasons to the developer instead of deleting them
- **AND** required cleanup remains pending until the developer reports completion
- **AND** the cleanup record is kept in an existing retained run or durable hand-off/report, without creating a new nested cleanup-history tree
