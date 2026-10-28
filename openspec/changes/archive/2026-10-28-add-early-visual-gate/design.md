# Design

## Context

See `proposal.md` for motivation. `project-governance` currently orders spec approval, implementation, independent review and final visual approval. `AGENTS.md` also requires a joint pre-freeze audit, controlled process ownership, compact checkpoints and uv-created environments. The late gate has allowed complete numeric matrices and repeated renders before a human judges the visible result. The current `add-shared-body-characters` change has already completed its technical review and is awaiting its final human visual decision; this proposal does not modify or approve that change.

## Goals / Non-Goals

**Goals:** bound the work needed for the first visual decision, make that decision explicit, and prevent known visual rejection from consuming full verification resources.

**Non-goals:** a new CLI, automatic visual judgment, weaker acceptance metrics, changing licensing or package identity, retrospective approval, new images for this governance change, or replacement of independent final checks.

## Decisions

### 1. Add a named early gate without renumbering Gate 1 or Gate 2

The ordered path for a visual-affecting change is:

1. Human Gate 1 approves OpenSpec requirements, including the bounded preview plan.
2. Dev implements the smallest coherent visual result and runs preview prerequisites.
3. Dev generates one bounded preview; the orchestrator presents it and records **Early visual gate: accepted / rejected / pending**.
4. On acceptance, the roles conduct the existing joint pre-freeze audit and resolve contract, documentation, environment and negative-case gaps before freezing the final candidate.
5. Dev and independent reviewer run all required full verification and final packs with their declared identities and ownership.
6. Human Gate 2 judges the independently verified final pack; cleanup and archive retain their existing order.

An early acceptance means the proposed visual direction is suitable for investing in full verification. It is not proof of geometry, contacts, timing, determinism or final visual correctness. Keeping the current final Gate 2 avoids silently weakening archived and in-flight acceptance contracts. Moving the only existing visual gate earlier was rejected because later fixes can change the visible result and a developer preview cannot replace an independent final pack.

### 2. Bound work by declared scope rather than a guessed runtime threshold

The preview plan explicitly lists allowed preparation/render work and the deferred checks. Before early acceptance, allow source/material clearance, selected source/schema/identity validation, uv/process/environment preflight, focused unit or smoke checks needed to render safely, and a single candidate packaging step when required by the existing installed/identity workflow. Existing API validation is not bypassed to make a preview cheaper.

Defer complete regression suites, all-fixture or all-tempo/stature matrices, <=0.01-beat full dense audits, duplicate clean render/pixel comparisons, full multi-build package closure checks and full acceptance packs. A generating command that automatically triggers these scopes is not an appropriate early-preview command merely because it is called a preview. The developer selects a supported bounded route described in the change and records the command and limits. If the current route cannot meet the plan safely, it returns to the architect for a bounded solution before running the full workload.

An existing supported route can produce a bounded body-direction preview without new CLI flags: public `prepare(..., profile="adult-reference-v1", stature=1.70, fixtures=("arm-raise",), bpms=(120,))`, then one public `render(..., images=True, characters=("skeleton", "male", "female"), render_only=True)` in a distinct fresh flat run. This prepares and renders **all** samples of that fixture, not an invented sample subset. The current four-beat fixture includes its neutral baseline at beat 0 and yields 13 samples at 120 BPM; its fixed front/side views for three characters imply 78 PNGs (calculated from the source and sampling rule, not measured by a new render). `render_only=True` retains sealed, supervised rendering while omitting full evaluated/native-midpoint measurements. Presentation may select existing result images by `(character_id, sample_id, view)` and use `prepared.timelines` for correctly timed GIFs and onion skins; it does not trigger another Blender run or claim that fewer images were generated.

The worked guidance must show this public API route, its actual complete-fixture sample/view count, separate prepare/render/presentation roots, and a reproducible presentation plan using only already generated images. It must not promise sample selection through `render`, use the default three-BPM preparation for an alleged one-BPM preview, or call normal `review-pack` before the early decision: that command starts repeat render passes. Existing focused thorax/squat diagnostic examples must be explicitly labelled as post-early-acceptance workflows unless replaced with a genuinely bounded supported route. A scoped fixture name alone is insufficient permission for those commands.

