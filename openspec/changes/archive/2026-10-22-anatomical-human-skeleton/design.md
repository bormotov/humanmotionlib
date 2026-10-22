# Design: Anatomical human skeleton

## Context

See `proposal.md` for motivation and the two capability deltas for acceptance behavior. There is no existing canonical skeleton, runtime toolchain, or published data-model specification to migrate. The local Blender executable reports **5.2.2 LTS**, build `d13f752e3b9c`; this becomes the reference build, not an implicit dependency on an application path.

This document is the numerical dossier required by the specifications. Tables and formulas below define the complete initial profile, including authored approximations. A formula defines all its indexed instances; implementers must not choose missing coordinates, ranges, coupling curves, or diagnostic amplitudes. Approval means accepting this documented animation approximation, not asserting population-wide or clinical validation.

Revision state (2026-10-22): the approved R3 squat revision has been implemented and independently reproduced with PASS WITH NOTES for its recorded source snapshot. Human visual gate 2 remains pending for thorax and squat. The human confirmed the four-artifact presentation planning refinement on 2026-10-22. The HTML-only refinement below requires separate implementation and independent presentation verification; it does not reopen the approved numerical dossier or extend the old verdict to revised HTML. Preserve all earlier results as historical source-specific evidence.

## Goals / Non-Goals

**Goals:** Separate anatomical bodies, joint intent, backend controls, and humanoid semantic mapping; make the entire profile reconstructible and quantitatively inspectable; retain stable local attachment frames for later muscles.

**Non-Goals:** Predict forces, tissue mechanics, pain-free movement, individual anatomy, or forward gait. Do not import an unverified anatomical mesh, motion capture recording, MPFB character, or third-party rig. The production pose/segment/motion and export schemas remain separate changes.

## Decisions

### 1. Use a generated anatomical rig with explicit approximation metadata

Use repository-authored procedural skeletal meshes, rigid transforms, and explicit joint coupling. Native Blender bones are a backend representation. Geometry is rigidly attached to anatomical bodies; only named cartilage/connection guides are non-rigid. Use separate `Anatomy`, `Controls`, `Humanoid`, and `Review` collections.

**Alternatives:** MPFB/Rigify would supply human-surface and animation conveniences, but does not itself supply this anatomical dossier and would add asset licensing and version dependencies. A downloaded scan or atlas would require additional source clearance and retopology. A stick skeleton would fail the visible-anatomy requirement. None is a dependency of this design.

The profile is `adult-reference-v1`, with `description`, `license: CC-BY-4.0`, and provenance per source record. Geometry parameters not taken from a measurement are labeled **A: authored approximation**. A is an explicit status, not a claim that the value was measured or anatomically validated. Its purpose is an inspectable reference body consistent with the declared landmarks and joint mechanics. Human review can reject its proportions or shapes before implementation approval.

Evidence identifiers used below resolve in `docs/used-materials.md`:

| ID used here | Register identifier | Portion actually used |
|---|---|---|
| H | `hands-on-anatomy-2024` | Authored skeletal-landmark/action text, chapters 1–9; no figures |
| O | `openstax-1e-thoracic-cage` | Retained CC BY 4.0 first-edition section 7.4 text: Sternum, Parts of a Typical Rib, Rib Classifications; no figures or measured contours |
| W | `wang-2024-segment-lengths` | Adult DXA Table 1 and mechanical-axis definitions |
| F | `faisal-2019-joint-monitoring` | Table 3, adult reference means already preserved in the spec |
| M | `moromizato-2016-rom` | Table 1, passive wrist/hip/shoulder/trunk observations and measurement context |
| S | `beczkowska-2022-spine-rom` | Table 3, regional spinal reference ranges |
| B | `bang-2025-shoulder-rhythm` | Section 2.1, approximate humerus/scapula coordination during abduction |
| P | `yu-2019-patellar-kinematics` | Sections 3.2–3.6 and 4.3, tracking trends and coordinate sensitivity |
| A | `brockett-chapman-2016-ankle` | Motion axes and ROM text, printed pp. 234–235; no figures |
| T | `tovaruela-2025-hallux` | Introduction, MTP dorsiflexion and its role in terminal stance |
| R | `parallel-manipulator-2024-wrist` | Table 2, reported wrist deviation reference ranges |
| K | `kudzia-2022-body-segments` | Original Proposed columns, Tables 3 and 6: segment mass means and limb proximal COM fractions; no illustrations/code |
| Q | `kasahara-2024-squat-com` | Discussion and conclusions on coordinated ankle/hip/knee COM control; no adopted angle targets |
| V | `three-vrm-humanoid-vocabulary` | MIT-licensed bone-name and required-name constants |

All numerical rules are profile-specific. Referencing several studies does not imply their participants form a single measured subject. The profile does not replace anatomical range variability with a universal hard stop.

### 2. Establish one transform convention and a neutral assembly pose

Use the canonical space, quaternion order, and multiplication semantics in `anatomical-skeleton`. In this document, positions are multiples of stature `H`, angles are degrees, and `Rx`, `Ry`, `Rz` are active right-hand rotations about the named axes. Matrix products act rightmost first. `Rot(u,a)` is rotation about unit vector `u`. Implementations convert to radians only inside trigonometric calculations.

The coordinate tables describe the **neutral assembly pose**, with arms down, elbows and knees extended, palms anterior, and feet anterior. The canonical **rest T-pose** is obtained by the exact shoulder algorithm below at elevation 90 degrees in the lateral plane, with all other assembly actions unchanged. Compute `q_rest` and rest-local translations from this solved T-pose, not by setting clinical angles to zero. To serialize a solved pose, use `q_delta = inverse(q_rest) * q_local_solved`.

For every anatomical body with endpoints `a,b`, its neutral geometry basis is:

1. `y = normalize(b-a)`.
2. Project anterior `(0,1,0)` perpendicular to `y` and normalize as `z`; if its norm is below `1e-8`, project superior `(0,0,1)` instead.
3. `x = normalize(y cross z)`; replace `z` by `x cross y`.

Use the identity anatomical action frame at each neutral joint; its axes inherit the proximal body's rotation. Convert action rotations to body-local quaternions through the explicit basis change. Thus anatomical action frames and Blender's bone-longitudinal Y axes are distinct. Bodies without a shaft use identity bases; scapulae use the orthonormal frame from their three listed landmarks. Bone roll is never chosen by a Blender default.

For mirroring, use `J = diag(-1,1,1)`, `p' = Jp`, and `R' = JRJ`. Mirrored geometry bases are `B' = JB diag(-1,1,1)`. Swap side identifiers, reverse triangle winding, and recompute outward normals. No negative object/bone scale is retained.

**Alternative:** Using backend Euler channels as clinical angles would make rotation order and mirrored limits depend on the scene and is rejected.

### 3. Freeze the neutral coordinate and geometry dossier

Right-side coordinates below have positive X. Generate the left side by mirroring. All A entries are authored reference-body dimensions informed by H's anatomical relationships, not extracted measurements. Nominal coordinate/size conformance is `1e-4 H`; W segment ratios retain their stricter `1e-6 H` tolerance. These are construction tolerances, not biological confidence intervals.

#### Main landmarks

| Stable landmark | Neutral coordinate `(X,Y,Z)/H` | Basis / rationale |
|---|---|---|
| `world.origin` | `(0,0,0)` | A; midpoint of ankle projections on floor |
| `pelvis.origin` | `(0,0,0.4895)` | A; ankle height plus W thigh and shank lengths |
| `hip.R` | `(0.055,0,0.4895)` | A; symmetric hip spacing `0.110 H` |
| `knee.R` | `(0.055,0,0.2555)` | W thigh length `0.2340 H` |
| `ankle.R` | `(0.055,0,0.0400)` | W shank length `0.2155 H` |
| `sacrum.base` | `(0,-0.008,0.530)` | A; pelvis-to-spine anchor |
| `pelvis.asis.R` | `(0.080,0.025,0.535)` | A; anterior iliac landmark |
| `pelvis.psis.R` | `(0.060,-0.035,0.535)` | A; posterior iliac landmark |
| `pelvis.crest.R` | `(0.085,0,0.555)` | A; upper iliac extent |
| `pelvis.ischium.R` | `(0.045,-0.015,0.455)` | A; inferior pelvic landmark |
| `pelvis.pubis.R` | `(0.020,0.035,0.470)` | A; anterior lower landmark |
| `sternum.top` | `(0,0.018,0.795)` | A; superior manubrial midsurface anchor, thoracic revision below |
| `sternum.bottom` | `(0,0.059,0.665)` | A; xiphoid midsurface tip, thoracic revision below |
| `sc.R` | `(0.012,0.018,0.790)` | A; sternoclavicular articulation |
| `ac.R` | `(0.100,0,0.800)` | A; acromioclavicular articulation |
| `shoulder.R` | `(0.105,0,0.800)` | A; glenohumeral center |
| `scapula.medial.R` | `(0.035,-0.045,0.790)` | A; blade medial corner |
| `scapula.inferior.R` | `(0.070,-0.045,0.700)` | A; blade inferior corner |
| `elbow.R` | `(0.105,0,0.6395)` | W upper-arm length `0.1605 H` |
| `wrist.R` | `(0.105,0,0.5030)` | W forearm length `0.1365 H` |
| `skull.base` | `(0,0,0.875)` | A; head/neck junction |
| `skull.top` | `(0,0,1.000)` | A; stature endpoint |
| `skull.chin` | `(0,0.035,0.880)` | A; face orientation and lower extent |

The neutral hip/knee/ankle centers define mechanical limb lengths; mesh bounding-box lengths must not replace them. Pelvic breadth, neck size, and head dimensions are independent A choices and do not claim support from W.

#### Spine and attachment hierarchy

Create individual vertebral bodies for `L5..L1`, `T12..T1`, and `C7..C1`, in that inferior-to-superior parent order, with the first attached to `sacrum.base`. Index `i` from zero within each row. All formulas are A; H supplies regional identification. They define every center and the authored rest curvature:

