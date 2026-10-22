# backend-execution Specification

## Purpose

Make repository-owned Blender execution bounded and diagnosable, so native process failures cannot silently become successful build or review evidence.

## Requirements

### Requirement: Routine backend work has one controlled execution path

Documented routine builds, render passes, backend probes and Blender integration tests SHALL use a shared supervised execution policy. It SHALL preserve executable resource discovery, the pinned version/build check, factory-startup isolation for scripts and explicit nonzero exit on Python exceptions. It SHALL NOT launch a GUI application as an automatic recovery action.

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

### Requirement: Backend execution and cancellation are bounded

Every supervised invocation SHALL have a finite positive execution deadline. Timeout, caller cancellation and failure cleanup SHALL terminate only the invocation's owned child process tree, finish within documented bounds and return failure. Missing executables and spawn errors SHALL also produce controlled failures. Unconfirmed termination SHALL remain explicit pending cleanup, never success.

#### Scenario: Stop a hung process and its descendant
- **Verification:** synthetic sleeping-child/descendant integration test with elapsed-time and process-liveness assertions.
- **WHEN** a test child and its descendant outlive a one-second deadline and ignore graceful termination
- **THEN** the supervisor escalates after the documented grace period, reports timeout and leaves neither owned process running
- **AND** completion occurs within the deadline plus cleanup allowance plus two seconds of test scheduling tolerance
- **AND** an unrelated sentinel process remains alive

#### Scenario: Cancel or fail to start work
- **Verification:** synthetic cancellation, missing executable and injected spawn-error tests.
- **WHEN** the caller is interrupted after spawn, or process creation fails
- **THEN** the operation exits unsuccessfully with a cancellation or spawn-error record as appropriate
- **AND** any child tree that was created is cleaned before releasing its execution slot
- **AND** no completed build or pack verdict is emitted

### Requirement: Checkout-owned backend work does not overlap

At most one supervised Blender child SHALL be active per checkout across independent callers. Waiting for the execution slot SHALL have a finite deadline and be cancellable. Abandoned ownership records SHALL NOT block later work after the actual owner has exited, and another caller SHALL NOT release or replace a live owner's slot.

#### Scenario: Contend for a running backend
- **Verification:** two-supervisor integration test with child lifetime intervals and bounded wait assertions.
- **WHEN** two independent callers target the same checkout while the first owns the execution slot
- **THEN** their Blender child lifetime intervals do not overlap
- **AND** a caller whose slot-wait deadline expires records contention without spawning a child
- **AND** unrelated Python-only checks can proceed

#### Scenario: Recover ownership after supervisor death
- **Verification:** controlled owner-termination test and process-liveness/ownership assertions.
- **WHEN** a supervisor exits unexpectedly while its owned child may still be alive
- **THEN** a later invocation cannot overlap that live child or kill an unrelated process based only on an old PID
- **AND** after the owned process tree has ended the execution slot becomes available without deleting a live owner's lock
- **AND** unverifiable orphan ownership is reported as requiring operator resolution rather than bypassed

### Requirement: Invocation evidence survives failures

Each invocation SHALL retain a machine-readable outcome and captured output within its owning run. Evidence SHALL identify operation, command, source identity, executable, platform, timing, deadline, exit status or signal, timeout/cancellation, last observed phase and output-validation result. Unobserved phases SHALL be marked unknown. A parent killed before finalization SHALL leave recognizable unfinished evidence.

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
