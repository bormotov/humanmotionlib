# Independent review — add-shared-body-characters

## Final independent assessment — 2026-10-28

**Verdict: PASS WITH NOTES for the independently measured technical scope; human visual Gate 2 is pending.** This verdict does not approve visual correctness or make an incomplete consumer report pass. The requirements/scenarios and their check classes are enumerated in the verification checklist below; the dated continuation is historical evidence, not the current status. The identity-bound evidence below is for candidate try294 only.

- Submitted wheel SHA-256 `3aa76e1b2aab46963eb2c168c917d8cf85817557d6d2ef5307a99175e1d13fbd`; runtime manifest SHA-256 `7f21ef2ff07c9ebf3ef63e08bd8269dc5a9720de34380c6996a833ee80449454`. The wheel hash was independently rechecked in `build/add-shared-body-characters_r1_reviewer_try-14_final-check/standalone-identity-audit.json`; the package rebuild, byte closure and manifest checks are in reviewer try11/try12 evidence below. Documentation-only changes after freezing are not represented as a new package identity.
- Installed source/schema validation returned `valid-sources`: 180 structures, 67 actions, 3 placements and 32 diagnostic fixtures. Host tests passed 380 with 7 explicit installed-harness skips; those 7 passed separately in the installed harness. See `build/add-shared-body-characters_r1_reviewer_try-12_host-check/`.
- Independent installed verifier on reviewer-owned three-height constructions returned a **complete** aggregate numeric pass: 5,714,431 measurements, 32 diagnostics at each of H=1.50, 1.70, 1.90 m, 60/60 native midpoints per body and no matrix failures. Evidence: `build/add-shared-body-characters_r1_reviewer_try-12_numeric-matrix/metrics.json` and scalar summary in reviewer try12 host-check. Worst observed native residual 1.06649e-6 m, minimum surface floor -1.68086e-7 m and maximum sole distance 1.66521e-7 m; strictest H=1.50 m limits are 1.5e-5, -1.5e-4 and 1.5e-3 m respectively. See the detailed result below for scope, dense coverage, positive controls and provenance of the uv-only environment.
- The separate consumer-motion report `build/add-shared-body-characters_r1_reviewer_try-12_consumer-check/metrics.json` is **not an aggregate pass**: its top-level status and numeric status are `fail`, with failed diagnostic fixture coverage (32 missing) and tempo coverage (one observed tempo); the character matrix is incomplete because H=1.50 and 1.90 m are absent. All 17 supplied H=1.70 samples pass their scoped sample checks and native/dense character checks. Rendering is `not-run`, visual is `not-assessed`. The complete three-height diagnostic aggregate above is a different report; it does not change the consumer report's status. This limited custom-input result is consistent with the consumer-specific verification scope and is not evidence of complete diagnostic coverage.
- Independent visual packs are `build/add-shared-body-characters_r1_reviewer_try-12_visual-pack/index.html` and the distinct try13 pack. All 1,044 cross-pack clean images matched in decoded RGBA; camera/floor/light scene properties matched across three stature scenes. A new independent parser rechecked the primary standalone pack: 12 HTML pages, 1,377 local links and no missing or escaping targets; output in reviewer try14 `standalone-identity-audit.json`. The fixed scene audit compares configured world matrices and settings; pixel comparisons are separate evidence.
- Provenance/clearance: the reviewer inventory resolved 770 provenance records and 14 inherited materials. See reviewer try5 `clearance-review.md` for the checked scopes, conditions and limitations of live retrieval; no additional external surface reference was used. Kudzia and Kasahara are attributed by author/title/DOI in `THIRD-PARTY-NOTICES.md`, although their literal material IDs do not occur there. Some unchanged publishers could not be re-fetched live; the audit does not claim otherwise.

### Final reviewer-owned cleanup record

The original owner checked its own obsolete runs and removed these six whole roots (prefix `build/add-shared-body-characters_r1_reviewer_`), totaling **4,200,255,633 regular-file bytes**, counted before the first deletion pass:

| Root suffix | Regular bytes |
|---|---:|
| `try-9_numeric-h150` | 4,042,845,369 |
| `try-10_candidate-check` | 23,301,479 |
| `try-10_fault-build` | 27,098,156 |
| `try-10_fault-check` | 105,287,764 |
| `try-10_fault-input` | 1,452,283 |
| `try-10_host-check` | 270,582 |

Before removal there were no matching active processes and no inbound symlinks from outside these roots; four symlinks were internal to an obsolete environment/cache. The first pass encountered self-imposed read-only environment directories; the owner restored permissions only inside its own root and completed removal. A post-removal no-follow scan found zero external inbound symlinks and confirmed all six roots absent. The owner checked references and retained the historical outcomes in this record, with final-candidate replacements available. Inventory and completion record: `build/add-shared-body-characters_r1_reviewer_try-12_host-check/superseded-runs-inventory.json` and `superseded-cleanup-result.json`. No cleanup remains pending from this operation.

The owner of try6–8 additionally removed three obsolete try251 visual preparations (same reviewer prefix): `try-8_visual-input-h150` 4,232,909 bytes, `try-8_visual-input-h170` 27,071,130 bytes and `try-8_visual-input-h190` 4,218,480 bytes, totaling **35,522,519 regular-file bytes**. Before removal no matching reviewer try5–8 or related Blender/verifier process was observed, internal symlinks were zero, and a no-follow scan found zero inbound symlinks. After removal all three roots were absent and inbound links remained zero; no review.md text pointed to those exact removed paths. Owner retained try5 inputs/host as dependencies of try6, try6 numeric/visual/aggregate for the documented R3 diagnostic and historical evidence, try7 for diagnostic freeze, and try8 candidate/numeric inputs for `independent-matrix.json` and the scoped audit. No pending cleanup was reported for those three removed roots.

The original owner independently inventoried its 20 early try1–5 roots, totaling 1,350,686,445 regular-file bytes, and removed **0 roots / 0 bytes** because each has a recorded dependency or protected diagnostic purpose. Before/after inventories match; a no-follow build-wide scan found no external inbound symlinks and process inspection found no matching processes before or after. Exact per-root reasons and revisit triggers, inventories and procedure: `build/add-shared-body-characters_r1_reviewer_try-15_early-cleanup/cleanup-result.json`, `inventory-before.json`, `inventory-after.json` and `audit.py`. The try1 check and try2/3 preserve original R1/R2 evidence; try4 is linked by try6 outcomes; try5 host contains the cited current source-clearance review and its inputs are linked by try6 outcomes. The try1 stature inputs are linked from the retained try1 check's `numeric-inputs.json`; retaining those inputs does not promote them to native acceptance evidence. The owner reported no pending cleanup in its scope.

Retained: reviewer try11 native/input/package/fault results, try12 environment/host/numeric/consumer and visual pack, try13 independent comparison pack, and reviewer try14 standalone link/identity audit: these are required for frozen identity, reproducibility, diagnostics or the pending human visual gate. The protected historical baseline and other agents' roots were not removed. Earlier partial cleanups and byte counts are recorded chronologically below; they do not overlap the six roots above. Reviewer-owned dependency-aware cleanup is complete for the inspected owners; retained roots have concrete evidence dependencies or revisit triggers, and no failed or interrupted cleanup remains pending in their scopes. Any developer-owned cleanup remains that owner's responsibility and is not represented as completed by this review.

### Findings disposition

