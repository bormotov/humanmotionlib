# Developer hand-off

## Gate 1

The user invoked `$openspec-apply-change support-consumer-authored-motions` on 2026-10-25. This explicitly approves the proposal, both delta specifications, and design for implementation. The approved scope is an API for consumer-authored motions and a verification example whose depth is supplied by the consumer. It does not add a production exercise or prescribed amplitude.

## Baseline and build-run inventory

A clean, non-editable pre-change package environment was built in `build/support-consumer-authored-motions_r1_dev_try-1_baseline-package/environment/` with its uv cache in the same run root. `verify_runtime_integrity()` passed for package `0.2.0`, runtime manifest SHA-256 `cbe204cc4faf3ff870261795b54cf9769fdb74767ffc09e3af8768a6096fbaf2`, 42 sealed implementation modules.

Preparation succeeded in `build/support-consumer-authored-motions_r1_dev_try-1_baseline-prepare/input.json`: squat, arm-raise and neutral at BPM 90; 35 pose samples; arm-raise/squat each have 5 static and 17 animation entries, neutral has 1 and 1. Prepared content SHA-256: `dadd04b9d8e14083c26ea1b1272e73f942555eca3b820f1fde6cbc23636b3cc5`.

The first render attempt in `build/support-consumer-authored-motions_r1_dev_try-1_baseline-render/` failed only because sandbox restrictions denied the supervisor's `/bin/ps` process-group check. The receipt/logs are retained at `processes/c0a03b8baa444e0892bdd3eb453bbadb/` as diagnostic evidence. An escalated read-only process check confirmed the Blender process group had exited; no supervisor code or receipt was changed. The fresh retry succeeded in `build/support-consumer-authored-motions_r1_dev_try-2_baseline-render/` using the original sealed prepared input. Blender reported 5.2.2 LTS, build `d13f752e3b9c`; metadata reports package version `0.2.0` and runtime manifest hash `cbe204cc4faf3ff870261795b54cf9769fdb74767ffc09e3af8768a6096fbaf2`.

Baseline manifest references the expected prepared SHA-256 above and has 35 samples / 77 image records. All 77 image files exist and decode successfully with Pillow; views include front/side and the existing diagnostic extras. Timeline inventory is arm-raise and squat each 5 static / 17 animation entries, neutral 1 / 1. Preparation and rendered inputs are distinct runs, no symlinks were found in the retained run roots, and no external materials were used. Source/package identities, exact inventory, render metadata and receipts are preserved before any candidate code edits.

No code was edited before baseline capture. Retained roots: baseline package environment (reproducible pre-change runtime), prepared input (render dependency), successful baseline render (candidate comparison dependency), and failed try-1 render receipt/logs (explicitly retained sandbox-diagnostic evidence). The prior failed process group was observed absent during escalated diagnosis; `ps` could not run in the sandbox. No other cleanup is pending.

## Cleanup

- Removed paths/bytes: none.
- Retained paths: baseline package environment (required to reproduce), prepared input (required for render comparison), failed render invocation receipt/logs (unresolved cleanup diagnostic).
- Dependency/link checks: the baseline prepared input is referenced by the successful render; package environment, prepare, failed render and successful render roots are distinct. No symlinks were found in these roots. The failed attempt is retained as historical diagnostic evidence; its process group was confirmed absent by an escalated read-only check.
- Pending cleanup: none for baseline capture. The failed try-1 diagnostic root is intentionally retained for audit.

## Documentation example verification

Ran the complete `action_sweep` code block from `docs/usage.md` with the
candidate package environment. The command extracted the block beginning at
`complete_source = {`, supplied the repository as the explicit workspace, and
changed the illustrative output operand to this fresh docs-owned run:

```sh
build/support-consumer-authored-motions_r1_dev_try-1_candidate-package/environment/bin/python -c "from pathlib import Path; from humanmotionlib.api import prepare; text=Path('docs/usage.md').read_text(); start=text.index('complete_source = {'); end=text.index(chr(96)*3, start); fence=text.rfind(chr(96)*3, 0, start); block=text[fence+3:end].split(chr(10),1)[1]; block=block.replace('consumer-motion_r1_app_try-3_prepare','support-consumer-authored-motions_r1_docs_try-1_example'); ns={'Path':Path,'workspace':Path.cwd(),'prepare':prepare}; exec(block,ns); print('documented complete source prepared:',len(ns['prepared'].poses),'poses; run:',ns['prepared'].run_root)"
```

