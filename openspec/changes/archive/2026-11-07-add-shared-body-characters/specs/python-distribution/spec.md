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
