# Skeleton tooling

## Repository build workflows

After cloning, install GNU Make 3.81+ and a POSIX shell, then run `make` for concise help.
`make dev` prepares the project tools and current library, validates canonical
sources, and prints next actions. `make package` independently checks its exact
wheel and source archive without Blender. `make matrix-build
CHARACTER=male HEIGHT=1.70` prepares current sources and renders one selected
preview; `make matrix-check CHARACTER=male HEIGHT=1.70` checks existing output
without rebuilding it. Help and matrix-list work without Python, uv or Blender.

The workflow reads the tools location from `[tool.humanmotionlib.workflow]` in
`pyproject.toml`. Its environment, uv cache and uv-managed Python live below
that project-owned path. First use requires uv and may download the locked
CPython/dependencies. Rendering additionally requires the pinned Blender
version described below. Host workflows are supported on macOS arm64 and
Ubuntu 24.04 x64; native Windows is unsupported and WSL is unverified.
Rendering currently requires macOS arm64. The optional `WORKSPACE` Make variable selects a
different absolute checkout path.

Examples later in this file that invoke the installed CLI use the default
configured executable `build/project-tools_r1_contributor_current_environment/environment/bin/hml`.
If `tools-root` is changed in `pyproject.toml`, use the corresponding path under
that configured root. They do not rely on shell variables exported only inside
the Make process.

`make mostlyclean`, `make clean` and `make distclean` use fixed areas described
in [the cleanup guide](../docs/build-matrix.md). Every selected object is
removed, including unknown files, matrix logs and local R6/history. Cleanup
checks process activity and path containment, unlinks selected links without
traversing them, and needs `ps`, `lsof`, `find`, `wc`, `awk`, `grep`, `basename`
and `rm`. It does not invoke Python, uv or Blender.

The lower-level commands below remain useful for dedicated host checks,
acceptance runs and release work. They are not required for the ordinary
clone-to-development or clone-to-package paths.

## Contributor matrix runner

Use [the build matrix guide](../docs/build-matrix.md) for the fixed
character/height table and `matrix-list`, `matrix-build` and `matrix-check`
commands. The runner wraps the installed public generation API and existing
presentation assembler. The ordinary Make build route prepares current sources
before a selected build; direct runner use assumes an already prepared
compatible environment. Each selected result uses one stable root; every
repeated build repeats preparation, rendering and presentation, while check
validates current output without generating it.

## Versioned GitHub releases

Each newly archived OpenSpec change on `main` triggers the serialized release
workflow. Closely spaced accepted changes may share a release. The contributor
helper treats an archived change directory with `.openspec.yaml` as the
acceptance marker, compares canonical `openspec/specs/**/spec.md` file bytes to
the last published release boundary, and selects the next `0.x` version:

- Any canonical specification path or byte change increments MINOR and resets
  PATCH, including editorial corrections.
- With no canonical specification change, PATCH increments.
- Invalid, non-`0.x`, conflicting, or missing release history fails closed.

`tools/release-config.toml` pins the pre-automation bootstrap commit at version
`0.2.0`; historical archives at or before that commit are not published. The
workflow reserves a version-only commit on `main`, runs the locked host and
package checks against that exact commit, and publishes its checked wheel and
`SHA256SUMS` to an immutable `vX.Y.Z` GitHub Release. It records covered change
and acceptance commits in release notes. It never publishes to PyPI.

Inspect a proposed selection without writing a commit or calling GitHub:

```sh
build/project-tools_r1_contributor_current_environment/environment/bin/python3.14 tools/release.py plan \
  --boundary <published-release-commit> --target main
```

The GitHub workflow owns version reservation and publication. To recover a
failed run, rerun the failed workflow or start `Versioned release` with
`workflow_dispatch`; it reconciles the reserved commit, tag, draft and checksums
before selecting another version. It requires Actions write access to `main`
for the version-only commit and `contents: write` for the tag and release.
Branch rules must permit the workflow identity to make those commits; the
workflow does not bypass branch protection or use a permanent token.

HML's host Python is managed by uv;
`.python-version` selects CPython 3.14 and `pyproject.toml` constrains it to
`>=3.14,<3.15`. The ordinary Make workflow creates/reuses its configured
environment with uv and installs locked build dependencies before building a
fresh wheel. Independent acceptance environments use `uv venv`, locked
dependencies and the exact wheel under review; do not copy another
environment's files.
Blender supplies its own embedded Python; it is
selected and verified through the pinned Blender executable and is not required
to match the HML host Python version.
Blender must be available as `blender` on PATH. The backend contract lives in
`pyproject.toml`: Blender 5.2.2 LTS, build `d13f752e3b9c`, reference platform
Darwin arm64. A different Blender version or build is an error. MPFB and Rigify
are not used. No tool requires a workstation-specific executable path or GUI state.

