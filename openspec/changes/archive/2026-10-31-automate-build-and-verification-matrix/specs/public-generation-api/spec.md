# Spec Delta

## MODIFIED Requirements

### Requirement: API execution preserves installation and workspace boundaries

The API SHALL enforce explicit absolute workspace, write-containment, disjoint input/output, immutable-package and existing supervised-backend contracts. Resource and executable discovery SHALL remain independent of the invocation directory. Standalone calls SHALL retain fresh flat-run defaults. A narrow explicit matrix-destination binding SHALL permit generation into declared preparation and render content within one stable matrix result root; this binding SHALL not add a package, process or execution-plan protocol.

#### Scenario: Use an installed API from an unrelated directory
- **Verification:** non-editable installed package, unrelated invocation directory and existing path/immutable-resource tests.
- **WHEN** preparation and rendering target an explicit caller workspace from an unrelated directory containing misleading checkout-shaped neighbors
- **THEN** resources come from the installed package and all HML state is inside the workspace's permitted build tree
- **AND** relative operands resolve against the workspace, returned paths are absolute and independent input/output runs remain disjoint after symlink resolution
- **AND** standalone calls reject missing/relative workspace, invalid run names, occupied destinations, overlap and symlink escape before allocating state or launching Blender
- **AND** probe/build/render retain backend pins and existing supervision, cancellation and environment-boundary rules.

#### Scenario: Write a selected matrix result directly
- **Verification:** public API destination mapping and two sequential matrix builds with original receipt paths.
- **WHEN** the thin matrix runner explicitly binds a stable five-component result root and its fixed preparation/render destinations
- **THEN** the API validates containment, nonsymlink paths and producer input/output separation before writing
- **AND** generation writes directly to those content paths and returns original evidence for those paths
- **AND** the runner may clear its previous declared result before a complete repeat while preserving logs and unrelated content
- **AND** an explicitly requested but incomplete, foreign, escaping or overlapping binding fails before backend work; omitting matrix mode retains standalone fresh-run defaults.
