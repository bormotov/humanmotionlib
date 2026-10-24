# Spec Delta

## MODIFIED Requirements

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
