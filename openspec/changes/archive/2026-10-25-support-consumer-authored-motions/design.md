# Design

## Context

See `proposal.md` for motivation and the two delta specifications for observable behavior. The consumer confirmed that this change covers API capability and a verification example; depth belongs to the consumer, and no production exercise is requested.

Observed implementation constraints:

- `api.prepare` delegates to `prepare_skeleton.prepare`, whose source loader selects only installed resources and fixture identifiers. `docs/usage.md` and the public preparation requirement explicitly prohibit external motion sources today.
- There is no general pose/segment/motion schema or compositor. `schema/diagnostic.schema.json` defines action tracks, integer duration, rest policy, closed analytic constructors, contacts and provenance. `DiagnosticEvaluator` already evaluates that language independently of Blender.
- `validate_bundle` checks packaged records and ownership, but some evaluator prerequisites are not schema conditions, `hold` requires previous intent, and `free` needs external layers. Existing source validation alone does not establish solved movement/contact validity.
- `prepared.read_prepared` currently treats every `source_hashes` key as an installed resource. `api._provenance` rereads package bytes for every source. Consumer records cannot simply be inserted into that namespace.
- Render paths and public joins currently use `fixture`/`fixture_id`; consumers control no render settings. Identifier validation is therefore also a filesystem contract.
- Real-backend review exposed that consumer prepared reading imported host PyYAML/schema modules into Blender, whose embedded Python does not supply them. The human explicitly approved the Gate 1 amendment: validate the source in host Python before Blender, and validate prepared-snapshot integrity inside Blender. This approval replaces the original identical host/backend validation-path decision; it does not approve a compiled reference index or new dependency.

## Goals / Non-Goals

**Goals:** Reuse the supported kinematic language through a bounded public source adapter; preserve exact sampling and existing diagnostic behavior; carry a fully reproducible consumer snapshot and additive attribution into rendering.

**Non-Goals:** General sequence/repeat/parallel composition, parameter expressions, runtime callbacks, consumer profiles/rigs/scenes, a new clinical motion standard, an exercise recommendation, a canonical shallow squat, custom renderer settings, CLI import switches, or bake/export work. This initial source scope is documented explicitly rather than calling it the future general motion format.

## Decisions

### 1. Add one explicit source operand to the existing API

Extend `prepare` with optional keyword `motion: Mapping[str, Any] | str | Path | None = None`. `motion is None` takes the existing packaged-diagnostic path. A non-null motion and non-null `fixtures`, including an empty selection, are an `invalid-request`. The profile, stature, BPM, workspace and output parameters retain their meanings. One consumer movement is returned per call; packaged bases are dependencies, not extra delivered movements.

A path is a local `.yaml`, `.yml` or `.json` file. Relative paths resolve against the explicit workspace; absolute readable paths can refer to the consumer's external project. The path itself must not lie in the output run; when it belongs to a managed input run, that run and the output run must be disjoint after symlink resolution. HML never writes beside the source. Load bytes once, reject duplicate keys, YAML executable tags, recursive aliases, non-string object keys and non-JSON-compatible Python objects, then deep-copy the document. File and mapping forms use the same canonical semantic hash, so representation and formatting do not change motion identity. JSON/YAML parser failures are `source-validation`; missing/unreadable files are `io-error`; argument type/selection errors are `invalid-request`.

**Alternative considered:** separate preparation functions for variants and files. A single explicit operand keeps one pipeline and makes selection conflict observable. Batch mixed built-in/custom requests add no necessary capability to the confirmed example and are deferred.

### 2. Use a closed envelope around the existing action language

Introduce packaged `schema/consumer-motion.schema.json`, with closed nested objects and offline references to existing schemas. The public envelope is:

| Field | Contract |
|---|---|
| `format` | Exact string `hml-consumer-motion/v1`. |
| `motion` | Exactly one complete `skeleton-diagnostic/v1` document or the variant record below. |
| `materials` | Required array, possibly empty, of consumer clearance records. |

The complete definition has exactly the existing diagnostic source fields and constructor vocabulary. Reuse its schema rather than creating a competing joint representation. The `kind: skeleton-diagnostic` spelling denotes the scoped language; it does not grant diagnostic/library acceptance. Consumer IDs match `[a-z0-9]+(-[a-z0-9]+)*`, are distinct from every packaged fixture, and never contain path separators, dots, traversal or empty components. The complete source's `profile` must equal the selected packaged profile.