Commands that write files or invoke Blender require an explicit absolute
workspace before the subcommand, for example
`build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" prepare-skeleton ...`.
Relative path operands are resolved from that workspace, not the process cwd.
Read-only `help`, `version`, `validate`, and `check-environment` need no
workspace. All managed output, receipts, locks and backend scratch stay under
the selected workspace's `build/` tree.

## Command contract

For a fresh local host check, create an empty run root directly under `build/`
with a five-part run identity, then keep its environment and uv cache inside it.
The example below is a single developer host-check attempt:

```sh
mkdir build/upgrade-host-python-314_r1_dev_try-1_host
HOST_RUN=build/upgrade-host-python-314_r1_dev_try-1_host
HOST_PYTHON="$PWD/$HOST_RUN/environment/bin/python"
export UV_CACHE_DIR="$PWD/$HOST_RUN/cache"
uv lock --check
uv venv --python 3.14 "$HOST_RUN/environment"
uv export --locked --no-dev --no-emit-project --no-hashes \
  --output-file "$HOST_RUN/requirements.txt"
uv pip install --python "$HOST_PYTHON" --requirement "$HOST_RUN/requirements.txt"
uv pip install --python "$HOST_PYTHON" --no-deps .
"$HOST_PYTHON" -c 'import sys; print("executable:", sys.executable); print("prefix:", sys.prefix); assert sys.prefix == sys.exec_prefix'
"$HOST_PYTHON" -c 'import importlib.metadata as m, importlib.util as u, pathlib, site; names=("humanmotionlib", "yaml", "PIL", "jsonschema", "referencing"); print("distribution:", m.version("humanmotionlib")); print("module origins:", {n: u.find_spec(n).origin for n in names}); print("site:", site.getsitepackages()); print("pth files:", {str(p): p.read_text() for d in site.getsitepackages() for p in pathlib.Path(d).glob("*.pth")})'
"$HOST_PYTHON" -c 'import os; print("uv cache:", os.path.realpath(os.environ["UV_CACHE_DIR"]))'
"$HOST_RUN/environment/bin/hml" check-environment
uv pip check --python "$HOST_PYTHON"
"$HOST_RUN/environment/bin/hml" validate --profile adult-reference-v1
HUMANMOTIONLIB_TEST_RUN_ROOT="$PWD/$HOST_RUN" \
HUMANMOTIONLIB_SOURCE_ROOT="$PWD" \
  "$HOST_PYTHON" -m humanmotionlib.check_host --test-root "$PWD/tests" \
  --json-report "$PWD/$HOST_RUN/host-checks.json"
```

The installed `hml check-environment` command checks the interpreter, dependency
metadata and packaged resources. The explicit `humanmotionlib.check_host`
contributor command reports the selected test total, skips and the only two
modules excluded because they require real Blender: `tests.test_blender_backend`
and `tests.test_pipeline_faults`. It fails on an interpreter/metadata mismatch,
dependency import error, discovery error, empty selection or failed test. This
host-suite command applies only the two explicit Blender-module exclusions
listed above. Real-backend acceptance runs separately with the pinned Blender
on the Darwin arm64 reference platform. The CI uv version is pinned in
`.github/workflows/host-python.yml`; local uv should use that same version for
reproducible lock operations. The workflow pins uv 0.13.5 and uses `make dev`
to prepare and install the current package before running host checks against
that project-owned environment. The package workflow separately verifies a
distribution wheel in a fresh independent installation.

When passed `--json-report`, the host command atomically writes
`matrix-test-outcome/v1`: selected/discovered, passed, failed, error, skipped
and excluded counts, per-case outcomes and tracebacks, process exit status, and
the interpreter/package import identity. Discovery/import failures and an empty
selection are recorded as non-success. Installed acceptance remains a
separate package/host workflow with its own explicitly allocated run root;
the contributor matrix does not invoke it. Its structured outcome is
`installed-acceptance/installed-acceptance.json`, and fixtures and negative
control outputs live under `installed-generated/<kind>/`. The package CI
invocation in `.github/workflows/package.yml` shows its isolated installed
environment setup.
For an explicitly selected candidate runtime physically located under the
checkout's `build/`, the host checker accepts its package import only when all
five declarations are supplied together: `--expected-python`,
`--expected-prefix`, `--expected-purelib`, `--expected-package-origin`, and
`--candidate-manifest`. It compares each declaration with the live interpreter
and verifies the successful candidate manifest, selected role, wheel bytes and
installed `direct_url.json` binding, package version, and runtime-manifest
hash. This exception applies only to that exact candidate environment; imports
from checkout source or another build environment still fail. External
installed-environment checks omit these declarations and retain the
outside-checkout import requirement.
Before process-supervision checks, confirm the printed cache path is inside the
run root. Run `ps -axo pid,ppid,pgid,state,command >/dev/null` with the same
privileges as the check to confirm process-table visibility; success alone does
not prove an owned process group is empty. Run the test's process-visibility
preflight as that same user. If the OS denies inspection, record the limitation
and obtain the required access before proceeding; do not bypass ownership or
liveness guards. The module-origin probe should resolve the package and each
locked dependency from this environment's `site-packages`. Review the contents
of every listed `.pth` file and investigate unexpected external import paths
before running acceptance checks.