It succeeded at BPM 90 with 9 poses. The prepared file is
`build/support-consumer-authored-motions_r1_docs_try-1_example/input.json`,
SHA-256 `013b67f8b71639cc326586715c8a144d5eac2981182461ab941a524de5035679`;
its resolved source hash is
`619e3b4a5c7c6d6f644a5d3d18d314db1ba88d8e44320a51388f754f84f2a2db`.
The 2,622,408-byte input is embedded and self-contained; the original source
document was an in-memory mapping. The run contains only `input.json`, has no
symlinks, and no other change artifact referenced this path before this
record. Core dev requested retaining this run as documentation acceptance
evidence; it remains a dependency of this hand-off record. No cleanup is
pending for the docs example run.

## Consumer implementation and focused verification

The consumer API, source resolver, schemas, prepared-input sealing, host/backend integrity checks and focused tests are implemented. No built-in squat depth was added; the documented helper takes `knee_peak_deg` from the caller. Review corrections addressed license obligation profiles and attribution, ISO calendar-date validation, exact fresh base-lineage comparison, structured source/constraint details, request-class sample-budget errors, removal of an undocumented stature ceiling, and a safe example ID for fractional depth values.

Historical pre-amendment candidate try-9 was built as a non-editable package, version `0.2.0`, manifest SHA-256 `ca505f7053c81436e8f44a476c425f42233e6aab2344cb1c8d750f1cea03e43a`, 43 implementation modules and 52 resource entries. Its implementation and schema identities matched reviewed try-8; its only resource difference was the corrected `docs/usage.md` identifier. This root remains as historical evidence and is superseded by amended try-18 below.

Verification completed:

- `uv run --locked --no-sync hml validate --profile adult-reference-v1` passed: 180 structures, 67 actions, 3 placements and 32 fixtures.
- `uv run --locked --no-sync python -m unittest tests.test_build_adapter tests.test_source_schemas` passed 9 tests; packaged-resource inventory asserts both consumer schemas.
- Installed-wheel focused host-integrity test passed on code/schema-identical try-8 (1 test), covering consumer preparation/projection, stature 11, mutation independence, resealed source/resolved/effective/sample tampering, forged base lineage and missing original source files.
- The real dense coupled-between-frame test passed (1 test): delivered wrist-envelope samples are valid, while beat 0.01 violates the envelope; the API rejects with structured details before output creation. Dense samples do not enter returned timelines.
- Independent reviewer boundary probes accepted duration 0 with one sample, duration 256 at BPM 90 with 1,025 samples, and exactly 100,000 samples at BPM 0.00300004. They rejected duration 257, 100,001 samples and BPM 1e-12 before sampling/evaluation/output/process; interception spies would fail if those functions were reached. Input remained unchanged. Missing walking-constructor parameters also failed before output. This tests cardinality and pre-allocation interception without running 100,000 dense solves or rendering 100,000 frames.
- The documented complete-source example ran at BPM 90 in `build/support-consumer-authored-motions_r1_docs_try-1_example/input.json` and produced 9 poses. The fractional-depth helper correction was packaged in try-9.

Before the approved boundary amendment, reviewer render `build/support-consumer-authored-motions_r1_reviewer_try-3_render-30-a/` exited 1. Its receipt remains `processes/806fb4da3f8d426794fef35766e9ecd5/outcome.json`; the diagnostic was missing PyYAML in Blender's embedded Python when the old reader imported the consumer source verifier. That implementation was superseded by the amendment recorded below; the failed receipt remains historical evidence. The amended try-18 renderer acceptance is pending; no render integration or visual correctness is claimed.

## Candidate run cleanup

Pre-cleanup developer candidate inventories (symlinks were counted and not followed): try-1 candidate package 527 files / 18,554,286 bytes / 3 symlinks; try-2 candidate package 15 / 31,848 / 3; try-3 527 / 18,554,283 / 3; try-4 538 / 18,759,507 / 3; try-5 526 / 18,543,179 / 3; try-6 538 / 18,762,319 / 3; try-7 528 / 18,573,811 / 3; try-8 538 / 18,766,032 / 3. Empty try-1 through try-5 host-check roots contained no files. Parent confirmed no active main process uses developer try-1 through try-8. Reviewer confirmed it owns copied reviewer environments and does not depend on these paths; its active render uses only `build/support-consumer-authored-motions_r1_reviewer_try-3_verify/environment/`.

