# joint-mobility Specification

## Purpose

Provide explicit, testable joint mobility and coordinated skeletal articulation so exercise diagnostics can distinguish supported natural movement from impossible or unsupported poses.

## Requirements

### Requirement: Explicit joint action model

Every articulation SHALL declare anatomical actions, local axes, neutral-to-rest offsets, degrees of freedom, and whether a channel is independent, coupled, or fixed. Clinical action angles SHALL be in degrees and distinct from quaternion components or Blender Euler channels. Missing actions SHALL NOT become unrestricted rotations implicitly.

#### Scenario: Inspect the required action inventory
- **WHEN** a mobility profile is validated
- **THEN** it includes the following minimum action model on both sides where applicable

| Region | Required action model |
|---|---|
| Glenohumeral joint | Three bounded rotational degrees of freedom, distinct from total arm elevation |
| Shoulder girdle | Explicit clavicular and scapular articulation coordinated with arm elevation; dependent channels identified |
| Elbow | One primary flexion/extension degree of freedom; additional motion only through declared coupling |
| Radioulnar complex | One pronation/supination degree of freedom, distinct from elbow flexion and wrist rotation |
| Wrist | Two bounded rotational degrees of freedom for flexion/extension and radial/ulnar deviation |
| Hip | Three bounded rotational degrees of freedom |
| Knee complex | Primary flexion/extension with an explicit model of dependent tibial and patellar movement |
| Ankle and hindfoot | Separate dorsiflexion/plantarflexion and inversion/eversion actions, with their anatomical axes and dependencies |
| Forefoot | A declared toe/forefoot flexion-extension articulation supporting foot roll |
| Cervical, thoracic, and lumbar regions | Distributed flexion/extension, lateral flexion, and axial rotation with region-specific limits |
| Pelvis/root | Declared body placement channels, distinct from physiological joint mobility |

- **AND** jaw, individual finger motion, and individual toe motion outside the declared forefoot articulation are fixed or explicitly grouped and listed as unsupported controls
- **AND** fixed structures remain present in the skeletal inventory where required by `anatomical-skeleton`

#### Scenario: Check axis directions independently of the backend
- **WHEN** a small positive action is applied about each declared action axis
- **THEN** measured landmark displacement has the declared anatomical direction on both sides
- **AND** the report identifies the axis frame and neutral offset
- **AND** mirroring preserves action names, rather than applying identical Euler signs indiscriminately

#### Scenario: Verify absolute anatomical directions
- **WHEN** hip external rotation of 20 degrees is applied from anatomical neutral
- **THEN** the anterior foot direction turns laterally on each side (positive X on the right, negative X on the left)
- **WHEN** elbow flexion is 90 degrees and the forearm moves from assembly supination `p=-80` to clinical midrotation `p=0`
- **THEN** the radial/thumb direction points upward on both sides, and increasing pronation turns the palm toward the floor
- **WHEN** a neutral thigh undergoes 30 degrees knee flexion with its required dependent twist
- **THEN** the anterior tibial direction turns medially (negative X on the right, positive X on the left)
- **AND** independent geometric direction assertions reject the previous opposite-sign transforms even if a solver and its angle decoder agree with one another

### Requirement: Reference mobility and supported limits are distinct

The profile SHALL preserve sourced reference mobility separately from operational action limits and diagnostic targets. Reference cohort means SHALL NOT be labeled individual maxima or safety thresholds. Every supported action SHALL have finite bounds and explicit conditions; unreferenced channels SHALL fail profile acceptance rather than inherit a generic range.

#### Scenario: Preserve the initial reference observations
- **WHEN** the reference dataset is inspected
- **THEN** the following adult observations from `faisal-2019-joint-monitoring`, Table 3, ages 20–44, remain identifiable as reported mean magnitudes in degrees

| Action | Female mean | Male mean |
|---|---:|---:|
| Hip extension | 18.1 | 17.4 |
| Hip flexion | 133.8 | 130.4 |
| Knee flexion | 141.9 | 137.7 |
| Knee extension beyond neutral | 1.6 | 1.0 |
| Ankle dorsiflexion | 13.8 | 12.7 |
| Ankle plantarflexion | 62.1 | 54.6 |
| Total shoulder flexion | 172.0 | 168.8 |
| Elbow flexion | 150.0 | 144.6 |
| Elbow extension beyond neutral | 4.7 | 0.8 |
| Forearm pronation | 82.0 | 76.9 |
| Forearm supination | 90.6 | 85.0 |

