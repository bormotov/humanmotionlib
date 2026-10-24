# Skeleton tooling

Run commands from the repository root. HML's host Python is managed by uv;
`.python-version` selects CPython 3.14 and `pyproject.toml` constrains it to
`>=3.14,<3.15`. `uv sync --locked --no-editable` creates the environment with exact
dependencies from `uv.lock`. Blender supplies its own embedded Python; it is
selected and verified through the pinned Blender executable and is not required
to match the HML host Python version.
Blender must be available as `blender` on PATH. The backend contract lives in
`pyproject.toml`: Blender 5.2.2 LTS, build `d13f752e3b9c`, reference platform
Darwin arm64. A different Blender version or build is an error. MPFB and Rigify
are not used. No tool requires a workstation-specific executable path or GUI state.

## Command contract

For a fresh local host check, create an empty run root directly under `build/`
with a five-part run identity, then keep its environment and uv cache inside it.
The example below is a single developer host-check attempt:

```sh
mkdir build/upgrade-host-python-314_r1_dev_try-1_host
export UV_PROJECT_ENVIRONMENT=build/upgrade-host-python-314_r1_dev_try-1_host/environment
export UV_CACHE_DIR=build/upgrade-host-python-314_r1_dev_try-1_host/cache
uv lock --check
uv sync --locked --no-editable
uv run --locked --no-sync hml check-environment
uv pip check --python "$UV_PROJECT_ENVIRONMENT/bin/python"
uv run --locked --no-sync hml validate --profile adult-reference-v1
HUMANMOTIONLIB_TEST_RUN_ROOT="$PWD/build/upgrade-host-python-314_r1_dev_try-1_host" \
HUMANMOTIONLIB_SOURCE_ROOT="$PWD" \
  uv run --locked --no-sync python -m humanmotionlib.check_host --test-root "$PWD/tests"
```

The installed `hml check-environment` command checks the interpreter, dependency
metadata and packaged resources. The explicit `humanmotionlib.check_host`
contributor command reports the selected test total, skips and the only two
modules excluded because they require real Blender: `tests.test_blender_backend`
and `tests.test_pipeline_faults`. It fails on an interpreter/metadata mismatch,
dependency import error, discovery error, empty selection or failed test. The
full reference command below remains unfiltered and must run with the pinned
Blender on the Darwin arm64 reference platform. The CI uv version is pinned in
`.github/workflows/host-python.yml`; local uv should use that same version for
reproducible lock operations. The workflow pins uv 0.13.5.

The following entry points are approved by the change design. Validation,
preparation, headless construction, numeric verification, render-pack assembly,
and HTML-only presentation regeneration are available. A command existing does
not establish complete OpenSpec acceptance; the task list tracks the checks.

```sh
uv run --locked --no-sync hml validate --profile adult-reference-v1
uv run --locked --no-sync hml prepare-skeleton --profile adult-reference-v1 --output build/anatomical-human-skeleton_r1_dev_try-1_build/input.json
uv run --locked --no-sync hml run-blender --input build/anatomical-human-skeleton_r1_dev_try-1_build/input.json --output build/anatomical-human-skeleton_r1_dev_try-1_build
uv run --locked --no-sync hml verify-skeleton --input build/anatomical-human-skeleton_r1_dev_try-1_build --output build/anatomical-human-skeleton_r1_dev_try-1_checks/metrics.json
uv run --locked --no-sync hml review-pack --input build/anatomical-human-skeleton_r1_dev_try-1_build --output build/anatomical-human-skeleton_r1_dev_try-1_pack
HUMANMOTIONLIB_TEST_RUN_ROOT="$PWD/build/upgrade-host-python-314_r1_dev_try-1_host" HUMANMOTIONLIB_SOURCE_ROOT="$PWD" uv run --locked --no-sync python -m humanmotionlib.check_host --test-root "$PWD/tests"
```

The runtime, wrapper, backend, and fault suites write all receipts and case
artifacts below a flat caller-owned run root. For a reviewer run, allocate a
fresh direct child of `build/` and point the suites at it; importing test
modules alone creates no run directory. The suite keeps each module's cases
under `cases/<module>/` and never rewrites another role's run. For example:

```sh
mkdir build/harden-backend-process-execution_r3_reviewer_try-1_checks
HUMANMOTIONLIB_TEST_RUN_ROOT=build/harden-backend-process-execution_r3_reviewer_try-1_checks ./.venv/bin/python -m unittest tests.test_runtime tests.test_run_blender tests.test_blender_backend tests.test_pipeline_faults
```

When this variable is unset, each suite lazily allocates its own fresh
developer-owned run root. A caller-supplied root must already exist and must be
a direct child of `build/` with five valid identity components.

### Supervised backend execution

