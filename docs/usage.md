# HumanMotionLib usage

HumanMotionLib is distributed as versioned `humanmotionlib` Python package
releases. Python imports use the `humanmotionlib.*` namespace. The installed
command is `hml`; `python -m humanmotionlib` exposes the same command dispatcher.
The supported host interpreter is CPython `>=3.14,<3.15`.

## Install a release

Download the wheel for the version you want from the project's GitHub Release,
then install that file with a supported CPython:

```sh
python -m pip install ./humanmotionlib-X.Y.Z-py3-none-any.whl
```

Check the installed version with `hml --version`. During `0.x` development,
PATCH releases (`0.MINOR.PATCH`) contain fixes and small compatible changes;
MINOR releases (`0.MINOR.0`) contain new capabilities or incompatible changes.
Published releases are immutable; install the desired wheel rather than
expecting an existing version to change.

## Install and inspect

Install the wheel into a fresh environment with a supported CPython. The wheel
declares its runtime dependencies, so neither the source checkout nor its
`uv.lock` is needed at runtime. Check the installed command and environment:

```sh
hml --version
hml --help
hml check-environment
python -m humanmotionlib --version
```

The distribution does not install Blender. Supported construction and rendering
require Blender `5.2.2 LTS`, build `d13f752e3b9c`, on the documented reference
platform. HML checks the selected executable and reports a controlled error if
it is missing or has a different build. HML does not download Blender.

## Public Python generation API

`humanmotionlib.api` is the supported synchronous interface for the packaged
skeleton diagnostics and the bounded consumer-motion input described below.
Preparation validates sources and returns poses plus exact per-BPM timelines
without probing Blender. Rendering uses the pinned external Blender backend.
Consumer inputs use the existing `skeleton-diagnostic/v1` action language;
they do not add a general pose, segment, or motion-composition language.

```python
from pathlib import Path

from humanmotionlib.api import GenerationError, prepare, render

workspace = Path("/absolute/caller/workspace")
try:
    prepared = prepare(
        workspace=workspace,
        output="build/library-use_r1_app_try-1_prepare/input.json",
        fixtures=("neutral", "arm-raise"),
        bpms=(90,),
    )
    result = render(
        prepared, workspace=workspace,
        output="build/library-use_r1_app_try-1_render",
    )
except GenerationError as error:
    print(error.code, error.run_root, error.receipt_path)
    raise

front = {image.sample_id: image.path for image in result.images
         if image.view == "front"}
timeline = next(item for item in prepared.timelines
                if item.fixture_id == "arm-raise" and item.mode == "animation")
frames = [(entry.seconds, front[entry.sample_id]) for entry in timeline.entries]
portable_result = result.to_dict()  # standard json.dumps-compatible
```

Every writing call needs an explicit absolute workspace and a fresh flat run
root under `workspace/build/`. Relative operands resolve from that workspace.
The result exposes pose/control/contact data, image paths, source hashes,
provenance, the used-materials register and applicable license/notice text.
`prepared_sha256` is the sealed prepared-content identity checked by
`read_prepared`, not a hash of the JSON file's formatting bytes. Exact times
serialize as numerator/denominator pairs. `render` accepts either
the returned preparation result or its prepared JSON path; it re-reads and
verifies persisted bytes in host Python before probing or launching Blender.
For consumer inputs this includes schema and provenance validation, packaged
base re-resolution, dense preflight replay, and reconstruction of the solved
source and sample joins. The launcher binds that accepted content hash to its
private Blender invocation. Blender checks the prepared seal, active package
and resource hashes, consumer snapshot hashes, base-lineage hash references,
sample/timeline joins, and the exact host-validated identity using its
standard library and HML; it does not import host YAML or JSON Schema modules
or claim an independent source-validation verdict. Catch `GenerationError` to inspect
its stable `code`, `operation`, `run_root`, `receipt_path` and JSON-compatible
`details`. Stable codes are `invalid-request`, `source-validation`,
`input-integrity`, `io-error`, `backend-unavailable`, `backend-mismatch`,
`backend-contention`, `backend-timeout`, `backend-spawn`, `backend-failed`,
`output-integrity` and `cleanup-pending`. Numerical acceptance remains
`not-run` and visual acceptance remains `pending` until their separate checks.

### Select a character at render time

The public character IDs are `skeleton`, `male` and `female`. The skeleton is
the default and a complete public character on its own. Male and female use the
same prepared movement, profile and rig as the skeleton; this release changes
surface appearance only. Character selection does not change mass, mobility or
range of motion. See [the character source and compatibility guide](character-models.md)
for the authored mannequin limits and binding rules.

