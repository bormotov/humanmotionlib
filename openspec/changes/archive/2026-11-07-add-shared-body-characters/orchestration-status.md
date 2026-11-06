# Orchestration checkpoint

This is an operational checkpoint, not acceptance or a replacement for scoped reports.

## Later progress (current candidate)

### Latest checkpoint: try251

- Reviewer found that the three-height aggregate incorrectly compared stature-scaled metre values as identical. Architect confirmed this is a verifier defect and specified a fail-closed canonical-source comparison; developer fixed the verifier and the documented review-pack input paths. Reviewer independently tested the corrected comparator (6/6) including five negative mutations.
- Frozen try251 wheel SHA-256 `2fd71010dd78fadfca4078d841ab37394b180eb62a8a379df0310a2b1571f98a`, runtime manifest `de3ffa80c5f0622b7a0bb7ab7fd9d8186da28c4f4268d6fbe55346528a857b93`. Reviewer independently rebuilt its package and verified 116 logical files. Both dev and reviewer prepared fresh inputs for three heights; reviewer also prepared visual inputs.
- Try206 native, aggregate and visual results are historical and cannot be resealed or treated as try251 acceptance. Architect confirmed fresh native builds and checks are required under the final package identity. Tasks 7.1 and 8.1 are reopened.
- Dev try252 sandboxed suite ran 375 tests with 11 failures, 2 errors and 7 skips, all 13 affected tests process-supervision/ownership cases; an unsandboxed repeat is required. Reviewer additionally passed installed comparator tests 3/3 and surface/skinning tests 35/35 under try251. A system-access request for the full suite is awaiting a response; no process was present at the last check. Do not bypass process ownership guards.
- Next: full dev/reviewer host checks, fresh independent native/dense/aggregate at three heights, consumer and complete visual packs for try251, dependency-aware cleanup, then Human Gate 2. Preserve all evidence and unresolved diagnostics. Prior checkpoint text below is historical where it conflicts.

- Independent R2 compatibility checks passed 20/20, including actual default pack and strict sealed/legacy reuse. The finding is closed in that scope.
- Independent host checks on try206: 372 tests, 365 passed, 7 explicit installed-harness skips; isolated installed acceptance 7/7. OpenSpec progress is 19/37.
- Developer try212 native matrix built and passed API postflight at H=1.50, 1.70 and 1.90 m, each with 900 delivered samples and 60 midpoints. Developer try213 H=1.50 numeric report records pass; remaining heights and aggregate are pending.
- Independent reviewer native H=1.50 is running in its own try6 run, with its own installed candidate and input. Independent numeric and complete visual pack, both cleanups, and Human Gate 2 remain pending. Earlier status below is historical where it conflicts with this update.
- Subsequent checkpoint: independent reviewer native builds for all three heights completed API postflight; reviewer H=1.50 numeric passed (5,714,431 measurements), H=1.70 numeric is in progress and H=1.90 remains pending. Developer consumer try231 built successfully with 17 samples and 60-degree bilateral knee flexion; its host numeric audit is running. Developer H=1.70 focused visual evaluation built 171 samples. Developer exact-candidate host suite is running in try234.
- Visual eval at the other heights and the final visual packs remain pending. A required unsandboxed launch request received no response; the shell sandbox's earlier version probe reported an ambiguous orphaned descendant. The failed and concurrent attempts are retained as diagnostics; no acceptance is implied. Cleanup and Human Gate 2 remain pending.

## Current implementation snapshot

- Change: `add-shared-body-characters`; Human Gate 1 approved, Gate 2 pending. The human repeatedly authorized continuing implementation. No archive, release, commit or push was requested.
- Main agent orchestrates only; architect designs, dev implements, reviewer verifies independently. Repository text is English; conversation is Russian.
- Current candidate: `build/add-shared-body-characters_r1_dev_try-206_r2-final-candidate/wheelhouse/humanmotionlib-0.3.0-py3-none-any.whl`.
- Wheel SHA-256: `6f2389268cf59ee29e71bec00b659100483e199dd7a3ac520adb6806714a215f`.
- Runtime manifest SHA-256: `739c6f975d2e7f04fb05dbfd2a6984a1d86667d96ab587697ec397bae7836573` (50 implementation modules, 64 resources, 116 logical package files).
- Source remains frozen. Relative to try196, try199 changed only `docs/usage.md`; try206 then changed only `review_pack.py`. Root compared the installed manifests. Retain exact immutable artifacts and regenerate package-bound preparations rather than resealing old evidence.

## Independent findings and correction ownership

### R1: shared torso base and preset deltas

Reviewer confirmed that independent absolute torso tables violated the approved design. Architect specified the conforming correction: ten base `radius_h` pairs in the shared template, required signed `torso_radii_delta_h` pairs in presets (male zero, female the approved differences), effective addition before interpolation, no absolute fallback, and finite/positive effective dimensions before output.

`characters_dev` owns R1 data, schemas, `character_surface.py`, character documentation and relevant tests. Frozen silhouette values, topology, weights, binding, skeletal proportions, movements, contacts and tolerances remain unchanged. Initial unreleased source versions remain as directed by architect; all new package/preparation/request identities must be regenerated.