| Region / number | Center formula `(X,Y,Z)/H` | Body radii `(lateral,anterior,superior)/H` |
|---|---|---|
| Lumbar / 5 | `(0, 0.012 sin(pi i/4), 0.545 + 0.020 i)` | `(0.017,0.012,0.007)` |
| Thoracic / 12 | `(0, -0.018 sin(pi i/11), 0.645 + 0.014 i)` | `(0.014,0.010,0.005)` |
| Cervical / 7 | `(0, 0.006 sin(pi i/6), 0.815 + 0.009 i)` | `(0.010,0.007,0.003)` |

Each vertebra uses a low-resolution ellipsoid body, a posterior process extending `0.012 H` from its posterior surface with radius `0.002 H`, and paired lateral processes extending `0.006 H`, radius `0.002 H`. The spine's rest-local origins are the listed centers; intervening offsets are preserved by FK. The superior C1 attachment ends at `skull.base`. Sacrum and coccyx are fused visual groups fixed to pelvis, not extra joint controls. Discs and cartilage are identified non-rigid connection guides, not bones whose length can be used to bypass rigid-body checks.

Parent body relationships are: pelvis → sacrum → vertebral chain → skull; thoracic vertebrae → ribs; T1 → sternum; T1 → both SC/clavicles → AC/scapulae → humeri → elbow/ulnae and radii → wrists/hands; pelvis → femora → knee/tibiae and fibulae → ankle/tali → hindfoot → midfoot/metatarsals → MTP/toe groups. Patellae have dependent transforms relative to femora. Clavicle/scapula attachment closure is specified in section 5. The sternum's revised T1 parent preserves its superior SC closure during spinal motion; this is a rigid animation approximation, not a model of breathing or sternocostal joint mechanics.

#### Mesh envelopes and additional landmarks

All parameters in this table are A. Meshes are generated in the body's neutral frame and remain rigid after generation. End-cap/socket overlaps are labeled schematizations; there is no cartilage-contact or bone-collision simulation. Apart from the floor, conformance is checked by landmark/envelope measurements and human inspection rather than a claim of perfect joint-surface congruence.

| Structure | Complete shape parameters / landmark rule |
|---|---|
| Skull, grouped cranial bones | Cranial ellipsoid center `(0,0,0.9475) H`, radii `(0.045,0.0525,0.0525) H`; face block center `(0,0.038,0.915) H`, dimensions `(0.060,0.040,0.070) H`; orbital recess ellipsoids centered at `(±0.018,0.055,0.935) H`, radii `(0.011,0.018,0.009) H`; nasal recess center `(0,0.058,0.918) H`, radii `(0.006,0.012,0.012) H` |
| Mandible, fixed to skull | U-shaped tube through `(±0.028,0.005,0.915) H`, `(±0.025,0.025,0.885) H`, and chin; radius `0.005 H`; omit teeth, middle-ear bones and individual sutures |
| Pelvis | Separate right/left innominate meshes: triangulated shell through hip, ASIS, crest, PSIS, ischium, pubis; shell thickness `0.004 H`; hip socket rim radius `0.014 H`, neck opening radius `0.010 H`; sacrum ellipsoid center `(0,-0.012,0.510) H`, radii `(0.025,0.012,0.025) H`; coccyx tube to `(0,-0.015,0.475) H`, radius `0.003 H`; innominates, sacrum and coccyx are fixed relative to pelvis |
| Rib pairs 1..12 | Rigid tubes of radius `0.002 H`, one pair per Tj, through the five-point curves in the thoracic dossier below; free pairs 11–12 have complete short curved shafts and no anterior connector |
| Sternum and costal cartilages | One rigid thickness-`0.006 H` sternal shell with manubrium/body/xiphoid landmarks; twenty separately labeled non-rigid cartilage guides with radius `0.002 H`; all shape and binding rules are in the thoracic dossier below |
| Clavicle | Rigid S-profile tube from SC to AC, with offsets `+0.004 H` anterior at 1/3 and `-0.004 H` at 2/3; shaft radius `0.004 H`, end radius `0.006 H` |
| Scapula | Triangular blade through AC, medial and inferior landmarks, thickness `0.003 H`; glenoid center at shoulder with rim radius `0.010 H`; spine ridge from medial landmark to AC, radius `0.003 H` |
| Humerus | Shaft between shoulder/elbow with radius `0.006 H`; head sphere radius `0.012 H`; distal condyles centered elbow `±0.008 H` lateral, radius `0.008 H` |
| Ulna and radius | Two bowed shafts in a forearm envelope, ulna medial and radius lateral by `0.005 H` from elbow/wrist centerline in neutral; each radius `0.0035 H`; ulna olecranon extends `0.006 H` proximally and `0.005 H` posteriorly; radial bow offset `0.004 H` lateral at midshaft; end radii `0.005 H`; use the rotation-axis rule in section 5 |
| Femur | Shaft between hip/knee, radius `0.008 H`; head sphere radius `0.014 H`; greater-trochanter landmark hip `+(0.020,0,-0.015) H`; neck connects this landmark to head; distal condyles at knee `±0.010 H` lateral, radius `0.011 H` |
| Tibia and fibula | Tibial shaft follows knee/ankle centers, radius `0.008 H`, plateau half-width `0.014 H`; fibula is lateral by `0.016 H` at its proximal end `0.020 H` below knee and lateral by `0.013 H` at its distal end `0.005 H` below ankle; shaft radius `0.003 H`, end radii `0.005 H`; tibial tuberosity is knee `+(0,0.010,-0.020) H` |
| Patella | Ellipsoid radii `(0.010,0.005,0.013) H`; center is knee `+(0,0.016,0.006) H` in neutral; all subsequent positioning follows section 5 |
| Talus | Ellipsoid center ankle, radii `(0.012,0.018,0.010) H` |
| Calcaneus | Ellipsoid center ankle `+(0,-0.012,-0.022) H`, radii `(0.014,0.028,0.018) H`; bottom at floor in neutral |
| Other tarsals | One labeled fixed midfoot group, ellipsoid center ankle `+(0,0.035,-0.022) H`, radii `(0.021,0.023,0.012) H`; navicular, cuboid, and cuneiforms are recorded as grouped |

Geometry generation uses fixed mesh resolution: ellipsoids 24 longitudes × 12 latitudes; swept shafts 16 radial sides; curved centerlines 16 equal parameter intervals; deterministic named Boolean recesses only for the skull. Triangulation and object ordering are deterministic. Shape-envelope dimensions are measured on evaluated geometry; discrete sampling error must stay inside `1e-4 H`. Render smoothing changes normals, not dimensions.

#### Thoracic dossier: curved ribs, sternum, and costal arch (2026-10-21)

**Evidence and status.** O, section 7.4, identifies the posterior rib head/neck/angle relationships, the three sternal regions and the second-rib sternal-angle insertion, direct costal-cartilage attachments for ribs 1–7, cartilage-to-cartilage attachments for 8–10, and free short ribs 11–12. H chapter 5 supplies complementary palpable sternum/clavicle/rib landmarks. These texts inform topology and terminology only. Every coordinate, thickness, path, inclination, and shape bound below is **A**, an authored animation approximation. Neither a measured adult thorax nor the shape of the user's watermarked comparison illustration is claimed. Nominal conformance remains `1e-4 H`; rigid-body invariance remains `1e-6 H`.

**Rib paths.** Let the unchanged neutral center of Tj be `(0,yj,zj) H` from the spine formulas. Each rib keeps its existing body ID, Tj parent, origin at that center, and identity neutral action basis. In neutral world coordinates divided by H, the right rib's ordered centerline controls are:

1. `P0 = (0.012, yj-0.002, zj)` — paired head landmark, rather than a visible shaft starting at the vertebral centerline.
2. `P1 = (0.60 wj, yj-0.014, zj-0.008)` — posterior rib-angle landmark.
3. `P2 = (wj, (yj+aj)/2, (zj+ej)/2)` — lateral landmark.
4. `P3 = (0.90 wj, aj-0.006, ej+0.006)` — anterolateral landmark.
5. `P4 = (xj, aj, ej)` — bony tip; for 11–12 this is the free tip.

All columns below are dimensionless multiples of H. Expand them to canonical meters and body-local coordinates; do not encode executable formulas in YAML.

| Rib j | wj | xj | aj (tip anterior coordinate) | ej (tip height) | Head-to-tip inferior descent |
|---|---:|---:|---:|---:|---:|
| 1 | 0.045 | 0.022 | 0.024 | 0.783 | 0.016 |
| 2 | 0.058 | 0.030 | 0.039 | 0.759 | 0.026 |
| 3 | 0.070 | 0.035 | 0.047 | 0.739 | 0.032 |
| 4 | 0.079 | 0.038 | 0.053 | 0.719 | 0.038 |
| 5 | 0.085 | 0.041 | 0.057 | 0.699 | 0.044 |
| 6 | 0.089 | 0.043 | 0.058 | 0.681 | 0.048 |
| 7 | 0.090 | 0.046 | 0.057 | 0.663 | 0.052 |
| 8 | 0.087 | 0.052 | 0.052 | 0.650 | 0.051 |
| 9 | 0.081 | 0.057 | 0.041 | 0.641 | 0.046 |
| 10 | 0.071 | 0.054 | 0.027 | 0.635 | 0.038 |
| 11 | 0.057 | 0.050 | 0.007 | 0.627 | 0.032 |
| 12 | 0.040 | 0.033 | -0.002 | 0.615 | 0.030 |

Use interpolating uniform Catmull–Rom with duplicated endpoint controls. For span controls `a,b,c,d` and span parameter t, evaluate `0.5 * (2b + (-a+c)t + (2a-5b+4c-d)t² + (-a+3b-3c+d)t³)`, componentwise. Clamp only the control-point indices when duplicating endpoints; never clamp generated positions. Four spans with 16 equal whole-path intervals include every control exactly at samples 0,4,8,12,16. The existing sixteen-sided tube and deterministic caps remain. Measure the actual evaluated surface as well as the controls: interpolating curves can extend slightly beyond wj, so a control width is not the mesh envelope. Mirror all positions and winding through X=0 as elsewhere in this design. Cylindrical cross sections remain a declared schematization; no flattened cross-section anatomy is claimed.