Prepare once, then pass the same result to one or more render calls. The full
batch is normalized to registry order (`skeleton`, `male`, `female`), regardless
of the order supplied by the caller:

```python
prepared = prepare(
    workspace=workspace,
    output="build/library-use_r1_app_try-1_prepare/input.json",
    fixtures=("neutral", "arm-raise"),
    bpms=(90,),
)
result = render(
    prepared,
    workspace=workspace,
    output="build/library-use_r1_app_try-1_render",
    characters=("skeleton", "male", "female"),
)

portable = result.to_dict()
images = {(image.character_id, image.sample_id, image.view): image.path
          for image in result.images}
character_ids = [character.character_id for character in result.characters]
character_attribution = result.character_provenance
assert character_ids == ["skeleton", "male", "female"]
```

For a single surface, pass `characters=("male",)` or `characters=("female",)`.
For example, reuse the preparation above with a fresh output root:

```python
single = render(
    prepared,
    workspace=workspace,
    output="build/library-use_r1_app_try-2_single-render",
    characters=("female",),
)
female_images = {(image.character_id, image.sample_id, image.view): image.path
                 for image in single.images}
female_attribution = single.character_provenance
assert set(female_attribution) == {"female"}
```

Each writing call uses its own fresh run root. Batch results keep the existing
pose and timeline identities; use `RenderedImage.character_id` together with
`sample_id` and `view` to join images to the shared timeline. The result also
reports per-character artifact paths, provenance and a sealed `render_identity`.
`character_provenance` provides the source-attribution union for the selected
character set.

Character rendering adds `RenderedImage.character_id`, per-character artifact
records, `character_provenance` and a sealed `render_identity` to the existing
result projection. The host persists a `character-render-request/v1`; a render
with surfaces also writes a registry-ordered
`character-render-manifest/v1`. Receipts bind the request and complete union of
character outputs. These are additive character fields; the prepared pose and
timeline contract stays shared. Canonical resource edits invalidate the normal
package identity, so prepare again with the installed HML version before
rendering. The feature adds no runtime dependency or generated character mesh
download.

The command line offers the same selection on `run-blender`:

```sh
hml --workspace /path/to/workspace run-blender \
  --input build/library-use_r1_app_try-1_prepare/input.json \
  --output build/library-use_r1_app_try-1_render \
  --characters skeleton male female
```

### Numeric-only character verification

For a full no-images build, `verify-skeleton --character-output RUN
--numeric-only` verifies the native surface artifacts and dense host reference
without requiring a render manifest or PNGs. It still checks the complete
registry, sealed request, package/source identities, supervised `build` receipt
and exact numeric artifact hash inventory. The command reports rendering as
`not-run` and visual judgment as `not-assessed`; this scoped numeric success is
not a render or visual acceptance result. Without `--numeric-only`, character
verification continues to require the complete render manifest and image set.

To compare the supported statures, give one evaluated build for each height via
`--stature-builds`; `--input` must identify the same primary run as
`--character-output`:

```sh
hml --workspace /path/to/workspace verify-skeleton \
  --input build/add-shared-body-characters_r1_dev_try-1_h170-build \
  --output build/add-shared-body-characters_r1_dev_try-1_numeric-check/report.json \
  --character-output build/add-shared-body-characters_r1_dev_try-1_h170-build \
  --numeric-only \
  --stature-builds \
    build/add-shared-body-characters_r1_dev_try-1_h150-build \
    build/add-shared-body-characters_r1_dev_try-1_h170-build \
    build/add-shared-body-characters_r1_dev_try-1_h190-build
```

The aggregate passes only when all three heights have complete numeric
evidence, their candidate package/source/scene/diagnostic/sampling identities
agree, and evaluated cross-stature comparisons pass. Render repeatability,
pixel parity, and the human visual gate remain separate.

### Character review pack

`review-pack` can create a standalone comparison pack for any ordered subset of
`skeleton`, `male`, and `female`. The complete acceptance presentation uses all
three. It creates its clean repeatability pair and the required default,
explicit-skeleton, and single-character regression passes through the same
supervised render API. The complete pack also compares an immutable historical
skeleton baseline and actual renders at H=1.50m and H=1.90m against the H=1.70m
primary input. Supply the additional evidence with repeatable
`--stature-input H=RUN` and `--skeleton-baseline RUN` options:

```sh
hml --workspace /path/to/workspace review-pack \
  --input build/add-shared-body-characters_r1_app_try-1_candidate \
  --characters skeleton male female \
  --stature-input 1.50=build/add-shared-body-characters_r1_app_try-2_short \
  --stature-input 1.90=build/add-shared-body-characters_r1_app_try-3_tall \
  --skeleton-baseline build/add-shared-body-characters_r0_baseline_try-1_render \
  --output build/add-shared-body-characters_r1_app_try-1_pack
```

The supplementary inputs must be evaluated candidate runs with matching
profile, mobility and scene identities, and with neutral and squat beat 2
available. The primary input must be H=1.70m. Labels are checked against the
prepared stature; inputs and outputs must be disjoint. No image is resized to
fill a missing stature. A preview may omit the baseline or supplementary
heights, but its report names each missing item and returns `incomplete`; it
does not claim the complete acceptance pack. Omit these options for an ordinary
skeleton-only pack, which retains its existing behavior.

The character pack links front/side motion sheets, neutral/rest front/side/rear
silhouettes, shared-joint overlays, sole/contact crops, GIFs and onion skins.
It copies the required historical baseline images into `reference/baseline/`
for a standalone report and records source hashes. Managed render passes live
under the fresh output root in `clean-a/`, `clean-b/`, regression pass
directories and any supplied stature pass directories. JSON reports record
exact sample keys, pixel comparisons, source identities, missing evidence and
coverage. A numerical `pass` does not record visual acceptance.

Selection must be a nonempty sequence of distinct registered IDs. A bare
string, duplicate, unknown or incompatible ID fails during host preflight,
before output allocation or Blender probing. Character sources and their
versioned schemas are included in the installed package integrity manifest;
editing canonical sources requires regenerating preparations under the normal
package identity rules.

## Commands

The global `--workspace PATH` is required for every command that writes files
or launches the backend. It must be an absolute path and appear before the
command name. Relative input and output arguments are resolved from that
workspace, regardless of the invocation working directory. Read-only commands
such as `help`, `version`, `validate`, and `check-environment` need no workspace.
HML writes managed run state under the selected workspace's `build/` directory
and does not write into its installed package files.

```sh
# Validate canonical data and inspect an installation.
hml validate --profile adult-reference-v1
hml check-environment

# Prepare all diagnostic fixtures, or select a subset explicitly.
hml --workspace /path/to/workspace prepare-skeleton \
  --profile adult-reference-v1 --output build/<run>/input.json
hml --workspace /path/to/workspace prepare-skeleton \
  --profile adult-reference-v1 --fixtures neutral rest \
  --output build/<run>/input.json

# Supervised Blender construction, numeric verification and review presentation.
hml --workspace /path/to/workspace run-blender \
  --input build/<run>/input.json \
  --output build/<run>
hml --workspace /path/to/workspace verify-skeleton \
  --input build/<run> \
  --output build/<check-run>/metrics.json
hml --workspace /path/to/workspace review-pack \
  --input build/<run> \
  --output build/<pack-run>

# Regenerate HTML presentation from a retained, verified predecessor pack.
hml --workspace /path/to/workspace review-pack \
  --html-only-from /path/to/verified/predecessor-pack \
  --output build/<pack-run>
```

The Python API exposes the same workspace contract. `verify_transforms` is a
pure in-memory check. The full collection writer requires the explicit
workspace and keeps the `metrics.json` summary and `metrics-samples/` shard
directory in the supplied fresh run. `prepared` and `evaluated` below are
objects loaded and validated by the caller from explicit input paths:

```python
from pathlib import Path
from humanmotionlib.prepared import write_json
from humanmotionlib.runtime import validate_run_content_path
from humanmotionlib.verify_skeleton import verify_transforms
from humanmotionlib.verification_run import verify_collection

workspace = Path("/absolute/caller/workspace")
run = workspace / "build/portable-installed-runtime_r1_app_try-1_verify"
# Allocate `run` as a fresh direct child of workspace/build before calling.
summary = verify_collection(
    prepared,
    evaluated,
    run / "metrics.json",
    verify_transforms,
    workspace=workspace,
)
report, _ = validate_run_content_path(run / "metrics.json", workspace)
write_json(report, summary)
```

`verify_collection` validates the report destination, writes the per-sample
shards beside it and returns the summary; the caller persists that summary to
the validated destination. The records retain measured/expected values,
bounds, units, status and image links; existing verifier tolerances and
failure thresholds are unchanged. Use `verify_transforms(prepared)` when only
prepared transforms are available; this does not establish backend acceptance.

Each `<run>` placeholder must be replaced with a fresh direct child of
`build/`, named `<change>_<revision>_<role>_<attempt>_<kind>`. Its five
components use lowercase kebab-case and are joined by underscores. Independent
input and output roots must be disjoint, including after resolving symlinks.
Retries use a new attempt name. Existing accepted/protected packs may be read as
inputs and remain in place.

