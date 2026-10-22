# Independent review — r3 / try-1

**Verdict: PASS WITH NOTES (technical checks).** No open implementation finding. Human visual gate 2 remains pending; this verdict does not approve visual correctness or renew complete anatomical/mobility acceptance. The focused pack is [index.html](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_pack/index.html), with a short [index.md](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_pack/index.md).

## Identity and independent execution

HEAD `8e632deb6fe4e3bf9561e38c27a62ba2d7770623` plus frozen working-tree changes. Snapshot SHA-256 **`dc0b38051974d1a858bdeb25eca1d978f17878824fa859d9e328521803523233`**, 122 files. [Source inventory](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_checks/source-snapshot.json) covers tools/tests/schema/rig/scenes/data/docs/pins/licenses; [recheck](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_checks/source-recheck.json) confirms 122/122 unchanged. Review/task/handoff status artifacts are excluded from source identity; developer cleanup updates to handoff are expected. Repository AGENTS, reviewer role, current CLI status/apply and all four context artifacts/operator hand-offs were read. `/AGENTS.md` is absent; repository AGENTS applies.

Fresh empty five-component direct-child reviewer roots: `build/harden-backend-process-execution_r3_reviewer_try-1_checks/`, `_build/`, `_pack/`. Stock executable suites used `HUMANMOTIONLIB_TEST_RUN_ROOT` and module cases beneath the owned checks root. `TMPDIR` routed disposable workflow fixtures there; no allocator monkeypatches or source edits. Test-module imports create no runs. Existing checkout source plus factory-startup children and fresh outputs were used; developer artifacts were never used as independent acceptance evidence. All real Blender operations were supervised, serial, fail-fast and outside the execution sandbox on Darwin-arm64. No native failure, automatic retry, renderer/environment switch, GUI/MCP construction, version change or dependency change occurred.

## Findings and resolution

| ID | Severity | Requirement/scenario | Evidence and resolution | Direction |
|---|---|---|---|---|
| F-1 (r2, closed) | major | **Checkout-owned backend work does not overlap**; **Backend execution and cancellation are bounded** / *Contend for a running backend* invariant | Prior independent reproduction showed a zero-exit leader reported succeeded/cleanup not-needed while its descendant group stayed present; a second supervised child succeeded concurrently. The old snapshot was `2ec75861eade5f762683e6f5942ba161f6e546c68ddcee76759579f86d6ebdca`. Current `tools/runtime.py:449` observes the unreaped leader/group before release and fails/cleans surviving descendants. `tests/test_runtime.py:177` independently passed both exit codes 0/7: orphaned-descendant, failed, cleanup confirmed, group absent, unrelated sentinel survives. Current receipts are linked in [process cases](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_pack/process-cases.md). | No remaining fix required for the reproduced edge. Keep regression coverage. |
| F-2 (r2, closed) | major | **Crash recovery is explicit and preserves run ownership** / lifecycle fresh allocation and ownership | Prior stock modules allocated/reused developer roots. Current `tests/run_roots.py:16` accepts a caller-owned valid root; case allocation is exclusive. Import-side-effect test and all stock suites independently passed using only reviewer-owned cases. No developer root was written by reviewer tests. | No remaining fix required. |

The earlier queued-cancellation concern was unconfirmed at r2. It is now independently verified: `tests/test_runtime.py:247` passes queued SIGINT and SIGTERM with no contender spawn, cancellation evidence, live owner preservation and later slot availability. This is not an additional unresolved finding.

## Requirement/scenario checklist

A = automatable; N = numeric; H = human judgment. Each named delta requirement and scenario is listed. Process success remains separate from numerical/image/human acceptance.

