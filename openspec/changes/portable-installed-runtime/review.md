# Independent review

Verdict: PASS WITH NOTES. All required automated acceptance and cleanup checks pass. Human visual Gate 2 was accepted on 2026-10-24. The change is ready for OpenSpec finalization.

## Immutable identity and scope

Production source: `65a1b91e682d4094c7339adc43ab99d0f1c3477a`. Exact wheel SHA-256: `6171a6ea8e833095dcf0246a9eb0447b1aae422fdbc49c001d776e64454d227a`. Test-only follow-up: `adc0c3ebb59cf287f7488ff8ac670b8add6819d8`; independent Git diff confirms only `tests/test_runtime_workspace.py` changed, with identical production code/resources and wheel. Clean source came from immutable Git archives, not the developer working tree.

Reviewer-owned external run (`R`): `/private/tmp/hml-portable-review-65a1b91/build/portable-installed-runtime_65a1b91_reviewer_try-1_acceptance/`. Disposable source/install/caller workspaces are test content inside this one owning run, per design section 5. Every independent workflow output remains a fresh direct child of its selected fixture workspace's build directory. `/AGENTS.md` is absent; repository `AGENTS.md` was read. No Blender GUI/MCP state was used, and no project implementation, schema, YAML or spec was edited.

Local interpreter: CPython 3.14.6; uv 0.11.21; pinned build backend setuptools 83.0.0. Native backend: Blender 5.2.2 LTS, build d13f752e3b9c, Darwin-arm64; MPFB/Rigify unused. All package-controlled rendering comes from the exact non-editable read-only installation.

## Findings and resolution

No unresolved production-code finding remains. R1–R4 are resolved and independently rechecked; actual final-commit CI artifacts and cleanup are verified below.

| ID | Severity when found | Requirement/scenario | Evidence and current status | Suggested direction |
|---|---|---|---|---|
| R1 | blocker | Apply the same workspace contract to every writer / Validate destinations before creating filesystem state | Superseded c3e9007 report/shard owner mismatch. Resolved: actual full public verifier writes the complete 199883-metric summary and 31 shards; only the intentional subset coverage diagnostic fails. `R/full-numeric-command.json`, `R/independent-numeric-timing-audit.json`. | Completed owner/path separation; retain regression coverage. |
| R2 | blocker | Complete installed generation and presentation / internal clean-a/clean-b operations | Superseded c3e9007 rejects nested managed passes. Resolved: actual installed public normal pack runs both passes; 6 success receipts, 165 output hashes rechecked, 76 exact RGBA comparisons, public reuse preserves all 259 pack files. `R/real-backend-receipt-audit.json`, `R/reuse-independent-audit.json`. | Completed explicit owner/operation binding across host and embedded preflight; retain strict reuse inventory. |
| R3 | major | Generate with a read-only installation / Prove the installed artifact has no checkout dependency | Superseded copied-tamper fixture permission failure. Resolved: independent complete read-only installed harness passes; 92 original package files remain byte-identical. `R/installed-acceptance.json`. | Only disposable tamper copies become mutable; original installation stays read-only. |
| R4 | minor | Complete host suite / external owned fixture isolation | Initial 189-test run has one assertion failure: correct escaping-path rejection says `nested run identity` instead of expected `outside build` because TMPDIR has a valid outer run ancestor. Test-only adc0c3e accepts both diagnostic forms and preserves sentinel/no-output assertions. Fresh full suite: 189/189 pass, skips 0, 92.812 s. `R/host-suite.log:209`, `R/host-suite-followup.log`, `R/test-only-followup-identity.json`. | Resolved without weakening runtime rejection or changing the wheel. |

## Requirement and scenario checklist

A = automatable check; N = numeric metric; H = human judgement. Each exact delta requirement/scenario appears once. Evidence filenames below are relative to `R`; full commands, cwd, return codes and elapsed times are retained as `*-command.json` and logs.


### backend-execution

- [x] [A] **Requirement: Routine backend work has one controlled execution path** — real-backend-receipt-audit.json: 6 successful probe/build/render receipts; public normal pack and reuse.

