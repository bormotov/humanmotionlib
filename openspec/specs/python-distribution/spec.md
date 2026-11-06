# python-distribution Specification

## Purpose

Deliver the supported HML generation workflow as a dependency-complete Python distribution whose installed code and resources work independently of the source checkout.

## Requirements

### Requirement: Distribution identity and namespace are explicit

The installable distribution SHALL be named `humanmotionlib`, expose its implementation under `humanmotionlib.*`, and report one consistent release version through package metadata, Python and the command line, derived from the canonical `project.version` in `pyproject.toml`. Historical version `0.2.0` identifies the namespace migration; it SHALL NOT constrain subsequent release versions. The wheel SHALL NOT install a top-level `tools` package.

#### Scenario: Install and identify the wheel
- **Verification:** clean non-editable wheel install, metadata/import assertions and namespace inventory.
- **WHEN** the wheel is installed on supported CPython in an environment without the checkout on its import path
- **THEN** `humanmotionlib` imports from that installation and metadata, Python version reporting and `hml --version` all report the release version declared by the source snapshot used to build that wheel
- **AND** installing HML introduces no `tools` namespace and no dependency on checkout script paths
- **AND** active documentation maps former imports and commands to their installed replacements and labels the compatibility break.

#### Scenario: Build a later release without changing version-reporting code
- **Verification:** isolated build/install matrix with two valid declared release versions.
- **WHEN** the canonical project version advances beyond `0.2.0`
- **THEN** generated runtime version and manifest, distribution metadata, Python and CLI report that new version consistently without manually editing a second runtime version source
- **AND** version acceptance compares against the selected source version rather than a literal historical `0.2.0`
- **AND** the version change alone does not alter import namespaces, source resources, backend contracts or generation semantics.

### Requirement: Supported generation resources are complete

The wheel and source distribution SHALL contain the complete HML-owned resource closure for the supported anatomical skeleton diagnostics and registered characters. Installed validation, preparation, construction, numeric verification and review presentation SHALL require no checkout, Git state, runtime download or pre-generated source asset. Existing canonical data bytes and diagnostic coverage SHALL be preserved.

#### Scenario: Audit both distribution resource closures
- **Verification:** archive inventory, canonical-byte hash comparison and wheel rebuilt from the source distribution.
- **WHEN** distributions are built from the candidate sources
- **THEN** both carry the adult-reference profile and mobility, body groups, humanoid map, every diagnostic YAML, all schemas and their local references, fixed scene, required Blender code, backend contract, acceptance documentation and license/provenance records listed in design
- **AND** the wheel built from the source distribution has the same logical runtime-resource inventory and hashes as the direct wheel
- **AND** generated build history, environments, caches, tests and unrelated repository tooling are absent from the installed runtime.

#### Scenario: Reject an incomplete or altered installation
- **Verification:** isolated installed-resource deletion/corruption tests with process-spawn interception.
- **WHEN** a required resource or implementation file is missing, corrupt or inconsistent with the installed runtime manifest
- **THEN** affected generation fails with the logical resource identity before launching Blender
- **AND** no network fallback, checkout fallback or successful generation verdict occurs.

#### Scenario: Audit the complete character resource closure
- **Verification:** direct-wheel/sdist/rebuilt-wheel source inventory, schema-reference audit and byte hashes.
- **WHEN** distributions include skeleton, male and female character support
- **THEN** their registry, descriptors, common template, binding records, presets, schemas, documentation and required host/backend modules are present with canonical source bytes and implementation identities
- **AND** no generated mesh binary or runtime third-party character download substitutes for missing canonical data
- **AND** skeleton-only semantic execution does not parse/instantiate a body surface, while the complete installed resource integrity contract remains enforced.

### Requirement: Installed commands cover the supported workflow

Installed HML SHALL expose documented commands through the `hml` console entry point for source validation, skeleton preparation, supervised Blender construction/rendering, numeric verification and all existing review-pack modes. Module invocation through `python -m humanmotionlib` SHALL offer the same command contract. Python imports SHALL remain under `humanmotionlib.*`. Except for the explicit workspace and workspace-relative path contract, existing options, exit failures, numerical limits, contact checks and beat sampling SHALL retain their meanings.

