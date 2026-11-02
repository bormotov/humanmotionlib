# Build Cleanup Inventory (Review Only)

Date: 2026-10-26

## Scope and method

This report inventories direct children of `build/` named `add-shared-body-characters_*`. It is an advisory inventory only; no run roots were removed or modified. The scan counted regular files and bytes, enumerated symlinks without following them, and recorded text references from project sources/reports and eligible text artifacts in other build roots (up to 20 MB per file). Binary contents, external chat attachments, and agent runtime state cannot be fully discovered by this scan, so an absent reference is not proof that a root is obsolete.

Machine-readable details and the inventory script are retained in `build/add-shared-body-characters_r1_character-final-packaging_try-4_cleanup-inventory/`.

| Measure | Result |
|---|---:|
| Direct run roots scanned | 243 |
| Regular files | 24,996 |
| Regular file bytes | 22,120,027,397 |
| Symlink entries (not followed) | 68 |
| Scan errors | 0 |
| Roots with project source/report text references | 57 |
| Roots referenced by text in other build roots | 106 |

The scan's local reference list is limited to `openspec/`, `docs/`, `src/`, `tests/`, and `tools/`; build-to-build references are a separate field. Run roots often contain metadata, scripts, or logs that refer to other roots, so text references must be considered as dependency clues, not automatically as keep/delete decisions.

## Preserve

The following sets have concrete preservation reasons:

- Protected shared skeleton baseline: `build/add-shared-body-characters_r1_dev_try-1_input/` and `build/add-shared-body-characters_r1_dev_try-2_baseline/`. These are the historical comparison sources and outputs.
- User-visible focused preview: `build/add-shared-body-characters_r1_dev_try-121_focused-preview/`. Its skeleton, male, and female neutral front images were shown in chat; retain them and their parent run.
- Historical native matrix: inputs `try-74_all-h150-input`, `try-76_all-h170-input`, and `try-78_all-h190-input`; outputs `try-79_h150-native`, `try-80_h170-native`, and `try-81_h190-native`; retain the matrix harness/index at `try-82_native-matrix` and supporting reports/artifacts referenced by `native-checks.md`.
- Current numeric evidence: `try-147_numeric-verification` (focused and coverage-incomplete), the historical try70 full native matrix and its verified numeric audit roots `try-79`/`try-80`/`try-81` and `try-140`/`try-141`, plus the passing focused native try73 evidence. Early try65/try69 coordinate-space diagnostics are now resolved and their output roots are recorded as removed below.
- Current managed-pass candidate and visual work: try177 candidate/package/installation evidence; fresh try180 inputs, try183 evaluations and try179 render outputs. The try179 outputs exposed a postprocessing marker bug and remain useful for the helper's assembly debug. Old try168 candidate, try169 inputs, try171 outputs, and try173/174 consumer artifacts are historical/superseded; retain only while the corresponding current-candidate pack/consumer checks or reports still depend on them, then decide after the new candidate is frozen. The resolved preflight-only try175/176 roots were removed as recorded below.
- Package and installed-runtime snapshots explicitly consumed by `packaging-check.md`, `installation-check.md`, or `historical-baseline-check.md`, including the exact wheel/install identities recorded in those reports. Keep their referenced source snapshots until replacement evidence is accepted.
- This inventory run: `build/add-shared-body-characters_r1_character-final-packaging_try-4_cleanup-inventory/`, so the method and raw inventory can be audited.

The implementation agent also requested retention of older package-bound artifacts for comparison. That request controls even where the scan found no source/report text reference.

## Candidate groups for parent review

The original scan was advisory. The following per-root decisions were made after updating the developer handoff and native-check record and checking that no active process, symlink, or retained run dependency needed the obsolete roots.

