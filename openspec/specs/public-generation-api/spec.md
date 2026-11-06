# public-generation-api Specification

## Purpose

Let Python consumers prepare and render the supported HML diagnostics directly, with enough structured image, pose, timing and provenance information to use the generated frames without interpreting internal pipeline files.

## Requirements

### Requirement: Public generation has a small importable contract

HML SHALL expose documented synchronous `prepare` and `render` functions under `humanmotionlib.api`, with keyword parameters and typed results. They SHALL cover installed character rendering of the shared diagnostic pipeline and supported consumer-motion sources. Importing the API SHALL neither import Blender's Python API nor launch a process, parse command-line arguments, change the working directory or write files.

#### Scenario: Import and call from a Python application
- **Verification:** installed-wheel API smoke test, import/process/filesystem interception and signature assertions.
- **WHEN** an application imports the API outside the checkout with unrelated command-line arguments
- **THEN** the documented functions, result types and error types are importable without Blender installed
- **AND** no process, output, argument parsing, working-directory change or `sys.argv` mutation occurs
- **AND** source and installed usage have the same public contract and require no internal-module imports.

### Requirement: Preparation accepts explicit generation parameters

Preparation SHALL accept a packaged profile, optional stature, diagnostic fixture subset or explicit consumer motion, requested BPMs, an explicit workspace and prepared-file destination. It SHALL validate sources and parameters and return a persisted, integrity-sealed prepared input plus structured poses, timelines and provenance. Preparation SHALL NOT require or probe Blender.

#### Scenario: Prepare the existing supported coverage
- **Verification:** all-fixture preparation comparison with existing preparation and installed host tests.
- **WHEN** preparation selects the default profile and leaves stature, fixtures, consumer motion and BPMs unspecified
- **THEN** it selects `adult-reference-v1`, the profile's reference stature, every packaged diagnostic and BPMs 60, 120 and 180
- **AND** returned prepared identity, solved poses, controls, rest policies, contacts and sampling match the existing pipeline for the active package identity
- **AND** the returned prepared-file path exists and can be passed directly to rendering.

#### Scenario: Override and validate request parameters
- **Verification:** parameter matrix with finite-value, unknown-ID, duplicate and empty-selection cases and spawn/write interception.
- **WHEN** preparation selects fixtures `neutral` and `arm-raise`, stature 1.50 m and BPMs 60 and 90
- **THEN** only those fixtures are prepared, dimensioned data scales under the existing profile contract, and both requested timelines are returned
- **AND** unknown profiles/fixtures, empty or duplicate selections, non-positive/non-finite stature or BPM, boolean numeric values and unsupported options fail explicitly before output creation or backend probing
- **AND** callers cannot substitute renderer settings, unvalidated source dictionaries or unsupported motion formats through this API.

#### Scenario: Prepare a consumer movement explicitly
- **Verification:** mapping/file installed API matrix, default/selection regression and write/process interception.
- **WHEN** preparation supplies a valid `motion` document or local document path, no fixture subset, and explicit BPM/stature overrides
- **THEN** only that resolved consumer movement has returned pose/timeline samples, while required packaged bases remain available as source dependencies
- **AND** supplied BPM and stature retain their existing meaning
- **AND** supplying both `motion` and `fixtures` fails as an invalid request before output creation
- **AND** malformed consumer sources fail as source-validation errors with source/field details, rather than being treated as packaged fixture identifiers.

### Requirement: Results expose pose and exact playback context

Both result types SHALL provide ordered pose samples and per-fixture, per-BPM static and animation timelines referencing those samples. Each timeline entry SHALL identify its sample, sequence frame index, exact beat and exact seconds at that BPM. Pose records SHALL expose solved pose data, body group controls, rest policy and contact intent with declared units and conventions.