#### Scenario: Use installed host commands
- **Verification:** clean wheel subprocess smoke tests with unset `PYTHONPATH` from a directory outside the checkout.
- **WHEN** an installed user invokes help, environment inspection, validation and fixture-subset preparation using `hml <subcommand>` and `python -m humanmotionlib <subcommand>`
- **THEN** the commands work without repository files or test discovery and report the supported Python, installed dependency and resource identities
- **AND** preparation covers every diagnostic when no subset is selected and validates explicit fixture selections
- **AND** invalid sources/options and failed checks remain nonzero failures.

#### Scenario: Complete installed generation and presentation
- **Verification:** pinned real backend execution, existing numeric verifier, standalone-link audit and presentation regression checks.
- **WHEN** the wheel is used on the reference platform with the pinned external Blender
- **THEN** supervised construction and render-only mode, numeric verification including existing optional audits, normal review-pack creation, render reuse and HTML-only regeneration are available
- **AND** installed code supplies the backend script and its complete embedded-Python import closure without checkout or host-environment injection
- **AND** HTML-only regeneration launches no Blender and preserves the existing local-asset and predecessor-evidence contract
- **AND** a full-fixture host inventory/prepare check and focused real-backend pack are labeled with their respective scopes.

#### Scenario: Apply the same workspace contract to every writer
- **Verification:** console/module parity and public API tests for preparation, construction, numeric reports/dossiers, normal review, render reuse and HTML-only regeneration.
- **WHEN** a caller requests a filesystem-writing operation
- **THEN** both entry points and the corresponding public writing API require the same explicit workspace and enforce the same write containment
- **AND** omission or a relative workspace fails before allocating a run, lock or temporary file or launching Blender
- **AND** help, version, environment inspection, validation and pure in-memory computations remain usable without a workspace and create no HML filesystem state.

### Requirement: Installed resources are independent of writable workspaces

Filesystem-writing operations SHALL require an explicit absolute caller-owned workspace. HML-controlled results, temporary files, logs, receipts, caches and locks SHALL stay in its `build/` tree. Relative workflow operands SHALL resolve against that workspace. Runtime resources SHALL come only from the immutable installed package, independent of invocation directory or nearby checkout. Read-only operations SHALL need no workspace.

#### Scenario: Generate with a read-only installation
- **Verification:** read-only installation subprocess run, before/after hashes and filesystem write audit.
- **WHEN** installed HML validates, prepares and builds in an explicitly selected workspace different from its invocation directory
- **THEN** all HML state, receipts and generated outputs stay within that workspace's allowed build runs
- **AND** the package tree remains byte-identical, with no lock, cache, generated script or output written into site-packages
- **AND** no Git checkout or project configuration is created or required.

#### Scenario: Invoke the same pipeline from unrelated directories
- **Verification:** installed subprocess matrix with unset PYTHONPATH, read-only invocation directories, misleading checkout-shaped siblings and filesystem snapshots.
- **WHEN** the same installed workflow is invoked from two unrelated directories with identical explicit workspace and workflow operands
- **THEN** it selects the same resources, resolves the same paths and applies the same validation and ownership rules without reading neighboring checkout files
- **AND** no HML-controlled state is created in the invocation directory, installation, neighboring checkout or global temporary directory
- **AND** relative file operands resolve from the workspace; absolute external inputs remain read-only and outputs remain confined after resolving symlinks
- **AND** path escapes or writes through escaping symlinks fail before output creation or backend spawn.

### Requirement: Runtime integrity uses distribution-owned identity

Prepared-input and output evidence SHALL identify the installed package version, logical resource hashes and implementation identity without requiring development lock files or Git. Existing canonical prepared-content hashing SHALL remain enforced. Mismatched sources, altered content and stale render reuse SHALL fail closed; distribution identity SHALL NOT replace numerical or visual acceptance.

#### Scenario: Verify and reject prepared identities
- **Verification:** same-wheel relocated-install comparison and tampered/mismatched prepared-input tests.
- **WHEN** the same wheel prepares the same fixtures in two independent installations/workspaces
- **THEN** the logical source/implementation inventory and canonical prepared content hashes agree without embedding installation-specific paths
- **AND** readers verify every declared source hash against the active packaged inventory
- **AND** modified content, mismatched resource identities and incompatible legacy inputs fail with an explicit regeneration instruction
- **AND** accepted historical outputs remain unchanged and remain eligible as read-only inputs for the existing HTML-only presentation mode.