1. **Empty attempt roots.** The scan found 23 roots with zero regular files and no symlinks. Most appear to be failed preflight/check attempts and would reclaim no meaningful disk space. Candidate examples include older `dev_try-19_check` through `dev_try-30_check` roots and empty `dev_try-5_check`/`dev_try-6_check`. Before removing any, confirm the attempt is not resumed and check its exact text-reference entries in `inventory.json`. Exclude `try-120_focused-preview` and `try-122_installation-check` from bulk cleanup: try120 is adjacent to the displayed try121 preview, while the earlier handoff records try122's ownership as unclear.
2. **Superseded checks and generated test outputs.** Older `check`, `host-suite`, `supervision-tests`, and focused-render roots may be removable when the exact result is preserved in a retained report and no later run consumes their files. Some are unreferenced by project documents but referenced by build metadata; inspect each `build_text_references` list before deciding.
3. **Superseded wheel and virtual-environment snapshots.** Older `numeric-wheel`, `candidate-wheel`, and `candidate-venv` roots may contain substantial duplicated bytes. Remove only after verifying that no retained report cites that exact wheel/manifest and that no historical comparison is required. Keep the specific old candidate wheel and historical installed target used by the historical baseline report, as well as the active current candidate snapshot.
4. **Superseded render/evaluation matrices.** Older `character-eval`, `surface-check`, `skeleton-verify`, or review-pack outputs should be considered only after a replacement report covers the same source identity and scenario set. Failed runs can be unresolved diagnostics and should not be removed solely because a later output exists.

Do not treat `local_text_references = []` as a cleanup signal by itself. The machine inventory records both project text references and cross-build text references, but neither can identify chat-only references or agent-owned resumable state.

## Reference and cleanup risks

- `developer-handoff.md` contains older status snapshots and cleanup statements that predate later candidate and review evidence; it can mislead if treated as current state. Prefer the scoped identities in the specialized reports and current worker status.
- The review is still in progress and `review.md` is not present yet. A new candidate/evaluation matrix is expected after the managed-pass fix, so current diagnostics remain relevant.
- `native-checks.md` documents preserved matrix dependencies; do not collapse the input/output roots into generic “old run” groups.
- A clean filesystem scan cannot see task attachment references. In particular, the three try121 preview images were surfaced directly in chat and require preserving the enclosing run.
- The scan found 68 symlink entries and did not follow them. Any eventual cleanup should recheck symlinks immediately before removal and must not traverse or delete their targets.

## Executed cleanup decisions (2026-10-26)

Before and after symlink checks enumerated links without following targets. Removed these resolved, obsolete whole dev-owned roots after their historical failures were closed in `native-checks.md`:

- `build/add-shared-body-characters_r1_dev_try-61_h150-input/` — 1 file / 814 bytes.
- `build/add-shared-body-characters_r1_dev_try-62_h150-input/` — 1 file / 4,408,095 bytes.
- `build/add-shared-body-characters_r1_dev_try-63_h150-native/` — 1 harness file / 1,736 bytes; its requested output path had been rejected before Blender started.
- `build/add-shared-body-characters_r1_dev_try-65_h150-native/` — 7 files / 389,414 bytes; the 0.225 m offset was resolved by the corrected transform chain and passing try73/try70 evidence.
- `build/add-shared-body-characters_r1_dev_try-67_h150-input/` — 1 file / 4,408,095 bytes.
- `build/add-shared-body-characters_r1_dev_try-68_h150-harness/` — 1 harness file / 1,736 bytes.
- `build/add-shared-body-characters_r1_dev_try-69_h150-native/` — 7 files / 389,414 bytes; the 0.318 m offset was resolved by the corrected transform chain and passing try73/try70 evidence.

Total removed: **9,599,304 regular-file bytes** across seven roots; all seven paths are absent after removal. The pre-removal inventory found zero symlinks in each root, and no link target was followed. The old try60 and try66 candidate wheels were retained because separate retained host-suite logs cite those exact identities; try70 is retained as the dependency anchor for the historical full native matrix.

