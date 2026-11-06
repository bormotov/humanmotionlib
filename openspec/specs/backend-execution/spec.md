# backend-execution Specification

## Purpose

Make repository-owned Blender execution bounded and diagnosable, so native process failures cannot silently become successful build or review evidence.

## Requirements

### Requirement: Routine backend work has one controlled execution path

Documented routine builds, render passes, backend probes and Blender integration tests SHALL use a shared supervised execution policy in both source and installed workflows. It SHALL preserve executable resource discovery, the pinned version/build check, factory-startup isolation for scripts and explicit nonzero exit on Python exceptions. Installed execution SHALL resolve its script/import closure from the package without injecting the host environment into Blender. It SHALL NOT launch a GUI application as an automatic recovery action.

#### Scenario: Inspect and build with the pinned backend
- **Verification:** launcher argument assertions, mismatch tests and one real headless build.
- **WHEN** a routine build or render is requested using a PATH entry that resolves to the pinned executable
- **THEN** probing and script execution use its resolved executable, without a hard-coded application path
- **AND** script execution is background/factory-startup and uncaught Python exceptions produce a nonzero child exit
- **AND** a mismatched or unidentifiable version/build prevents script execution and fails the request
- **AND** pose data, body group controls, rest policies, contacts and beat sampling are not changed by the execution policy

#### Scenario: Keep presentation-only work independent of Blender
- **Verification:** process-spawn interception and existing presentation regression tests.
- **WHEN** the existing HTML-only review-pack mode is used
- **THEN** no Blender probe or Blender process is launched and media/evidence hashes retain their current contract

#### Scenario: Launch an installed backend without the checkout
- **Verification:** real wheel-installed build with absent checkout imports and host-environment isolation assertions.
- **WHEN** installed HML launches the pinned Blender from a caller-owned workspace
- **THEN** the package supplies the entry script and all HML modules required by Blender's embedded interpreter for the lifetime of the invocation
- **AND** neither the checkout nor host site-packages is added to Blender's import path, and the host Python version is not imposed on Blender
- **AND** Blender remains an explicit external prerequisite, with the unchanged version/build/reference-platform pins and no automatic executable or asset download.

#### Scenario: Keep backend working state in the caller workspace
- **Verification:** launcher argument/environment assertions, child write audit and pinned installed-backend execution outside the checkout.
- **WHEN** installed HML starts a probe, construction or render with an explicit workspace
- **THEN** it supplies the required package script/import closure for the child's lifetime without resolving it from the invocation directory or neighboring checkout
- **AND** HML-directed temporary, cache, configuration, extracted-resource and log locations are within the owning workspace's build tree
- **AND** no host site-packages injection, backend pin bypass or global temporary-file fallback occurs
- **AND** missing or invalid workspace/path inputs fail before lock allocation, probing or child launch.

### Requirement: Backend execution and cancellation are bounded

Every supervised invocation SHALL have a finite positive execution deadline. Normal completion SHALL reap the direct child, record its exit result and perform the existing output validation without subsequently probing or signaling its saved process-group identifier. Normal completion SHALL NOT claim to discover or terminate independently surviving descendants. Timeout, caller cancellation and failure cleanup SHALL finish within documented bounds and return failure; group signals SHALL be limited to the invocation's owned group while its direct child remains unreaped. After the child is reaped, its saved PID/PGID SHALL NOT authorize a group probe or signal. Missing executables and spawn errors SHALL produce controlled failures. Unconfirmed descendant termination SHALL remain explicit pending cleanup, never a confirmed-cleanup or success claim.

#### Scenario: Complete the direct child without post-exit group management
- **Verification:** zero/nonzero child integration tests and controlled group-probe/signal interception.
- **WHEN** the direct child exits and is reaped
- **THEN** the supervisor records its return code and applies the existing phase/output success rules
- **AND** no later group probe or signal is made using its saved PGID, even if a controlled probe would report a different group under that number
- **AND** no automatic orphan cleanup or descendant-termination claim is inferred from the direct child's exit.

#### Scenario: Stop a hung process and its descendant
- **Verification:** synthetic sleeping-child/descendant integration test, signal/reap ordering and elapsed-time assertions.
- **WHEN** a test child and its descendant outlive a one-second deadline and ignore graceful termination
- **THEN** any TERM/KILL escalation occurs before reaping the direct child, reports timeout and preserves an unrelated sentinel
- **AND** the direct child is reaped within the deadline plus documented cleanup allowance plus two seconds of scheduling tolerance
- **AND** no saved-PGID operations occur after reap; descendant cleanup that cannot be safely confirmed remains cleanup pending.

