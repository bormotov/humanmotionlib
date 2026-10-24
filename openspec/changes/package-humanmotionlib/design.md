# Design

## Context

See `proposal.md` for motivation. Observed repository state:

- `pyproject.toml` declares `humanmotionlib==0.1.0`, CPython `>=3.14,<3.15`, PyYAML, jsonschema and Pillow, but `[tool.uv] package = false`; no build backend or installed entry points exist. `referencing` is imported directly but currently arrives transitively through jsonschema.
- Runtime code is under `tools/`; executable modules insert the checkout into `sys.path`. `runtime.project_root()` conflates resource location, output workspace, backend cwd and slot ownership. `run_blender.py` passes relative `tools/build_skeleton.py` to Blender.
- Validation hashes canonical sources plus schemas, the material register, `pyproject.toml` and `uv.lock`. Prepared readers require those files under the inferred root. Backend implementation hashing scans `tools/*.py`.
- The skeleton is procedural: the profile describes anatomy and generated mesh primitives. No stored `.blend`, external anatomical mesh, MPFB or Rigify installation is part of supported generation.
- Review packs read the material register, third-party notices and `docs/anatomical-skeleton-acceptance.md`; HTML-only derivatives retain some predecessor evidence links. These are runtime dependencies, not optional contributor documentation.
- `.github/workflows/host-python.yml` already runs Linux CPython 3.14 host checks with uv 0.13.5, excluding the two named real-Blender modules. Full backend acceptance is separate on Darwin arm64, Blender `5.2.2 LTS` build `d13f752e3b9c`.

## Goals / Non-Goals

**Goals:** one installable implementation; byte-preserved canonical runtime data; explicit writable workspace; comparable source and installed execution; distribution archives that can be checked independently.

**Non-Goals:** broad Python/platform support, bundling Blender or Python dependencies inside the HML wheel, runtime downloading, adding pose/segment/motion formats or exports, changing anatomy/timing, publishing a release. `py3-none-any` describes the pure-Python wheel payload, not a promise that the POSIX supervisor or reference Blender works on every OS.

## Decisions

### 1. Source layout, version and build boundary

Move implementation modules to `src/humanmotionlib/`, preserving module names so the migration is mechanically `tools.<module>` to `humanmotionlib.<module>`. Use a regular package, with a minimal dependency-free initializer and no `bpy` import until Blender-specific execution. Install no `tools` alias or compatibility shim. Existing Python callable behavior remains covered by migrated tests; no new long-term stability promise for internal helpers is introduced.

Set the release version once in `[project].version` to `0.2.0`; generate packaged version information during build so `humanmotionlib.__version__` works in Blender without requiring host distribution metadata. Installed host inspection cross-checks it with distribution metadata. Do not derive a release version from Git at runtime.

Use an in-tree PEP 517 staging adapter, `hml_build_backend`, delegating distribution construction to `setuptools.build_meta` from `setuptools==83.0.0`, pinned in build requirements and the contributor build dependency group. The human approved replacing the initially proposed `80.9.0` during implementation planning because `83.0.0` fixes GHSA-h35f-9h28-mq5c (CVE-2026-59890), concerning Unicode normalization in sdist exclusion matching. Verify the exact whole-archive allowlist as well as runtime resource closure. The developer must verify that exact version's Python 3.14 build behavior and commercial/derivative license before use; incompatibility goes back to the architect. Keep build-only dependencies out of runtime `Requires-Dist`; run builds with the repository's pinned uv. Remove virtual-project mode and refresh the lock so locked contributor setup installs HML. Record the upstream advisory and release-history references with their clearance evidence in `docs/used-materials.md`.

Retain the existing runtime dependency bounds for PyYAML, jsonschema and Pillow. Add `referencing>=0.37,<1` as a direct runtime requirement, reflecting the directly imported API and the current lock's `0.37.0`. Keep CPython `>=3.14,<3.15`. Record every new dependency/change rationale and resolved version. A narrow build adapter must stage resource copies and generated metadata during both direct wheel builds and sdist rebuilds, inside the caller's build run; it must not mutate canonical sources or the source package.