After the managed-pass fix was exercised in successful try179 renders, also removed the resolved preflight-only roots `build/add-shared-body-characters_r1_dev_try-175_pack-orchestration/` (1 file / 1,331 bytes) and `build/add-shared-body-characters_r1_dev_try-176_visual-pack/` (1 sealed request / 51,952 bytes). Try176 had stopped before Blender because API-owned request creation conflicted with the old freshness guard; try179 succeeded with the bounded claim. Both roots were direct build children with zero symlinks, both paths are absent afterward, and no link target was followed. Their old harness/request no longer have a revisit trigger.

Also removed 20 empty dev-owned run roots that the scan confirmed had no symlinks or local/build text references: `try-5_check`, `try-6_check`, `try-10_package-check`, `try-19_check`, `try-20_check`, `try-23_check` through `try-30_check`, `try-42_h170-native`, `try-43_h190-native`, `try-50_skeleton-verify`, `try-86_candidate-host-check`, `try-101_numeric-host-check`, `try-103_numeric-host-check`, and `try-132_host-suite`. They contained zero regular bytes; after-check confirmed all 20 paths are absent. `try-120_focused-preview` was explicitly preserved despite being empty because it is adjacent to the chat-visible try121 preview. No other agent-owned roots were modified.

Protected roots remain unchanged: original baseline try2 and its source input, the supplemental historical BPM90 baseline, user-visible try121 preview, complete try70 generation matrix and numeric audits, focused try73 native evidence, current try147 scoped numeric report, try177 candidate and its packaging/installation proof, and active try179 visual evidence. Other superseded package-bound roots and active try180/183 work still require final dependency checks after the current visual/consumer work; cleanup is not complete.

## Current in-flight inventory (2026-10-27)

A fresh scan is recorded in `build/add-shared-body-characters_r1_dev_try-223_cleanup-inventory/inventory.json`, generated by the adjacent `inventory.py`. It covers 306 direct build roots, 65,641 regular files, 69,636,750,737 regular-file bytes, and 118 symlink entries; it reported no scan errors and did not traverse symlinks. The scan includes try206 and current try211–224 work.

No cleanup was completed in this scan. The user interrupted the attempted deletion before it ran; a follow-up confirmed both candidates remain. `build/add-shared-body-characters_r1_dev_try-1_verify/` has one zero-byte `.log`, no symlinks or source references, and only a historical inventory mention. `build/add-shared-body-characters_r1_dev_try-184_debug-presentation/` is empty, has no symlinks or detected text references. Both are candidates for removal after a final process/dependency check, with zero bytes reclaimed. Retain `try-120_focused-preview` and `try-122_installation-check` as previously protected; retain `try-134_host-suite-workspace` and `try-167_visual-pack` because earlier host/pack runs reference them; retain `try-185_debug-presentation` because it contains four symlinks whose purpose/targets are not part of this cleanup decision. Empty `try-217_consumer-build` and `try-222_consumer-check` are reserved outputs from incomplete diagnostic attempts. Preserve try224's supervised Blender receipt; it records `cleanup_pending`, and the coordinator later confirmed process group 88283 was absent from the full process list.

Current try206 native, dense and visual runs, superseded pack artifacts and historical package/build inputs require another dependency pass after the developer consumer and visual pack and reviewer numeric/visual work finish. Their replacement and exact evidence scopes are not yet complete, so cleanup remains pending; no other agent-owned root has been removed or modified.

## Follow-up dev runs (2026-10-27)

The try223 inventory predates follow-up attempts `try226` through `try241` and is not a final inventory. Current ownership/reasons pending the final dependency pass:

