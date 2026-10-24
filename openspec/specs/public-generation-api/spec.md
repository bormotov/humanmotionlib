# public-generation-api Specification

## Purpose

Let Python consumers prepare and render the supported HML diagnostics directly, with enough structured image, pose, timing and provenance information to use the generated frames without interpreting internal pipeline files.

## Requirements

### Requirement: Public generation has a small importable contract

HML SHALL expose documented synchronous `prepare` and `render` functions under `humanmotionlib.api`, with keyword parameters and typed results. They SHALL cover the installed skeleton diagnostic pipeline. Importing the API SHALL neither import Blender's Python API nor launch a process, parse command-line arguments, change the working directory or write files.

#### Scenario: Import and call from a Python application
- **Verification:** installed-wheel API smoke test, import/process/filesystem interception and signature assertions.
- **WHEN** an application imports the API outside the checkout with unrelated command-line arguments
- **THEN** the documented functions, result types and error types are importable without Blender installed
- **AND** no process, output, argument parsing, working-directory change or `sys.argv` mutation occurs
- **AND** source and installed usage have the same public contract and require no internal-module imports.

### Requirement: Preparation accepts explicit generation parameters

Preparation SHALL accept a packaged profile, optional stature and diagnostic fixture subset, requested BPMs, an explicit workspace and prepared-file destination. It SHALL validate sources and parameters and return a persisted, integrity-sealed prepared input plus structured poses, timelines and provenance. Preparation SHALL NOT require or probe Blender.

#### Scenario: Prepare the existing supported coverage
- **Verification:** all-fixture preparation comparison with existing preparation and installed host tests.
- **WHEN** preparation selects the default profile and leaves stature, fixtures and BPMs unspecified
- **THEN** it selects `adult-reference-v1`, the profile's reference stature, every packaged diagnostic and BPMs 60, 120 and 180
- **AND** returned prepared identity, solved poses, controls, rest policies, contacts and sampling match the existing pipeline
- **AND** the returned prepared-file path exists and can be passed directly to rendering.

#### Scenario: Override and validate request parameters
- **Verification:** parameter matrix with finite-value, unknown-ID, duplicate and empty-selection cases and spawn/write interception.
- **WHEN** preparation selects fixtures `neutral` and `arm-raise`, stature 1.50 m and BPMs 60 and 90
- **THEN** only those fixtures are prepared, dimensioned data scales under the existing profile contract, and both requested timelines are returned
- **AND** unknown profiles/fixtures, empty or duplicate selections, non-positive/non-finite stature or BPM, boolean numeric values and unsupported options fail explicitly before output creation or backend probing
- **AND** callers cannot substitute arbitrary motion files, renderer settings or unvalidated source dictionaries through this API.

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

Rendering SHALL accept a prior preparation result or explicit prepared-file path and a fresh output run. By default it SHALL render the fixed scene and return ordered image records linking absolute image paths, view identifiers and pose identities to the prepared timelines. Successful return SHALL require complete, fresh, readable outputs with matching source identity; process exit alone SHALL NOT suffice.

#### Scenario: Render a prepared subset
- **Verification:** pinned real backend run, image decoding, expected-view inventory and result/path assertions.
- **WHEN** an application renders a valid prepared subset using the default render mode
- **THEN** HML returns every expected image for every prepared sample, including front/side views and the existing extra neutral/rest views
- **AND** each returned image path exists, decodes and remains inside the selected output run
- **AND** pose and timeline references let callers obtain ordered images for each fixture, BPM, mode and view without reading manifests
- **AND** the result identifies prepared input, saved scene, metadata, render manifest, execution receipt and any evaluated/geometry artifacts actually produced
- **AND** missing, extra, duplicate, malformed, escaping or stale entries in the manifest's expected sample/view image inventory prevent a successful result; unrelated diagnostic logs are not image entries.

#### Scenario: Preserve existing construction modes
- **Verification:** API/CLI option-mapping tests and backend output inventory tests.
- **WHEN** the caller explicitly requests construction without images or render-only execution
- **THEN** construction without images returns an empty image collection and no claimed render manifest
- **AND** render-only execution omits evaluated/geometry artifacts and does not claim their verification
- **AND** incompatible image/destination options fail before launching Blender.

### Requirement: Generation exposes resolvable provenance

Preparation and render results SHALL expose source identities, hashes, license and provenance records, all referenced material identifiers, applicable license/register contents and limitations. Provenance SHALL remain available outside the checkout. Every external material actually used for this change SHALL have verified commercial and derivative permission and a complete used-materials entry, including materials requiring no attribution.