| ID | Original severity / requirement and scenario | Final independent disposition and evidence |
|---|---|---|
| R1 | Major — Surface variants reuse one construction and binding contract / Verify surface sharing | Corrected; shared template and bounded appearance differences checked on try294; host and complete numeric evidence above. |
| R2 | Major — Characters are first-class selectable library outputs / Select each character independently | Corrected; skeleton-only construction, selection and missing surface collection audit pass on try294. |
| R3 | Major — Authored appearance has a frozen testable dossier / Measure and visually identify the authored characters | Corrected numeric stature scaling; independent complete three-height aggregate passes. Visual identification remains a human decision. |
| R4 | Minor — Public generation API documentation and supported construction modes | Corrected in try294; installed host/API mode coverage passed. |
| R5 | Major — Supporting surfaces preserve contact and floor constraints / Check the sole beyond a rest-pose appearance | Corrected diagnostics reproduced using independent synthetic topology, stale, floor and sole faults; matching unmodified control exists in the full try294 aggregate. Synthetic failures are not claims about accepted native output. |

No unresolved measured technical finding is asserted above. The checklist's **H** parts are unverified until the human reviews the pack. Suggested visual review: inspect neutral front/side silhouettes, shoulder/waist/hip and joint close-ups, squat and walking GIF/onion-skin transitions, forefoot rocker and sole contact, and the three-stature comparisons. The reviewer observed subtle surface differences and no obvious fixed-scene shift at the displayed scale; the small figures require zoomed inspection and this observation is not visual approval.

## Historical final-candidate continuation — reviewer try9 onward

### Corrected package try294 — chronological review record

The reviewer independently rebuilt frozen try294 (submitted wheel SHA-256
`3aa76e1b2aab46963eb2c168c917d8cf85817557d6d2ef5307a99175e1d13fbd`,
runtime manifest `7f21ef2ff07c9ebf3ef63e08bd8269dc5a9720de34380c6996a833ee80449454`):
direct/sdist/rebuilt logical closure matched all 116 files and canonical
sources in `build/add-shared-body-characters_r1_reviewer_try-11_candidate-check/`.
Separate reviewer full inputs at all three heights each contain 900 samples;
focused visual inputs are independently prepared (171 at H170, 18 each at
H150 and H190). A fresh neutral-only supervised build was used to rerun four
synthetic full-verifier diagnostic faults in
`build/add-shared-body-characters_r1_reviewer_try-11_fault-check/`: topology,
stale request, floor and detached sole all produced the required context. The
floor case measured -0.001000089 m versus -0.00017 m; the sole case measured
0.009999925 m versus 0.0017 m. These are intentionally synthetic cases with
consistent test receipt inventories, not accepted native output. The full
independent H150 native run is in progress; the remaining numeric, host,
visual and human checks are pending.

The H150 native run subsequently completed with supervised `succeeded`, 900
delivered samples and 60 midpoint samples in
`build/add-shared-body-characters_r1_reviewer_try-11_numeric-h150/`. A fresh
independent H170 build has started. This remains a construction-only result;
numeric, complete matrix, visual and human checks are not yet established.

The reviewer subsequently completed the independent H170 and H190 native
construction runs under `..._reviewer_try-11_numeric-h170/` and
`..._reviewer_try-11_numeric-h190/`. Each supervised build receipt is
`succeeded`, exit 0, with output validation `pass`; all three each delivered
900 samples and 60 native midpoints. They used the reviewer try11 venv,
created with `uv venv` and with the reviewer-built wheel installed by uv;
its dependencies were copied with byte-hash verification from the existing
environment. They remain construction results, not numeric acceptance.

The human subsequently requested that newly created environments be created
and populated with uv without copying. The new separate
`build/add-shared-body-characters_r1_reviewer_try-12_environment/venv/` was
created with `uv venv`, independently rebuilt wheel installed with `uv pip`,
and all seven locked dependencies installed with `uv pip --offline` from the
existing uv cache. `uv pip check` passed eight packages and runtime integrity
confirmed manifest `7f21ef2ff07c9ebf3ef63e08bd8269dc5a9720de34380c6996a833ee80449454`.
All imported package and dependency origins resolve inside this new venv.
The 378 non-pycache files across HML and seven dependency trees were compared
with try11: zero differences. No earlier result or receipt was reassigned to
the new environment. Future independent host/numeric/visual checks will use
the uv-only environment; numeric, visual and human verdicts remain pending.

The independent full host suite on the uv-only try12 environment completed
with 380 tests, zero failures/errors and seven explicit installed-harness
skips in 1,034.93 s; the frozen source snapshot remained unchanged. The seven
installed-only checks passed separately 7/7 in the reviewer-owned decoy
workspace. Independent source/schema/nested provenance inventory passed for
14 inherited material references and 770 provenance records. Evidence:
`build/add-shared-body-characters_r1_reviewer_try-12_host-check/host-tests.json`,
`installed-tests.json`, `source-provenance.json`, and accompanying logs.
These are host/package results, not native, visual or human acceptance.

The independently built wheel contains 124 files: 116 under the
`humanmotionlib/` runtime tree and eight dist-info files (including RECORD).
The runtime tree comprises 50 Python implementation files, 64 canonical
resources and two runtime metadata files. This matches the developer's
independent 124/116/50/64 inventory; archive byte hashes need not match
because of build metadata.

### Independent three-stature numeric matrix — try294

The reviewer ran the ordinary installed `verify-skeleton --numeric-only`
entry point with `--action-coverage --dense-floor --stature-builds` on its own
three complete try11 native builds. The exact report is
`build/add-shared-body-characters_r1_reviewer_try-12_numeric-matrix/metrics.json`.
It completed `status=pass`, `numeric_status=pass`, 5,714,431 measurements,
with `matrix_complete=true`, no matrix failures, all three leaf numeric
statuses `pass`, and the evaluated cross-stature comparison `pass`. Required
and observed statures are 1.50, 1.70 and 1.90 m. All three generation and
verifier identities match manifest
`7f21ef2ff07c9ebf3ef63e08bd8269dc5a9720de34380c6996a833ee80449454`;
each registry contains skeleton, male and female with no missing/extra IDs.
Each leaf reports 60 expected and 60 observed native midpoints per body.
The input preparations contain 900 samples and 32 fixtures per stature.

A streaming scalar audit of the large report (not a second verifier) found
maximum recorded native residual 1.06649e-6 m, minimum recorded floor
-1.68086e-7 m and maximum recorded sole distance 1.66521e-7 m. Even the
strictest absolute bounds at the smallest H=1.50 m are respectively 1.5e-5 m,
-1.5e-4 m and 1.5e-3 m. The report's own per-stature checks use each height's
actual H and remain authoritative (`numeric-scalar-summary.json`). Dense
floor and squat-balance steps passed, including 2,181 squat-balance samples
per height. Rendering was deliberately `not-run` for this numeric command and
human visual acceptance was not assessed.

The full, unmodified aggregate is also an independent positive control for
the synthetic fault branches: the exact-candidate input at each height has
both `neutral/00000` and `walking-in-place/00000` at beat 0, matching the
reviewer and developer fault fixtures; the six walking-in-place rows are
present for male/female across the three successful native leaves. Identity,
fixture, beat and sample evidence are recorded in
`..._reviewer_try-12_host-check/control-coverage.json`. The negative synthetic
reports retain their own altered paths and are not relabeled as native output.

### Independent visual comparison — try294

Two separate reviewer-owned complete comparison packs were generated from the
reviewer's fresh try294 focused preparations and evaluated builds, using the
uv-only try12 installation:
`build/add-shared-body-characters_r1_reviewer_try-12_visual-pack/index.html`
and `build/add-shared-body-characters_r1_reviewer_try-13_visual-pack/index.html`.
Each pack's coverage, baseline, character regression, within-pack clean-pass
repeatability, stature, GIF timing and complete-pack reports passed. Each covers
171 samples and the three registered characters, with 192 character composites
plus four stature strips, 54 GIFs, and 12 HTML pages. Arm raise and squat each
contain 17 animation and five count samples; walking contains 33 and nine.
Each pack has default/explicit skeleton and male/female singleton passes in
addition to two separately managed clean batch passes. Historical baseline
was the protected supplemental BPM90 render under its own pre-change identity.