- Retain successful current-candidate evidence: `try231_consumer-build` (successful 17-sample consumer API build), `try230_consumer-check` (unresolved scoped consumer report), `try227_visual-build-h170` (H=1.70 evaluation), `try240_host-suite` (exact try206 372-test pass), and `try241_package-check` (exact try206 wheel/sdist/rebuilt-wheel closure).
- Retain successful current-candidate visual evidence: `try242_visual-build-h150` and `try245_visual-build-h190` (each 18 samples, all characters, successful Blender 5.2.2 receipts), plus `try247_visual-pack` (complete pack pass: 4,064 PNGs, 54 GIFs, 12 HTML pages, 192 composites, zero symlinks). Keep existing `try227_visual-build-h170` as the H=1.70 pack input.
- Retain immediate dependencies: `try235_host-env` (isolated installed try206 interpreter used by `try236`, `try238`, `try239`, `try240`, `try242`, `try245` and `try247`), `try219_visual-input-h150`, `try221_visual-input-h190`, `try220_visual-input-h170`, `try216_consumer-input`, and the immutable historical baseline. The isolated uv cache roots `try243_cache-h150`, `try244_cache-h190`, and `try246_cache-pack` were used only by their individual launches; final inventory should verify their symlinks/bytes and remove them if no concrete dependency remains.
- Preserve diagnostic evidence until the final pass: `try234_host-suite` (stale `.venv` child-interpreter run and exact tracebacks), `try236_host-targeted` (two consumer tests that passed after isolation), `try238_runtime-targeted` (sandbox process-table ambiguity), and `try239_runtime-escalated` (12/12 runtime process cases passed). The earlier harness-only roots `try233_host-suite` (bad root path) and `try237_runtime-targeted` (unittest import path failed before any runtime test) were removed after confirming they were direct dev-owned roots, had no symlinks or external text references, and were no longer needed: 9 files / 18,005 bytes removed, zero symlinks, both paths absent after removal.
- Superseded planned roots `try226_visual-build-h150`, `try228_visual-build-h190`, and `try229_visual-pack` remain empty and were not reused. They are safe cleanup candidates after a final dependency check; actual visual outputs are in `try242`, `try245`, and `try247`.

No cleanup has been performed on these follow-up runs. Reviewer aggregate/visual work remains active; do not touch those roots. At final cleanup, re-check active processes and all path/link dependencies before removing superseded diagnostics, uv caches or empty planned roots; preserve try230 while its consumer-only verifier scope interpretation is unresolved. Do not follow symlinks outside `build/`. The final inventory must account for virtual-environment symlinks in `try235` and retain that venv while try240 remains the handoff evidence.

## Selective cleanup after user request (2026-10-27)

The user authorized removal of build data that is clearly unnecessary. A fresh, path-specific check removed five obsolete empty dev-owned run roots:

- `build/add-shared-body-characters_r1_dev_try-226_visual-build-h150/`
- `build/add-shared-body-characters_r1_dev_try-228_visual-build-h190/`
- `build/add-shared-body-characters_r1_dev_try-229_visual-pack/`
- `build/add-shared-body-characters_r1_dev_try-1_verify/`
- `build/add-shared-body-characters_r1_dev_try-184_debug-presentation/`

Before removal, `find` showed no symlinks in any of the five roots and only one file total: a zero-byte log in `try-1_verify`; the other four roots were empty. Project-source/reference scan found no references beyond this inventory's previous candidate note. Full process inspection showed the active try257 host suite, which was not touched; no Blender process was present. These are superseded empty attempts, replaced by later try242/245/247 visual evidence and current try251+ work. All five paths are absent afterward. Removed **5 run roots / 1 zero-byte file / 0 regular-file bytes**; no symlink target was followed and reclaimed disk space is effectively zero.

The inventory's preceding paragraph that listed these as cleanup candidates is historical and resolved by this entry. Current work is preserved: active `try257_host-suite`, final try251 candidate and prepared `try253`–`try255` inputs, reviewer try8 inputs, try206 diagnostic/history and packs, protected old baseline, supplemental BPM90 baseline, and user-visible try121 preview. Other old roots and caches were not removed in this pass; final dependency-aware cleanup remains pending because native and review acceptance for try251 are incomplete. The earlier candidate list must not be read as authorization to remove those unresolved roots.