#### Scenario: Interpret returned frames without parsing pipeline JSON
- **Verification:** structured-result assertions and rational timing checks against the sampler.
- **WHEN** a four-beat arm raise is prepared at 60, 90, 120 and 180 BPM
- **THEN** every timeline entry resolves to exactly one returned pose, and every pose identifies its fixture, beat, action values, FK deltas and world root
- **AND** static timelines contain five count samples; animation timelines contain 21, 17, 13 and 13 entries respectively, including endpoints once
- **AND** each full beat has at least two in-between samples and intervals no longer than 200 ms
- **AND** the beat-2 sample reports seconds 2, 4/3, 1 and 2/3 respectively, rather than reusing the prepared sample's legacy 120-BPM timestamp
- **AND** static and animation entries at a shared beat reference the same pose identity.

### Requirement: Rendering returns complete validated image results

Rendering SHALL accept a prior preparation result or explicit prepared-file path, a fresh output run and an optional character selection defaulting to skeleton. It SHALL return ordered character-linked images and artifacts. Successful return SHALL require the complete fresh readable output set and matching prepared/render identities; process exit alone SHALL NOT suffice.

#### Scenario: Render a prepared subset
- **Verification:** pinned real backend run, image decoding, expected-view inventory and result/path assertions.
- **WHEN** an application renders a valid prepared subset using the default render mode
- **THEN** HML returns every expected skeleton image for every prepared sample, including front/side views and the existing extra neutral/rest views
- **AND** each returned image path exists, decodes and remains inside the selected output run
- **AND** pose and timeline references let callers obtain ordered images for each fixture, BPM, mode and view without reading manifests
- **AND** the result identifies prepared input, saved scene, metadata, render manifest, execution receipt and any evaluated/geometry artifacts actually produced
- **AND** missing, extra, duplicate, malformed, escaping or stale entries in the manifest's expected sample/view image inventory prevent a successful result; unrelated diagnostic logs are not image entries.

#### Scenario: Preserve existing construction modes
- **Verification:** API/CLI option-mapping tests and backend output inventory tests.
- **WHEN** the caller explicitly requests construction without images or render-only execution
- **THEN** construction without images returns an empty image collection and no claimed render manifest
- **AND** render-only execution omits evaluated/geometry artifacts and does not claim their verification
- **AND** incompatible image/destination options fail before launching Blender
- **AND** selected character identities remain available in both modes without inventing surface numeric evidence.

#### Scenario: Render a complete character batch
- **Verification:** installed API/CLI host-contract tests, controlled image/result decoding and character/sample/view inventory faults. The product contract is retained; native complete-character batch pixel parity is outside the approved remaining diagonal acceptance.
- **WHEN** rendering selects skeleton, male and female from one prepared input
- **THEN** every selected character uses the existing shared poses/timelines, and every image explicitly identifies character, sample and view
- **AND** skeleton retains existing paths/views, while each surface has the design's front/side and neutral/rest rear inventory in its own collision-free paths
- **AND** ordered character descriptors, per-character artifacts, provenance and render identity are available through typed results and projections
- **AND** each character rendered alone has the same decoded image pixels as its batch member
- **AND** a missing or mismatched character image/artifact fails the whole request without a success-shaped partial batch.

### Requirement: Generation exposes resolvable provenance

Preparation and render results SHALL expose packaged and consumer source identities, hashes, license/provenance, referenced materials, register contents and limitations. Render results SHALL additionally expose selected-character dependency attribution separately from shared preparation. Every external material actually used SHALL have verified commercial/derivative permission and a complete used-materials entry, including no-attribution materials.

#### Scenario: Follow generated-data attribution
- **Verification:** source-to-result provenance comparison, nested reference traversal and installed license-content audit.
- **WHEN** a caller prepares and renders the reference profile and an authored diagnostic
- **THEN** results distinguish authored diagnostic provenance from adapted profile/mobility provenance and preserve source locators and declared modifications
- **AND** every material referenced anywhere in the used source records resolves in the provided register, including nested profile records
- **AND** returned register/license contents preserve applicable CC-BY-4.0 data, Apache-2.0 code and third-party conditions without requiring the caller to open repository files
- **AND** result limitations identify the kinematic approximation and the absence of clinical or human visual acceptance.

