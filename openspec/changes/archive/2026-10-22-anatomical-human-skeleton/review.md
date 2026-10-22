# Independent review: anatomical-human-skeleton, squat R3

Date: 2026-10-22. Verdict: **PASS WITH NOTES** for the independently reproduced
automatable and numeric requirements. **Human visual gate 2 remains pending**
for the revised thorax and revised squat. No open implementation finding remains.
Passing authored shape/static-mass bounds establishes approved dossier
conformance, not anthropometric accuracy, clinical validity or dynamic balance.

## Scope and evidence lineage

Fresh post-fix output root (`R`):
`build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/`.
The old R2 report is preserved as `R/previous-review-r2.md`. Initial R3 evidence,
including the original major finding, remains in the parent independent directory.
Developer builds, prepared inputs and renders were not reused as acceptance proof.
The independent CLI runner executed fresh pipeline commands under reviewer
ownership; this reviewer audited sources, measurements, retained outputs, images
and verdict. Root only orchestrated.

Read current AGENTS.md, reviewer role, proposal, both capability deltas, complete
design and tasks. See [checklist](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/checklist.md),
[scenario map](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/acceptance-map.md) and [commands](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/commands.md).
The current governance amendment is part of the frozen snapshot.
The [source snapshot](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/source-snapshot.json) SHA256 is
`6cb031d5a0b5a3cf570e8d4f4fd926e45567fea19f937342e37854e91205cb3c`. [Final source comparison](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/source-final-check.json)
finds zero changes in reviewed immutable sources and zero source/implementation
mismatches in all three native builds and both render passes. Only mutable
review.md/tasks.md are excluded from the start-to-finish comparison.

Headless Blender **5.2.2 LTS**, build **d13f752e3b9c**, was invoked through the
resolved executable with `--background --factory-startup`; no GUI state was used.
MPFB/Rigify and bake/export are explicit non-goals of this change. Dependencies
remain pinned. Sandboxed Blender startup SIGSEGV was an execution-environment
failure; the authentic logs are preserved and the complete escalated run passed.
No engine, bounds or coverage was changed to obtain a pass.

## Reproduced gates

| Gate | Independent result | Evidence in R |
|---|---|---|
| Schema and strict OpenSpec | PASS: canonical inventory, mapping, provenance and closed mass contract | `validation.json`, `openspec-validation.log` |
| Complete suite | PASS: 123 tests, 179.319 seconds, exit0 | `unittest.log` |
| Native H=1.50 m | PASS: 900 samples / 5,714,431 metrics | `stature-1.5-metrics.json` and sample shards |
| Native H=1.70 m | PASS: 900 samples / 5,714,431 metrics | `metrics.json` and sample shards |
| Native H=1.90 m | PASS: 900 samples / 5,714,431 metrics | `stature-1.9-metrics.json` and sample shards |
| Dense continuity/action/coupling/closure | PASS: 46,271 poses, all 32 fixtures | `metrics.json:dense` |
| Dense actual-mesh floor | PASS: 46,271 poses | `metrics.json:dense_floor` |
| Three-stature normalized evaluated comparison | PASS: 4,498 checks, including mass bindings | `metrics.json:stature_comparison` |
| Dense squat at each stature | PASS: 2,181 samples each at 1.5/1.7/1.9 m | `metrics.json:stature_balance` |
| Dense record retention and independent arithmetic | PASS: 8,724 records in four reports, 104 extrema entries | `retention-audit.json` |
| Actual native squat arithmetic | PASS: 87 observations, all three coefficient variants | `independent-mass-arithmetic.json` |
| Two clean renders | PASS: 1,872 identical decoded PNG pairs | `render-repeatability.json` |
| GIF timing | PASS: 192 previews; max duration error 3.33333333 ms <10 ms | `gif-timing.json` |
| Local pack links | PASS: 33 HTML pages, 2,593 links, zero missing targets | `link-check.json` |

All three native builds contain 176 bones/360 meshes. Every delivered sample
checks actual evaluated transforms, vertices, rigid scales, landmarks,
attachments, scene, contacts, floor, timing and loop closure. The dense audit
uses canonical transforms, not tens of thousands of separately built Blender
scenes. Its floor proof uses actual exported mesh vertices and conservative
cubic Bezier guide hulls, expanded by tube radius/float padding, with complete
vertex fallback when the hull cannot certify clearance. No tolerance was relaxed.
Fresh native frame agreement and normalized geometry/mass scaling are separate
gates. [Measured extrema](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/verification-summary.json) retain worst metric
IDs, units, expected values and tolerances; original sample shards remain present.

## Squat and whole-body static assessment

