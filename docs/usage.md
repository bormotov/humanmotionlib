# HumanMotionLib usage

HumanMotionLib is distributed as the `humanmotionlib` Python package, version
`0.2.0`. Python imports use the `humanmotionlib.*` namespace. The installed
command is `hml`; `python -m humanmotionlib` exposes the same command dispatcher.
The supported host interpreter is CPython `>=3.14,<3.15`.

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
workspace and places both `metrics.json` and its `metrics-samples/` shard
directory in the supplied fresh run. `prepared` and `evaluated` below are
objects loaded and validated by the caller from explicit input paths:

```python
from pathlib import Path
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
```

The API checks that the summary and every per-sample shard stay inside the
selected run. Its records retain measured/expected values, bounds, units,
status and image links; the existing verifier tolerances and failure
thresholds are unchanged. Use `verify_transforms(prepared)` when only the
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
