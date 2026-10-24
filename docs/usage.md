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

The optional global `--workspace PATH` selects the writable workspace and must
appear before the command name. It defaults to the resolved invocation working
directory. Relative input and output arguments are resolved from the invocation
working directory; choosing a workspace does not rewrite their meaning. HML
writes managed run state under the workspace's `build/` directory and does not
write into its installed package files.

```sh
# Validate canonical data and inspect an installation.
hml --workspace /path/to/workspace validate --profile adult-reference-v1
hml check-environment

# Prepare all diagnostic fixtures, or select a subset explicitly.
hml --workspace /path/to/workspace prepare-skeleton \
  --profile adult-reference-v1 --output /path/to/workspace/build/<run>/input.json
hml --workspace /path/to/workspace prepare-skeleton \
  --profile adult-reference-v1 --fixtures neutral rest \
  --output /path/to/workspace/build/<run>/input.json

# Supervised Blender construction, numeric verification and review presentation.
hml --workspace /path/to/workspace run-blender \
  --input /path/to/workspace/build/<run>/input.json \
  --output /path/to/workspace/build/<run>
hml --workspace /path/to/workspace verify-skeleton \
  --input /path/to/workspace/build/<run> \
  --output /path/to/workspace/build/<check-run>/metrics.json
hml --workspace /path/to/workspace review-pack \
  --input /path/to/workspace/build/<run> \
  --output /path/to/workspace/build/<pack-run>

# Regenerate HTML presentation from a retained, verified predecessor pack.
hml --workspace /path/to/workspace review-pack \
  --html-only-from /path/to/verified/predecessor-pack \
  --output /path/to/workspace/build/<pack-run>
```

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
uses `hml run-blender` or `hml review-pack` so the supervisor can check backend
identity, enforce deadlines and record receipts.

## Source contributors

For development, use the repository's pinned CPython selector and locked uv
environment. `uv sync --locked --no-editable` builds and installs the project wheel with its contributor/build
dependencies. Use `uv run --locked --no-sync` afterward so uv does not request an editable install. Source validation and generation use the same `hml` commands;
the default workspace is the checkout when invoked from its root. Keep every
new run in a fresh direct child of `build/`.

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
