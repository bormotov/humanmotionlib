# character-models Specification

## Purpose
Provide independently selectable humanoid characters that share canonical skeletal motion and reusable surface construction, so common library changes propagate coherently without duplicated animation sources.

## Requirements

### Requirement: Remaining real-backend acceptance uses the approved diagonal

Remaining developer and independent reviewer real-backend acceptance SHALL cover exactly `skeleton` H=1.50 m, `male` H=1.70 m and `female` H=1.90 m with the approved diagnostics, applicable numerical/contact bounds, focused visual coverage and repeatability. Other supported pairs SHALL remain supported and be reported as unassessed. Source/host product contracts SHALL remain tested.

#### Scenario: Verify the exact diagonal scope
- **Verification:** independently generated pair reports, aggregate identity/coverage checks and negative input tests.
- **WHEN** the three approved character/stature pair reports are aggregated
- **THEN** a diagonal numeric pass requires all three successful applicable leaf checks, matching candidate package/backend/canonical source and diagnostic definitions with only declared stature scaling
- **AND** missing, duplicate, wrong-character, wrong-height, stale, mismatched or failed members prevent a successful aggregate
- **AND** the report enumerates required, observed and unassessed pairs and distinguishes diagonal numeric completeness from rendering, repeatability and human acceptance
- **AND** it does not claim a complete character/stature cross-product, native same-character cross-stature equivalence or complete-character batch pixel parity.
- **AND** source/host selection, scaling, propagation, batch-integrity and API/CLI checks retain their product coverage without requiring the excluded native/render cross-product.

#### Scenario: Review only the selected live pairs
- **Verification:** pair-scoped source/package/API/CLI comparisons, two clean render passes per pair and explicit human visual review.
- **WHEN** the current candidate's three selected pairs are independently rendered and presented
- **THEN** corresponding images are compared only within the same character/stature pair, and each pair's repeated decoded pixels agree exactly on the pinned backend
- **AND** skeleton default and explicit selection agree at H=1.50 m
- **AND** the pack labels every pair and discloses the excluded six pairs and unperformed native batch/cross-stature comparisons
- **AND** a mixed-character/mixed-height overview is not described as a same-height silhouette or same-character scaling comparison.

### Requirement: Characters are first-class selectable library outputs

HML SHALL provide the stable character IDs `skeleton`, `male` and `female` at the same public selection level. Skeleton SHALL be a complete character, require no body surface, and remain the default. Character definitions SHALL have explicit identities, compatible profile references, descriptions, licenses and provenance.

#### Scenario: Select each character independently
- **Verification:** installed API/CLI matrix, source validation and scene inventory.
- **WHEN** the same prepared movement is rendered separately with each registered character
- **THEN** each produces its own explicitly identified usable character images and saved-scene collection
- **AND** skeleton succeeds without parsing or instantiating a surface template and has no invented surface provenance
- **AND** omitted selection produces skeleton with the existing image paths and expected views.

### Requirement: Character definitions are canonical declarative sources

Character registry, descriptors, shared surface template, binding contract and appearance presets SHALL be versioned schema-validated repository data, reconstructible without GUI state or a downloaded/generated source asset. Invalid or incompatible definitions SHALL fail before output allocation or backend launch.

#### Scenario: Reconstruct and reject character data
- **Verification:** clean-source reconstruction and schema/semantic fault matrix with write/process interception.
- **WHEN** a selected definition has duplicate IDs, unknown fields, unsupported constructors, nonfinite/nonpositive dimensions, unresolved carriers, cyclic references, missing provenance or a profile/bind mismatch
- **THEN** validation identifies the character, source and offending field before creating successful output
- **AND** character data cannot introduce action tracks, root compensation, camera overrides or executable expressions.

### Requirement: All current characters share skeletal movement semantics

The three characters SHALL use identical skeletal proportions, joint centers, rest transforms, rig controls and solved movement for a given preparation. Character choice SHALL NOT alter actions, rest policies, contacts, body-group ownership, world root, timing, mobility limits or mass-model selection.