Routine build and render work goes through `hml run-blender` or the
review-pack command. The runner resolves Blender from `PATH`, records the
resolved executable, and performs a pinned version/build probe before starting
the script. It writes one `backend-invocation/v1` receipt per probe and child
under `<run-root>/processes/<invocation-id>/outcome.json`, with separate stdout
and stderr logs, command/cwd/platform/Python identity, source hash, deadline,
process group, completion phases, exit or signal outcome, output hashes, and
cleanup status. A receipt is updated atomically as the invocation progresses.
Build scripts emit flushed `HML_PHASE` markers; `script_complete` is emitted
only after required files, including `skeleton.blend`, are saved.

The defaults are 30 seconds for the backend probe, 1800 seconds for a build,
14400 seconds for a render, and 30 seconds to acquire the checkout-wide backend
slot. Cancellation and timeout send TERM for up to 5 seconds, then KILL and
reap for up to 5 seconds. All overrides must be finite, positive, and no more
than 86400 seconds. The supervisor uses POSIX process groups and advisory file
locks; the pinned backend contract names Darwin arm64 as its reference
platform. The persistent lock file is `build/.backend-execution.lock`;
ownership state is recorded in `build/.backend-execution-state.json`. A
confirmed-dead owner can be recovered.
On Darwin, bounded `ps` snapshots of PID, process-group ID and process state
preserve the unreaped leader as an identity anchor where the reference Python
does not expose `waitid`. Zombie-only groups have no live work; missing,
malformed or unreadable observations remain ambiguous, and `EPERM` alone never
proves that an owned group is absent.
Unreadable or ambiguous state, or an unconfirmed cleanup, blocks later backend
work for operator resolution rather than risking overlap. The lock file remains
in place because unlinking an advisory lock can split ownership.

Every supervised command that launches Blender needs a fresh, caller-owned flat
run root under `build/`; its prepared `input.json` may be created in that same
root as shown above. Runtime APIs require an explicit owning run root and check
that it resolves beneath `build/` with a valid five-component run identity;
callers still allocate a fresh root and keep independent input/output roots
disjoint. Probe and script receipts/logs are written below that root.
The build runner accepts `--timeout-seconds` (default 1800 seconds for its
script child) and `--slot-timeout-seconds` (default 30 seconds per slot
acquisition). Its version probe has its own 30-second deadline. For example,
append `--timeout-seconds 2400 --slot-timeout-seconds 60` to the
`hml run-blender` command for an explicitly bounded longer build. The
review-pack command accepts the same options; its 14400-second execution
deadline applies to each render pass, not to the complete two-pass operation.
All timeout values must be finite, positive, and at most 86400 seconds.

The runner launches Blender with `--background --factory-startup
--python-exit-code 1` and invokes the packaged `humanmotionlib.build_skeleton`
entry script through the resolved PATH executable. Routine builds, renders,
and automated checks use the supervised `hml run-blender` or `hml review-pack`
commands. Do not invoke the internal Blender script directly; that bypasses
the supervisor's deadline, checkout slot, receipt and output validation.
The runtime requires POSIX process groups and advisory locks; the pinned
backend reference platform is Darwin arm64. It does not manage independent
checkouts or interactive Blender sessions.

The supplied backend failure evidence and its bounded hypotheses are recorded
in [backend-crash-triage.md](../docs/backend-crash-triage.md). That record keeps
application and operating-system reports correlated by timestamps and hashes;
it does not attribute the failures to a confirmed hardware or upstream cause.

| Command | Inputs | Outputs |
|---|---|---|
| `hml validate` | Selected profile, mobility, mapping, groups, fixtures, scene, schemas, source register | Validation diagnostics; nonzero status on invalid input |
| `hml prepare-skeleton` | Validated sources and pinned backend contract | JSON with solved transforms, exact timing, source/schema hashes, metadata |
| `hml run-blender` | Prepared JSON, factory-startup Blender | Generated skeleton, evaluated geometry/transform measurements, build metadata inside the selected build run root |
| `hml verify-skeleton` | Evaluated build measurements and canonical dossier | Per-metric measured/expected/bound/status records and coverage in `metrics.json`; nonzero status on failure |
| `hml review-pack` | Build outputs and fixed review scene | Clean renders, labeled sheets, GIFs, overlays, attribution/limitations, metadata and HTML index |
| `hml review-pack --html-only-from` | Complete verified review pack and a fresh output directory | Diagnostic HTML, presentation provenance, scoped HTML/link/hash verification; no Blender process or media rewrite |
| `humanmotionlib.check_host` | Explicit repository test root and caller-owned run root | Automated contributor checks; nonzero status on failure |

### Flat run roots and cleanup

Every independently managed build, check or review run is a direct child of
`build/` named `<change>_<revision>_<role>_<attempt>_<kind>/`. Split the basename
on `_` to recover exactly five components. Each component uses lowercase
kebab-case matching `[a-z0-9]+(?:-[a-z0-9]+)*`; `_` joins components only. For
example, `build/anatomical-human-skeleton_r1_dev_try-1_build/` has the components
`anatomical-human-skeleton`, `r1`, `dev`, `try-1`, `build`. A retry or independent
review gets a new sibling identity, never a nested run directory or reused root.
Tool-required content such as `frames/`, `assets/`, `reference/` and `clean-a/`
may remain inside its owning run. Preparation and construction may share one
build root. Distinct input/output roots must not coincide or contain one another,
including after symlink resolution. Existing protected historical paths may be
read as explicitly labeled legacy inputs; do not relocate them as part of a new run.

