# Developer hand-off

## Workflow and decision record

**Early visual gate for `add-early-visual-gate`: not applicable.** Reason: this approved change modifies governance and contributor instructions only; it changes no poses, motions, visible characters, scene, rendering behavior, or other visible result. There is no visual direction to preview or ask the human to judge.

For visual work, retain one record per preview with: change and approved plan; source/package identity; owned run path; exact commands and fixture/pose/segment, variants, views/details, stature and tempo; artifacts; completed prerequisites; deferred scopes and limitations; decision (`accepted`, `rejected`, `pending`, or `not applicable` with a reason) with exact human-message reference when a human decision applies; next permitted work; and cleanup/dependency status. A generic “continue” leaves the decision pending. Rejection permits only approved correction and a fresh preview. Changed visual sources require a new preview and decision before further expensive checks. Technical-only changes record the applicability rationale and rerun identity-required checks. Nonvisual work records `not applicable` and why.

For in-flight work, preserve historical evidence, scope, and identity; never create a retrospective early approval. If expensive verification is already complete, do not rerun it just to mimic the new order. If it remains, hold it until an applicable early decision. Independent final review and final Human Gate 2 remain required for visual changes. Applied example: `add-shared-body-characters` already has technical review evidence and is awaiting its final human visual decision, as stated in this change's design; this governance change does not relabel that evidence, invent an early decision or require reruns solely to recreate the earlier ordering.

## Policy command-plan audit

Audited against the delta scenarios in `specs/project-governance/spec.md`, `AGENTS.md` lines 100–112 and the [Early visual gate and bounded preview section](../../../tools/README.md#early-visual-gate-and-bounded-preview), lines 172–257. This is a policy dry run, not an executed render or acceptance result.

| Case | Ordered trace and evidence | Result |
|---|---|---|
| Accepted | Gate 1 approves the preview plan (AGENTS 100); prerequisites and bounded preview only (101–102); record explicit accepted decision and preview identity (102); then joint audit, freeze, full checks, independent review (103–104); final human Gate 2 (104). | Conforms; early acceptance only unlocks later work. |
| Rejected | Generate bounded preview (101–102); record rejection; stop full suites/matrices/dense/repeated renders (101–102); correct only approved scope and produce a fresh preview (102); retry decision before expensive work. | Conforms; no full verification on rejected visual direction. |
| No decision | Record `pending`; silence, “continue”, metrics or a running process do not accept (102); keep expensive verification blocked. | Conforms. |
| Changed visual sources | Assess source change; appearance/pose/motion/scene/render changes require fresh preview and renewed early decision before expensive work (105); never relabel prior identity. | Conforms. |
| Technical-only change | Record applicability; renew identity-bound checks (105, 110, 112); prior preview remains scoped to its recorded inputs. | Conforms. |
| Nonvisual change | Record `not applicable` with scope reason; proceed to applicable technical/review gates without gratuitous preview (103). | Conforms. |
| In-flight adoption | Preserve completed evidence and identity; no retrospective decision; no rerun solely to simulate ordering; defer only remaining expensive work for an unaccepted visual direction; retain final Gate 2 (105). | Conforms. |
| Final gate preserved | Full independent technical verification and reviewer-owned pack follow early acceptance (103–104); human Gate 2 remains before archive (104–105). | Conforms; early gate does not replace final acceptance. |

Worked route in the [Early visual gate and bounded preview section](../../../tools/README.md#early-visual-gate-and-bounded-preview), lines 178–257, names the complete `arm-raise` fixture, all three variants, front/side views and fixed-crop details, H=1.70 m, 120 BPM, all 13 samples/78 planned PNGs, and deferred scopes. The contact sheet chooses only already generated beats 0/2/4; GIF/onion use the full returned animation timeline and fail if the existing timing helper does not pass. Public API signatures and fixture/sampling/render behavior were checked read-only; no render was run.

## Verification and cleanup

- `openspec validate add-early-visual-gate --strict`: passed.
- No Blender, full host suite, render matrix or external material was used for this governance audit.
- The eight scenario traces are policy checks based on cited instructions, not executed product behavior.
- Corrected dev audit root: `build/add-early-visual-gate_r1_dev_try-2_policy-check/`; it contains the corrected route evidence and eight scenario traces. After the independent PASS, removed obsolete own root `build/add-early-visual-gate_r1_dev_try-1_policy-check/` (one receipt, 2,154 bytes). Before removal, `realpath` confirmed it was a direct child of `build/`, `find -P` found no symlinks, and `rg` found no consumer dependency beyond the historical build-plan name and this hand-off. Post-check confirmed the root no longer exists; try-2 remains the sole retained dev policy-audit root, is a direct child of `build/`, and contains only its required receipt with no symlinks. Other agents' and reviewer-owned roots were untouched. Pending cleanup: none.
- Role instruction paragraphs for `.codex/agents/architect.toml`, `dev.toml`, and `reviewer.toml` are applied and reviewed in the working diff. Existing role ownership boundaries remain in place; the pre-existing reviewer model change was preserved.