#### Scenario: Compare the common movement across characters
- **Verification:** complete fixture/consumer-source host comparison and frame identities; native skeletal checks use the approved diagonal only.
- **WHEN** host/source evaluation resolves the same prepared diagnostics or consumer motion for all three character selections at the same stature and BPM, without a native render of that cross-character set
- **THEN** pose/sample/timeline identities and skeletal action/frame/contact data agree under unchanged existing tolerances
- **AND** male/female appearance never implicitly selects sex-specific mass coefficients or reference mobility observations
- **AND** changing appearance does not rewrite or duplicate a movement definition.

### Requirement: Surface variants reuse one construction and binding contract

Male and female SHALL derive from one shared surface template and binding contract, with differences expressed by declarative appearance parameters. Common topology, stable vertex identities and normalized carrier weights SHALL be shared. Each surface SHALL remain distinguishable from rigid skeletal geometry and controls.

#### Scenario: Verify surface sharing and separate inspection
- **Verification:** source-dependency audit, generated topology/weight comparison and saved-scene inspection.
- **WHEN** both surfaces are reconstructed from clean sources
- **THEN** component/vertex/face identities and weight assignments match exactly, while rest coordinates follow their approved presets
- **AND** skeleton geometry, body surfaces and controls can be inspected independently
- **AND** no copied male/female movement tree, auto-weight result or hand-edited generated mesh is a source of truth.

### Requirement: Shoulder surfaces form connected smoothly bound junctions

Each surface character SHALL have connected torso-to-arm shoulder junctions that deform continuously from the common posed skeleton. Both appearances SHALL share the same junction topology and weighting rules. The shoulder correction SHALL preserve the approved neck direction and leave other joint designs and skeletal movement unchanged.

#### Scenario: Verify connected shoulder construction
- **Verification:** indexed-edge adjacency, connectivity, rest-coordinate and weight comparisons; native/reference deformation checks after early acceptance.
- **WHEN** male and female surfaces are reconstructed at a supported stature
- **THEN** torso and both arms belong to one connected closed mesh with shared junction vertices, no internal shoulder caps, no duplicate seam vertices and exactly two oppositely directed incident triangles per edge
- **AND** the two appearances share exact vertex/face identities and weights, with left/right reflection and the declared carrier-influence bounds
- **AND** vertices and faces outside the declared shoulder replacement retain their R3 rest geometry, weights and materials, including neck termination, distal arms and lower body.

#### Scenario: Inspect shoulder shape through movement
- **Verification:** one bounded identified preview and explicit human visual inspection; subsequent independent full coverage remains separate.
- **WHEN** the connected shoulder result is shown in neutral, rest and the complete representative arm raise
- **THEN** the human can judge the shoulder-to-torso transition, upper-arm height, axilla and neck together in fixed full views and matched R3/new crops
- **AND** the junction remains continuous under finite normalized weights, with stable topology, no collapsed triangles or disconnected seams, using the common keyed animation
- **AND** the model is described as an authored skinning approximation, without claims of muscle/skin simulation or pose-dependent remeshing
- **AND** expensive verification waits for explicit acceptance of this new preview identity.

#### Scenario: Refine angular shoulders without changing the shared movement
- **Verification:** local density/connectivity/weight and preservation measurements, fixed-scene comparison preview and explicit human decision.
- **WHEN** the human requests more surface points after reviewing the connected shoulder direction
- **THEN** both surface characters gain the same denser locally smoothed shoulder topology with conforming shared boundaries and smooth shading
- **AND** the refined envelope stays within the design's declared rest-shape deviation bound while preserving the readable neck and unchanged non-shoulder surfaces, skeleton and keyed movement
- **AND** additional points produce actual local curvature rather than merely dividing the same flat faces, and normalized mirrored binding deforms the junction continuously
- **AND** the new preview identifies its new package/render identity and acceptance remains pending until an explicit human decision; prior partial improvement is not acceptance.