| Requirement or scenario | Type | Verdict/evidence |
|---|---|---|
| Routine backend work has one controlled execution path | A | PASS: launch-site/source audit, wrapper/probe assertions, real supervised integration. Only `tools/runtime.py` contains routine native spawn; test subprocess helpers are authored synthetic children. |
| Inspect and build with the pinned backend | A | PASS: resolved symlink/identity/mismatch/no-script-after-failed-probe tests; current real builds pin Blender 5.2.2 LTS `d13f752e3b9c`. Background/factory-startup/Python-exit-code 1 in receipts/argv tests. |
| Keep presentation-only work independent of Blender | A | PASS: HTML-only interception and existing presentation regressions; no probe/native launch. |
| Backend execution and cancellation are bounded | A/N | PASS for required matrix: finite defaults/override rejection, missing/spawn errors, cancellation, timeout, descendant cleanup and sentinel survival. |
| Stop a hung process and its descendant | A/N | PASS: resistant descendant deadline 1s; recorded elapsed **6.031563s <13s**; cleanup confirmed, sentinel survives. |
| Cancel or fail to start work | A | PASS: after-spawn cancellation, queued SIGINT/SIGTERM, two spawn-error cases; no completed pack verdict; owned cleanup/no-spawn assertions. |
| Checkout-owned backend work does not overlap | A/N | PASS: separate caller lifetime intervals do not overlap; F-1 zero/nonzero descendant cases now fail closed and clean. |
| Contend for a running backend | A/N | PASS: two callers serialized; slot contention **0.154173s** at 0.15s configured wait, no child stdout/spawn; unrelated Python work runs. |
| Recover ownership after supervisor death | A | PASS: own invocation-ID correlated unfinished receipt; live orphan blocks; confirmed-absent group permits recovery; ambiguous ownership blocks and preserves sentinel. |
| Invocation evidence survives failures | A | PASS: receipt/log matrix, raw exit/signal classification, unknown phases, unfinished parent-death evidence; current actual build/render phases and output hashes. |
| Diagnose a native failure before the script starts | A | PASS synthetic equivalent only: positive code7 and directly observed SIGTERM retain raw status/signal and unknown phase, without causal inference/private environment collection. No real application intentionally crashed. |
| Distinguish script execution and process shutdown | A | PASS: actual ordered script_started/input_loaded/backend_ready/progress/outputs_written/script_complete, saved blend required; nonzero-child-complete-output and missing completion tests fail closed; unfinished record distinguishable. |
| Successful execution requires complete fresh evidence | A | PASS: matching current completion/input/backend identity and fresh output preflight, readable image/manifest inventory, complete hash closure. |
| Reject apparently usable outputs from a failed execution | A | PASS: missing/malformed metadata, missing completion, stale outputs, nonzero complete-output cases; failed first pass prevents retry/second pass/assembly. |
| Accept a complete operation without weakening numerical checks | A/N | PASS: 2 current numerical builds, 31/31 samples each, matching receipts/input identity; downstream metric aggregate remains honestly FAIL for omitted diagnostic coverage. |
| Crash recovery is explicit and preserves run ownership | A | PASS: no automatic retry/fallback launch path; current caller-owned test/run guards and dependency cleanup below. |
| Fail one clean render pass | A | PASS injected failure: one first-pass call, zero retry/second-pass/assembly; stale/changed reuse rejected; protected legacy HTML-only regressions pass. |
| Complete a failed-attempt hand-off | A | PASS reviewer-owned lifecycle; resolved r2 evidence removal and owner cleanup recorded below. Native diagnostic causes remain unresolved and retained by their owner. |
| Execution hardening preserves reproducible animation outputs | A/N/H | Technical PASS: unchanged canonical sources/conventions/pins, two numeric comparisons, two exact render passes and timing/stability. H pending. |
| Compare the focused regression pack | N/H | Technical PASS: exact requested layouts, original PNGs, six animation sheets/GIFs, count onions, 33-case process table. **Human decision pending** for readability/planted feet/stable framing. Full diagnostic acceptance not claimed. |

[33-row synthetic case table](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_pack/process-cases.md) contains expected/actual/evidence/cleanup for every runtime/wrapper/pack synthetic test, plus granular invocation receipt rows. These are simulated/authored failures, not new vendor incidents.

## Tests and measured quality gates

**64/64 tests:** [source/runtime/wrapper/presentation 57](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_checks/source-suite.json), [backend 6](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_checks/backend-suite.json), [fault harness 1](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_checks/fault-suite.json), with all ten intended fault rows rejected by the harness. [Logs/runner](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_checks/review_suite.py) reproduce the stock test bodies; logs sit alongside each JSON. Official [validator](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_checks/validation.log): 180 structures, 67 actions, 32 fixtures, valid-sources. OpenSpec validation and diff whitespace checks passed.

