# build-artifact-lifecycle Specification

## Purpose

Keep generated build and verification runs identifiable and removable without losing accepted outputs or the evidence needed to verify them.

## Requirements

### Requirement: Run identity is encoded in a flat directory name

Every new independently managed build, check or review run SHALL occupy a direct child of the selected workspace's `build/`. All writing callers SHALL explicitly select an absolute writable workspace independently of package resources; repository use SHALL explicitly select its checkout when intended. Its basename SHALL encode change, revision, role, attempt and kind in that order, separated by single underscores. Each component SHALL match `[a-z0-9]+(?:-[a-z0-9]+)*`. A new independent attempt SHALL use a fresh identity rather than overwrite an existing run. The narrow manual matrix exception SHALL use one predetermined five-component root per character/height, replacing only its declared current content and retaining attempt logs until an explicit Make cleanup target selects their area; callers SHALL not choose revision, role or attempt operands for it.

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
- **AND** output ownership, input/output separation, symlink checks, fresh attempts and cleanup within declared generated areas follow the same rules as repository runs
- **AND** selecting a different workspace does not relocate or modify existing inputs, and no run is allocated beneath installed resources; explicit cleanup may later remove local inputs within its declared generated areas.

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
- **AND** repeated actions replace declared current content in that root and preserve ordinary log files as attempt history until an explicit Make cleanup target removes their area
- **AND** this exception creates no UUID roots, nested independent attempts or publication copies; standalone callers retain fresh-run rules

### Requirement: Artifact content is distinct from independently managed runs

A run SHALL allow necessary internal content directories without encoding additional independent run identities in them. Ordinary generation SHALL leave existing historical inputs unchanged. Explicit Make cleanup SHALL remove all contents selected by its fixed areas, including local accepted/protected history; no history-specific exception or dependency scan SHALL apply. Durable results SHALL be stored outside those generated areas. Future path guidance SHALL distinguish generation from explicit cleanup and the stable matrix exception. Preparation, render and presentation inside a selected matrix root SHALL be content for that one current result, not independently allocated runs.

#### Scenario: Keep required internal structure
- **Verification:** documentation comparison and filesystem inspection.
- **WHEN** a review command creates its frames, assets, reference data and tool-managed clean render passes inside one run
- **THEN** those content directories remain valid and are not flattened into thousands of files or independent sibling runs
- **AND** a separately initiated revision, reviewer attempt or derivative pack receives its own direct child of `build/`

#### Scenario: Continue work without relocating accepted history
- **Verification:** historical-path and requirement audit.
- **WHEN** the convention is adopted after `anatomical-human-skeleton` has been archived
- **THEN** ordinary adoption does not move or regenerate earlier packs or predecessor inputs; an explicit Make cleanup can remove them when they lie inside its declared areas
- **AND** examples consuming those historical paths identify them as existing inputs, while newly generated outputs follow the flat convention

### Requirement: Verification completion includes cleanup

Developer and reviewer hand-offs SHALL include cleanup after success or failure and record its outcome. Fixed Make cleanup areas SHALL determine removal, including unknown files, logs and local accepted history; active work SHALL block unsafe removal. Missing/interrupted cleanup SHALL remain pending. Ordinary matrix actions SHALL retain current results and attempt logs, while explicit clean/distclean SHALL remove them. No separate cleanup ownership inventory or legacy dependency scan SHALL be required.

#### Scenario: Finish a successful verification
- **Verification:** before/after area checks and durable report inspection.
- **WHEN** checks complete and the accepted output and required evidence are identified
- **THEN** the selected cleanup rules remove their generated areas, including obsolete retries, temporary outputs and residual diagnostics
- **AND** sources in version control and any results already stored outside the cleanup areas remain unchanged; local references into removed areas have no preservation guarantee
- **AND** surviving local areas are explained by the selected level; a historical label, JSON/log extension or missing producer marker does not create an exemption