#### Scenario: Retain a readable shoulder line with lowered arms
- **Verification:** canonical neutral contour measurements, exact topology/weight and preservation checks, bounded fixed-scene comparison and explicit human visual decision.
- **WHEN** the human reports excessive rounding after local shoulder refinement
- **THEN** the shared upper shoulder shape presents the design's shallow shoulder plateau in the arms-down neutral pose while retaining a smooth outer transition to the upper arm
- **AND** the same dense connected topology and weights deform the revised canonical rest surface throughout the common arm raise, with no per-frame shape correction, altered skeletal motion or new animation control
- **AND** neck, lower shoulder boundary, distal arms and all other components preserve their previous rest geometry and weights outside the declared upper-shoulder correction
- **AND** partial improvement does not accept the new identity or release expensive verification without an explicit human decision.

#### Scenario: Repair the confirmed orientation and shoulder mirror defects
- **Verification:** complete component directed-edge checks, ancestry-based reflected geometry/topology/weight comparisons and focused positive/negative controls; bounded identified before/after preview and explicit human decision.
- **WHEN** the 2026-11-05 approved correction reconstructs either surface character
- **THEN** every component is a closed consistently oriented manifold, including both leg cap fans, and each undirected edge has exactly two oppositely directed incident triangles
- **AND** the complete left shoulder bridge, including its seam vertices and edges, has reflected coordinates, triangle connectivity and carrier-swapped weights corresponding to the canonical right bridge under stable seam/endpoint ancestry, within the existing 1e-12 canonical mirror tolerance; unselected seam-transition faces retain their original surface, material and orientation under the design's preservation checks
- **AND** the design's explicit preservation boundary, six-component inventory, torso/regional counts and existing shape/deformation/contact limits hold; no tolerance waiver or anatomical/movement change substitutes for the repair
- **AND** one fresh before/after preview shows male H1.70 and female H1.90 in neutral, rest, the complete arm-raise and complete squat at BPM90 with fixed full views and relevant shoulder/leg details
- **AND** full suites, dense audits, native acceptance, repeated clean renders and the independent final pack wait for explicit acceptance of that new preview; the earlier R6 acceptance and failed host suites retain their original identities and scope.

### Requirement: Authored appearance has a frozen testable dossier

The body surfaces SHALL conform to the approved numerical silhouette, topology, material and deformation dossier in this change's design. The two appearances SHALL be original stylized exercise mannequins, explicitly identified as authored approximations rather than measured or universal male/female anatomy.

#### Scenario: Measure and visually identify the authored characters
- **Verification:** independent rest-vertex/ring measurements and explicit human visual review.
- **WHEN** source construction is checked at supported statures and the approved live pairs male H=1.70 m and female H=1.90 m are generated
- **THEN** control-ring coordinates and extrema match the frozen dossier within 1e-5H for native vertices, with uniform stature scaling
- **AND** independently measured waist/hip slices preserve the dossier's distinct silhouettes within 1e-4H
- **AND** matte opaque suit/body regions, plain head and grouped mitten hands follow the dossier without external texture/model assets
- **AND** the human separately judges whether silhouettes read as the intended characters and body junctions remain visually continuous.

#### Scenario: Correct the rejected shoulder presentation
- **Verification:** focused source/identity comparison, bounded early preview and explicit human visual decision, followed by identity-bound independent acceptance.
- **WHEN** the male/female shoulder surfaces are revised after the human's visual rejection
- **THEN** both present a continuous upper-torso/shoulder/upper-arm envelope without an apparently elevated detached arm-root peg in neutral, rest and the representative arm raise
- **AND** the correction preserves a readable narrow neck transition to the head without a broad upper-torso collar swallowing the neck, and both shoulder and neck appearance are judged together in the fresh preview
- **AND** the correction preserves the shared skeletal joint centers and movement, lower-body appearance and fixed scene, while torso/leg-junction redesign remains deferred
- **AND** a fresh identified preview receives explicit early human acceptance before expensive verification resumes, and historical results retain their original candidate identities.

