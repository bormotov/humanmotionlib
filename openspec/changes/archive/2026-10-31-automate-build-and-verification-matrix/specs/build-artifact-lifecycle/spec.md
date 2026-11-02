# Spec Delta

## MODIFIED Requirements

### Requirement: Run identity is encoded in a flat directory name

Every new independently managed build, check or review run SHALL occupy a direct child of the selected workspace's `build/`. All writing callers SHALL explicitly select an absolute writable workspace independently of package resources; repository use SHALL explicitly select its checkout when intended. Its basename SHALL encode change, revision, role, attempt and kind in that order, separated by single underscores. Each component SHALL match `[a-z0-9]+(?:-[a-z0-9]+)*`. A new independent attempt SHALL use a fresh identity rather than overwrite an existing run. The narrow manual matrix exception SHALL use one predetermined five-component root per character/height, replacing only its declared current content and retaining attempt logs; callers SHALL not choose revision, role or attempt operands for it.

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


#### Scenario: Repeat one manual matrix element at its stable path
- **Verification:** list/build/check path assertions and two sequential complete builds.
- **WHEN** the contributor builds or checks the same supported character/height again
- **THEN** the matrix uses its predetermined direct child of build with exactly five valid components
- **AND** the runner derives that path automatically, without caller revision, role or attempt parameters
- **AND** repeated actions replace declared current content in that root and preserve only ordinary log files as attempt history
- **AND** this exception creates no UUID roots, nested independent attempts or publication copies; standalone callers retain fresh-run rules

### Requirement: Artifact content is distinct from independently managed runs

A run SHALL allow necessary internal content directories without encoding additional independent run identities in them. Existing accepted and explicitly protected historical outputs SHALL retain their paths and contents unless a separately approved migration changes them. Future path guidance SHALL distinguish this legacy exception and the explicit stable matrix exception from the rule for new independent runs. Preparation, render and presentation inside a selected matrix root SHALL be content for that one current result, not independently allocated runs.

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

Developer and reviewer hand-offs SHALL include cleanup after their checks finish, on success or failure. Cleanup SHALL remove obsolete generated runs and unnecessary residual files, including logs and JSON, while retaining accepted outputs, their required dependencies, active work and explicitly protected evidence. A skipped or interrupted cleanup SHALL be recorded as pending and completed before a completion claim. For the manual matrix, current required outputs and attempt log files SHALL be retained, while previous generated results and transient/failed data SHALL be removed; logs are an explicit preservation requirement for this workflow.

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

#### Scenario: Replace matrix data without deleting other work
- **Verification:** controlled success/failure/repeat cleanup with foreign files and symlink negatives.
- **WHEN** a selected matrix build finishes or is repeated
- **THEN** cleanup acts only on that element's known generated content and temporary files
- **AND** its logs, unrelated files, other elements, installed tooling and protected historical evidence remain unchanged
- **AND** removed paths/bytes and any cleanup failure are written to the action log, without another cleanup-history tree
