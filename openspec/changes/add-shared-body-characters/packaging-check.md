# Developer packaging check

## Scope and source snapshot

This report verifies task 6.1's direct wheel, source distribution and rebuilt
wheel resource closure. The source snapshot was captured before building and
recomputed after all package comparisons. Both inventories contain 117 files
and have SHA-256 `b8e30eb0c5a23b75b55d65d202673a62669535d3f2ec015e360eb6d6327bb467`.
The snapshot includes packaging configuration/backend, every package Python
module, canonical character YAML, schema resources, packaged documentation,
and the existing rig/profile/diagnostic source closure. The before and after
file inventories are retained in
`build/add-shared-body-characters_r1_dev_try-13_package-check/`.

## Reproducible commands

The pinned setuptools 83.0.0 distribution was already present in the local uv
archive. The build ran offline, without build isolation or network access, and
used a fresh owned package-check root:

```sh
UV_CACHE_DIR="$PWD/build/add-shared-body-characters_r1_dev_try-13_package-check/uv-cache" \
PYTHONPATH="/Users/bormotov/.cache/uv/archive-v0/7t1dWiC--kLpoh4q" \
SETUPTOOLS_USE_DISTUTILS=local \
uv build --python "$PWD/.venv/bin/python" --offline --no-build-isolation \
  --wheel --sdist \
  --out-dir "$PWD/build/add-shared-body-characters_r1_dev_try-13_package-check/direct"

UV_CACHE_DIR="$PWD/build/add-shared-body-characters_r1_dev_try-13_package-check/uv-cache" \
PYTHONPATH="/Users/bormotov/.cache/uv/archive-v0/7t1dWiC--kLpoh4q" \
SETUPTOOLS_USE_DISTUTILS=local \
uv build --python "$PWD/.venv/bin/python" --offline --no-build-isolation \
  --wheel \
  --out-dir "$PWD/build/add-shared-body-characters_r1_dev_try-13_package-check/rebuilt" \
  "$PWD/build/add-shared-body-characters_r1_dev_try-13_package-check/direct/humanmotionlib-0.3.0.tar.gz"
```

The direct wheel, sdist, and rebuilt wheel are at:

- `build/add-shared-body-characters_r1_dev_try-13_package-check/direct/humanmotionlib-0.3.0-py3-none-any.whl`
- `build/add-shared-body-characters_r1_dev_try-13_package-check/direct/humanmotionlib-0.3.0.tar.gz`
- `build/add-shared-body-characters_r1_dev_try-13_package-check/rebuilt/humanmotionlib-0.3.0-py3-none-any.whl`

## Results

An independent archive audit compared every logical `humanmotionlib/` file in
the wheel and sdist, verified every resource hash against the runtime manifest,
and matched all manifest resources to canonical source bytes. The rebuilt wheel
and the independently produced try-11 candidate wheel had the same logical
package tree as the direct wheel. Wheel archive SHA-256 values differ because
container metadata is not required to be byte-identical.

| Artifact | SHA-256 | Package files |
|---|---|---:|
| Direct wheel | `a04b5ef68382469d2785b7df6e4fb65116f510fc6e1be6ee94006f89bb2cb8cb` | 115 |
| Source distribution | `f64e023a620929fbfd490742200558ef3db4cb787ce7a95540b294d621dac271` | 115 |
| Wheel rebuilt from sdist | `6d0db0954e170ae840c4ac8975bac08263b83c2f04d65d30cea6c417f8638be6` | 115 |
| Independently installed try-11 candidate wheel | `1a4b4a64673de99704c2480c3d256edaa23fe5dd7e96da46e8e19c4af9196e5e` | 115 |

The runtime manifest closes over 64 resources and 49 Python implementation
modules. It includes all seven canonical character YAML files, all four
`character-*.schema.json` files, `docs/character-models.md` and
`docs/usage.md`. Direct wheel, sdist and rebuilt wheel agree on each resource
and implementation byte. Source resource hashes match the current authored
files. No mesh or animation binaries are packaged and there are no runtime
asset downloads. The exact machine-readable result is
`build/add-shared-body-characters_r1_dev_try-13_package-check/packaging-audit.json`.

## Cleanup

This run is retained for the developer handoff and independent review as the
task 6.1 artifact dependency closure: 14 files / 918,475 bytes, zero symlinks.
The separate preliminary try-1 package unit-test root held only uv cache
metadata and empty test case directories. Its 1,764 regular-file bytes were
removed after confirming there were no symlinks or dependent outputs; the root
is absent after cleanup. The try-8 package output is preliminary because it
predates the final `character_paths.py` snapshot; try-11's installed candidate
is retained by the parent for native checks. This report does not replace
installed API acceptance, native rendering, or visual review.

## Final candidate package closure (try142)