After checks finish, including failure or interruption:

1. Inventory only the run roots owned by this work and identify the accepted result,
   its linked-media/timing/provenance/numeric dependency closure, active work and
   explicitly protected history.
2. Check every local reference and required dependency before deletion. Remove
   obsolete whole run roots, including logs/JSON without a concrete continuing need;
   do not follow symlinks outside `build/`, delete active runs, or remove another
   agent's output. Reviewers clean only their own roots and hand exact developer-owned
   cleanup paths to the developer.
3. Recheck retained links/dependencies and record removed paths and bytes, retained
   paths with specific reasons, dependency-check results and pending cleanup in the
   existing review or hand-off record. A failed or interrupted cleanup is pending;
   do not claim completion until it is resolved. Keep JSON/log diagnostics only for
   a named dependency, explicit history, active/resumable work, or unresolved finding,
   and state when their retention should be reconsidered.

Compact hand-off record example:

```markdown
### Cleanup
- Removed: `build/anatomical-human-skeleton_r1_dev_try-0_pack/` — 1234 bytes.
- Retained: `build/anatomical-human-skeleton_r1_dev_try-1_pack/` — accepted pack and referenced media/provenance.
- Retained: `build/anatomical-human-skeleton_r1_dev_try-1_checks/fault.json` — unresolved finding `F-1`; reconsider after fix.
- Dependency check: accepted links resolve; protected history and active runs unchanged.
- Pending cleanup: none.
```

`humanmotionlib.runtime.inspect_blender()` checks the executable version/build before
backend work. Automated runtime tests also check intentional mismatches.
Outputs under `build/` and Python environments/caches are ignored. Do not put
scratch binaries or unreviewed release artifacts in `dist/`.

### HTML-only presentation regeneration

To update diagnostic navigation and paired previews from a previously verified
pack, use the existing review-pack command with `--html-only-from`. The HTML
groups every available preview variant by BPM and pairs Front/Side, including
the shoulder-plane detail GIFs. The input
must contain its retained `reference/input.json`, all 32 diagnostic HTML pages,
linked media, render/timing records, and numeric evidence. The destination must
be a fresh flat run root. The example input is a protected historical R3 pack
and is explicitly a legacy input; it is not a new-run output path:

```sh
uv run --locked --no-sync hml review-pack \
  --html-only-from build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix \
  --output build/anatomical-human-skeleton_r1_dev_html-derivative_pack
```

This mode reads retained page content and metadata, writes HTML plus
`presentation-provenance.json` and `presentation-verification.json`, and copies
every linked or inline PNG/GIF target byte-for-byte into the derivative's local
`assets/` directory. That includes animation previews, static and animation
sheets, front/side onion-skin overlays, and exact sample frames. Repeated links
to the same predecessor-relative file share one local copy. All visual links
then resolve inside the standalone `file://` pack; timing and numeric-evidence
links may continue to reference the predecessor by relative path. This mode
does not invoke Blender or re-encode media, revise predecessor metadata, or
modify the `--reuse-renders` prepared-input hash policy. Provenance records the
original numeric snapshot and verdict hashes, presentation generator, copied
visual-asset hashes, and reused media/evidence hashes. Failures name missing
inventory, broken links, escaped assets, or inconsistent bytes.

## Source validation

`hml validate` loads the profile, mobility, group/map records, every diagnostic
YAML and the fixed scene. Duplicate YAML keys are errors, including nested
keys. It validates closed schemas, finite values, IDs, parents/cycles,
landmark/attachment references, local frames, action references, ownership,
source-register links, humanoid targets, fixture writers and contact targets.
Failures retain the offending identifier and field. The successful JSON status
is `valid-sources`, with source/schema hashes and an explicit scope statement;
it does not claim generated anatomy, solved contacts, timing, renders or
independent review passed. Missing required source files are errors.

The zero-beat rest/neutral fixtures explicitly declare their terminal support
state and anchor/target set through zero-length contact records. Such intervals
have no interior; their final sample uses the terminal state with that declared
anchor set. Ordinary nonzero-duration contact intervals must have positive
length. The neutral fixture bootstraps its own named neutral base without
recursive evaluation; other fixtures reference that base.

## Canonical transform math

`humanmotionlib.math3d` uses right-handed X subject-right, Y anterior, Z superior,
active rotations and unit quaternions in `[w,x,y,z]` order. Local orientation
is `q_rest * q_delta`; world orientation is `q_parent * q_local`. A child's
local translation is rotated by its parent's world orientation before adding
the parent's world position. `local_delta` computes `inverse(q_rest) * q_local`.
Degree-valued actions are converted to radians only for trigonometry.
The neutral shaft basis is the exact projected-anterior/fallback-superior
construction from the dossier, not a backend bone-roll default. Matrices
must be orthonormal with determinant +1 within `1e-6`; quaternion norm error
above `1e-6` is rejected. Quaternion sign does not change orientation.
Mirror position through X=0 and use `J R J` for rotations; no negative scale
is introduced. Triangle winding and fixture-side ownership remain part of
the later geometry/mirroring integration checks.