Alternative considered: ship `tools` as the package or leave checkout wrappers as the real implementation. Both retain namespace collisions or checkout coupling. Duplicating source data under `src/` would create two canonical copies; build-time staging preserves one source of truth.

### 2. Explicit runtime resource inventory

Keep canonical authoring paths in the repository and copy them byte-for-byte to `humanmotionlib/resources/` at build time. Preserve their logical relative names in the resource namespace:

| Packaged logical resources | Purpose |
|---|---|
| `rig/profiles/*.yaml` (currently `adult-reference-v1.yaml`) | Procedural anatomical skeleton model and mass metadata |
| `rig/mobility/*.yaml` | Action ranges and closed coupling parameters |
| `rig/body-groups.yaml`, `rig/humanoid-map.yaml` | Controls ownership and humanoid adapter |
| Every `rig/diagnostics/*.yaml` (currently 32) | Full supported diagnostic inventory, including sweeps |
| Every `schema/*.schema.json` (currently 7) | Offline registry and transitive local references |
| `scenes/skeleton-review.yaml` | Fixed full-body and inspection cameras, floor, light and display |
| `docs/used-materials.md` | Provenance resolution and commercial-use register |
| `docs/anatomical-skeleton-acceptance.md` | Acceptance map copied into generated packs |
| `docs/usage.md` (new) | Installed setup, command/option reference and migration guide |
| `LICENSE-CODE`, `LICENSE-DATA`, `THIRD-PARTY-NOTICES.md` | Distinct project licenses and third-party attribution |
| Generated `backend-contract.json` | Exact existing backend pins and not-used MPFB/Rigify declarations |
| Generated `runtime-manifest.json` | Release, resource inventory and implementation hashes |

All migrated Python modules, including the Blender entry script and its import closure, are package code and must be included. Use an explicit resource allowlist with deterministic recursive expansion, not a copy of the repository. A closure check must discover any additional actual file reads during migrated generation and fail if they lack a declared packaged resource. There are currently no runtime templates, fonts, images, binary skeletons or external meshes to copy. Tests, `.github`, OpenSpec history, developer agent/skill files, diagnostic triage docs, `build/`, `dist/`, caches and environments are not runtime resources. Canonical root `pyproject.toml`, `.python-version` and `uv.lock` belong to development/sdist context, not installed resource lookup.

Use `importlib.resources` through one resource-access boundary. Schema IDs remain unchanged and never trigger web access. Ordinary wheel installations expose files for Blender; acquire resource filesystem paths for the complete subprocess lifetime and use absolute script paths. Zipped Python imports are not a supported launch mode. The sdist includes package source, the resource closure, license files, build adapter/configuration and contributor lock/version selector; rebuilding it must not need `.git` or the original checkout.

### 3. Commands and migration map

Provide the `hml` console command and `python -m humanmotionlib` with the same dispatcher. The distribution and Python import namespace remain `humanmotionlib`; `hml` is the console entry-point name. Global `--workspace PATH` precedes the subcommand; default is the resolved invocation cwd. Document options centrally in `docs/usage.md`, included in both distributions and readable from the installed resource inventory, and update `tools/README.md` as a contributor link/migration index.

| Former command | Installed command |
|---|---|
| `python tools/validate.py ...` | `hml validate ...` |
| `python tools/prepare_skeleton.py ...` | `hml prepare-skeleton ...` |
| `python tools/run_blender.py ...` | `hml run-blender ...` |
| `python tools/verify_skeleton.py ...` | `hml verify-skeleton ...` |
| `python tools/review_pack.py ...` | `hml review-pack ...` |
| `python tools/check_host.py --check-environment` | `hml check-environment` |
| `tools.<module>` imports | `humanmotionlib.<module>` |

