# Independent review: support-consumer-authored-motions

**Verdict: PASS WITH NOTES.** No implementation findings remain open. Automated, installed-package, native numeric and reproducibility checks pass. **Human Gate 2 was approved on 2026-10-25** after the human reviewed the presented pack and confirmed that it looked as intended. Archived on 2026-10-25 after spec synchronization and human Gate 2 approval.

Reviewed on 2026-10-25. The reviewer changed no project implementation, schema or canonical motion source.

## Results and package scope

- The complete independent duplicate-render set uses immutable manifest `0937304c988678ba98ea20ccce770d024e2a996d14384ad21f44583398c2b340`: 44 implementation modules, 52 resources, pinned Blender **5.2.2 LTS / d13f752e3b9c**, Darwin arm64; MPFB/Rigify are not used.
- The final candidate is manifest `4948674cfe7a5adfff7e5cfd2a909b83c1fba1199bd1dded2258ead817c09da7`. The reviewer independently inspected its exact installed diff: only the consumer file-parser exception wrapper changed. All resources, schemas, generation/numeric/backend modules and backend contract are byte-identical. The change preserves the original cause and adds structured file-source/field details.
- Seven independent final installed parser faults pass. Fresh preparation under the final identity produces exactly the same effective prepared data as the reviewed 30-degree source after excluding package identity/content seal. Its original consumer file was removed before rendering.
- A separate final-identity real integration render passes: **34/34 decoded images match**, and all **17 native samples** have exactly equal frames, attachments, geometry, world root and scene observations to the earlier 30-degree render. Host hash, private expected-hash argument, receipt and evaluated-output identities agree. This bridges the parser-only patch without representing the older eight renders as if they carried the newer manifest.

Evidence: [final contract and parser cases](../../../../build/support-consumer-authored-motions_r2_reviewer_try-2_final-contract/final-contract.json), [exact installed source diff](../../../../build/support-consumer-authored-motions_r2_reviewer_try-2_final-contract/parser-only-diff.txt), [final native integration](../../../../build/support-consumer-authored-motions_r2_reviewer_try-2_final-contract/final-smoke-result.json).

## Independent checks

| Check | Result and scope |
|---|---|
| Source-schema validation | Valid: 180 structures, 67 actions, 3 placements, 32 packaged fixtures; new schemas resolve offline. |
| Original independent host suite | 239 tests: 238 passed; one stale lineage-message assertion failed. The corrected exact test was independently rerun and passed (1 test / 22.589 s). The original command is not claimed green. |
| Consumer source/API matrix | 70/70 independent cases passed: representations, parser/schema/semantic faults, parameter/provenance validation, snapshot mutations and consumer-selected peaks. Source adapter and schema hashes were checked across subsequent identities; amended paths were checked separately. |
| Focused amended regressions | 25/25 passed in 143.915 s: API, prepared contract, run-Blender, bootstrap and dependency-isolated consumer reader. |
| Host/backend boundary | 13/13 independent checks passed. A `python -S` process loaded only HML, denied YAML/schema/registry/host adapters, and checked reader plus entry bootstrap. Host semantic/provenance/replay faults failed before probe/process/output. |
| Native expected identity | Missing, mismatched and resealed-substitution cases all failed for the expected reason, before `input_loaded` or scene artifacts, with finalized receipts and no pending cleanup. |
| Final parser contract | 7/7 passed for YAML duplicate/syntax/tag/UTF-8 and JSON duplicate/syntax/non-finite errors: structured path/field, cause preserved, caller bytes unchanged, no process/output. |
| Installed use | Sources reconstructed through the installed public API from an unrelated directory; external source files removed before native rendering. Full-definition, scaling and whole-track replacement paths checked. |