#### Scenario: Finish failed or interrupted verification
- **Verification:** workflow dry run and hand-off record inspection.
- **WHEN** checks fail or a run is interrupted
- **THEN** active work is not removed; an explicit cleanup removes all inactive contents in its selected areas, including failed diagnostics and local evidence
- **AND** the hand-off records the selected cleanup level, completed removals and pending failures without adding a local protected-history mechanism
- **AND** an interruption that prevents cleanup leaves an explicit pending item rather than a statement that cleanup is complete

### Requirement: Cleanup respects ownership and records its result

Cleanup SHALL act only within the fixed generated areas inside build, without following symlinks or deleting active work. Explicit Make cleanup SHALL select all contents in those areas regardless of producer or historical status. Role-scoped automatic cleanup SHALL remain inside its assigned area. The existing durable report SHALL record removed paths/bytes and pending failures; no separate owner/file inventory or reference scan SHALL be required.

#### Scenario: Remove a complete obsolete run safely
- **Verification:** controlled filesystem exercise and receipt inspection.
- **WHEN** an inactive run lies inside the selected cleanup area
- **THEN** its entire run root is removed, rather than leaving unneeded JSON/log fragments and empty identity directories
- **AND** removed paths/bytes and any failure are recorded with the cleanup result without a dependency scan
- **AND** active work blocks removal, external/out-of-scope paths remain unchanged and local historical status does not exempt an in-scope run

#### Scenario: Reviewer encounters obsolete developer output
- **Verification:** role-instruction audit and workflow dry run.
- **WHEN** a reviewer performing role-scoped automatic cleanup identifies output outside its assigned area
- **THEN** the reviewer reports that work to the orchestrator instead of silently broadening its assigned area; an explicitly requested Make cleanup uses its declared wider scope
- **AND** required cleanup remains pending until the responsible scoped action completes
- **AND** the cleanup record is kept in an existing retained run or durable hand-off/report, without creating a new nested cleanup-history tree

#### Scenario: Replace matrix data without deleting other work
- **Verification:** controlled success/failure/repeat cleanup with foreign files and symlink negatives.
- **WHEN** a selected matrix build finishes or is repeated
- **THEN** cleanup acts only on that element's known generated content and temporary files
- **AND** ordinary action cleanup keeps its logs, unrelated files and other elements unchanged; a later explicit Make cleanup removes everything selected by its declared areas, including those logs
- **AND** removed paths/bytes and any cleanup failure are written to the action log, without another cleanup-history tree

### Requirement: Make cleanup has three explicit levels

Make SHALL provide argument-free mostlyclean, clean and distclean using fixed generated-file areas and patterns. Each selected area SHALL be removed completely, including unknown files and local history. Mostlyclean SHALL keep completed results and reusable tools; clean SHALL keep reusable tools only; distclean SHALL remove those tools too. Versioned source and external artifact storage SHALL remain outside these areas.

#### Scenario: Remove intermediate work while retaining useful builds
- **WHEN** make mostlyclean runs with inactive local build data
- **THEN** it removes direct children of build/ matching *_stage or *_check, including all their nested contents
- **AND** completed package/preview results and the configured reusable tools directory remain
- **AND** marker files, producer inventories and reference scans are not required to select or remove a matching area
- **Verification:** disposable matching/nonmatching directories with unknown nested files, repeated calls and unchanged completed-result hashes.

#### Scenario: Retire ordinary results but retain prepared tools
- **WHEN** make clean runs with inactive local build data
- **THEN** it removes every direct child of build/ except the one reusable tools directory fixed by committed project configuration, including dotfiles, unknown entries, matrix logs and historical character/review results
- **AND** the configured tools directory (default build/project-tools_r1_contributor_current_environment/) and everything outside build/ remain
- **AND** a historical or protected label does not exempt an entry in the selected area
- **Verification:** exact deletion table on a disposable build tree containing ordinary, unknown, matrix-log and R6-like entries without ownership records.