Each pack reports 1,044 exact decoded-RGBA clean-pass comparisons and 1,552
default/explicit/batch/singleton/baseline comparisons, with no failures.
The separately authored cross-pack audit compared all 1,044 clean-a decoded
RGBA images from the two disjoint pack roots: zero pixel differences
(`..._reviewer_try-12_host-check/cross-pack-pixels.json`). Independent HTML
parsing of each pack found 12 pages and 1,377 local links, with zero missing
or escaping targets (`visual-link-audit.json`, `visual-link-audit-pack2.json`
in the same host-check run). The pinned Blender scene audit compared the
world matrices and settings of six cameras and Floor, plus render engine,
shading, resolution and color settings, across all three saved reviewer
stature scenes: exact equality (`scene-audit-expanded.json`). The selected
surface collections and skeletal/control collections could be toggled
independently in the saved H170 scene without saving modifications
(`collection-audit.json`). A fresh skeleton-only no-image construction and
headless saved-scene inspection found no surface collections or surface
objects while preserving skeletal geometry (`skeleton-only-audit.json`).

Reviewer visual observation is not acceptance: the two featureless silhouettes
show modest torso-shape differences while the skeleton remains a separate
representation. Squat and forefoot rocker appear synchronized in the viewed
front/side sheets, with no obvious scene shift at their displayed scale; the
figures are small, so the human should inspect the joint and sole close-ups as
well as GIFs/onion skins. Human Gate 2 remains explicitly pending.

The four disposable synthetic fault case directories `topology`, `stale`,
`floor` and `sole` under `..._reviewer_try-11_fault-check/` were removed after
the successful assertions: 104,441,913 regular-file bytes, zero internal
symlinks. A no-follow scan before and after found zero inbound symlinks. The
independent neutral native source run, test scripts and fault result JSONs
remain, allowing exact regeneration; no accepted or other agent's run was
touched. This is partial cleanup only. Complete review cleanup remains pending
until the aggregate and any unresolved findings have finished.

After the corrected candidate's independent matrix passed and its diagnostic
faults were reproduced, ten obsolete reviewer-owned roots were removed:
`try-9_control`, `try-9_host-check`, `try-9_numeric-h170`,
`try-10_numeric-h150`, `try-10_input-h150`, `try-10_input-h170`,
`try-10_input-h190`, and `try-10_visual-input-h150/h170/h190` (all prefixed
`build/add-shared-body-characters_r1_reviewer_`). The inventory at
`..._reviewer_try-12_host-check/obsolete-runs-inventory.json` records each
path and byte count: 460,888,683 regular-file bytes total. The old H170 and
H150 build receipts recorded `cancelled` / -15 after coordinator-initiated
interruptions, not successful builds; their triggering findings are fixed
and reproduced by the final candidate. The obsolete try251 host source audit
is superseded by the try294 source/provenance audit. Current reviewer native,
packs, scripts, fault reports, candidate and protected baseline were retained.
Before removal there were zero internal or inbound symlinks and no matching
active process; a no-follow scan after removal found zero inbound symlinks.
This does not yet claim complete reviewer cleanup: consumer verification is
still running and current evidence must remain available through the human
gate.

### Corrected diagnostic context — try286, scoped fault audit

The reviewer independently rebuilt try286 (submitted wheel SHA-256
`eb1097d1c4943993ae03ca30c066252e8524a9d9050bdb04908774f7fea8d6b6`, manifest
`1f6a45f29018d07d71cec82b123c3256a8a339f0dc02575fbef1cd160d35134f`).
Direct wheel, sdist and rebuilt wheel match the submitted candidate and
canonical sources on 116 logical files. Fresh, independent neutral-only
construction in the former reviewer try10 fault-build returned successful supervised build/postflight; that obsolete run has since been removed after the final candidate reproduced the scoped checks. This is a single-sample
test construction, not the required complete native matrix.

The reviewer confirmed a separate documentation discrepancy in
`docs/character-models.md`: its unqualified claims that `images=False` builds
produce evaluated geometry and `render_only=True` produces images do not
describe the supported combination `images=False, render_only=True`, which
returns no images and no evaluated geometry (see `tests/test_api.py`,
`test_no_image_build_modes_and_prepared_path_input`). Since correcting the
packaged documentation changes the package identity, the reviewer stopped
its own try286 H150 full build with Ctrl-C: launcher exited 130 and its receipt
records cancelled/-15; no matching process remained. The try286 inputs, archive closure and scoped fault checks were historical evidence and are not final-candidate results; obsolete owned roots were later removed as recorded in the cleanup section.

Four independent synthetic full `verify_character_output` fault cases were run under the now-removed reviewer try10 fault-check; final-candidate equivalents are retained in reviewer try11 fault-check.
They copy that reviewer-owned real output into disposable cases and recompute
receipt output inventories for the intentionally changed synthetic files;
they do not claim that the synthetic in-memory pose was a sealed preparation.
No verifier or oracle is mocked. A forged vertex ID yielded a topology failure
identifying male, neutral, beat 0, component and missing/extra IDs; a stale
prepared hash yielded request artifact, field and expected/observed SHA-256,
with beat not applicable. A coherent -0.001 m synthetic world translation
yielded floor-bound failures for both bodies, measured minimum -0.001000089 m
against -0.00017 m. A synthetic calcaneus.L anchor-carrier offset, leaving
skin carrier frames and vertices unchanged, yielded sole-contact failures for
both bodies at heel.L, measured 0.009999925 m against 0.0017 m. Each failure
contains its fixture and authoritative beat 0. These checks address the
previous diagnostic-context finding only; they do not establish complete
native/dense, determinism, rendering or human visual acceptance.

The present reviewer resumed the independent review of frozen try251. The
reviewer-owned try8 package reconstruction and preparations are retained;
the installed runtime manifest remains `de3ffa80c5f0622b7a0bb7ab7fd9d8186da28c4f4268d6fbe55346528a857b93`.
The source and nested provenance audit was repeated with the reviewer-installed
try251 package in the since-removed obsolete reviewer try9 host-check run:
source/schema validation passed, 14 inherited materials and 770 provenance
records resolved. The full host suite and H170 native build were subsequently
interrupted, not accepted; no numeric, image or human verdict follows from
this historical audit. The separate reviewer H=1.50 m native build
in the former reviewer try9 numeric-h150 root returned supervised `succeeded` after 900 delivered and 60 midpoint samples; its root was subsequently removed and its result is historical construction evidence only.

The architect subsequently confirmed a diagnostic-context defect against the
approved character-models requirement: native delivered floor/contact failure
messages do not consistently include beat, measurement and bound. Correction
changes the packaged verifier and package identity. At coordinator direction,
the reviewer stopped its own in-progress try251 H170 build and host suite with
Ctrl-C; the H170 receipt records cancelled/-15 and both launcher sessions
exited 130. A process-list check found no remaining matching reviewer process.
Neither interrupted run is a pass. The completed H150 try251 build and source audit are scoped historical results; their obsolete roots were later removed. The H170 receipt and interrupted host
log were later removed as resolved diagnostics after final-candidate checks;
the cancellation outcomes are retained in this review record.

## Historical status checkpoint

