# Installed package acceptance

## Candidate and environment

- Candidate: `humanmotionlib-0.3.0-py3-none-any.whl`, generated for try85.
- Wheel SHA-256: `b14d5315e7e344eacb212c0cfa803f4b837ea7fa2bf8d9e9c82f9ecd40792c55`.
- Runtime manifest SHA-256: `da144c15f66f37eb334e3ff776fcd04ed752aaec00e14aac465b378559e3ba09`.
- Fresh, non-editable venv: `build/add-shared-body-characters_r1_dev_try-123_installed-acceptance/venv`.
- Interpreter: Python 3.14.6. Installed HML imported from that venv's `site-packages`; distribution version is 0.3.0 and `direct_url.json` points to the try85 wheel with no editable-install marker.
- The installed HML package and its dist-info were made read-only before the run. Their captured tree hashes are in `build/add-shared-body-characters_r1_dev_try-123_installed-acceptance/bootstrap-manifest.json`; the test fixture also verifies that installed HML bytes are unchanged after the suite.
- Runtime dependency directories were copied offline from the earlier verified try2 venv and byte-checked during bootstrap. The copied closure contains Pillow 12.3.0, attrs 26.1.0 (both `attrs` and `attr`), jsonschema 4.26.0, jsonschema-specifications 2025.9.1, referencing 0.37.0, rpds-py 2026.9.1, and PyYAML 6.0.3. Per-directory source hashes are recorded in the bootstrap manifest. No dependency was downloaded.
- Invocation ran from the unrelated `cwd-one` directory, which contains a valid decoy `pyproject.toml` and poison source-shaped directories. The API was given the repository as its explicit workspace so API-created run roots stayed directly under `build/`.

## Commands and result

Bootstrap:

```text
uv venv --no-cache --no-python-downloads --python /Users/bormotov/work/humanmotionlib/.venv/bin/python3 build/add-shared-body-characters_r1_dev_try-123_installed-acceptance/venv
uv pip install --offline --no-deps --cache-dir build/add-shared-body-characters_r1_dev_try-123_installed-acceptance/uv-cache --python build/add-shared-body-characters_r1_dev_try-123_installed-acceptance/venv/bin/python build/add-shared-body-characters_r1_dev_try-85_numeric-wheel/humanmotionlib-0.3.0-py3-none-any.whl
uv run --no-sync --no-project --cache-dir build/add-shared-body-characters_r1_dev_try-123_installed-acceptance/uv-cache --python build/add-shared-body-characters_r1_dev_try-123_installed-acceptance/venv/bin/python python build/add-shared-body-characters_r1_dev_try-123_installed-acceptance/bootstrap.py
```

Focused host acceptance (environment variables set the decoy-root fixture and explicit workspace):

```text
HML_ACCEPTANCE_WORKSPACE=/Users/bormotov/work/humanmotionlib/build/add-shared-body-characters_r1_dev_try-123_installed-workspace HML_ACCEPTANCE_REPOSITORY=/Users/bormotov/work/humanmotionlib HML_ACCEPTANCE_ROOT=/Users/bormotov/work/humanmotionlib/build/add-shared-body-characters_r1_dev_try-123_installed-acceptance PYTHONDONTWRITEBYTECODE=1 \
uv run --no-sync --no-project --cache-dir /Users/bormotov/work/humanmotionlib/build/add-shared-body-characters_r1_dev_try-123_installed-acceptance/uv-cache --python /Users/bormotov/work/humanmotionlib/build/add-shared-body-characters_r1_dev_try-123_installed-acceptance/venv/bin/python python /Users/bormotov/work/humanmotionlib/tests/test_character_installation.py
```

Result: **7 tests passed** in 35.580 seconds. Captured stdout: `build/add-shared-body-characters_r1_dev_try-123_installed-acceptance/test-output.log`. The first try122 run had 4/7 pass and exposed three incorrect test expectations (`skeletal` renderer kind and `input-integrity` for package-wide byte tampering); the assertions were corrected and the full slice passed from a fresh try123 install. The first attempt's failure trace was retained in the task conversation; no product code was changed for it.

Coverage in `tests/test_character_installation.py`:

1. Imports and dependency closure come from a non-editable wheel installation; registry and all three character descriptors resolve there.
2. Public prepare/render records round-trip all three character IDs, maintain the shared prepared input, and seal the render request.
3. The `hml` entry point prepares from the unrelated decoy CWD with an explicit workspace.
4. Skeleton selection and preparation do not semantically load surface templates or appearances.
5. Missing or corrupt packaged appearance bytes fail the global integrity gate with `input-integrity` before backend probing or output creation.
6. Corrupt implementation bytes fail the same preflight without changing the actual install, probing the backend, or creating output.
7. Empty, duplicate and unknown character selections fail before backend probing or output creation.