`humanmotionlib.mirror` swaps side identifiers and body-group ownership, reflects
positions, conjugates rotations, and reverses shell triangle winding so
outward normals follow the reflection. The expanded left-side records are
derived from right-side records through this function; origins and primitive
dimension parameters remain unchanged. Fixture contacts/world targets mirror
with the same explicit times and named clinical values. Tests check proper
rotation determinants, normal direction, side-specific positive action axes,
and mirror involution on both neutral and rest frames.

`humanmotionlib.poses` reads neutral frames from the expanded dossier and reconstructs
the solved rest T-pose through parent FK. Identity rotation deltas reproduce
that T-pose; `to_deltas` and `apply_deltas` round-trip neutral/posed frames with
explicit local translations and `inverse(q_rest) * q_local` orientations.
Unsupported channel fields, non-unit quaternions and non-finite positions
fail. This internal representation is not a completed distribution export.
`scaled_profile` scales meter-valued fields while preserving topology, angles,
bases and normalized ratios; review cameras remain fixed and are not scaled.

## Anatomical action validation

`humanmotionlib.actions` keeps valid, unsupported, out-of-range, and
unsatisfied-constraint states separate. Reports retain joint/action, measured
value, bounds or condition, and beat. Inputs and targets are not clamped or
rewritten. Fixed/coupled channels cannot be written independently. Contact
failure records retain requested targets and joint residuals; the bounded
contact solver itself is a later implementation task.

Independent scalar ranges, sign-specific hip/wrist/spine envelopes,
thoracic/lumbar combined budgets, shoulder plane/twist sectors, and dependent
GH guards are checked separately. Total elevation and GH swing/twist appear
as distinct values. Reference means are never used as fallback operating
limits. The closed formulas in `humanmotionlib.articulation` consume canonical numeric
parameters and require validated action inputs; curve saturation is only the
explicit knee coupling rule, not clamping the commanded knee angle.

Tests measure angles from rotation elements, anatomical landmark trajectories,
and independent scalar identities to within 0.1 degrees. Lower/mid/upper bounds
pass; samples 0.5 degrees outside fail. These checks have no foot pins or floor
constraints. Floating geometry sweeps and measurements from actual Blender
outputs remain separate requirements; action validity alone cannot establish
contact satisfaction or anatomical/natural visual acceptance.

## Kinematics and independent measurements

`humanmotionlib.kinematics` evaluates source action values on rigid anatomical frames;
`humanmotionlib.articulation` supplies the closed coupling formulas. The neutral
solution and the 90-degree lateral-elevation solution reproduce the separately
stored assembly/T-pose frames. Invalid intent produces no accepted pose.
Parent-following transforms preserve unit scale and rigid local geometry.

`humanmotionlib.measurements` reconstructs actions from supplied body matrices and
joint positions. It does not import solver, evaluator, or articulation
routines and does not read a success flag. Independent reference formulas,
the dossier's knot tables, and explicit source intent check the measured
relationships. Each metric records its measured/expected value, tolerance,
beat and requirement. Dimensionless envelope tolerances propagate the approved
0.1-degree measurement tolerance; source commands still use exact envelopes.

`humanmotionlib.coverage` enumerates every action's positive, lower/interior/upper,
outside, or unsupported-writer cases, including both sides. Invalid cases pass
only when rejected without generating a pose. Numeric coverage is separate
from the explicitly pending visual coverage.

Only the 20 named cartilage connections have deformable bindings.
`humanmotionlib.guides` validates and topologically orders rigid-local endpoint,
solved-guide-control, and co-rotating endpoint-midpoint bindings. Cartilages
8–10 attach to the preceding cartilage's evaluated middle control, not its
body frame or the neighboring rib. Missing targets, cycles, duplicate writers,
cross-side links and rigid-body deformation fail validation. The sternum
follows T1; SC, AC and GH centers and limb kinematics retain their approved
values. Rib, sternum, vertebral and limb
geometry stays rigid. Forefoot ball witnesses remain attached to the same toe
frames across the rocker. Tests include frozen scapula/patella/vertebra faults,
a wrist-twist substitute for pronation, and a wrong hindfoot axis, all of which
must fail measurements even when individual scalar limits appear plausible.

These are kinematic animation approximations. Matching numeric curves is not
clinical validation or independent human visual acceptance. The headless
backend must supply actual evaluated frames/geometry for the final reports.

### Focused thoracic preview

Before regenerating full diagnostic packs, prepare just the two structural
poses in a fresh flat build run, then build, measure and render them using the
same entry points. The verifier report and preview pack use separate sibling
runs:

```text
uv run --locked --no-sync hml prepare-skeleton --profile adult-reference-v1 --fixtures neutral rest --output build/anatomical-human-skeleton_r1_dev_thorax-preview_build/input.json
uv run --locked --no-sync hml run-blender --input build/anatomical-human-skeleton_r1_dev_thorax-preview_build/input.json --output build/anatomical-human-skeleton_r1_dev_thorax-preview_build
uv run --locked --no-sync hml verify-skeleton --input build/anatomical-human-skeleton_r1_dev_thorax-preview_build --output build/anatomical-human-skeleton_r1_dev_thorax-preview_checks/metrics.json --thorax-preview
uv run --locked --no-sync hml review-pack --input build/anatomical-human-skeleton_r1_dev_thorax-preview_build --output build/anatomical-human-skeleton_r1_dev_thorax-preview_pack
```

The preview verifies evaluated native geometry but does not assert complete
diagnostic coverage. Its index includes fixed front/side/three-quarter thoracic
inspection views in context and isolation. Inspection cameras are separately
defined in the scene source; full-body diagnostic cameras remain fixed.
`humanmotionlib.thorax_measurements` compares measured tube ring means and sternal
shell midsurfaces with the numerical dossier. Independent Hermite sampling
measures curvature extrema, descent, widening and floating-rib length ratios.
All delivered frames additionally check actual mesh-based SC and costal-guide
closure. Missing native controls fail rather than falling back to prepared
points. `tests/test_thorax.py` retains former uniform rib geometry, bony-tip
costal connections and stale posed midpoints as negative regressions. Full
multi-stature verification, repeat rendering, independent review and human
visual acceptance remain required after this preview.

## Approval and provenance

The human approved implementation by invoking `openspec-apply-change` for
`anatomical-human-skeleton` after completion of its specifications and design.
That approval does not replace independent review or the final human visual gate.
All anatomy uses the frozen numeric dossier. Source provenance resolves through
`docs/used-materials.md`; authored approximations must retain their rationale.

## Current implementation status

Toolchain/license setup, canonical sources, transform math, action validation,
and dependent articulation are implemented and have numeric unit checks.
Backend construction, evaluated-mesh checks, diagnostics, and review-pack
acceptance remain tracked separately in the OpenSpec task list.
The expanded profile preserves its primitives and uses the human-approved
0.158 H × 0.050 H foot envelope; both envelope checks pass. The
walking-trajectory design correction and its passing preflight
are recorded in `docs/anatomical-human-skeleton-preflight.md`. The corrected
trajectory passes the current preflight, while the original penetrating
construction remains a negative regression. Full evaluated-mesh floor checks
and review are still required; passing the preflight does not mark them done.

## Prepared interchange and transform verifier

`prepare_skeleton.py` validates every source before producing
`skeleton-prepared/v1` JSON. It embeds the scaled source bundle, meter-valued
placements, expected action intent, proper body matrices, explicit guide points,
and rest-relative FK deltas. Arrays use sorted stable IDs/topological order;
JSON object keys are sorted, numbers must be finite, and timestamps are exact
numerator/denominator records. `--stature` scales meter fields while retaining
angles, normalized ratios, scene settings and topology.

The payload carries SHA-256 hashes of all canonical sources, schemas, licensing
register and dependency/backend contracts. A separate content digest detects
payload modifications. Consumers reject duplicate keys, changed/missing source
hashes, unknown formats and sample/body inventory gaps. Hashes describe inputs;
they do not establish geometric or visual correctness.

Before backend construction, the explicit transform-only command is useful:

```sh
uv run --locked --no-sync hml verify-skeleton --input build/anatomical-human-skeleton_r1_dev_try-1_build/input.json --output build/anatomical-human-skeleton_r1_dev_transform-check_checks/prepared-metrics.json --transforms-only --action-coverage
```

The verifier reconstructs angles/couplings from supplied matrices and compares
neutral/T-pose frames to the separately stored dossier. It imports no pose solver
in its measurement path and ignores solver success flags. Its report names the
limited scope. The default directory command requires evaluated Blender evidence;
missing backend/mesh/contact checks cannot be represented as full acceptance.

## Headless construction and actual geometry

`build_skeleton.py` starts with factory data and builds `Anatomy`, `Controls`,
`Humanoid`, and `Review` collections. Its 176 active body frames have native
Blender control bones, rigid mesh attachments and separate semantic mapping
nodes; four explicitly omitted structures have no invented geometry. Primitive
IDs remain object names. The standalone `WorldRoot` records declared diagnostic
stage placement independently of anatomical pelvis actions.

Ellipsoids use 24×12 angular resolution, tubes use 16 radial sides and 16
centerline intervals, shells use the canonical triangulation and thickness.
Curved centerlines use interpolating Catmull-Rom with duplicated endpoint
controls. Capsule ends taper into the specified elliptical cross-section.
Skull recesses are named exact Boolean differences. Only the 20 declared
cartilage guides update their endpoint geometry; rigid body vertices do not
stretch to close articulations.

