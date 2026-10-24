# Design

## Context

The preceding distribution change already provides a resource boundary rather than a complete pipeline location contract. Read-only inspection found:

- `package_resources.py` uses `importlib.resources.files("humanmotionlib")`, verifies declared resource bytes and implementation hashes, and supplies the backend contract. `validate.py`, `source_validation.py` and `prepared.py` already use that boundary for installed validation and prepared-input identity.
- `runtime.workspace_root(None)` selects `Path.cwd()`. `validate_run_root`, backend slot state and invocation receipts build on this optional selection. `prepare_skeleton.py`, `run_blender.py` and `review_pack.py` resolve operands using ambient cwd before validating destinations.
- `cli.py` forwards workspace only to preparation, backend execution and review creation. `verify_skeleton.main()` receives no workspace and writes `--output` without run ownership checks. Its `verification_run.verify_collection()` also creates a sibling `<report-stem>-samples/` directory.
- `run_blender.run()` supplies the installed `build_skeleton.py` path and explicit workspace to Blender; the script bootstraps only its own package and disables bytecode writes. Supervisor child environments remove `PYTHONPATH`/`PYTHONHOME` but inherit temporary-directory and application state locations.
- `review_pack.main()` requires normal inputs to be a run in the output workspace. HTML-only regeneration accepts a supplied predecessor but `presentation.regenerate_html()` subsequently searches for the first path component named `build` to produce provenance. A preserved external predecessor without that component fails after presentation writes have begun.
- Package CI already installs a wheel non-editably, makes package files read-only and runs from a different directory. That directory and its workspace are fixture directories under the checkout's package check run; the current smoke scope does not establish every writer's behavior without accessible neighboring source trees.
- `runtime.project_root()` and explicit source-root validation branches serve contributor tests; `check_host.py` separates installed environment inspection from contributor discovery. Runtime portability does not require shipping tests or source metadata.

File names above are under `src/humanmotionlib/` unless stated otherwise. No generation, backend execution or source modification was performed while drafting this design.

## Goals / Non-Goals

**Goals:** use an installed HML wheel from arbitrary invocation directories; require a caller-selected writable workspace; contain HML-controlled outputs, temporary files, logs and locks; preserve package/prepared/render/predecessor integrity; demonstrate unchanged generated motion and framing.

**Non-goals:** changing canonical anatomy, poses, segments, motions, controls, rest policies, contacts, beat sampling, source or prepared formats, backend pins, supported host Python, distribution naming or release version; adding dependencies; publishing a release; supporting zipped Python imports; changing PEP 517 source-build staging. Building a wheel is a producer operation with source inputs, distinct from executing the installed wheel.

## Decisions

### 1. Require one absolute workspace at every state-writing workflow boundary

Keep the existing global spelling `hml --workspace ABSOLUTE_PATH <command>` and the equivalent module invocation. Require it for `prepare-skeleton`, `run-blender`, `verify-skeleton` and every `review-pack` mode, including render reuse and HTML-only regeneration. Help for any command remains available without workspace selection. Version, help, `validate` and `check-environment` remain read-only and require no workspace.

Python workflow entry points that allocate runs, produce verification/presentation files or launch supervised children accept an explicit workspace and reject omitted, empty or relative selections before writing or spawning. Propagate that value through all calls; a wrapper must not restore an ambient default. Pure in-memory functions such as `prepare()`, `verify_transforms()` and mathematical evaluators need no workspace. Low-level serialization helpers operate only on destinations validated by their owning workflow and are not an alternative pipeline entry point.

Normalize the supplied absolute path once, resolving symlinks. An explicit alias to a workspace may resolve to its real directory; that resolved directory defines ownership and slot identity. An existing non-directory or non-writable destination fails clearly. A new workspace may be created only after lexical arguments and intended ownership have passed preflight. Never infer a workspace from input/output ancestry, installation location, a nearby checkout, an environment source-root hint or cwd.

Requiring an absolute selection rather than interpreting a relative workspace once avoids retaining an initial cwd dependency. Retaining `workspace/build/` rather than accepting arbitrary output roots preserves the established build lifecycle and avoids another directory convention.