At this checkpoint, review was in progress on corrected try294. Independent package, host, complete
three-stature numeric and two visual packs have passed within the scopes
recorded above. Independent consumer-motion reconstruction and final
dependency-aware cleanup remain in progress. No final verdict or human visual
approval is recorded.

### Historical status — try206 (superseded)

R1 host/source correction passed independently on try196, and R2 small actual
default/reuse compatibility plus negative checks passed independently on
try206. Final frozen try206 host/package/source/installed checks are complete;
full native/character-pack review and human Gate 2 remain pending. Earlier snapshot findings below
are retained with their exact identities, not relabeled current evidence.

The then-reviewed source was frozen submitted candidate try206, version 0.3.0.
The reviewer independently rebuilt the canonical checkout into direct wheel,
sdist and rebuilt wheel in
`build/add-shared-body-characters_r1_reviewer_try-4_r2-check/`.
All 116 logical package files match canonical bytes and the submitted wheel;
the archive byte hashes differ legitimately with build metadata. Reviewer
direct/rebuilt wheel SHA-256 is
`76f7224d46824bd93270a993e68740c77f99adb1941bf4027137c9a74d6d8bd8`.
Reviewer sdist SHA-256 is
`88c87767440facf1c31417418fa8c811739f8d4a30a3f4409d4439b4157bd179`.
Runtime manifest SHA-256 is
`739c6f975d2e7f04fb05dbfd2a6984a1d86667d96ab587697ec397bae7836573`.
The manifest covers 50 Python implementation files and 64 canonical resources.

The private CPython 3.14 environment contains the reviewer's own non-editable
wheel and offline, hash-checked dependencies from the lock. HML and dist-info
are read-only. The final full host suite completed with 372 tests: 365 passed,
zero failures/errors, and seven explicit installed-harness cases were skipped.
Those separate installed cases passed 7/7. The runtime source snapshot remained
unchanged throughout the full run. Native construction is waiting only for the
developer's sequential matrix to release the shared Blender slot.

## Verification checklist

Types: **A** = automatable host/source/package contract; **N** = native or
numeric measurement; **H** = human visual decision. Items are evaluated against the recorded technical evidence; H portions remain pending
until the human visual decision. Developer logs do not establish
reviewer acceptance.

### Character models

| Requirement / scenario | Type | Independent check |
|---|---|---|
| Characters are first-class selectable library outputs / Select each character independently | A,N | Installed selection matrix, scene inventory, default skeleton laziness |
| Character definitions are canonical declarative sources / Reconstruct and reject character data | A | Closed schemas and hostile source-copy fault matrix before writes/probe |
| All current characters share skeletal movement semantics / Compare the common movement across characters | A,N | Exact shared source/pose/timeline identities; all native frames; consumer squat |
| Surface variants reuse one construction and binding contract / Verify surface sharing and separate inspection | A,N | Shared vertex/face/weight identities; independent scene collections |
| Authored appearance has a frozen testable dossier / Measure and visually identify the authored characters | N,H | Independent table/ring/extrema/slice measurements at three heights; silhouette decision |
| Surface deformation follows the common posed skeleton / Verify deformation throughout existing movement coverage | N | All delivered vertices and nonempty native midpoint schedule versus independent DQ oracle |
| Supporting surfaces preserve contact and floor constraints / Check the sole beyond a rest-pose appearance | N | Full-vertex minima, dense <=0.01-beat audit, actual posed sole-to-anchor and skeletal sliding |
| Character rendering preserves deterministic fixed-scene output / Compare singleton, batch and repeated output | N | Exact decoded RGBA comparisons, native vertices <=1e-6H, fixed scene matrices |
| Common library changes propagate through the registered set / Demonstrate single-source edits and isolated appearance edits | A,N | Disposable shared key/radius/female waist source-copy checks and complete membership |
| Bind-significant skeletal changes require coherent compatibility renewal / Reject a stale bind instead of drifting silently | A | Shoulder-rest mutation rejected for surfaces without requiring a surface for skeleton |
| Appearance and future body proportions remain separate concerns / Inspect the extension boundary | A | Closed data dependencies and unsupported selector rejection |
| Character provenance and reference clearance remain resolvable / Audit original surfaces and inherited attribution | A | Every nested source/material/license resolves; register and notices audit |
| Independent character review precedes visual acceptance / Review the shared character set | A,N,H | Own clean evidence and standalone pack; separate explicit human Gate 2 |

### Public generation API

| Requirement / scenario | Type | Independent check |
|---|---|---|
| Public generation has a small importable contract / Import and call from a Python application | A | Installed no-side-effect import/signature tests outside checkout |
| Rendering returns complete validated image results / Render a prepared subset | A,N | Pinned native image inventory/decoding and exact pose/time joins |
| Rendering returns complete validated image results / Preserve existing construction modes | A,N | No-images and render-only inventories; incompatible options before launch |
| Rendering returns complete validated image results / Render a complete character batch | A,N | Full explicit membership, typed result joins, singleton pixel parity, batch faults |
| Generation exposes resolvable provenance / Follow generated-data attribution | A | Source/result/license/register traversal |
| Generation exposes resolvable provenance / Follow a consumer variant's inherited attribution | A,N | Sealed consumer lineage survives deletion of original caller source |
| Generation exposes resolvable provenance / Reject uncleared new reference use | A | Material inventory and exact commercial derivative basis |
| Generation exposes resolvable provenance / Follow appearance and inherited skeletal attribution | A | Selected closure and portable union of character/consumer/profile provenance |
| CLI generation delegates to the public contract / Compare Python and command callers | A,N | API/console/module equivalence, paths, finite deadlines/cancellation and failure class |
| CLI generation delegates to the public contract / Compare explicit and omitted character selection | A,N | Default/explicit/single/batch matrix and invalid-selection preflight |
| Public results have a documented portable projection / Consume and serialize a result safely | A | Standard JSON, deterministic order, exact fractions and deep mutation isolation |
| Public results have a documented portable projection / Join consumer poses with existing result types | A,N | Consumer fixture IDs and lineage preserve all timeline/image joins |
| Public results have a documented portable projection / Join several appearances to one exact timeline | A,N | No duplicated pose IDs; registry order; per-character image joins and detached projections |
| API integration preserves generation output and visual review / Compare API generation with the existing workflow | N,H | Own clean focused pixels/geometry versus immutable historical baseline; human pack |
| API integration preserves generation output and visual review / Preserve default behavior while reviewing the added characters | A,N,H | Existing skeleton/workspace semantics, separate surface/numeric/render/human verdicts |
| Render character selection is validated and integrity-bound / Validate selection before allocating output | A | String/empty/duplicate/unknown/incompatible/schema/bind faults without writes/probe |
| Render character selection is validated and integrity-bound / Reject render selection substitution | A,N | External expected seals, source closure, receipt/manifest replacement/reseal faults; isolated backend imports |

### Python distribution

| Requirement / scenario | Type | Independent check |
|---|---|---|
| Supported generation resources are complete / Audit both distribution resource closures | A | Independent direct/sdist/rebuilt logical and canonical bytes |
| Supported generation resources are complete / Reject an incomplete or altered installation | A | Disposable missing/corrupt resource/implementation copies fail before backend |
| Supported generation resources are complete / Audit the complete character resource closure | A | All descriptors/template/presets/schemas/docs/host/backend present; no generated assets/downloads |
| Packaging preserves generation output / Compare the package regression pack | N,H | Two own focused wheel renders, baseline geometry/pixels, exact timing and human review |
| Packaging preserves generation output / Generate all characters from an installed artifact | A,N,H | Read-only installed API/CLI, complete source/numeric/image identities, parity and independent human gate |

### Numerical dossier and presentation acceptance

