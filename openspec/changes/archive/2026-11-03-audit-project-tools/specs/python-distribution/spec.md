# Spec Delta

## ADDED Requirements

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
