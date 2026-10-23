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

The committed dependency lock SHALL resolve consistently with the host Python requirement. Fresh locked setup SHALL install HML's declared dependencies without rewriting project requirements or the lock. Any dependency change SHALL be justified by Python 3.14 compatibility or lock consistency, and all installed direct dependencies SHALL import successfully.

#### Scenario: Recreate the host environment from the committed lock
- **Verification:** clean-environment locked sync, dependency consistency/import checks and before/after file hashes.
- **WHEN** setup is performed from the committed requirements and lock with host Python 3.14
- **THEN** locked dependency installation succeeds, the environment passes dependency consistency checks, and YAML, JSON Schema and image-processing dependencies import
- **AND** requirements and lock bytes remain unchanged by setup and subsequent checks
- **AND** the report identifies installed dependency versions and explains any differences from the previous lock.

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