**Sternal shape.** Keep the `sternum` body and attachment IDs. Its origin is `sternum.top`; derive its body basis from top to bottom using section 2. Replace the capsule by one ruled midsurface strip, with a left/right vertex pair `(±b,y,z) H` for each row below, in superior-to-inferior order. Connect consecutive rows by quads triangulated from the first vertex; use winding facing anterior. Apply the existing shell construction with averaged unit vertex normals and symmetric thickness `0.006 H`, closing the boundary. The table defines midsurface coordinates, not outer-surface extrema. Existing envelope checks must measure the resulting thickness offsets explicitly.

| Sternal level | z/H | y/H | Half-width b/H |
|---|---:|---:|---:|
| Superior manubrium / sternum.top | 0.795 | 0.018 | 0.008 |
| SC level / manubrium | 0.790 | 0.018 | 0.012 |
| Sternal angle / sternum.angle | 0.765 | 0.042 | 0.009 |
| Upper body | 0.745 | 0.050 | 0.010 |
| Middle body | 0.720 | 0.058 | 0.009 |
| Lower body | 0.695 | 0.062 | 0.008 |
| Body–xiphoid junction / sternum.body_end | 0.680 | 0.063 | 0.006 |
| Xiphoid tip / sternum.bottom | 0.665 | 0.059 | 0.002 |

Add paired sternal SC landmarks `(±0.012,0.018,0.790) H` to the sternum. They coincide with the unchanged `sc.R/L` centers on its midsurface side edges. The sternum now follows T1, as do the SC centers before clavicular articulation. Consequently these landmark pairs remain coincident during all diagnostic poses without moving the SC/AC/GH centers or changing the shoulder algorithm. Preserve the three sternal regions as labels within this one rigid body, not additional motion channels. Small cartilage caps and exact joint surfaces remain outside this schematic geometry.

**Costosternal insertions.** Define `S_j` on each side by linearly interpolating y and b along the sternal row table at these heights. Its coordinate is `(±b(z), y(z), z) H`, on the midsurface edge. These are distinct, explicitly named insertion landmarks, not equally spaced fractions between top and bottom.

| Rib j | S_j height/H | Right S_j X/H | S_j Y/H | Meaning |
|---|---:|---:|---:|---|
| 1 | 0.783 | 0.011160 | 0.024720 | Manubrial insertion |
| 2 | 0.765 | 0.009000 | 0.042000 | Sternal angle |
| 3 | 0.746 | 0.009950 | 0.049600 | Upper body |
| 4 | 0.728 | 0.009320 | 0.055440 | Body |
| 5 | 0.710 | 0.008600 | 0.059600 | Body |
| 6 | 0.692 | 0.007600 | 0.062200 | Lower body |
| 7 | 0.681 | 0.006133333333333333 | 0.06293333333333333 | Inferior body near xiphoid junction |

The row interpolation is authoritative over displayed decimal rounding. Cartilages 1–7 run from their rib's P4 to S_j. For 8–10, the endpoint is the **evaluated middle control of the preceding cartilage on the same side**, not a rigid point on the preceding rib. There is no guide for 11–12. The guide IDs and count remain unchanged.

**Guide evaluation.** Each guide has three controls `G0,G1,G2` and the same Catmull–Rom/tube resolution as above (two spans, with G1 at sample 8). At every pose:

- G0 is the posed rigid rib tip P4.
- G2 for 1–7 is the posed sternal insertion S_j; G2 for 8–10 is G1 of already evaluated guide j−1.
- `G1 = (G0+G2)/2 + R_Tj * (0,0.001,-dj) H`, where `dj=0.003` for rib 7 and `0.001` otherwise. R_Tj is the current vertebral world rotation, so the offset co-rotates with the torso. Mirror this complete rule on the left.

Represent these as a closed declarative binding contract in the profile schema: existing rigid-body-local point bindings; references to a specific solved guide control; and an endpoint-midpoint binding with an explicit offset frame/vector. No general expressions, iterative guide solver, or new dependency is introduced. Validate the control and guide dependency graph before construction; reject cycles, invalid indices, missing targets, duplicate writers, cross-side connections, and guide deformation on rigid bodies. Solve endpoints before the local midpoint, and guides in numeric order 1→10 on each side. A guide-control reference resolves its current solved world position, never the undeformed local point or the guide body's rigid frame. Preserve neutral reference controls in the canonical source for auditing; recalculate all bound controls in posed evaluation, including the middle control.

**Shape checks independent of exact-coordinate reconstruction.** In neutral assembly and rest T-pose, measure these authored shape criteria on both sides. They supplement the `1e-4 H` nominal dossier checks and are not biological confidence intervals:

- The complete rib/sternum surface is inside `|X| <= 0.095 H`, `-0.038 H <= Y <= 0.070 H`, and `0.610 H <= Z <= 0.803 H`. The neutral rib/sternum shape is the same in these two poses.
- Rib 1 lateral centerline extent is between `0.040 H` and `0.050 H`; the largest centerline lateral extent among 6–8 is between `0.084 H` and `0.094 H`, at least `0.035 H` larger than rib 1. Do not infer width solely from the named lateral control.
- Each rib angle P1 is at least `0.010 H` posterior to its vertebral center. The first head-to-tip descent is in `[0.014,0.018] H`; descents for 2–7 are in `[0.024,0.056] H` and strictly increase. Report endpoint descent and the corresponding sagittal chord inclination separately; this is not the inclination of every point of a curved rib.
- For each true rib, `max_curve_Y - S_j.Y <= 0.003 H`, and the cartilage's neutral end-to-end anterior displacement `G2.Y-G0.Y >= -1e-4 H`. This is a profile-specific anti-overhang check; it is not a universal claim that real costal cartilage can never curve posteriorly. Whole-cage surface bounds include the shell and cartilage thickness separately.
- Guides 8–10 terminate on the preceding cartilage's solved G1 within `1e-4 H` in every diagnostic sample. Rib 11 and 12 tips have no outgoing cartilage binding. On dense neutral centerline sampling at 1024 equal parameter intervals, the arc-length ratios rib11/rib10 are in `[0.65,0.80]` and rib12/rib11 in `[0.70,0.85]`; the full five-point paths must exist rather than truncating a longer rib at its lateral point.
- Sternal SC landmarks coincide with their named joint centers within `1e-4 H` at every sample. True-rib insertion correspondence includes rib 2 at `sternum.angle`. Dynamic cartilage endpoint and midpoint errors are reported separately; neither successful FK nor a guide's parent transform proves closure.

Retain the rejected three-point, constant-`0.100 H` anterior-offset construction as a negative regression. It must fail overhang/envelope checks; replacing the new 8–10 endpoints by bony tips must fail topology and posed guide-closure checks. Missing metrics cannot pass. Do not alter the camera, spine curvature, global root, shoulder pivots, limb proportions, or motion amplitudes to make these checks pass.

#### Hands and feet

In a neutral hand, use `d=(0,0,-1)` distal, `l=(1,0,0)` lateral on the right, `n=(0,1,0)` palmar. Hand origin is wrist. The carpal group is an ellipsoid at `0.010 H d`, radii `(0.020,0.008,0.010) H` in `(l,n,d)`. For the five rays thumb→little, lateral coordinates are `[0.022,0.012,0,-0.011,-0.020] H`; metacarpal bases are `0.015 H d + lateral*l`. Digit directions are `normalize(d + c*l)` with `c=[0.7,0.08,0,-0.06,-0.12]`. Metacarpal lengths are `[0.030,0.040,0.040,0.038,0.034] H`; total phalange lengths are `[0.035,0.050,0.055,0.050,0.040] H`, divided `[0.60,0.40]` for thumb and `[0.45,0.35,0.20]` for other digits. Shafts have radius `0.002 H`, joints `0.003 H`. All digits are fixed geometry bodies under the hand; the radius/ulna/hand coupling still moves the complete hand. These are A dimensions; no independent finger animation is supplied.

For each foot, the frame is ankle-relative `(l,anterior,superior)`. Metatarsal bases are `(x,0.035,-0.024) H` with `x=[-0.018,-0.009,0,0.010,0.020] H` medial→lateral. Heads are `(x,0.075,-0.030) H`; toe endpoints have Y `[0.110,0.112,0.107,0.100,0.090] H` and Z `-0.034 H`. Each toe is a labeled rigid group of its phalanges; all groups share the MTP action, with fixed offsets to their respective heads. Metatarsal shafts have radius `0.003 H`, toe shafts `0.002 H`, and distal toe pads are spherical skeletal visualization caps of radius `0.006 H`, centered at those endpoints. Thus the neutral distal cap bottom is at world Z=0. The rear extremity is `Y=-0.040 H`; the front extremity includes the second toe cap at `Y=(0.112+0.006)H=0.118 H`, giving a foot envelope length of `0.158 H`. The width is `(0.020+0.006)-(-0.018-0.006)=0.050 H`. These are A dimensions, not shoe/soft-tissue dimensions. On 2026-10-20 the human explicitly chose to preserve these primitives and correct the earlier inconsistent aggregate claims `0.152 H` and `0.055 H`; no primitive dimension, joint/contact location, or tolerance changes in that correction.

Contact anchors, in neutral ankle-relative coordinates, are heel `(0,-0.025,-0.040) H`, medial ball `(-0.018,0.075,-0.040) H`, lateral ball `(0.020,0.075,-0.040) H`, and toe tips `(x,Y_tip,-0.040) H`. The ball contact witnesses attach to the corresponding proximal toe-group frames at the MTP line, offset `0.010 H` below their heads; toe-tip witnesses attach to those toe bodies. This attachment is fixed in the profile, not reassigned during a rocker. They are explicitly labeled contact-envelope witnesses, not anatomical bone centers. Individual toes and cartilage guides do not add independent degrees of freedom.

### 4. Freeze supported action bounds and composition

All actions below have schema-enforced finite bounds. Ranges are **authored operating envelopes**, selected with the cited reference observations; they are not direct estimates of every individual's physiological maxima. The F observations remain unchanged in the spec. No action is unlocked solely because a quaternion can express it.

