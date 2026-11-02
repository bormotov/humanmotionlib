# Spec Delta

## MODIFIED Requirements

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

### Requirement: Packaging preserves generation output

Packaging SHALL preserve anatomy, controls, rest policies, contacts, fixed camera/floor/light, mirroring, beat timing and existing render/numeric tolerances. The installed skeleton default SHALL retain its baseline; added characters SHALL satisfy their character-models contract. Independent reviewer evidence SHALL compare installed output and include explicit human visual approval before archive.

#### Scenario: Compare the package regression pack
- **Verification:** numeric comparison, decoded-pixel comparison, timing/link audits and explicit human visual review.
- **WHEN** the reviewer builds the design's neutral/rest and four-beat arm-raise subset twice from the wheel on the pinned reference backend
- **THEN** clean skeleton outputs are deterministic and match the baseline geometry and decoded render pixels within the unchanged applicable limits
- **AND** the human receives labeled count/in-between sheets, GIFs, onion-skin overlays and baseline/package comparisons specified in design
- **AND** full-fixture validation/preparation coverage and focused visual coverage are separately reported, without claiming renewed complete anatomical acceptance.

#### Scenario: Generate all characters from an installed artifact
- **Verification:** non-editable wheel API/CLI runs outside the checkout, real backend suite and filesystem/resource audits.
- **WHEN** one shared preparation is rendered with each character individually and the full registered set from a read-only installation
- **THEN** character identities, surface topology/binding, exact pose/timeline links, source provenance and expected image inventories agree with the source workflow
- **AND** default/explicit/batch skeleton output preserves the baseline, and surface singleton/batch output agrees exactly on the pinned renderer
- **AND** invocation-directory independence, explicit workspace containment, disjoint runs and fail-closed package/render integrity remain enforced
- **AND** host-only CI results remain labeled separately from real Blender numeric/render evidence and human visual acceptance.