The skeleton lazy-loading check patches the YAML semantic loader. It intentionally does not remove a body file: a missing file is a package-wide integrity failure even when skeleton rendering would not parse that body definition.

## Evidence and run inventory

- Test source SHA-256 after the successful run: `a05eb45cf18fb89875beef8e0cf1d1f84927dd57004ca94c693ce9916fb77314`.
- Bootstrap script SHA-256: `275b7aaa38f568c64dff4f7bef6008d6ab20b645f3360621c6f9528f95fc4160`.
- Bootstrap manifest SHA-256: `20f9b25ddc6889f4f08b0a0cbc0d56f7b652d93ef8e7dd33a0cd62788877a6ee`.
- Successful venv, bootstrap evidence and decoy CWD are retained at `build/add-shared-body-characters_r1_dev_try-123_installed-acceptance/` for parent/reviewer inspection. The API workspace was the repository itself so its generated run roots stayed flat under `build/`; the empty sibling try123 workspace root was removed.
- Superseded try122 acceptance and generated API roots were inventoried and removed: 161,900,448 file bytes total across the try122 acceptance, workspace, shared-input, skeleton-lazy-input, api-render, api-input and cli-input roots. Four internal symlinks (three venv interpreter aliases and one uv cache wheel link) were removed without following them. The empty `build/add-shared-body-characters_r1_dev_try-122_installation-check/` was pre-existing/ownership-unclear and was not touched.
- No other agent's native matrix or candidate artifacts were read, modified or removed. No Blender process was started.

This report covers the installation acceptance slice only. It does not assert the full numerical, dense-surface, visual or reviewer gates.

## Final candidate installation (try142)

The final candidate wheel at
`build/add-shared-body-characters_r1_dev_try-142_candidate-wheel/wheelhouse/humanmotionlib-0.3.0-py3-none-any.whl`
has SHA-256
`54f0820a4e9a38069eaabfc87da6d08f8237e5ee065a314f22957ab663fc6611` and
runtime-manifest SHA-256
`e0e502871751ca42cced0976c7a73727fea708920ff5dc2cbba5709bb1c08aa7`. The
fresh non-editable Python 3.14.6 installation is retained at
`build/add-shared-body-characters_r1_dev_try-146_installed-acceptance/venv/`.
The wheel's package and dist-info were made read-only before test execution;
the test verifies they remain byte-identical. Runtime dependencies were copied
from the earlier local verified install and byte-checked, with no downloads.

The seven installed acceptance cases passed in 41.341 seconds. They ran from
`cwd-one`, containing a valid decoy project and poison source directories,
while HML was imported from the non-editable venv and API outputs used the
explicit repository workspace. They check installed origins/registries,
character result and shared-preparation records, CLI behavior, skeleton lazy
surface loading, global missing/corrupt resource integrity, implementation
tampering, and invalid character selection. Blender was intentionally not
launched by these host acceptance fixtures. Output is
`build/add-shared-body-characters_r1_dev_try-146_installed-acceptance/test-output.log`.

Commands:

```text
uv venv --no-cache --no-python-downloads --python .venv/bin/python build/add-shared-body-characters_r1_dev_try-146_installed-acceptance/venv
uv pip install --offline --no-deps --cache-dir build/add-shared-body-characters_r1_dev_try-146_installed-acceptance/uv-cache --python build/add-shared-body-characters_r1_dev_try-146_installed-acceptance/venv/bin/python build/add-shared-body-characters_r1_dev_try-142_candidate-wheel/wheelhouse/humanmotionlib-0.3.0-py3-none-any.whl
build/add-shared-body-characters_r1_dev_try-146_installed-acceptance/venv/bin/python build/add-shared-body-characters_r1_dev_try-146_installed-acceptance/bootstrap.py
# From build/add-shared-body-characters_r1_dev_try-146_installed-acceptance/cwd-one:
HML_ACCEPTANCE_WORKSPACE=/Users/bormotov/work/humanmotionlib/build/add-shared-body-characters_r1_dev_try-146_installed-acceptance HML_ACCEPTANCE_REPOSITORY=/Users/bormotov/work/humanmotionlib HML_ACCEPTANCE_ROOT=/Users/bormotov/work/humanmotionlib/build/add-shared-body-characters_r1_dev_try-146_installed-acceptance PYTHONDONTWRITEBYTECODE=1 /Users/bormotov/work/humanmotionlib/build/add-shared-body-characters_r1_dev_try-146_installed-acceptance/venv/bin/python /Users/bormotov/work/humanmotionlib/build/add-shared-body-characters_r1_dev_try-146_installed-acceptance/test_character_installation.py
```