- **AND** the profile does not silently average sexes or combine this mobility cohort with the proportion cohort as if they described one measured person
- **AND** total shoulder motion is not assigned entirely to the glenohumeral joint

#### Scenario: Freeze the complete mobility dossier before implementation
- **WHEN** design and specifications reach the first human approval gate
- **THEN** the planning artifacts provide numerical minimum and maximum action angles, action composition order, neutral definitions, reference locators, and conditional constraints for every supported articulation
- **AND** they define numerical curves or bounded reference samples for shoulder-girdle coordination, forearm articulation, spinal distribution, knee/patellar articulation, and foot roll
- **AND** each approximation has a rationale, limitations, and numerical comparison tolerances
- **AND** wrist, spinal, shoulder-girdle, hip off-sagittal, hindfoot, and forefoot values absent from the initial reference table require additional cleared evidence
- **AND** no implementation begins with placeholders or evidence still delegated to the implementer

### Requirement: Joint limits are validated without silent correction

Validation SHALL distinguish valid, unsupported, out-of-range, and unsatisfied-constraint states. It SHALL report joint, action, measured value, allowed bounds or coupling condition, and fixture time. Validation SHALL NOT silently clamp a pose, change its target, stretch bones, or move the floor to obtain a pass.

#### Scenario: Check boundaries of an independent action
- **WHEN** an action is sampled at its lower bound, midpoint, upper bound, and `0.5 degrees` beyond either bound with other conditions satisfied
- **THEN** bound and interior samples pass within `0.1 degrees` measurement tolerance
- **AND** both outside samples fail with their measured values and bounds
- **AND** boundary evaluation does not confuse quaternion sign equivalence or angle wrapping with a different anatomical pose

#### Scenario: Reject unsupported knee motion
- **WHEN** an input commands `10 degrees` of independent knee varus/valgus or bypasses a required dependent channel
- **THEN** it is rejected as unsupported even if all quaternion values are mathematically valid
- **AND** no generated diagnostic frame is reported as valid from that input

#### Scenario: Report an unreachable contact target
- **WHEN** a declared foot target cannot be satisfied with the profile's rigid structure and mobility bounds
- **THEN** the result fails with contact and joint residuals
- **AND** the requested target and limits remain visible in the failure report

### Requirement: Coupled motion is observable and constrained

Coupled articulation SHALL be measured against the approved mobility dossier throughout its supported domain. Shoulder elevation SHALL involve the declared shoulder girdle; pronation/supination SHALL articulate radius and ulna; knee motion SHALL include dependent tibial/patellar behavior; torso motion SHALL be distributed across spinal regions. Independent axis boxes alone SHALL NOT prove coupled anatomical validity.

#### Scenario: Verify coupled reference samples
- **WHEN** each coupling is evaluated at its approved reference samples and intermediate inputs
- **THEN** dependent transforms and anatomical landmarks agree with the dossier's numerical bounds
- **AND** a pose with individually permitted angles but a violated coupling condition fails
- **AND** freezing a required dependent structure, such as the scapula or patella, causes a verification failure

#### Scenario: Verify continuity through the diagnostic domain
- **WHEN** a supported diagnostic is evaluated at every delivered animation time and additional steps no greater than `0.01 beats`
- **THEN** coupling conditions and mobility limits hold at every sample
- **AND** there are no discrete quaternion-branch jumps or discontinuous dependent transforms
- **AND** the maximum position and orientation changes are reported against the dossier's declared continuity bounds

#### Scenario: Preserve thoracic attachments during motion
- **WHEN** spinal and shoulder diagnostics are evaluated at delivered times and dense steps no greater than `0.01 beats`
- **THEN** each rib follows its named vertebra rigidly and the sternum follows T1 rigidly, with existing rigid-dimension tolerances preserved
- **AND** sternal SC landmarks remain within `1e-4 H` of their corresponding SC joint centers
- **AND** cartilages 1–7 terminate at the current posed rib tips and named sternal insertions, while 8–10 terminate at the preceding cartilage's current solved middle control, all within `1e-4 H`
- **AND** every cartilage middle control satisfies the dossier's endpoint-midpoint and co-rotating offset rule within `1e-4 H`
- **AND** guide dependencies are evaluated in acyclic order; cycles, missing references, cross-side links, duplicate writers, and binding-driven deformation of rigid ribs or sternum fail validation
- **AND** binding lower guides to rigid bony tips or retaining undeformed guide controls fails independent posed-closure checks even if joint angles and rigid-body transforms pass