Two independent 31-sample numerical builds were prepared from canonical sources at H=1.70m, neutral/rest/arm-raise, BPM60/120/180. Prepared SHA-256 `8418ec846de10fcd84b5fe93e71775dae30d368d3b8c6482369c4826bd1cc411`. [Numeric repeatability](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_build/numeric-repeatability.json): topology and metadata identical; maximum frame-origin and geometry-bound difference **0m ≤1.7e-6m (1e-6H)**; maximum rotation-entry difference **0 ≤1e-6**. Each build passes all 31 per-sample transform/backend checks. Raw [metrics](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_pack/metrics.json) remain **FAIL only for `diagnostic_fixture_coverage`:29 omitted fixtures vs0 full-coverage requirement**. No metric was rewritten to pass. The complete detailed metric directory is bundled in the pack with working image references.

[Independent pack verification](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_pack/independent-verification.json):

| Gate | Actual | Tolerance/criterion |
|---|---:|---|
| Two fresh render passes | 76/76 decoded RGBA pairs equal | Exact equality, original1024×1024 PNGs |
| Receipt output hashes/current inputs | 170 checked | Exact hashes; pinned identity/current completion |
| Local HTML/entry-point/process-table links | 236 checked,0 missing | All resolve |
| Original pixels in paired cells | 28/28 exact | No crop/reframe/resampling in full-size sheets |
| Scene camera/floor/light/settings | 31/31 scene records identical | Exact metadata equality |
| Root drift | 0m | ≤0.00017m |
| Contact sliding | 0m | ≤0.0017m |
| Contact-target maximum residual | 3.371748e-9m | ≤0.0017m |
| Minimum geometry floor Z | 0m | ≥-0.00017m |
| Left/right/top128px exterior image regions, all arm front/side samples | 0 differing pixels | Exact equality outside character |
| Arm loop closure | position0m;matrix-entry0 | ≤1e-6H /1e-6 |
| BPM60 sampling | 5 static,21 animation;4 in-betweens;200ms | ≥2 in-betweens;≤200ms |
| BPM120 sampling | 5 static,13 animation;2 in-betweens;166.666667ms | Same |
| BPM180 sampling | 5 static,13 animation;2 in-betweens;111.111111ms | Same |
| GIFs | 6/6;4s/2s/1.33s paired front/side | Maximum error3.333333ms <10ms |

Static/animation records share sample IDs at count boundaries. Original endpoint PNGs remain; GIF terminal duplicate coalesces with loop start per existing contract. Via-based circular direction, a newly mirrored segment and export/bake round-trip are **not introduced by this change**; no new acceptance claims for those capabilities. Existing bilateral/source/transform checks run in the stock suite; this focused run does not replace the full historical diagnostic gate.

## Pack and visual observation

The reproducible [supplement recipe](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_checks/supplement_pack.py) composes original pixels into full-resolution paired sheets and established `sheet` thumbnails, copies raw metrics plus detail closure, writes the case table, and regenerates focused entry points using existing `write_html`. Generated HTML/metrics were not hand-edited. [Audit recipe](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_checks/verify_pack.py) validates current render reuse receipts/hashes, exact paired cells, GIFs, scene/contact/timing and local links. The initial audit helper used an evaluated-sample field that belongs to the prepared source; its reviewer-only lookup was corrected before the successful audit. No backend/render retry occurred.

- [Neutral/rest4×2 original-pixel sheet](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_pack/composites/paired-neutral-rest.png): clean-a front, clean-b front, clean-a side, clean-b side; neutral/rest rows.
- [Arm counts5×4 original-pixel sheet](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_pack/composites/paired-arm-static.png): counts0–4; clean-a front/clean-b front/clean-a side/clean-b side.
- [Arm animation page](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_pack/arm-raise.html): six sheets, six GIFs, front/side BPM120 five-count onions and every original PNG. Example [120 BPM side GIF](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_pack/composites/arm-raise-120-side.gif).

**Reviewer opinion, not human approval:** paired silhouettes appear identical. I viewed paired sheets, both onions and front/side60/120 animation sheets covering every distinct arm sample (180 reuses120 beat samples with different timing). Feet and floor remain visually aligned; no camera/scale shift or obvious floor penetration is visible. Front projection foreshortens the forward-reaching arms near counts1/3, overlapping their projection with the shoulder/torso; the side view clearly shows the forward-up-down arc. The simplified skeleton and faint outlines are existing authored presentation choices. The human must decide whether that movement is sufficiently readable at all tempos.