For the right side, hip action orientation is `Rx(f) Ry(b) Rz(-r)` and wrist orientation is `Rx(f) Ry(b)`, relative to anatomical neutral. `f` is flexion, positive `b` is hip adduction or wrist ulnar deviation, and positive `r` is hip external rotation. Mirror transforms for the left; do not reuse backend signs. For each antagonistic action, divide by its sign-specific magnitude below. Combined motion is permitted only if the sum of those squared fractions is at most one; this is an A multiaxis envelope, not a sourced physiological surface.

| Action / axis | Operating bounds, degrees | Evidence and approximation rationale |
|---|---:|---|
| Hip `f` | `[-15,120]` | F/M; reduced extension/flexion envelope |
| Hip `b` | `[-30,10]` | M Table 1; reduced abduction/adduction |
| Hip `r` | `[-30,35]` | M; reduced internal/external rotation |
| Elbow flexion about neutral `+X` | `[0,140]` | F/M; exclude hyperextension from the supported exercise envelope |
| Forearm `p` about proximal-directed elbow/wrist axis | `[-80,75]` | F; supination negative, pronation positive; neutral assembly is `p=-80`, not clinical midrotation |
| Wrist `f` | `[-60,70]` | M and R; extension negative, palmar flexion positive |
| Wrist `b` | `[-15,25]` | R Table 2; reduced radial/ulnar deviation; wrist axial twist is fixed |
| Knee flexion `k` | `[0,130]` | F; other independent tibial actions are unsupported |
| Talocrural dorsiflexion `a`, neutral `+X` | `[-40,20]` | A printed p.235 reports 10–20-degree dorsiflexion variability; R3 authored operating maximum 20, not a universal physiological limit. F means remain unchanged; plantarflexion negative |
| Hindfoot inversion action `i` | `[-10,20]` | A pp. 234–235; eversion negative, oblique-axis angle rather than a clinical planar measurement |
| MTP/toe-group extension `m`, neutral `+X` | `[-10,45]` | T introduction supports dorsiflexion relevance; A reduced group envelope; plantarflexion negative |
| Cervical flexion / lateral flexion / rotation | `[-50,50] / [-30,30] / [-60,60]` | S Table 3; reduced envelopes |
| Thoracic flexion / lateral flexion / rotation | `[-25,35] / [-20,20] / [-25,25]` | S; reduced envelopes |
| Lumbar flexion / lateral flexion / rotation | `[-15,35] / [-15,15] / [-10,10]` | S; reduced envelopes |
| Pelvis X,Y position | `[-0.25,0.25] H` each | A; body placement, not joint ROM |
| Pelvis Z position | `[0.20,0.60] H` | A; absolute world height |
| Pelvis pitch / lateral tilt / yaw | `[-30,30] / [-15,15] / [-30,30]` | A; body placement |

For spine and pelvis, positive anterior flexion/pitch is `Rx(-f)`, positive right lateral lean is `Ry(b)`, and yaw is `Rz(r)`, ordered `Rx(-f) Ry(b) Rz(r)`. Apply the same squared-fraction envelope within each spinal region. In addition, lumbar+thoracic action sums must remain in flexion `[-30,50]`, lateral flexion `[-25,25]`, and rotation `[-35,35]`. These A coupling budgets prevent simply adding every isolated regional maximum.

The shoulder uses three independent coordinates: total elevation `e ≥ 0`, elevation-plane azimuth `psi` in `[-180,180]`, and axial external twist `tau` in `[-55,70]`. Azimuth 0 is forward, +90 lateral, ±180 posterior, and -90 across the midline on the right. At `e=0`, azimuth must be canonical zero. `u(psi)=(cos psi,-sin psi,0)`, and total humerus orientation is `Rot(u,e) Rz(-tau)`. The maximum elevation is periodic piecewise-linear interpolation through `(psi,e_max)=[(-180,40),(-90,20),(0,168),(90,160),(180,40)]`. Apply `(e/e_max)^2 + (tau/tau_max)^2 ≤ 1`; at nonzero twist the reachable swing is consequently reduced. These A sector limits are informed by F/M and deliberately do not treat three Euler maxima as a box.

The generated glenohumeral orientation is dependent on the shoulder girdle. Its neutral-relative swing must remain ≤125 degrees and absolute twist ≤100 degrees; these are A backend guard bounds, not separately asserted clinical ROM. All generated shoulder poses must satisfy both total and dependent bounds. Fixed jaw/digit controls are rejected as unsupported. No `free` body-group channel is silently assigned a pose.

**Alternative:** A uniform ±180-degree limit or a fixed hinge for every joint would fail the spec. A complete measured multiaxis physiological limit surface is not claimed; profile-specific ellipsoidal/sector bounds and explicit coupling are inspectable approximations.

### 5. Specify every dependent articulation

All following curves are deterministic A approximations informed by the listed cleared sources. They are checked as authored curves, with their evidence limitations exposed; matching the curves is not independent proof of clinical anatomy. Canonical formula samples are required at domain endpoints and each 15-degree action increment. Numerical residual bounds are `0.1 degrees` for orientations and `1e-4 H` for positions, in addition to the stricter rigid-body length checks.

**Shoulder girdle (B, H).** Let `v = ac-sc` in the neutral thorax frame. Clavicular orientation is `C = Rz(-e/16) Ry(-e/10) Rot(normalize(v),e/8)`. Its AC position is `sc + C*v`. Scapular orientation relative to neutral is `G = Rot(u,e/3) Rx(e/10) Rz(-0.075e)`. Place the scapula at the new AC position, preserving its AC-to-glenoid vector rotated by G. The glenohumeral center follows that glenoid; the humerus orientation relative to scapula is `inverse(G)*R_total`. Thus scapular pose is not incorrectly obtained by adding clavicle angles again. AC orientation is derived by closure `inverse(C)*G`.

At `e=[0,30,60,90,120,160,168]`, the principal upward-rotation channel is `[0,10,20,30,40,53.333333,56]` degrees. Clavicle elevation is `[0,3,6,9,12,16,16.8]`, retraction `e/16`, and axial rotation `e/8`. Posterior tilt is `e/10`, external scapular rotation is `0.075e`. B supports approximate 2:1 coordination in abduction; extending this simple rule to the other supported planes and the small additional channels is explicitly an authored animation approximation. There is no claim that the ratio is constant physiology or a measured forward-flexion curve.

**Forearm (H, F).** Ulna remains under the elbow articulation. Define the proximal-directed pronation axis as `normalize(proximal_radius - distal_ulna)`, through the proximal radius center (elbow plus the neutral radial offset) and distal ulna center (wrist plus the neutral ulnar offset). The proximal radius remains the rotation origin; reversing the direction does not move the axis line. The radius is a rigid body rotated about this line through `p+80` degrees; its proximal endpoint stays on the axis, its distal endpoint traces a circle, and its bow is preserved. The wrist/hand frame rotates with the distal radius, using the same rotation applied to its neutral wrist frame. The canonical radiocarpal midpoint is the rotated neutral wrist landmark. Do not twist the entire ulna or use wrist axial rotation to impersonate pronation. Sample `p=[-80,-40,0,40,75]`; the corresponding radius rotations are `[0,40,80,120,155]`. This is a fixed-axis forearm approximation, not a reconstruction of individual radioulnar contact surfaces.

**Knee (P, H).** In the femur's neutral action frame define `t=k/30`, saturated to `[0,1]`, `s(t)=3t²-2t³`, and dependent tibial twist `z(k)=-8 s(t)` degrees about the distal-directed right axis `-Z` (left axial mirror `+Z`), so negative twist is medial. The shank orientation relative to the femur is `K=Rx(-k) Rz(-z(k))`. Its proximal translation is `d(k)=(0,-0.003 sin(k),-0.001(1-cos(k))) H`, applied at the nominal knee center in the femur frame. Tibia/fibula retain their own complete rigid geometry; offsets change the articulation's location, not shaft length. This A screw-home/rollback trajectory encodes the initial medial tibial rotation discussed by P, with chosen magnitudes rather than copied participant data. Check samples `k=[0,15,30,60,90,130]`: twist `[0,-4,-8,-8,-8,-8]`; translation is given exactly by the formula.

**Patella (P).** In the femur action frame, rotate the neutral knee-to-patella-center vector about `+X` by `-0.65k`; the patellar body flexes by `-0.65k`. Add lateral displacement `H*[0,-0.0004,0.0003,0.0006,0.0004]` at knee angles `[0,15,30,90,130]`, with reflection on the left. Add corresponding patellar tilt `[0,-1,0,3,2]` degrees about its superior local axis; other patellar rotation is fixed. Interpolate each sample interval by `v_i + (v_next-v_i)*(3t²-2t³)`, where `t=(k-k_i)/(k_next-k_i)`, giving continuous zero slopes at sample knots and no overshoot. The 0.65 factor lies within P's reported 60–70% trend; translations, tilt samples, and constant-radius tracking are authored reductions, not digitized measured curves. In full extension and at 90-degree flexion, this produces patellar flexion 0 and 58.5 degrees. All samples above 90 remain a declared animation approximation.

**Spine (S, H).** Each regional action is distributed equally over its five lumbar, twelve thoracic, or seven cervical joints: each local action is `Rx(-f/N) Ry(b/N) Rz(r/N)` inserted after that joint's fixed rest transform. No body is scaled. At regional flexion 0, 15, and 30 degrees, each vertebra contributes respectively `0`, `15/N`, and `30/N`; analogous formulas cover the full bounded domain, all axes, and their composition. Uniform distribution is an authored low-detail approximation; anatomy does not imply equal intervertebral mobility. Ribs follow their vertebra rigidly, the revised sternum follows T1 to retain SC closure, and section 3's evaluated cartilage graph bridges the resulting relative motion without being classified as rigid bone.

**Ankle/hindfoot (A).** Talocrural orientation is `Rx(a)`; the radius/fibula malleolar geometry remains on the shank. Rotate the calcaneus/midfoot group about a hindfoot pivot coincident with the ankle center using `Rot(h,i)`, with right-side `h=(-sin(23)cos(40), cos(23)cos(40), sin(40))`. This uses the cited oblique-axis directions; locating the pivot at the ankle center and retaining a fixed sagittal talocrural axis are explicit simplifications. The full foot orientation is `Rx(a) Rot(h,i)`. Changing inversion therefore produces coupled pitch/yaw rather than an independent foot Euler roll. No extra independent foot yaw is allowed. The axis-direction cosines, not a rounded approximate vector, are canonical.