After the final implementation snapshot was built as candidate try142, a fresh
offline direct wheel, sdist and wheel rebuilt from that sdist were produced in
`build/add-shared-body-characters_r1_dev_try-143_package-check/` with cached
`setuptools==83.0.0`, `--offline` and `--no-build-isolation`. The audit script
`audit.py` compares the exact `humanmotionlib/` file sets and bytes in all three
archives, compares the direct wheel to the installed-candidate try142 wheel,
checks every implementation/resource/backend-contract digest in
`runtime-manifest.json`, verifies every manifest resource against the current
canonical source bytes, and rejects generated mesh/clip resources.

| Artifact | SHA-256 | Logical package files |
|---|---|---:|
| Direct wheel | `cf1c3dbdfc69b068e4bca7da55d2bd6abe09e9906c10b504b35dba713c346d63` | 116 |
| Source distribution | `c0ffd1c3e3c3c2b96bf60d0c47b2c5e746af65ddf822b5626a2e32c9572db822` | 116 |
| Wheel rebuilt from sdist | `cec650688ca138076bf2c82a2a53e5247a6f89a00d31d09b5b2398d44523bcd0` | 116 |
| Candidate try142 wheel | `54f0820a4e9a38069eaabfc87da6d08f8237e5ee065a314f22957ab663fc6611` | 116 |

All four wheels have identical logical package contents. The current runtime
manifest SHA-256 is
`e0e502871751ca42cced0976c7a73727fea708920ff5dc2cbba5709bb1c08aa7`; it
closes over 50 Python implementation modules and 64 canonical runtime
resources. Direct wheel, sdist and rebuilt wheel have the same resource and
implementation bytes. No generated character mesh/clip binary or runtime
asset download is present. The complete machine-readable result is
`build/add-shared-body-characters_r1_dev_try-143_package-check/packaging-audit.json`.

This fresh build root is retained for developer/reviewer reproducibility: 13
files / 977,425 bytes, zero symlinks. The unrelated-cwd acceptance-workspace
root created by the harness was empty and removed; no linked paths were
followed. A first acceptance invocation was corrected after its test process
was launched from the repository root instead of the decoy cwd; it did not
expose a product failure and its obsolete whole run root was removed after
inventory. The successful clean install is reported separately in
`installation-check.md`.

## Final baseline-join candidate package closure (try164)

After the review-pack exact-beat baseline join fix, fresh offline direct wheel,
sdist and rebuilt wheel were produced in
`build/add-shared-body-characters_r1_character-final-packaging_try-2_package-check/`
using cached `setuptools==83.0.0`, `--offline` and `--no-build-isolation`.
The run-local audit checks all logical archive files/bytes, equality to the
try164 candidate wheel, runtime-manifest resource and implementation hashes,
canonical resource bytes, and absence of generated mesh/clip resources.

| Artifact | SHA-256 | Logical package files |
|---|---|---:|
| Direct wheel | `6716ba186cb305ec5a8067b817723b87383f1d05f6b7f23b788c2a6a5b7ac3a0` | 116 |
| Source distribution | `dddedb9141477e9352448fddbf0d05326e860218cbf60c0f6f2f52b16f80aff2` | 116 |
| Wheel rebuilt from sdist | `df7c9c99091cf965259b6af699a0d76ed88f3982fbc81c66cfe260085a301c36` | 116 |
| Candidate try164 wheel | `fe1b4c14c9e8b42be49887c8e741f29159d5d9170f5f068c3e11ea64f4133a6f` | 116 |

All four artifacts have identical logical package bytes. The try164 runtime
manifest SHA-256 is
`40ed6c7832e58936f2e545e979216324158641fcd29522dc82a581b3eb4a11bb`; it
closes over 50 implementation modules and 64 runtime resources. The direct
wheel, sdist and rebuilt wheel match all canonical resources, including the
fixed-scene source and character documents. No generated mesh/clip binaries or
runtime asset downloads are present. The machine-readable result is
`build/add-shared-body-characters_r1_character-final-packaging_try-2_package-check/packaging-audit.json`.

This packaging result applies to try164 only. At that point, the seven-test
installed acceptance still referred to try142. The later try168 packaging and
installed acceptance are recorded below and in `installation-check.md`.

## Final Path/string baseline-join candidate closure (try168)

The candidate after the follow-up review-pack baseline path/string resolution
was rebuilt and audited in a fresh run at
`build/add-shared-body-characters_r1_character-final-packaging_try-3_package-check/`.
The build used cached `setuptools==83.0.0`, offline and without build
isolation. The local audit checked exact logical archive bytes, candidate
wheel parity, all runtime manifest hashes, canonical resources and absence of
generated mesh/clip binaries.

| Artifact | SHA-256 | Logical package files |
|---|---|---:|
| Direct wheel | `b5bd3e1209412f4eb46115175841cdea8d9c6284a179736671bb1c51021a0c1b` | 116 |
| Source distribution | `bbf650a237a0e68eaac88d7cf0125651113d7922b8e3dfd83f78b487dc498555` | 116 |
| Wheel rebuilt from sdist | `1c2d862643291bcd7234a11664089399663628139161c8756ef78f5c3444117e` | 116 |
| Candidate try168 wheel | `b702c7bf928280245271f72d521bfdc5e519feb32f1a193346d93deb7cd4001b` | 116 |