The commands retain the operation options for stature, fixture selection,
timeouts and slot timeouts, render-only construction, verification audits,
render reuse, and HTML-only presentation. Run `hml <command> --help` for the
options supported by the installed release. Invalid sources, options,
incomplete resources, backend mismatches and failed checks return a nonzero
status. The raw Blender script is an internal entry point; normal construction
uses `hml --workspace /absolute/path run-blender` or
`hml --workspace /absolute/path review-pack` so the supervisor can check
backend identity, enforce deadlines and record receipts.

## Source contributors

For repository development, start from the checkout with `make`. GNU Make and
a POSIX shell are required to read help; uv is additionally required for
package and development workflows. The Make workflow obtains CPython 3.14,
installs the locked build dependencies, rebuilds the current package and
records the project tools/cache under the configured `build/` tools root.
Blender is needed only by rendering workflows. No shell activation or manual
Python/cache/run paths are needed for the normal routes.
Host workflows are supported on macOS arm64 and Ubuntu 24.04 x64; native
Windows is unsupported and WSL is unverified. Rendering currently requires
macOS arm64 Blender 5.2.2 LTS build `d13f752e3b9c`.

```sh
make
make dev
make package
make matrix-list
make matrix-build CHARACTER=male HEIGHT=1.70
make matrix-check CHARACTER=male HEIGHT=1.70
```

`make dev` validates the current package and canonical library sources, then
prints next actions. `make package` builds both archives, compares the wheel
rebuilt from the source archive, and checks the exact wheel in an independent
environment without Blender or publication. Matrix list/help need no Python,
uv or Blender. Matrix build renders only its selected pair; matrix check checks
existing compatible results and does not rebuild them. The direct `hml` and
`uv` commands remain available for advanced or separately managed workflows;
their options are documented by each command's help.

If a selected matrix result root or `build.json` is missing, `make matrix-check`
prints the exact selected `make matrix-build CHARACTER=... HEIGHT=...` command
and returns without creating result files, logs or reports. A check against an
existing result starts an attempt and retains its log and current report even
when validation fails.

`make mostlyclean`, `make clean` and `make distclean` remove the exact fixed
areas listed in [the matrix/build guide](build-matrix.md). Every object inside
a selected area is disposable, including unknown files, matrix logs and local
R6/history. Cleanup needs Make, a POSIX shell, `ps`, `lsof` and the basic
filesystem tools named by `make help`, not Python/uv/Blender. It checks active
work and containment and never follows links to their targets.

### Consumer-authored movement

`prepare` accepts one optional `motion` argument as a mapping or a local
`.yaml`, `.yml`, or `.json` path. A complete document uses the existing
`skeleton-diagnostic/v1` schema. A `skeleton-motion-variant/v1` document
changes selected key values on one packaged base through explicit
`track_scales` or replaces complete tracks through `track_overrides`.
Supplying `motion` together with `fixtures` is an invalid request. Relative
source paths resolve against the explicit workspace. Preparation copies the
source, validates it and persists a sealed snapshot; rendering uses that
snapshot after the original file is removed. JSON Schema and its references
are loaded from the package, never from a consumer URL.

Example below scales the packaged squat's bilateral knees and the four
explicitly coupled ankle/pelvis/lumbar tracks. The caller must supply a value;
30° and 60° are test inputs showing how consumer-selected values travel
through preparation. The example's `0 < knee_peak_deg <= 90` range is only a
domain chosen for this helper. It is not an HML exercise recommendation, and
the API itself does not prescribe a squat depth. Passing source validation
does not imply clinical, evaluated-mesh, or human visual acceptance.

