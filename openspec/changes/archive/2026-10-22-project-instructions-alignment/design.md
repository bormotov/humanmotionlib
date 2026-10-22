# Design

## Current reconciliation scope

The human explicitly requested reconciliation to current policy, independent review in `review.md`, and synchronization of `project-governance`. This authorizes the planning corrections below and the subsequent review/sync; it does not authorize archiving or changing implementation behavior. The flat-run and ownership policy was already approved and implemented by `flat-build-workflow`. Current `AGENTS.md`, the three role instructions, `tools/README.md` and `openspec/specs/build-artifact-lifecycle/spec.md` are the cleanup baseline.

## Decisions

- `T_beat` means the duration of one beat, derived from BPM as `60 / BPM` seconds. For each full beat, animation sampling uses `max(3, ceil(T_beat / 0.2 seconds))` intervals. Static samples are placed at every beat boundary. Fractional-beat segment boundary allocation remains for the timing implementation change to define.
- Apache-2.0 covers project code. CC-BY-4.0 covers library-authored data and distributable authored assets, including poses, segments, motions, baked clips, and renders. Third-party character and scene assets retain their own licenses and must be checked separately.
- Every motion records provenance. A composed motion records its source segment identifiers or external references; its distribution license remains CC-BY-4.0 when all included material is compatible with that license.
- External references and inputs are gated before use: their specific license must explicitly permit commercial use of the resulting work and be compatible with CC-BY-4.0 distribution. When that cannot be established, the source is not used. Every external material actually used is recorded in `docs/used-materials.md`, even where attribution is not required; provenance links to that register.
- IK target coordinate space, normalization and units are decided by the change that introduces each concrete contact feature, before implementation. The general glossary leaves new representations to that scoped decision; it does not reopen already accepted contracts. `anatomical-skeleton` fixes canonical axes/units and `joint-mobility` already specifies foot-local anchors, world-space targets, stature scaling and beat intervals for anatomical diagnostics. This reconciliation preserves those contracts rather than redefining IK globally.
- Subagent concurrency is a scheduling capability, not workflow order. Independent tasks may run concurrently; the OpenSpec approval, implementation, review, and archive gates remain in sequence.
- Reviewer cleanup is limited to its own unprotected flat run outputs, with an inventory, dependency checks and a durable cleanup receipt as required by `build-artifact-lifecycle`. A change ID in a legacy path does not establish ownership or permission to replace history. Accepted outputs, explicitly protected history and their required dependency closure remain unchanged. If developer-owned or otherwise out-of-scope outputs need removal, the reviewer reports exact paths/reasons to the developer and keeps cleanup pending until resolved. The previous blanket `build/review/<change-id>/` permission is superseded, not retained as an alternative.

## Codex configuration

Use the supported `max_concurrent_threads_per_session` key for the subagent concurrency cap. Keep comments accurate about host/runtime feature enablement and the V1-only `max_depth` behavior; do not imply that these settings enforce the OpenSpec lifecycle.

## Verification and acceptance

The seven checked original tasks are historical implementation records, not evidence that the new closure work has passed. The appended tasks separately track reconciliation, independent review/cleanup, and sync. The reviewer audits current local Markdown/TOML instructions against every governance scenario, parses `.codex/config.toml` and role TOML, checks timing-policy arithmetic at BPM 60/120/180, and cross-checks the existing configuration-reference entry in `docs/used-materials.md`. No new external reference is needed for this local policy reconciliation; a newly consulted external source would still require clearance and registration before use.

Use one fresh owned review run, `build/project-instructions-alignment_r1_reviewer_try-1_review/`; if occupied, allocate a new attempt component. Any check fixtures/logs are internal content of that run, not independent nested runs. Put the requirement/scenario matrix, commands/results, licensing findings, scope limitations, verdict and cleanup receipt in `openspec/changes/project-instructions-alignment/review.md`. Retain generated evidence only when the report requires it; otherwise remove the obsolete owned run and record removed bytes and post-cleanup dependency checks in that report. Other agents' outputs and protected historical packs remain unchanged.

This instructions-only change needs a text review pack/report rather than contact sheets, GIFs or onion-skin images. It changes no pose, segment, motion, scene or rendering, so no new visual gate or animation rebuild applies. Existing timing, fixed camera/floor and source licensing rules remain in force for the changes that implement those features.

After independent review passes, sync the five requirement blocks and this delta's Purpose into the missing `project-governance` main spec using the sync workflow; preserve all scenarios, remove delta section markers, and validate both the main spec and change. Report findings rather than silently changing runtime or role instructions if the review discovers a material mismatch. Do not archive as part of this request.
