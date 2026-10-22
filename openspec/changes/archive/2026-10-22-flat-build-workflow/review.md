# Independent review — flat-build-workflow

**Verdict: PASS** (instruction/documentation-only scope), 2026-10-22.

No blocker, major or minor findings. This review does not approve skeleton anatomy, animation readability or any historical visual pack. No new visual decision is required by this change.

## Scope and independent evidence

Reviewed the approved proposal, design, tasks and all three delta specifications, followed by the frozen complete diff of `AGENTS.md`, `.codex/agents/{architect,dev,reviewer}.toml` and `tools/README.md`. The literal `/AGENTS.md` does not exist on this host; repository `AGENTS.md` was read. No implementation fixes, task edits, specification edits, commits or archive actions were performed.

- `python3` standard-library audit: all **3 TOML files parse**; **18 unique future README run roots** split into exactly five components matching `[a-z0-9]+(?:-[a-z0-9]+)*`; **22 output examples** use those roots. The sole README `build/review/` path is the explicitly labeled protected legacy R3 input.
- Compared old/current runnable examples with only `build/...` tokens normalized: all **18 existing commands** remain, with existing flags; the added commands spell out the already documented stature workflow. Preparation and construction use the same build root; independent verifier/pack/HTML outputs are disjoint siblings. Confirmed flags against the existing entry-point argument declarations without invoking Blender.
- Complete instruction diff: all former current nested reviewer output/write/cleanup destinations are replaced; reviewer access is bounded to its report and one exact owned run. Developer cleanup hand-off, accepted/protected history, active ownership, resolved-symlink overlap, retained dependency closure, diagnostic revisit triggers and pending cleanup are covered. No managed block was changed.
- `openspec validate flat-build-workflow --strict`: **PASS**. `git diff --check`: **PASS**.
- Independent bounded filesystem exercise: **22 assertions passed**, reproduced from the documented procedure rather than developer fixtures/logs. It allocated only `build/flat-build-workflow_r1_reviewer_try-1_checks/`. Its fixture containers were disposable content inside that owned run, not additional independently managed nested runs or writes into real developer output.

## Requirement and scenario checklist

`A` = automatable/document audit or controlled workflow check; `N` = numeric metric. No new human visual judgement gate applies. Existing non-path scenarios below are recorded explicitly as unchanged scope, not claimed as newly rerendered acceptance.

| Requirement or scenario | Class | Result and evidence |
| --- | --- | --- |
| Lifecycle: Run identity is encoded in a flat directory name | A | PASS: AGENTS, three role instructions and README agree on five ordered components and direct-child allocation. |
| Allocate an identifiable review attempt | A | PASS: `anatomical-human-skeleton_r3_reviewer_fix-try_pack` round-trips; fresh sibling retry accepted; actual reviewer root allocated fresh. |
| Reject ambiguous or nested run identity before writing | A | PASS: underscore-in-component, omitted component, uppercase, occupied root and nested identity rejected before generating; equal/ancestor/descendant and symlink-resolved overlap rejected. |
| Lifecycle: Artifact content is distinct from independently managed runs | A | PASS: documentation explicitly distinguishes content from attempts and retains historical exceptions. |
| Keep required internal structure | A | PASS: actual `frames/`, `assets/`, `reference/`, `clean-a/` content directories allowed; separately managed examples use siblings. |
| Continue work without relocating accepted history | A | PASS: README legacy R3 input labeled; no historical write/move/regeneration/deletion; 42 focused historical metadata/hash records unchanged across exercise. |
| Lifecycle: Verification completion includes cleanup | A | PASS: success, failure/interruption, dependency closure, active work, protected evidence and pending completion specified across workflow/docs. |
| Finish a successful verification | A/N | PASS: accepted fixture's relative evidence link resolved before and after whole obsolete-container removal; no log/JSON fragment survived; byte receipt below. |
| Finish failed or interrupted verification | A | PASS: failure fixture retained while pending with reason `unresolved F-1` and trigger `after diagnostic review`; removed after review; pending cleared before completion. |
| Lifecycle: Cleanup respects ownership and records its result | A/N | PASS: scope is exact owned run; external target untouched; byte-accurate receipts retained here without a cleanup-history tree. |
| Remove a complete obsolete run safely | A/N | PASS: complete obsolete and failed simulated-run containers removed; relative dependency, protected/active fixtures and external target unchanged; final actual reviewer run removed entirely. |
| Reviewer encounters obsolete developer output | A | PASS: dry-run exact path `build/flat-build-workflow_r1_reviewer_try-1_checks/fixtures/developer-output/` handed off in the exercise as obsolete log outside simulated reviewer ownership; kept pending until simulated developer acknowledgement. Its file stayed unchanged. No real developer cleanup was requested or required. |
| Anatomical-skeleton: Structural visual review pack (modified path) | A | PASS for modification: future pack destination uses lifecycle convention; contents and visual gates unchanged. |
| Review the skeleton before muscles | A | Unchanged content/visual scenario; audited that diff does not weaken it. Existing anatomy/render acceptance not rerun. |
| Inspect the revised thorax closely | A | Unchanged content/visual scenario; fixed cameras, required views, metrics and renewed human gate preserved by narrow delta. Not rerendered. |
| Locate a future structural pack without migrating history | A | PASS: exact future convention and former generic history exception present; no current instruction directs new output to legacy location. |
| Joint-mobility: Verification report and human visual gate (modified path) | A | PASS for modification: future actual fresh pack root is required; numerical and human acceptance requirements preserved. |
| Review a completed implementation | A | PASS for path clause; per-action, coupling, numeric and visual coverage clauses unchanged and outside this documentation change's execution scope. |
| Verify a presentation-only derivative | A | Unchanged source/media/browser scenario; README keeps existing command/flags and legacy input, changes output to sibling flat root. No HTML/media regenerated or browser acceptance claimed. |
| Keep historical reports valid after adopting flat run names | A | PASS: reviewer output scoped to its actual exact fresh root, historical report/pack paths and preservation obligations retained. |

