# Spec Delta

## MODIFIED Requirements

### Requirement: Public generation has a small importable contract

HML SHALL expose documented synchronous `prepare` and `render` functions under `humanmotionlib.api`, with keyword parameters and typed results. They SHALL cover the installed skeleton diagnostic pipeline and the supported consumer-motion source contract. Importing the API SHALL neither import Blender's Python API nor launch a process, parse command-line arguments, change the working directory or write files.

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

### Requirement: Generation exposes resolvable provenance

Preparation and render results SHALL expose packaged and consumer source identities, hashes, license and provenance records, all referenced material identifiers, applicable license/register contents and limitations. Provenance SHALL remain available outside the checkout. Every external material actually used for this change SHALL have verified commercial and derivative permission and a complete used-materials entry, including materials requiring no attribution.

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

### Requirement: Public results have a documented portable projection

Results SHALL provide a documented JSON-compatible projection containing the same information as their typed Python fields, including consumer identity/lineage when present. Paths SHALL project as absolute strings, exact times as numerator/denominator pairs and collections in deterministic order. Returned metadata SHALL be independent snapshots whose modification cannot alter prepared files, resource identities or a later render request.

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
