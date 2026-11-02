# host-python-runtime Specification

## Purpose

Define the supported Python environment for running HML on the host and the evidence that distinguishes host compatibility from Blender backend compatibility.

## Requirements

### Requirement: HML selects one supported host Python minor

HML SHALL support standard CPython 3.14 as its host interpreter. Declared requirements, repository version selection and active setup instructions SHALL agree on this minor and exclude other minors from supported locked setup. Blender's embedded interpreter SHALL remain outside this host constraint.

#### Scenario: Select the supported host
- **Verification:** configuration audit and executed interpreter assertion in a fresh locked environment.
- **WHEN** a contributor follows the documented default setup
- **THEN** the interpreter running HML reports CPython with major/minor `(3, 14)`
- **AND** project and lock metadata require `>=3.14,<3.15` and the repository version selector requests `3.14`
- **AND** the resolved interpreter patch version and executable are recorded with verification evidence.

#### Scenario: Reject an unsupported host selection
- **Verification:** version-constraint checks and a locked setup attempt with an explicitly selected Python 3.12 or 3.13 interpreter.
- **WHEN** locked setup is explicitly requested with a host interpreter outside the supported minor
- **THEN** setup fails rather than producing a supported HML environment or silently selecting a different requested interpreter
- **AND** acceptance checks establish that 3.12, 3.13 and 3.15 do not satisfy the declared support interval.

### Requirement: Locked host dependencies reproduce a usable environment

The committed dependency lock SHALL resolve consistently with the host Python requirement. Fresh locked setup SHALL install HML's declared dependencies without rewriting project requirements or the lock. Dependency changes SHALL be justified by Python 3.14 compatibility, lock consistency or the approved installable-distribution/build contract, and all installed direct dependencies SHALL import successfully. Wheel installation SHALL resolve the declared runtime dependencies without a checkout lock; contributor setup SHALL continue to use the committed lock.

#### Scenario: Recreate the host environment from the committed lock
- **Verification:** clean-environment locked sync, dependency consistency/import checks and before/after file hashes.
- **WHEN** setup is performed from the committed requirements and lock with host Python 3.14
- **THEN** locked dependency installation succeeds, the environment passes dependency consistency checks, and YAML, JSON Schema and image-processing dependencies import
- **AND** requirements and lock bytes remain unchanged by setup and subsequent checks
- **AND** the report identifies installed dependency versions and explains any differences from the previous lock.

#### Scenario: Install complete runtime dependencies from the wheel
- **Verification:** fresh non-editable wheel install, dependency consistency/import checks and metadata audit.
- **WHEN** the built wheel is installed into a fresh CPython 3.14 environment
- **THEN** YAML, JSON Schema, the directly imported schema-registry API and image-processing dependencies are declared directly and import successfully
- **AND** build-only tools are separated from runtime requirements and the installed version agrees with source/build metadata
- **AND** installed validation and environment inspection need no repository version selector or lock file
- **AND** contributor locked sync installs the actual project package and the lock remains fresh.

### Requirement: Host checks retain existing HML behavior

The migration SHALL preserve source validation, numerical tolerances, prepared-input integrity, sampling and supervised-process behavior under host Python 3.14. Compatibility fixes SHALL correct observed failures without weakening checks or changing pose, segment, motion, body group, controls, rest policy, contact or beat contracts.

#### Scenario: Verify the complete host scope
- **Verification:** actual host-only unittest execution and source validator result with test totals and named exclusions.
- **WHEN** the host checks run on Python 3.14 without real Blender
- **THEN** every discovered test outside the explicitly classified real-backend modules executes, including synthetic process supervision, wrapper and presentation tests
- **AND** errors, failed tests, discovery/import failures and an empty selected suite produce a failing result
- **AND** any skipped test and excluded backend scope are reported explicitly
- **AND** canonical source validation succeeds without changing source data or acceptance tolerances.

### Requirement: CI enforces the host environment contract

Pull-request and push CI SHALL execute the supported host interpreter, validate version-selection consistency, check and install the committed lock without regeneration, validate canonical sources and run the complete host-only test scope. It SHALL expose failures and identify the backend scope excluded from that job.

#### Scenario: Run the host job from a clean checkout
- **Verification:** workflow inspection and one successful CI execution, with failing-path assertions for version mismatch, stale lock and failed host tests.
- **WHEN** CI checks a candidate commit
- **THEN** it asserts the actual HML interpreter is Python 3.14, verifies metadata agreement and lock freshness, and executes validation and the host suite
- **AND** a wrong interpreter, stale lock, failed validation or failed host test prevents job success
- **AND** the job does not install or substitute a different Blender to make host checks pass
- **AND** its status is explicitly scoped to host checks rather than full backend acceptance.

### Requirement: Blender compatibility is verified independently

The host migration SHALL preserve the pinned Blender executable version, build and reference platform. Blender SHALL use its own embedded Python without a host-version equality requirement or host-environment injection. Full acceptance SHALL include successful real backend tests through the existing supervised path and report host and embedded interpreter identities separately.