- Exact try196 R1 integrated tests: **40/40 pass**, `build/add-shared-body-characters_r1_dev_try-197_integrated-host-check/test-report.json`.
- Exact try196 API/CLI regressions: **28/28 pass**, `build/add-shared-body-characters_r1_dev_try-198_api-cli-regressions/test-report.json`.
- Reviewer independently rebuilt try196 in `build/add-shared-body-characters_r1_reviewer_try-2_r1-check/`; **7/7 reviewer-authored R1 checks passed**. All ten rings at three heights, all-vertex common-base/isolation propagation, twelve invalid preflights and unchanged topology/weights were independently checked. R1 is corrected in HOST/SOURCE scope, with full current native acceptance still pending.

### R2: default skeleton review-pack route

Reviewer independently reproduced the old default producer calling `run_blender.run(owner_run=...)` without a claim, rejected by the new strict guard. Architect requires the default producer to use the same private owned API as the character producer (public API for standalone), with no auto-claim or guard bypass. Reuse supports exact legacy current-package inventory or strict sealed inventory, and missing sealed requests cannot downgrade to legacy.

The initial helper released `review_pack.py` and its tests to `characters_dev`; it has no active native/test job. `characters_dev` now owns R2 integration and the shared private API expected-request builder. Its fresh try204 R2 tests passed 41/41 on try199, but the reviewer's actual installed-only smoke found two real consumer bugs: producer postflight omitted the request from the receipt union (22 expected versus 23 actual files), and reuse incorrectly counted all outcomes rather than the render operation.

Try206 fixes both actual defects through shared strict postflight/reuse validation. Sealed passes require exactly one successful probe and render; genuine legacy supports its documented optional probe. Unknown, missing, failed and duplicate operations remain rejected. Fresh try208 tests had 41 pass plus one test NameError; the corrected test passed separately 1/1 in try209, with runtime unchanged. Do not describe that as one uninterrupted 42/42 run.

Reviewer independently rebuilt try206 and the actual neutral/rest default pack + two real clean passes + no-spawn sealed reuse **passed** in `reviewer_try-4_r2-check/actual-r2.json` (18 PNGs per pass, exact decoded repeatability). Its host negative/legacy checks are still pending before R2 closure. No native session remains active. Dev is running host-only full matrix preparation in fresh `try-211_full-matrix-prep` (session 24289), asserting 900 samples/32 fixtures/BPM60,120,180 at each height; native launch waits for reviewer R2 negatives.

## Prior evidence stays scoped

- The historical developer visual pack try194 passed under **try191**, not try196: 171 samples, 192 composites, four stature strips, 12 HTML pages, 1,377 local links and 207 inventory paths. It predates R1/R2 and does not close their requirements. Its large render tree was superseded by the later try247 pack and removed during selective cleanup; the report summary remains here, and removal is recorded in `cleanup-inventory.md`.
- Try191 midpoint build `try195` passed: 22 delivered samples and four additional beats 0.5/1.5/2.5/3.5 for both surfaces; canonical residuals below 0.9 micrometres. `midpoint-check.json` records its scope. Midpoint rows are shared solved frames, not per-character rows. The midpoint payload is sealed by render preflight, not stored in prepared input JSON.
- Independent try191 reviewer host run: 364 tests, 356 pass, one R2 error, seven explicit installation-harness skips; own installed acceptance 7/7 and package closure passed. Snapshot was stable. `review.md` remains IN PROGRESS, with R1/R2 open; native was never launched.
- The old try70 full native matrix at three heights and try140/141 dense verification remain historical evidence. Current canonical torso sources changed; do not enlarge GenerationAnchor exceptions or reseal old generation to call it current.
- Protected old baseline try2 and its input remain untouched. Additional exact pre-change BPM90 baseline is `build/add-shared-body-characters_r1_character-final-packaging_try-1_historical-render/`: 69 shared-core samples and 152 PNGs, own historical wheel identity. Join images by exact fixture/Fraction beat, never by matching index IDs. Preserve user-visible try121 preview.

## Workflow and pending work

OpenSpec progress is **18/37**. Dev tasks 2.4/2.6 were reopened for R1 and reclosed on exact try196 developer evidence; independent finding closure is separate. Tasks 4.5/6.4 were closed after the required runnable single-character docs example and exact try199 source/installed documentation checks. Task 5.3 explicitly tracks R2. Do not mark partial native, rendering or visual approval tasks complete.

Next: finish independent R2 negatives/legacy closure; run final host/installed/package checks and clean current native/dense matrix at all three heights; regenerate final complete visual evidence; finish developer/reviewer cleanup and reports; present independent review pack for explicit Human Gate 2. No numerical result implies visual approval.

All independent runs require fresh empty direct-child roots with the five-component naming convention. Do not reuse an old midpoint harness root for a new independent acceptance run. Use explicit resolved path tables and verify candidate origin/manifest/seals before launch; partial string replacement previously retained stale f-string paths. Use an exact private interpreter for child tests that remove PYTHONPATH. Offline caches belong inside the writable owning run. Real supervision checks need system process inspection through the escalated saved harness.

Cleanup inventory is in `cleanup-inventory.md`. Seven resolved coordinate-space attempt roots (9,599,304 bytes) and twenty empty obsolete roots were removed and recorded; protected/current/reference dependencies remain. Never delete another agent's active run or follow symlinks. Older reports or checkmarks are not blanket final-candidate acceptance.