The 70-case/full-host source-contract evidence remains at its original [review run](../../../../build/support-consumer-authored-motions_r1_reviewer_try-2_verify/scenario-results.json). Relevant historical logs, fixed-lineage retest, real between-frame coupled fault, replacement and limit reports are also preserved compactly in [history](../../../../build/support-consumer-authored-motions_r2_reviewer_try-1_verify/history/checked-source-candidate/host-suite.log). Amended evidence: [25-test log](../../../../build/support-consumer-authored-motions_r2_reviewer_try-1_verify/amended-regressions.log), [13-case boundary results](../../../../build/support-consumer-authored-motions_r2_reviewer_try-1_boundary/boundary-results.json), [native negative receipts](../../../../build/support-consumer-authored-motions_r2_reviewer_try-1_verify/native-identity-faults.json).

The explicit work-bound checks cover source/semantic/cardinality acceptance at 0 and 256 beats and exactly 100000 samples. Overflows and tiny BPM fail with sampler/evaluator/process interception before allocation/output; requested mappings remain unchanged. Maximal 256-beat dense solving or rendering 100000 frames was not performed. Ordinary preparation, dense solving and native generation were tested independently. A real wrist-envelope trajectory has valid delivered-quarter scores but exceeds its bound at beat 0.01; it is rejected there with measured score `1.0024068776597432`, allowed `[0,1]`, structured constraint details and no output. See [limit evidence](../../../../build/support-consumer-authored-motions_r2_reviewer_try-1_verify/history/checked-source-candidate/budget-boundaries-result.json) and [between-frame evidence](../../../../build/support-consumer-authored-motions_r2_reviewer_try-1_verify/history/checked-source-candidate/between-frame-result.json).

## Native numeric and image results

Four independently reconstructed cases (30-degree and 60-degree squat variants, a complete authored arm sweep, and packaged neutral/arm-raise/squat) were each rendered twice from clean inputs. All 546380 native measurement checks passed.

| Metric | Measured | Acceptance |
|---|---:|---:|
| Bilateral 30-degree peak | 30.0000017637 degrees | within 0.1 degrees |
| Bilateral 60-degree peak | 60.0000079766 degrees | within 0.1 degrees |
| Unchanged bilateral diagnostic peak | 90.0000075150 degrees | within 0.1 degrees |
| Maximum contact target/sliding residual | 3.371747884e-9 m | <= 0.0017 m (0.001 stature) |
| Lowest evaluated mesh bound | -1.040834086e-17 m | >= -0.00017 m |
| Maximum rigid local-vertex residual | 0 m | <= 0.000001 stature |
| Loop position residual | 0 m | <= 0.00017 m |
| Maximum native matrix loop-angle metric | 0.0100898844 degrees | <= 0.1 degrees |
| World-root XY | fixed | no declared drift |
| Dynamic BPM-90 timelines | 5 static / 17 animation entries | exact rational beats/seconds; 1/6 s intervals; shared pose IDs |
| Duplicate decoded images | 179 comparisons, 0 differences | exact equality |
| Packaged pre-change comparison | 77 comparisons, 0 differences | exact equality |
| GIF duration | 2670 ms vs 2666 2/3 ms | 3 1/3 ms error < 10 ms |

Every successful invocation's expected argument, copied input, `input_loaded`/`outputs_written`/`script_complete` phases, receipt and outputs were checked against the same prepared identity. Fixed cameras, floor, light/settings, rigid transforms, operating/coupling bounds and contact observations pass the independent native verifier. Variant evidence does not inherit the diagnostic's 90-degree or static-balance verdict.

[Numeric summary and per-case identities](../../../../build/support-consumer-authored-motions_r2_reviewer_try-1_verify/numeric-summary.json) links the complete native measurement reports in that same run. No bake/export, new via-based circle, compositor or new mirroring algorithm is introduced; their future acceptance gates are outside this change. Existing mirror/regression checks remain covered by the host suite.

## Scenario coverage

A = automatable host/installed check; N = native numeric/backend measurement; H = human visual judgment.

