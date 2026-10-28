# Independent policy review

Verdict: **PASS.** This is a governance-only change; no Blender, render, bake, or motion metrics are applicable. Early visual gate: **not applicable**, because this change alters instructions and workflow documentation only. No new external material was used; `docs/used-materials.md` has no change in this scope. Final visual approval of `add-shared-body-characters` remains the human's decision and is not implied here.

## Findings

| ID | Severity | Requirement or scenario | Evidence | Suggested direction |
|---|---|---|---|
| R1 | major, resolved | Early visual approval precedes expensive verification; bounded preview command plan | Historical thorax/squat workflows prepared default three BPMs and called `review-pack`, which runs `clean-a` and `clean-b` (`review_pack.py:1413-1420`). The entire sequences are now explicitly post-acceptance in `tools/README.md`, “Focused thoracic preview” and “Squat R3 static plausibility and focused preview”. | No further action. |
| R2 | major, resolved | Preview exposes the proposed visual direction; task 2.1 supported worked command plan | The original plan implied an unsupported render sample selector. `tools/README.md` now specifies the full selected fixture at one BPM, all 13 samples / 78 images calculated from the sampling and fixed-view source, one `render_only=True` pass, and presentation from existing images. `api.py:828-839` has no sample selector; `run_blender.py:139-145` enumerates every prepared sample. | No further action. The image count is a source-based calculation, not a measured render. |
| R3 | minor, resolved | A change has no visual effect | `developer-handoff.md` now records this change's own early-gate `not applicable` decision and reason. | No further action. |

## Requirement and scenario checklist

All items are policy/command-plan audits, not executed product enforcement. Human visual judgement applies to actual visual changes, not to this change.

| Requirement/scenario | Independent check and result |
|---|---|
| Lifecycle / independent implementation | Automatable instruction audit: `AGENTS.md` roles and flow preserve parallel independent delegation and Gate 1. PASS. |
| Lifecycle / separate implementation and acceptance | Instruction audit: reviewer role has separate output ownership; `AGENTS.md` flow preserves final independent review, Gate 2, cleanup. PASS. |
| Early approval / visual ready | Command-plan audit: policy blocks full scopes until explicit decision (`AGENTS.md:101-103`); historical full workflows are explicitly post-acceptance. PASS. |
| Early approval / nonvisual | Scope audit: explicit not-applicable decision and reason in hand-off, no render needed. PASS. |
| Preview / character or motion | Instruction audit: `tools/README.md` covers scene, variants, samples, tempo, motion/GIF/onion skin, supported route and disclosure. PASS as a command-plan audit. Human evaluation is not applicable to this governance-only review. |
| Decision / rejected or absent | Ordered policy trace: pending, rejected or generic continuation → no expensive verification; approved correction → new preview and decision. PASS. |
| Decision / source changes | Ordered policy trace: visual change → fresh preview and acceptance; technical change → document applicability and rerun identity-bound checks without relabeling evidence (`AGENTS.md:105,110`). PASS. |
| Decision / in-flight adoption | Policy trace: preserve old evidence, no invented acceptance or gratuitous reruns; hold remaining applicable expensive work and retain final human gate (`AGENTS.md:105`; hand-off in-flight section). PASS. |
| Accepted and final gate | Explicit accepted message and identity → pre-freeze audit → candidate freeze → independent full verification → independent final pack → human Gate 2 → cleanup/archive; early acceptance is not final approval. PASS. |

## Verification and limitations

- `openspec validate add-early-visual-gate --strict`: PASS. Python `tomllib` successfully parsed agent TOML files.
- Independently traced `prepare` → `validate_sources` → selected-fixture sampling and `render` → backend output enumeration, plus `review-pack` clean passes. Source validation does validate all bundled fixture documents for schema/integrity; this is distinct from running a full diagnostic render/tempo matrix and is not bypassed.
- Source-clearance guidance requires register and commercial/derivative clearance before preview (`AGENTS.md` sections 4 and 8, `tools/README.md:176`). No newly introduced source was identified in the governance diff; older register entries are outside this change's provenance scope.
- Project rules retain uv-created environments, interpreter/origin/.pth/cache checks and process-inspection preflight (`AGENTS.md` section 7). This audit did not create an environment or launch process-supervision tests. Reviewer output is separate from developer output; source files and historical in-flight changes were not modified. Existing reviewer-model diff predates this change according to developer hand-off and is outside this review's scope.
- The checks do not establish visual correctness or runtime measurements; neither is needed for this governance-only change. There is no review image pack or question for human visual decision for this change.

## Ownership and cleanup

- Fresh reviewer-owned root `build/add-early-visual-gate_r1_reviewer_try-1_policy-check/`, direct child of build, was empty at creation and contained no outputs or symlinks. This report is the sole required receipt and depends only on tracked workspace sources, not that root.
- Removed empty owned root `build/add-early-visual-gate_r1_reviewer_try-1_policy-check/`: 0 file bytes; no retained reviewer build roots. Its removal cannot break an evidence link because none points to content inside it. `review.md` resolves in the change directory; other agents' and historical runs were not touched. Pending cleanup: none.

## Final hand-off recheck

After developer cleanup, the retained [corrected policy audit](../../../build/add-early-visual-gate_r1_dev_try-2_policy-check/policy-audit.md) exists, is inside the expected direct build child, has no symlinks, covers the eight scenarios and identifies its image count as calculated. Its relative README links resolve; the hand-off points to the current bounded route. The obsolete dev try-1 root is absent; the hand-off records its removal as 2,154 bytes and explains retention and dependency checks. The task 3.1 evidence path resolves. Strict OpenSpec validation passed again. The final instruction diff still contains the local post-acceptance caveats for the entire historical thorax and squat sequences. Verdict remains **PASS**; reviewer work for tasks 3.3–3.4 is complete, with no pending reviewer cleanup.