#### Scenario: Follow generated-data attribution
- **Verification:** source-to-result provenance comparison, nested reference traversal and installed license-content audit.
- **WHEN** a caller prepares and renders the reference profile and an authored diagnostic
- **THEN** results distinguish authored diagnostic provenance from adapted profile/mobility provenance and preserve source locators and declared modifications
- **AND** every material referenced anywhere in the used source records resolves in the provided register, including nested profile records
- **AND** returned register/license contents preserve applicable CC-BY-4.0 data, Apache-2.0 code and third-party conditions without requiring the caller to open repository files
- **AND** result limitations identify the kinematic approximation and the absence of clinical or human visual acceptance.

#### Scenario: Reject uncleared new reference use
- **Verification:** developer/reviewer source-clearance inventory against `docs/used-materials.md`.
- **WHEN** implementation uses an external document, example, dependency or asset to inform or produce the change
- **THEN** the register records exact material/part, source and license URLs, permission basis, conditions, checked date and related outputs
- **AND** missing, ambiguous, non-commercial, no-derivatives or incompatible terms block that use
- **AND** existing registered sources are reused without asserting that a URL's public availability grants permission.

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

The API SHALL enforce the existing explicit absolute workspace, flat fresh-run, write-containment, disjoint input/output, immutable-package and external-backend contracts. Resource and executable discovery SHALL be independent of the invocation directory. Rendering SHALL use HML's supervised pinned Blender path with finite execution and slot deadlines.

#### Scenario: Use an installed API from an unrelated directory
- **Verification:** non-editable wheel run with checkout imports disabled, read-only invocation/installation trees, path matrix and filesystem audit.
- **WHEN** preparation and rendering target an explicit caller workspace from an unrelated directory containing misleading checkout-shaped neighbors
- **THEN** resources come from the installed package and all HML state is inside the workspace's permitted build tree
- **AND** relative operands resolve against the workspace, returned paths are absolute and independent input/output runs remain disjoint after symlink resolution
- **AND** missing/relative workspace, invalid run names, occupied destinations, overlap and symlink escape fail before allocating state or launching Blender
- **AND** probe/build/render retain backend pins, process ownership, cancellation, lock contention and no-host-environment-injection rules.

### Requirement: CLI generation delegates to the public contract

The `prepare-skeleton` and `run-blender` commands SHALL translate arguments into the same public generation operations used by Python callers. Existing documented options, default behavior, output artifacts and exit failures SHALL remain compatible. CLI parsing and presentation SHALL NOT become prerequisites for Python API use.

#### Scenario: Compare Python and command callers
- **Verification:** CLI delegation assertions, subprocess parity matrix and normalized result/artifact comparison.
- **WHEN** equivalent supported preparation and construction/render requests run through Python, `hml` and `python -m humanmotionlib` in independent fresh runs
- **THEN** they select the same resources, parameters, samples and outputs, with equivalent identity and failure classification after excluding run-specific paths and receipt IDs
- **AND** CLI invalid arguments still return nonzero status while API errors remain catchable
- **AND** existing no-images construction, `--render-dir`, `--render-only`, stature, fixture and deadline options keep their meanings
- **AND** other command modes retain their existing behavior without being added to this small public API.

### Requirement: Public results have a documented portable projection

Results SHALL provide a documented JSON-compatible projection containing the same information as their typed Python fields. Paths SHALL project as absolute strings, exact times as numerator/denominator pairs and collections in deterministic order. Returned metadata SHALL be independent snapshots whose modification cannot alter prepared files, resource identities or a later render request.

#### Scenario: Consume and serialize a result safely
- **Verification:** JSON serialization, deterministic ordering, deep-mutation and artifact-hash tests.
- **WHEN** a caller serializes a result projection or modifies a returned nested mapping
- **THEN** standard JSON serialization succeeds without a custom encoder and preserves exact timing/provenance links
- **AND** the same request has stable sample/timeline/image ordering
- **AND** prepared-file bytes and package resources remain unchanged, and rendering revalidates the persisted prepared input rather than trusting modified result metadata.

### Requirement: API integration preserves generation output and visual review

The API integration SHALL preserve existing poses, controls, rest policies, contacts, units, mirroring, beat timing and fixed camera/floor/light. Independent review SHALL separate host-contract evidence, real-backend/numeric evidence and human visual judgment, and provide the focused comparison pack defined in design before archive.

#### Scenario: Compare API generation with the existing workflow
- **Verification:** independent clean builds, existing numeric verifier, exact decoded-pixel comparison and explicit human visual review.
- **WHEN** the reviewer generates neutral/rest and the four-beat arm raise at reference stature using the pre-change CLI baseline and candidate API/CLI
- **THEN** pose/timing content and evaluated geometry meet unchanged applicable limits and corresponding decoded image pixels agree exactly on the pinned reference backend
- **AND** all-fixture host preparation coverage is reported separately from focused visual coverage
- **AND** the human receives labeled count/in-between sheets, timed GIFs, onion-skin overlays and baseline/API/CLI comparisons
- **AND** numerical or process success never implies human visual acceptance.