The canonical test source hash is
`28c39510575a1c89c6c2ad4d18d6e7f3936d8bdccbd1d5d61c6bcea7b589801b`. A
run-local copy changes only unique `try-123` workspace labels to `try-146` to
avoid collisions with historical acceptance outputs; its hash is
`92fc1930328269dad6ed1424f52aee5ad8b1b6c13a8ccfb3b4aa34eb6a2fc964`. The
bootstrap is run-local; its SHA-256 is
`884b97a1d2970f4ac2d54a9c7db7265194fda2c6f18b789992c12f026b84f116` and its
bootstrap manifest is retained beside it.

Cleanup inventory: an initial try144 launch ran from the wrong current working
directory, so one fixture failed on its decoy-CWD precondition after the other
six passed. This was a harness invocation error; a fresh try146 run from the
decoy directory passed all seven. The obsolete try144 root (1,027 files,
25,748,030 regular-file bytes, four internal symlinks) and empty try145
workspace root were removed after confirming both were owned, direct children
of `build/`; symlink targets were not followed. The empty try147 workspace
directory was also removed. Successful try146 is retained as review evidence:
1,027 files, 25,745,173 bytes and four internal virtualenv/cache symlinks; the
test and bootstrap manifests record the installed tree hashes. No outside
symlink target was read or changed. The separate packaging archive verification
is in `packaging-check.md`.

## Final try168 installed acceptance

The follow-up candidate after the final review-pack path/string fix was
installed from the exact wheel
`build/add-shared-body-characters_r1_dev_try-168_candidate-build/wheelhouse/humanmotionlib-0.3.0-py3-none-any.whl`
(SHA-256 `b702c7bf928280245271f72d521bfdc5e519feb32f1a193346d93deb7cd4001b`,
runtime manifest
`b457ec11b1dec544dc0a6b89d8c71b04c58721bf1ab890a371b27d3cc05c5dfb`) into
the fresh, non-editable Python 3.14.6 venv at
`build/add-shared-body-characters_r1_character-final-packaging_try-3_installed-acceptance/venv/`.
The test ran with that venv's interpreter from its decoy `cwd-one` directory,
which contains a valid decoy project and poison source folders. HML was not
imported from the checkout. Package and dist-info were made read-only before
the run and remained unchanged. Runtime dependencies were copied from the
already verified local environment and hash-checked; no dependency was
downloaded.

The installed acceptance suite passed **7/7 in 50.347 seconds**:

```text
HML_ACCEPTANCE_WORKSPACE=/Users/bormotov/work/humanmotionlib/build/add-shared-body-characters_r1_character-final-packaging_try-3_installed-acceptance HML_ACCEPTANCE_REPOSITORY=/Users/bormotov/work/humanmotionlib HML_ACCEPTANCE_ROOT=/Users/bormotov/work/humanmotionlib/build/add-shared-body-characters_r1_character-final-packaging_try-3_installed-acceptance PYTHONDONTWRITEBYTECODE=1 /Users/bormotov/work/humanmotionlib/build/add-shared-body-characters_r1_character-final-packaging_try-3_installed-acceptance/venv/bin/python /Users/bormotov/work/humanmotionlib/build/add-shared-body-characters_r1_character-final-packaging_try-3_installed-acceptance/test_character_installation.py
```

The exact source test hash is
`28c39510575a1c89c6c2ad4d18d6e7f3936d8bdccbd1d5d61c6bcea7b589801b`. The
run-local copy changes only generated run-root labels to avoid collisions; its
SHA-256 is
`be6004ac09ec746fd05d0f112da07ecb43444cccb6d437ef842d0e23ebaabc46`. The
bootstrap SHA-256 is
`03f58626b79c48118f6f63a3742dba58565d769d58a290190235e91707aaa15c`; its
manifest records Python, wheel path, dependency hashes and installed-tree
hashes. Output is
`build/add-shared-body-characters_r1_character-final-packaging_try-3_installed-acceptance/test-output.log`.
Blender was not launched by these host tests.