All four artifacts have identical logical package bytes. Runtime manifest
SHA-256 `b457ec11b1dec544dc0a6b89d8c71b04c58721bf1ab890a371b27d3cc05c5dfb`
closes over 50 implementation modules and 64 resources. Source resource hashes
match the packaged canonical bytes, and the package contains no generated
mesh/clip binaries or runtime asset downloads. See
`build/add-shared-body-characters_r1_character-final-packaging_try-3_package-check/packaging-audit.json`
for the full result.

The fresh package-check run is retained as review evidence: 13 files,
983,846 regular-file bytes, zero symlinks. This closure audit and the
try168-specific installed test slice in `installation-check.md` precede the
later review-pack visual work; any subsequent production-code candidate needs
its own identity-bound recheck.

## Final managed-pass candidate package closure (try177)

After the managed-pass claim fix, the frozen try177 candidate was rebuilt and
audited from a fresh package-check root at
`build/add-shared-body-characters_r1_character-final-packaging_try-5_package-check/`.
The build used cached `setuptools==83.0.0`, offline and without build
isolation. The direct wheel, source distribution, and wheel rebuilt from that
sdist were checked against the exact try177 candidate wheel. The audit checks
logical file inventories and bytes across all archives, runtime-manifest
implementation/resource/backend-contract digests, canonical source-resource
bytes, and absence of generated mesh/clip resources.

| Artifact | SHA-256 | Logical package files |
|---|---|---:|
| Direct wheel | `10f4459aceee759c538d3c83421baee0d554b7949ce4e31c2a7d4d0525beeab3` | 116 |
| Source distribution | `ad34507570aa469f6afe5114684be4427cd8c76fdb6864e8b249207d43a0b1c0` | 116 |
| Wheel rebuilt from sdist | `601e3161f555e94028c36a5cf910c09689830477d4c14ace363536876163cfaf` | 116 |
| Candidate try177 wheel | `bf42f87b0ebad22a7c1da01666299aa7874eecf7eed56f6e0ae4a35da131ddb8` | 116 |

All four artifacts have identical logical package bytes. The candidate runtime
manifest SHA-256 is
`06d2fed42a7e798bebc1d5b92d74fd10a1f10340c0ff1308fc77bee53da795c4`; it
closes over 50 implementation modules and 64 resources. Direct wheel, sdist,
and rebuilt wheel agree with canonical resource bytes. The candidate and fresh
direct wheel declare the same four runtime dependencies already present in
the previous candidate: PyYAML, jsonschema, Pillow, and referencing. No
generated mesh/clip binaries or runtime asset downloads are present. The exact
machine result is
`build/add-shared-body-characters_r1_character-final-packaging_try-5_package-check/packaging-audit.json`.

The retained package-check root contains 14 files / 989,769 bytes and no
symlinks. The build emitted setuptools' existing warning that no README file
is present in the sdist; archive closure and logical-byte checks passed.

## Frozen try206 developer package closure

To bind developer task 7.1 to the frozen try206 wheel, an offline direct wheel
and sdist were built from the frozen source snapshot in
`build/add-shared-body-characters_r1_dev_try-241_package-check/`; the wheel
was rebuilt from that sdist. The audit compared all 116 logical package files
against the exact try206 candidate, checked runtime-manifest implementation,
resource and backend-contract hashes against source bytes, and rejected
generated mesh/clip resources.

| Artifact | SHA-256 | Logical package files |
|---|---|---:|
| Direct wheel | `a45ade8bbaab33373270e3b4bbc32ac7a7ee3185b3c0bfb98ddb3d0d0b63579d` | 116 |
| Source distribution | `e459ccacfdee8bed5c9110d8532df090523639409b63aec45e81afa389ea61b2` | 116 |
| Wheel rebuilt from sdist | `60e0c13202862244a00d2abb7d37c9d8b3995fab8e47d9d2c0ed4632a8174224` | 116 |
| Frozen try206 candidate | `6f2389268cf59ee29e71bec00b659100483e199dd7a3ac520adb6806714a215f` | 116 |

All four archives have identical logical package bytes. Runtime-manifest
SHA-256 is
`739c6f975d2e7f04fb05dbfd2a6984a1d86667d96ab587697ec397bae7836573` and
closes over 50 implementation modules and 64 resources. Canonical source
resources match the wheel; no generated mesh/clip resource or runtime asset
download is present. Machine-readable result: `packaging-audit.json`.
The command was `uv --cache-dir build/add-shared-body-characters_r1_dev_try-241_package-check/uv-cache build --python .venv/bin/python --offline --no-build-isolation --wheel --sdist --out-dir build/add-shared-body-characters_r1_dev_try-241_package-check/direct`, followed by the same command with `--wheel --out-dir .../rebuilt <direct-sdist>` and `python3 .../audit.py`.
