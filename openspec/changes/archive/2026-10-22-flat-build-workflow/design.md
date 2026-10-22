# Design

## Context

See `proposal.md` for motivation. `AGENTS.md` and both execution-agent instructions currently prescribe `build/review/<change-id>/`; reviewer write and cleanup permissions repeat that scope. The main `anatomical-skeleton` and `joint-mobility` specs also prescribe the old review path. `tools/README.md` mixes short scratch paths with deeply nested review examples.

Existing commands take explicit output paths. `review_pack.py` has necessary internal `clean-a`/`clean-b` render passes, `frames/`, reference data and composites; presentation derivatives use `assets/` to preserve media dependencies. These are content, not independently initiated workflow attempts. Generating a derivative inside its predecessor can change the predecessor inventory even when verification later rejects it, so destination separation must be checked before launch.

## Goals / Non-Goals

**Goals:** Make future run identity and deletion boundaries obvious, replace conflicting instructions consistently, and make cleanup part of every developer/reviewer completion hand-off.

**Non-Goals:** A cleanup engine, new CLI flags, automatic runtime path enforcement, a new manifest format, flattening internal artifact layouts, rewriting archived evidence, migrating the current accepted HTML pack, or another skeleton render. Pose/segment/motion data, body groups, controls/rest policies, contacts, beats, bake behavior, fixed cameras/floor and frame timing remain unchanged.

## Decisions

### 1. Five components, one unambiguous separator

Use `build/<change>_<revision>_<role>_<attempt>_<kind>/`. All five components are present and follow lowercase kebab-case (`[a-z0-9]+(?:-[a-z0-9]+)*`); `_` is reserved for joining components. Use the OpenSpec change ID, a meaningful revision such as `r1`, the owning role (`dev` or `reviewer`), an explicit attempt such as `try-1` or `fix-try`, and an artifact kind such as `build`, `checks` or `pack`. Names do not include machine-specific paths or settings.

Example: `build/anatomical-human-skeleton_r3_reviewer_fix-try_pack/`. A sibling attempt changes `fix-try` to `fix-try-2`. New run allocation requires a nonexistent or empty destination; never overwrite an occupied previous attempt. Later steps of the *same* run can consume and add its own artifacts: preparation followed by building beside its `input.json` is valid. Distinct input and output run roots cannot coincide or contain one another, including through resolved symlinks.

Joining everything with `-` was rejected because existing change and stage names already contain hyphens. Requiring every component to abandon hyphens would unnecessarily alter familiar change IDs. Additional `build/review/` or per-change parent directories were rejected because they reintroduce identification hierarchy.

### 2. Flatten workflow identity, retain tool-managed content

Independently initiated build, check, reviewer and derivative-pack runs get sibling roots. Files and content subdirectories inside a run keep tool-required relative structure, including `assets/` paths derived from predecessor media. Do not relocate internal files or change tools to satisfy this instruction. A logical retry is not represented by creating another `revision/independent/fix/pack/` under an existing run. Ordinary temporary test fixtures inside one owned checks run remain content.

### 3. Keep one consistent workflow contract

Update these exact locations after Human gate 1:

| File | Required adjustment |
| --- | --- |
| `AGENTS.md` | Repository-layout note, Flow reviewer output path, tooling rules and completion cleanup; reserve `_` and distinguish content from independent runs. Leave managed blocks untouched. |
| `.codex/agents/architect.toml` | Require planned acceptance packs and tasks to use the naming convention and include cleanup verification. |
| `.codex/agents/dev.toml` | Flat build/check/pack roots; preflight allocation; cleanup before hand-off; honest pending-cleanup reporting. |
| `.codex/agents/reviewer.toml` | Replace all old nested write/output/cleanup scope references with only this reviewer's explicitly identified owned flat run roots. Keep access to `openspec/changes/<change-id>/review.md`, and keep the developer hand-off for cleanup outside owned roots. Preserve accepted/protected evidence even inside owned roots. |
| `tools/README.md` | Define the convention once and make all current runnable build, preview, verification, stature and HTML-derivative output examples consistent. Include the cleanup checklist and a compact hand-off example. Explicitly label any retained historical input path as legacy. |