#### Scenario: Preserve fail-closed integrity outside the checkout
- **Verification:** isolated wheel copies with missing/corrupt resources or implementation files, altered prepared content and stale/mismatched predecessor evidence.
- **WHEN** an installed external-workspace workflow encounters altered data or identity while a neighboring checkout contains apparently valid replacements
- **THEN** it fails the affected integrity or reuse check without substituting checkout content or accepting stale output
- **AND** diagnostics identify the failed logical identity and required regeneration without using installation or invocation paths as canonical content identity
- **AND** relocating an unchanged installation or workspace alone does not invalidate otherwise compatible input evidence.

### Requirement: Distribution licenses and provenance are complete

Installed distributions SHALL include project code/data licenses, third-party notices and the used-materials register. Every external source actually used for this change SHALL have verified commercial and derivative permission compatible with its intended use and distribution, including build tools, actions and reference-only materials. Provenance and output attribution SHALL remain resolvable after installation.

#### Scenario: Audit commercial redistribution and output attribution
- **Verification:** archive license inventory, source-clearance audit, provenance validator and generated-attribution comparison.
- **WHEN** the developer adds packaging tools/actions or redistributes existing runtime resources
- **THEN** `docs/used-materials.md` records each actually used external material, exact part/version, source and license URLs, permission basis, conditions, checked date and related outputs, including no-attribution sources
- **AND** Apache-2.0 code, CC-BY-4.0 data and applicable third-party conditions remain distinguishable in installed files and metadata
- **AND** missing, ambiguous, non-commercial, no-derivatives or conflicting permissions block use/distribution until resolved
- **AND** generated packs retain the complete relevant attribution and limitations without fetching references.

### Requirement: CI builds and checks the distributable artifact

Push and pull-request GitHub Actions SHALL build the wheel and source distribution, validate their contents and install the built wheel non-editably in a fresh supported host environment outside the checkout. Successful CI SHALL retain the checked wheel and evidence as downloadable artifacts. Host-only CI SHALL identify its unexecuted real-backend scope and SHALL NOT publish to a package index.

#### Scenario: Check the actual wheel in CI
- **Verification:** workflow inspection and successful GitHub Actions execution linked to the candidate commit.
- **WHEN** the package job runs on a clean checkout
- **THEN** build/version/dependency consistency, runtime and license inventory, source-distribution rebuild parity, dependency consistency and installed command smoke checks all pass before a successful artifact verdict
- **AND** the installed checks run with checkout imports disabled and exercise all canonical source validation and preparation
- **AND** a missing resource, namespace leak, metadata mismatch, failed install or failed smoke command makes the job fail
- **AND** the uploaded wheel checksum, commit, workflow run, interpreter/build-tool versions and scoped results identify exactly the checked artifact
- **AND** existing locked host tests still run and host-only success does not imply real Blender acceptance.

#### Scenario: Prove the installed artifact has no checkout dependency
- **Verification:** CI external installed-workflow matrix and retained machine-readable results tied to the wheel checksum.
- **WHEN** CI validates the non-editably installed wheel
- **THEN** invocation directories and explicitly selected workspaces are outside the source checkout and wheel installation, with checkout imports disabled
- **AND** host coverage includes all-fixture validation/preparation, numeric report writing and available presentation-only modes using controlled evidence
- **AND** missing-workspace, workspace-relative path, write-escape, misleading-neighbor and integrity-tampering cases are exercised
- **AND** assertions prove runtime imports/resources come from the installation and HML writes stay under each caller-selected workspace's build tree
- **AND** synthetic presentation evidence and host-only checks are explicitly distinguished from real Blender and human visual acceptance.

### Requirement: Packaging preserves generation output

Packaging SHALL preserve anatomy, controls, rest policies, contacts, fixed camera/floor/light, mirroring, beat timing and existing render/numeric tolerances. Installed skeleton default, explicit and batch modes retain their source-workflow agreement contract: batch selection/semantics/integrity receive host/source checks, while native default/explicit equivalence is checked at H=1.50 m without requiring batch pixel evidence. Added characters SHALL satisfy their character-models contract. Independent reviewer evidence SHALL compare installed output for skeleton H=1.50 m, male H=1.70 m and female H=1.90 m and include explicit human visual approval before archive. Product batch contracts and the complete installed resource closure remain required; native full-batch pixel parity and same-character cross-stature render comparisons are outside the remaining diagonal acceptance and SHALL be labeled unassessed. Historical pre-change Blender construction and rendered output SHALL NOT be required as a comparison oracle for this change.

