# Foot binding dossier blocker

Status: the human approved the exact bounded design correction on 2026-10-25 with "Да, исправить design и продолжить" in response to the main agent's correction question. The planning correction is now applied in `design.md` and recorded in `approvals.md`. Implementation/native verification and human visual acceptance remain pending; this record retains the original blocker and read-only evidence, and is not a native acceptance verdict. The main agent requested the original bounded read-only architectural check during implementation on 2026-10-25.

## Finding and affected requirement

The originally frozen design section 4.5 assigned hindfoot-only weights through y=0.075H, blended hindfoot to MTP from y=0.075H to 0.085H, then assigned MTP-only weights. With the specified preserve-volume reference deformation and existing `forefoot-rocker` motion, that superseded band puts actual sole-ring vertices below the unchanged floor limit.

Violated contract: `character-models / Supporting surfaces preserve contact and floor constraints`, scenario `Check the sole beyond a rest-pose appearance`, requires every evaluated surface vertex at z >= -1e-4H. The same threshold is frozen in design section 5. This is a numerical incompatibility between the authored binding and the floor requirement, not a reason to weaken that requirement or change movement/root/floor/camera.

Canonical supporting ball anchors belong to `toe.1.R` and `toe.5.R`, both children of `mtp.R`; they are not hindfoot-only carriers. Neutral positions in stature units are:

| Anchor | Carrier | World position/H |
|---|---|---|
| `contact.heel.R` | `calcaneus.R` | (0.055, -0.025, 0) |
| `contact.medial_ball.R` | `toe.1.R` | (0.037, 0.075, 0) |
| `contact.lateral_ball.R` | `toe.5.R` | (0.075, 0.075, 0) |

The left side is the canonical mirror. At rocker beat 2, the hindfoot is plantarflexed 30 degrees while MTP restores the toe/ball frame to its planted world orientation. A hindfoot-only sole station at y=0.075H therefore does not follow the ball carrier. Blending after that station introduces the below-floor region. Point-to-point mismatch with a corresponding rest vertex is not by itself a closest-sole-distance failure; the confirmed blocker here is the full vertex floor bound.

## Read-only arithmetic results

The calculation uses the existing canonical evaluator, rest matrices and the design's normalized dual-quaternion reference, not Blender. It samples beats 0 through 4 inclusive at spacing 0.01 (401 samples), and every foot longitudinal ring produced by the frozen four-interval subdivision. A lower-half sole vertex at theta=3*pi/2 has x=0.055H and z=0 in rest, so the tested curve consists of actual specified vertices, rather than an inferred bounding box.

| Band [start,end]/H | Lowest sole z/H | Worst beat | Result against -0.0001H |
|---|---:|---:|---|
| Original frozen [0.075,0.085], superseded | -0.0008916300730211087 | 2.00 | Fail |
| Approved correction [0.065,0.075] | approximately +2.1182e-16 | numerical roundoff varies | Pass for this calculation |
| Alternative [0.060,0.075] | approximately +2.1182e-16 | numerical roundoff varies | Pass, wider change unnecessary |

At H=1.70m the original frozen minimum is approximately -1.516mm; the permitted minimum is -0.170mm. The approved correction leaves all surface shape tables, topology, skeletal transforms, contact anchors/targets and movement intent unchanged. Squat MTP extension is zero, so moving this band does not alter squat foot deformation.

**Approved minimal correction:** retain a 0.010H smoothstep band but move it to y=0.065H..0.075H; use hindfoot-only weights at/below 0.065H and MTP-only weights at/above 0.075H. At the supporting ball station the sole then follows the actual MTP carrier. The human's approval covers this authored binding correction and continued implementation only. Native Blender agreement, complete diagnostic/stature coverage and human visual acceptance remain required; this arithmetic and the planning approval are not their substitute. Delta specifications and task acceptance bounds need no change, and no task completion is recorded by this correction.

## Other dossier checks

- Named arm/leg carriers and joint landmarks resolve. Rest arms run along X, so the projected +Y limb section axis is nondegenerate; rest legs run along -Z and also admit that axis.
- Torso carrier origin z/H values are strictly increasing: pelvis 0.4895, L5 0.545, L1 0.625, T12 0.645, T6 0.729, T1 0.799, C7 0.815, C3 0.851, C1 0.869. Their rest and anatomical-neutral origins and bases agree. The proposed torso z-ring weighting is therefore not blocked by a rest/neutral mismatch.
- Mannequin shoulder/hip/head junction readability and native/reference preserve-volume agreement remain testable risks; this check asserts no native or human visual verdict.