- [x] [A] **Scenario: Inspect and build with the pinned backend** — real-backend-receipt-audit.json; independent-numeric-timing-audit.json: Blender 5.2.2 LTS / d13f752e3b9c, Darwin-arm64.

- [x] [A] **Scenario: Keep presentation-only work independent of Blender** — reuse-independent-audit.json; html-independent-audit.json: sentinel Blender never called.

- [x] [A] **Scenario: Launch an installed backend without the checkout** — focused-build-command.json; six receipts use installed site-packages backend script; installed-before/after inventories unchanged.

- [x] [A] **Scenario: Keep backend working state in the caller workspace** — real-backend-receipt-audit.json: correct resolved workspace/owner/operation, 165 fresh output hashes, receipt-local scratch removed after child exit.

- [x] [A] **Requirement: Checkout-owned backend work does not overlap** — installed-supervision-matrix.json plus host-suite-followup.log: alias serialization, separate domains, bounded waits/cancellation/orphan tests.

- [x] [A] **Scenario: Contend for a running backend** — installed-supervision-matrix.json: same-domain child intervals separated by 99.271 ms; full host bounded-wait and contention scenarios pass.

- [x] [A] **Scenario: Recover ownership after supervisor death** — host-suite-followup.log: actual process-visible abandoned-owner, unrelated-PID, orphan and cleanup tests pass; no sandbox result substituted.

- [x] [A] **Scenario: Share ownership across installed callers** — installed-supervision-matrix.json: two physically separate non-editable installs; shared alias resolves to the same persistent lock domain.

- [x] [A] **Scenario: Ignore invocation and installation location for lock ownership** — installed-supervision-matrix.json: two readonly cwd values; same domain no overlap, separate domains overlap 654.684 ms.

- [x] [A] **Requirement: Invocation evidence survives failures** — host-suite-followup.log: native-like nonzero exit, phase/shutdown distinction, cancellation, timeout, initial/final receipt checks pass.

- [x] [A] **Scenario: Diagnose a native failure before the script starts** — host-suite-followup.log: controlled native-like exit has raw status, captured logs and unknown phase; no deliberate real Blender crash.

- [x] [A] **Scenario: Distinguish script execution and process shutdown** — host-suite-followup.log: completion marker and process-exit assertions; real-backend-receipt-audit.json: script_complete plus exit 0.

- [x] [A] **Scenario: Identify a wheel-installed invocation** — real-backend-receipt-audit.json; focused input/build/render identities agree with exact installed wheel inventory and prepared hash.

- [x] [A] **Scenario: Identify explicit workspace ownership after an external invocation** — real-backend-receipt-audit.json; installed-supervision-matrix.json; failure receipt tests in host-suite-followup.log.


### build-artifact-lifecycle

- [x] [A] **Requirement: Run identity is encoded in a flat directory name** — identity.json; all new independent workflow roots are five-component direct children of their selected fixture workspace/build.

- [x] [A] **Scenario: Allocate an identifiable review attempt** — identity.json; caller-workspace/build public workflow roots; host run-root validator tests.

- [x] [A] **Scenario: Reject ambiguous or nested run identity before writing** — direct-api-preflight-audit.json; installed-acceptance.json; full host negative managed-pass/nested/occupied/escaping-path tests.

- [x] [A] **Scenario: Allocate an installed-workflow run** — installed-acceptance.json; direct-api-preflight-audit.json; normal-pack-command.json: package unchanged, separate flat owned outputs.

- [x] [A] **Scenario: Validate destinations before creating filesystem state** — 27 direct API missing/empty/relative-workspace cases; installed traversal/symlink negatives; fresh full-report/shard and managed-pass tests.

- [x] [A] **Scenario: Read protected predecessors without lexical checkout inference** — html-independent-audit.json; independent-html-link-audit.json; full host no-build/misleading-build synthetic cases. Real legacy input remains in place.


### python-distribution