**Forefoot/foot roll (T, A).** The shared MTP line has posterior-to-anterior offset `0.075 H` and world-neutral height `0.010 H`; it runs laterally through all five metatarsal heads. Toe groups rotate by `Rx(m)` about their respective heads. A forefoot rocker with rear-foot pitch `-r` and `m=r`, `r ∈ [0,30]`, keeps toe direction horizontal while raising the rear foot. Translation is solved by keeping the ball contact witnesses fixed; samples `r=[0,10,20,30]` map to `m=[0,10,20,30]`. This is an authored rocker, not a measured gait trajectory. The dedicated seated/floating action sweep also covers the complete `m ∈ [-10,45]` operating envelope without claiming floor contact.

**Continuity bounds.** Valid fixture evaluation steps of at most `0.01 beat` may change no tracked body origin by more than `0.02 H` or body orientation by more than 5 degrees. An isolated mobility action sweep uses four beats from neutral to its negative limit, positive limit, and neutral, with `ease_in_out(t)=3t²-2t³` per leg; coupled helpers are re-evaluated at every time. For the dense numeric coverage sweep, impose input steps ≤0.25 degrees in addition to the beat-grid check. Thresholds are engineering checks to catch branch flips; they do not estimate human velocity limits.

### 6. Use data-side kinematics and independently measured constraints

Solve FK and analytic coupling in Python, then assign solved body transforms to Blender. Use rigid attachments rather than deforming a bone mesh to fake a pose. Contact solving can change only the declared controlled channels, inside their operating envelopes. Use deterministic damped least-squares with fixed initial seed from the previous solution, damping `1e-4`, maximum 100 iterations, and normalized position residual target `1e-5 H`. Use a canonical neutral seed at every sequence start, deterministic variable ordering, and fixed positive knee branch. Failure after the budget is `unsatisfied-constraint`, not success with relaxed thresholds.

The numeric verifier reconstructs action angles and contact landmarks from generated transforms without consulting the solver's success flag. Independent expected samples use the formulas/tables in this document and targeted inverse-transform checks. Do not verify both measured and expected values by calling the same solver routine. An optional solved-frame cache is generated under `build/` and is not the source of truth.

**Alternatives:** Blender's GUI constraint state would obscure required controls and reproducibility. A full dynamics solver would add an unrelated muscle/force simulation. The chosen kinematic solver enforces declared constraints but does not prove dynamic balance. The R3 squat adds a scoped static COM/support plausibility check; it does not claim dynamic stability at playback tempos.

### 7. Fix diagnostic fixtures and contact semantics

Store fixture intent as YAML under `rig/diagnostics/`, schema version `skeleton-diagnostic/v1`. This change explicitly introduces this scoped verification format. Each file has `id`, `description`, `provenance`, `profile`, `duration_beats`, `controls`, `rest_policy`, action key samples, world-root intent, and contact intervals. Values are beats, degrees, and canonical meters; normalized design coordinates are expanded using H. Repeated contact targets refer to stable foot-local anchor IDs and world positions. Omitted groups use `base` against the named neutral fixture; `hold` and `free` have the project meanings and conflicting writers fail validation.

All three main fixtures keep the non-anatomical `world_root` at identity. Pelvis translation is explicitly keyed motion in `pelvis`, including the backward shift needed for a squat. It is not automatic root drift. Dossier body placement is distinct from a future exported hips-translation channel.

#### Squat R2 (historical rejected construction; negative regression only)

Use `k=[0,45,90,45,0]` at beats `[0,1,2,3,4]`, smoothstep interpolation. Pelvis anterior pitch and talocrural dorsiflexion are `p=a=12k/90`. Lumbar anterior flexion is `10k/90`; thoracic/cervical actions are zero relative to their regional neutral. Thus the bottom torso orientation contains 12 degrees pelvis pitch plus 10 degrees distributed lumbar flexion. Arms hold 80-degree forward elevation; both arm groups are controlled.

With the right leg's knee transform K above, define `P=Rx(-p)`, `A(i)=Rx(a) Rot(h,i)`, and hip orientation `U(i)=inverse(P)*inverse(K*A(i))`. Choose the unique `i ∈ [-10,20]` for which the lateral component of

`v(i) = P*U(i) * ((0,0,-0.234)H + d(k) + K*(0,0,-0.2155)H)`

is zero. Solve by 60 fixed bisection steps on the sign-changing bracket, or fail if there is no root. Set pelvis `Y=-v_y` and `Z=0.040H-v_z`; X remains zero. Mirror for the left leg. This construction explicitly defines hip orientation and keeps both ankle frames at their original position/orientation. It does not leave hip-angle selection to the implementer.

The following reference audit was calculated independently with scalar matrix arithmetic while drafting this design. Rounding in this table is for review; formulas are canonical. Hip angles use the `Rx(f) Ry(b) Rz(-r)` decomposition.

| k | Hindfoot i | Right hip `(f,b,r)` | Pelvis `(Y,Z)/H` |
|---:|---:|---|---|
| 0 | 0.000000000 | `(0,0,0)` | `(0,0.489500000)` |
| 15 | -0.701652493 | `(14.759357284,-0.451737420,3.534539773)` | `(-0.042613343,0.483751267)` |
| 30 | -2.608731017 | `(29.012530832,-1.609427759,6.212301484)` | `(-0.079552852,0.467373309)` |
| 45 | -3.663286549 | `(43.640371632,-2.161600063,5.420489054)` | `(-0.114514035,0.440343298)` |
| 60 | -4.598367842 | `(58.324582307,-2.585411868,4.684572933)` | `(-0.143283402,0.403884071)` |
| 75 | -5.437334043 | `(73.052932639,-2.901858192,4.001074495)` | `(-0.163896512,0.359502744)` |
| 90 | -6.198510420 | `(87.815945733,-3.127968930,3.369465167)` | `(-0.174727485,0.309142260)` |

This proves closure of the specified center/frame construction at these samples, not clearance of every generated mesh or clinical correctness. The latter checks remain mandatory implementation/review acceptance work. Both feet have flat contacts over `[0,4]`; controlled groups are pelvis, torso, both legs, and both arms.

#### Squat R3: whole-body mass and static plausibility dossier

The human rejected the squat's balance/readability at visual gate 2. Foot
closure alone did not establish balance. The following supersedes the former
12-degree ankle/pelvis construction; all other geometry and diagnostic targets
remain fixed. This scoped check estimates **whole-body** mass including
unrendered soft tissues; it does not weigh the skeletal mesh or solve muscle
forces/dynamic stability at the GIF playback tempos.

Use k=[0,45,90,45,0] at beats [0,1,2,3,4] and the existing smoothstep
interpolation. Set talocrural a=20k/90, pelvis pitch p=25k/90 and lumbar
flexion=10k/90. Arms retain 80-degree forward elevation. All other squat keys,
contacts and masks remain unchanged. Use the same analytic flat-leg formulas,
root bracket/60 bisections and hip decomposition above; replace only the
specified a,p functions. Pelvis Y=-v_y, Z=0.040H-v_z. Mirror the right leg.

The following rounded values are planning arithmetic, not implementation or
independent-review acceptance. Position/COM table conformance is 1e-4H; angle
conformance is 0.1 degrees. The formulas remain canonical.

| k | Hindfoot i | Right hip (f,b,r), degrees | Pelvis (Y,Z)/H | Knee Y/H | Estimated COM Y/H |
|---:|---:|---|---|---:|---:|
| 0 | 0.000000000 | (0.000000000, -0.000000000, 0.000000000) | (-0.000000000, 0.489500000) | -0.000000000 | 0.017938833 |
| 15 | -0.714279815 | (15.589158292, -0.449227544, 3.514876145) | (-0.032247565, 0.484624762) | 0.013340045 | 0.007483516 |
| 30 | -2.688377707 | (30.661728344, -1.574340712, 6.076282432) | (-0.059423335, 0.470633798) | 0.028115932 | 0.000771627 |
| 45 | -3.801628496 | (46.116344550, -2.057262262, 5.157890040) | (-0.086068986, 0.447406860) | 0.041803165 | -0.006135963 |
| 60 | -4.783206031 | (61.636011802, -2.366517234, 4.286702683) | (-0.108583814, 0.415701085) | 0.055175351 | -0.010534089 |
| 75 | -5.644182672 | (77.210810002, -2.522124977, 3.476078337) | (-0.125498842, 0.376443325) | 0.068186478 | -0.011430410 |
| 90 | -6.392846611 | (92.832771898, -2.543428129, 2.738335388) | (-0.135496597, 0.330874410) | 0.080794598 | -0.007927533 |

**Mass coefficients.** Kudzia, Jackson and Dumas (2022), original Proposed
columns of Tables 3 and 6 (not ECM, regression or literature Mean Value
columns), are cleared as `kudzia-2022-body-segments` under CC BY 4.0. Use the
following raw mass weights; reference=(male+female)/2 per row. Paired rows are
instantiated once per side by mirror. Sum all 16 weights and normalize each
by that sum at evaluation; reference total is 74.15. These blended weights do
not assert one measured subject or a universally representative body.

| Region | Male weight | Female weight | Reference weight | Carrier | Neutral-world-axis offset from carrier origin, /H |
|---|---:|---:|---:|---|---|
| head | 5.6 | 5.3 | 5.45 | skull | (0,0.010,0.060) |
| upper_trunk | 11.5 | 12.0 | 11.75 | T6 | (0,0.020,0) |
| abdomen | 11.0 | 7.0 | 9.0 | L1 | (0,0.015,0) |
| pelvis | 9.2 | 8.9 | 9.05 | pelvis | (0,0.010,0.030) |
| thigh, each side | 10.4 | 12.0 | 11.2 | femur.side | (0,0,-0.103779) |
| shank, each side | 3.5 | 3.9 | 3.7 | knee.side | (0,0,-0.08781625) |
| foot, each side | 1.1 | 1.1 | 1.1 | hindfoot.side | (0,0.040,-0.025) |
| upper_arm, each side | 2.1 | 1.9 | 2.0 | humerus.side | (0,0,-0.066447) |
| forearm, each side | 1.1 | 0.9 | 1.0 | elbow.side | (0,0,-0.05726175) |
| hand, each side | 0.5 | 0.4 | 0.45 | wrist.side | (0,0,-0.041382) |