Removed whole obsolete developer roots after parent process/dependency checks and reviewer confirmation: try-1 through try-8 candidate packages (130,545,265 file bytes total; 4,237 files and 24 symlinks) and empty try-1 through try-5 host-check roots (0 bytes). Each path was a direct child of `build/`, inventoried without following symlinks, and verified absent immediately after removal. No reviewer-owned run or retained baseline/docs root was modified. Historical try-9 remains as a pre-amendment candidate.

## Approved host/backend boundary amendment

The user approved the boundary amendment recorded in the proposal/spec/design: host Python performs full consumer schema, provenance, base-lineage, resolution, dense preflight and solved-sample replay before Blender probing; Blender verifies prepared/package integrity and the exact host-validated identity using only HML and its standard library. No new format, runtime dependency, host site-packages injection, source parser, or reduced-validation fallback was introduced. Task 4.2 was reopened; 4.5–4.7 were added in the amended checklist.

Implementation split: `prepared.py` contains the dependency-free integrity core and consumer snapshot/source/resolved hashes, base-lineage resource/hash mapping, sorted sample/frame identity, and sampling-to-sample timeline checks. Host `read_prepared` delegates full source/schema/replay checks to `consumer_prepared_validation.py`. `run_blender.run` fully reads and validates persisted input before the Blender version probe, then passes its canonical `content_sha256` as private `--expected-prepared-sha256`; Blender compares this immediately after integrity read and before `input_loaded` or scene construction. The same hash is used by the receipt, script phases and output contracts.

Final amended candidate: `build/support-consumer-authored-motions_r1_dev_try-18_candidate-package/environment/`, runtime manifest SHA-256 `0937304c988678ba98ea20ccce770d024e2a996d14384ad21f44583398c2b340`, 44 implementation modules. Built with `uv sync --locked --no-editable --reinstall-package humanmotionlib --python .venv/bin/python` and the copied locked cache under that run. `hml validate --profile adult-reference-v1` passed for the installed candidate: 180 structures, 67 actions, 3 placements and 32 fixtures.

Final scoped regression command, using a fresh owned test root, passed 22 tests in 41.206 seconds:

```sh
HUMANMOTIONLIB_SOURCE_ROOT="$PWD" \
HUMANMOTIONLIB_TEST_RUN_ROOT="$PWD/build/support-consumer-authored-motions_r1_dev_try-18_candidate-tests" \
  build/support-consumer-authored-motions_r1_dev_try-18_candidate-package/environment/bin/python -m unittest \
    tests.test_consumer_motion.ConsumerMotionTests.test_backend_reader_is_dependency_isolated_and_host_identity_bound \
    tests.test_consumer_motion.ConsumerMotionTests.test_host_api_prepares_and_seals_complete_input \
    tests.test_prepared_contract tests.test_run_blender tests.test_blender_bootstrap \
    tests.test_build_adapter tests.test_source_schemas
```

The isolation test blocks imports of YAML, JSON Schema, referencing and all host source-validation adapters in a fresh Python process; a valid consumer input still reads. It rejects absent or mismatched expected identity, a resealed substitute with the former identity, and dangling timeline references. The host tamper case rejects before `inspect_blender` and creates no output. The runner test confirms forwarding the validated identity. The combined command also covers host replay/tampering, prepared contracts, Blender bootstrap, package inventory and schemas.

The 30-degree authored squat variant was prepared at BPM 90 in `build/support-consumer-authored-motions_r1_dev_try-18_candidate-prepare/input.json`, 17 samples, prepared SHA-256 `12ef9544b7568702861c446cfbe524cb449b8c81ad00aa4c55200e90bca2fc08`, under this candidate's exact manifest identity. The next supervised render command is:

```sh
build/support-consumer-authored-motions_r1_dev_try-18_candidate-package/environment/bin/hml \
  --workspace "$PWD" run-blender \
  --input build/support-consumer-authored-motions_r1_dev_try-18_candidate-prepare/input.json \
  --output build/support-consumer-authored-motions_r1_dev_try-<fresh-attempt>_candidate-render \
  --render-dir build/support-consumer-authored-motions_r1_dev_try-<fresh-attempt>_candidate-render/frames \
  --render-only
```

