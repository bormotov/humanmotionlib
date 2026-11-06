## MODIFIED Requirements

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
