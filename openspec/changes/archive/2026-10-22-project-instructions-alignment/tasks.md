## 1. Project instructions

- [x] Update `AGENTS.md` with beat sampling, approved licenses, motion provenance, open IK representation, and the ordered lifecycle with permitted parallel work. Verify each decision appears consistently in the glossary, data rules, workflow, quality gates, and licensing section.
- [x] Update `.codex/config.toml` comments and concurrency setting so they describe runtime concurrency accurately and do not claim runtime-enforced sequential processing. Verify TOML parses.
- [x] Update `.codex/agents/reviewer.toml` to bound cleanup to its review-output scope and require developer cleanup outside it. Verify its write-scope and cleanup instructions agree.
- [x] Add the commercial-use source-clearance rule to project and role instructions, and create `docs/used-materials.md` as the register for all external materials actually used. Verify the register captures license evidence, conditions, check date, and related outputs, including CC0/no-attribution items.
- [x] Require the reviewer to audit source use against the register and provenance. Verify ambiguous or incompatible source permissions fail review.

## 2. Validation

- [x] Run `openspec validate project-instructions-alignment` and resolve any validation errors.
- [x] Re-read the changed instructions and confirm the delta requirements and decisions are represented without closing the IK question.

## 3. Current-policy reconciliation and closure

The seven completed items above record the original implementation. Their former cleanup scope and globally open IK wording are superseded by the current reconciled specification and design; they are not authorization to clean legacy packs or reopen an accepted contact contract.

- [x] 3.1 Reconcile the existing proposal, design and five `project-governance` requirements with current `AGENTS.md`, role instructions and accepted capability specs, including owned flat-run cleanup, protected history and scoped contact representation. Verify scenario coverage, the new capability Purpose and `openspec validate project-instructions-alignment --strict` without implementation edits.
- [x] 3.2 Independently verify every reconciled requirement/scenario against current local instructions, TOML and the relevant source-register entry, and deliver `review.md` with commands, findings/verdict, scope exclusions and dependency-aware cleanup receipt for a fresh owned flat review run. Verify no unreported blockers or pending cleanup and no implementation or protected-history modifications.
- [x] 3.3 Synchronize `project-governance` into the missing main spec after the independent review passes. Verify the delta Purpose and all five complete requirement/scenario blocks match the main spec, no delta-style headers remain, unrelated main specs are unchanged, and both main-spec and change strict validation pass.

## Closure verification — 2026-10-22

Independent review: PASS (`review.md`), covering all five governance requirements and eleven scenarios. Its owned temporary review run was removed completely; no cleanup is pending. The verified main `openspec/specs/project-governance/spec.md` preserves the delta Purpose and all five complete requirement/scenario blocks, contains canonical main-spec headings, and leaves the three other main specifications unchanged. `openspec validate --specs --strict` passed all four main specs; `openspec validate project-instructions-alignment --strict` passed. No implementation, historical evidence, archival or commit changes were made by this closure work.