The bottom uses 90-degree knees, 20-degree ankles, 25-degree pelvis pitch and 10-degree lumbar flexion, approved flat-foot
closure, 80-degree arm elevation and the same 60-bisection construction. The ankle positive limit
is 20 degrees; cohort reference observations 13.8F/12.7M and walking ankle 12 degrees are unchanged.
The independently derived scalar/matrix regression covers the construction.
Ten actual native fault mutations include the former squat and rearward upper
body; both fail `balance.reference_margin`. The old 12-degree construction has
valid planted contacts but COM Y=-0.0650806008562H, behind the heel at -0.025H.
The suite also rejects missing/forged/equalized mass, shifted/degenerate measured
support, absent contacts and invalid source inventories; intended targets cannot
hide changed observed support. Fault scenes are temporary; assertions/log remain.

Six measured permanent heel/ball witnesses form the support hull. Sixteen actual
evaluated carrier-bone mass points, including unrendered tissues, supply COM.
Native mass points are exported from evaluated matrices, not prepared COM
metadata. The reference/male/female coefficients are normalized separately.
Independent weighted fsum and supporting-line arithmetic import no production
balance/kinematics/solver routine. Reference native binding maximum is 1.11446232196e-07 m
against 1e-4H; exact worst sample/limit is retained in the summary.

Across the complete dense grid at all heights, minimum nominal margin is
**0.0134132800435H >=0.010H**. The minimum three-variant margin minus the
fixed 0.005H placement allowance is **0.00818377852609H >=0.005H**.
Independent retained-grid COM residual is at most **2.22045e-16 m** and margin
residual **2.08167e-17H**, each <1e-12; source-bound point residual is
**1.52586e-16H** against 1e-4H. Every retained record includes body frames,
mass points, support positions, contacts, checks, COM XYZ, normalized fractions,
support hull/edge margins, worst edge, all variants, uncertainty, units, beat and
sample ID. All extrema values/identities are independently rebuilt. Links are
explicit **nearest delivered render context**, with exact-match flags; they do
not claim each dense beat was independently rendered. All image/page paths exist.

Dense records contain all 180 canonical frames, including four declared omitted
semantic structures; native rigs contain 176 bones. An initial reviewer helper
mistakenly required the native count in dense records. Its original failed
result is preserved and explained in `R/commands.md`; the corrected helper
requires exact equality with the complete canonical ID set. No source, bound
or measurement arithmetic was changed.

## Preserved thorax and earlier quality contracts

Fresh native/thoracic metrics retain measured rib ring controls and sternal
shell midsurfaces, neutral shape/relational bounds, T1-carried sternum/SC closure,
cartilage 1–7 insertions, 8–10 solved-cartilage endpoints/midpoints and free 11/12.
The independently reopened native model confirms 176 bones, sternum parentT1,
32 shell vertices and unit scales; see `native-model-inspection.json`.
Frozen scapula/patella, wrong hip sign, stretched shank, root drift, uniform ribs,
bony arch and stale midpoint faults still fail their intended measurements.
Absolute anatomical direction witnesses, ROM boundary/outside rejection,
couplings, canonical/previous contact seeds, mirror involution, rigid scales,
loop closure, masks, sampling and fixed scene remain covered by the full suite
and fresh all-fixture metrics. No convention was silently changed.

Reference native extrema include angular residual 0.0298540080143 degrees,
scale deviation 4.76837158203e-07 ratio, rigidity 0 m, root translation
4.76837158647e-09 m, pin-target residual 3.37174788401e-09 m and
sliding 0 m. Detailed per-height tolerances and worst
samples remain in `verification-summary.json`; none is substituted by a visual
opinion. Source scope comparison preserves all 180 structure records, scene,
groups and mapping; R3 changes only the approved mass metadata, squat/ankle
intent/bound and provenance. The retention correction changes reporting only.

The following maxima span all three fresh native reports; the tolerance shown
belongs to the actual worst measurement (meter tolerances scale with stature).

| Measurement | Actual maximum residual | Tolerance |
|---|---|---|
| Angular residual | 0.0298540080143 degrees | 0.1 degrees |
| Scale deviation | 4.76837158203e-07 ratio | 1e-06 ratio |
| Rigid vertex displacement | 0 m | 1.5e-06 m |
| Mechanical length residual | 6.92728301666e-08 H | 1e-06 H |
| Root translation | 5.96046448309e-09 m | 0.00015 m |
| Pin-target residual | 4.21468485501e-09 m | 0.0015 m |
| Contact sliding | 1.38777878078e-17 m | 0.0019 m |
| Loop origin | 1.93491956313e-20 m | 0.00019 m |
| Loop orientation | 0.014396088018 degrees | 0.1 degrees |
| Actual mass binding | 1.28946820737e-07 m | 0.00019 m |
| Thorax SC closure | 1.22878123093e-07 m | 0.00019 m |
| Cartilage rib endpoint | 5.96093012064e-07 m | 0.00019 m |
| Cartilage distal endpoint | 4.77069932031e-07 m | 0.00019 m |
| Cartilage midpoint | 4.52298070099e-07 m | 0.00019 m |

