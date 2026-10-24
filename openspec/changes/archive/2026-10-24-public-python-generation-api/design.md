# Design

## Context

See `proposal.md` for motivation. The installed package already provides the required backend and data closure:

- `prepare_skeleton.prepare(profile_id, stature, fixtures, bpms)` validates and solves packaged diagnostic sources, returning a sealed `skeleton-prepared/v1` dictionary. Its CLI owns path validation and persistence.
- `run_blender.run(...)` reads/revalidates that input, probes the pinned external Blender, uses `runtime.invocation`, validates expected outputs and returns a receipt. Images are listed separately in `render-manifest.json`.
- `sampling.py` provides exact rational static/animation plans. Prepared samples are the union of beat positions needed by requested BPMs. Their legacy `seconds` field is fixed to the 120-BPM primary timeline; it is not a general playback timestamp.
- `review_pack.py` already checks the complete expected sample/view inventory, file placement, readability and receipt hashes. This validation must be shared where appropriate, rather than weakened for the public result.
- `cli.py` dispatches operation parsers through `sys.argv`. `humanmotionlib.__init__` intentionally imports no host-only libraries because Blender also imports the package.
- Packaged sources currently describe anatomical skeleton diagnostics, not the future general pose/segment/motion library.

Relevant existing contracts remain `python-distribution`, `backend-execution`, `build-artifact-lifecycle`, `anatomical-skeleton` and `joint-mobility`. No rotation, unit, file-format, source-data, camera or backend-pin migration is proposed.

## Goals / Non-Goals

**Goals:** A Python consumer can import two functions, prepare supported data, invoke rendering, inspect ordered frame records and attribution, and catch failures without reading internal JSON. The CLI uses that same orchestration.

**Non-Goals:** A new diagnostic evaluator, new source authoring format, new anatomy or exercise targets, a service/job manager, configuration files, arbitrary render settings, package-index publication, or public APIs for every verifier/review-pack mode.

## Decisions

### 1. Two synchronous functions, explicit destinations

Add `humanmotionlib.api` as the supported import surface. Do not eagerly re-export it from the package root, preserving the lightweight embedded-Python import contract. Standard-library dataclasses, `Path` and `Fraction` suffice; add no dependency.

The public signatures are:

```python
prepare(
    *, workspace: str | Path, output: str | Path,
    profile: str = "adult-reference-v1", stature: float | None = None,
    fixtures: Sequence[str] | None = None,
    bpms: Sequence[int | float] = (60, 120, 180),
) -> PreparedResult

render(
    prepared: PreparedResult | str | Path,
    *, workspace: str | Path, output: str | Path,
    images: bool = True, render_dir: str | Path | None = None,
    render_only: bool = False,
    timeout_seconds: float = DEFAULT_BUILD_TIMEOUT,
    slot_timeout_seconds: float = DEFAULT_SLOT_TIMEOUT,
) -> GenerationResult
```

`output` for preparation is a JSON file directly inside a valid fresh run; its filename remains caller-selected to preserve the current CLI. `output` for rendering is a valid fresh run root. Relative paths, including `render_dir`, resolve against the explicit workspace. When images are enabled and `render_dir` is omitted, use `<output>/frames`. An explicit render directory must remain inside output. `images=False` disables images and rejects a supplied `render_dir`; `render_only=True` independently disables evaluated/geometry output, preserving the existing CLI combination even without images. The default public render produces measurements and images in one supervised construction; no automatic verification or second clean render is implied.

Keep current timeout constants, PATH-based Blender selection and version/build checks. Do not add executable overrides, a backend selector, downloads or arbitrary Blender arguments.

Preparation validates nonempty unique fixture/BPM selections; `None` fixtures means all. Preserve requested BPM order and normalize equivalent numeric BPM values for duplicate detection. Reject booleans, nonfinite or nonpositive numeric parameters before any filesystem state. Profile defaults and omitted stature preserve current behavior; arbitrary fixture input paths and dictionaries are unsupported.

An alternative single `generate` convenience call would obscure the reusable preparation boundary. It is unnecessary for the requested two-stage workflow. A raw-dictionary public return would expose internal formats and leave consumers assembling the same joins as today.

### 2. Result contract and exact joins

