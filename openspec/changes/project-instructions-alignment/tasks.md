## 1. Project instructions

- [x] Update `AGENTS.md` with beat sampling, approved licenses, motion provenance, open IK representation, and the ordered lifecycle with permitted parallel work. Verify each decision appears consistently in the glossary, data rules, workflow, quality gates, and licensing section.
- [x] Update `.codex/config.toml` comments and concurrency setting so they describe runtime concurrency accurately and do not claim runtime-enforced sequential processing. Verify TOML parses.
- [x] Update `.codex/agents/reviewer.toml` to bound cleanup to its review-output scope and require developer cleanup outside it. Verify its write-scope and cleanup instructions agree.
- [x] Add the commercial-use source-clearance rule to project and role instructions, and create `docs/used-materials.md` as the register for all external materials actually used. Verify the register captures license evidence, conditions, check date, and related outputs, including CC0/no-attribution items.
- [x] Require the reviewer to audit source use against the register and provenance. Verify ambiguous or incompatible source permissions fail review.

## 2. Validation

- [x] Run `openspec validate project-instructions-alignment` and resolve any validation errors.
- [x] Re-read the changed instructions and confirm the delta requirements and decisions are represented without closing the IK question.
