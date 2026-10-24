# Independent Review — package-humanmotionlib

Verdict: **FAIL (interim; corrected candidate and remaining checks pending)**.

Human visual gate: **PENDING**. No visual approval is implied.

## Candidate and scope

Initial frozen package source supplied by main; independently built direct wheel in `build/package-humanmotionlib_r1_reviewer_try-1_checks/direct/`. This attempt found regressions before expensive rendering. Developer corrections require a fresh final candidate verification.

## Findings

| ID | Severity | Requirement / scenario | Evidence | Suggested direction |
|---|---|---|---|---|
| F-1 | major | Installed commands cover supported workflow / Complete installed generation and presentation | `review_pack.py:378` rejects occupied output before reuse; reuse then requires existing output/clean-a and clean-b. Independent installed CLI `reuse-repro.log` fails occupied output. | Preserve explicit same-attempt continuation with complete preflight and integrity checks; no implicit render fallback. |
| F-2 | minor | Distribution identity and namespace are explicit / Install and identify the wheel | `tools/README.md` actively documented removed `tools/*.py` commands before appended migration section. | Update active contributor commands and distinguish historical references. |
| F-3 | major | Installed commands cover supported workflow / Use installed host commands | `hml check-environment --not-an-option` exits 0; `cli.py` discards supplied arguments. `invalid-environment-option.log`. | Preserve parser behavior and reject unknown arguments in console/module invocation. |

| F-4 | major | Invocation evidence survives failures / Identify a wheel-installed invocation | `receipt-identity-repro.json`: initial/failure receipt lacks package release, resource/manifest and implementation identity and explicit workspace; no later runtime/runner update supplies them. | Capture installed identity and selected workspace in the durable initial receipt before child launch; verify success and early failure evidence. |

| F-5 | major | CI builds and checks the distributable artifact / Check the actual wheel in CI | `.github/workflows/package.yml:71-73,144` renames the wheel to `humanmotionlib-candidate.whl`; approved uv 0.13.5 independently rejects it as missing a Python tag. `ci-wheel-filename-repro.log`. | Preserve the valid wheel basename for installation and artifact identity. |
| F-6 | minor | CI builds and checks the distributable artifact / Check the actual wheel in CI | Numeric installed-test loop executes from checkout after external-cwd subshell ends; uploaded evidence excludes generated import/resource identity JSON and before/after package SHA inventories. | Run installed smoke scope from explicit external cwd and retain its small identity/resource/write-audit evidence. |

## Requirement and scenario checklist

A = automatable check; N = numeric metric; H = human visual judgement. Status is pending unless evidence is stated below.

### backend-execution
- [A] Routine backend work has one controlled execution path — pending final verification.
  - [A] Inspect and build with the pinned backend — pending final verification.
  - [A] Keep presentation-only work independent of Blender — pending final verification.
  - [A] Launch an installed backend without the checkout — pending final verification.
- [A] Checkout-owned backend work does not overlap — pending final verification.
  - [A] Contend for a running backend — pending final verification.
  - [A] Recover ownership after supervisor death — pending final verification.
  - [A] Share ownership across installed callers — pending final verification.
- [A] Invocation evidence survives failures — pending final verification.
  - [A] Diagnose a native failure before the script starts — pending final verification.
  - [A] Distinguish script execution and process shutdown — pending final verification.
  - [A] Identify a wheel-installed invocation — pending final verification.

### build-artifact-lifecycle
- [A] Run identity is encoded in a flat directory name — pending final verification.
  - [A] Allocate an identifiable review attempt — pending final verification.
  - [A] Reject ambiguous or nested run identity before writing — pending final verification.
  - [A] Allocate an installed-workflow run — pending final verification.

### host-python-runtime
- [A] Locked host dependencies reproduce a usable environment — pending final verification.
  - [A] Recreate the host environment from the committed lock — pending final verification.
  - [A] Install complete runtime dependencies from the wheel — pending final verification.

### python-distribution
- [A] Distribution identity and namespace are explicit — pending final verification.
  - [A] Install and identify the wheel — pending final verification.
- [A] Supported generation resources are complete — pending final verification.
  - [A] Audit both distribution resource closures — pending final verification.
  - [A] Reject an incomplete or altered installation — pending final verification.
- [A] Installed commands cover the supported workflow — pending final verification.
  - [A] Use installed host commands — pending final verification.
  - [A] Complete installed generation and presentation — pending final verification.
- [A] Installed resources are independent of writable workspaces — pending final verification.
  - [A] Generate with a read-only installation — pending final verification.
- [A] Runtime integrity uses distribution-owned identity — pending final verification.
  - [A] Verify and reject prepared identities — pending final verification.
- [A] Distribution licenses and provenance are complete — pending final verification.
  - [A] Audit commercial redistribution and output attribution — pending final verification.
- [A] CI builds and checks the distributable artifact — pending final verification.
  - [A] Check the actual wheel in CI — pending final verification.
- [A] Packaging preserves generation output — pending final verification.
  - [N + H] Compare the package regression pack — pending final verification.

## Independently reproduced results

- Direct wheel and sdist build succeeded using approved uv 0.13.5, setuptools 83.0.0, CPython 3.14.6. Sandbox DNS failure required an approved escalated build.
- Exact canonical resource closure: 50 resources and 40 implementation files checked by SHA-256; all 32 diagnostics and seven schemas included. Wheel inventory retained in `wheel-inventory.json`.
- Extracted-sdist wheel built offline, independently of Git/checkout authoring directories; 92 logical package files match byte-for-byte (`parity.json`).
- Fresh locked non-editable contributor installation succeeded. Complete host suite: 168 tests in 190.701 seconds, OK, zero skipped; only the two documented real-backend modules excluded. Tests changed during this preliminary run; final candidate revalidation remains required.
- Fresh direct-wheel runtime install succeeded without contributor lock. External-cwd source validation covers 32 fixtures; default preparation covers all 32 fixtures/900 samples. Read-only installation has 92 unchanged files, relocated package prepares identical canonical identities, corrupted `rig/body-groups.yaml` fails before process launch (`integrity-and-readonly.json`).
- Primary exact-version setuptools and referencing license URLs independently inspected; both grant commercial modification/distribution under MIT conditions. Advisory confirms patched setuptools 83.0.0. Pinned checkout/setup-python/upload-artifact action license URLs independently confirm MIT; setup-uv retrieval at exact SHA pending. Provenance validators passed; complete generated attribution audit pending.

- Baseline identity independently verified against commit `b9dc38d74b60e839e41446a1e08264f5153cb34c`: 83 source/code hashes; 44 canonical rig/schema/scene files unchanged. Focused prepared 31 samples, sampling, units and primary BPM exactly equal baseline (`baseline-identity.json`, `prepared-baseline-parity.json`).

## Not yet verified

Corrected final candidate, real pinned Blender build, two clean render passes, baseline decoded pixels/geometry, exact visual pack, all installed negative/isolation checks, actual successful candidate CI and explicit human gate are pending.

## Cleanup and retained dependencies

- Removed: none (0 bytes).
- Retained: reviewer try-1 checks root for active checks and F-1/F-2/F-3 diagnostics; revisit after corrections are independently verified.
- Retained: reviewer try-1 build/pack roots, currently empty and reserved for the authorized review.
- No developer, historical or other reviewer runs modified.
- Dependency/link cleanup audit pending final pack; no cleanup completion claimed.