The consumer-motion source and public API fault matrix is run from the locked
candidate environment. Allocate the run before executing; these test modules
write process/fault cases only beneath this owned root:

```sh
mkdir build/support-consumer-authored-motions_r1_dev_try-1_host-check
HOST_RUN=build/support-consumer-authored-motions_r1_dev_try-1_host-check
HOST_PYTHON="$PWD/$HOST_RUN/environment/bin/python"
export UV_CACHE_DIR="$PWD/$HOST_RUN/cache"
uv venv --python 3.14 "$HOST_RUN/environment"
uv export --locked --no-dev --no-emit-project --no-hashes \
  --output-file "$HOST_RUN/requirements.txt"
uv pip install --python "$HOST_PYTHON" --requirement "$HOST_RUN/requirements.txt"
uv pip install --python "$HOST_PYTHON" --no-deps .
"$HOST_PYTHON" -c 'import sys; print("executable:", sys.executable); print("prefix:", sys.prefix); assert sys.prefix == sys.exec_prefix'
"$HOST_PYTHON" -c 'import importlib.metadata as m, importlib.util as u, pathlib, site; names=("humanmotionlib", "yaml", "PIL", "jsonschema", "referencing"); print("distribution:", m.version("humanmotionlib")); print("module origins:", {n: u.find_spec(n).origin for n in names}); print("site:", site.getsitepackages()); print("pth files:", {str(p): p.read_text() for d in site.getsitepackages() for p in pathlib.Path(d).glob("*.pth")})'
"$HOST_PYTHON" -c 'import os; print("uv cache:", os.path.realpath(os.environ["UV_CACHE_DIR"]))'
uv pip check --python "$HOST_PYTHON"
"$HOST_RUN/environment/bin/hml" check-environment
ps -axo pid,ppid,pgid,state,command >/dev/null
HUMANMOTIONLIB_TEST_RUN_ROOT="$PWD/build/support-consumer-authored-motions_r1_dev_try-1_host-check" \
HUMANMOTIONLIB_SOURCE_ROOT="$PWD" \
  "$HOST_PYTHON" -m unittest \
    tests.test_consumer_motion tests.test_api tests.test_prepared_contract \
    tests.test_run_blender tests.test_blender_bootstrap
```

Consumer rendering repeats full schema, provenance, base-lineage, preflight
and solved-sample validation in host Python before Blender is probed. The
supervised launcher passes the accepted canonical prepared hash to the private
backend entry point. Blender checks that exact identity plus the prepared seal,
package/resource hashes and consumer sample/timeline references using its
standard library and HML; it does not load YAML, JSON Schema, or host validation
modules. The dependency-isolated reader and substitution checks are included in
`tests.test_consumer_motion`.

The following entry points are approved by the change design. Validation,
preparation, headless construction, numeric verification, render-pack assembly,
and HTML-only presentation regeneration are available. The synchronous public
Python generation API for packaged skeleton diagnostics and bounded consumer
motion inputs is documented in
[`docs/usage.md`](../docs/usage.md); it uses the same workspace and supervised
Blender contracts as the CLI:

```python
from pathlib import Path
from humanmotionlib.api import GenerationError, prepare, render

workspace = Path("/absolute/caller/workspace")
try:
    prepared = prepare(workspace=workspace, output="build/library-use_r1_app_try-1_prepare/input.json",
                       fixtures=("neutral", "arm-raise"), bpms=(90,))
    result = render(prepared, workspace=workspace,
                    output="build/library-use_r1_app_try-1_render")
except GenerationError as error:
    print(error.code, error.run_root, error.receipt_path)
    raise
```

A command existing does not establish complete OpenSpec acceptance; the task
list tracks the checks.

## Early visual gate and bounded preview

For a visual-affecting change, Gate 1 approves the exact preview plan with the change. Before an explicit early human decision, run only source/material clearance, selected source/schema/identity/environment checks, focused checks required for safe preview generation, and any one candidate-packaging step required by the installed workflow. Do not start full regression suites, full fixture/tempo/stature matrices, dense audits, duplicate render comparisons or the complete acceptance pack until the human accepts the identified preview. If no safe supported route can produce it, return to the architect for a bounded plan; do not relabel a full acceptance command as a preview.

The plan and pack identify exact fixture/pose/segment, every affected visible variant, view and detail views, one representative stature and BPM (or explain why not applicable), source/package identity, fixed scene/backend, and deferred scopes. Include baseline and changed count poses; for motion, one complete representative segment or closed cycle as a correctly timed GIF plus a key-transition onion skin from the same keyed animation. State omitted full-matrix, dense, native, repeatability and independent-review scopes as pending. Clear and register every external source before preview use. For Blender-backed work, use the pinned backend and fixed scene; follow the uv interpreter/origin/`.pth`/cache/package and process-visibility preflight in `AGENTS.md` whenever the preview route creates or tests an isolated environment or supervises a process.

