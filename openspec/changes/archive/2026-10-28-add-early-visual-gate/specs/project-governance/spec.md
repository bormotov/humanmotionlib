# Spec Delta

## MODIFIED Requirements

### Requirement: OpenSpec lifecycle stays ordered while independent tasks may run in parallel

The project workflow SHALL require approved OpenSpec scope before implementation and independent review before archive. Visual-affecting changes SHALL obtain early human visual approval before expensive verification and final human visual approval after independent review. Independent implementation tasks within the approved scope SHALL remain eligible for parallel delegation with non-conflicting ownership.

#### Scenario: Independent implementation tasks
- **WHEN** tasks in an approved change are independent and have non-conflicting ownership
- **THEN** they may be delegated concurrently, while the change still follows the architect, implementation, early visual gate where applicable, independent review, and archive lifecycle
- **Verification:** review of project and subagent instructions.

#### Scenario: Implementation and acceptance use separate responsibilities
- **WHEN** an approved change is implemented and reviewed
- **THEN** the main agent orchestrates and manages OpenSpec artifacts while implementation and independent verification are delegated to their respective roles
- **AND** review precedes archive and a change affecting poses, motions, visible characters, scene or rendering requires the human's final visual approval before archive
- **AND** early preview approval does not satisfy independent review, numerical acceptance, final Human Gate 2 or cleanup
- **Verification:** audit of project and role instructions and their change-level gates.

## ADDED Requirements

### Requirement: Early visual approval precedes expensive verification

A change affecting poses, motions, visible characters, scene or rendering SHALL obtain an explicit human decision on a bounded preview before launching full regression suites, full diagnostic/tempo/stature matrices, dense audits, repeated render comparisons or full acceptance packs. Necessary preview preflight and focused checks SHALL precede that decision.

#### Scenario: A visual implementation is ready for its first preview
- **WHEN** an approved visual-affecting change first produces reviewable output
- **THEN** the developer creates only the planned bounded preview after source clearance, applicable schema/identity/environment checks and focused checks necessary to render that preview
- **AND** the orchestrator presents its artifacts and limitations to the human and keeps expensive verification pending until explicit early visual acceptance
- **AND** waiting, a request to continue, a developer opinion, passing metrics or an already-running process is not recorded as visual acceptance
- **Verification:** workflow dry run with a command timeline and a human decision record.

#### Scenario: A change has no visual effect
- **WHEN** the approved scope changes only governance, nonvisual documentation or another behavior with no affected visible result
- **THEN** the change records why the early visual gate is not applicable and follows its applicable technical and review gates without generating a gratuitous preview
- **Verification:** scope and instruction audit.

### Requirement: The early preview exposes the proposed visual direction

The approved change SHALL define a small representative preview before generation, identifying affected visible variants, poses or segments, views, stature, tempo and relevant detail views. The preview SHALL use canonical sources and the fixed scene, expose its identity and limitations, and contain enough static and moving evidence for the human to judge the proposed visual direction.

#### Scenario: Inspect a character or motion preview
- **WHEN** a preview is presented for an early decision
- **THEN** it shows all affected visible variants side by side under the same scene, representative count poses and relevant joint, junction or contact details
- **AND** a motion-affecting change includes at least one complete representative segment as a timed animation and a key-transition onion-skin overlay, sampled under the existing beat rule
- **AND** the pack identifies selected fixture/pose/segment, beat, character, view, stature and tempo, its canonical source/package identity and unexecuted verification scopes
- **AND** count and animation images come from the same keyed animation, circular direction uses the declared via poses, and neither camera nor floor is moved to hide a defect
- **Verification:** preview inventory and identity audit plus explicit human visual inspection.

### Requirement: Early visual decisions remain explicit and scoped

The orchestrator SHALL record early acceptance or rejection with the human message, preview identity and scope in the existing change hand-off. Rejection SHALL return the affected work for correction and a fresh preview. Visual changes after acceptance SHALL require renewed early acceptance before further expensive verification; technical-only changes SHALL preserve a documented applicability assessment and identity rules.

#### Scenario: A preview is rejected or has no decision
- **WHEN** the human rejects a preview, requests visual changes, or has not supplied an explicit decision
- **THEN** expensive verification remains blocked for that proposed visual direction
- **AND** the developer corrects approved implementation defects or returns requirement changes to the architect and human before producing a fresh preview
- **AND** rejected preview evidence is retained or cleaned according to dependency and diagnostic needs, with a recorded reason and fresh run identity for the retry
- **Verification:** accepted/rejected/missing-decision workflow dry runs and hand-off audit.

#### Scenario: Sources change after early acceptance
- **WHEN** the accepted preview's sources or package inputs change
- **THEN** the hand-off records whether the change affects the judged appearance, pose, motion, scene or rendering
- **AND** an affected visual direction is shown in a fresh preview and requires renewed human early acceptance before further expensive checks
- **AND** a technical-only change does not claim that historical evidence exercised a new identity, and all checks required by the existing identity contract are renewed
- **Verification:** source-change workflow examples and identity/evidence audit.

#### Scenario: Adopt the ordering during unfinished work
- **WHEN** this process is adopted while a visual change is already in progress
- **THEN** completed evidence retains its original identity and scope, and no past early decision is invented
- **AND** any remaining expensive verification for an unaccepted visual direction waits for the early decision; already completed expensive work is not rerun solely to demonstrate the new order
- **AND** final independent review, cleanup and the final human visual decision remain required
- **Verification:** migration checklist using an existing change's recorded status without rerendering it.