### Additional cache cleanup (same request)

Also removed the completed per-launch UV cache roots `try-243_cache-h150`, `try-244_cache-h190`, and `try-246_cache-pack`. Immediately before removal, each occupied 12 KiB by `du -sk`, had no symlinks, and no active process referenced its path. The only contents were the empty/cache marker layout; their rendered outputs and reports are retained separately at `try242`, `try245`, and `try247`. No project or build text reference was found. All three roots are absent after removal. Recorded footprint removed: **36 KiB filesystem allocation** (12 KiB per root, rounded by `du`); regular-file payload bytes were not measured before deletion, so this is a disk-usage estimate rather than a payload-byte count. No symlink target was followed.

After this pass, five empty obsolete roots plus three completed per-launch caches were removed. Current try257 completed successfully and is retained; native inputs `try253`–`try255` and planned distinct outputs `try258`–`try260`, aggregate `try261`, final candidate try251, reviewer try8, all protected baselines, try121 and unresolved try206 diagnostics remain untouched. Full cleanup remains pending until the final native/aggregate/review work is complete.

### Superseded large run groups (same user request)

A fresh top-size and dependency pass removed ten older whole run roots that were conclusively superseded:

- `try-178_pack-orchestration` and `try-179_visual-pack`: the corresponding try177 managed-pass render operations are complete, the marker-ID assembly defect was resolved in later packs, and the exact try206 complete pack try247 passed. Their only source references were internal orchestration scripts and the now-updated `native-checks.md`; no current input, baseline, active process, user-visible preview or review requirement consumes these outputs. The root had no symlinks.
- `try-192_pack-orchestration`, `try-193_character-eval-h150`, `try-193_character-eval-h170`, `try-193_character-eval-h190`, and `try-194_visual-pack`: these belong to the try191 pre-R1/R2 visual attempt. The pack and its input evaluations were superseded by try247; no source, retained report, midpoint run, or current try251 input consumed them. `orchestration-status.md` retains the historical result without a broken artifact link. No symlinks were present.
- `try-46_skeleton-native`, `try-47_skeleton-native-check`, and `try-51_skeleton-verify`: this early skeleton-only generation/check pair has no consumer outside its own harness/run records. Its verifier report (`status=fail`, 652 samples) failed only the 32 tempo-coverage checks; later protected full native matrix try79/80/81 and numeric audits try140/141 supersede that incomplete coverage. It is not the protected baseline or user preview. No symlinks were present.

Immediately before removal, `stat` counted **9,106 regular files / 10,590,335,465 bytes** across these ten roots; symlink count was zero. Project source/reference search found only the two historical passages updated above. Build-to-build reference search found only each removed pack's own orchestration artifacts, its own receipts, and the try47 harness referencing try46; all such dependent roots are included in this removal. Process inspection found no active process for any removed root; active final try251 work (host evidence, inputs try253–255 and current H150 output try258) was kept. All ten paths are absent after removal, and no symlink targets were followed. The protected try79–81 baseline matrix, try140/141 audits, try121 preview, try251 candidate, active/resumable native matrix and unresolved try206 review diagnostics were not touched.

## Dangling-link correction and final large-root check (2026-10-27)

A fresh inventory found that `build/add-shared-body-characters_r1_dev_try-185_debug-presentation/` contained exactly four symlinks (`clean-a`, `clean-b`, `stature-150`, `stature-190`) whose absolute targets were the already-removed obsolete try179 visual-pack root. The targets were dangling. The root contained zero regular files and zero regular-file bytes; no target was followed. A no-follow scan of every symlink under `build/` found no inbound symlinks into try185 or the reviewed large debug roots try186–190. Project/source/report search found no references to try185 except this inventory's historical retention note. The only build-side try190 references were self-references in its own `stature-comparison.json`; the retained cleanup scan inventory also records metadata about try186–190 but is not a runtime consumer. Removed the whole try185 root to eliminate those dangling links; post-check confirms it is absent and the four dangling links are gone.