Worked route (plan only; paths are illustrative and no render is started here): prepare one complete `arm-raise` fixture at the representative H=1.70 m and 120 BPM, then make one render batch for all three characters. This produces all 13 samples of the four-beat fixture (78 PNGs: fixed front/side views × three characters); no input or post-hoc renderer filtering is assumed. Beat 0 is the neutral baseline. A compact presentation may select already-rendered beats 0, 2 and 4 for labeled count sheets, while the timed GIF and transition onion use the complete generated animation timeline. Gate 1 fixes the crop rectangles from the fixed-camera projection before rendering; if the selected full views cannot expose a required detail through those crops, stop and return to the architect instead of moving a camera or adding an unplanned render. Build a distinct fresh presentation run using `result.images` and `prepared.timelines` plus the existing `humanmotionlib.review_graphics` sheet/GIF/onion helpers. This packages already generated images and makes no further Blender call; do not invoke `review-pack`, which starts duplicate clean renders. The exact supported API calls are:

```python
from pathlib import Path
from humanmotionlib.api import prepare, render

workspace = Path("/absolute/caller/workspace")
prepared = prepare(workspace=workspace,
                   output="build/add-shared-body-characters_r1_dev_try-1_prepare/input.json",
                   profile="adult-reference-v1", stature=1.70,
                   fixtures=("arm-raise",), bpms=(120,))
result = render(prepared, workspace=workspace,
                output="build/add-shared-body-characters_r1_dev_try-1_preview",
                images=True, characters=("skeleton", "male", "female"),
                render_only=True)
```

The presentation step is reproducible from the returned public records and paths:

```python
from fractions import Fraction
from pathlib import Path
from humanmotionlib.review_graphics import gif, onion, sheet

characters = ("skeleton", "male", "female")
images = {(image.character_id, image.sample_id, image.view): image.path
          for image in result.images}
animation = next(item for item in prepared.timelines
                 if item.fixture_id == "arm-raise" and item.bpm == 120
                 and item.mode == "animation")
static = next(item for item in prepared.timelines
              if item.fixture_id == "arm-raise" and item.bpm == 120
              and item.mode == "static")
presentation_root = workspace / "build/add-shared-body-characters_r1_dev_try-1_visual-pack"
# Preflight this as a fresh, empty run root before creating files.
presentation_root.mkdir()
count_entries = [entry for entry in static.entries
                 if entry.beat in (Fraction(0), Fraction(2), Fraction(4))]
interval = animation.entries[1].seconds - animation.entries[0].seconds
gif_reports = []
for view in ("front", "side"):
    count_paths = [images[(character, entry.sample_id, view)]
                   for entry in count_entries for character in characters]
    captions = [f"{entry.beat}-{character}"
                for entry in count_entries for character in characters]
    sheet(count_paths, captions, presentation_root / f"counts-{view}.png", columns=3)
    transitions = [entry for entry in animation.entries
                   if entry.beat in (Fraction(0), Fraction(1), Fraction(2),
                                     Fraction(3), Fraction(4))]
    for character in characters:
        frames = [images[(character, entry.sample_id, view)]
                  for entry in animation.entries]
        gif_report = gif(frames, interval,
                         presentation_root / f"{character}-{view}.gif")
        if gif_report["status"] != "pass":
            raise ValueError(f"GIF timing failed: {gif_report}")
        gif_reports.append((character, view, gif_report))
        onion([images[(character, entry.sample_id, view)] for entry in transitions],
              presentation_root / f"{character}-{view}-onion.png")

(presentation_root / "index.md").write_text(
    "# Early visual preview\n\n"
    f"Prepared identity: `{prepared.prepared_sha256}`\n\n"
    f"Render identity: `{result.render_identity}`\n\n"
    f"Package identity: `{prepared.package_identity}`\n\n"
    f"Source/material provenance: `{prepared.provenance.sources}`; "
    f"materials `{prepared.provenance.material_ids}`\n\n"
    f"Character provenance: `{result.character_provenance}`\n\n"
    f"Backend: `{result.backend_identity}`\n\n"
    f"GIF timing checks: `{gif_reports}`\n\n"
    "Scope: arm-raise, H=1.70 m, 120 BPM; all 13 generated samples, "
    "three characters, fixed front and side views (78 PNGs). Beat 0 is "
    "the neutral baseline.\n\n"
    "Deferred: native/evaluated geometry checks; other fixtures, BPMs and "
    "statures; diagnostic matrices; repeatability; independent review and "
    "final human gate.\n"
)
```