Export the following frozen top-level dataclasses from `humanmotionlib.api`; nested mappings are detached deep copies. Export the nested record types too so annotations are importable. Each type has `to_dict()` returning only JSON-compatible values. These are Python result projections, not a new canonical disk format.

| Type | Public fields |
|---|---|
| `PreparedResult` | `workspace: Path`, `run_root: Path`, `prepared_path: Path`, `prepared_sha256: str`, `profile_id: str`, `stature_m: float`, `package_identity: Mapping`, `poses: tuple[PoseSample, ...]`, `timelines: tuple[Timeline, ...]`, `provenance: ProvenanceInfo`, `units: Mapping`, `limitations: tuple[str, ...]` |
| `PoseSample` | `sample_id: str`, `fixture_id: str`, `beat: Fraction`, `actions: Mapping`, `fk_deltas: Mapping`, `world_root: Mapping`, `controls: tuple[str, ...]`, `rest_policy: Mapping`, `contacts: tuple[Mapping, ...]` |
| `Timeline` | `fixture_id: str`, `bpm: int | float`, `mode: str` (`static` or `animation`), `entries: tuple[TimelineEntry, ...]` |
| `TimelineEntry` | `sample_id: str`, `frame_index: int`, `beat: Fraction`, `seconds: Fraction` |
| `RenderedImage` | `sample_id: str`, `view: str`, `path: Path` |
| `ProvenanceInfo` | `sources: tuple[SourceProvenance, ...]`, `material_ids: tuple[str, ...]`, `register_text: str`, `licenses: Mapping[str, str]` |
| `SourceProvenance` | `logical_path: str`, `sha256: str`, `license: str | None`, `provenance: Mapping | None`, `nested_provenance: Mapping[str, Mapping]` |
| `GenerationResult` | `prepared: PreparedResult`, `output_root: Path`, `images: tuple[RenderedImage, ...]`, `artifacts: Mapping[str, Path]`, `receipt_path: Path`, `backend_identity: Mapping`, `numerical_acceptance: str`, `visual_acceptance: str` |

`actions` contains the solved sample's `expected_actions` in the existing anatomical degrees convention. FK deltas, world root and contacts preserve existing data/conventions; results do not invent VRM pose coverage for internal anatomical helpers. Source records include every resource in prepared `source_hashes`; resources without source-level license/provenance retain explicit `None`. Preserve full child-object provenance in `nested_provenance`, keyed by the existing object's JSON-pointer path within its logical source; this locates records without inventing source IDs. Collect material IDs recursively from all their provenance records, not just the diagnostic's often-empty root `sources` list. Include the full packaged used-materials register and project/third-party license and notice text in `ProvenanceInfo`; this keeps attribution usable without new generated sidecars or fragile resource-path lifetimes.

`poses` follow canonical prepared sample-ID order. `timelines` follow fixture-ID order, requested BPM order, then static before animation; entries follow increasing time. Images follow pose order then lexicographically sorted view ID. A timeline entry and image record join through `sample_id`; image files are reused for the same beat-relative pose across BPMs and modes. Public seconds always come from that timeline's sampling plan, never from the legacy sample timestamp. `frame_index` is the playback plan index, not the union-sample PNG filename number.

The `GenerationResult.artifacts` keys are `prepared`, `scene`, `metadata`, plus `evaluated`/`geometry` when measured and `render_manifest` when images are enabled. Do not fabricate paths for unproduced artifacts. `receipt_path` points to the completed supervised invocation's `outcome.json`. `numerical_acceptance` is `not-run` and `visual_acceptance` is `pending`; generation success alone does not establish either gate.

`to_dict()` recursively converts paths to absolute strings, fractions to `{numerator, denominator}`, tuples to arrays and records to mappings; preserve finite numeric values and source keys. Mutating nested result metadata or its projection cannot alter prepared-file bytes or subsequent requests. `render(PreparedResult)` reads `prepared_path` again, verifies its hash equals `prepared_sha256`, then applies normal installed source/implementation integrity validation. A path argument undergoes the same validation and reconstructs its preparation context without a prior in-memory object. In that reconstructed context, `workspace` is the explicitly selected render workspace and `run_root` is the prepared file's actual parent directory; neither field infers a checkout or authorizes writes to external input directories.