The large debug-presentation roots try186–190 remain retained. Later packaging/debug work exists, but the handoff records try190's successful assembly checks as scoped diagnostic evidence, and the available artifacts do not establish that the earlier large iterations contain no unresolved or user-relevant debug evidence. Their no-follow inventory totals **17,121,650,709 regular-file bytes** across try186–190 (4,121 + 4,145 + 4,168 + 4,168 + 4,172 files respectively). They have no inbound symlinks and no external project/report references beyond the cleanup inventory; this alone is insufficient to prove they are safe to remove. No further large root was removed in this pass. The dangling-link cleanup reclaimed zero regular-file bytes and removed four symlink entries.

## Post-cleanup symlink and size audit (2026-10-27)

After removing try185, a full recursive `os.walk(..., followlinks=False)` scan of `build/` enumerated **401 symlink entries**. Each link was inspected with `lstat`/`readlink`; targets were normalized lexically without resolving symlink chains. **Zero symlinks target an absent direct run-root**, and no remaining target mentions the removed try179 or try185 roots. There are 47 lexical targets outside `build/`, all Python interpreter links from isolated environments/caches; these were reported but not followed or modified. No other dangling references to removed roots were found. `du -sh build` reports **115G** at this audit time (includes active and protected work; the size can change while builds continue).

## Final developer cleanup for candidate try294 (2026-10-28)

After the try294 native/consumer/visual evidence finished, the following empty, obsolete dev-owned run roots were checked individually: `try-265_visual-input-h190`, `try-282_context-tests`, `try-283_candidate-build`, `try-287_verification-tests`, `try-289_host-suite`, and `try-297_host-suite`. Immediately before removal, each root had zero regular files, zero regular-file bytes, and zero symlinks (including symlinked directories); the five try265/282/283/287/297 paths had no matching text references outside their own paths in the project or `build/`, and try289 likewise had no external text references. These attempts had been superseded by the exact try294 candidate evidence; no input/output consumer, protected baseline, user-visible artifact or unresolved diagnostic depended on their empty directories. The earlier try289 interruption remains described as a stale-discovery failed attempt in the handoff, but its empty directory was unnecessary. A process-table check after current evidence completion found no active verification or cleanup process for these roots. Removed all six whole roots with `rmdir`; all six paths are absent afterward. **Removed: 6 roots, 0 regular files, 0 regular-file bytes, 0 symlinks.** No symlink was followed.

The complete `build/` no-follow inventory immediately before removal of the five try265/282/283/287/297 roots counted 617 direct run roots, 171,315 regular files / 205,647,788,614 regular-file bytes, and 235 symlink entries. After removal it counted 612 roots with the same regular file/byte/symlink totals. A post-clean lexical link scan found no source or symlink target referencing any removed root; the full scan recorded 168 lexical targets outside `build/` (primarily isolated-environment interpreter links), which were listed but not followed. No link was followed outside `build/`.

Retained current exact-candidate evidence and dependencies: try294 candidate, try299/304 private uv environments, try300 host suite, try301 package closure, try305 installed acceptance, native inputs try306–308 and successful outputs try311/314/313, aggregate try315, consumer input/build/report try316/319/321, focused preview input/build try317/320. Retained failure/harness diagnostics try302/303, try309/310 and the unresolved try312 process-ownership diagnostic. Protected baselines and the user-visible try121 preview remain unchanged. Reviewer-owned roots were not modified. Other empty roots try120, try122, try134, try167, try217 and try222 remain retained under their earlier explicit protection, dependency or unresolved-attempt reasons. The reviewer still owns its separate review cleanup and visual gate; this developer cleanup has no pending dev-owned removal from the scoped current evidence.