- [x] [A] **Requirement: Installed commands cover the supported workflow** — installed-acceptance.json; public real build/normal pack/reuse/full numeric and real HTML-only commands; direct-api-preflight-audit.json.

- [x] [A] **Scenario: Use installed host commands** — installed-acceptance.json: console/module/direct prepare, help/version/environment/validate, 32-fixture validation and 900 samples.

- [x] [A] **Scenario: Complete installed generation and presentation** — public pinned build + two clean render passes + full numeric writer + reuse + real HTML-only; labeled full-fixture host versus focused native scopes.

- [x] [A] **Scenario: Apply the same workspace contract to every writer** — direct-api-preflight-audit.json: 27 invalid direct API cases allocate nothing; pure preparation needs no workspace. Existing CLI/module and writer-path suites pass.

- [x] [A] **Requirement: Installed resources are independent of writable workspaces** — installed-before.json = installed-after.json (92 files); real-backend-receipt-audit.json; relocation-independent-audit.json.

- [x] [A] **Scenario: Generate with a read-only installation** — installed-acceptance.json; actual readonly installed backend; 92 package files unchanged after host, numeric, native and presentation workflows.

- [x] [A] **Scenario: Invoke the same pipeline from unrelated directories** — installed-acceptance.json two cwd; relocation-independent-audit.json two installs/workspaces with chmod-0555 cwd; installed-supervision-matrix.json two readonly cwd values.

- [x] [A] **Requirement: Runtime integrity uses distribution-owned identity** — independent-build-comparison.json; all-wheel-file-inventory.json; relocation-independent-audit.json; resource/implementation/prepared/reuse negatives.

- [x] [A] **Scenario: Verify and reject prepared identities** — relocation-independent-audit.json: 900 prepared samples, 136911495 bytes exactly equal across installs/workspaces; tamper failures retained.

- [x] [A] **Scenario: Preserve fail-closed integrity outside the checkout** — installed-acceptance.json: missing resource, altered implementation, tampered prepared content, incomplete reuse, traversal and escaping symlink reject with unchanged sentinels/install.

- [x] [A] **Requirement: CI builds and checks the distributable artifact** — ci-final-artifact-audit.json and artifacts/ci-runs.json: final adc0c3e package/host workflows succeed; actual checked artifact retained and audited.

- [x] [A] **Scenario: Check the actual wheel in CI** — ci-final-artifact-audit.json: final CI wheel checksum bound to official summary, all 100 logical files exactly match the independently source/sdist-built and native-tested package; actual CI install/parity checks pass.

- [x] [A] **Scenario: Prove the installed artifact has no checkout dependency** — actual final CI installed-acceptance.json passes from external caller paths: 900 samples, readonly 92-file package, integrity/path negatives, scoped synthetic presentation; ci-final-artifact-audit.json.


### Quality gates and measured bounds