#### Scenario: Follow a consumer variant's inherited attribution
- **Verification:** original-to-result traversal, snapshot hashes, registered-material union and installed render test.
- **WHEN** a caller prepares a consumer variant of the packaged squat
- **THEN** results distinguish its consumer contribution, resolved definition, packaged base and profile/mobility provenance
- **AND** source identities identify which hashes describe package bytes and which describe canonical submitted/resolved consumer content
- **AND** the consumer's contribution cannot replace or conceal base attribution or register entries
- **AND** rendering preserves the same consumer identity/provenance even when its original source file is unavailable.

#### Scenario: Reject uncleared new reference use
- **Verification:** developer/reviewer source-clearance inventory against `docs/used-materials.md`.
- **WHEN** implementation uses an external document, example, dependency or asset to inform or produce the change
- **THEN** the register records exact material/part, source and license URLs, permission basis, conditions, checked date and related outputs
- **AND** missing, ambiguous, non-commercial, no-derivatives or incompatible terms block that use
- **AND** existing registered sources are reused without asserting that a URL's public availability grants permission.

#### Scenario: Follow appearance and inherited skeletal attribution
- **Verification:** selected dependency-closure comparison and installed portable-projection audit.
- **WHEN** a caller renders one or both surface characters from a prepared consumer movement
- **THEN** separate character provenance identifies authored descriptor/template/preset sources and revisions, alongside unchanged consumer/base/profile/mobility attribution
- **AND** all referenced material and license records resolve outside the checkout
- **AND** a skeleton-only selection exposes its descriptor provenance without claiming that a body surface was used
- **AND** neither selecting a visible sex nor surface volume changes mass coefficients or clinical/mobility claims.

### Requirement: API failures are catchable and retain evidence

Public operations SHALL raise documented API exceptions for invalid requests, source/integrity failures and backend failures rather than exit the interpreter or return a success-shaped partial result. Backend errors SHALL expose a stable reason and available receipt/run paths, preserve the original cause and retain timeout, cancellation and cleanup evidence under the existing supervisor policy.

#### Scenario: Diagnose validation and backend failures
- **Verification:** host fault matrix with tampered prepared input, missing executable, mismatch, contention, timeout, spawn failure and invalid output.
- **WHEN** invalid input or a supervised backend failure occurs
- **THEN** a caller can catch the documented exception and inspect its reason without parsing console output
- **AND** preflight errors expose no invented receipt; failures after receipt creation expose the existing receipt and owning run
- **AND** no API failure calls `sys.exit`, retries automatically, downloads a backend, launches a GUI or treats partial images as a successful result
- **AND** cancellation terminates the owned child tree and preserves pending cleanup if termination is unconfirmed; `KeyboardInterrupt` is re-raised after cleanup.

### Requirement: API execution preserves installation and workspace boundaries

The API SHALL enforce explicit absolute workspace, write-containment, disjoint input/output, immutable-package and existing supervised-backend contracts. Resource and executable discovery SHALL remain independent of the invocation directory. Standalone calls SHALL retain fresh flat-run defaults. A narrow explicit matrix-destination binding SHALL permit generation into declared preparation and render content within one stable matrix result root; this binding SHALL not add a package, process or execution-plan protocol.

#### Scenario: Use an installed API from an unrelated directory
- **Verification:** non-editable installed package, unrelated invocation directory and existing path/immutable-resource tests.
- **WHEN** preparation and rendering target an explicit caller workspace from an unrelated directory containing misleading checkout-shaped neighbors
- **THEN** resources come from the installed package and all HML state is inside the workspace's permitted build tree
- **AND** relative operands resolve against the workspace, returned paths are absolute and independent input/output runs remain disjoint after symlink resolution
- **AND** standalone calls reject missing/relative workspace, invalid run names, occupied destinations, overlap and symlink escape before allocating state or launching Blender
- **AND** probe/build/render retain backend pins and existing supervision, cancellation and environment-boundary rules.

