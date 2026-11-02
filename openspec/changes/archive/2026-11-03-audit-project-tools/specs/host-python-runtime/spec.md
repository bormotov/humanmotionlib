# Spec Delta

## ADDED Requirements

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