Usage documentation will include the complete minimal example:

```python
from pathlib import Path
from humanmotionlib.api import prepare, render

workspace = Path("/absolute/caller/workspace")
prepared = prepare(
    workspace=workspace,
    output="build/library-use_r1_app_try-1_prepare/input.json",
    fixtures=("neutral", "arm-raise"), bpms=(90,),
)
result = render(
    prepared, workspace=workspace,
    output="build/library-use_r1_app_try-1_render",
)
front = {image.sample_id: image.path for image in result.images
         if image.view == "front"}
timeline = next(item for item in result.prepared.timelines
                if item.fixture_id == "arm-raise" and item.mode == "animation")
frames = [(entry.seconds, front[entry.sample_id]) for entry in timeline.entries]
serializable = result.to_dict()
```

### 3. Reuse services, keep parsing at the edge

Move the preparation CLI's path-validation/persistence orchestration into the API service and retain `prepare_skeleton.prepare` as its internal evaluator. Delegate render orchestration to `run_blender.run`; share strict manifest/view/path checks with review code through a host-only helper rather than importing the full review renderer into the API or duplicating its checks.

`prepare-skeleton` parses existing arguments and calls public `prepare`. `run-blender` calls public `render`, mapping omission of `--render-dir` to `images=False` and preserving `--render-only` behavior. Refactor these parser entry points to accept an explicit argument list so generation APIs never consume or mutate application `sys.argv`. Preserve CLI progress/result presentation and exit semantics. Other command modes need no public wrappers or behavior changes. The existing internal `--owner-run` path is a tool-owned review-pass facility; preserve its internal call path, do not expose ownership bypasses in the public API.

Independent API preparation and render examples use disjoint direct-child runs. Preserve the existing backend exception for a designated run containing only its own prepared input when the CLI intentionally prepares and constructs in the same run; that is one managed run, not overlapping independent runs. No new provenance sidecars are added, so the current freshness allowance need not expand. All invalid destination checks precede state allocation, probing or copying. An empty, already-created valid run remains acceptable where the existing contract accepts it; an occupied or symlink-escaping run fails.

### 4. Errors are data-bearing exceptions

Export `GenerationError(RuntimeError)` with `code: str`, `operation: str`, `run_root: Path | None`, `receipt_path: Path | None` and `details: Mapping`. Stable codes are `invalid-request`, `source-validation`, `input-integrity`, `io-error`, `backend-unavailable`, `backend-mismatch`, `backend-contention`, `backend-timeout`, `backend-spawn`, `backend-failed`, `output-integrity` and `cleanup-pending`. Use the originating structured supervisor outcome for backend classification; do not infer failure causes by matching human error strings. Add structured classification at the existing supervisor boundary only where current errors lack it, retaining its semantics and receipt evidence.

Translate expected parameter, validation, integrity, filesystem and invocation exceptions with `raise ... from error`. Preserve the original backend outcome in `details` when cleanup is pending. Unexpected programming errors propagate with their traceback rather than being mislabeled input problems. `KeyboardInterrupt` passes through after existing supervisor cleanup; do not convert interpreter cancellation into a successful or incomplete result. No automatic retry, global recovery, environment dump or GUI fallback is introduced.

### 5. Installed acceptance and human visual pack

Host coverage exercises all packaged fixtures, default and custom BPMs, both input forms, result projections/mutation isolation, error categories and API/CLI parity. Wheel acceptance runs non-editably on supported CPython 3.14 outside the checkout with `PYTHONPATH` unset, misleading neighboring resources and read-only installation/invocation directories. It verifies package/resource identity and all writes under the explicit workspace. No unsupported host or backend is substituted.

Before implementation, retain a baseline generated through the current CLI at reference stature H=1.70 m for `neutral`, `rest` and `arm-raise`, BPMs 60/120/180. Candidate reviewer runs independently prepare and construct through the public API, repeat the API generation from clean state, and construct equivalent inputs through the candidate CLI. Use the unchanged pinned Blender/reference platform and fixed scene. Compare prepared content after excluding implementation/package identity that legitimately changes; compare pose/action/contact/timing content exactly, evaluated geometry within existing tolerances and decoded pixels exactly. Do not compare `.blend` binary ordering or incidental metadata timestamps.