### Requirement: Surface deformation follows the common posed skeleton

Visible surfaces SHALL deform from explicit finite normalized carrier weights and canonical rest transforms without stretching the skeleton or adding motion controls. Native evaluated surfaces SHALL agree with the independent deformation reference within 1e-5H. Missing, stale or forged evaluated evidence SHALL fail verification.

#### Scenario: Verify deformation throughout existing movement coverage
- **Verification:** full native delivered-vertex comparison, additional native key-interval midpoints and dense reference checks.
- **WHEN** all packaged diagnostics are evaluated for male H=1.70 m and female H=1.90 m under the approved diagonal scope
- **THEN** surface evidence reports per-character/sample worst residuals, finite vertices, stable topology and triangle areas greater than 1e-12H squared
- **AND** weights sum to one within 1e-12 in canonical expansion and 1e-6 natively, with no unresolved or unsupported influence
- **AND** coupled shoulder, forearm, knee and forefoot behavior reaches the surface through the existing posed carriers
- **AND** native, dense-reference and visual coverage are reported separately, without claiming that surface deformation is rigid or anatomically measured.

### Requirement: Supporting surfaces preserve contact and floor constraints

Character surfaces SHALL respect the existing fixed floor and skeletal contact intent. Every evaluated surface vertex SHALL remain at or above -1e-4H. During a declared heel/ball support, the visible sole SHALL remain within 1e-3H of the actual posed contact anchor; unchanged skeletal target/sliding bounds SHALL also apply.

#### Scenario: Check the sole beyond a rest-pose appearance
- **Verification:** native full-vertex bounds, dense surface audit at spacing at most 0.01 beats and independent anchor-to-sole measurements.
- **WHEN** every diagnostic, key/contact event and delivered sample is checked for male H=1.70 m and female H=1.90 m under the approved diagonal scope
- **THEN** floor bounds apply to the complete surface without hiding offending vertices or substituting intended targets
- **AND** planted squat/walking feet and rolling forefoot support satisfy both skeletal-contact and visible-sole conditions
- **AND** a failure reports character, component/vertex or anchor, beat, measured residual and bound
- **AND** moving the camera/floor/root, changing movement intent or clamping surface vertices cannot conceal a failure.

### Requirement: Character rendering preserves deterministic fixed-scene output

Character rendering SHALL preserve the shared fixed camera, floor, lights, projection, resolution and beat sampling. A character rendered alone or in a batch SHALL have identical decoded pixels for the same sample/view on the pinned reference backend. Independent repeated builds SHALL reproduce topology, surfaces and images within the stated bounds.

#### Scenario: Compare singleton, batch and repeated output
- **Verification:** native reconstruction and exact decoded-pixel repeatability for each selected pair, plus host batch/visibility/identity contract tests.
- **WHEN** the focused acceptance set is rendered twice independently for each approved diagonal pair
- **THEN** each pair's corresponding decoded images match exactly and canonical topology/weight identities agree
- **AND** native rest/posed vertices agree within 1e-6H between runs
- **AND** fixed scene/selection isolation and complete-character batch integrity remain covered by source/host checks; native complete-character batch pixel parity is explicitly unassessed in this reduced acceptance
- **AND** current-candidate skeleton default and explicit output at H=1.50 m have identical evaluated geometry within existing limits and exact corresponding decoded pixels; historical pre-change Blender output is not required.

### Requirement: Common library changes propagate through the registered set

HML SHALL support one registry-driven regeneration/check operation for the complete character set using shared preparation. The suite report SHALL identify common and per-character source identities and complete membership. A missing or failed member SHALL prevent a complete successful suite verdict.

