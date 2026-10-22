# Proposal: Align project instructions with agreed workflow

## Why

The original change clarified timing, licensing, provenance and subagent scheduling. Its unmerged planning artifacts now contain an obsolete reviewer cleanup scope and imply that all IK representation remains undefined, although accepted capability specifications already govern flat build runs and anatomical contact intent.

## What changes

- Define one beat as the timing unit, static sampling at each beat, and animation sampling intervals from the beat duration.
- Set Apache-2.0 for project code and CC-BY-4.0 for library data/assets, and require provenance for motions as well as poses and segments.
- Require explicit commercial-use and derivative clearance for all external source material, and maintain a register of every source actually used, including CC0 and no-attribution sources.
- Require each concrete IK/contact feature to define its representation before implementation; preserve contracts already established for scoped features.
- Clarify that independent implementation tasks may run in parallel inside an approved OpenSpec change, while architect approval, implementation, review, and archive remain ordered.
- Bound reviewer cleanup to its own unprotected flat run outputs under the existing `build-artifact-lifecycle` rules; developer-owned cleanup is handed to the developer, and accepted history and required dependencies remain protected.
- Reconcile the existing planning artifacts with current instructions, independently verify them in `review.md`, and sync the new `project-governance` main specification.

## Capabilities

### New Capabilities

- `project-governance`: instruction-level timing, licensing/provenance, scoped contact decisions, ordered lifecycle with permitted parallel tasks, and reviewer cleanup authority.

### Modified Capabilities

None. The existing `build-artifact-lifecycle`, `anatomical-skeleton` and `joint-mobility` contracts are consumed unchanged; this reconciliation does not replace their detailed requirements.

## Impact

The original implementation updated `AGENTS.md`, Codex role/configuration instructions and `docs/used-materials.md`. The current closure work updates only this change's planning artifacts, adds its independent review, and creates `openspec/specs/project-governance/spec.md` by verified sync. No runtime code, source-data schema, pose, segment, motion, camera, render or historical review-pack change is authorized by this reconciliation.