Lowest delivered mesh point is -6.93889390391e-18 m, against the associated
lower bound -0.00015 m. Dense certified floor bound
is -3.69548813772e-09 m, against
-0.00017 m. The curve-hull certificate is
conservative; it does not omit overshoot between sampled controls.

| Dense continuity metric (units in key) | Actual maximum | Upper bound |
|---|---|---|
| max_driving_input_step_deg | 0.249999928555 | 0.25 |
| max_orientation_step_deg | 0.249999671943 | 5 |
| max_origin_step_h | 0.00211764467293 | 0.02 |
| max_step_beats | 0.01 | 0.01 |

The time/step comparisons retain the stated 1e-9 floating comparison allowance.
Normalized evaluated-vertex residual is
1.75319666988e-08H,
rest-origin residual 7.01304917305e-08H
and orientation-matrix residual
0, each
against 1e-6. Source mass-point coefficients stay fixed while positions scale.
The actual normalized native mass-point residual is
5.14293343179e-08H
against 1e-6H; normalized coefficient residual is
0 against 1e-12.

## Licensing and provenance

PASS; see [source audit](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/source-audit.md) and
[primary-column audit](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/source-column-audit.json). Primary published
Kudzia and Kasahara XML/permission evidence is retained in the parent review
directory. Both explicitly license the used text/data under CC BY4.0, compatible
with commercial adaptation with attribution; current register/notices/output
credits preserve authors, license links and changes. Kudzia **Proposed Tables 3/6**
were independently parsed: 53 checks PASS, reference raw total 74.15. No ECM,
regression/MeanValue columns, participant scans, figures or third-party code were
used. Kasahara supplies qualitative context, not numerical exercise targets.
The specifically cleared first-edition OpenStax text and wrist credits remain;
current OpenStax editions, permission-only figures and the watermarked comparison
image are excluded. Head/trunk/pelvis/foot placements, skeleton adaptation and
cohort averaging are authored approximations. The allowance is mathematical,
not a clinical confidence interval. Static assessment makes no dynamics claim.

## Findings and remaining human gate

| ID | Severity | Requirement/scenario | Evidence and resolution | Suggested direction |
|---|---|---|---|---|
| R3-RET-01 | Major, RESOLVED | Squat / Measure squat static balance independently; tasks 7.8/9.4: retain observations/extrema | Initial dense output discarded successful rows. Supported reporting now retains all rows; fresh 123 tests and independent full 8,724-record arithmetic/extrema/link audit PASS. Historical finding/output preserved. | Preserve complete retained output contract in later changes. |
| None open | — | Applicable automatable/numeric gates | Fresh source/native/dense/render proof above | Proceed to explicit human visual decision. |

Reviewer visual observations are opinion, recorded in
[visual inspection](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/visual-inspection.md). The squat shows forward knees,
inclined shanks, planted feet and a forward torso; the unannotated view and COM
card should be assessed together. The ribs remain stylized/faceted and the
sternum schematic. Numerical approval does not resolve the human silhouette
and motion-readability decisions.

Open [the fresh pack](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/index.html) and [short index](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/index.md).
Direct squat views: [unannotated counts](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/composites/squat-60-side-static.png),
[COM/support counts](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/composites/squat-60-side-static-balance.png) and
[onion overlay](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/composites/squat-side-onion.png).

| Thorax view | Context | Isolated |
|---|---|---|
| Front | [sheet](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/composites/neutral-thorax-front.png) | [sheet](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/composites/neutral-thorax-front-isolated.png) |
| Side | [sheet](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/composites/neutral-thorax-side.png) | [sheet](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/composites/neutral-thorax-side-isolated.png) |
| Three-quarter | [sheet](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/composites/neutral-thorax-three-quarter.png) | [sheet](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/composites/neutral-thorax-three-quarter-isolated.png) |

Fresh [native model](../../../build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/reference/skeleton.blend).
Human must explicitly accept/reject the corrected squat depth/posture/readability
and revised thorax silhouette/connections, with concrete view/frame notes if
rejected. **Human visual approval remains PENDING.** No other applicable numeric
gate lacks evidence. Bake/export round trip and production via-circles are N/A:
this change explicitly excludes distribution baking/export and introduces no
production circular segment. The change has not been archived.