This try168 installed result covers selection, preparation/render result
records, CLI invocation, skeleton lazy surface loading, tampered/missing
resources and invalid selections from the final candidate. It complements the
try168 archive closure in `packaging-check.md`; subsequent code changes require
their own candidate-specific recheck.

Cleanup record: both successful fresh run roots are direct children of
`build/`, retained for the developer handoff and review, with no links in the
package-check run and four venv/cache symlinks in the installed run.
They contain 13 files / 983,846 bytes and 1,027 files / 25,796,258 bytes,
respectively. Symlink targets were not followed. The successful
install/environment is the dependency closure of its report.

The complete installation rerun also created temporary API input/output roots
as part of the test cases. After the suite passed, the five owned direct-child
runs `..._try-3_api-render`, `..._try-3_shared-input`,
`..._try-3_cli-input`, `..._try-3_skeleton-lazy-input`, and
`..._try-3_api-input` were inventoried and removed. They contained 141,318,942
regular-file bytes total and zero symlinks; no paths were followed. Before and
after inventories showed no links in those roots. The package-check and
installed-acceptance roots remain the evidence dependency closure.

The try168 suite is scoped to installed selection/API/CLI, lazy loading and
resource integrity. It does not resolve the separately reported managed-pass
render-pack issue; any follow-up candidate incorporating that fix requires a
new identity-bound acceptance run.

## Final managed-pass candidate installed acceptance (try177)

The frozen managed-pass-fix candidate was installed from the exact wheel
`build/add-shared-body-characters_r1_dev_try-177_candidate-build/wheelhouse/humanmotionlib-0.3.0-py3-none-any.whl`
(SHA-256
`bf42f87b0ebad22a7c1da01666299aa7874eecf7eed56f6e0ae4a35da131ddb8`, runtime
manifest SHA-256
`06d2fed42a7e798bebc1d5b92d74fd10a1f10340c0ff1308fc77bee53da795c4`) into a
fresh non-editable Python 3.14.6 venv at
`build/add-shared-body-characters_r1_character-final-packaging_try-5_installed-acceptance/venv/`.
The package and dist-info were made read-only before running the acceptance
suite. Runtime dependencies were copied offline from the previously verified
local acceptance environment and individually hash-checked; the install used
`--offline --no-deps`, with no dependency download. The bootstrap manifest
records the candidate wheel path, dependency hashes, venv Python version, and
installed package/dist-info tree hashes.

The suite ran from the unrelated `cwd-one` decoy project, using the explicit
repository workspace. HML imported from the venv's non-editable site install,
not the checkout. All seven tests passed in 34.373 seconds. Coverage includes
selected character registry/order and source closure, portable public prepare
and render records, CLI invocation, skeleton-only lazy surface parsing,
missing/corrupt resource rejection before backend/output, implementation
tamper rejection, and invalid character selection rejection before backend or
output. Installed package bytes remained unchanged; Blender was not launched.

Exact command (run with the working directory set to the `cwd-one` path):

```text
HML_ACCEPTANCE_WORKSPACE=/Users/bormotov/work/humanmotionlib/build/add-shared-body-characters_r1_character-final-packaging_try-5_installed-acceptance HML_ACCEPTANCE_REPOSITORY=/Users/bormotov/work/humanmotionlib HML_ACCEPTANCE_ROOT=/Users/bormotov/work/humanmotionlib/build/add-shared-body-characters_r1_character-final-packaging_try-5_installed-acceptance PYTHONDONTWRITEBYTECODE=1 /Users/bormotov/work/humanmotionlib/build/add-shared-body-characters_r1_character-final-packaging_try-5_installed-acceptance/venv/bin/python /Users/bormotov/work/humanmotionlib/build/add-shared-body-characters_r1_character-final-packaging_try-5_installed-acceptance/test_character_installation.py
```

The exact source-test SHA-256 is
`846364f67fb72988e562cdc7a0300b2a00e1c1392d8e19de54622c7d675e913d`;
the run-local bootstrap SHA-256 is
`c4d27b52abd67c11711f8efa064f7f956d4609107fa8c5bc4db6b320c526307b`. Test
output is retained at
`build/add-shared-body-characters_r1_character-final-packaging_try-5_installed-acceptance/test-output.log`.

The package-check root is retained with the archive audit. The installed
acceptance root contains 1,025 regular files / 25,831,833 bytes plus four
virtualenv/cache symlinks. The tests also created five direct-child API input/render roots
under `build/` with the try5 identity. They are retained as run outputs pending
the parent cleanup pass; this acceptance task did not remove any roots or
follow symlink targets.