The builder writes `skeleton.blend`, `evaluated.json`, and `build-metadata.json`.
Measurements come from Blender's evaluated dependency graph: body matrices,
attachment/landmark positions, per-mesh bounds/floor minima, topology digests,
rigid local-vertex residuals, object/bone scales and directly observed scene
settings. The verifier checks this evidence against source intent and stored
numeric targets without trusting a solver flag. Clean-build tests exercise
H=1.50/1.70/1.90 m, a repeated isolated 1.70 m build and deliberately altered
scale, attachment, floor, inventory and articulation evidence.

The runtime resolves `blender` from PATH and follows executable symlinks before
launching it. This matters on macOS: an executable invoked through a symlink
can lose its application resources. Automated subprocesses use the resolved
executable; no installation path is stored in repository humanmotionlib. If invoking
the documented `blender` command directly, ensure the PATH launcher preserves
resource discovery. The version/build pin remains mandatory.

## Diagnostic authoring, contacts and timing

`rig/diagnostics/*.yaml` is scoped verification intent. It does not define the
future production Pose/Segment/Motion library. Tracks have explicit group
ownership, integer count keys, finite action values and named easing. Closed
constructors encode the approved squat, corrected flat-foot step and forefoot
rocker. Their amplitudes remain in YAML. The squat derives hip angles and pelvis
position by the frozen 60-step sign-bracketed construction, preserving ankle
frames. Walking reflects its right-side prototype and retains the original
penetrating construction only as a negative regression.

Unowned actions use `base` against neutral, `hold` requires previous intent,
and `free` requires a supplied disjoint parallel writer. Duplicate writers or
unowned keys fail. Noise/follow-through remain disabled. Floating bilateral
sweeps cover every independent joint axis; shoulder-plane sweeps declare a
1-degree elevation context because azimuth is undefined at zero elevation.
The anatomical neutral action value is the sweep's start/end value; the
companion placement is explicitly described in the fixture.

Contact intervals are half-open. Terminal states select their declared anchors
at the endpoint; a zero-length endpoint record can declare terminal-only flat
support, as in the rocker. Flat support checks heel and both ball witnesses;
ball support checks both ball witnesses. Attachments never change bodies.
`humanmotionlib.contacts` independently measures positions/sliding and supplies a
bounded damped least-squares solver (sorted variables, previous/canonical seed,
positive knee branch, damping 1e-4, 100 iterations, 1e-5 H residual target).
Candidate variables are projected to their operating bounds; requested fixed
intent and targets are retained. Coupling-invalid candidates are rejected.
Failure retains original targets, limits and residuals and produces no accepted
solution. Closed diagnostic constructors already satisfy their exact pins and
therefore do not replace the frozen trajectories with a numerical amplitude fit.

`humanmotionlib.sampling` stores exact rational beat/second timestamps at BPM
60/120/180. All modes refer to the same solved sample IDs; BPM never changes
beat-relative geometry. Preparation can select a source fixture subset with
`--fixtures neutral rest` for isolated builds. No image interpolation occurs.
The optional verifier `--dense` streams additional <=0.01-beat samples with
<=0.25-degree driving-action steps, records continuity maxima and retains each
failure. A walking arm's fixed-plane direction selector has canonical zero at
zero elevation; its resulting full matrices are included in continuity checks.
Its undefined zero-elevation azimuth is not a scalar amplitude-step metric.

Skull Boolean recesses are applied once during construction. They are rigid
geometry thereafter; they are not re-solved in world space after each pose.

The build command also accepts internal review flags `--render-dir` and
`--render-only`. These reconstruct the same sources with fixed cameras and
write a render manifest; render-only output never substitutes for evaluated
mesh metrics. Green markers show declared pins and fixed dark lines mark the
floor axes. Annotation thickness is visual only and excluded from anatomy
measurements. Metadata records tool hashes and independent collection visibility.

## Full verification and visual pack

Backend verification shards detailed per-sample records beside `metrics.json`
so the summary remains readable. Every detailed metric retains measured and
expected values, tolerance, units, beat, status and its fixed-view image link.
The summary links those records and reports loop/timing/complete-sole apex
checks. A missing record or failed check cannot become acceptance.

`hml review-pack` invokes two factory-startup render-only builds in isolated
`clean-a`/`clean-b` directories, compares decoded RGBA pixels, then writes the
HTML index, every diagnostic/action-family page, count/animation sheets at all
three BPMs, GIF previews and count onion-skins. `--reuse-renders` only reassembles
already completed passes whose prepared content hash still matches. Logs and
manifests retain failures and actual backend/GPU/tool metadata.

Regional views crop the fixed neutral renders; cameras are never reframed.
Axes use 0.025 H object-space vectors. Label lettering is original repository
bitmap artwork, avoiding imported font assets. GIF terminal duplicate poses
coalesce with the next loop start; endpoint PNGs/count sheets remain explicit.
Centisecond duration rounding uses cumulative error diffusion and is decoded
again to check total error below 10 ms. PNG timestamps are exact rational
records in `sample-timing.json` and the per-diagnostic HTML tables.

See `docs/anatomical-skeleton-acceptance.md` for every delta-spec scenario's
executable evidence and the remaining independent/human visual criteria.

