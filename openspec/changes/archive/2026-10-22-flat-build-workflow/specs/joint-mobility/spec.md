# Spec Delta

## MODIFIED Requirements

### Requirement: Verification report and human visual gate

Independent review SHALL report per-joint action coverage, limit and coupling checks, contact residuals, rigid-structure invariants, root drift, mirror and loop error, timing, and render repeatability. The report SHALL distinguish numerical acceptance from human judgments of anatomical plausibility and movement readability. No visual-affecting change SHALL be archived without human approval of its review pack.

#### Scenario: Review a completed implementation
- **WHEN** independent verification reconstructs the skeleton and diagnostics from repository sources
- **THEN** `review.md` references each violated requirement and scenario, and links the pack in a direct child of `build/` named according to `build-artifact-lifecycle`
- **AND** every supported action has valid, boundary, invalid, and visual coverage; every coupled relation has valid and invalid coverage
- **AND** incomplete reference evidence, missing checks, or unresolved numerical failures prevent an acceptance verdict
- **AND** the human can approve or reject visual naturalness after inspecting the numeric results and images

#### Scenario: Verify a presentation-only derivative
- **Verification:** independent source/media hash audit and browser review.
- **WHEN** only diagnostic HTML navigation or layout changes
- **THEN** generated HTML is independently regenerated and checked in a fresh presentation output directory
- **AND** provenance identifies the original numeric/render snapshot and the new presentation-generator snapshot separately
- **AND** original media bytes, timing records, numeric evidence and their recorded hashes remain unchanged
- **AND** the original numeric verdict is explicitly scoped to its original snapshot and renewed presentation verification covers the revised HTML
- **AND** the human visual gate remains pending until the human explicitly accepts the presented pack

#### Scenario: Keep historical reports valid after adopting flat run names
- **Verification:** historical-reference and workflow audit.
- **WHEN** a future independent review uses the flat convention
- **THEN** it links its actual fresh run root instead of the former generic `build/review/anatomical-human-skeleton/` destination
- **AND** existing accepted reports, packs and expressly protected predecessors retain their paths and preservation obligations