| Gate | Type | Independent result and tolerance |
|---|---|---|
| Canonical/schema/rig identity | A | All-fixture validation: 32 fixtures, 180 structures, 67 actions, 3 placements; 900 prepared samples. All 44 canonical YAML/schema files exactly match the pre-change wheel. Clean wheel and sdist rebuild exactly match all 100 logical wheel files (92 runtime package files plus distribution metadata/licenses); namespace leaks 0. |
| Native evaluated regression | N | All 31 focused evaluated sample dictionaries exactly equal the protected baseline, including body frames, geometry, attachments, mass points, scene and root evidence. |
| Numeric report scope | N | 199883 total metrics; all 31 sample reports pass. Root checks: 1288/1289 pass. The sole expected failure is `diagnostic_fixture_coverage`: measured 29, expected 0, tolerance 0 because this deliberately renders only neutral/rest/arm-raise. This report is not called an overall numeric PASS or renewed anatomical acceptance. |
| Timing | N | At 60/120/180 BPM: 5/3/3 intervals per beat, 21/13/13 animation PNG samples, five static counts; exact steps 200/166.667/111.111 ms. Six decoded GIFs have maximum frame intervals 200/170/120 ms, loop-duration error at most 3.333 ms against 10 ms tolerance; duplicated terminal PNG count is coalesced with GIF loop start. |
| Scene/root stability | N | All 31 scene records exactly equal; outside the conservative fixed character exclusion [200,200,824,900], front/side background and floor-band channel difference is 0 (tolerance 0). Root position residual 0 m <=0.00017 m; rotation residual 0 degrees <=0.1 degree. |
| Contacts/floor | N | 186 sliding checks: max 0 m <=0.0017 m. 186 target checks: max 3.371748e-9 m <=0.0017 m. 11160 floor checks: minimum geometry height 0 m >=-0.00017 m. |
| Loop closure | N | 528 origin checks: max 0 m <=0.00017 m. 528 rotation checks: max 0.0143961 degree <=0.1 degree. |
| Mirror/direction | N | 2263 paired native L/R frames: reflected-origin error 0 m <=0.00017 m; rotation matrix element error 0 <=1e-6. Measured shoulder elevation at counts 0/1/2/3/4 is approximately 0/80/160/80/0 degrees; all 29 union samples have the intended monotonic half-cycle direction, tolerance 0.1 degree. No new circular via-based motion is introduced. |
| Determinism/baseline pixels | N | All 76 view images: exact decoded RGBA equality across two clean passes and against protected baseline; max channel error 0, tolerance 0. Baseline 259-file inventory and build metadata independently rehashed unchanged. |
| Ownership/supervision | A/N | Six successful real receipts bind workspace/owner/operation correctly; 165 fresh output file hashes rechecked. Scratch is receipt-local and removed only after child exit; no pack/pass-root scratch. Two installed callers + alias: no child overlap, gap 99.271 ms. Distinct domains: simultaneous overlap 654.684 ms. Timeout/cancellation/orphan/phase failure tests pass with real process visibility. |
| Bake round trip | A | Not a changed capability: no bake/export entry point or format is introduced or modified. Source-to-native evaluated frame/geometry identity is reproduced; no new GLB/VRMA/BVH round-trip claim is made. |
| Licensing/provenance/scope | A | `licensing-scope-audit.json`: 36 canonical provenance records, 13 registered material IDs; specific cleared portions, commercial derivative permission and attribution remain in the unchanged register/notices. No new dependency, action, external reference, mesh/image/video source, convention or canonical anatomy change. Notices remain packaged and in output attribution. |

Detailed evidence: `independent-numeric-timing-audit.json`, `independent-mirror-audit.json`, `independent-direction-audit.json`, `visual-pack/independent-comparison.json`, `real-backend-receipt-audit.json`, `installed-supervision-matrix.json`, `all-wheel-file-inventory.json`.

## Installed isolation and real predecessor

The independent external copied harness passes in 80.612 s: readonly 92-file installation unchanged, two unrelated cwd values, console/module/direct preparation, all 900 samples, host numeric transforms, and six missing/corrupt/prepared/reuse/path negatives. `installed-before.json`, `installed-after.json`, `installed-acceptance.json`.

A second physically independent non-editable installation and separate workspace, invoked from chmod-0555 cwd, produces byte-identical all-fixture preparation: 136911495 bytes; SHA-256 `103c22fca2817bc7d227b083b3df08c55506979c74641a5b1ba09924a4cc3a3a`; canonical content hash `8802bed3d892678efef67f227717b1a0bf651699c22b5510a416097b0b864a50`. `relocation-independent-audit.json`. Nine direct writer/API boundaries reject each of missing, empty and relative workspace selection before any lock/receipt/output allocation (27 cases); pure in-memory preparation remains usable without workspace. `direct-api-preflight-audit.json`.

Actual protected predecessor remains unmodified at `/Users/bormotov/work/humanmotionlib/build/review/anatomical-human-skeleton/squat-r3-final/independent/retention-fix/`. HTML-only derivative: `R/caller-workspace/build/portable-installed-runtime_65a1b91_reviewer_try-1_html/index.html`. All 4437 input media/evidence inventory hashes remain unchanged; 33 pages and 2553 copied local visual assets pass project checks. Independent stdlib HTML parsing checks 3910 local href/src occurrences, 2594 unique targets and 204 inline visuals: broken links 0, escaping/symlinked local assets 0. Sentinel Blender executable is never called. `html-independent-audit.json`, `independent-html-link-audit.json`. Historical numeric verdict is not extended. Controlled no-build/misleading-build inputs are separate host synthetic fixtures; the real protected legacy input is not relocated.