Initial consumer rest context is `policy: base`, with `base_fixture` naming a packaged fixture. Reject `hold` and `free` because no previous/layer context is part of this public request. `procedural.noise` and `follow_through` must remain false. Preserve integer durations and integer key/contact/constructor events; a complete definition cannot silently acquire a fractional timing convention. Circular intent needs explicit intermediate keyed action poses; shortest-path interpolation is not reinterpreted as a requested full circle.

Consumer durations are bounded to 0–256 beats and the exact union of delivered beats to 100000 pose samples. Count the rational sampling grids before allocation, stopping once the limit is exceeded; do not build an enormous timeline to determine that it is excessive. This caps the additional dense grid at 25601 points. The limits apply only to the new consumer branch, preserve existing BPM meaning, and are documented as input resource limits rather than anatomical limits. Duration/source overflow is `source-validation`; exceeding the sampling budget due to request BPMs is `invalid-request`.

The variant record is closed:

| Field | Contract |
|---|---|
| `schema_version`, `kind`, `format` | `1`, `skeleton-motion-variant`, `skeleton-motion-variant/v1`. |
| `id`, `description`, `profile`, `license`, `provenance` | Existing source metadata conventions; `license` and provenance license are `CC-BY-4.0`. |
| `base_fixture` | Existing packaged fixture ID in the selected profile; no consumer-chain/file/URL references. |
| `track_scales` | Required object mapping existing base track channels to finite numeric multipliers; may be empty. |
| `track_overrides` | Required array of complete track records in the existing track shape; may be empty. |

At least one scale or replacement is required. Deep-copy the packaged fixture, substitute the variant's ID/description/contribution provenance, scale the specified existing key **values** (not beats) about numeric zero, and replace specified existing tracks in their original positions. Unknown channels, repeated replacements and scale/replacement overlap fail. Scales can be zero or negative only if the resolved motion passes all operating checks; they have no implicit anatomical meaning. No field other than metadata and the selected tracks changes. In particular, constructor parameters, duration, root, contacts, controls and rest policy inherit unchanged. A consumer needing changes to those fields submits a complete definition.

Store the base's original document identity/provenance independently of the contribution. Variant `provenance` describes the contribution; it cannot overwrite or assert authorship of inherited content. Its inherited source/material closure remains explicit in lineage and public provenance. This allows an authored scaling contribution without pretending that the adapted squat's sources disappeared.

**Alternatives considered:** accept arbitrary dictionaries unchecked; introduce a generic motion compositor now; add a squat-specific public recipe; implement arbitrary JSON Patch. These either violate the validation boundary, exceed this change, imply exercise design, or expose hard-to-constrain inheritance semantics. Whole-track replacements and multipliers have simple, testable meanings.

### 3. Separate structural, semantic and solved checks

Use a host-only consumer adapter module to load/resolve documents and reuse packaged source validation without making a filesystem checkout or HML resource mutation. Feed the resolved movement plus its packaged base closure into the existing evaluator. Run these stages in host Python entirely before preparation output allocation; host rendering repeats the persisted-source validation and reconstruction before any Blender probe or launch:

1. Validate normal API parameters and output destination without creating directories.
2. Verify installed resources and source envelope, finite numerics, schema and clearance records.
3. Resolve variant/base lineage, profile, references, groups, writers, key ordering and contact intervals; validate the normalized effective source against the existing diagnostic schema.
4. Validate constructor-specific data and generated writers. `walking_flat` requires its complete existing parameter set and nonempty ordered, non-overlapping phases within duration; other constructors reject walking parameters/phases. `forefoot_rocker` requires ordered integer reference knots within its constructor interval; other constructors reject nonempty reference knots. Constructor intervals must satisfy `0 <= start <= end <= duration`; dynamic constructors require a nonempty interval. All dependent reads must resolve, and implicit writes must belong to `controls`.
5. Reject a track that the selected constructor overwrites: `squat_closed` owns `pelvis.y`, `pelvis.z`, bilateral `hip.{flexion,adduction,external_rotation}` and `hindfoot.inversion`; `walking_flat` owns bilateral elbow/forearm, hip, hindfoot, knee, ankle and shoulder-elevation/plane channels; `forefoot_rocker` owns pelvis y/z, ankles and MTP extension; `rest` owns bilateral shoulder elevation/plane. Such tracks are contradictory input, not a supported override. Keep required constructor controls at their existing conservative set; tightening consumer semantics does not rewrite packaged fixtures.
6. Evaluate at the union of delivered beats, explicit events, endpoints and `i/100` beats. Iterate dense samples without adding them to delivered output. Existing action/coupling guards remain authoritative. Check skeletal contact targets, witness/side consistency and sliding against `1e-3 H` using existing attachment measurements and per-interval history; reject contradictory overlapping declarations. Preserve requested values, targets and error details. Resolve L/R through existing conventions; no new mirror or rotation convention is introduced.
7. Sample/solve the requested movement with the unchanged BPM sampler and existing stature scaling, then seal and persist in the fresh output run.