### 2. Anchor operands to the workspace and distinguish reads from writes

Resolve relative workflow path operands against the explicit workspace, then normalize them. This includes prepared input, backend input/output/render destinations, verification reports and stature inputs, review inputs/output, and HTML-only predecessors. Absolute operands retain their explicit meanings.

| Path purpose | Resolution and ownership |
|---|---|
| Runtime data, schemas, scene, licenses, notices, backend contract and implementation | Installed package resource/implementation inventory only |
| Relative workflow operand | Selected workspace plus the supplied relative path |
| Absolute read-only input | Explicit supplied path; may be in another workspace or protected legacy location |
| New independent output | Fresh valid five-component direct child of selected `workspace/build/` |
| Content output, report shards, frames, receipts, logs and scratch | Validated content paths within their owning run |
| Shared persistent backend lock and state | Selected `workspace/build/.backend-execution.lock` and `.backend-execution-state.json` |

Check containment after symlink resolution and reject a `build/`, run root or child destination that redirects writes outside its owner. Reject escaping `..` paths and absolute destinations outside the allowed root. Avoid searching lexical path components for ownership. Input/output disjointness, fresh attempt identities and rejection of nested independent runs remain enforced. Keep the existing narrowly defined prepared-input/build-output co-ownership exception within one designated run; it does not permit overwriting successful or failed backend products.

Normal review input may be an explicitly selected valid build from another workspace: validate its prepared/backend evidence and read-only ownership rather than requiring its owner to equal the output workspace. Protected legacy paths remain readable through existing supported predecessor modes without renaming or rewriting them. Do not make arbitrary directory contents eligible merely because their path is explicit.

Numeric verification allocates or validates its fresh check run before creating the report or `<report-stem>-samples/` shards. Full verification, preview and transforms-only modes use the same path policy. Render reuse is the existing exception for resuming assembly of an owned complete pack: validate managed contents and all reuse identities before any modification. It does not authorize another generation attempt inside that root.

All operation preflight that can be completed from arguments, resource identity and existing inputs occurs before creating output content or starting a backend. Invalid workspace selections must not even allocate locks or receipts. Invalid existing input evidence must not partially publish a pack.

### 3. Carry workspace ownership into backend execution and scratch

Use one validated workspace context for run allocation, supervisor receipts, backend cwd and lock selection. Backend cwd is the selected workspace, explicitly passed; changing the host process cwd is unnecessary. Canonical source identity never includes that cwd.

Create scratch under the owning invocation/run, not the installation, a neighboring checkout or the system temporary default. Configure child temporary-directory variables and Blender-controlled writable configuration/cache paths to those run-local directories. Use a child-environment copy; do not mutate the pipeline's global environment or leave `tempfile` global settings changed. Keep the existing removal of host Python path/home injection and retain Blender's independent embedded interpreter. HML-controlled extraction, temporary files and logs, if needed, follow the same ownership rule. Ordinary OS service activity outside HML's control is outside the output contract.

Keep the installed backend script/import closure alive and read-only for the full invocation. Do not copy unchecked scripts into scratch or depend on host site-packages in Blender. Preserve executable discovery, version/build checks, deadlines, process-tree cancellation, finite slot waits, orphan-ownership safeguards, phase markers and fresh output validation.

Two callers, including distinct installations and symlink aliases, selecting the same resolved workspace contend on the same persistent lock/state. Distinct workspaces remain distinct serialization domains; this change does not introduce a machine-global Blender lock. Receipts identify resolved workspace, owning run and scratch locations as diagnostic paths alongside unchanged package and prepared identities. Scratch cleanup follows dependency-aware run cleanup; unresolved failure evidence retains a concrete reason.

### 4. Preserve resource and evidence checks during path migration

Retain `importlib.resources` access and manifest validation; do not implement another source discovery mechanism. No runtime fallback to `rig/`, `schema/`, `scenes/`, `docs/`, `pyproject.toml`, `uv.lock` or a sibling checkout is allowed when an installed resource is absent or corrupt. Explicit contributor source inspection remains separate and must not be called by installed workflow commands.