```python
from pathlib import Path
from humanmotionlib.api import prepare, render

workspace = Path("/absolute/caller/workspace")

def shallow_squat_source(knee_peak_deg: float) -> dict:
    if isinstance(knee_peak_deg, bool) or not (0 < knee_peak_deg <= 90):
        raise ValueError("This example accepts an explicit value in (0, 90].")
    factor = knee_peak_deg / 90
    return {
        "format": "hml-consumer-motion/v1",
        "materials": [],  # authored scaling contribution adds no source
        "motion": {
            "schema_version": 1,
            "kind": "skeleton-motion-variant",
            "format": "skeleton-motion-variant/v1",
            "id": "consumer-selected-squat-depth",
            "description": "Consumer-authored scaled variant of the packaged squat.",
            "profile": "adult-reference-v1",
            "license": "CC-BY-4.0",
            "provenance": {
                "kind": "authored",
                "license": "CC-BY-4.0",
                "sources": [],
                "rationale": "Consumer-authored track scaling for API verification.",
                "changes": "Scales bilateral knee, ankle, pelvis and lumbar tracks.",
            },
            "base_fixture": "squat",
            "track_scales": {
                "knee.L.flexion": factor,
                "knee.R.flexion": factor,
                "ankle.L.dorsiflexion": factor,
                "ankle.R.dorsiflexion": factor,
                "pelvis.pitch": factor,
                "lumbar.flexion": factor,
            },
            "track_overrides": [],
        },
    }

for attempt, knee_peak_deg in enumerate((30, 60), start=1):
    prepared = prepare(
        workspace=workspace,
        output=f"build/consumer-motion_r1_app_try-{attempt}_prepare/input.json",
        motion=shallow_squat_source(knee_peak_deg),
        bpms=(90,),
    )
    result = render(
        prepared,
        workspace=workspace,
        output=f"build/consumer-motion_r1_app_try-{attempt}_render",
    )
    beat_two = next(
        pose for pose in prepared.poses
        if pose.fixture_id == "consumer-selected-squat-depth" and pose.beat == 2
    )
    print(knee_peak_deg, beat_two.actions, len(result.images))
```

The run names above are examples; choose fresh valid five-part run identities
for actual work. Keep the prepare and render roots disjoint.

A complete source document can also be supplied directly. This authored
`action_sweep` example uses one arm track and the neutral packaged base:

```python
complete_source = {
    "format": "hml-consumer-motion/v1",
    "materials": [],
    "motion": {
        "schema_version": 1,
        "kind": "skeleton-diagnostic",
        "format": "skeleton-diagnostic/v1",
        "id": "consumer-arm-sweep",
        "description": "Authored two-beat arm elevation used to demonstrate consumer input.",
        "license": "CC-BY-4.0",
        "provenance": {
            "kind": "authored",
            "license": "CC-BY-4.0",
            "sources": [],
            "rationale": "Original technical API example.",
            "changes": "No external movement source was adapted.",
        },
        "profile": "adult-reference-v1",
        "duration_beats": 2,
        "controls": ["arm_L"],
        "rest_policy": {"policy": "base", "base_fixture": "neutral"},
        "tracks": [{
            "channel": "shoulder.L.elevation",
            "easing": "linear",
            "keys": [
                {"beat": 0, "value": 0},
                {"beat": 1, "value": 10},
                {"beat": 2, "value": 0},
            ],
        }],
        "construction": {
            "type": "action_sweep",
            "side": "L",
            "start_beat": 0,
            "end_beat": 2,
            "reference_knots": [],
        },
        "world_root": {
            "mode": "identity",
            "translation_m": [0, 0, 0],
            "orientation": [1, 0, 0, 0],
            "clearance_h": 0,
        },
        "contacts": [],
        "terminal_contacts": [
            {"foot": "L", "state": "none"},
            {"foot": "R", "state": "none"},
        ],
        "procedural": {"noise": False, "follow_through": False},
    },
}

prepared = prepare(
    workspace=workspace,
    output="build/consumer-motion_r1_app_try-3_prepare/input.json",
    motion=complete_source,
    bpms=(90,),
)
```

Consumer sources still pass the profile's action ownership, constructor,
contact, and mobility checks. Clearance records support the closed license
set documented in [`schema/README.md`](../schema/README.md). Preparation checks
consumer declarations offline and preserves their obligations with inherited
packaged attribution; it cannot verify the truth of a consumer's permission
claim. A provenance source's `material` value refers to the clearance record's
`id`; its `material` field is the human readable description. Consumer
preparations accept integer durations through 256 beats and up to 100000
distinct delivered pose samples. These are input resource bounds.

## Migration

The package and import namespace is `humanmotionlib`; the command name is
`hml`. Replace former script invocations and imports as follows:

| Former use | Installed use |
|---|---|
| `python tools/validate.py ...` | `hml validate ...` |
| `python tools/prepare_skeleton.py ...` | `hml prepare-skeleton ...` |
| `python tools/run_blender.py ...` | `hml run-blender ...` |
| `python tools/verify_skeleton.py ...` | `hml verify-skeleton ...` |
| `python tools/review_pack.py ...` | `hml review-pack ...` |
| `python tools/check_host.py --check-environment` | `hml check-environment` |
| `tools.<module>` | `humanmotionlib.<module>` |

Version `0.2.0` marks the change to the installable distribution and import
namespace. The package does not provide a `tools` import compatibility alias.
