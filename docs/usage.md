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

For development, use the repository's pinned CPython selector and locked uv
environment. `uv sync --locked --no-editable` builds and installs the project
wheel with its contributor/build dependencies. Use `uv run --locked --no-sync`
afterward so uv does not request an editable install. Source and installed
writing commands both require an absolute workspace; for checkout work, pass
`"$PWD"`. Keep every new run in a fresh direct child of that workspace's
`build/`.

```sh
uv lock --check
uv sync --locked --no-editable
uv run --locked --no-sync hml check-environment
uv run --locked --no-sync hml validate --profile adult-reference-v1
HUMANMOTIONLIB_SOURCE_ROOT="$PWD" uv run --locked --no-sync python -m humanmotionlib.check_host --test-root "$PWD/tests"
```

Test discovery is a contributor-only operation with the repository's explicit
`tests/` root. Set `HUMANMOTIONLIB_SOURCE_ROOT` to the checkout when running
source-oriented contributor tests; installed commands do not infer a checkout.
The installed package does not include tests or discover tests from the caller's current directory. Installed `check-environment` inspects the active
interpreter, distribution dependencies and packaged resources without requiring
repository metadata.

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