Shoulder-plane pages additionally show a fixed pixel crop of the same full-view
frames. This makes the explicitly small conditional elevation context inspectable
without moving the camera or changing any action amplitude. Full views remain
available beside that detail preview.

`geometry-reference.json` preserves actual Blender-evaluated body-local vertices.
The dense floor audit combines them with the same canonical keyed transforms
whose delivered native frames are independently checked. A transformed local
AABB supplies a conservative lower bound; when that bound crosses the floor,
every evaluated vertex is tested. Thus no vertex can be skipped as an assumed
sole surface. Explicit non-rigid guides are regenerated at each dense sample.
The report distinguishes conservative bounds from exact vertex minima and
retains the worst bound/beat for every mesh plus every failure. This avoids
rebuilding identical rigid meshes at every dense time, while leaving the
floor threshold unchanged. Dense native-frame conformance and dense geometry
proof are separate, stated evidence scopes.

Rigid control bones explicitly disable scale inheritance, keep local scales at
one, and normalize their quaternion channels after float32 matrix decomposition.
This prevents small DCC decomposition errors accumulating along deep chains;
measurement still enforces the original 1e-6 scale/frame tolerances.

The holistic backend verifier requires every declared diagnostic, all three
reference tempos and every planned delivered sample. It independently checks
beat/second fractions against the timing formula. Isolated `--fixtures` builds
are for unit checks and explicit transform-only inspection; they cannot satisfy
the complete change-level diagnostic coverage gate.

For the full delivered and dense geometry report use:

```sh
uv run --locked --no-sync hml verify-skeleton --input build/anatomical-human-skeleton_r1_dev_try-1_build --output build/anatomical-human-skeleton_r1_dev_try-1-dense_checks/metrics.json --action-coverage --dense-floor
```

The native anatomical hierarchy also uses computed world-frame adapter targets
inside `Controls`. They copy the authoritative solved frames to native bones,
preventing accumulated float32 translation cancellation along the vertebral
chain. They add no independent anatomical channels or public humanoid targets.
Geometry still follows its native bone via rigid body attachments. Fault tests
mutate these actual scene targets and still must fail independent measurements.

To include actual cross-stature vertex/topology and native rest-frame comparison:

```sh
uv run --locked --no-sync hml verify-skeleton --input build/anatomical-human-skeleton_r1_dev_try-1_build --output build/anatomical-human-skeleton_r1_dev_try-1-stature_checks/metrics.json --action-coverage --dense-floor --stature-builds build/anatomical-human-skeleton_r1_dev_stature-1-5_build build/anatomical-human-skeleton_r1_dev_try-1_build build/anatomical-human-skeleton_r1_dev_stature-1-9_build
```

Generate the additional stature builds with the same preparation/build commands,
adding `--stature 1.5` or `--stature 1.9` to preparation and using sibling roots
`build/anatomical-human-skeleton_r1_dev_stature-1-5_build/` and
`build/anatomical-human-skeleton_r1_dev_stature-1-9_build/`. Each verifier output
belongs in its own flat checks run. All delivered samples at each stature must
also pass their own backend verifier run.

```sh
uv run --locked --no-sync hml prepare-skeleton --profile adult-reference-v1 --stature 1.5 --output build/anatomical-human-skeleton_r1_dev_stature-1-5_build/input.json
uv run --locked --no-sync hml run-blender --input build/anatomical-human-skeleton_r1_dev_stature-1-5_build/input.json --output build/anatomical-human-skeleton_r1_dev_stature-1-5_build
uv run --locked --no-sync hml prepare-skeleton --profile adult-reference-v1 --stature 1.9 --output build/anatomical-human-skeleton_r1_dev_stature-1-9_build/input.json
uv run --locked --no-sync hml run-blender --input build/anatomical-human-skeleton_r1_dev_stature-1-9_build/input.json --output build/anatomical-human-skeleton_r1_dev_stature-1-9_build
uv run --locked --no-sync hml verify-skeleton --input build/anatomical-human-skeleton_r1_dev_stature-1-5_build --output build/anatomical-human-skeleton_r1_dev_stature-1-5_checks/metrics.json --action-coverage --dense-floor
uv run --locked --no-sync hml verify-skeleton --input build/anatomical-human-skeleton_r1_dev_stature-1-9_build --output build/anatomical-human-skeleton_r1_dev_stature-1-9_checks/metrics.json --action-coverage --dense-floor
```

Approved action-direction refinement (2026-10-21): hip and wrist conventions are separate closed fields. Right hip is `Rx(f)*Ry(b)*Rz(-r)`; forearm rotation is positive about `normalize(proximal_radius-distal_ulna)`; knee dependent z uses distal -Z, hence `Rx(-k)*Rz(-z(k))`. Left sides use axial reflection. Rebuild all prepared inputs and outputs; old source hashes cannot establish acceptance. Absolute bilateral witness checks in the action-coverage report measure lateral toes, thumb-up midrotation with elbow 90, palm-down pronation and medial tibial turn independently of action-angle decoders.

### Squat R3 static plausibility and focused preview