Retain canonical prepared JSON hashing, finite values, duplicate-key rejection, logical source hashes, package version/manifest/implementation checks, sample inventories, backend prepared-hash correspondence and render-reuse receipts/manifests. Location changes affect diagnostic paths, not canonical resource identity. Compare identical-wheel preparations across installations/workspaces/cwds byte-for-byte. Candidate-to-baseline comparisons allow changed implementation/package metadata but require unchanged canonical data, sampling, evaluated geometry and pixels under the existing bounds.

For HTML-only derivatives, resolve predecessor and output from explicit operands and validate their disjointness and full evidence/media closure before writing. Replace the first-`build`-component heuristic with the explicit predecessor path. Keep `review-presentation-provenance/v1`; the existing `predecessor` string is diagnostic: use a workspace-relative path when the predecessor is contained in the selected workspace, otherwise its explicit normalized absolute path. Predecessor identity remains the retained source-snapshot, verdict and media/evidence hashes. Existing historical provenance files remain untouched and readable; do not reinterpret them as the active package's source identity. HTML links continue to be generated from the actual predecessor/output roots, preserving local copied visual assets and required predecessor evidence links. No Blender process is launched for HTML-only or render reuse.

No external content is necessary for this change. If implementation or verification actually uses any external tool, action, reference or asset beyond existing cleared usage, verify commercial and derivative permissions compatible with the intended distribution before use and record the exact used part/version and clearance in `docs/used-materials.md`, including no-attribution sources. Preserve existing output attribution.

### 5. Make portability a distributable-artifact check

Build and record one exact wheel, retain direct/sdist resource parity and install non-editably into fresh supported environments. Installed acceptance uses caller fixture workspaces and cwd directories disjoint from the HML source tree; no checkout is available through imports, neighboring resource directories or source-root environment variables. An installed check harness is copied with its required fixture inputs, rather than importing repository test helpers at runtime. A repository may remain available only to the outer harness for build provenance and before/after auditing.

Temporary fixture workspaces belonging to one check run may live under its content directory; they are test content, not independent verification attempts. To prove physical checkout independence, stage that owning check run beneath an explicit external caller `build/` root, with the normal five-component identity. The outer hand-off records its absolute selected workspace. Do not describe a changed cwd under the checkout as sufficient isolation.

| Check | Required evidence |
|---|---|
| CLI/module/API path contract | Missing/empty/relative workspace rejection; two unrelated cwd values; identical resolved operands and prepared bytes; read-only commands without workspace; help without allocation |
| Package resources | Read-only install and absent checkout; misleading cwd/sibling `rig`, schema, scene and project files ignored; missing/corrupt packaged resource fails before Blender even when a valid-looking checkout exists |
| Write containment | Before/after inventories for install, source tree, cwd and external sentinel; report shards, scratch, logs and state only in selected ownership roots; invalid destinations and escaping symlinks rejected before mutation |
| Integrity negatives | Existing prepared-content, logical-source, manifest/implementation, evaluated identity, incomplete/stale render-reuse and predecessor-media failures stay failures; no fallback or bypass flags |
| External predecessor | Protected read-only predecessor outside any `build` directory; misleading ancestor named `build`; HTML-only succeeds, keeps media/evidence hashes and valid links, launches no backend |
| Supervision | Same-workspace callers across installations/aliases serialize; distinct workspaces use distinct state; timeout/cancellation/spawn/orphan failure checks retain evidence and owned-child cleanup |
| Runtime regression | All-fixture validation/preparation inventory; focused real pinned backend twice; existing numeric/timing checks; baseline/candidate decoded pixel comparisons |

Exercise both console and module entry points, and direct state-writing APIs, without editable installs. Preserve the complete existing host suite and its named real-backend exclusions. Package CI adds portable host checks and negative cases to the current wheel job and labels Blender scope unexecuted; local independent reviewer checks provide reference-platform real-backend evidence. Record candidate commit, wheel SHA-256, runtime manifest, interpreter and backend identities, commands, scopes, filesystem audits and actual CI run link. No new dependencies or actions are required by this design.

### 6. Acceptance pack and human visual gate