The output root must be a fresh five-component run with a concrete unused attempt number. The parent reports that the pinned renderer completed all eight render attempts and three identity-negative cases successfully on try-18: runs `build/support-consumer-authored-motions_r2_reviewer_try-1_render-{30,60,full,baseline}-{a,b}` and `..._identity-{missing,mismatch,substitution}`, with the run inventory in `build/support-consumer-authored-motions_r2_reviewer_try-1_verify/render-cases.json`. These belong to the reviewer and are preserved untouched. Reviewer is independently checking image/receipt inventory and metrics; tasks 4.3 and 4.7 remain open until that evidence is recorded. The try-19 parser-only change does not modify rendering behavior.

## Amended candidate cleanup

Removed obsolete dev try-10 candidate package (2,362 files / 55,308,178 bytes / 21 symlinks) and test roots try-10 through try-17 (2,523 files / 5,537 bytes / no symlinks) after parent process/dependency checks and reviewer confirmation of independent environments. Total removed: 2,523 files, 55,313,715 bytes and 21 symlink entries; each target was a direct child of `build/`, inventoried without following links, and verified absent after removal. Retained try-9 as historical pre-amendment package evidence, baseline package/input/successful-render roots, docs example, final try-18 package/test/input. No reviewer-owned run or outside-root target was followed or removed. No cleanup remains pending for these developer runs.

## Parser error detail correction (R9)

The reviewer found that duplicate or malformed YAML/JSON file inputs produced public `source-validation` errors with empty `details`. `load_consumer_document` now wraps those parser failures with `source_id` equal to the resolved source path, `field` equal to `$`, and `message` equal to the parser's original message; the original exception remains `__cause__`. No untrusted document content is parsed to derive an identifier. No resolver, schema, sampling, solved pose, backend or render code changed.

Fresh immutable package: `build/support-consumer-authored-motions_r1_dev_try-19_candidate-package/environment/`, manifest SHA-256 `4948674cfe7a5adfff7e5cfd2a909b83c1fba1199bd1dded2258ead817c09da7`, 44 implementation modules. A fresh test run passed 23 tests in 58.518 seconds:

```sh
HUMANMOTIONLIB_SOURCE_ROOT="$PWD" \
HUMANMOTIONLIB_TEST_RUN_ROOT="$PWD/build/support-consumer-authored-motions_r1_dev_try-20_candidate-tests" \
  build/support-consumer-authored-motions_r1_dev_try-19_candidate-package/environment/bin/python -m unittest \
    tests.test_consumer_motion.ConsumerMotionTests.test_parse_failures_include_source_and_root_field_details \
    tests.test_consumer_motion.ConsumerMotionTests.test_backend_reader_is_dependency_isolated_and_host_identity_bound \
    tests.test_consumer_motion.ConsumerMotionTests.test_host_api_prepares_and_seals_complete_input \
    tests.test_prepared_contract tests.test_run_blender tests.test_blender_bootstrap \
    tests.test_build_adapter tests.test_source_schemas
```

The new public-API test covers duplicate and malformed YAML and duplicate and malformed JSON, asserting `GenerationError.code == "source-validation"`, absolute-path `source_id`, root field `$`, original parser message and no output directory. Existing duplicate-safe direct loader, host tamper replay, dependency-isolated backend, prepared contract, runner/bootstrap, package resource and schema tests also passed. Installed `hml validate --profile adult-reference-v1` passed for try-19: 180 structures, 67 actions, 3 placements and 32 fixtures.

Regenerated 30-degree BPM-90 consumer input under try-19 exact package identity: `build/support-consumer-authored-motions_r1_dev_try-19_candidate-prepare/input.json`, 17 poses/samples, content SHA-256 `77d78553d8cabc64d61ea40cc8f1821344f59d6cfaa8aa0f4f1421c05b1088ac`. The earlier successful try-18 renders use their original manifest identity; this parser-only change cannot affect source resolution or rendered geometry. Reviewer still provides the required artifact/receipt inventory before tasks 4.3 and 4.7 are marked. Retained try-19 package, try-19 prepared input and try-20 passing test run. Removed the redundant empty try-19 subset test root (0 files / 0 bytes / 0 symlinks) after reviewer confirmed no dependency; verified the direct-child path was absent after cleanup.