Limb offsets are the arithmetic mean of male/female Proposed proximal COM
fractions (thigh .4435, shank .4075, upper arm .414, forearm .4195, hand .418)
applied to the existing neutral carrier-to-distal centerline, with the hand
ending at phalanx.middle.3. A mass point is rigid on its carrier, not a blend
of moving joint centers. Head/trunk/pelvis/foot offsets and the use of this
skeletal endpoint vocabulary are **authored placement approximations**;
no participant scan, figure, code or true tissue density is imported. Neck
and other tissue contributions are represented by the regional mass budget,
not omitted because their visible bones are small. Point offsets are not
claimed as new anatomical measurements.

In the existing skeleton-profile/v1 source, add one closed `mass_model`
object with `id: adult-reference-point-masses-v1`, `assessment: static`,
`description`, `provenance` and exactly 16 `segments`. Each segment has stable
`id`, resolved rigid `body`, strictly positive finite `weight_kg`,
`male_weight_kg`, `female_weight_kg`, body-local `position_m`, description and
provenance. Canonical body-local position is B^T times the neutral-world-axis
offset above. All three weight sums are positive and fractions normalize to
one within 1e-12. Validate the complete inventory, per-side symmetry,
reference-weight averaging, source locators and body/frame references. Missing,
extra, duplicate, nonfinite, zero/negative, unresolved or asymmetric mass
records fail validation. No new standalone source file format or dependency
is introduced; this unpublished profile's schema is extended explicitly.
Scaling stature scales point positions, not weights or fractions.

**Measurements.** For each mass segment j, get p_j=t_body+R_body*p_local
from the actual evaluated carrier frame. COM=sum(w_j*p_j)/sum(w_j).
Compute the XY convex hull of the *measured permanent attachments* named in
the current squat's declared flat contacts. Both feet and heel/ball witnesses
must be present with independent target/sliding/floor checks; a missing,
degenerate or nonfloor support polygon fails. Do not substitute intended
target positions for measured support or caller-supplied COM metadata for
observations. The support hull is a conservative contact-envelope model, not
a measured pressure distribution or shoe outline.

Use a counterclockwise hull. The COM margin is the minimum signed perpendicular
XY distance to any hull edge, positive inside. Required reference margin is
>=0.010H at **every delivered squat frame and every existing dense squat
sample**, all three statures. Repeat with male/female mass weights (same
approximate carrier points, not claims of sex-specific anatomy). Subtract
0.005H from the minimum of all three margins as a conservative horizontal
point-placement perturbation bound; require this lower bound >=0.005H.
This is a mathematical perturbation allowance, not a population confidence
interval. The planning grid of 361 knee inputs found minimum cohort margin
0.013183781H, at k=70.5 degrees, hence lower bound 0.008183781H. Final
acceptance still requires the prescribed denser grid and native frames.

Record COM XYZ, all segment positions/normalized fractions, support vertices,
edge margins, worst edge, three weight-variant margins, perturbation lower
bound, units, fixture/beat, measured/expected bounds and image links. Native
backend evaluation exports the 16 mass points from actual posed bone matrices;
verify source offsets and mean-coefficient/weighted-sum arithmetic independently
of the pose constructor. Prepared COM values/flags alone are not evidence.
The data-side dense audit uses canonical evaluated frames and is labeled as
such; native conformance is checked on every delivered frame separately.
No successful pinned-foot result can bypass a failed balance check.

**Regression and visual review.** Preserve the old a=p=12k/90 construction as
a rejected negative. With the reference mass model its bottom COM Y is
-0.065080601H, behind the measured heel boundary at -0.025H; it must fail
balance even though pins, floor and joint limits pass. Also reject posterior
upper-body displacement with intact feet; missing/forged mass observations;
zero/equalized/omitted masses; and support silently replaced by targets.
Preserve all existing sign, thorax, contact, floor and timing fault regressions.

Create an early squat-only front/side pack at 60/120/180 BPM through the
existing documented commands before the expensive complete rebuild. Show
whole-body COM, floor projection, measured support hull/edge and signed margin
in separate diagnostic overlays, with the label 'Estimated whole-body COM;
static plausibility only'. Preserve unannotated views, fixed cameras/floor
and the previous R2 results. Regenerate the full action set after the ankle
sweep endpoint changes to 20 degrees; stepping remains 12 degrees and its
frozen reference table remains unchanged. Full source hashes, 3-stature native
checks, dense contacts/floor/balance, two clean renders and independent review
must match one R3 snapshot. Human gate 2 remains open for thorax and squat.

#### Forward arm raise

At beats `[0,1,2,3,4]`, set total forward elevation `e=[0,80,160,80,0]`, `psi=0`, `tau=0`, elbow flexion zero, forearm `p=-80`, and wrist actions zero. Use smoothstep per beat. Both feet have flat contacts throughout; pelvis position and all trunk actions stay at their initial values. Controls are `arm_L`, `arm_R`; their shoulder-girdle channels belong to those groups, even when their anatomical parents are on the torso. Internal helper updates do not confer ownership of unrelated torso channels.

#### Walking in place

Left swing beats 0–2 uses half-wave `w=sin²(pi*t/2)`; right swing beats 4–6 is its mirror with `t=beat-4`. Outside a swing, w=0. Knee flexion is `k=60w`, ankle dorsiflexion `a=12w`, and MTP action zero. Knee coupling remains enabled. Pelvis and world root stay at neutral/identity. Derive hip orientation and hindfoot action by the exact flat-orientation construction below, rather than prescribing hip flexion independently. Contralateral arm forward swing is `20w`, ipsilateral backward swing `15w`, with shoulder coupling evaluated in the respective planes. Elbows stay at 10-degree flexion, wrists zero, forearms at `p=-80`. Controlled groups are both legs and both arms; unowned groups follow the neutral base.

**Swing construction.** Use K, d(k), and the oblique axis h from section 5. For the right-side prototype define `A(i)=Rx(a) Rot(h,i)` and `U(i)=inverse(K*A(i))`. Choose the unique `i ∈ [-10,20]` making the lateral component of

`v(i)=U(i)*((0,0,-0.234)H + d(k) + K*(0,0,-0.2155)H)`

zero, using the same sign-changing bracket and 60 fixed bisection steps as the squat; fail if the bracket or uniqueness condition does not hold. The hip center stays at `(0.055,0,0.4895) H`; the ankle center is that hip center plus v. This preserves ankle X while permitting authored forward/upward swing. Hip actions are the declared `Rx(f) Ry(b) Rz(-r)` decomposition of U, not independent added rotations. The rear-foot orientation is exactly `U*K*A=identity`; toes follow it because MTP action is zero. Mirroring generates the other side. The talus retains its separate talocrural attachment; no body is stretched or translated independently to conceal a violation.

The following scalar-matrix audit freezes rounded reference samples; formulas are canonical. `ankle (Y,Z)/H` is absolute world placement. The rigid foot envelope whose neutral minimum is zero has clearance `ankle_Z/H-0.040` while its world orientation stays identity. Talus, shank, and all other visible structures still require the complete evaluated-geometry floor check.

| w | Knee k | Ankle a | Hindfoot i | Right hip `(f,b,r)` | Ankle `(Y,Z)/H` | Foot-envelope clearance/H |
|---:|---:|---:|---:|---|---|---:|
| 0 | 0 | 0 | 0.000000000 | `(0,0,0)` | `(0,0.040000000)` | 0.000000000 |
| 0.25 | 15 | 3 | -0.711044146 | `(11.756730885,-0.449863493,3.519858446)` | `(0.034841057,0.045070945)` | 0.005070945 |
| 0.5 | 30 | 6 | -2.667460488 | `(22.999701270,-1.583315743,6.111071448)` | `(0.064471855,0.059593055)` | 0.019593055 |
| 0.75 | 45 | 9 | -3.764313978 | `(34.623089765,-2.084100783,5.225423700)` | `(0.093231169,0.083672242)` | 0.043672242 |
| 1 | 60 | 12 | -4.731693677 | `(46.309631158,-2.422945563,4.389235643)` | `(0.117369751,0.116450283)` | 0.076450283 |

This is an authored verification trajectory using the existing cleared anatomy/coupling basis, not measured gait. The fixed-pelvis leg shortens by articulation during swing; its foot travels forward and returns to the same neutral contact location. At apex, knee flexion is 60 degrees and foot-envelope clearance is `0.076450283 H`. A dense 0.01-beat scalar audit gives maximum hip multiaxis-envelope score `0.171179111` (limit 1), foot orientation matrix residual below `1e-12`, and no negative clearance beyond floating-point noise. Repeat that audit at delivered frame times, with angular input steps at most 0.25 degrees, before accepting the fixture. Apply all existing limits and continuity tolerances unchanged.

**Correction rationale (2026-10-20).** The earlier `hip=30w`, `knee=60w`, `ankle=12w`, `hindfoot=0` construction pitched the forefoot downward before the ankle rose enough. The third toe's attached bottom surface point reached `-0.004545930 H` at beat 0.35, violating the unchanged `-1e-4 H` floor limit. Retain that construction only as a negative regression. The human authorized correcting this trajectory after the implementation preflight report; this revision changes action construction, not joint limits, body dimensions, camera/floor placement, duration, contacts, or acceptance thresholds.

Right flat contacts are `[0,4)` and `[6,8]`; left flat contacts are `[2,8]`. At beats 0 and 4 the lifting foot is geometrically on the floor but not declared pinned after lift-off. Touchdown is at beats 2 and 6 and closes continuously onto its neutral targets. There are no fractional contact events or heel/toe phases in this fixture; the separate rocker below tests those. Clearance is measured on the entire evaluated sole envelope, including toe caps, not just on the ankle marker. The specified apex is subject to the spec's minimum `0.02 H` clearance and 45-degree knee-flexion acceptance checks; a failure requires a planning revision rather than amplitude adjustment during implementation.