Keep existing operation options from the original parsers, including `--fixtures`, stature, timeout/slot timeout, render-only, verification audits, render reuse and HTML-only regeneration. The raw Blender script is an internal backend entry point, not a second unsupervised normal command. Source contributor test discovery remains a development command, documented separately with an explicit repository tests root; the wheel does not carry tests or silently discover arbitrary cwd tests. The installed environment command checks actual CPython, distribution requirements and imports without reading contributor files.

`--reuse-renders` resumes assembly within the same caller-owned, unprotected pack run; it does not allocate or retry an independent generation attempt. Before any writes, validate both completed clean passes, their manifests/receipts, prepared/package identities, retained reference input and expected managed contents. Reject missing, failed, stale or unrelated contents without mutation. Reuse launches no backend process and preserves existing input, render and receipt bytes. Normal generation and HTML-only derivatives continue to require fresh output roots. Verify successful no-spawn resume, normal occupied-root rejection and no-write rejection of missing, failed, mismatched or unrelated contents.

Preserve the existing CLI contract: `hml review-pack --reuse-renders --input <build-run> --output <existing-pack-run>`. Input and output remain distinct and disjoint; the selected build's `input.json` must match the retained inputs in both clean passes, their evidence and any retained reference input. Same-run continuation identifies the existing output pack attempt; it does not change `--input` to select that pack.

### 4. Workspace and backend isolation

Introduce a caller-passed execution context containing the resolved workspace; propagate it through launch, review-pack clean passes, runtime supervision, tests and path ownership checks. Avoid process-global `chdir`, hidden checkout discovery and deriving workspace from the input file. Resolve relative CLI paths from invocation cwd; `--workspace` selects allowed `build/` ownership and backend cwd, not an implicit reinterpretation of all arguments. Documentation uses absolute workspace paths where necessary.

The workspace's `build/` holds the persistent existing lock/state names, and all new independent runs remain direct children with five-part names. Resolve workspace symlinks before locking so two installations selecting the same workspace serialize correctly. Different workspaces are separate execution domains; no machine-global backend lock is promised. Repository commands defaulting to the checkout retain the existing slot location. Keep stale-owner recovery, cancellation bounds, receipts and fail-closed completion unchanged.

Pass an absolute packaged script path and the workspace explicitly to Blender. Bootstrap only the installed `humanmotionlib` package through an explicit importlib package specification, with submodule search locations restricted to that package directory. Do not add its containing directory, host site-packages or the checkout to `sys.path`; preserve package resource discovery and reject conflicting package origins. Do not export host `PYTHONPATH` or use `--python-use-system-env`. Verify that a neighboring host-only module is unavailable to Blender while packaged HML imports and resources resolve. Keep the Blender-imported HML closure standard-library-only apart from `bpy`, `mathutils` and `gpu` supplied by Blender. Generate backend/version data accessible to that closure without importing host-only dependencies. Blender's embedded Python is verified separately and is not constrained to 3.14.

HML does not create caches in the installed tree. Test immutable installs with bytecode writes disabled; the Blender bootstrap suppresses bytecode writes before importing its HML closure. Any HML-managed materialization belongs to its owning run. Read-only site-packages must work. Missing/mismatched Blender is an explicit controlled failure, never an automatic download or renderer change.

### 5. Resource identity, prepared inputs and compatibility

Generate a deterministic `runtime-manifest.json` with a format identifier, release version, original logical resource names and SHA-256 values, canonical backend contract identity, and relative packaged `.py` implementation hashes. Exclude the manifest's own digest from its entries to avoid recursion. Record its hash separately in prepared/output identity. No absolute path, timestamp or checkout-specific identity enters canonical resource identity. Validate the manifest against actual package bytes before host preparation/backend launch and independently in the embedded loader.

Preserve `skeleton-prepared/v1`, its canonical finite JSON serialization and content hash algorithm. `source_hashes` in new prepared inputs resolves logical resource keys through the package inventory, including backend contract and manifest identity, instead of filesystem-relative checkout lookup. Add explicit release/manifest/implementation identity fields as finite additive payload metadata; readers verify them and all source hashes. Remove runtime reliance on `pyproject.toml`/`uv.lock` hashes; the development lock is still checked in contributor CI. Runtime manifests are generated packaging metadata, not a new skeletal source format or convention.

