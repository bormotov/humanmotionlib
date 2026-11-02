# Spec Delta

## ADDED Requirements

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

## MODIFIED Requirements

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