## Actual CI evidence

Final source/test commit `adc0c3ebb59cf287f7488ff8ac670b8add6819d8`: [package CI](https://github.com/bormotov/humanmotionlib/actions/runs/40090969803) and [Host Python CI](https://github.com/bormotov/humanmotionlib/actions/runs/40090969813) both succeed. Actual downloaded final artifacts are copied into `R/artifacts/ci-final-adc/`; authorized run metadata is retained in `R/artifacts/ci-runs.json`. The independent available GitHub connector returned 404, so artifacts/status were obtained through the root's authorized GitHub channel, then independently audited from their bytes; this access limitation is recorded, not interpreted as CI failure.

Final CI wheel SHA-256: `6d7aa0632932bd9b8b9f889afb88962be421ce82b8aee6be731bbdbee53c8866`. All 100 logical wheel files exactly match the local `6171a6ea...54d227a` wheel used for native acceptance and both independent source/sdist rebuilds. The ZIP containers have different timestamps/checksums; their complete runtime, distribution metadata and license bytes are identical. The official artifact summary binds final commit, workflow run, checked wheel checksum, direct/sdist parity and successful installed checks. Copied CI harness matches immutable source; package before/after hashes are identical; all 900 samples and 32-fixture source counts pass. CI used Python 3.14.8 and uv 0.13.5, and explicitly labels real Blender unexecuted and package publication not performed. `R/ci-final-artifact-audit.json`.

The earlier production-source `65a1b91` [package](https://github.com/bormotov/humanmotionlib/actions/runs/40088969790) and [Host Python](https://github.com/bormotov/humanmotionlib/actions/runs/40088969810) runs also succeed. Its actual checked wheel SHA-256 `b5c6b0d48a87cf00b093461d2e5e6d3951551d42eecb20215512ebf9c472d052` has the same 100 logical files. Its downloaded artifact is retained under `R/artifacts/ci-source65/`; `R/ci-source65-artifact-audit.json`. CI host-only success is kept separate from the independently executed pinned native backend and human Gate 2.

## Human pack and visual judgement

Entry point: `R/visual-pack/index.md`. It links:

- `neutral-rest-overview.png`: two rows, front/rear/side columns, fixed framing.
- `arm-raise-counts.png`: front/side rows at counts 0–4.
- `arm-raise-120-panel-1.png` and `arm-raise-120-panel-2.png`: all 13 samples, seven/six columns, explicit beat labels.
- Six paired front/side GIFs at 60/120/180 BPM in the companion native pack.
- Separate front/side count onion overlays with beat-color legends.
- `all-frames.png`: every rendered view; 76 labeled baseline/candidate/absolute-difference panels with error summaries and original links.
- Real protected predecessor HTML-only derivative and detailed numeric/isolation/hash/link audits.

The Markdown pack links resolve; `visual-pack-link-audit.json` records the final count and targets. The reviewer inspected every-view contact sheet, neutral/rest overview, both count/animation panels and both onions. **Visual opinion only:** floor and body position appear fixed, feet appear planted, and arms move symmetrically forward and overhead. No new body crossing or visible penetration was observed. Front-view arms are foreshortened at counts 1/3; side view clarifies direction. Coincident counts 0/4 and 1/3 cause later onion colors to cover earlier ones. Pixel equality establishes unchanged rendering, not human approval of anatomy or exercise readability.

- [x] [H] Human Gate 2: accepted by the human on 2026-10-24: "визуально проблем не замечено, принимается." Acceptance covers the delivered visual pack, including silhouette/stature/framing, count alignment, forward arm movement/readability, contact appearance and HTML presentation. Recorded by the orchestrator from the human's explicit approval; the reviewer does not decide this for the human.

## Unverified or intentionally excluded scope

All delta requirements/scenarios were verified within the declared scope. The human accepted the delivered visual pack on 2026-10-24. Native scope is the approved neutral/rest/four-beat arm-raise regression, not all 32 fixtures, dense-floor/full-domain or three-stature native anatomical acceptance. Those unchanged optional algorithms and writer paths have host coverage; this review does not claim their complete real-backend rerun. Circular via sweeps and new export/bake formats are outside this change.

## Cleanup and retained dependency closure

Cleanup is complete; pending cleanup: none. Only reviewer-owned content or explicitly authorized central maintenance was removed. Developer/accepted/protected roots were not changed by this reviewer.

| Cleanup owner/scope | Removed regular-file logical bytes | Exact record |
|---|---:|---|
| Current reviewer setup/disposable fixture content | 1031870358 | `R/cleanup-setup.json`: build/install caches, duplicate 900-sample workspaces, tamper and synthetic/hostile-neighbor fixtures, extracted sdist, superseded source fixture and completed fixture build content. |
| Current reviewer completed environments/temp/config | 34227158 | `R/cleanup-environments.json`: both readonly venvs, host temp/cache/config and empty invocation fixture. Proxies had completed and actual CI comparison passed before removal; cleanup used the base interpreter, not a removed environment. |
| Inactive old c3e9007 reviewer root, central root maintenance | 902742983 | `R/predecessor-cleanup-result.json`, `R/predecessor-cleanup-inventory.json`: exact old root removed, 3007 regular files and four symlinks, zero symlink targets followed. This reviewer did not mutate another reviewer's root. |

Own removals total 1066097516 bytes; central predecessor removal 902742983 bytes is recorded separately. Before/after current cleanup all 2950 required visual/HTML/raw-frame/receipt/numeric-shard targets remain present as an identical dependency set; central old-root cleanup checks 3031 required targets. Final closure is rechecked after record/index updates in `R/final-retention-audit.json`. No removal followed a symlink target.

Old diagnostic proof closure is preserved as 10 SHA-256-verified files (3547690 bytes) in `R/diagnostic-history-c3e9007/`: exact superseded wheel, immutable source archive, harness/assembler, cited R1/R2/R3 failure logs and independent baseline/predecessor hash evidence. `R/predecessor-diagnostic-preservation.json`. This retains reproducible resolved-finding history without an obsolete environment. Revisit on an audit or reopening of R1–R3.

Retained current roots and reasons:

- `R/artifacts/`, `R/rebuilt/`, `R/sdist-wheel/`, `R/source.tar`, `R/source-followup/`: exact local and both actual CI wheels/logs, immutable production/test source closure, independent build/sdist proof; reproduce in a new run if a runtime/packaging finding is reopened.
- `R/caller-workspace/build/`: real source build, complete numeric report/shards, accepted technical two-pass pack, HTML derivative, pass-local receipts and logs. These are the human pack's actual linked dependencies.
- `R/visual-pack/`: all frames, counts, seven/six-column animation panels, paired GIF links, colored onions, all 76 baseline/candidate/difference panels and index; retained for human Gate 2.
- `R/serialization-workspace/`, `R/serialization-alias`, `R/domain-a/`, `R/domain-b/` and tiny readonly cwd fixtures: actual two-installation serialization/domain receipt and lifetime evidence. Retain for a concrete workspace/concurrency regression audit.
- Root audit JSON/logs and reviewer scripts: commands, checksums, metrics, failure/resolution history and cleanup proof. Their removed interpreter/execution paths are diagnostic provenance, not active dependencies.

Protected dependencies remain unchanged at `build/package-humanmotionlib_r1_dev_try-23_build/`, `build/package-humanmotionlib_r1_dev_try-23_pack/`, the exact pre-change wheel/evidence in external baseline try-2, and the real historical HTML predecessor. Do not remove or relocate them while baseline comparison links or retained predecessor evidence depend on them. Reconsider final pack/dependency retention only after human Gate 2 or a replacement pack with verified closure.