| Requirement / scenario | Type | Evidence / status |
|---|---|---|
| Closed source / equivalent mapping, YAML, JSON | A | 70-case matrix, representation identity/immutability cases: pass |
| Closed source / unsupported or ambiguous documents | A | Parser/schema matrix plus final seven structured-parser cases: pass |
| Variants / scale explicit squat tracks | A,N | Source-resolution comparisons, 30/60 native peaks and unchanged base: pass |
| Variants / complete track replacement and conflict rejection | A | Independent replacement report; complete key records retained, conflict/duplicate errors, no output: pass |
| Semantics / invalid shape-valid source | A | Profile/ID/channel/control/writer/event/constructor/rest matrix: pass |
| Semantics / body groups and root intent | A,N | Prepared/source joins and native observations: pass |
| Solved checks / infeasible or between-frame intent | A,N | Actual coupled-between-frame fault, mobility and unreachable-contact cases: pass |
| Work bounds / duration and sampling budget | A | Explicit source/cardinality boundaries and allocation/evaluator/process spies: pass within stated evidence scope |
| Clearance / retain cleared declarations | A | Supported license profiles, extra obligations, additive inherited materials and projection: pass |
| Clearance / reject missing or incompatible records | A | Missing/duplicate/conflicting/incomplete/date/NC/ND/obligation/attribution matrix: pass |
| Self-contained snapshot / source project unavailable | A,N | Deleted source files, host tamper/reseal matrix and real installed renders: pass |
| Host/backend boundary / host validation before backend | A,N | 13-case dependency-deny and pre-probe replay/provenance tests: pass |
| Host/backend boundary / reject post-validation replacement | A,N | Dependency-isolated mismatch tests and three native negative receipts: pass |
| Consumer example / external depth | A,N,H | 30/60/90 measurements and pack: automated/numeric pass; human visual approval recorded on 2026-10-25 |
| Public import / safe import and signatures | A | Independent API/bootstrap regressions: pass |
| Preparation / existing default coverage | A | All-fixture preparation regression and existing default API test: pass |
| Preparation / parameter overrides and invalid selections | A | Existing API plus consumer matrix: pass |
| Preparation / explicit consumer movement and selection conflict | A | Source-only result joins and mutual exclusion: pass |
| Provenance / packaged attribution | A | Installed source/register/license-content tests and source closure: pass |
| Provenance / inherited consumer attribution | A | Separate submitted/resolved/base hashes and retained packaged materials: pass |
| Provenance / uncleared reference use | A | Actual-source audit below; no new external source used: pass |
| Projection / serialization and mutation independence | A | Rational JSON projection, deterministic order and detached snapshots: pass |
| Projection / pose, timeline, image joins | A,N | Complete installed results and all native image inventories: pass |

## Resolved findings

No finding below remains open.

| ID | Original severity | Requirement / defect | Closure evidence |
|---|---|---|---|
| R1 | Major | Clearance obligation subsets, extra flags and required attribution disagreed with design | Independent supported-license and negative matrices pass |
| R2 | Major | BPM sample-budget overflow classified as source-validation | Independent tiny-BPM/100001 cases now return invalid-request before allocation |
| R3 | Major | Resealed forged base-lineage ID accepted | Host and backend lineage integrity faults reject; full host re-resolution preserved |
| R4 | Major | Semantic/solved error fields were trapped in text | Source/channel/beat/state/measured/allowed details checked, including the real between-frame fault |
| R5 | Major | Clearance date format was not enforced | Invalid-date fault rejected in independent matrix |
| R6 | Major | Undocumented stature ceiling failed after persistence | Ceiling removed; independent 1.7 m and 11 m static preparations pass |
| R7 | Minor | Fractional documented depth generated an unsafe ID | Exact installed documentation helper at 30.5 degrees passes with a safe ID |
| R8 | Blocker | Blender imported host YAML dependency | Human-approved boundary amendment, dependency-isolated reader/bootstrap, eight native passes and final smoke all pass |
| R9 | Minor | File-parser failures returned empty structured details | Final installed seven-case parser matrix passes; exact parser-only diff inspected |

Historical failed receipts/source snapshots are retained compactly under the review run's `history/`. They are resolved-candidate evidence, not current verdicts. The stale resource-count and lineage-message test assertions were corrected and retested; their earlier failed commands remain described honestly above.

