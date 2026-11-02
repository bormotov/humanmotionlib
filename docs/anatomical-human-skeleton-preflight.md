# Anatomical skeleton implementation preflight

Status: trajectory and aggregate foot-dimension contradictions corrected with
explicit human authorization, 2026-10-20. Neither correction changes numerical
acceptance tolerances. No built skeleton or accepted review pack is claimed;
`tasks.md` remains the implementation progress record.

## Original finding (retained as a negative regression)

The frozen walking-in-place construction in
`openspec/changes/anatomical-human-skeleton/design.md`, section 7, penetrates
the floor during lift-off and touchdown. This violates `joint-mobility`:

- Requirement **Contact and floor measurements**, scenario **Measure planted
  and rolling foot support**: visible geometry cannot go below `-1e-4 H`.
- Requirement **Diagnostic timing and stable rendering**, scenario **Verify
  rendering stability and determinism**: floor/root changes cannot conceal
  penetration.

The independent regression `tests/test_walking_dossier.py` directly evaluates
the approved formulas with scalar matrix arithmetic. It does not use a rig,
Blender solver, or an implementation success flag. Its measured point is the
third toe cap's neutral bottom surface point: ankle-relative
`(0, 0.107, -0.040) H`. The design specifies a toe cap center Z of `-0.034 H`
and radius `0.006 H`, so that point exists on its rigid surface. The MTP action
is zero in this diagnostic. Mirroring preserves Z, so the finding applies to
either side's swing. One penetrating surface point suffices to disprove
complete-mesh clearance; this test does not claim to replace the later full
evaluated-mesh checks.

| Sampling | Witness beat in first swing | Surface Z/H | Z at H=1.70 m | Allowed minimum |
|---|---:|---:|---:|---:|
| Dense 0.01-beat grid | 0.35 | -0.004545930 | -7.728082 mm | -0.170000 mm |
| Delivered frames, BPM 60 | 0.40 (also 1.60) | -0.004160867 | -7.073474 mm | -0.170000 mm |
| Delivered frames, BPM 120/180 | 1/3 | -0.004526772 | -7.695513 mm | -0.170000 mm |

Neutral endpoints pass. Passing an apex-clearance check does not ensure
clearance during the rest of the swing. For small swing weight `w`, the
prescribed hip/knee/ankle combination pitches the forefoot down to first order,
while ankle elevation grows only to second order. This is a trajectory issue,
not floating-point noise or a missing renderer setting.

## Reproduce

The command sequence below is historical reproduction guidance from the
pre-Make workflow. It records how that earlier calculation was checked; it is
not the current project setup route. In a current checkout, prepare the project
environment and package with `make dev`. The equivalent focused regression
check was verified with the configured project interpreter:

```sh
make dev
build/project-tools_r1_contributor_current_environment/environment/bin/python -m unittest tests.test_walking_dossier
```

The focused command above passed 5 tests in the configured environment. The
old `uv sync`/`uv run` commands are retained only as a record of the historical
preflight workflow.

The seven runtime/walking tests pass, including checks that the original
construction is rejected and that the corrected construction meets preflight
bounds. The two foot-envelope methods now check the human-approved aggregate
dimensions on both sides. No test is skipped or marked as an expected failure.

## Authorized correction

The human authorized correcting the trajectory. Section 7 of the numerical
dossier now retains `knee=60w` and `ankle=12w`, deriving hip orientation and
hindfoot action so the rear-foot world orientation is identity and ankle X
stays fixed. The fixed pelvis is unchanged. The five-row reference table
records the exact construction's samples. Apex foot-envelope clearance is
`0.082663752 H`; the maximum sampled hip envelope score is `0.245596844`
against limit 1. Tests cover all delivered BPM grids and 0.0025-beat steps
(primary knee action increments below 0.25 degrees), neutral closure,
orientation, limits, and reference values. The original floor/root, body
dimensions, limits, knee/clearance targets, duration, contact events, and
acceptance tolerances remain unchanged.

This removes the specific planning blocker. It does not establish full rig,
mesh, contact, continuity, rendering, or independent-review acceptance; those
remain tracked implementation requirements, including the complete evaluated
geometry floor test. The original trajectory is retained only as a negative
regression with its measured penetration above.

## Corrected finding: inconsistent foot dimensions

While expanding task 2.2 into numeric records, the supplied foot geometry and
the design's stated overall dimensions proved inconsistent. This affects
`anatomical-skeleton`, requirement **Approval-ready anatomical reference dossier**,
scenario **Verify geometry against the approved dossier**. Shape-envelope
tolerance is `1e-4 H`.

The provisional source profile and `tests/test_profile_dossier.py` make this
reproducible without Blender. They measure neutral primitive envelopes in
world space, including toe end-cap spheres of the declared radius. The
specified cardinal extrema are represented by the prescribed mesh resolution.
The anterior boundary is set by the second toe cap; the posterior boundary
by the calcaneus. The first/fifth toe caps set the lateral bounds.

| Quantity | Superseded design text | Preserved numeric primitives / approved value | At H=1.70 m |
|---|---:|---:|---|
| Posterior Y/H | -0.040 | -0.012 - 0.028 = -0.040 | -0.0680 m |
| Anterior Y/H | 0.112 implied | 0.112 + 0.006 = 0.118 | 0.2006 m |
| Length/H | 0.152 | 0.118 - (-0.040) = 0.158 | 0.2686 m instead of 0.2584 m |
| Width/H | 0.055 | (0.020 + 0.006) - (-0.018 - 0.006) = 0.050 | 0.0850 m instead of 0.0935 m |

Both original differences exceeded `1e-4 H`. The human explicitly chose to
preserve the given primitives and correct the aggregate dimensions to length
0.158 H and width 0.050 H. The numerical dossier and envelope tests now use
that decision, retaining the original `1e-4 H` tolerance. The canonical profile
has not been resized. Mechanical limb ratios, structure references, local
bases, quaternions, source provenance, and the corrected envelopes are checked
separately; these checks do not replace eventual evaluated-mesh verification.

## Approved direction refinement (2026-10-21)

The earlier calculations above record the preflight history. The human subsequently authorized correcting hip external, forearm pronation and dependent tibial direction signs. The approved design now gives stepping apex clearance `0.076450283 H` and maximum hip envelope score `0.171179111`. Canonical fixtures preserve their principal amplitudes. New tests assert physical anatomical directions independently of angle decoders; earlier opposite-sign numeric/raster results are stale and require rebuilding.