Add fixed pixel crops of the already rendered front/side images for shoulder, waist/hip, knee and sole details; record each crop rectangle and source image in the index. Cropping does not move the camera or add a Blender pass. The index records all created render samples, selected presentation samples, source/package identity, fixed scene/backend, chosen stature/BPM, crop rectangles, limitations, and deferred fixtures, statures, BPMs, diagnostic matrices, repeatability and independent-review scopes as pending. Retain provenance from `result.character_provenance` and `result.prepared.provenance`. The historical thoracic/squat examples below include `review-pack` and its repeated clean passes; they are not early-gate routes. Do not execute those pack commands before the human early decision for a new visual direction.

## Character selection

`skeleton`, `male` and `female` are equal render character IDs. The skeleton is
the default and has no surface template. Male and female use the same prepared
movement and rig; only the authored surface appearance differs. Prepare the
movement once and select one or all IDs when rendering:

```sh
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" run-blender \
  --input build/add-shared-body-characters_r1_dev_try-1_prepare/input.json \
  --output build/add-shared-body-characters_r1_dev_try-1_render \
  --characters skeleton male female
```

The API equivalent is:

```python
result = render(prepared, workspace=workspace, output=render_root,
                characters=("skeleton", "male", "female"))
```

A single-character selection uses a one-item tuple. The selection is validated before backend probing and
normalized to registry order. Result images are joined by
`(character_id, sample_id, view)` while pose and timeline IDs remain shared.
Run roots are independent flat children of `build/`; prepare and render roots
must not overlap. Canonical character YAML, versioned schemas, source guide and
usage documentation are copied into the explicit wheel/sdist resource closure
and verified by the runtime manifest. See [`docs/usage.md`](../docs/usage.md)
and [`docs/character-models.md`](../docs/character-models.md) for user-facing
examples and source/binding details.

The public result adds `RenderedImage.character_id`, per-character artifact
records, `character_provenance` and `render_identity`. Surface renders persist
the sealed `character-render-request/v1` and ordered
`character-render-manifest/v1`; receipts bind the union output inventory.
Canonical resource changes require regeneration under the package identity
rules. Character surfaces add no runtime dependency or downloaded mesh asset.

## Character review pack

The normal `review-pack` command accepts `--characters ID [ID ...]` and defaults
to `skeleton`, preserving the existing skeleton-only presentation. IDs are
validated and normalized to registry order. For the complete standalone
character comparison pack, supply all three IDs, a primary H=1.70m evaluated
input and supplementary candidate runs with repeatable `--stature-input H=RUN`
(H=1.50 and H=1.90). Historical skeleton comparison is optional and may be
supplied with `--skeleton-baseline RUN`:

```sh
hml --workspace "$PWD" review-pack \
  --input build/add-shared-body-characters_r1_app_try-1_candidate \
  --characters skeleton male female \
  --stature-input 1.50=build/add-shared-body-characters_r1_app_try-2_short \
  --stature-input 1.90=build/add-shared-body-characters_r1_app_try-3_tall \
  --skeleton-baseline build/add-shared-body-characters_r0_baseline_try-1_render \
  --output build/add-shared-body-characters_r1_app_try-1_pack
```

All supplied evidence is checked before the output directory or managed render
passes are created. Stature labels must match their persisted profile within
1e-9m; the candidate profile, mobility and fixed scene sources must match, and
neutral plus squat beat 2 must be present. If supplied, the baseline is
validated against its own historical seal and output receipt and stays
read-only; malformed or stale evidence fails preflight. Missing required
stature or current-mode comparison evidence produces an explicitly incomplete
report. Historical baseline absence does not affect current-candidate pack
completeness. No frame is rescaled, fabricated, or substituted. Review renders use the internal
designated-owner adapter to the same sealed API preflight, supervised backend,
and artifact validation as `api.render`. The public API still accepts only
fresh independent flat output roots.

The approved reduced acceptance route is explicit `diagonal-v1`; it accepts
only `skeleton` H=1.50m, `male` H=1.70m and `female` H=1.90m, with each pair
rendered in two independent clean passes. `--input` must be the skeleton H=1.50m
run, and each `--diagonal-input` is a distinct evaluated run:

```sh
hml --workspace "$PWD" review-pack \
  --acceptance-scope diagonal-v1 \
  --input build/add-shared-body-characters_r9_dev_try-1_skeleton-150 \
  --diagonal-input skeleton=build/add-shared-body-characters_r9_dev_try-1_skeleton-150 \
  --diagonal-input male=build/add-shared-body-characters_r9_dev_try-1_male-170 \
  --diagonal-input female=build/add-shared-body-characters_r9_dev_try-1_female-190 \
  --output build/add-shared-body-characters_r9_reviewer_try-1_diagonal-pack
```

The diagonal pack labels its overview as mixed character/height and lists the
six excluded pairs. It does not claim a complete Cartesian matrix or full
change acceptance. Native numeric, source/package/API/CLI parity, independent
review and Human Gate 2 remain separate requirements.