Use existing entry points and flags. For example, replace future basic outputs with `build/anatomical-human-skeleton_r1_dev_try-1_build/` and a sibling `..._checks/` or `..._pack/`; keep preparation and building in the same owned build root. Existing historical predecessor inputs remain literal paths and are labeled accordingly. Do not edit `.agents/skills/`, executable code or old archived specifications.

### 4. Cleanup is a completion step with bounded retention

After checks finish, the owning agent inventories the generated outputs concerned, identifies the accepted result and complete dependency closure, and separates removal candidates from retained outputs. Follow actual pack/media/timing/provenance/numeric-evidence references; a required artifact is not obsolete just because another run contains the current HTML. Explicit complete-history preservation requirements still apply even when not discoverable by HTML links.

Remove obsolete whole run roots where possible. Within retained runs remove temporary files only if no pack, evidence or explicit preservation obligation requires them. Do not retain arbitrary JSON/log files merely because they are small. Keep a diagnostic only with its concrete purpose and a revisit trigger (for example, until its finding is resolved). Failed and interrupted checks use the same classification; unresolved failures and active resumable work are valid reasons, not blanket reasons to retain every attempt forever.

Only generated paths resolved inside `build/` are deletion candidates. Do not traverse symlinks outside it, touch another active agent's work or use whole-`build` deletion. A reviewer removes only its own unprotected runs; the developer handles other candidates after exact-path hand-off. Check dependencies before deletion and again afterward. If a required cleanup cannot finish, report the exact pending item and do not claim completion.

Append a compact Markdown cleanup section to the existing durable review or developer hand-off record: removed paths/bytes, retained roots/exceptional files with reasons, dependency-check result and pending work (`none` if empty). A short grouped list can describe a retained pack and its dependency closure. Keep the record in an existing retained run or `review.md`; do not create a new per-attempt cleanup-history tree or custom registry. The developer's own completion evidence can use the existing change's `tasks.md` verification notes. A reviewer records its own outcome in `review.md` without editing tasks or specs.

### 5. Verify the workflow without rebuilding the skeleton

The independent reviewer audits all updated instructions and current command examples for consistency, parses the three TOML files, and exercises the documented allocation/cleanup procedure on tiny disposable fixtures under its own flat checks run. Cover valid `fix-try`, invalid `_` inside a component, nested run identity, occupied new-run destination, distinct input/output overlap, allowed `frames/assets/clean-a` content, success cleanup, failed/pending cleanup, an external symlink, a protected dependency and an unrelated active run. These are workflow checks, not a new permanent executable validator or test suite.

For the cleanup exercise, use small text files with relative links; prove the necessary target survives, the obsolete whole run disappears, dangling fragments are absent, protected/external/active files are unchanged, and the receipt matches actual removed bytes. Document the reviewer-to-developer hand-off case as a dry run without deleting developer outputs. Remove the exercise's disposable material after verification; keep its compact result in `review.md`.

No visual acceptance frames, GIF, contact sheet or onion-skin overlay is required for this instruction-only change. Existing accepted visual packs are not changed. Human gate 1 approves this workflow; independent review checks its implementation. Source clearance remains mandatory if external material is unexpectedly introduced; none is needed here, so do not add unused entries to `docs/used-materials.md`.

## Risks / Trade-offs

- Flat root names are longer and rely on agent discipline rather than automatic CLI enforcement → keep one exact convention and independently audit examples/hand-offs.
- Cleanup could break an accepted derivative through predecessor references → protect dependency closure and explicit historical requirements before deletion and check links afterward.
- Reviewer scope could accidentally expand to other agents' output → retain ownership restriction and exact-path developer hand-off in every affected instruction.
- Old nested paths remain visible → mark them as legacy retained inputs; relocation is a separate task requiring its own dependency/immutability plan.

## Migration Plan

Adopt the instructions for new runs after approval. Update current instructions and README examples together, then independently verify and clean the small acceptance exercise. Sync the two narrow path deltas and new lifecycle specification using the normal OpenSpec workflow when finalizing the change. Leave archived changes, historical R2/R3 proofs and current accepted pack untouched. Roll back an instruction error by restoring the affected text; do not move existing evidence as part of rollback.