The reviewer pack must include:

- Neutral/rest full-resolution front, rear and side views in a three-column sheet; rows identify neutral/rest and baseline/API/CLI. Keep existing extra fixed thorax views linked for inspection without changing their cameras.
- Arm-raise front and side count sheets at beats 0, 1, 2, 3, 4. Columns are these five beats; rows are baseline, API and CLI for each view. Labels show fixture, source path, beat, exact seconds and BPM.
- Animation sheets for every delivered arm-raise sample at 60/120/180 BPM, including the 21/13/13 frame inventories. Mark count boundaries and display front/side in separate labeled rows; wrap only between rows of a fixed ten-column grid.
- Paired front/side GIFs per BPM using the existing encoder and terminal-loop convention, with exact PNG timing records alongside the bounded GIF quantization report.
- Front/side onion-skin overlays of beats 0, 1/3, 2/3, 1, 4/3, 5/3, 2, 7/3, 8/3, 3, 10/3, 11/3, 4 from the 120-BPM plan; retain floor/contact markers and fixed framing.
- Baseline/API, repeat-API and API/CLI decoded-pixel difference summaries, geometry/timing comparison and a machine-readable export of the public result for the same pack. Public result image paths must resolve to the reviewed images.

Human gate 2 asks whether pose labels/time links match the visible pose, raising/lowering direction is readable, feet and framing remain stable, and API/CLI images match baseline. Full-fixture host coverage is not a renewed complete anatomical/mobility visual verdict. Failed numerical or integrity checks remain failures regardless of visual similarity.

### 6. Evidence ownership and cleanup

Every independent build/check/review run is a fresh direct child of the selected workspace's `build/` using `<change>_<revision>_<role>_<attempt>_<kind>`. Planned first-attempt roots are listed in tasks; retries replace `try-1` with a new attempt, never nest a run. Tool content such as `frames/`, `assets/`, `environment/` and managed clean passes remains inside its owning run. Baseline inputs are read-only and independent outputs are disjoint after resolving symlinks.

The developer hand-off and reviewer `review.md` inventory run roots, bytes, links and input/evidence dependencies before cleanup. Remove obsolete owned whole runs after checking inbound dependencies, never follow symlinks outside `build/` and never remove another agent's active run. Retain the baseline while comparisons depend on it, final wheel/check evidence while identifying the candidate artifact, and reviewer runs referenced by the pending human gate or final review. Each retained root names its dependency or unresolved diagnostic and reconsideration event. Record removals/bytes, retained reasons, before/after dependency checks and pending cleanup. Failed or interrupted cleanup remains pending until resolved.

## Risks / Trade-offs

- [A stable API can accidentally expose internal format assumptions] → Only the documented result projection is public; canonical input dictionaries remain private and revalidated on render.
- [Union sample timestamps could misstate non-120 BPM playback] → Join exact sampling plans by sample ID; test a non-default BPM explicitly.
- [Returning nested provenance may be large] → Return detached metadata and packaged text without loading images or duplicating image files; no new storage format or dependency.
- [CLI compatibility could be lost in a facade refactor] → Preserve option/default/failure parity, including construction-only and designated shared-run behavior, with normalized artifact comparisons.
- [Host tests can hide real backend failure] → Retain separate host and pinned-backend verdicts; require independent clean renders and human visual approval.

## Migration Plan

This is an additive public import surface. Existing command names/options, internal module imports, canonical sources and disk formats remain available. Document that `humanmotionlib.api` is the supported generation interface and identify the current diagnostic-only scope. Include new modules/docs in the existing distribution manifest and test the built wheel; no package publication is authorized. Rollback removes the facade and restores CLI delegation without modifying source assets or accepted history. Package release/version policy remains unchanged by this proposal.

## Decisions for Human Gate 1

Approve the two synchronous calls and result/error contract; the existing diagnostic-only coverage; explicit workspace/fresh-run ownership; default profile/reference stature/all fixtures and BPMs 60/120/180; external pinned Blender supervision; CLI compatibility; and the focused independent visual gate. There are no unresolved questions requiring a scope decision.