Resolution occurs in the profile's reference-stature source units **before** meter-valued data is scaled. Validate the actual requested stature after scaling; angles and multipliers are dimensionless. Constructor-derived channels and changed tracks must pass the same ownership checks as directly supplied tracks. Rest-base cycles and unprovided contexts are rejected explicitly rather than relying on recursion failure.

Return `GenerationError('source-validation', 'prepare', ...)` with JSON-compatible `details` including `source_id`, `field`, and for solved failures `beat`, `state`, `channel` or `constraint`, requested/measured value and bounds/residual. No process receipt is invented. The preflight establishes kinematic/source feasibility, not independent evaluated-mesh/floor/balance or visual acceptance. Full geometry verification stays a separate review step; custom motions do not inherit the packaged squat's 90-degree dossier or its balance verdict merely by using the same constructor.

**Alternative considered:** validate only schema and delivered frames. Constructor prerequisites, coupled limits between frames and unsatisfied contacts make that insufficient for externally supplied intent.

### 4. Keep consumer provenance separate from package resource integrity

Consumer clearance records are structured input, not Markdown parsed from arbitrary files. Each record contains `id`, `material`, `part_used`, `source_url`, `license`, `license_url`, `permission_basis`, `permissions`, `conditions`, `attribution`, `checked_on` and `related_outputs`. Text fields are nonempty except attribution, which may be empty for a license requiring none; related outputs is a nonempty string array. `checked_on` is a valid ISO date. `permissions` is a closed object with `commercial_use`, `derivatives` and `cc_by_4_0_distribution` all explicitly true. `permission_basis` states the grounds for those declarations; conditions must state applicable obligations or explicitly state none. Source/license URLs must be absolute HTTP(S) URLs, and records cannot override packaged IDs.

The initial supported license IDs are `CC-BY-4.0`, `CC0-1.0`, `MIT` and `Apache-2.0`; unknown/custom, NC and ND terms fail rather than being inferred compatible. All used references, including CC0, require a record; records merely found are not included. New referenced materials can reuse a packaged register ID without resupplying it. Adapted contributions need nonempty source references; authored contributions may have no external sources. Reject unused supplied entries so the delivered register describes actual use. Preserve package register bytes and append a deterministic consumer section to the returned register content, alongside the structured source snapshot.

True permission flags alone are insufficient. Add a closed `obligations` object to every clearance record, checked against a pinned supported-license profile: `retain_attribution`, `retain_license_text`, `retain_change_notice`, `retain_copyright_notice`, and `retain_notice_if_present`. Require at least the applicable flags (CC-BY: attribution, license, change; MIT: copyright and license; Apache: license, copyright, change and notice-if-present; CC0 has no required flags). Additional declared obligations remain true and are retained. Require nonempty attribution for profiles requiring attribution/copyright, and conditions text plus full license URL for every record. The normalized result exposes these obligations so consumers cannot mistake permission for absence of conditions; this profile is a supported-input validation rule, not a complete legal analysis of a license.

This is offline validation of the caller's clearance declarations and attribution closure; HML does not browse licenses, prove ownership or certify legal truth at runtime. Dev/reviewer must independently clear any external material they actually use to build this change and record it in repo `docs/used-materials.md`, including CC0 and attribution-free sources. The planned examples derive only from already registered HML sources and authored test numbers, so no new external reference is required.

**Alternative considered:** require every consumer to edit HML's Markdown register or accept provenance strings unchecked. Neither supports installed immutable packages with auditable external attribution.

### 5. Add a self-contained sealed consumer snapshot