## Findings

| ID | Severity | Violated requirement/scenario | Evidence | Suggested direction |
| --- | --- | --- | --- | --- |
| — | — | None within approved scope | Independent audit and exercise above | — |

## Scope, provenance and limitations

Changed tracked implementation scope is exactly the five approved instruction/documentation files; other additions are this change's planning/review artifacts. No executable code, schemas, YAML, dependency contract, archived specification, generated media or licensing register change was present. `docs/used-materials.md` was inspected: no external source or asset was introduced or used to inform this workflow change, so no new register entry is required. Historical source licenses were not re-certified as part of this unrelated change.

Blender rendering/baking, source-data schema checks, animation timing/stability/contacts/direction/loops/mirroring/round-trip/determinism metrics and visual pack generation are not applicable: approved design explicitly excludes rebuilding skeleton media, permanent validators and a new test suite. Existing anatomy and presentation scenario content remains unchanged; its historical acceptance is not extended to a new source snapshot. Rules rely on operator discipline, as designed; this exercise does not claim runtime CLI enforcement.

## Cleanup receipt

All byte counts are exact logical content bytes from `lstat`, not filesystem allocation blocks. Symbolic-link payload bytes are reported separately and exclude target contents.

| Removed path | Regular-file bytes | Symlink payload bytes | Reason |
| --- | ---: | ---: | --- |
| `build/flat-build-workflow_r1_reviewer_try-1_checks/fixtures/obsolete/` | 12 | 45 | Obsolete simulated run, including log/JSON and external-target link; whole container removed without following link. |
| `build/flat-build-workflow_r1_reviewer_try-1_checks/fixtures/failed/` | 18 | 0 | Failure diagnosis concluded; no continuing diagnostic need. |
| `build/flat-build-workflow_r1_reviewer_try-1_checks/` (remaining content) | 84 | 93 | Exercise completed; simulated protected/active/ownership states ended; complete owned run removed. |
| **Total** | **114** | **138** | **252 logical bytes; no residual directory/log/JSON fragments.** |

- Retained build outputs: **none**. Retained durable evidence: this `review.md`; no second evidence registry or cleanup-history directory.
- Dependency checks: accepted fixture's `../protected/evidence.json` target resolved before and after candidate deletion; protected, active and simulated developer file hashes unchanged at ownership checkpoint. Final teardown occurred only after ending those simulations.
- External protection: symlink pointed to repository `AGENTS.md` outside `build/`; its SHA-256 was unchanged before/after candidate deletion and final teardown. The link itself was unlinked; target not traversed for deletion.
- Historical protection: 42 metadata/focused-small-file hash records covering immediate historical entries and selected R2/R3 pack indices/evidence were identical before/after. No broad 33-GB hash scan was performed. This is bounded preservation evidence, not a claim to have rehashed all historical media.
- Final check: exact reviewer run no longer exists; no developer or other reviewer root was changed or cleaned. Real developer cleanup hand-off: **none required**. Pending cleanup: **none**.