## Reproduction

Run from the repository root. This command reads sources and prints arithmetic results; it creates no HML build/render artifacts and launches no Blender. `--no-cache` avoids the host uv-cache permission issue encountered by the first attempt. All arithmetic below is a disposable design calculation, not implementation code or a new entry point.

```bash
uv --no-cache run --locked --no-sync python - <<'PY'
from pathlib import Path
from humanmotionlib.validate import load_sources
from humanmotionlib.diagnostics import DiagnosticEvaluator
from humanmotionlib.poses import rest_pose
from humanmotionlib import math3d as m

sources, _ = load_sources('adult-reference-v1', Path.cwd())
profile = sources['profile']
height = profile['stature_m']
rest = rest_pose(profile)
evaluator = DiagnosticEvaluator(sources)
stations = [-.040, -.025, 0, .045, .075, .100, .118]
rings = [a + (b-a)*j/4 for a,b in zip(stations,stations[1:])
         for j in range(4)] + [stations[-1]]

def multiply(a, b):
    w,x,y,z = a
    v,p,q,r = b
    return [w*v-x*p-y*q-z*r, w*p+x*v+y*r-z*q,
            w*q-x*r+y*v+z*p, w*r+x*q-y*p+z*v]

def rigid_dq(carrier, frames):
    rotation = m.mm(frames[carrier]['rotation'],
                    m.transpose(rest[carrier]['rotation']))
    translation = m.sub(frames[carrier]['position_m'],
                        m.mv(rotation,rest[carrier]['position_m']))
    real = m.quaternion(rotation)
    return real, m.scale(multiply([0,*translation],real),.5)

def sole_vertex(y, frames, band):
    t = max(0,min(1,(y-band[0])/(band[1]-band[0])))
    weight = t*t*(3-2*t)
    q1,d1 = rigid_dq('hindfoot.R',frames)
    q2,d2 = rigid_dq('mtp.R',frames)
    if m.dot(q1,q2) < 0:
        q2,d2 = m.scale(q2,-1),m.scale(d2,-1)
    real = m.add(m.scale(q1,1-weight),m.scale(q2,weight))
    dual = m.add(m.scale(d1,1-weight),m.scale(d2,weight))
    length = m.norm(real)
    real,dual = m.scale(real,1/length),m.scale(dual,1/length)
    dual = m.sub(dual,m.scale(real,m.dot(real,dual)))
    translation = m.scale(multiply(dual,m.qinverse(real))[1:],2)
    return m.add(m.mv(m.qmatrix(real),[.055*height,y*height,0]),
                 translation)

for band in [(.075,.085),(.065,.075),(.060,.075)]:
    worst = (float('inf'),None,None)
    for sample in range(401):
        beat = sample/100
        frames = evaluator.evaluate('forefoot-rocker',beat)['frames']
        for y in rings:
            value = sole_vertex(y,frames,band)[2]/height
            if value < worst[0]:
                worst = (value,beat,y)
    print('band/H',band,'minimum z/H, beat, rest y/H',worst)
PY
```

The calculation intentionally uses a raw quaternion product for dual parts: existing HML `qmul` validates unit rotation quaternions and is not a general product for a translation/dual quaternion.

Source SHA-256 identities at the time of this check:

| Source | SHA-256 |
|---|---|
| `rig/profiles/adult-reference-v1.yaml` | `e93d232f8b2f64a06f8a8064b6fe0dcdcbd0afc3050f27faa67799906fd94e41` |
| `rig/mobility/adult-reference-v1.yaml` | `9d3316fd6ed72a645ceb4a0e88bb748ee07b58c19bfa7def8a8d18bdee6108cc` |
| `rig/diagnostics/forefoot-rocker.yaml` | `7143a4ad7b9a0c88e0e116753b59ca2ef6a32409211fbd59d4e52a16bc2fed71` |
| `design.md` before any approved correction | `49d616e82ace836387d1c30ea9786553b6960ab05e6026c03afb839d3f242afa` |