## Source, license and scope audit

The implementation adds no runtime dependency or compiled source index. The changed module/resource inventory matches the approved API/source-validation and host/backend boundary scope. No canonical packaged squat/pose/motion, camera, floor, light, bone naming, units or rotation convention was changed. Sources and templates remain text; generated binaries stay under ignored `build/`.

The reviewer used repository sources, already registered HML data and original technical numbers only. Synthetic `example.invalid` clearance records exercise declarations; they are not external references or claims of real permission. `docs/used-materials.md` and inherited profile/mobility/squat attribution remain intact. Outputs preserve CC-BY-4.0 data, Apache-2.0 code and applicable third-party conditions. Original repository bitmap lettering was used for composites; no new font, image, exercise reference or other external material was introduced. Offline clearance checking is not independent verification of a caller's legal claims.

## Visual pack and human decision

[Final pack index](../../../../build/support-consumer-authored-motions_r2_reviewer_try-2_review-pack/index.md)

- [Readable bottom-pose comparison](../../../../build/support-consumer-authored-motions_r2_reviewer_try-2_review-pack/depth-bottom-comparison.png): 30/60/90 degrees, same fixed crop.
- [Front/side count sheets](../../../../build/support-consumer-authored-motions_r2_reviewer_try-2_review-pack/depth-counts.png) and [all in-between samples](../../../../build/support-consumer-authored-motions_r2_reviewer_try-2_review-pack/depth-inbetweens.png).
- [30-degree side GIF](../../../../build/support-consumer-authored-motions_r2_reviewer_try-2_review-pack/depth-30-side-detail.gif), [60-degree side GIF](../../../../build/support-consumer-authored-motions_r2_reviewer_try-2_review-pack/depth-60-side-detail.gif), [90-degree side GIF](../../../../build/support-consumer-authored-motions_r2_reviewer_try-2_review-pack/depth-90-side-detail.gif).
- Descent/ascent colored onion skins, bottom overlay, complete-definition count sheet/GIFs and baseline comparisons are linked from the index. Detail crops are fixed at `[280,220,760,820]`; native framing is unchanged.

**Reviewer opinion:** the side views clearly distinguish the shallower depths and ordered descent/ascent; feet appear aligned with the same floor, and I see no obvious limb crossing, floor penetration or framing shift. The complete-definition arm sweep is visible and returns to its start. Clean overlays preserve the fixed floor while distinguishing poses. These are observations, not human acceptance or an exercise recommendation.

### Human Gate 2 decision

On 2026-10-25, after receiving the final pack and comparison preview, the human explicitly approved the visual result and confirmed that everything looked as intended. This records acceptance of the presented depth/direction, apparent foot planting/posture and fixed framing. All acceptance tasks are complete; archiving was completed separately on 2026-10-25. The generated pack's original pending label reflects its state when published; this dated decision is the authoritative acceptance record.

## Cleanup and retained dependencies

[Cleanup inventory](../../../../build/support-consumer-authored-motions_r2_reviewer_try-2_final-contract/cleanup-record.json) records **16 obsolete reviewer roots removed / 219215888 bytes**, per-root file/link counts and verified absence. Links were inventoried without following symlinks, and no developer, accepted baseline, outside-build target or active final run was removed. The old tint-pack root was superseded by the inspected final pack; its source locator in publication history is historical, not an active asset dependency.

**22 reviewer roots are retained with individual reasons:** the original checked source-contract/full-host evidence at its existing path; final immutable reviewed environments and scripts; sealed render inputs; duplicate native renders/numeric evidence; native negative receipts; dependency-boundary evidence; final parser/smoke evidence; and the final human pack. Compact resolved-failure history preserves the actual earlier diagnostics without keeping obsolete failed environments. The pre-change developer baseline is retained read-only as a required comparison dependency.

Required final pack, metric, parser, smoke and original checked-source links were checked after cleanup. **Pending cleanup: none.** Human Gate 2 is approved; the change was archived on 2026-10-25.