#### Scenario: Write a selected matrix result directly
- **Verification:** public API destination mapping and two sequential matrix builds with original receipt paths.
- **WHEN** the thin matrix runner explicitly binds a stable five-component result root and its fixed preparation/render destinations
- **THEN** the API validates containment, nonsymlink paths and producer input/output separation before writing
- **AND** generation writes directly to those content paths and returns original evidence for those paths
- **AND** the runner may clear its previous declared result before a complete repeat while preserving logs and unrelated content
- **AND** an explicitly requested but incomplete, foreign, escaping or overlapping binding fails before backend work; omitting matrix mode retains standalone fresh-run defaults.

### Requirement: CLI generation delegates to the public contract

The `prepare-skeleton` and `run-blender` commands SHALL translate arguments into the same public generation operations used by Python callers. Existing documented options, default behavior, output artifacts and exit failures SHALL remain compatible. `run-blender` SHALL additionally expose the same character selection as `render`. CLI parsing and presentation SHALL NOT become prerequisites for Python API use.

#### Scenario: Compare Python and command callers
- **Verification:** CLI delegation assertions, subprocess parity matrix and normalized result/artifact comparison.
- **WHEN** equivalent supported preparation and construction/render requests run through Python, `hml` and `python -m humanmotionlib` in independent fresh runs
- **THEN** they select the same resources, parameters, samples and outputs, with equivalent identity and failure classification after excluding run-specific paths and receipt IDs
- **AND** CLI invalid arguments still return nonzero status while API errors remain catchable
- **AND** existing no-images construction, `--render-dir`, `--render-only`, stature, fixture and deadline options keep their meanings
- **AND** other command modes retain their existing behavior without being added to this small public API.

#### Scenario: Compare explicit and omitted character selection
- **Verification:** installed console/module/API selection and parity matrix.
- **WHEN** callers omit selection, explicitly select skeleton, individually select a surface, or request the complete registered set
- **THEN** equivalent requests have the same selected identities, image inventory, source closure and output semantics
- **AND** omission remains skeleton-only and preserves existing command behavior
- **AND** CLI `--characters` and Python `characters` reject unknown, empty or duplicate selections explicitly.

### Requirement: Public results have a documented portable projection

Results SHALL provide a documented JSON-compatible projection matching their typed fields, including consumer lineage and selected-character identity/provenance when present. Paths SHALL project as absolute strings, exact times as numerator/denominator pairs and collections deterministically. Returned metadata SHALL be independent snapshots whose modification cannot alter prepared files, resource identities or later rendering.

#### Scenario: Consume and serialize a result safely
- **Verification:** JSON serialization, deterministic ordering, deep-mutation and artifact-hash tests.
- **WHEN** a caller serializes a result projection or modifies a returned nested mapping
- **THEN** standard JSON serialization succeeds without a custom encoder and preserves exact timing/provenance links
- **AND** the same request has stable sample/timeline/image ordering
- **AND** prepared-file bytes and package resources remain unchanged, and rendering revalidates the persisted prepared input rather than trusting modified result metadata.

#### Scenario: Join consumer poses with existing result types
- **Verification:** typed-field/projection parity and image/timeline reference assertions.
- **WHEN** a consumer movement with a distinct valid identifier is prepared and rendered
- **THEN** existing `fixture_id` fields carry that consumer movement identifier and remain joinable with pose, timeline and image records
- **AND** an additive optional `consumer_motion` record exposes submitted/resolved hashes, submitted document, resolved definition and base lineage consistently in typed results and their projections
- **AND** diagnostic-only requests expose no invented consumer source and keep existing fields and ordering.

#### Scenario: Join several appearances to one exact timeline
- **Verification:** result/projection parity, deterministic ordering and mutation tests.
- **WHEN** a complete-character result is serialized or its returned nested metadata is modified
- **THEN** every image remains joinable by explicit character/sample/view identity to the shared exact timeline, without tripling or renaming pose IDs
- **AND** character order is registry order regardless of request order
- **AND** projected character/artifact/provenance records match typed values and all paths are absolute
- **AND** modifying returned metadata cannot change request seals, package resources, prepared content or later rendering.