- All 32 diagnostics, BPM60/120/180 and all three heights must be independently regenerated; scoped developer builds do not satisfy this gate.
- Source expansion tolerance 1e-9H; native rest/ring/extrema and DQ tolerance 1e-5H; waist/hip slice tolerance 1e-4H.
- Canonical weights sum within 1e-12, native weights within 1e-6, at most two influences; triangle area strictly greater than 1e-12H squared.
- Every surface vertex z >= -1e-4H; actual posed sole-to-contact anchor distance <=1e-3H; original skeletal contact/frame limits remain unchanged.
- Verify the approved hindfoot-to-MTP blend band 0.065H..0.075H, not the superseded band.
- Native undelivered key midpoints must be nonempty in the BPM60 matrix and independently reconstructed; no YAML/schema dependency injected into Blender.
- Dense grid includes delivered/key/contact events with spacing <=0.01 beats; separate native/dense scopes and worst IDs/values.
- Three-height numeric aggregate must preserve the complete expected height/fixture/BPM/character membership and source/package identity.
- Consumer squat depth 60 degrees/BPM90, appearance-independent, with source lineage and actual native geometry.
- Focused visual H=1.70/BPM90: neutral/rest; arm-raise and squat 17 animation/5 count samples; walking33/9; rocker and all required shoulder/forearm/knee sweeps.
- Full historical baseline join: exact `(fixture, Fraction beat)` for all69 core samples, independent old/new IDs and views; no counts-only intersection.
- Standalone pack: three-character sheets, silhouettes/joint centers, GIF timing, onion skins, joint/sole close-ups, three-height neutral/squat-bottom strips, local links and complete inventory.
- Independent repeated batches, singleton/batch and default/explicit/batch skeleton decoded pixels must be exact; native repeat vertices <=1e-6H; no byte-identical .blend requirement.
- The reviewer will inspect images and state observations as opinion; silhouette identity, readable motion, continuous junctions and planted feet require the human's explicit decision.

## Evidence recorded so far

- `build/add-shared-body-characters_r1_reviewer_try-1_check/package-audit.json`: independent archive/source closure PASS.
- `build/add-shared-body-characters_r1_reviewer_try-1_check/source-snapshot.json`: frozen canonical source hashes.
- `build/add-shared-body-characters_r1_reviewer_try-1_check/dependency-copy.json`: locked offline dependency hashes.
- `build/add-shared-body-characters_r1_reviewer_try-1_check/installation.json`: own non-editable wheel/interpreter/installed hash inventory.
- `build/add-shared-body-characters_r1_reviewer_try-1_check/host-tests.json`: full host suite, 364 tests, zero assertion failures, one error (R2), seven expected installed-harness skips, 713.857 seconds; natural private interpreter, unchanged source snapshot.
- `build/add-shared-body-characters_r1_reviewer_try-1_check/installed-tests.json`: explicit installed acceptance PASS 7/7 in 41.966 seconds from a valid decoy CWD, no Blender and no package mutation.
- `build/add-shared-body-characters_r1_reviewer_try-1_check/source-provenance.json`: source/schema and nested register inventory PASS, 32 diagnostics, 14 inherited materials, 770 provenance records. Live permission and attribution review is separately scoped below.

## Findings

| ID | Severity | Requirement / scenario | Evidence | Suggested direction |
|---|---|---|---|---|
| R1 | major, corrected and independently verified for provisional try196 host/source scope | Surface variants reuse one construction and binding contract; frozen design §4.2 | Original try191 used separate absolute torso tables rather than the required base/delta representation. The scoped independent follow-up below verifies template `radius_h` plus appearance `torso_radii_delta_h`, frozen shapes, propagation/isolation and fail-closed invalid inputs. | Preserve this correction in the unified final candidate and renew package-bound native/render review; the scoped host result is not final acceptance. |
| R2 | major, corrected and independently verified for scoped try206 compatibility | Character rendering preserves deterministic fixed-scene output; public API/CLI backward compatibility; design §7 normal skeleton-only/default workflow | Original try191 omitted the API creation claim; actual try199 then exposed the sealed-request inventory omission and operation-unfiltered receipt discovery. The separate try206 actual/default/reuse and host negative matrix below now pass. | Preserve strict claims, complete-union equality and operation-specific receipt checks in the unified final snapshot; full host/native/character review remains required. |
| R3 | major, corrected and independently verified on try294 | Design §7, three-stature numeric matrix | Reviewer try206 matrix reported incomplete because scaled metre-valued mobility/diagnostic fields were compared as identical. Try294 canonical-scaling comparator, negative cases and full independent three-stature aggregate now pass. | Preserve exact source/package identity and stature scaling; do not infer pass from individual leaf reports. |
| R4 | minor, corrected on try294 | Character review-pack documentation / supported generation modes | Try206 examples passed `input.json` where the CLI requires a run directory; try286 docs also made unqualified claims about `images=False` and `render_only=True`. Current examples and mode descriptions match the checked contract. | Keep examples and documented image/evidence distinctions aligned with API/CLI. |
| R5 | major, corrected and independently verified on try294 | Character models / supporting surfaces / check the sole beyond a rest-pose appearance | Earlier delivered native floor/contact failures omitted authoritative beat or measured/bound context. Independent try11 synthetic full-verifier cases now exercise topology, stale identity, floor and detached sole; try12 complete numeric matrix provides unmodified neutral and walking beat-0 positive control. | Preserve fail-closed behavior, character/fixture/beat/vertex-or-anchor and measured/bound diagnostics without changing tolerances. |

The original archive tests alone do not establish numeric/render/human acceptance.
R2 was independently reproduced using only the reviewer's installed wheel,
without importing the canonical review-pack module or launching Blender:
`build/add-shared-body-characters_r1_reviewer_try-1_check/reproduce-default-pack.json`.
Both module origins are inside the private reviewer venv; the backend probe
was not reached and `clean-a` was not created.
The submitted developer handoff still names older try177 and requires final reconciliation with try191; this is tracked as pending process documentation rather than a final verdict.

## R1 independent follow-up — provisional try196

This follow-up is HOST/SOURCE ONLY. R2 and the full final-candidate native/render
review remain open. No developer test harness, acceptance output or native mesh
was reused. Fresh run:
`build/add-shared-body-characters_r1_reviewer_try-2_r1-check/`.

The reviewer independently rebuilt direct wheel, sdist and rebuilt wheel from
the frozen canonical sources. Their 116 logical package files match one
another, canonical bytes and the submitted provisional wheel SHA-256
`cff54359a150cc91f5cb46e5712b6631424366461b7866c3a5eb5fe0d3694b8b`.
Runtime manifest SHA-256 is
`63351e7294bf3820c7209fc19076024b891cb95204ad2fa9cad4b93773e53048`.
Checks ran using the reviewer's own non-editable read-only wheel/private
interpreter. The canonical runtime source snapshot remained unchanged.

Reviewer-authored checks passed **7/7 in 6.734 seconds**:

| Check | Independent result |
|---|---|
| Actual shared source representation | All 10 shared template rings own positive `radius_h` pairs; appearances contain only required signed delta pairs; male deltas all zero; all frozen female pairs match the approved dossier. |
| Frozen control rings at three heights | All 1920 literal control-ring vertices at H=1.50/1.70/1.90 checked; maximum normalized residual `1.8504e-17H` versus bound `1e-9H`. |
| Unchanged analytic geometry | Compared 55776 vertices at three heights against the reviewer's independently built prior try191 analytic source, not developer meshes; maximum normalized change `2.0688e-17H`; component/vertex/face IDs, material assignments and weights exactly unchanged. |
| Common torso edit | Physical disposable source-copy base waist rx +0.001H propagated to both variants at all 3 heights; every affected/interpolated vertex checked; other components, topology, weights, appearances and skeleton closure unchanged. |
| Female isolation | Physical disposable female delta +0.001H changed only female torso at all 3 heights; all expected vertex displacements, unchanged other components/topology/weights and unchanged male/skeleton closures checked. |
| Invalid inputs before allocation/backend | All 12 physical source-copy cases rejected before output creation, allocation boundary or backend call: zero/negative effective radius, NaN/Inf delta/base, zero base, malformed delta count/shape, nonzero male delta, legacy absolute table and legacy radii_source. |
| Packaged docs/schema closure | Canonical and packaged character docs/schema bytes agree; delta/base fields required; legacy absolute/source fields closed; no fallback documented or accepted. |

Evidence: `package-audit.json`, `source-snapshot.json`, `r1-tests.log`,
`r1-tests.json`, and the independent reproducible `check_r1.py` in that run.
Command:

```text
uv run --no-project build/add-shared-body-characters_r1_reviewer_try-2_r1-check/environment/bin/python build/add-shared-body-characters_r1_reviewer_try-2_r1-check/check_r1.py
```

The retained old reviewer191 wheel is a concrete dependency of the analytic
regression check. No native Blender work, full host rerun or final visual
approval is claimed by this provisional result.

## R2 independent actual smoke — docs-inclusive try199

This is a SMALL DEFAULT SKELETON compatibility check, not full character or
diagnostic acceptance. The reviewer independently rebuilt and installed the
canonical source in
`build/add-shared-body-characters_r1_reviewer_try-3_r2-check/`.
Direct wheel, sdist and rebuilt wheel have the same 116 logical package files
and match the submitted try199 reference wheel SHA-256
`da4d6758d708278d13849744a5ebdb2a83802d9d34d85e16ceca729eb57ec9d3`.
Runtime manifest SHA-256 is
`d04f7e51aef3e2921eea2441daa4abcfee9eb90c659ff2e02d557cee7a165538`.

The reviewer's explicit private interpreter, pinned headless Blender and public
API created fresh disjoint direct-child runs:

- `..._reviewer_try-3_r2-input`: neutral/rest, H=1.70, BPM90, two prepared samples.
- `..._reviewer_try-3_r2-eval`: actual supervised no-images skeleton evaluation, succeeded.
- `..._reviewer_try-3_r2-pack`: actual default `review_pack.main`, with no character option; clean-a native rendering succeeded, then wrapper postflight failed.

`run_actual.py` completed with a failure in 9.959 seconds and preserved its full
traceback in `actual-r2.json`. Source snapshot was unchanged. The actual native
render receipt reports Blender 5.2.2 LTS/build `d13f752e3b9c`, succeeded state
and 18 readable neutral/rest PNGs. The public API accepted its complete output.
The review-pack wrapper then rejected that same output at
`review_pack.py:61` with
`Render receipt output inventory does not match the complete render output set`.

Read-only diagnosis of the retained real pass establishes:

| Observation | Actual result |
|---|---|
| Legacy `_validate_manifest` expected set | 22 files |
| Sealed successful render receipt | 23 files |
| Difference | Exactly `character-render-request.json`; zero missing files |
| Sealed request identity/content | Exactly equals the current expected skeleton render-only request |
| Documented complete union hashes | PASS when independently checked read-only; no output altered and no failed invocation relabeled successful |
| Actual outcome operations | `version-probe` and `render-pass`, both legitimate |
| Actual `reuse_render_pass` | Fails before accepting the pass: `Expected one nonsymlink supervised receipt`; implementation counts both operations without filtering |

Evidence: `actual-r2.json`, `actual-pack.log`, `actual-pass-diagnosis.json`,
`run_actual.py` and `audit_actual_pass.py` in the fresh check run, plus the
unmodified native receipts/images in its separate pack run. The actual pack
never reached clean-b, final assembly or successful sealed reuse. Missing/
changed request, extra/symlink and legacy reuse acceptance checks are not
reported as passing while a valid real pass itself is rejected. The native
slot was released; no live reviewer process remains.

## R2 independent repeat — corrected try206

The reviewer independently rebuilt and installed canonical try206 in
`build/add-shared-body-characters_r1_reviewer_try-4_r2-check/`.
Its direct wheel, sdist and rebuilt wheel contain identical 116 logical files
and match the submitted reference wheel SHA-256
`6f2389268cf59ee29e71bec00b659100483e199dd7a3ac520adb6806714a215f`.
Runtime manifest SHA-256 is
`739c6f975d2e7f04fb05dbfd2a6984a1d86667d96ab587697ec397bae7836573`.
All native work used the explicit private installed interpreter and the
supervised pinned Blender; canonical runtime bytes remained unchanged.

Actual positives passed in **16.662 seconds** through fresh direct-child
`..._reviewer_try-4_r2-input`, `..._reviewer_try-4_r2-eval`, and
`..._reviewer_try-4_r2-pack` runs:

- Real neutral/rest two-sample skeleton evaluation succeeded.
- Actual default skeleton `review_pack.main` completed clean-a, clean-b and assembly.
- Each real pass contains 18 readable PNGs, the sealed request and both legitimate version-probe/render-pass receipts.
- All 18 corresponding decoded RGBA comparisons passed exactly.
- Actual `--reuse-renders` completed successfully while new rendering and backend calls were patched to fail if attempted.

A separately authored HOST-ONLY reuse matrix passed **20/20 in 2.655 seconds**.
It used disposable copies of the real complete pack and never changed that
native pack. Three positive controls establish meaningful rejection tests:
the valid sealed pack and two explicitly **synthetic current-package legacy
compatibility fixtures**, with and without an optional valid probe. These
legacy fixtures test the reader contract and are not claimed as native legacy
generation. The 17 negative cases reject missing/changed/symlinked/broken-link
requests; extra pass/pack entries; unknown, missing or duplicate render/probe
operations; failed/stale probes; symlinked process directories; omitted request
hash membership; extra receipt outputs; and a failed probe in legacy form.
Every case forbids new rendering/backend invocation.

Evidence: `actual-r2.json`, `actual-pack.log`, `actual-reuse.log`,
`reuse-matrix.json`, `run_actual.py`, and `check_reuse.py` in the fresh check
run. Exact R1 source/schema/data/character-doc hash continuity from the reviewer's
independently checked try196 to try206 passed in `r1-source-continuity.json`;
this does not relabel old results as new native evidence.

All 20 temporary fixture workspaces were inventoried and removed after their
expected results: 995,198,197 regular-file bytes and three symlinks were removed
without following link targets. The exact removed fixture paths/counts are in
`reuse-matrix.json`; the original real native pack's complete file-hash map
remained unchanged. Successful actual input/evaluation/pack roots, environment,
archive/source hashes, harnesses and logs are retained as the dependency
closure. Native slot was released; no reviewer process remains active.

This closes R2 for the scoped corrected default/reuse contract. It is not a
full diagnostic, all-character, full-host, licensing or human visual verdict.

## Final unified-candidate execution — frozen try206 (in progress)

Fresh final host run:
`build/add-shared-body-characters_r1_reviewer_try-5_host-check/`.
It consumes the reviewer's own independently built/non-editable try206 wheel
and private interpreter from the retained try4 environment; no developer
installation or acceptance evidence is consumed. Its copied source snapshot
is the exact verified try206 snapshot, guarded before and after checks.