Changes with no visible effect record early gate `not applicable` and the scope reason in the hand-off, including this governance-only change. A numeric value or automatic check cannot accept a visual direction.

### 3. Use a small, named human acceptance pack

Each visual feature's Gate 1 plan chooses exact samples; the default is one representative supported stature and one supported tempo, not the full matrix. The compact pack has an `index.md` or HTML entry point and:

- One front/side sheet with columns for every changed visible variant and a relevant unchanged comparator; rows for neutral/rest or equivalent baseline and at least one representative changed count pose. Labels identify character, fixture/pose, beat and view.
- For changed motion, one complete representative segment (or the smallest closed cycle necessary to see direction), a correctly timed GIF and an onion-skin overlay with start, intermediate and end samples. Static and animated samples use the same keyed animation and the existing beat sampling rule, including explicit via poses where direction requires them.
- Close-ups of affected joints, surface junctions or support contacts. For a new exercise body this ordinarily includes shoulder, waist/hip, knee and sole; a change affecting fewer areas limits these details accordingly.
- A concise inventory with source/package identity, pinned backend version, fixed scene, selected stature/BPM and omitted checks. State that native/dense/full-matrix/repeatability/independent-final scopes are pending, not passed.

All actual external materials must have commercial/derivative/distribution permission checked before even this preview and be registered in `docs/used-materials.md`. This governance change uses no new external material.

### 4. Record one decision against one preview and renew it when needed

The existing hand-off or orchestration record holds the preview identity, run path, scopes and limitations, the exact human message reference and decision, and the next allowed work. Generic requests to continue do not constitute visual acceptance. A rejection leads to corrections, a fresh run and resubmission; only work needed to repair and preview the rejected direction continues before acceptance.

Any source change is assessed for visual impact. A changed silhouette, pose/motion, binding/deformation, scene or rendering needs renewed early acceptance before more expensive verification. A documentation-only or other technical change records why the previously judged direction still applies, while its new package identity and renewed technical checks still follow the existing contract. The old preview never acquires a new hash retroactively.

### 5. Align role instructions and verify the process without rendering

Implementation edits `AGENTS.md`, `.codex/agents/architect.toml`, `.codex/agents/dev.toml`, `.codex/agents/reviewer.toml` and contributor guidance as needed. Architect plans the bounded sample set and sequencing, dev produces the preview before expensive checks, reviewer checks the explicit early decision before starting expensive final reproduction, and the orchestrator records and presents it. The early gate is a human decision; the reviewer must still reproduce final technical evidence independently.

Verify with a policy/command-plan audit covering: accepted, rejected, absent decision, changed visual sources, technical-only changes, nonvisual change, adoption during unfinished work, and preserved final gate. No test of this governance change needs Blender, a full host suite or a rendered demonstration. If an independently managed policy audit writes outputs, use `build/add-early-visual-gate_r1_dev_try-1_policy-check/` and a distinct reviewer root `build/add-early-visual-gate_r1_reviewer_try-1_policy-check/`. Keep required audit receipts and remove obsolete whole owned attempts after checking links and ownership; record removed bytes, retained reasons and pending cleanup in the hand-off/review record.

## Risks / Trade-offs

- **The small preview misses a later defect.** Full independent technical verification and final Human Gate 2 remain mandatory.
- **The preview grows into a full acceptance pack.** Gate 1 names a bounded sample list and deferred workload; the pre-run command audit checks the real scope.
- **The human's decision is ambiguous.** Keep the gate pending until explicit acceptance or rejection of the identified preview is received.
- **A later technical fix changes appearance.** Assess visual impact and renew the early gate when affected; keep exact identity and evidence scopes.
- **Retrofitting invalidates existing work unnecessarily.** Apply the ordering only to remaining work and new visual revisions; preserve all recorded outcomes and required history.

## Migration Plan

After approval, update the project and role guidance coherently, audit the workflow scenarios, and obtain an independent policy review. For any in-flight change, record completed scopes and pending visual decisions without inventing an early acceptance. If its expensive verification is already complete, continue to the required final human gate; do not rerun work just to simulate an earlier preview. New visual revisions use the early gate before renewed expensive checks. Reverting this governance change would require an explicitly approved process change; no runtime/data migration or release is introduced here.