#### Foot-roll diagnostic and action sweeps

Add a four-beat bilateral heel-rise/forefoot-rocker fixture with `r=[0,15,30,15,0]` at integer beats and smoothstep interpolation. Pin both ball witnesses; release heel/toe-tip anchors for the moving contact envelope. Keep toe groups horizontal by `m=r`, set talocrural `a=-r`, hindfoot zero, and hip/knee actions zero. Keep the MTP line fixed at world `Y=0.075 H, Z=0.010 H`; derive ankle position by rotating its vector `(0,-0.075,0.030) H` about that line by `Rx(-r)`. Translate the neutral pelvis by the same ankle displacement: `deltaY/H=0.075*(1-cos r)+0.030*sin r`, `deltaZ/H=0.075*sin r+0.030*(cos r-1)`. Both rigid legs therefore stay vertical, while the fixed toe-group witnesses preserve forefoot support. This exact construction avoids an underdetermined balance solve. All allowed joint ranges remain active; controlled groups are pelvis and both legs. Terminal full flat contact is declared at beat 4. The rocking fixture tests a functional coupling; floating action sweeps separately test all axis bounds, including plantarflexion and maximum MTP extension, without inventing foot pins.

For every isolated action sweep, lift/reposition only its declared body placement enough to put the lowest rest mesh point `0.15 H` above the floor, then hold that placement. Contacts are empty. This placement is a declared diagnostic stage offset outside the clinical pelvis bounds, identified as `world_root` intent, not an anatomical pose or unreported drift. Source changes to the static/animated stage transform must match exactly.

### 8. Keep VRM semantics as an explicit adapter

Use **VRMC_vrm 1.0 humanoid names**, with the exact selected vocabulary/required subset listed in the MIT-licensed V constants; do not copy or depend on an uncleared specification document. Store an explicit mapping in `rig/humanoid-map.yaml`. The internal anatomical hierarchy can contain more bodies and helper translations than the humanoid proxy hierarchy.

| Humanoid semantic | Internal target / body group |
|---|---|
| `hips` | pelvis origin/frame / `pelvis` |
| `spine` | L1 regional result / `torso` |
| `chest` | T6 regional result / `torso` |
| `upperChest` | T1 regional result / `torso` |
| `neck` | C3 regional result / `head_neck` |
| `head` | skull base/frame / `head_neck` |
| `leftShoulder`, `rightShoulder` | corresponding SC→AC clavicle frames / corresponding arm |
| `leftUpperArm`, `rightUpperArm` | glenohumeral centers/humeri / corresponding arm |
| `leftLowerArm`, `rightLowerArm` | elbow frames; radius/ulna detail retained internally / corresponding arm |
| `leftHand`, `rightHand` | solved radiocarpal midpoint/hand frames / corresponding arm |
| `leftUpperLeg`, `rightUpperLeg` | hip centers/femora / corresponding leg |
| `leftLowerLeg`, `rightLowerLeg` | solved knee centers/tibiae / corresponding leg |
| `leftFoot`, `rightFoot` | solved ankle/hindfoot frames / corresponding leg |
| `leftToes`, `rightToes` | common MTP frame / corresponding leg |

Eyes are absent, jaw and individual finger entries are deliberately unmapped optional semantics. Every required V entry resolves. Scapulae, patellae, detailed vertebrae, radii/ulnae separation, ribs, and cartilage guides are internal and reported as such. Mapping is not an export claim: knee rollback, a moving radiocarpal midpoint, and many-to-one spinal detail cannot be assumed to survive VRMA's translation restrictions. Export reconstruction and error assessment belong to `bake-and-export`; the mapping report must expose these losses now. There is no invented MPFB/Rigify map because neither rig is used.

### 9. Data organization, dependencies, and command contract

Implementation introduces the following source contracts, all versioned `1` and validated with JSON Schema Draft 2020-12:

| Source | Required records |
|---|---|
| `rig/profiles/adult-reference-v1.yaml` | units, stature, landmarks, geometry inventory, attachment formulas expanded to numeric records, descriptions, A/W/H provenance |
| `rig/mobility/adult-reference-v1.yaml` | action frames, neutral offsets, operating bounds, composition order, multiaxis conditions, coupled curves, reference observations, provenance |
| `rig/body-groups.yaml` | smallest groups and explicit channel membership, including dependent helpers |
| `rig/humanoid-map.yaml` | semantic version, selected vocabulary and required entries, target IDs, omissions and mapping losses |
| `rig/diagnostics/*.yaml` | the scoped fixture format in section 7 |
| `scenes/skeleton-review.yaml` | fixed renderer, cameras, floor, materials, resolution and review overlays |
| `schema/*.schema.json` | closed object shapes, finite numbers, units/version enums, required provenance and field ranges |

Cross-record validation rejects cycles, dangling references, duplicate YAML keys, overlapping independent writers, omitted controls, non-unit quaternions, invalid frames, and source/license gaps. All formulas in this design must be expanded explicitly into validated canonical data; an arbitrary expression-evaluation language is not introduced. Coupling types are a closed set with numeric parameters, not executable strings in YAML.

Python tooling uses `uv`, Python 3.12, and explicitly declared `PyYAML`, `jsonschema`, and `Pillow` dependencies, with exact resolution committed in `uv.lock` during implementation. Use the standard library for matrix/quaternion arithmetic and the numerical solver; no scientific simulation, DCC add-on, or neural model dependency is needed. Blender scripts read prevalidated JSON build inputs produced by the Python side; Blender's bundled Python does not install application dependencies. Third-party notices for any distributed code or copied vocabulary are retained under their original licenses.

Maintain these established command contracts together in `tools/README.md`; extend their documented options for the thoracic preview and measurements during implementation:

```text
uv run python tools/validate.py --profile adult-reference-v1
uv run python tools/prepare_skeleton.py --profile adult-reference-v1 --output build/skeleton/input.json
blender --background --factory-startup --python tools/build_skeleton.py -- --input build/skeleton/input.json --output build/skeleton
uv run python tools/verify_skeleton.py --input build/skeleton --output build/review/anatomical-human-skeleton/metrics.json
uv run python tools/review_pack.py --input build/skeleton --output build/review/anatomical-human-skeleton
```

`prepare_skeleton.py` solves fixture intent and emits canonical transforms/timing. `build_skeleton.py` independently constructs the geometry and applies those transforms. `verify_skeleton.py` compares generated body/landmark measurements with the dossiers and fixtures, retaining measured and expected values. `review_pack.py` orchestrates clean headless renders and assembles contact sheets/GIFs/overlays from generated frames. Ordinary automated checks run through `uv run python -m unittest discover -s tests`. No generated binary enters git.

### 10. Pin rendering, sampling, and review artifacts

Use Blender **5.2.2 LTS**, build `d13f752e3b9c`, Workbench with flat material-color illumination, opaque background `(0.94,0.95,0.96)`, bone color `(0.80,0.76,0.64)`, floor color `(0.35,0.37,0.40)` at Z=0, and black object outlines. Shadows, cavity effects, and transparency are disabled. Use deterministic object sorting and 16-sample render anti-aliasing. Flat illumination requires no external studio-light image or user lighting preset. MPFB/Rigify versions are recorded as `not-used`. The reference platform is the available Darwin arm64 build; metadata records the actual GPU/driver/render settings. Exact-pixel repeatability is required between two runs in that same reference environment; cross-platform equivalence is not inferred.

Fixed orthographic cameras look at `(0,0,0.95) m`: front at `(0,8,0.95)`, rear at `(0,-8,0.95)`, right side at `(8,0,0.95)`. Their vertical axis is world +Z. Orthographic scale is `4.0 m`, resolution `1024×1024`. The same settings apply to all fixtures and all tested statures. The frame contains the maximum supported arm elevation without reframing. The floor extends `6×6 m`. Inspection overlays use object-space axis lines of `0.025 H` and fixed labels derived from IDs; crowded structure labels are split into regional sheets without moving the underlying camera.

For thoracic inspection, add three separately named, fixed orthographic cameras to the source scene: front `(0,8,1.22) m`, right side `(8,0,1.22) m`, and right anterior three-quarter `(8,8,1.22) m`, each aimed at `(0,0,1.22) m` with world +Z up, scale `0.80 m`, resolution `1024×1024`, and the same materials/renderer. Their transforms and scale are identical for neutral/T-pose and H=1.50/1.70/1.90 m; no fit-to-body operation is allowed. These are explicit regional inspection views, not replacements for the full-body diagnostic cameras. Show both context and a labeled isolated thorax (ribs, sternum, guides, vertebrae, and clavicles; hide limbs and scapulae only in this isolated view). Camera, floor, and anatomical transforms remain unchanged between visibility variants. Rib numbers, bone/cartilage classification, posterior angles, sternal regions, and insertion connections must be readable without superimposing every label on one image. Document early-preview options under the existing prepare/build/review commands; do not add an undocumented entry point.

For four-beat fixtures, include both endpoints once: static count frames = 5; animation frame counts at 60/120/180 BPM = 21/13/13. For the eight-beat fixture these are 9 static and 41/25/25 animation frames. No fractional segment/contact events are introduced. Blender integer frame indices are sample IDs; exact rational beat/second timestamps in metadata are authoritative, avoiding frame-rate rounding. At each requested time, evaluate the same keyed animation before rendering either mode. Do not interpolate rendered images. GIF centisecond duration rounding uses cumulative error diffusion, with cumulative preview error <10 ms; PNG timestamps remain exact.

The review pack contains:

- `index.html` with links and an English explanation of the profile and approximation labels;
- structural front/rear/side views, neutral/T-pose comparisons, regional close-up sheets using the fixed views, and local-axis overlays;
- labeled front/side/three-quarter thoracic inspection sheets in context and isolation, with the section 3 shape/topology metrics and fixed inspection-camera metadata;
- front/side count and animation contact sheets, GIFs, and onion-skin overlays for every main diagnostic plus every joint-action family;
- an action/coupling coverage matrix linking valid, boundary, unsupported, and invalid samples;
- `metrics.json`, `build-metadata.json`, and an attribution/limitations report with source identifiers;
- clean-repeat comparison outputs and independent review's `review.md` in the change directory.

