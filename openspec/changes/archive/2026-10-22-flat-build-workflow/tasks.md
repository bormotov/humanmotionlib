# Tasks

## 1. Adopt one workflow rule

- [x] 1.1 After explicit Human gate 1 approval, update `AGENTS.md` repository layout, reviewer output location, tooling and completion process with the five-component flat naming and cleanup rules; verify the new example round-trips into five valid components, no current nested-output instruction remains, and any managed block is unchanged.
- [x] 1.2 Align `.codex/agents/architect.toml`, `dev.toml` and `reviewer.toml`, including reviewer write/cleanup ownership and developer cleanup hand-off; verify all three parse as TOML and that each role's instructions cover its responsibility without granting the reviewer access to unrelated run roots.

## 2. Document executable use and cleanup

- [x] 2.1 Revise all current `tools/README.md` output examples (basic build, verifier, previews, stature builds and HTML derivatives) to use consistent flat run roots with existing commands/flags; verify every new-run path satisfies the convention, same-run preparation/build paths agree, distinct input/output roots are disjoint, and any literal historical input is explicitly labeled legacy.
- [x] 2.2 Document the post-check cleanup checklist and compact Markdown hand-off example in `tools/README.md`; verify coverage of success, failure, interruption/pending cleanup, dependency closure, protected history, active-work exclusion, whole-run removal, byte counts and specific retention reasons for exceptional JSON/log files.
- [x] 2.3 Run the developer's small allocation/cleanup exercise described in `design.md` using owned flat scratch roots, remove its disposable outputs afterward, and append concise results/cleanup evidence to this task file; verify valid/invalid names, allowed content directories, occupied/overlapping run rejection, retained relative-link dependency, removal of obsolete whole roots, unchanged protected/external/active files, and accurate removed bytes without touching accepted legacy packs.

## 3. Independent integration verification

- [x] 3.1 Have a separate reviewer audit the complete instruction/README diff and independently repeat the bounded workflow exercise, including a dry-run developer-cleanup hand-off; verify every `build-artifact-lifecycle` scenario and the two modified path requirements in `review.md`, with actual evidence and an explicit verdict, without rebuilding or altering skeleton media.
- [x] 3.2 Complete reviewer cleanup and any exact-path developer hand-off, retain only needed evidence in an existing durable report, and verify the review receipt records removed paths/bytes, retained roots/reasons, dependency checks and no pending cleanup; confirm historical accepted/protected artifacts are unchanged and no new nested cleanup-history tree remains.
- [x] 3.3 Run `openspec validate flat-build-workflow --strict` and check the final changed-file scope; verify only the approved instructions/docs and this change's planning/review artifacts are changed, with no executable code, schemas, YAML motion data, archived evidence, generated media or new external materials.

## Workflow follow-up

- Sync the new lifecycle capability and the two narrow path deltas through the normal OpenSpec sync/archive workflow after the independent review passes.
- This instruction-only change has no new visual pack or Human gate 2 visual approval requirement; it does not reopen the accepted skeleton's visual gate.

## Planning approval — 2026-10-22

After the proposed flat five-component naming, internal-content distinction, mandatory cleanup and legacy-history exception were presented, the human instructed the agent to continue. This is recorded as approval to implement the described instruction/documentation-only plan.

## Developer exercise results (task 2.3)

- The bounded filesystem exercise accepted `build/flat-build-workflow_r1_dev_try-1_checks/` as a five-component direct child; rejected an underscore inside a component, a nested run identity, and reuse of the occupied root. It accepted `frames/`, `assets/`, and `clean-a/` as content directories and confirmed build/check/pack roots were disjoint.
- A relative reference from an accepted fixture resolved to a protected predecessor fixture and remained valid after cleanup. A cleanup candidate containing an external symlink was removed without following it; the outside sentinel hash was unchanged. An unrelated active-run hash and the protected predecessor hash were unchanged.
- Simulated interrupted cleanup retained a failure diagnostic as pending; after review, the obsolete roots `build/flat-build-workflow_r1_dev_fixture-obsolete_pack/` and `build/flat-build-workflow_r1_dev_fixture-failed_checks/` were removed. Their regular files totaled 36 bytes (`7 + 11 + 18`); the pending item then cleared. All disposable run roots were removed after the exercise. No accepted legacy pack was touched.