### Requirement: API integration preserves generation output and visual review

The API integration SHALL preserve existing poses, controls, rest policies, contacts, units, mirroring, beat timing and fixed camera/floor/light. Independent review SHALL separate host-contract, real-backend/numeric and human evidence. Skeleton default, explicit and batch modes retain their agreement contract, with batch selection/semantics/integrity verified through host/source tests and live default/explicit pixel equivalence checked at H=1.50 m. New characters SHALL receive the design's independently generated diagonal comparison pack and explicit human visual approval before archive. The remaining live acceptance SHALL use skeleton H=1.50 m, male H=1.70 m and female H=1.90 m; API/CLI comparisons SHALL keep character and stature identical within each comparison. Historical pre-change Blender construction and rendered output SHALL NOT be required as a comparison oracle for this change. Native same-height all-character/batch pixel parity and same-character cross-stature comparisons SHALL be disclosed as unassessed in this reduced acceptance.

#### Scenario: Compare API generation with the existing workflow
- **Verification:** independent clean builds, existing numeric verifier, exact decoded-pixel comparison and explicit human visual review.
- **WHEN** the reviewer generates neutral/rest and the four-beat arm raise for each approved diagonal pair using current-candidate API and CLI workflows
- **THEN** pose/timing content and evaluated geometry meet unchanged applicable limits and corresponding decoded image pixels agree exactly on the pinned reference backend
- **AND** all-fixture host preparation coverage is reported separately from focused visual coverage
- **AND** the human receives labeled count/in-between sheets, timed GIFs, onion-skin overlays and current-candidate API/CLI comparisons
- **AND** numerical or process success never implies human visual acceptance.

#### Scenario: Preserve default behavior while reviewing the added characters
- **Verification:** approved diagonal real-backend acceptance, full host selection/batch contracts and explicit human visual review.
- **WHEN** candidate skeleton default/explicit H=1.50 m, male H=1.70 m and female H=1.90 m API/CLI results are independently reviewed
- **THEN** current-candidate skeleton default/explicit equivalence, consumer semantics and existing API failure/workspace contracts remain satisfied
- **AND** the new character evidence has separate surface, floor/contact, per-pair repeatability, source-clearance and visual verdicts, with native batch parity explicitly unassessed
- **AND** returning a render result still reports numeric acceptance as not-run and visual acceptance as pending until their separate verification gates.

### Requirement: Render character selection is validated and integrity-bound

Rendering SHALL validate a nonempty unique selection of packaged characters, normalize it to registry order, and bind its exact source closure to the persisted prepared identity. Host and backend SHALL agree on that render identity. Invalid selections or stale/tampered character inputs SHALL fail before successful construction or image reuse.

#### Scenario: Validate selection before allocating output
- **Verification:** API parameter/source/compatibility fault matrix with filesystem and process interception.
- **WHEN** selection is a bare string, empty, duplicate, unknown or incompatible, or selected source data fails schema/provenance/bind validation
- **THEN** the caller receives a catchable invalid-request or source/integrity failure with character/source context before output allocation or backend probing
- **AND** preparation is reused unchanged and skeleton selection has no semantic dependency on surface construction.

#### Scenario: Reject render selection substitution
- **Verification:** host/backend replacement, reseal, stale reuse and incomplete-batch fault matrix.
- **WHEN** character sources/selection change after host validation, a render request is resealed for a different character, or a manifest/receipt omits or swaps a batch member
- **THEN** expected render identity, package hashes and output membership prevent a successful result
- **AND** receipt, script phases, metadata and successful outputs identify the same prepared and character render request
- **AND** the backend performs integrity checks using only its standard-library/HML closure, not host YAML/schema dependencies
- **AND** existing finite deadlines, cancellation, workspace confinement and no automatic retry/download contracts remain enforced for the whole request.