### Requirement: Diagnostic sources are explicit and reusable

Diagnostic poses and sequences SHALL be schema-validated repository data with descriptions, provenance, beats, controlled body groups, rest policies, and declared contacts. They SHALL use the same canonical skeleton and keyed animation for static and animated views. Procedural noise and follow-through SHALL be disabled. Their storage contract SHALL be fixed in design before implementation.

#### Scenario: Inspect a diagnostic fixture
- **WHEN** the fixture set is validated
- **THEN** it contains named rest and anatomical-neutral poses, individual action sweeps, a squat, forward arm raising, and walking in place
- **AND** it identifies these sequences as authored verification exercises rather than measured gait or a production motion library
- **AND** left/right variants are generated by mirroring
- **AND** each sequence declares controlled groups and leaves all other channels governed by an explicit rest policy

### Requirement: Squat diagnostic exercises balance and planted feet

The squat SHALL follow the approved four-beat R3 dossier with 90-degree bottom knee flexion, planted feet and controlled pelvis, torso, legs and arms. Static balance plausibility SHALL be checked using the whole-body mass model and measured support hull independently of contact success. The positive ankle operating bound SHALL be 20 degrees; sourced cohort observations remain unchanged.

#### Scenario: Verify a complete squat
- **WHEN** the squat is sampled on the reference skeleton
- **THEN** both knees reach `90 ± 2 degrees` at beat 2, with ankle dorsiflexion 20 degrees, pelvis pitch 25 degrees and lumbar flexion 10 degrees, without exceeding any mobility or coupling condition
- **AND** standing at beats 0 and 4, descent through beat 1 and ascent through beat 3 follow the approved interpolation
- **AND** pelvis height decreases and returns, while both feet satisfy declared contacts
- **AND** no horizontal root drift is introduced and the final pose matches the initial pose within `0.1 degrees` and `1e-4 H`
- **AND** controlled channels include `pelvis`, `torso`, `leg_L`, and `leg_R`, plus any arm groups positioned by the fixture
- **AND** the torso and pelvis are not frozen merely to satisfy a legs-only mask

#### Scenario: Measure squat static balance independently
- **WHEN** the revised squat is checked at every delivered time and existing dense sample on H=1.50/1.70/1.90 m
- **THEN** weighted COM from all 16 actual carrier-bound mass observations projects into the measured flat-contact XY convex hull with reference margin at least 0.010H
- **AND** the minimum margin across reference/male-weight/female-weight variants minus the 0.005H placement allowance is at least 0.005H
- **AND** masses represent the whole body including unrendered tissues, not equal bone weights or skeletal mesh volume
- **AND** source values, COM XYZ, support vertices, edge margins, variants, uncertainty bound, units, beat and image references are retained
- **AND** missing/degenerate support, missing/forged mass evidence or failed margin causes failure regardless of valid joint angles, pins and floor checks
- **AND** the report labels this static plausibility for an approximate body, not dynamic balance validation at animation tempos

#### Scenario: Reject the former squat despite planted feet
- **WHEN** the former 12-degree ankle/pelvis squat is evaluated with the approved mass model at its 90-degree knee bottom
- **THEN** measured balance fails because estimated COM falls behind the support hull, even if original foot pins, joint limits and floor checks pass
- **AND** an intact-foot posterior upper-body fault also fails the balance requirement
- **AND** omitting/zeroing/equalizing mass weights, forging observations or substituting intended support targets cannot conceal the failure

### Requirement: Arm-raising diagnostic exercises shoulder coordination

Forward arm raising SHALL last four beats: anatomical-neutral arms at beat 0, upward movement at beat 1, total elevation `160 ± 2 degrees` at beat 2, lowering at beat 3, and neutral at beat 4. Both arms and their shoulder girdles SHALL participate; elbow flexion SHALL remain within `2 degrees` of extension. Feet SHALL remain planted.

#### Scenario: Verify arm elevation without torso compensation
- **WHEN** the arm-raising diagnostic is evaluated
- **THEN** both arms reach the total elevation target with the dossier's shoulder-girdle coordination
- **AND** trunk and pelvis orientations remain within `1 degree` of their initial values and horizontal root position within `1e-4 H`
- **AND** glenohumeral and total elevation are reported separately
- **AND** the final pose closes within `0.1 degrees` and `1e-4 H`

### Requirement: Walking-in-place diagnostic alternates support