## Scope, sources and licensing

No dependency, backend/MPFB pin, source format, coordinate/rotation convention, canonical pose/rig/motion data or fixed scene source changed. MPFB/Rigify are not used. No extra native launch bypass, crash retry, GUI relaunch or private environment collection was found. New runtime/test/runner code carries Apache-2.0 SPDX identifiers; authored data/renders retain CC-BY4.0. `docs/used-materials.md` is unchanged and was audited with source-integrity/provenance checks: no new external reference, imported character, illustration, dataset or font is used by this process-policy change. Existing used text/data/vocabulary permissions and attribution remain in the register and bundled THIRD-PARTY notices; no restricted figures were imported. This review consulted repository evidence only and added no external material.

Crash documentation separates evidence from hypotheses and leaves unavailable browser checks pending. Original private C1/B1–B3 reports are outside this review: repository incident summaries/hash strings were compared, not recomputed from unavailable originals. The causes of those incidents and the development try-4 native failure remain unknown. Successful controlled executions do not prove sandbox/Metal/OOM causation or an upstream repair. No Chrome crash reproduction/browser relaunch was attempted.

## Cleanup and retained closure

Cleanup **complete**. [Owned inventory and before/after dependency audit](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_checks/cleanup.json), [obsolete-root inventory](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_checks/obsolete-inventory.json), and [236 retained link targets](../../../../build/harden-backend-process-execution_r3_reviewer_try-1_checks/dependency-links.json) record the closure.

| Removed owner path | Regular bytes | Reason |
|---|---:|---|
| `build/harden-backend-process-execution_r2_reviewer_try-1_checks/` | 38,766 | Resolved F1/F2 diagnostic superseded by current independent regression; original observations/resolution durably summarized above. |
| `build/harden-backend-process-execution_r3_reviewer_try-1_checks/r2-review-checkpoint.md` | 13,688 | Obsolete copied report linked old root; summary preserved in this durable report. |

Total reviewer removal: **52,454 regular-file bytes**. No symlinks existed in the removed root; none were followed. Pre-removal audit found only the obsolete copy and developer handoff's stale descriptive retention statement; the owner updated that handoff statement. No retained pack dependency targeted the old root. Both removed paths are absent; all236 retained local targets still exist. 122/122 reviewed source files remain unchanged. The checkout coordination state is finished; lock/state files were retained by protocol, not deleted.

Retained r3 reviewer roots (inventory measured before `cleanup.json` itself): checks194 regular files/107,367,309bytes; build88/277,790,992bytes; pack302/257,591,695bytes. Checks retain stock64-test results, synthetic cases/receipts/source identity and reproducible numeric/pack/audit recipes; build retains both numerical output/receipt hash closures; pack retains human-gate originals, media, metrics detail closure, attribution and both clean-pass receipts. One retained probe-test symlink points to its sibling authored fixture; no symlink escapes an owner root. **Reconsideration:** after human gate2 resolution/archive, preserve the accepted pack's required dependency closure and remove unneeded duplicates only after another dependency audit. No obsolete independently managed reviewer root remains and no reviewer cleanup is pending.

Developer owner cleanup is independently cross-checked and recorded in [dev-handoff.md](dev-handoff.md): **16 superseded r1/r2/r3 roots,512,296,552 regular-file bytes removed**. Their current cleanup list is absent; an additional historical r2 try-1 checks path is also absent (the audit JSON therefore counts17 distinct absent paths mentioned across the handoff). The native-failure r1 try-4 and authorized-comparison r1 try-6 diagnostic roots remain present and protected, with operator-record links/reconsideration triggers. Reviewer outputs do not depend on any developer root. No reviewer deleted developer output or accepted history. The handoff now correctly states that the r2 reviewer root was owner-removed. No developer cleanup remains pending.

All test/build/render/audit commands have finished; no approval request or child workload remains active. Technical tasks4.1–4.4 have complete evidence. The orchestrator owns checkbox edits because reviewer role writes only this report and owned runs.

Human gate2/task4.5 remains open. Questions: do the paired passes match, do feet stay planted, are raising/lowering and count poses readable at60/120/180BPM, and is framing stable? No archive, spec sync or commit performed.