An input from another release/resource inventory, including an old checkout-bound prepared file, must fail clearly and request regeneration; do not disable source checks to accept it. Existing protected outputs are not rewritten. HTML-only derivation remains the intentional exception: it validates retained predecessor evidence/media according to its current mode, without asking the active package inventory to equal the old pack's generation inventory. It records the current presentation generator identity plus the predecessor hashes.

Implementation hashes now cover `humanmotionlib/*.py`, including backend and package bootstrap, using logical package paths. Absolute executable/workspace paths stay in invocation receipts only. Compare baseline and new outputs by geometry, transforms, sample timing and decoded pixels, not entire metadata files whose package identity intentionally changes.

### 6. Distribution metadata, clearance and CI

Preserve separate Apache-2.0 and CC-BY-4.0 declarations and include both full files plus notices/register as installed resources and standard distribution license files. Metadata must describe mixed code/data licensing honestly; it must not imply third-party material is relicensed. The developer verifies commercial use, derivatives and intended redistribution against exact source/tool/action licenses before actual use, then records all used sources, including references and no-attribution materials, in `docs/used-materials.md`. Reuse existing cleared anatomical portions; do not fetch or redistribute their books, articles, figures or datasets.

Extend CI with a package job on push/PR, on the existing Ubuntu/CPython 3.14 host scope, using pinned actions and uv. It builds a direct wheel and sdist into a fresh flat run, rebuilds a wheel from the extracted sdist in another fresh run, compares logical payloads, and installs the exact direct wheel into a fresh environment. Installed smoke subprocesses run from a separate cwd with `PYTHONPATH` unset and no checkout source path. Record import origins, metadata, wheel hash and resource hashes; validate all sources, prepare all fixtures, run selected numeric host checks, exercise CLI errors and HTML-only mode with a synthetic valid predecessor. Verify dependency consistency and archive contents. Keep normal locked host tests as a separate required scope; do not replace them with smoke tests.

Upload the checked wheel and small verification evidence with commit/run identity and 90-day retention, including diagnostic logs on failure. Do not upload environments or caches, publish to PyPI, or install a different Blender in CI. Local reviewer evidence supplies real backend acceptance; CI explicitly labels the missing scope. Record one actual successful GitHub Actions run before marking the CI task complete; if unavailable, leave that acceptance item pending.

### 7. Acceptance pack and human visual gate

Before migration, the developer captures a source baseline on the pinned reference platform in `build/package-humanmotionlib_r1_dev_try-1_baseline/`, with commit, source/code hashes, commands and backend receipts. Use unchanged canonical sources, `neutral`, `rest` and the four-beat `arm-raise` fixture, primary 120 BPM and existing preview timing at 60/120/180 BPM. Store only the focused baseline/evidence needed for comparison, retaining it until the reviewer pack has a self-contained verified comparison closure. No older accepted pack is modified.

The reviewer builds the wheel independently and runs installed generation without checkout imports. Use `build/package-humanmotionlib_r1_reviewer_try-1_build/` for evaluated generation and `build/package-humanmotionlib_r1_reviewer_try-1_pack/` for the render/review pack. Its internal `clean-a/` and `clean-b/` are the tool-required passes of this one pack, not new independently managed runs. Both clean passes must agree exactly in decoded pixels; compare candidate to the baseline with unchanged applicable geometry/transform limits and exact decoded pixels on the same pinned backend. Audit every count and animation time, contact checks, locked cameras/floor/light and static/animation sample agreement.

Required human-facing layout:

- Neutral/rest overview: rows are `neutral` and `rest`; columns are front, rear and side, at the fixed full-body framing. Provide the existing thorax inspection views as linked full-resolution detail if rendered.
- Arm-raise static sheet: two rows (front, side), five columns at beats `0,1,2,3,4`. Preserve a full-resolution link for each count.
- Animation sheet: front row and side row at primary 120 BPM, all 13 samples `0,1/3,2/3,1,...,4`, split into consecutive panels if needed with at most seven columns and explicit beat labels. This shows two in-betweens per beat; verify other BPM intervals against `max(3, ceil((60/BPM)/0.2))`.
- Paired front/side GIFs at 60, 120 and 180 BPM using the existing timing rules and the same keyed source; label BPM and count beats.
- Separate front/side onion-skin overlays at beats `0,1,2,3,4`, colored by beat and with a visible legend.
- Baseline/candidate comparison sheet for each view and beat, three labeled columns (baseline, installed package, absolute decoded-pixel difference), with per-frame error summaries and links to both originals. Identity-only metadata differences are listed separately.

The human checks stable framing/floor, unchanged skeletal silhouette and stature, arm movement readability, count alignment, contact appearance and the absence of visible changes against baseline. This is Gate 2 even though no visible change is intended, because scene/render execution paths change. Report full-fixture source validation/preparation independently from the focused real-backend comparison; do not claim full anatomical reacceptance. `review.md` must map scenarios to evidence and leave human approval pending until given.

### 8. Runs, evidence and cleanup

Use each direct-child run listed in `tasks.md`; every retry changes the attempt component. Independent input/output runs must be distinct and disjoint after symlink resolution. Test-created secondary workspaces are isolated fixtures beneath the owning check run, not independently managed attempts; their internal `build/` layouts exercise installed workspace semantics. Tool content such as environments, cache, sdist extraction and clean passes stays within its owning run. Never place new artifacts in the release `dist/` directory during this work.

At each hand-off, inventory owned runs and all pack/media/receipt/resource dependencies before removal. Keep the candidate wheel plus its hash and verification results as the exact reviewed artifact; keep the final pack and its source/evidence closure for Gate 2; retain the baseline until its necessary comparison content is copied and independently verified. Remove superseded runs, environments, caches and duplicate distribution stages once no dependent check remains. Existing review/hand-off records list removed paths/bytes, retained paths with concrete reasons, before/after dependency checks and pending cleanup. Failed diagnostic evidence needs a named finding and a reconsideration event. Never delete another agent's active run or follow a symlink outside the selected `build/`.

## Risks / Trade-offs

- [Staged data omitted from sdist] → compare wheel payloads from direct and sdist builds and run both inventory checks before acceptance.
- [Blender resolves host-only imports after namespace migration] → keep its closure explicit and test a real wheel install with host import-path injection disabled.
- [Old prepared files stop validating] → fail closed with regeneration guidance, retain accepted history and preserve HTML-only predecessor support.
- [Pure-Python wheel mistaken for cross-platform backend support] → document Linux host CI and unchanged POSIX/reference-platform boundaries separately.
- [Packaging changes metadata hashes] → compare stable logical resource hashes and actual pixels/measurements, separately recording intentional identity changes.
- [A build tool version fails Python 3.14 or source clearance] → stop that implementation step and return the exact incompatibility to the architect before selecting a replacement.

## Migration Plan

1. After Human gate 1, record the pre-migration baseline and dependency/source inventories.
2. Move code and update imports/tests/command documentation; add package resources, metadata and workspace context together so no intermediate release claims installation support.
3. Build and verify direct/sdist-derived artifacts; install non-editably and complete host and pinned backend checks, CI execution and independent review.
4. Obtain human visual approval before archive. Applying this change authorizes no upload to a package index.
5. Rollback before release is a source change reverting the package migration and its lock changes; do not rewrite protected build history. Users with incompatible prepared inputs regenerate with their selected version. No canonical data conversion is needed.

All material choices are recorded above; there are no open human questions. Defaults for approval are version `0.2.0`, deliberate namespace break, external pinned Blender, existing Python/platform support and CI artifacts without publishing.