The approved R3 squat keeps knees at 90 degrees at the bottom, with ankle
dorsiflexion 20 degrees, pelvis pitch 25 degrees and lumbar flexion 10 degrees.
The positive ankle operating ceiling is explicitly revised to 20 degrees;
reference cohort observations and the stepping ankle peak of 12 degrees are
unchanged. These are authored exercise/operating choices, not universal ROM.

The profile contains a closed `mass_model` of 16 rigid carrier-local points
representing whole-body regions including unrendered tissues. `humanmotionlib.balance`
checks the frozen weights/points and normalization independently of the pose
constructor. `weight_kg` is the average of the two recorded coefficient columns;
weights normalize by their 16-region sum. They are not mesh-volume/bone weights
or a claim that all scaled bodies have the same physical mass. Points scale
with stature, coefficients/fractions do not. Source and adaptation credits are
in THIRD-PARTY-NOTICES.md and docs/used-materials.md.

Native exports include actual posed-bone `mass_points`. Each delivered sample
checks source-bound placement; squat additionally checks weighted COM against
the measured permanent flat-contact XY hull, reference margin >=0.010H and
minimum reference/male-weight/female-weight margin minus0.005H >=0.005H.
The placement allowance is an authored perturbation bound, not a population
confidence interval. Missing/forged evidence fails. Dense squat samples repeat
the canonical-frame static audit and retain every sampled body frame, mass
point, measured support anchor, check and complete three-variant assessment.
`static_balance.extrema` (or `stature_balance[].extrema`) records each metric's
minimum and maximum with its sample ID and beat. Dense samples link to the
nearest delivered front/side render as contextual references and mark whether
the beat is an exact match; the image paths are relative to the review-pack
root. Actual native delivered frames are verified separately. No dynamic
stability, force, muscle or speed-dependent balance claim is made.

Produce the early squat-only preview through the established commands:

```sh
uv run --locked --no-sync hml prepare-skeleton --profile adult-reference-v1 --fixtures squat --output build/anatomical-human-skeleton_r1_dev_squat-preview_build/input.json
uv run --locked --no-sync hml run-blender --input build/anatomical-human-skeleton_r1_dev_squat-preview_build/input.json --output build/anatomical-human-skeleton_r1_dev_squat-preview_build
uv run --locked --no-sync hml verify-skeleton --input build/anatomical-human-skeleton_r1_dev_squat-preview_build --output build/anatomical-human-skeleton_r1_dev_squat-preview_checks/metrics.json --squat-preview
uv run --locked --no-sync hml review-pack --input build/anatomical-human-skeleton_r1_dev_squat-preview_build --output build/anatomical-human-skeleton_r1_dev_squat-preview_pack
```

The preview is development evidence only. It cannot satisfy full fixture/action,
three-stature, independent or human acceptance. Regenerate the complete set
using the ordinary commands into a new flat full-build run after the preview.
Do not reuse R2 inputs or renders: hashes intentionally changed.

`squat-balance.json` records actual native render-pass mass/support observations,
all normalized fractions, COM coordinates, signed edge margins, variants and
checks. Separate `*-balance.png` contact sheets and `*-balance.gif` animations
supplement the unannotated views. Their fixed source crop is [280,220,760,820]
for every pose/view/stature; cameras and floor never move. The blue support
hull and green estimated COM/projection have a separate plan-view inset and
static-only legend. Derived overlays are also compared pixel-for-pixel across
the two clean native render passes. All GIFs, including the six extra squat
COM previews, use the existing timing verification.

The native fault suite retains the previous eight cases and additionally rejects
the former squat and a posterior upper-body fault on `balance.reference_margin`.
Unit regressions reject missing/equalized/zero masses, forged mass points and
support observations replaced by intended targets. Original squat formulas
remain only a negative regression.

`--stature-builds` now also checks actual normalized native mass-point positions
and source fractions, then runs the complete dense squat balance grid separately
at all three statures (`stature_balance` in the resulting report). This supplements
the reference full-domain `--dense`/`--dense-floor` audits and the 900 delivered
native samples per stature. Its canonical-frame scope remains explicit.

## Installed package migration

The runtime now lives in `src/humanmotionlib/`. Imports use `humanmotionlib.*`; the old `tools` package is no longer installed. For installed use, follow [`docs/usage.md`](../docs/usage.md): invoke `hml <subcommand>` or `python -m humanmotionlib <subcommand>`. Contributor-only test discovery remains explicit through `hml check-environment` and the repository test commands in the usage guide.

| Previous checkout command | Installed command |
|---|---|
| `python tools/validate.py ...` | `hml validate ...` |
| `python tools/prepare_skeleton.py ...` | `hml prepare-skeleton ...` |
| `python tools/run_blender.py ...` | `hml run-blender ...` |
| `python tools/verify_skeleton.py ...` | `hml verify-skeleton ...` |
| `python tools/review_pack.py ...` | `hml review-pack ...` |
| `python tools/check_host.py --check-environment` | `hml check-environment` |
| `tools.<module>` | `humanmotionlib.<module>` |
