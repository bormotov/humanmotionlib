# project-governance Specification

## Purpose

Keep project and agent instructions consistent about timing, source permissions, scoped contact decisions, workflow gates and safe reviewer cleanup authority.

## Requirements

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

### Requirement: Reviewer cleanup is bounded
Role-scoped automatic reviewer cleanup SHALL stay inside its assigned flat run areas. An explicitly authorized Make cleanup SHALL use the fixed project areas, removing all inactive contents including local accepted history regardless of producer. Active work and outside-area files SHALL remain safe. The durable review report SHALL record removed paths/bytes and pending failures without a separate ownership inventory or legacy dependency scan.

#### Scenario: Start a fresh owned review run
- **WHEN** a reviewer starts verification for a change with earlier build or review outputs
- **THEN** it allocates a fresh direct child of `build/` named `<change>_<revision>_reviewer_<attempt>_<kind>/` with exactly five underscore-separated lowercase-kebab components
- **AND** ordinary run allocation does not remove, replace or relocate earlier results; explicit Make cleanup can remove them when they fall inside its selected areas
- **Verification:** audit of reviewer instructions, accepted lifecycle requirements and the recorded run path.

#### Scenario: Complete checks and clean owned outputs
- **WHEN** review checks finish successfully, fail or are interrupted
- **THEN** the reviewer applies the assigned cleanup area and records removals; an explicit Make target removes all selected inactive contents without a legacy dependency/reference scan
- **AND** it does not traverse symlinks, remove active work or broaden automatic role-scoped cleanup; producer names and JSON/log extensions do not create exceptions within an explicitly selected Make area
- **AND** `review.md` records selected areas, removed paths/bytes and pending cleanup; unresolved cleanup prevents a completion claim
- **Verification:** role-instruction audit and review of the independent check run's cleanup receipt against `build-artifact-lifecycle`.

#### Scenario: Verification needs cleanup outside reviewer ownership
- **WHEN** required automatic cleanup concerns build output outside the reviewer's assigned area
- **THEN** the reviewer reports the required wider scope to the orchestrator; explicitly authorized Make cleanup follows its declared areas
- **AND** cleanup remains pending and obstructed verification waits until the responsible action completes
- **Verification:** review of reviewer/developer hand-off instructions and any cleanup hand-off recorded for this review.

### Requirement: Development preparation and package checks have clear purposes

Instructions SHALL allow reuse of prepared development tools and require a clean independent installation where checks must prove that the built package works on its own. Make SHALL manage both routes. Each setup SHALL have a stated purpose, owner and cleanup rule, and use its own installed package/dependencies without borrowing files from another setup or the source checkout.

#### Scenario: Prepare development tools and check a built package
- **WHEN** instructions describe development preparation, selected previews and package checking
- **THEN** development reuses tools with a freshly built library, while package checks use a fresh uv-created setup with the exact package being checked
- **AND** logs contain the standard pre-test tool/package/cache records required by project instructions
- **AND** contributors do not manually assemble diagnostic commands or paths for default routes
- **AND** development-tool reuse never turns local success into independent review or complete library acceptance
- **Verification:** instruction/configuration audit, actual installed-file checks and controls that reject using files from another setup.

### Requirement: Tooling audits resolve workflow contradictions

A tooling audit SHALL consider requirements, settings, current sources, check independence, outputs and recorded results together. Each contradiction SHALL be fixed within scope or documented with a concrete reason, affected goal and next action. Guides SHALL distinguish readiness for development, preview results, checked packages and change acceptance.

#### Scenario: Reconcile current project tooling
- **WHEN** the audit compares Make, uv/package building, supported HML commands, guides, CI and agent instructions
- **THEN** each contradiction maps to a correction and verified result or a justified remaining gap
- **AND** default repository routes need no manual cache, tool or run-directory setup
- **AND** required movement inputs and human decisions remain explicit rather than being guessed or bypassed
- **Verification:** requirements/tool/instruction comparison, literal clean-checkout walkthrough and independently checked gap records.

### Requirement: Tooling audits preserve paused visual work

The tooling audit SHALL keep visual work paused and preserve its recorded decisions and source identities. Reports SHALL state which sources/packages were checked and assess whether images could change. Tool preparation, local checks or a rebuilt package SHALL not count as acceptance of different character results.

#### Scenario: Complete the tools audit while character work is paused
- **WHEN** this tooling change is implemented and reviewed
- **THEN** no real character matrix, dense audit or final visual pack runs under this authorization; R6 remains a historical visual decision and is not relabeled as current-package evidence
- **AND** command coordination is checked with controlled examples and host/package checks; reports explain why no visual gate applies
- **AND** any required change to visible results returns for separately approved scope and preview planning
- **AND** recorded process-safety and determinism findings keep their status unless separately authorized and checked
- **Verification:** changed-file/command timeline audit, historical decision/source-record inspection and scoped review verdict.

### Requirement: Cleanup guidance declares disposable areas

Instructions SHALL define fixed cleanup areas and explain that every selected object is removed, including unknown files and local history. Sources SHALL remain in version control and durable results in artifact storage outside those areas. Cleanup SHALL need no separate owner inventory, file manifest or legacy-reference scan. Active-work and path-containment checks SHALL still apply.

#### Scenario: Review the cleanup policy alongside build guidance
- **WHEN** the audit reconciles Make help, workflow guides, AGENTS and role instructions
- **THEN** each document states the same three-level cleanup areas, including removal of local R6-like history and matrix logs at clean/distclean
- **AND** no hidden protection based on ownership records, unknown contents, accepted status or local references remains
- **AND** durable source/review decisions and external artifact storage are not inside the cleanup scope, and failed cleanup remains pending
- **Verification:** instruction/rule-table audit, unknown/history-removal fixtures, outside-area hashes and independent failure-report review.