- Full canonical host suite PASS: 372 tests, 365 passed, zero failures/errors and seven explicit installed-harness skips, in 873.353 seconds. Only the documented real-Blender modules were excluded (six backend tests and one pipeline fault test); their native scope remains separate. The canonical source snapshot was unchanged.
- Explicit installed acceptance PASS 7/7 in 109.383 seconds from a fresh decoy fixture workspace and read-only install, with no Blender. These are the seven cases skipped in ordinary host discovery, not untested coverage.
- Source/schema and nested provenance inventory passed: 32 diagnostics, 14 referenced inherited materials, 770 records.
- Independent fresh full preparations at H=1.50/1.70/1.90 are complete in `..._reviewer_try-5_input-h150`, `input-h170` and `input-h190`: 900 samples at each height, BPM60/120/180. Old try191 inputs remain explicitly stale and are not reused.
- Full native work is not yet launched: the developer currently owns the shared Blender slot. The reviewer will use only these new independent preparations after slot release.

Exact final host/source evidence:

- `build/add-shared-body-characters_r1_reviewer_try-5_host-check/host-tests.json` and `host-tests.log`: final complete host result, exact interpreter/origin/manifest, exclusions/skips, source guard and full trace log.
- `build/add-shared-body-characters_r1_reviewer_try-5_host-check/installed-tests.json` and `installed-tests.log`: final seven installed cases, direct venv origin, valid decoy CWD and unchanged read-only package.
- `build/add-shared-body-characters_r1_reviewer_try-5_host-check/source-provenance.json`: source/schema validation and all nested source/register identities.
- `build/add-shared-body-characters_r1_reviewer_try-5_host-check/clearance-review.md`: independent portion/permission/attribution audit and scoped live-retrieval limits; no new external material and no missing/contradictory clearance found.
- `build/add-shared-body-characters_r1_reviewer_try-4_r2-check/package-audit.json`: independent canonical direct/sdist/rebuilt closure, each logical file hash and candidate match.
- `build/add-shared-body-characters_r1_reviewer_try-4_r2-check/installation.json` and `dependency-copy.json`: reviewer wheel/interpreter/installed-file identity and exact locked offline dependency hashes.
- `build/add-shared-body-characters_r1_reviewer_try-5_host-check/source-snapshot.json`: exact frozen runtime sources used for the final checks.
- `build/add-shared-body-characters_r1_reviewer_try-5_host-check/numeric-inputs.json` and `visual-inputs.json`: independently prepared final numeric/focused inputs and seals, not developer generation evidence.

The full host log independently repeats the common arm-raise edit, shared
surface-radius edit, isolated female waist edit, stale shoulder bind rejection,
new torso-base/delta propagation, selection and complete request/manifest
integrity scenarios. R1's stronger reviewer-authored three-height all-vertex
source-copy checks and R2's actual default/reuse checks remain explicitly
linked above rather than replaced by developer logs.

## Provenance audit scope

All14 nested inherited material IDs resolve to complete canonical register
entries. New surface/appearance sources declare original authorship and contain
no third-party mesh/texture asset; skeleton descriptor attribution remains
separate from those authored surfaces. No dependency or convention changes
appear in `pyproject.toml`/`uv.lock` for this patch. The unchanged notice sections
retain author/title/DOI/portion/license/modification information.
Scoped live permission checks and retrieval limits are recorded in
`build/add-shared-body-characters_r1_reviewer_try-1_check/live-license-review.md`.
This is not a claim that every inherited remote license was reverified live.

## Cleanup and pending work

Only the exact reviewer-owned check run and this review record have been written.
No developer, protected baseline, or other review root was modified or removed.
The first host launcher assertion rejected uv's project-interpreter selection
before HML import/test execution; the corrected command explicitly names the
private venv executable with `uv run --no-project`.
No cleanup is claimed complete while review corrections remain unresolved. Build artifacts,
environment, logs and source/dependency hashes are retained as current evidence.
Native/render reproduction, visual pack, code scope/licensing audit and final
cleanup/verdict remain pending.
The full three-height preparation is complete (900 samples at each height),
but native construction is temporarily held for R1's source/design decision;
the host tests completed under their already captured frozen identity.
R1's provisional host/source correction has now been independently checked.
The try191 source snapshot, own archives,
private installation, logs and prepared inputs are retained as prior evidence;
they must not be relabeled as the corrected candidate. The new provisional R1
run is retained with its dependency closure; no roots were removed. The full
native matrix was never launched. The separate try199 small actual compatibility
smoke is retained as unresolved R2 evidence with its input/evaluation/render
dependency closure. No roots were removed. Final acceptance awaits a unified frozen R1/R2 candidate and renewed
affected/whole-host/installed/native/render evidence.

## Independent native construction continuation — try6

The reviewer independently generated all three no-images character builds from
its own try5 preparations and try4 non-editable wheel. Each request asserted
900 prepared samples and runtime manifest SHA-256
`739c6f975d2e7f04fb05dbfd2a6984a1d86667d96ab587697ec397bae7836573`
before invoking the installed public API. All three API calls returned after
supervised Blender and complete output postflight; each backend emitted 900
samples and 60 sealed midpoint samples. The fresh runs are:

- `build/add-shared-body-characters_r1_reviewer_try-6_numeric-h150/`: render identity `956c22b76d04063189d1b3ac2cef2b261240021c1e76582c65135754ee1e5ba2`.
- `build/add-shared-body-characters_r1_reviewer_try-6_numeric-h170/`: render identity `689c741e8735bbf28a46918d1de466071c288bdef6394d0a0be4e52e9673cbda`.
- `build/add-shared-body-characters_r1_reviewer_try-6_numeric-h190/`: render identity `3d4d66376b7a8e6f81d3a1e6eb789dd4115a74b8855eaebf20de1392a042dbfb`.

These are construction results only, not numeric conformance, rendering or
human visual approval. The outputs and their prepared inputs, installed wheel,
process receipts and logs are retained as dependencies for the pending
independent dense verification. Blender was released for developer work.

The independent H=1.50m full verifier subsequently completed with `status=pass`,
`numeric_status=pass`, and 5,714,431 measurements in
`build/add-shared-body-characters_r1_reviewer_try-6_check-h150/metrics.json`.
The invocation used the reviewer's installed interpreter and `verify-skeleton`
with `--action-coverage --dense-floor --character-output <own H150 run>
--numeric-only`; all 900 delivered skeleton samples and all listed dense-floor
fixtures completed. This is one-stature numeric scope only: the H=1.70/1.90
runs, three-stature aggregate, rendering and human visual review remain
pending. The reviewer-run native inputs, per-sample evidence and report are
retained for the pending aggregate and reproducibility.

The independent H=1.70m full verifier also returned `status=pass`,
`numeric_status=pass`, 5,714,431 measurements, with all 900 skeleton samples
and dense-floor scenarios complete:
`build/add-shared-body-characters_r1_reviewer_try-6_check-h170/metrics.json`.
It used the same installed reviewer interpreter and flags as the H150 check,
but its own H170 native input and fresh output. This is still a scoped numeric
result; H190, three-height aggregation and visual acceptance remain pending.

### Read-only inspection of developer consumer evidence

The developer's try231 input and try230 report were inspected as a separate
consumer-specific technical case, not as independent native generation. The
prepared content identity is
`f42b24b2c191d2cd386c18746b8813521214ab5e4e56c4eb8138ca7d62e8b0ce`, and
try230 identifies render request
`c7db00674e2eea22caf89f16bcc2a6079cb1bc5474ef13a9f8766d45968c19c2`.
The preparation has 17 shared consumer samples, a maximum left-knee flexion of
60 degrees, and a BPM90 timeline with 17 animation and five static samples.
Its `primary_bpm` is 120; the separately stored BPM90 timeline must not be
misrepresented as its primary rate. The registry reports all three character
IDs. The leaf native checks report pass for 17 male and 17 female samples,
with maximum residuals 7.47295e-7m and 7.34574e-7m respectively; the scoped
consumer dense rows report 401 points per body, minimum z about -2.24e-16m,
and maximum sole distance about 1.56e-16m.