Keep `skeleton-prepared/v1` and its current package-only `source_hashes` semantics. Add optional sealed `consumer_motion` to consumer preparations only:

| Field | Meaning |
|---|---|
| `format` | `hml-consumer-motion-snapshot/v1`. |
| `document`, `source_sha256` | Canonical submitted envelope and its canonical-content SHA-256. |
| `resolved_definition`, `resolved_sha256` | Unscaled effective diagnostic definition and canonical hash. |
| `base_lineage` | Deterministic referenced packaged fixture records: ID, logical package resource key and raw-resource SHA-256, including required rest bases. |
| `validation` | Preflight scope, actual stature, dense step and successful kinematic/contact check summary; no evaluated or visual acceptance. |

The existing full prepared-content seal covers these fields, scaled effective source, poses and timelines. Host `read_prepared` checks schema/finite contents, source and resolution hashes, package/base identity, then re-resolves the submitted document and compares its effective source with the snapshot and scaled source. It reconstructs dense preflight, sample/timeline IDs and solved pose content before accepting consumer input for the backend. This host validation is mandatory both after preparation persistence and for each render request, including explicit prepared-file inputs and internal managed review passes. No original consumer file is reread.

#### Host validation and backend integrity boundary

Split the reader into a shared dependency-free integrity core and a host validation wrapper. Keep the existing host `read_prepared` behavior, including rejection of resealed inconsistent consumer payloads. Move its consumer source/schema/replay helper into a host-only module such as `consumer_prepared_validation.py`; that helper may import `consumer_motion`, `prepare_skeleton`, `validate`, PyYAML and JSON Schema. The stdlib integrity core in `prepared.py` must not import those modules, directly or transitively. Blender calls the integrity core, not the host validation wrapper. No pure-source evaluator, YAML parser, generic schema validator or compiled-reference resource is required inside Blender.

The integrity core reads JSON once with duplicate-key rejection, enforces finite data and the prepared format/content seal, verifies the active package identity and every declared package-resource hash, and retains the existing unique/sorted sample IDs and body inventory checks. For a consumer snapshot it also checks submitted/resolved canonical hashes, base-lineage logical resource/hash correspondence against the active package, and sample/timeline references against the prepared sample inventory. These are integrity/consistency checks on the transferred prepared data, not YAML/schema validation, source-to-base re-resolution or dense kinematic replay.

`run_blender.run` fully validates the persisted input in host Python before its version probe and obtains canonical `content_sha256` from that validated in-memory value. It passes this exact value to the private Blender entry point as `--expected-prepared-sha256`, as well as the existing invocation receipt's `source_sha256`. The backend compares the loaded content seal with this expected identity before emitting `input_loaded`, constructing the scene or writing output. A consumer snapshot without an expected identity is rejected. Launcher-generated invocations always supply the argument; its shape is a lowercase SHA-256 hex string. The private entry point does not expose an option to skip host validation through the public API.

This binding closes the gap between host validation and backend reading: replacing a file with another correctly resealed document after host validation fails the expected-identity check. Existing `input_loaded`, build metadata, output manifests and receipt/output validation must agree on that same identity. Post-render host reading of the copied prepared input performs full validation again. Hash-equivalent formatting changes retain their existing canonical-content meaning.

Blender trusts the installed HML host launcher to have performed source validation; it no longer independently reparses package YAML or repeats source semantics. A caller directly invoking an internal backend script with an invented matching hash does not obtain a source-validation verdict. Content hashing detects inconsistency/substitution relative to the host-validated identity, not author authentication or permission truth. The host's provenance, kinematic, numerical and human-review requirements remain unchanged. There is no runtime auto-detection of dependencies, swallowed import error, fallback to reduced validation, host site-packages injection or new compiled-source format.

Add optional `consumer_motion` to `PreparedResult` and inherited generation results, as an independent deep snapshot with projection parity. Keep `fixture_id` as the existing result join key, populated with the consumer ID. Extend source-provenance projection with explicit origin/hash basis for consumer sources; existing package records and fields stay readable. Consumer identities use logical labels such as `consumer/<id>/submitted` and `consumer/<id>/resolved`, never pretend to be package resources. Base lineage records preserve raw-package hash semantics; consumer records explicitly use canonical content hash semantics. Results never need internal-module imports or repository paths to interpret these fields.