#### Scenario: Remove project-prepared tools for a fresh rebuild
- **WHEN** make distclean runs with inactive local build data
- **THEN** the entire local build/ area is removed, including prepared tools, dependency caches, project-downloaded Python, unknown entries and local history
- **AND** versioned authoring/configuration/lock files outside build, Git state, dist/ releases, system tools/global caches and external artifact storage remain unchanged
- **Verification:** disposable local/global/artifact-storage fixtures and before/after source/configuration/release hashes.

### Requirement: Cleanup is confined to declared generated areas

Cleanup SHALL derive its removal areas from fixed project rules. Everything inside a selected area SHALL be disposable regardless of ownership markers, file inventories, references or historical status. Cleanup SHALL NOT scan legacy dependencies or consult a separate cleanup manifest. It SHALL remain inside the selected workspace's real build/ directory and SHALL never traverse symbolic links.

#### Scenario: Remove unknown work inside a selected area
- **WHEN** a matching cleanup area contains unknown files, legacy names, local evidence or references to other local results
- **THEN** all selected entries are removed without an ownership/dependency classification or special history-preservation step
- **AND** entries outside that level's declared area remain untouched
- **AND** cleanup does not promise that references from surviving local files into removed areas will remain usable
- **Verification:** mixed known/unknown/reference fixtures with no registration files and exact inside/outside assertions.

#### Scenario: Stop before removing active or uncheckable candidates
- **WHEN** a selected area is in use by active work, or required process/path inspection cannot establish that removal is safe
- **THEN** cleanup exits nonzero before any removal and identifies the blocker and retry/remedy
- **AND** it neither terminates the process nor treats missing visibility as proof of inactivity
- **Verification:** real controlled active-process and denied-inspection cases with zero-deletion controls.

#### Scenario: Do not traverse generated links
- **WHEN** an entry inside a selected cleanup area is a symbolic link
- **THEN** cleanup removes the link entry without traversing or changing its target, including targets outside build or in another local result
- **AND** a symbolic-link workspace/build boundary or an escaping configured removal area fails before removal
- **Verification:** inward/outward/broken-link fixtures, target hashes and invalid-boundary controls.

### Requirement: Cleanup reports completion and supports safe repetition

Cleanup SHALL report its level, selected areas, removed paths/bytes and pending failures without preparing tools or creating a new history run. Missing areas SHALL count as already clean. A failed or interrupted removal SHALL return nonzero and retain enough command output for a safe repeat. It SHALL NOT label partial removal complete.

#### Scenario: Repeat cleanup or diagnose a partial failure
- **WHEN** cleanup runs on an empty checkout, repeats successfully or encounters a removal error/interruption
- **THEN** absent areas need no repair, repetition is harmless and failure reports completed removals and unresolved targets
- **AND** managed development/review records the outcome in its existing durable report, without a cleanup inventory or legacy-reference scan
- **Verification:** empty/repeat/permission/interruption controls, exit statuses, byte accounting and no-new-tool/history assertions.

### Requirement: Normal builds restore cleaned project state

After cleanup, ordinary package, development-preparation and selected-preview commands SHALL recreate required tools and results using project defaults. Checks SHALL refuse absent results without filesystem writes and retain diagnostics for started attempts against existing results. Sources remain in version control and durable published results belong in external artifact storage; cleanup SHALL not implement transfer or archival.

#### Scenario: Rebuild after each cleanup level
- **WHEN** an ordinary default build follows mostlyclean, clean or distclean
- **THEN** required tools/results are recreated without manual path/cache/environment repair
- **AND** Make and direct existing-result checks after removal give the exact selected rebuild command without creating directories, logs or reports or starting generation
- **AND** checks that start against an existing result retain their ordinary attempt log and current report, including validation failures, without changing recorded sources
- **AND** cleanup and restoration do not resume paused character verification or grant a new visual decision
- **Verification:** literal package/dev and controlled selected-preview restoration after each level plus check-only no-generation controls.