The original try230 overall report remains `fail` and its character leaf
`incomplete`: diagnostic-fixture/tempo coverage and the other two heights are
not supplied by this consumer-only input. Its leaf native/dense pass is not a
full-matrix pass. Independent reconstruction of the consumer case, source and
shared-frame/contact comparison, and complete independent numeric/visual
review remain pending.

The independent H=1.90m verifier also returned `status=pass`,
`numeric_status=pass`, and 5,714,431 measurements, with 900 skeleton samples
and the complete dense-floor list:
`build/add-shared-body-characters_r1_reviewer_try-6_check-h190/metrics.json`.
All three individual numeric reports now pass independently, but the required
three-height aggregate and rendering/human visual review remain pending.

### Independent three-height aggregate — finding pending

The reviewer's installed CLI `verify-skeleton --numeric-only --stature-builds`
was run against all three independently generated try6 native runs. The
result is preserved at
`build/add-shared-body-characters_r1_reviewer_try-6_numeric-matrix/metrics.json`.
All three leaf numeric results are `pass`, the three evaluated-stature
comparison is `pass`, and dense squat balance passed 2181 samples at each
height. Nevertheless, the aggregate is `incomplete` / `numeric_status:
incomplete` and `matrix_complete: false` because it reports mobility and
diagnostic definition differences for both H170 and H190 against H150. This
is not relabeled a pass.

Read-only comparison finds expected stature-scaled meter-valued examples:
`mobility/couplings/1/parameters/glenoid_m/0` 0.1575 versus 0.1785, and
`diagnostics/0/contacts/0/targets_m/0/0` -0.0825 versus -0.0935 (H150 versus
H170). The frozen design requires equality except intentional stature scaling;
these observations require architect/developer diagnosis and a corrected
aggregate with the identity and all applicable checks intact. This finding
blocks the required all-stature numeric pass. The three scoped reports remain
valid for their separate heights and do not substitute for the aggregate.

### Independent review-pack documentation discrepancy

The `tools/README.md` character pack example passes `<run>/input.json` to
`--input` and `--stature-input`. The exact installed try206 CLI rejected the
first such path before allocating an output, reporting that the existing input
must be a direct-child build run; the same invocation using run directories
was subsequently started. The documentation example should be reconciled
with the supported interface and retested. This is separate from visual review.

### Independent visual pack — try206 only

The reviewer generated H170 (171 samples) and H150/H190 (18 samples each)
from its own try5 prepared inputs in fresh try6 visual-eval runs, using the
reviewer-installed try206 manifest `739c6f975d2e7f04fb05dbfd2a6984a1d86667d96ab587697ec397bae7836573`.
The standalone pack is
`build/add-shared-body-characters_r1_reviewer_try-6_visual-pack/index.html`.
Its command completed with `complete_pack_status`, baseline, regression,
repeatability, stature, GIF and coverage all `pass`: 171 samples, 192
composites, all three character IDs, arm-raise/squat 17 animation and five
count samples, walking 33 animation and nine count samples. Two clean batch
passes and separate default/explicit skeleton and male/female singleton passes
completed. This is evidence for try206 only; applicability to a subsequent
candidate requires source/package and renderer equivalence to be established
explicitly. No artifact was resealed or relabeled.

Reviewer visual observation, not human acceptance: in neutral side and front
sheets the figures are stylized mannequin silhouettes; the two surface variants
are similar, with visibly different torso outlines, while the skeleton remains
separate. In the squat count sheet all three follow the same sequence, but the
figures occupy a small part of the composed sheet, so close-up pages should be
used to assess junctions and the soles. Human judgment on silhouette identity,
movement readability, continuous junctions and planted/rolling feet remains
mandatory.

## Corrected candidate try251 — independent follow-up in progress

The earlier try206 aggregate finding is under correction, not yet closed.
The architect required comparison against canonical sources after intentional
stature scaling, while preserving complete source/package identity and failing
closed for independently invalid changes. The submitted try251 wheel SHA-256
is `2fd71010dd78fadfca4078d841ab37394b180eb62a8a379df0310a2b1571f98a`;
the runtime manifest SHA-256 is
`de3ffa80c5f0622b7a0bb7ab7fd9d8186da28c4f4268d6fbe55346528a857b93`.
Fresh independent reviewer package reconstruction and private installation:
`build/add-shared-body-characters_r1_reviewer_try-8_candidate-check/`.
Direct wheel, sdist and rebuilt wheel matched canonical and submitted
candidate across 116 logical package files.

The independently authored comparator check used three newly prepared,
package-validated inputs and passed six cases: valid 1.50/1.70/1.90 definitions
plus individually changed profile, mobility, diagnostic contact, scene and a
consumer snapshot without resolver. Evidence is `independent-matrix.json` and
`check_matrix.py` in that run. This is scoped host-only evidence; it does not
assert success of the public aggregate or native rendering. New separate
reviewer inputs under `..._reviewer_try-8_input-h150`, `input-h170` and
`input-h190` each contain 900 samples and use try251's package identity.
Focused reviewer visual inputs are also separately prepared at all three
heights. The earlier try206 native and visual outputs were not resealed, and
are historical comparisons only; fresh final-candidate native, numeric,
consumer and visual outputs remain required.

The earlier try248 independent package/comparator attempt remains historical.
The subsequently changed source was detected by the reviewer's source
snapshot guard before any try248 input was generated; no mixed-identity input
or successful full check is claimed from that attempt.

### Additional try251 host-only checks and current cleanup inventory

Using the reviewer's own read-only try251 installation, the three targeted
matrix-workspace tests passed 3/3 with an explicit test workspace and reviewer
owned run root; the surface, scalar skinning and compiled-skinning modules
passed 35/35. No Blender or process inspection was used in those 38 tests.
The separate six reviewer-authored comparator cases remain in
`..._reviewer_try-8_candidate-check/independent-matrix.json`. A prior direct
unittest invocation failed all seven at fixture setup because an installed
package has no implicit repository root; it did not exercise any test body.
The targeted repeat used `HUMANMOTIONLIB_SOURCE_ROOT`,
`HUMANMOTIONLIB_TEST_RUN_ROOT` and a reviewer-local `UV_CACHE_DIR`, and the
result above does not claim a complete host suite or process supervision.

Inventory was taken without following links over reviewer-owned try6/try7/try8
roots. No root was removed in this pass: try6 contains the current unresolved
three-height finding, native/visual comparison and its dependencies; try7
contains the interrupted freeze diagnostic and audit needed to reconcile that
history; try8 contains the current installed candidate, tests and fresh
resumable numeric/visual inputs. The largest retained try6 roots include three
native runs (4,042,845,104; 4,039,251,975; 4,039,505,671 regular-file bytes),
three scoped checks (2,760,630,763; 2,727,168,476; 2,732,391,275 bytes), the
aggregate (3,732,766,431 bytes) and visual pack (3,505,007,398 bytes); each
has zero symlinks. The try7 and try8 candidate roots contain respectively
23,009,804 and 23,014,783 regular-file bytes and four links each; these links
were inventoried, not followed or removed. The six resumable try8 input roots
contain 448,369,557 regular-file bytes total and zero links. Their own current
candidate/evidence dependencies are retained. Removed: zero paths, zero bytes.
Full dependency-aware cleanup is pending after final-candidate results and the
resolution of the try206 aggregate finding; no other agent's run was touched.