Pack reports mark `scope=visual-comparison-pack` and
`full_change_acceptance=not-assessed`. Source/package and API/CLI parity,
complete native/dense numeric and contact verification, independent review,
and human Gate 2 are separate evidence required to accept the full change.

The output owns `clean-a/`, `clean-b/`, default/explicit skeleton and singleton
comparison passes, and optional `stature-150/` / `stature-190/` passes. The
assembled report includes front/side sheets, GIFs, count-direction onion skins,
neutral/rest front/side/rear silhouette rows, shared joint-center overlays,
fixed sole/contact crops, stature strips, copied baseline frames, exact
decoded-pixel comparisons, and JSON coverage/inventory/source reports. HTML-only
regeneration remains presentation-only and rejects these normal-mode inputs.

### Numeric-only character verification

An intentional no-images character build is checked explicitly, never inferred
from a missing manifest:

```sh
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" verify-skeleton \
  --input build/add-shared-body-characters_r1_dev_try-1_h170-build \
  --output build/add-shared-body-characters_r1_dev_try-1_numeric-check/report.json \
  --character-output build/add-shared-body-characters_r1_dev_try-1_h170-build \
  --numeric-only
```

This mode requires a successful supervised `build` receipt and exact hashes for
the input, metadata, saved scene, character request, evaluated skeleton and
geometry, and each selected surface reference/evaluated pair. It runs the same
native, sealed-midpoint and dense-reference checks; it does not create a
manifest or render images. Reports state `rendering: not-run` and
`visual: not-assessed`. The character acceptance verdict remains incomplete.
The default verifier continues to require the complete render manifest and
image inventory. Add three disjoint run roots with `--stature-builds RUN RUN
RUN` for the H=1.50/1.70/1.90 numeric matrix; each run must use the same
candidate package, backend contract, canonical sources, diagnostics and
sampling coverage, and all evaluated cross-stature checks must pass. A single
stature result stays scoped and lists the other required heights as missing.

The reduced `diagonal-v1` scope uses exactly skeleton H=1.50m, male H=1.70m
and female H=1.90m. A numeric leaf uses one approved character and its matching
run:

```sh
hml --workspace "$PWD" verify-skeleton \
  --acceptance-scope diagonal-v1 --numeric-only --selected-character male \
  --input build/add-shared-body-characters_r9_dev_try-1_male-170 \
  --character-output build/add-shared-body-characters_r9_dev_try-1_male-170 \
  --output build/add-shared-body-characters_r9_dev_try-1_numeric/report.json
```

The aggregate uses three repeatable `--diagonal-build CHARACTER=RUN` operands;
`--input` and `--character-output` name the skeleton H=1.50m run. It reports
required, observed and unassessed pairs without setting `matrix_complete`.
Rendering, repeatability, visual judgment and full change acceptance remain
separate requirements.

