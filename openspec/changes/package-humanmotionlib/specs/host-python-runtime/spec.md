# Spec Delta

## MODIFIED Requirements

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

