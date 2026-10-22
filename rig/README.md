# Anatomical skeleton sources

`profiles/adult-reference-v1.yaml` is the expanded numerical
profile for the approved skeleton change. It contains 180 structure records
and 283 landmarks. Its canonical-record checks pass, including the corrected
foot envelope below. Generated geometry and independent review remain separate
acceptance requirements; schema validity is not anatomical acceptance.

## Numeric record contract

Positions and dimensions are meters at the recorded reference stature 1.70 m.
Landmarks explicitly identify their reference frame; the current dossier's
neutral landmarks use world coordinates. A structure's `origin_m` is its
neutral world origin and `basis` maps neutral body-local coordinates to world.
Geometry points/centers and attachment transforms are body-local. Separate
`rest_translation_m` and `rest_orientation` describe the solved T-pose relative
to the declared parent. They do not redefine anatomical-neutral actions.

Primitive dimensions are expanded numbers, not executable expressions.
Transverse radii on the sternum's `elliptic_capsule` are lateral/anterior;
its two endpoints define the longitudinal axis. Spheres and ellipsoids retain
their dimensions. Swept shafts, shells and subtractive skull recesses have
explicit records; guides are identified as helpers and non-rigid where stated.
Anatomical joint centers and contact-envelope witnesses are distinct.

The inventory distinguishes individual, fused, grouped, and omitted items.
Named local attachments remain stable even where articulation is fixed.
Hands/fingers are fixed geometry in this change, while the MTP action drives
the grouped toes. The world root is diagnostic placement intent, distinct from
pelvis motion and canonical anatomical structures.

## Provenance and bounds

Every landmark/structure carries provenance resolving to the cleared portions
of `docs/used-materials.md`. Authored geometry and coordinates do not claim to
be measured individual anatomy. Only four mechanical segment ratios use the
symmetric adult DXA adaptation; their tolerance is `1e-6 H`. General coordinate
and shape conformance uses `1e-4 H`; rigid posing invariants use `1e-6 H`.
See the change's numerical dossier for the full rationale and limitations.
These records import no atlas mesh, third-party illustration, or motion clip.

## Approved foot envelope

The human chose to preserve the numeric primitive records and correct the
design's aggregate claims to 0.158 H length and 0.050 H width. At H=1.70 m,
these are 0.2686 m and 0.0850 m. The front boundary includes the second toe's
0.006 H cap radius. No anatomical primitive, contact anchor, or tolerance was
resized. Profile tests measure these envelopes independently on both sides.
See `docs/anatomical-human-skeleton-preflight.md` for the derivation and decision.

## Mobility source

`mobility/adult-reference-v1.yaml` separates degree-valued anatomical actions
from meter-valued pelvis placements. Each action records its neutral offset,
axis/frame, finite operating bounds, ownership, and independent/coupled/fixed
status. Action frames refer to neutral anatomical frames attached to bodies;
they are distinct from the body's longitudinal mesh/bone basis. Inherited
proximal rotation and that explicit basis change must be used in evaluation.
Axial-vector mirroring uses `-J` for the same named positive action. Forearm
line endpoints locate the radioulnar axis, with rotation direction given by
the action's signed axis. Plane-dependent shoulder directions use the declared
sector/girdle construction rather than treating their reference axis as fixed.

Closed coupling types carry numeric parameters, including region counts,
shoulder sector knots, patellar knots, and fixed oblique axes. Composition
orders are explicit. Unsupported/fixed controls cannot become free Euler
rotations. The eleven Faisal reference rows retain both sex-specific means
and their cohort; they are not operating maxima, and are not merged with the
DXA proportion cohort. The data tests verify those observations independently.

## Ownership and humanoid adapter

`body-groups.yaml` assigns each named action/placement and generated transform
channel to exactly one smallest group. Computed transform ownership does not
authorize a diagnostic to key another group's action. Shoulder-girdle channels
belong to the arms even though their parent is T1; hands/digits belong to arms
and feet/toes to legs. Fixed parent-following remains distinct from intent writes.

`humanoid-map.yaml` resolves all 15 required names and seven optional proxies
from the cleared three-vrm vocabulary. It reports the 33 omitted optional
semantics and internal anatomical detail. Articulation frames may supply a
semantic joint; non-anatomical helper geometry is not represented as a public
humanoid bone. Many-to-one spine mappings, knee/radiocarpal translations,
scapular/patellar detail, fixed digits, and export limitations remain explicit.
MIT vocabulary notices are retained in `THIRD-PARTY-NOTICES.md`. This is an
adapter contract; it claims no MPFB/Rigify mapping or completed export round trip.