```sh
build/project-tools_r1_contributor_current_environment/environment/bin/hml validate --profile adult-reference-v1
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" prepare-skeleton --profile adult-reference-v1 --output build/anatomical-human-skeleton_r1_dev_try-1_build/input.json
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" run-blender --input build/anatomical-human-skeleton_r1_dev_try-1_build/input.json --output build/anatomical-human-skeleton_r1_dev_try-1_build
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" verify-skeleton --input build/anatomical-human-skeleton_r1_dev_try-1_build --output build/anatomical-human-skeleton_r1_dev_try-1_checks/metrics.json
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" review-pack --input build/anatomical-human-skeleton_r1_dev_try-1_build --output build/anatomical-human-skeleton_r1_dev_try-1_pack
HOST_RUN=build/upgrade-host-python-314_r1_dev_try-1_host
HOST_PYTHON="$PWD/$HOST_RUN/environment/bin/python"
HUMANMOTIONLIB_TEST_RUN_ROOT="$PWD/$HOST_RUN" HUMANMOTIONLIB_SOURCE_ROOT="$PWD" "$HOST_PYTHON" -m humanmotionlib.check_host --test-root "$PWD/tests"
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
cleanup status. Each invocation keeps temporary, Blender config and cache data
in its own `<run-root>/processes/<invocation-id>/scratch/` directory. The
supervisor removes scratch after a successful, confirmed child exit and retains
it with a receipt reason when execution fails or cleanup is unresolved. Review
packs own two internal pass roots, `clean-a/` and `clean-b/`; each pass has its
own receipts and scratch, while independent run identities remain direct
children of `build/`. A receipt is updated atomically as the invocation
progresses.
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
Normal direct-child completion is reaped without probing or signaling its
saved process-group ID. On timeout or cancellation, TERM/KILL and group-state
probes are limited to the period before the direct child is reaped. If group
termination cannot be confirmed before reaping, the receipt reports
`cleanup_pending` and the operation fails with its diagnostics retained. The
supervisor does not inspect the global process table. The backend supervisor
and its dedicated tests own workspace lock retirement and cross-caller overlap
behavior.

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

Explicit Make cleanup uses these fixed disposable areas:

| Target | Selected area |
|---|---|
| `make mostlyclean` | Every direct `build/*_stage` and `build/*_check` entry, with all nested/hidden contents |
| `make clean` | Every direct child of `build/` except the configured reusable tools root |
| `make distclean` | The entire `build/` directory, including reusable tools |

Unknown files, local R6/history and matrix logs inside a selected area are
removed with everything else there. No owner records, path inventories,
history exceptions or legacy-reference scans are used. Canonical files and
releases under `dist/` are outside these areas; keep durable reports/artifacts
in the existing review/hand-off or external artifact storage. Role-scoped
automatic cleanup remains within its assigned run area and does not silently
become a whole-workspace Make cleanup.

Before removal, cleanup verifies that selected paths remain inside the real
workspace `build/` boundary and checks active work using process visibility and
open/cwd path inspection. It never terminates work or traverses a selected
symlink; it unlinks the link itself. Missing process visibility, an active
process or an escaping boundary stops cleanup before deletion. Failures report
completed removals and pending paths. Test broad cleanup only on disposable
trees, never against real build history.

Compact hand-off record example:

```markdown
### Cleanup
- Selected: `make mostlyclean` — direct `_stage` and `_check` entries in a disposable checkout.
- Removed: `<path>` — `<bytes>` bytes.
- Pending: `<path>` — `<reason>`, if any.
- Activity/path check: pass or pending with the exact failed check.
- Pending cleanup: none, or list the remaining operation.
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
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" review-pack \
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

The entire command sequence below is a historical, post-early-acceptance
diagnostic/review workflow, not a bounded early-gate recipe. Preparation uses
the default three BPMs; verification and `review-pack` add further work, and
the pack launches clean render passes. For new visual work, do not run any
command in this sequence before early acceptance. The word “focused” below
refers only to its feature-specific diagnostic scope.

Before regenerating full diagnostic packs, prepare just the two structural
poses in a fresh flat build run, then build, measure and render them using the
same entry points. The verifier report and preview pack use separate sibling
runs:

```text
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" prepare-skeleton --profile adult-reference-v1 --fixtures neutral rest --output build/anatomical-human-skeleton_r1_dev_thorax-preview_build/input.json
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" run-blender --input build/anatomical-human-skeleton_r1_dev_thorax-preview_build/input.json --output build/anatomical-human-skeleton_r1_dev_thorax-preview_build
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" verify-skeleton --input build/anatomical-human-skeleton_r1_dev_thorax-preview_build --output build/anatomical-human-skeleton_r1_dev_thorax-preview_checks/metrics.json --thorax-preview
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" review-pack --input build/anatomical-human-skeleton_r1_dev_thorax-preview_build --output build/anatomical-human-skeleton_r1_dev_thorax-preview_pack
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
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" verify-skeleton --input build/anatomical-human-skeleton_r1_dev_try-1_build/input.json --output build/anatomical-human-skeleton_r1_dev_transform-check_checks/prepared-metrics.json --transforms-only --action-coverage
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

Direct callers can use `verify_transforms(prepared)` as a pure in-memory check,
or call `verification_run.verify_collection` for full evaluated evidence. The
full writer requires `workspace=` and an output inside a fresh run allocated by
the caller; it writes `metrics-samples/`, returns the summary for persistence,
and rejects escaped or overlapping destinations before creating files:

```python
from pathlib import Path
from humanmotionlib.prepared import write_json
from humanmotionlib.runtime import validate_run_content_path
from humanmotionlib.verify_skeleton import verify_transforms
from humanmotionlib.verification_run import verify_collection

workspace = Path("/absolute/caller/workspace")
run = workspace / "build/portable-installed-runtime_r1_app_try-1_verify"
# Allocate this as a fresh direct child of workspace/build first.
summary = verify_collection(
    prepared, evaluated, run / "metrics.json", verify_transforms,
    workspace=workspace,
)
report, _ = validate_run_content_path(run / "metrics.json", workspace)
write_json(report, summary)
```

`verify_collection` writes the shard directory and returns the summary for the
caller to persist to the validated report path. The numerical records and
acceptance bounds are those produced by the existing `backend_measurements`
verifier; this API change only constrains where they are written. Prepared-only
transforms do not establish backend acceptance.

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
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" verify-skeleton --input build/anatomical-human-skeleton_r1_dev_try-1_build --output build/anatomical-human-skeleton_r1_dev_try-1-dense_checks/metrics.json --action-coverage --dense-floor
```

The native anatomical hierarchy also uses computed world-frame adapter targets
inside `Controls`. They copy the authoritative solved frames to native bones,
preventing accumulated float32 translation cancellation along the vertebral
chain. They add no independent anatomical channels or public humanoid targets.
Geometry still follows its native bone via rigid body attachments. Fault tests
mutate these actual scene targets and still must fail independent measurements.

To include actual cross-stature vertex/topology and native rest-frame comparison:

```sh
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" verify-skeleton --input build/anatomical-human-skeleton_r1_dev_try-1_build --output build/anatomical-human-skeleton_r1_dev_try-1-stature_checks/metrics.json --action-coverage --dense-floor --stature-builds build/anatomical-human-skeleton_r1_dev_stature-1-5_build build/anatomical-human-skeleton_r1_dev_try-1_build build/anatomical-human-skeleton_r1_dev_stature-1-9_build
```

Generate the additional stature builds with the same preparation/build commands,
adding `--stature 1.5` or `--stature 1.9` to preparation and using sibling roots
`build/anatomical-human-skeleton_r1_dev_stature-1-5_build/` and
`build/anatomical-human-skeleton_r1_dev_stature-1-9_build/`. Each verifier output
belongs in its own flat checks run. All delivered samples at each stature must
also pass their own backend verifier run.

```sh
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" prepare-skeleton --profile adult-reference-v1 --stature 1.5 --output build/anatomical-human-skeleton_r1_dev_stature-1-5_build/input.json
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" run-blender --input build/anatomical-human-skeleton_r1_dev_stature-1-5_build/input.json --output build/anatomical-human-skeleton_r1_dev_stature-1-5_build
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" prepare-skeleton --profile adult-reference-v1 --stature 1.9 --output build/anatomical-human-skeleton_r1_dev_stature-1-9_build/input.json
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" run-blender --input build/anatomical-human-skeleton_r1_dev_stature-1-9_build/input.json --output build/anatomical-human-skeleton_r1_dev_stature-1-9_build
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" verify-skeleton --input build/anatomical-human-skeleton_r1_dev_stature-1-5_build --output build/anatomical-human-skeleton_r1_dev_stature-1-5_checks/metrics.json --action-coverage --dense-floor
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" verify-skeleton --input build/anatomical-human-skeleton_r1_dev_stature-1-9_build --output build/anatomical-human-skeleton_r1_dev_stature-1-9_checks/metrics.json --action-coverage --dense-floor
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

The entire command sequence below is a historical, post-early-acceptance
diagnostic/review workflow, not a bounded early-gate route. Preparation uses
the default three BPMs, the verifier runs feature diagnostics, and `review-pack`
launches clean render passes. For new visual work, do not run any command in
this sequence before early acceptance. Do not treat the word “preview” in this
older change-specific instruction as authorization to start this workload.

The original feature-specific command sequence was:

```sh
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" prepare-skeleton --profile adult-reference-v1 --fixtures squat --output build/anatomical-human-skeleton_r1_dev_squat-preview_build/input.json
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" run-blender --input build/anatomical-human-skeleton_r1_dev_squat-preview_build/input.json --output build/anatomical-human-skeleton_r1_dev_squat-preview_build
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" verify-skeleton --input build/anatomical-human-skeleton_r1_dev_squat-preview_build --output build/anatomical-human-skeleton_r1_dev_squat-preview_checks/metrics.json --squat-preview
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" review-pack --input build/anatomical-human-skeleton_r1_dev_squat-preview_build --output build/anatomical-human-skeleton_r1_dev_squat-preview_pack
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

Every filesystem-writing command and direct writer API requires an explicit
absolute caller workspace. The global CLI option goes before the subcommand;
relative input/output operands are interpreted under that workspace, even when
the process starts from another directory. Read-only `help`, `version`,
`validate`, and `check-environment` do not create HML state and need no
workspace. For repository work, use `"$PWD"`; for an installed caller, use its
own absolute workspace path:

```sh
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" prepare-skeleton \
  --profile adult-reference-v1 --output build/portable-installed-runtime_e3dcbf_dev_try-1_fixture/input.json
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" run-blender \
  --input build/portable-installed-runtime_e3dcbf_dev_try-1_fixture/input.json \
  --output build/portable-installed-runtime_e3dcbf_dev_try-1_fixture
build/project-tools_r1_contributor_current_environment/environment/bin/hml --workspace "$PWD" verify-skeleton \
  --input build/portable-installed-runtime_e3dcbf_dev_try-1_fixture \
  --output build/portable-installed-runtime_e3dcbf_dev_try-1_metrics/checks.json --transforms-only
```

Python callers pass the same required context explicitly, for example
`prepare_skeleton.main(workspace="/absolute/caller/workspace")` after setting
the command arguments. No writer selects a workspace from the current directory.

| Previous checkout command | Installed command |
|---|---|
| `python tools/validate.py ...` | `hml validate ...` |
| `python tools/prepare_skeleton.py ...` | `hml prepare-skeleton ...` |
| `python tools/run_blender.py ...` | `hml run-blender ...` |
| `python tools/verify_skeleton.py ...` | `hml verify-skeleton ...` |
| `python tools/review_pack.py ...` | `hml review-pack ...` |
| `python tools/check_host.py --check-environment` | `hml check-environment` |
| `tools.<module>` | `humanmotionlib.<module>` |