Capture or identify a verified unchanged pre-change baseline using installed HML with an explicit workspace. The developer records its exact release/commit, wheel hash, prepared source identity and pinned backend. Never modify an accepted historical pack. Use `neutral`, `rest` and four-beat `arm-raise`, with the same canonical source and 60/120/180 BPM sampling; this is focused regression evidence rather than renewed complete anatomical acceptance.

The independent reviewer creates a fresh candidate build and a pack with internal `clean-a/` and `clean-b/` passes. Check repeatability and baseline correspondence using existing numerical bounds and exact decoded pixels on the pinned reference backend. The human-facing pack contains:

- Neutral/rest overview: rows `neutral` and `rest`, columns front/rear/side, same fixed framing; full-resolution links retain inspection views.
- Arm-raise static sheet: front and side rows, five columns at beats `0,1,2,3,4`.
- Arm-raise animation sheet at 120 BPM: front and side rows, all 13 samples from beat `0` to `4` at thirds, split into panels of at most seven columns with explicit beat labels.
- Paired front/side GIFs at 60, 120 and 180 BPM from the same keyed animation, with timing checked against `n = max(3, ceil((60/BPM)/0.2))` and at least two in-between frames per beat.
- Separate front/side onion-skin overlays at count beats `0,1,2,3,4`, with beat-color legends.
- Per-view/beat comparison panels with three labeled columns: baseline, external-workspace candidate, absolute decoded-pixel difference; include error summaries and links to originals.
- A link-audited HTML-only derivative of a protected external predecessor, with before/after evidence hashes and an explicit statement that its original numeric verdict is not extended.

The human checks unchanged silhouette, stature, camera/floor framing, count alignment, arm movement readability, contact appearance and presentation. The reviewer maps scenarios to evidence in `review.md`; Gate 2 remains pending until human approval even though no visible change is intended. Full-fixture source/preparation coverage and focused real-backend coverage are reported separately.

## Risks / Trade-offs

- [Callers relied on implicit cwd or cwd-relative operands] -> Mark the interface break in active usage documentation, update every maintained caller and test, and reject omissions with an actionable workspace example.
- [A wrapper forgets to propagate context] -> Cover console, module, direct APIs, verification shard writers, render reuse and HTML-only modes with two-cwd tests and output audits.
- [Symlink containment checks allow external writes] -> Validate resolved workspace/build/run/content ownership before any mutation; add sentinel-based escape and alias tests while preserving intentional external read inputs.
- [Changing scratch environment changes output or leaks state] -> Scope overrides to child environments, retain reference backend pins, run focused deterministic render comparisons and inspect temp/cache/config locations.
- [Portability tests accidentally read the neighboring checkout] -> Use an external owning check run, unset source/import hints, add conflicting resource trees and audit actual import/resource origins.
- [External predecessor links are mistaken for a standalone evidence pack] -> Preserve existing local-visual/retained-evidence semantics, audit every required link and keep dependent predecessors protected until a verified replacement closure exists.

## Migration Plan

1. After Gate 1, capture the unchanged focused baseline and inventory existing resource/evidence identities; keep protected history untouched.
2. Introduce the required workspace/path context, migrate all workflow writers and backend scratch/ownership propagation, and update direct callers/tests/docs/CI together. Source contributors pass their absolute checkout explicitly when it is their chosen workspace.
3. Run the complete host scope and isolated wheel checks, then independent reference-backend comparisons and the human pack. Present actual CI/backend scope and unresolved findings honestly.
4. Record output cleanup and retained dependencies in existing developer/reviewer hand-offs. Keep the exact checked wheel, final pack and baseline comparison closure until the human gate; remove unneeded environments, caches and superseded owned attempts after dependency checks.
5. No stored source/prepared format conversion is needed. Previous prepared files with a different active implementation/manifest identity require regeneration under existing checks; location changes alone do not invalidate same-wheel prepared content. Do not rewrite old receipts, provenance or accepted packs.

Rollback uses the previous recorded wheel and its matching prepared inputs in a fresh run. Retain the explicit workspace in pipeline calls; absolute operands retain their meaning in the previous interface. Relative operands must be expanded to absolute paths before using the previous wheel because its cwd-relative semantics differ. Do not reuse failed candidate run roots or weaken integrity checks to make rollback outputs pass.
