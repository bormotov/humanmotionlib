# python-distribution Specification

## Purpose

Deliver the supported HML generation workflow as a dependency-complete Python distribution whose installed code and resources work independently of the source checkout.

## Requirements

### Requirement: Distribution identity and namespace are explicit

The installable distribution SHALL be named `humanmotionlib`, expose its implementation under `humanmotionlib.*`, and report one consistent release version through package metadata, Python and the command line. Version `0.2.0` SHALL identify this namespace migration. The wheel SHALL NOT install a top-level `tools` package.

#### Scenario: Install and identify the wheel
- **Verification:** clean non-editable wheel install, metadata/import assertions and namespace inventory.
- **WHEN** the wheel is installed on supported CPython in an environment without the checkout on its import path
- **THEN** `humanmotionlib` imports from that installation and metadata, Python version reporting and `hml --version` all report `0.2.0`
- **AND** installing HML introduces no `tools` namespace and no dependency on checkout script paths
- **AND** active documentation maps former imports and commands to their installed replacements and labels the compatibility break.

### Requirement: Supported generation resources are complete

The wheel and source distribution SHALL contain the complete HML-owned resource closure for the supported anatomical skeleton diagnostics. Installed validation, preparation, construction, numeric verification and review presentation SHALL require no checkout, Git state, runtime download or pre-generated asset. Canonical data bytes and existing diagnostic coverage SHALL be preserved.

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

The namespace and resource migration SHALL preserve anatomy, controls, rest policies, contacts, fixed camera/floor/light, mirroring, beat timing and existing render/numeric tolerances. Independent reviewer evidence SHALL compare the installed workflow with the pre-migration baseline and include an explicit human visual gate before archive.

#### Scenario: Compare the package regression pack
- **Verification:** numeric comparison, decoded-pixel comparison, timing/link audits and explicit human visual review.
- **WHEN** the reviewer builds the design's neutral/rest and four-beat arm-raise subset twice from the wheel on the pinned reference backend
- **THEN** clean outputs are deterministic and match the baseline geometry and decoded render pixels within the unchanged applicable limits
- **AND** the human receives labeled count/in-between sheets, GIFs, onion-skin overlays and baseline/package comparisons specified in design
- **AND** full-fixture validation/preparation coverage and focused visual coverage are separately reported, without claiming renewed complete anatomical acceptance.