#### Scenario: Compare the package regression pack
- **Verification:** numeric comparison, decoded-pixel comparison, timing/link audits and explicit human visual review.
- **WHEN** the reviewer builds the design's neutral/rest and four-beat arm-raise subset twice for each approved diagonal pair from the wheel on the pinned reference backend
- **THEN** each pair's outputs are deterministic and current-candidate source and installed workflows agree on evaluated geometry and decoded render pixels at the same character/stature within the unchanged applicable limits
- **AND** the human receives labeled count/in-between sheets, GIFs, onion-skin overlays and current-candidate source/package comparisons specified in design
- **AND** full-fixture validation/preparation coverage and focused visual coverage are separately reported, without claiming renewed complete anatomical acceptance.

#### Scenario: Generate all characters from an installed artifact
- **Verification:** non-editable wheel pair-scoped API/CLI runs outside the checkout, host batch-contract tests and filesystem/resource audits.
- **WHEN** the approved diagonal pairs are rendered from a read-only installation and complete-registry selection/closure is checked through host tests
- **THEN** character identities, surface topology/binding, exact pose/timeline links, source provenance and expected image inventories agree with the source workflow
- **AND** current-candidate default/explicit skeleton H=1.50 m output agrees exactly on the pinned renderer, while full-batch semantics remain host-checked and native batch pixel parity is reported as unassessed
- **AND** invocation-directory independence, explicit workspace containment, disjoint runs and fail-closed package/render integrity remain enforced
- **AND** host-only CI results remain labeled separately from real Blender numeric/render evidence and human visual acceptance.

### Requirement: Development builds use current library sources

A repository operation that needs current sources SHALL always rebuild and install the library package before preparing or generating results. The package SHALL contain the matching code, data and source records. Contributors SHALL need no manual refresh or import-path setup; existing checks that files match their recorded sources SHALL remain enforced.

#### Scenario: Rebuild after implementation and data edits
- **WHEN** a contributor changes packaged Python code or character/movement data and repeats a supported repository build
- **THEN** the library package is rebuilt and installed before that operation, even when the project version and dependency lock are unchanged
- **AND** new preparation uses the changed code/data and their corresponding recorded hashes
- **AND** unchanged dependencies can be reused without causing old project files to be selected
- **AND** source files and installed files are not hand-edited to manufacture matching records
- **Verification:** disposable Python/YAML edit controls, build/install order observations and source/package/prepared-file hash comparison.

#### Scenario: Keep earlier results tied to their original sources
- **WHEN** a rebuilt package differs from a previously prepared input or result
- **THEN** existing checks reject the mismatched input or result reuse before Blender starts
- **AND** old files and their source records remain unchanged; only newly prepared results identify the rebuilt package
- **AND** installed packages work independently of the checkout and need no runtime downloads
- **Verification:** exact-package external-work-directory check, old-input/reuse failure controls and source/installation write audit.

### Requirement: Package production has a complete default route

The repository SHALL provide one package command without mandatory arguments that prepares its tools, builds wheel and source archives, compares rebuilding from the source archive and checks the built library in a clean installation. It SHALL report artifacts and check scope without publishing or requiring caller-managed output paths.

#### Scenario: Produce a distributable package from a clone
- **WHEN** a contributor invokes `make package` with supported host prerequisites and no prepared tools or results
- **THEN** current wheel/source archives and a check report appear in a fresh automatically chosen owned run
- **AND** rebuilding from the source archive produces the same runtime files and bytes as the direct package build
- **AND** version, tool/source checks and bounded input preparation work with the exact built package independently of checkout imports
- **AND** the command needs no Blender and claims no Blender/visual acceptance
- **AND** publishing remains a separate existing checked release process
- **Verification:** literal clean-checkout package command, archive file/hash comparison and clean installed-package checks with stated scope.

#### Scenario: Stop before distributing an unchecked result
- **WHEN** package build, source-archive comparison or installed-package checks fail
- **THEN** the command exits nonzero and reports the failed stage and diagnostic evidence
- **AND** no overall verified-package result or publication is recorded
- **Verification:** stage failure controls and unchanged source/lock and out-of-scope result hashes.