#### Diagnostic HTML presentation refinement

Generate the index and every diagnostic page from one deterministic diagnostic inventory, ordered lexicographically by diagnostic ID as in the current index. Include all 32 current pages: main diagnostics, neutral/rest and isolated sweeps. Place a semantic navigation region near the start of each page, with a pack-index link and an ordinary visible link for every diagnostic. Mark the current link with `aria-current="page"` and a visible style. Use a wrapping horizontal list; long identifiers wrap within their links. Separate Previous/Next controls are unnecessary because every destination is directly available.

Group output by BPM, then preview variant. Within each group, place Front and Side figures in a two-column grid at viewport widths >=1024 CSS px, with equal flexible columns, `min-width:0`, and proportional images constrained to their columns. Below 1024 px use one column, Front before Side. This threshold allows two useful inspection previews while the existing 1200 px maximum content width remains applicable. Keep BPM/view captions and their static/animation sheet links with their corresponding group. Retain onion-skin and exact-sample links. No new framework, dependency, player, synchronization behavior or media transformation is required.

Extend the existing `review_pack.py` command contract with a documented HTML-only regeneration mode taking an existing verified pack and a fresh output directory. It must assemble pages from retained metadata and media without invoking Blender or re-encoding images/GIFs. Validate the complete inventory and media hashes; fail clearly for absent or inconsistent inputs. Do not weaken the existing `--reuse-renders` source-hash policy or rewrite original native/build manifests to match changed presentation-tool hashes.

Use `build/review/anatomical-human-skeleton/presentation-r1/developer/` and `presentation-r1/independent/` for fresh developer and independent presentation outputs. The verified media predecessor is `build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/`. Preserve it and its report. Reuse its media through explicit relative references, or copy bytes unchanged where needed; resolve every generated local link. Keep original artifact hashes and source/native tool hashes intact. A separate presentation provenance record identifies the predecessor path and snapshot hash, reused artifact hashes, current presentation-generator hash and presentation verification results. Historical metrics and the old reviewer verdict remain labeled evidence for the predecessor, never a numeric acceptance verdict for the new source snapshot. No presentation implementation or verification is recorded as completed by the planning approval.

Independent presentation verification enumerates all pages and BPM/view pairs, validates links/current markers, checks layout geometry at 1024/1200/390 CSS px, verifies unchanged media/timing/evidence hashes, and regenerates HTML deterministically. Retain browser captures of arm-raise, forefoot-rocker, squat and an isolated sweep at desktop and narrow widths; the complete page inventory receives automated checks. The human inspects direct navigation and paired views alongside the existing thorax/squat visual criteria. Preserve all contact sheets, GIFs and onion-skin overlays without recomposition. Full native geometry reconstruction and two new Blender render passes are unnecessary for this HTML-only refinement; any changed geometry, timing or media invalidates this limited scope and requires the corresponding existing checks. No external source material is needed for the presentation refinement; any external material actually used remains subject to the project's commercial/derivative clearance and used-materials register requirements.

Compare decoded PNG pixels between repeated renders rather than compressed bytes or `.blend` hashes. Measure floor/camera/light transforms directly across samples; background pixels alone cannot prove stability because shadows or overlays can change. For each failed metric retain joint/structure ID, beat, measured value, expected bounds, and associated image reference. Human anatomical/naturalness judgments remain separate from numeric pass flags.

### 11. Verify the dossier, not only the generated implementation

Implementation and independent review must cover every requirement/scenario in both specs. Required numeric families are schema/reference integrity; reference-profile proportions at three statures; thoracic envelopes, inclination, posterior angles, sternal insertions, SC closure and solved cartilage-graph closure; rest/local-frame/quaternion conformance; rigid-body dimensions; mirror involution; axis sign and limit boundaries; coupled samples and invalid combinations; continuous diagnostic samples; foot anchors and complete-mesh floor clearance; root versus declared pelvis motion; loop closure; shared static/animation transforms; timing and repeatability.

Boundary tests use isolated/floating diagnostic context so a floor pin cannot make a valid action-boundary pose unreachable. Conditional boundaries are tested with their stated companion coordinates, not outside the supported envelope. Test deliberate faults: frozen scapula/patella, wrong-side action signs, a stretched shank, an unreachable foot pin, a world-root offset, the rejected thoracic constant-offset construction, costal-arch endpoints bound to bone instead of cartilage, and undeformed guide midpoints during thoracic motion. Expected failures must cite the affected requirement/scenario. A code path reporting `not-checked` is not a pass.

The numerical squat and corrected walking audits above are planning evidence only. Retain the original walking construction as a rejected negative regression and verify the corrected construction against its reference table, dense/action-step samples, and every delivered frame grid. Full geometry floor clearance, shoulder multi-axis coverage, and the closed-chain rocker still require the specified implementation checks; their acceptance thresholds are fixed here. An implementation failure must return to planning, not relax the thresholds or drop the diagnostic. The independent reviewer rebuilds into a fresh output directory and does not repair implementation code.

## Risks / Trade-offs

- **Authored geometry is less detailed than a scan** → expose all A coordinates/shapes, show labeled multiview geometry at the first visual opportunity, and require human acceptance; do not describe it as individually measured anatomy.
- **Simplified coupling can look mechanical despite meeting limits** → keep numeric curves inspectable, exercise them in isolated and combined views, and let the human reject naturalness. Changing a curve requires revising this dossier and affected checks.
- **Rigid thoracic geometry and flexible cartilage guides simplify rib mechanics** → preserve rigid rib lengths, label guides and regional approximations, and make no breathing or tissue-force claim.
- **A coordinate-perfect model can still have an implausible rib cage** → add relational shape/topology checks independent of the exact-coordinate goldens, show the focused thoracic preview before the expensive complete rerender, and retain the human visual gate. The numerical bounds remain authored choices, not anatomical validation.
- **Guide-to-guide attachments can follow stale frames instead of visible cartilage** → resolve an acyclic control-point dependency graph at every pose and measure closure on the actually evaluated guides. Keep the sternum rigidly anchored to T1 so SC closure does not depend on guide deformation.
- **Projection-based W proportions do not determine complete 3D anatomy** → use them only for the four named ratios and explicitly mark all remaining dimensions as A.
- **Many-to-one humanoid mapping loses anatomical detail** → report losses; do not claim an unperformed FK/VRMA export round trip.
- **Reference materials contain separately licensed figures** → use the cleared authored text/tables only; do not import or trace excluded illustrations.
- **Workbench/platform differences can affect pixels** → freeze the reference Blender build and actual renderer/platform metadata; compare repeated clean runs there.
- **No prior runtime package exists** → introduce commands and dependency locking explicitly in this change, keeping implementation separate from planning artifacts.

## Migration Plan

1. Obtain human approval of both capability specs and this complete numeric dossier; the presence of `design.md` alone is not approval.
2. Implement the source schemas/data and validation first, then the generated rig, diagnostics, and review workflow using the future `tasks.md` checklist. Do not populate `dist/`.
3. Run implementation checks; then independently reconstruct and review. Fix failures without changing acceptance criteria; bring any required criterion or anatomy revision back to planning.
4. Present the pack for human visual approval. Archive only after that approval and all tracked work are complete.

For the confirmed thoracic revision, update canonical geometry, sternal parent/local transforms, named landmarks and cartilage bindings first; preserve body/attachment IDs and all unrelated conventions. Update the closed binding schema, evaluator, independent mesh/guide measurements, nominal goldens, relational negative regressions, scene source and command documentation. Produce the focused neutral/T-pose thoracic preview and report its shape metrics before the complete multi-stature diagnostic/repeat-render pipeline. An early preview is development evidence; it does not replace independent review or human gate 2. Reopen the affected checklist items, regenerate every prepared-input source hash and affected output, and repeat the complete required acceptance checks into fresh directories. Never mix old meshes, hashes, metrics, and new geometry in one acceptance verdict.

There are no published runtime consumers to migrate. Preserve earlier outputs and the existing reviewer report as historical evidence until renewed review replaces the verdict with an explicitly identified new source snapshot. Human gate 2 remains rejected/pending for the current shape, regardless of the previous numeric PASS. Rollback of the revision restores only its own source changes from an explicit saved baseline; it does not remove the earlier implementation, unrelated edits, or shared output. Future muscle work references stable body-local attachment IDs and cannot silently replace this profile or its transform convention.

### Approved action-direction correction (2026-10-21)

The human approved correction of three reversed action directions before independent review: right hip external rotation uses -Z, forearm pronation uses the proximal-directed radius-to-ulna line, and dependent tibial twist uses distal -Z. Anatomical meanings follow H authored text, chapters 1 and 3; no illustrations are used. Absolute bilateral direction tests must verify lateral toes at hip external +20 degrees, upward radial/thumb direction at elbow 90 and forearm p=0, and medial anterior tibial direction at knee 30. These checks must reject the former sign choices independently of action decoders. The 80-degree forearm offset is a fixed-axis approximation, so midrotation is not claimed to reproduce an exact right-angle palm orientation.

This refines the first unreleased dossier. Regenerate canonical mobility records, affected schema convention fields, solver/independent measurement logic, golden tables, prepared inputs, all renders, and metrics; invalidate stale cached acceptance evidence while retaining historical reports. No published poses need migration. That action-direction correction preserved geometry; the later confirmed thoracic revision supersedes only that preservation for ribs, sternum, and costal guides. Preserve right-handed coordinates, units, wxyz/rest-relative rotations, mirrored-side policy, action bounds, cohort observations, 90-degree squat, 160-degree arm raise, 60-degree stepping knee peak, and every existing acceptance tolerance except changes explicitly superseded by the later R3 squat dossier. Derived hip/hindfoot actions and pelvis/ankle trajectories follow the corrected formulas above.

R3 approval recorded (2026-10-21): the human explicitly approved the complete numerical squat/mass/ankle revision and authorized implementation, full regeneration and independent review. Human visual gate 2 remains pending.