The walking-in-place diagnostic SHALL last eight beats and return to its starting pose. The left leg SHALL swing during beats 0–2 and the right during beats 4–6; the opposite foot SHALL support each swing. Each swing SHALL reach at least `0.02 H` sole clearance and `45 degrees` knee flexion. Arm swing SHALL oppose the swinging leg. Horizontal root translation SHALL remain fixed.

#### Scenario: Verify the alternating stepping cycle
- **WHEN** the eight-beat diagnostic is evaluated
- **THEN** each swing contains at least one sample meeting the clearance and knee-flexion targets
- **AND** both feet are fully planted during beats 2–4 and 6–8
- **AND** support changes, lift-off, touchdown, and any heel/toe contact phases have explicit beat boundaries and anchor points in the approved fixture dossier
- **AND** foot-roll and forearm action sweeps are included separately if their full supported articulation is not exercised by this stepping cycle
- **AND** final pose and horizontal root position close within `0.1 degrees` and `1e-4 H`
- **AND** the pack calls this walking in place and does not claim it validates forward gait or muscle-driven balance

### Requirement: Contact and floor measurements

Contact intent SHALL identify foot-local anchor points, world-space targets, and beat intervals using meters in canonical space. Targets SHALL scale with stature. Contacts SHALL be checked against solved geometry independently of solver success flags. Declared floor contacts SHALL have at most `1e-3 H` target error and horizontal sliding; visible geometry SHALL NOT penetrate below `-1e-4 H`.

#### Scenario: Measure planted and rolling foot support
- **WHEN** a flat-foot contact interval is checked
- **THEN** heel, medial forefoot, and lateral forefoot anchors are each measured against their fixed targets throughout the interval
- **AND** rolling support pins only the explicitly declared heel or forefoot anchors without incorrectly pinning a lifted part of the foot
- **AND** every interval endpoint is evaluated with its declared contact state; intervals use `[start,end)` and the final sequence endpoint uses the terminal declared state
- **AND** a failed contact measurement fails the diagnostic regardless of visual appearance

### Requirement: Diagnostic timing and stable rendering

Diagnostics SHALL use one beat per count and verify BPM `60`, `120`, and `180`. Static samples SHALL occur at count boundaries. Each full beat SHALL have `n = max(3, ceil((60 / BPM) / 0.2))` equal animation intervals. Every diagnostic event and segment boundary SHALL lie on the delivered frame grid; fractional events require an explicit allocation rule approved in design.

#### Scenario: Verify samples from the same animation
- **WHEN** a four-beat diagnostic is rendered at BPM 60, 120, and 180
- **THEN** it yields five static samples and respectively 21, 13, and 13 animation samples, counting each endpoint once
- **AND** each adjacent count pair has at least two in-between frames and no interval longer than `200 ms`
- **AND** static and animation transforms at shared times agree within `0.1 degrees` and `1e-4 H`
- **AND** sequence timing changes playback speed without changing beat-relative geometry

#### Scenario: Verify rendering stability and determinism
- **WHEN** a diagnostic is rendered twice from clean state using identical sources and pinned versions
- **THEN** camera, floor, lights, resolution, and projection are identical across its frames and both runs
- **AND** the review pack includes front and side contact sheets, animation GIFs, and onion-skin overlays with floor and contact markers
- **AND** squat review provides separate COM/support overlays and unannotated views with the R3 static-plausibility label and signed margin, and preserves the preceding rejected pack
- **AND** decoded image pixels match exactly between runs on the declared reference renderer and platform
- **AND** no camera reframing or floor movement conceals drift, penetration, or clipping

### Requirement: Diagnostic HTML supports direct navigation and paired comparison

Every diagnostic HTML page SHALL provide consistent horizontal, wrapping navigation to all sibling diagnostics and the index, with the current page identified. Each BPM's labeled front and side animation previews SHALL share a row at viewport widths >=1024 CSS pixels and stack front first below that width. Existing review links SHALL remain available.

#### Scenario: Navigate across the complete diagnostic set
- **Verification:** static link validation and browser inspection.
- **WHEN** every generated diagnostic page is inspected
- **THEN** its navigation contains the same ordered diagnostic identifiers as the pack index, with valid local destinations
- **AND** the complete set includes neutral/rest pages, main exercise diagnostics and every isolated action sweep
- **AND** it contains a pack-index link and exactly one current-page marker
- **AND** any diagnostic can be reached directly from any other diagnostic, including movement back to an earlier item
- **AND** links remain visible and usable when the navigation wraps