#### Scenario: Cancel or fail to start work
- **Verification:** synthetic cancellation, late-cancellation, missing executable and injected spawn-error tests.
- **WHEN** the caller is interrupted after spawn, or process creation fails
- **THEN** the operation exits unsuccessfully with a cancellation or spawn-error record as appropriate
- **AND** cleanup attempts signal only while the direct child remains unreaped and finish within documented bounds
- **AND** interruption observed after reap performs no saved-PGID operation
- **AND** unconfirmed descendant termination retains pending cleanup and no completed build or pack verdict is emitted.

### Requirement: Checkout-owned backend work does not overlap

At most one supervised Blender child SHALL be active per selected workspace across independent callers, including callers using different installations. Every caller SHALL explicitly select an absolute workspace; repository use SHALL explicitly select its checkout when that is the intended workspace. Waiting for the execution slot SHALL have a finite deadline and be cancellable. Abandoned ownership records SHALL NOT block later work after the actual owner has exited, and another caller SHALL NOT release or replace a live owner's slot. Slot state SHALL reside in the workspace's `build/`, outside immutable package resources.

#### Scenario: Contend for a running backend
- **Verification:** two-supervisor integration test with child lifetime intervals and bounded wait assertions.
- **WHEN** two independent callers target the same workspace while the first owns the execution slot
- **THEN** their Blender child lifetime intervals do not overlap
- **AND** a caller whose slot-wait deadline expires records contention without spawning a child
- **AND** unrelated Python-only checks can proceed

#### Scenario: Recover ownership after supervisor death
- **Verification:** controlled owner-termination test and process-liveness/ownership assertions.
- **WHEN** a supervisor exits unexpectedly while its owned child may still be alive
- **THEN** a later invocation cannot overlap that live child or kill an unrelated process based only on an old PID
- **AND** after the owned process tree has ended the execution slot becomes available without deleting a live owner's lock
- **AND** unverifiable orphan ownership is reported as requiring operator resolution rather than bypassed

#### Scenario: Share ownership across installed callers
- **Verification:** two independently installed callers, symlink-resolved workspace assertion and filesystem inspection.
- **WHEN** callers from two installations select paths resolving to the same workspace
- **THEN** they contend for the same persistent workspace lock/state and cannot overlap
- **AND** distinct workspaces use distinct ownership state without modifying either installation
- **AND** source-tree commands selecting the checkout retain its existing `build/.backend-execution.lock` and state-file locations.

#### Scenario: Ignore invocation and installation location for lock ownership
- **Verification:** independent installed callers with different invocation directories and symlink aliases of one workspace.
- **WHEN** callers explicitly target the same resolved workspace from unrelated invocation directories
- **THEN** they share its persistent lock and state under build and obey existing bounded contention and abandoned-owner rules
- **AND** distinct resolved workspaces have independent ownership state even when callers share an installation or invocation directory
- **AND** neither invocation-directory state nor package-local state acts as an alternate execution slot.

### Requirement: Invocation evidence survives failures

Each invocation SHALL retain a machine-readable outcome and captured output within its owning run. Evidence SHALL identify operation, command, source identity, package version/resource identity, implementation identity, workspace, executable, platform, timing, deadline, exit status or signal, timeout/cancellation, last observed phase and output-validation result. Unobserved phases SHALL be marked unknown. A parent killed before finalization SHALL leave recognizable unfinished evidence.

#### Scenario: Diagnose a native failure before the script starts
- **Verification:** synthetic signal-equivalent nonzero exit and receipt/log field validation; no real application is deliberately crashed.
- **WHEN** an invocation ends unsuccessfully before any script-start marker
- **THEN** its outcome contains the raw exit result and signal when directly available, captured stdout/stderr and an unknown script phase
- **AND** it does not infer a GPU, memory, source-data or shutdown cause from missing evidence
- **AND** no private environment dump or unrelated application crash reports are collected

#### Scenario: Distinguish script execution and process shutdown
- **Verification:** controlled phase-emitting child tests and backend completion assertions.
- **WHEN** a child starts the script, advances through build/render/output phases and reports script completion
- **THEN** the evidence preserves the last observed phase and treats script completion separately from process exit
- **AND** a nonzero exit after script completion is still failure
- **AND** an interrupted parent leaves an initial unfinished record distinguishable from a final successful outcome