**Alternatives considered:** mix external paths into `source_hashes`, reread the original source at render time, trust a mutable returned dictionary, import host dependencies into Blender, or introduce a compiled reference index and a second source validator. The selected human-approved boundary retains full host validation and binds backend integrity to its exact result while avoiding additional runtime dependencies and persisted formats.

### 6. Provide a consumer-controlled verification example

Document a public-only helper/example taking required argument `knee_peak_deg`; do not give it a default exercise amplitude. The example accepts finite non-boolean `0 < knee_peak_deg <= 90` **as its own documented example domain**, computes `factor = knee_peak_deg / 90`, and submits a variant of `squat` scaling these six channels:

- `knee.L.flexion`, `knee.R.flexion`;
- `ankle.L.dorsiflexion`, `ankle.R.dorsiflexion`;
- `pelvis.pitch`, `lumbar.flexion`.

The explicitly coupled scaling is part of this authored technical example, not an HML clinical model or universal depth parameter. Arms retain the existing constant track. The API itself has no new squat-depth limit; it validates the effective source against existing operating/contact bounds. Use test calls at 30 and 60 degrees to prove depth travels from consumer to source, solved count sample and render; state these are test inputs. The unchanged 90-degree fixture is comparison evidence. At BPM 90 all have count samples 0–4 and 17 animation samples. Also provide one complete self-contained consumer `action_sweep` definition with a new ID, a neutral base, explicit integer keys and metadata, using only public API imports and authored values.

Do not commit a new fixture to `rig/diagnostics`, `poses`, `segments` or `motions`. Put example text in `docs/usage.md` and synthetic source builders in tests; generated example files belong only to managed runs. No new CLI source option is introduced; commands still delegate their existing diagnostic options through the public API. Update `tools/README.md` with the authoritative contributor/example verification commands so entry points do not appear silently.

### 7. Independent verification and human visual pack

Record a pre-change baseline before implementation, then run candidate/independent verification using fresh direct children of `build/`. Names use exactly five underscore-separated components, each lowercase kebab-case, for example:

- `support-consumer-authored-motions_r1_dev_try-1_baseline-prepare` and `..._baseline-render`;
- `support-consumer-authored-motions_r1_dev_try-1_host-check`;
- `support-consumer-authored-motions_r1_reviewer_try-1_custom-prepare`;
- `support-consumer-authored-motions_r1_reviewer_try-1_render-a` and `..._render-b`;
- `support-consumer-authored-motions_r1_reviewer_try-1_verify` and `..._review-pack`.

Input, render, numeric and presentation runs are distinct/disjoint; retries get new attempt names. A single preparation can be input to two independent render runs. Keep wheels, temporary installations, test workspaces and example sources inside the owning run; a tool that requires a workspace/build hierarchy can use it inside that run, while independent externally managed runs stay flat. Document the owning run and avoid treating nested tool working directories as independent runs. Reuse protected accepted legacy packs read-only where useful.

Host acceptance includes all existing diagnostic preparations, mapping/YAML/JSON equivalence, fixture/motion conflict, schema and semantic faults, finite/boolean values, coupled/contact failures between delivered frames, provenance closure, snapshot/lineage mutation, and package/file immutability. Assert that consumer snapshot/source failures occur before any backend probe or launch. Exercise the installed wheel from an unrelated directory, removing source files before render. Include complete-definition and variant paths; test variant replacement as well as scaling. Add an isolated backend integrity-reader test with YAML/jsonschema/referencing and their host adapters unavailable, plus missing/mismatched expected identity and a controlled resealed-input substitution after host validation. Run relevant existing API, prepared, source-integrity, diagnostic, workspace and backend tests. A real backend is required for image claims, and its evidence must distinguish host source validation from backend integrity checks.

The focused pack contains:

- A summary distinguishing source/host tests, independent numeric/backend results and pending human judgment, with source/base/resolved hashes and parameter values.
- Count sheets for 30/60/90 test degrees: columns beats 0,1,2,3,4; rows each depth's front then side view. Use identical crop/scale and the fixed existing cameras/floor/light.
- In-between sheets with columns all 17 BPM-90 animation times and rows grouped by depth/view; labels include exact beat, seconds and requested/measured knee angle.
- Timed front/side GIFs for each depth at BPM 90, using exact timeline times and endpoints once.
- Side-view onion skins separately overlaying descent beats 0/1/2 and ascent beats 2/3/4 for each depth, with colors/legend, plus a beat-2 overlay comparing 30/60/90.
- A small front/side sheet and GIF for the complete-definition source; its source/description are labeled separately from the squat variants.
- Packaged squat baseline/candidate count comparisons, arm-raise/neutral regression coverage, and exact decoded-pixel comparison for corresponding unchanged baseline/candidate samples. Compare two clean candidate renders for deterministic pixels. Do not compare deliberately changed variants to the 90-degree fixture as a pixel-equality requirement.