#### Scenario: Compare both animation views at each BPM
- **Verification:** static content validation, browser geometry measurements and human visual review.
- **WHEN** every diagnostic page is inspected at 1024 and 1200 CSS pixels wide
- **THEN** its 60, 120 and 180 BPM front/side previews share a row in front-then-side order
- **AND** each pair belongs to one labeled BPM section, with explicit Front and Side labels
- **AND** each existing paired preview variant, including squat COM/support previews, follows the same arrangement
- **AND** existing image, static/animation sheet, onion-skin overlay and exact-timestamp links remain available
- **WHEN** the same pages are inspected at 390 CSS pixels wide
- **THEN** the previews stack front first and the navigation and preview components fit the available width without clipping or causing horizontal overflow

### Requirement: Verification report and human visual gate

Independent review SHALL report per-joint action coverage, limit and coupling checks, contact residuals, rigid-structure invariants, root drift, mirror and loop error, timing, and render repeatability. The report SHALL distinguish numerical acceptance from human judgments of anatomical plausibility and movement readability. No visual-affecting change SHALL be archived without human approval of its review pack.

#### Scenario: Review a completed implementation
- **WHEN** independent verification reconstructs the skeleton and diagnostics from repository sources
- **THEN** `review.md` references each violated requirement and scenario, and links the pack under `build/review/anatomical-human-skeleton/`
- **AND** every supported action has valid, boundary, invalid, and visual coverage; every coupled relation has valid and invalid coverage
- **AND** incomplete reference evidence, missing checks, or unresolved numerical failures prevent an acceptance verdict
- **AND** the human can approve or reject visual naturalness after inspecting the numeric results and images

#### Scenario: Verify a presentation-only derivative
- **Verification:** independent source/media hash audit and browser review.
- **WHEN** only diagnostic HTML navigation or layout changes
- **THEN** generated HTML is independently regenerated and checked in a fresh presentation output directory
- **AND** provenance identifies the original numeric/render snapshot and the new presentation-generator snapshot separately
- **AND** original media bytes, timing records, numeric evidence and their recorded hashes remain unchanged
- **AND** the original numeric verdict is explicitly scoped to its original snapshot and renewed presentation verification covers the revised HTML
- **AND** the human visual gate remains pending until the human explicitly accepts the presented pack

## Reference basis

- `kudzia-2022-body-segments`: Pawel Kudzia, Erika Jackson and Genevieve Dumas (2022), original Proposed mass/pCOM columns of Tables 3 and 6, CC BY 4.0. [Article](https://doi.org/10.1371/journal.pone.0262296). Cohort blending and skeletal-point placement are explicit approximations.
- `kasahara-2024-squat-com`: Satoshi Kasahara et al. (2024), discussion/conclusions on coordinated COM control, CC BY 4.0. [Article](https://doi.org/10.5114/jhk/183066). No clinical or joint-angle target is copied.


- `hands-on-anatomy-2024`: Phillips and O'Hara, *Hands-on Anatomy*, authored anatomical-action, skeletal-landmark, and ROM-assessment text, chapters 1–9. CC BY 4.0; no permission-only figures are used. [Publisher](https://temple.manifoldapp.org/projects/hands-on-anatomy).
- `openstax-1e-thoracic-cage`: OpenStax first-edition section 7.4 text, retained under CC BY 4.0 by LibreTexts, informs cartilage attachment topology only. The T1 sternum carrier and posed guide interpolation are authored animation approximations, not measured thoracic mechanics. [Section and license notice](https://med.libretexts.org/Bookshelves/Anatomy_and_Physiology/Anatomy_and_Physiology_1e_(OpenStax)/Unit_2:_Support_and_Movement/07:_Axial_Skeleton/7.04:_The_Thoracic_Cage).
- `faisal-2019-joint-monitoring`: Abu Ilius Faisal et al., *Monitoring Methods of Human Body Joints: State-of-the-Art and Research Challenges*, Sensors 19(11), 2629 (2019), Table 3 adult mean observations. CC BY 4.0. [Published article](https://pmc.ncbi.nlm.nih.gov/articles/PMC6603670/). This supplies reference observations, not the missing coupled-motion curves or all action bounds.

Diagnostic amplitudes, durations, numerical tolerances, and the decision to exclude hyperextension from exercise targets are authored acceptance choices, not medical guidance or claims of universal physiological limits. Exact remaining profile values and coupling bounds belong in the approval-ready dossier required above.