#### Scenario: Demonstrate single-source edits and isolated appearance edits
- **Verification:** controlled source-copy propagation tests and complete suite-report audit.
- **WHEN** valid disposable test copies change one shared movement key, one shared surface-radius parameter, or only the female waist parameter
- **THEN** the movement change reaches all three characters through the same solved poses
- **AND** the common surface change reaches both surfaces with the declared preset multipliers while skeleton geometry/poses stay unchanged
- **AND** the female-only change alters only its surface closure/vertices, not male, skeleton or movement identity
- **AND** no canonical/installed source or production exercise is modified by these technical tests.

### Requirement: Bind-significant skeletal changes require coherent compatibility renewal

Surface compatibility SHALL identify the skeletal rest/hierarchy/attachment contract used for binding. A bind-significant change SHALL invalidate stale surface bindings until intentionally renewed and checked across every dependent character. Source identity SHALL distinguish skeletal profile, template, binding and appearance.

#### Scenario: Reject a stale bind instead of drifting silently
- **Verification:** disposable source-copy rest-transform mutation and dependency-identity assertions.
- **WHEN** a shoulder rest transform changes without renewing the surface compatibility record
- **THEN** both surface definitions fail compatibility before generation rather than following an obsolete bind
- **AND** skeleton remains governed by its own source validation and does not require a surface to be generated
- **AND** documented future renewal regenerates all dependent surfaces together; this change supplies no alternate skeletal proportions or retargeting claim.

### Requirement: Appearance and future body proportions remain separate concerns

Character data SHALL distinguish skeletal profile, reusable surface template and appearance preset. Current characters SHALL retain the common profile. Unsupported body-type/proportion selections SHALL fail rather than be silently mapped to a sex-specific skeleton or movement.

#### Scenario: Inspect the extension boundary
- **Verification:** schema/dependency inspection and unsupported-selection tests.
- **WHEN** a caller requests an unimplemented athletic/body-type or alternate-proportion character
- **THEN** the request fails explicitly with no output or implicit fallback
- **AND** documentation explains that future skeletal shoulder/pelvis width changes require compatible binding and per-profile motion/contact evaluation, whereas additional appearances can reuse the current rig
- **AND** current character names impose no future mass, mobility or skeletal-proportion assumptions.

### Requirement: Character provenance and reference clearance remain resolvable

Every character source SHALL carry description, license and provenance, and outputs SHALL preserve the union of character and inherited skeletal/movement attribution. Every external material actually used SHALL have verified commercial/derivative/distribution clearance and a complete used-materials entry before use.

#### Scenario: Audit original surfaces and inherited attribution
- **Verification:** nested provenance traversal, installed register/license inventory and developer/reviewer source audit.
- **WHEN** an authored surface result is inspected outside the checkout
- **THEN** the template/preset authorship is distinct from adapted skeletal/mobility sources, with all referenced register entries resolvable
- **AND** any external reference or asset actually used records exact material/part, source/license URLs, permission basis, conditions, checked date and outputs, including no-attribution materials
- **AND** missing, ambiguous, NC, ND or incompatible permission blocks use and cannot be replaced by a public URL.

### Requirement: Independent character review precedes visual acceptance

An independent reviewer SHALL rebuild character evidence from canonical sources, report requirement/scenario failures and produce the design's complete visual comparison pack in its own build run. Numerical success SHALL NOT imply human visual acceptance. A visual-affecting character change SHALL NOT be archived before the human accepts the pack.

#### Scenario: Review the shared character set
- **Verification:** independent clean review, pack inventory/link audit and explicit human decision.
- **WHEN** implementation is submitted for review
- **THEN** the pack compares skeleton/male/female under the same scene, including neutral/rest, arm raise, squat, walking, deformation/sole details, exact timing, GIFs and onion-skin overlays defined in design
- **AND** all-fixture native/dense checks, focused visual coverage, repeatability, inherited licensing and suite completeness are separately identified
- **AND** cleanup records removed paths/bytes, retained reasons, dependency/link checks and pending work without deleting accepted/protected history or another agent's active run
- **AND** visual rejection remains unresolved until revised sources receive renewed independent evidence and explicit acceptance.