Independent numeric checks use existing measurements for actual bilateral knee angles, rigid transforms, coupling conditions, contact target/sliding/floor tolerances and loop closure. The four-beat variant loop must return within `0.1 degrees` and `1e-4 H`; world-root XY remains identical. Check requested degree peaks within 0.1 degrees and retain values/errors per sample. General custom motion validation does not inherit diagnostic-specific 90-degree or static-balance acceptance. If balance is reported for a variant, it must be freshly measured and separately labeled approximate static plausibility; it is not a prerequisite introduced by this API change.

The human inspects whether shallower depth and descent/ascent are readable, feet look planted, posture is credible and fixed framing is preserved. Store `review.md` in the change folder, cite requirement/scenario for each finding, and link the independently generated pack. Gate 2 remains pending until explicit human acceptance; numerical success never supplies it.

Before every hand-off, inventory all new runs, links and dependencies. Retain baseline evidence until candidate regression/review and human decisions no longer need it; retain final preparation/render/numeric/pack roots while the review links them. Remove obsolete whole retry runs only after checking dependencies and links, without following symlinks outside `build/` or touching another agent's active run. Record removed paths/bytes, retained paths/reasons, before/after link checks and pending cleanup in the existing hand-off/review record. No new build run is needed merely to write this proposal.

## Risks / Trade-offs

- **Initial language scope remains diagnostic-shaped** → Make supported constructors and missing composition/context explicit; complete consumer definitions are real external inputs but are not the future motion-library format.
- **Simple scaling can produce an invalid or implausible movement** → The consumer chooses explicit channel scales; preflight checks bounds/contacts, independent numeric review checks outputs, and human review checks readability. Never promise that every depth or recipe is acceptable.
- **Dense preflight grows with duration/BPM** → Iterate checks and keep only delivered samples; preserve the 0.01-beat evidence scope and report it, without claiming continuous mathematical proof.
- **Caller clearance declarations may be false** → Validate schema, supported licenses and reference closure; preserve exact declarations and state the limit of offline validation. Independent project source clearance remains required.
- **Full replay increases host render preflight time** → Keep full source/provenance/dense/sample validation on host, then transfer its exact validated identity to Blender; do not repeat host-only source processing inside the embedded runtime.
- **Backend integrity depends on the host validation decision** → Every supported launch goes through full host validation and passes its expected canonical prepared hash. Verify mismatches before scene construction; never describe backend integrity as independent source acceptance or author authentication.
- **Existing verifiers contain packaged fixture assumptions** → Keep consumer preflight/review scoped to actual selected sources, and avoid applying the packaged 90-degree dossier or full-library coverage assertions to the consumer ID.

## Migration Plan

This is an additive public API/source capability for the next compatible feature release under the project's version policy. Existing source dictionaries and fixture IDs need no migration. New source/envelope/snapshot formats and their package schemas ship together; the old diagnostic format, units, rotation conventions and package-only source-hash meaning are unchanged. Existing callers may omit `motion` and the optional result field. Previously prepared artifacts remain subject to the existing exact active-package identity check and are regenerated after upgrading HML; no cross-release compatibility is newly promised. Rollback uses the previous immutable package release and freshly prepared inputs for that release. Implementation begins only after Human Gate 1 approval of these artifacts.

The approved validation-boundary amendment changes code/package identity but adds no compiled index, source/snapshot format, dependency or public API option. Rebuild the candidate wheel and regenerate candidate prepared inputs under its exact identity before resumed review/render. Reopen the reader-integration task and run the new host/backend boundary checks. Preserve previous checked tasks and evidence under their original package identities; they are historical scoped evidence, not acceptance of the amended reader or new candidate. Failed Blender receipts remain failure evidence until dependency-aware cleanup permits removal. The pre-change visual baseline remains a read-only comparison input. Human Gate 2 stays pending.