#### Scenario: Run the complete suite on the reference backend
- **Verification:** independent complete unittest discovery, pinned executable probe, embedded-interpreter observation and supervised receipts on the reference platform.
- **WHEN** the migrated HML host is checked on Darwin arm64 with the pinned Blender
- **THEN** complete test discovery succeeds, including the real backend geometry/repeatability and injected scene-fault modules without exclusion or skip
- **AND** Blender version/build pins and existing numerical acceptance bounds remain unchanged
- **AND** evidence records the host Python 3.14 identity and the Python version actually supplied by Blender as distinct observations
- **AND** an unavailable or mismatched backend leaves backend acceptance incomplete rather than converting host-only success into a complete verdict.

#### Scenario: Preserve visual contracts if a compatibility correction affects rendering
- **Verification:** affected-scope audit; if triggered, deterministic decoded-pixel comparison and explicit human visual review.
- **WHEN** compatibility fixes change scene/render behavior or shared code affecting visible output
- **THEN** the focused neutral/rest and four-beat arm-raise acceptance pack defined in design is generated from sources through the supervised backend and reviewed before archive
- **AND** fixed camera/floor/light, beat timing, static/animation agreement and existing numerical limits remain enforced
- **AND** a host-only migration that does not affect visible output records why a new visual gate is inapplicable rather than claiming a new anatomical acceptance verdict.

### Requirement: Repository goals start from a clean checkout

Make SHALL provide package-building and development-preparation commands without mandatory arguments from a clean checkout. Each SHALL prepare its tools and report its result without shell activation, system Python, manual setup or caller-managed paths. Development preparation SHALL check current library sources and readiness, while describing the remaining result-building and acceptance steps.

#### Scenario: Follow the documented initial routes
- **WHEN** a contributor clones the repository, enters it and runs `make package` or `make dev` with the documented system prerequisites
- **THEN** the chosen route prepares its tools, installs the built HML package and completes its declared stages in order
- **AND** Python 3.14 and dependency versions come from project settings and the committed lock, which remain unchanged
- **AND** no manual cache export, Python choice, `uv sync` or output-path argument is required
- **AND** development output states completed readiness checks and available result-building/checking actions with their actual scopes
- **Verification:** independent literal clean-checkout routes, preparation logs, standard tool checks and unchanged configuration/lock hashes.

### Requirement: Workflow defaults are project-owned

Committed configuration SHALL define or derive ordinary cache, tool, work/output path, version and recipe defaults. Make SHALL apply them consistently and document optional overrides. Default generated state SHALL remain in owned project build locations, avoid personal machine paths and require no caller environment-variable setup.

#### Scenario: Use defaults and an intentional override
- **WHEN** default routes run from a checkout path containing spaces, or an operator uses a documented optional override
- **THEN** every subprocess uses the resolved settings consistently and logs show effective paths/versions
- **AND** required project caches and generated files are not written into a global cache or authoring directories
- **AND** invalid or escaping destinations fail before affected results change
- **Verification:** effective-setting/log checks, space-path walkthrough, override/failure controls and before/after filesystem comparison.

### Requirement: Prerequisites distinguish host tooling from rendering

Initial guidance and Make help SHALL state required system utilities, supported platforms and network/cache needs for each goal. uv SHALL manage Python and its dependencies. Blender SHALL be required only for operations that invoke it; a missing or incorrect pinned Blender SHALL give an actionable error rather than be replaced.

#### Scenario: Diagnose a new machine
- **WHEN** a required system utility or goal-specific Blender prerequisite is missing or unsupported
- **THEN** help or the invoked command names the requirement, expected version and documented installation/configuration remedy
- **AND** package-building and development-preparation commands work without Blender and report no Blender acceptance
- **AND** no system-level install, permission bypass or dependency-lock rewrite occurs
- **Verification:** missing-utility/version/Blender controls and package/dev routes without Blender.

### Requirement: Contributor command guidance is audited as executable workflows

The audit SHALL map supported tools, guides and CI to repository goals, requirements, side effects and acceptance scope. It SHALL fix reasonable command-coordination and instruction problems, and record each remaining gap with its cause, affected goal and next action. Matrix previews SHALL not be presented as the whole development workflow.

#### Scenario: Audit the supported command surface
- **WHEN** dev and reviewer assess preparation, validation, result building, checking, presentation, host/package tests and read-only release tools
- **THEN** every supported operation has bounded command evidence or a named deferred/controlled check, and contradictory instructions are reconciled
- **AND** defaults do not invent movement content, guess external inputs or silently start expensive acceptance work
- **AND** unresolved movement/Blender/release issues have evidence and a scoped next action
- **Verification:** design's command/result mapping, runnable guides, controlled command/failure tests and concrete gap records.

### Requirement: Cleanup needs no prepared Python tools

Make SHALL expose argument-free `mostlyclean`, `clean` and `distclean` with their requirements and fixed removal areas in help. Cleanup SHALL work with only the documented shell and basic system utilities, without preparing Python, installing packages, downloading tools or requiring caller-managed paths.

#### Scenario: Clean an unprepared or damaged checkout
- **WHEN** a contributor invokes any cleanup target with no project environment, uv, Python or Blender, or with damaged project tools
- **THEN** cleanup removes all selected contents, including unknown files and local history, and reports removed paths and pending failures without preparation or generation
- **AND** absent selected output is treated as already clean, and unchanged source/configuration/lock files require no repair
- **Verification:** literal Make calls with controlled PATH, absent/damaged tools, repeated calls, space-path cases and filesystem/process observations.