#### Scenario: Identify a wheel-installed invocation
- **Verification:** installed build receipt/metadata comparison against distribution metadata and manifest hashes.
- **WHEN** a supervised invocation is started without a source checkout
- **THEN** its prepared input, receipt and build/render metadata identify the same installed release and source/implementation inventory
- **AND** machine-specific command/workspace paths remain diagnostic evidence rather than canonical source identity
- **AND** collecting identity requires neither Git nor a development `uv.lock` or `pyproject.toml`.

#### Scenario: Identify explicit workspace ownership after an external invocation
- **Verification:** successful and failed installed invocation receipt/log audit.
- **WHEN** a pipeline starts an invocation outside the checkout with an explicit workspace
- **THEN** initial and finalized evidence identify the resolved workspace, owning run and HML-directed temporary/log locations
- **AND** failure or cancellation evidence remains in that run and preserves existing cleanup status
- **AND** absolute execution paths remain diagnostics and do not enter canonical resource or prepared-content hashes.

### Requirement: Successful execution requires complete fresh evidence

Process exit zero alone SHALL NOT establish success. A successful script invocation SHALL have current-invocation completion evidence and all required operation outputs validated against its input identity. Nonzero exits, timeouts, cancellation, malformed/missing outputs and stale or partial artifacts SHALL fail closed. Failed outputs SHALL NOT be automatically reused or published as a successful review pack.

#### Scenario: Reject apparently usable outputs from a failed execution
- **Verification:** synthetic child matrix and review-pack integration tests.
- **WHEN** a child writes plausible outputs but exits nonzero, or exits zero with missing/malformed outputs or without completion evidence
- **THEN** the operation reports failure and records the failed condition
- **AND** downstream clean-pass comparison or pack assembly does not run using those outputs
- **AND** files that existed before the invocation cannot satisfy its completion contract

#### Scenario: Accept a complete operation without weakening numerical checks
- **Verification:** real build/render integration test and existing input/manifest validation tests.
- **WHEN** a zero-exit invocation supplies completion evidence and all expected current outputs with the matching prepared-input hash
- **THEN** it is eligible for the existing numerical and render checks
- **AND** process success does not itself assert anatomical, contact, timing, determinism or human visual acceptance

### Requirement: Crash recovery is explicit and preserves run ownership

Supervised operations SHALL NOT retry failed backend invocations automatically, suppress crash reporting, bypass version checks or switch renderers to obtain success. A new manually initiated attempt SHALL use a fresh run identity. Evidence and cleanup SHALL follow `build-artifact-lifecycle`, including ownership, dependency checks and recorded retention reasons.

#### Scenario: Fail one clean render pass
- **Verification:** injected render failure with spawn-count and filesystem assertions.
- **WHEN** the first clean render fails
- **THEN** no automatic retry or second clean pass is launched, no successful pack is assembled and the failure record points to its evidence
- **AND** a later attempt cannot overwrite that independently managed run
- **AND** protected history, another caller's output and external paths remain unchanged

#### Scenario: Complete a failed-attempt hand-off
- **Verification:** cleanup inventory and durable hand-off audit.
- **WHEN** a failed attempt is diagnosed or superseded
- **THEN** obsolete owned runs are removed only after dependency checks, with removed paths/bytes and retained paths/reasons recorded
- **AND** unresolved diagnostic evidence is retained with a named issue and reconsideration event
- **AND** interrupted or unsafe cleanup remains pending

### Requirement: Execution hardening preserves reproducible animation outputs

Execution-policy changes SHALL preserve existing source formats, version pins, coordinate/rotation conventions, fixed camera/floor/light settings and frame timing. Focused clean comparisons SHALL separate execution reliability evidence from image/numerical acceptance and label diagnostic subsets honestly.

#### Scenario: Compare the focused regression pack
- **Verification:** independent numerical check, decoded-pixel comparison and explicit human visual review.
- **WHEN** the reviewer builds the design's neutral/rest and four-beat arm-raise subset through the supervised path twice on the reference platform
- **THEN** evaluated geometry/transforms meet existing repeat-build tolerances and corresponding decoded render pixels agree exactly
- **AND** beat/count frames, at least two in-betweens per full beat, labeled front/side sheets, GIF timing and onion-skin overlays meet the existing rules
- **AND** the human receives the specified comparison layout and approves or rejects readability and stable framing
- **AND** this focused result is not presented as a renewed complete anatomical or mobility acceptance verdict
