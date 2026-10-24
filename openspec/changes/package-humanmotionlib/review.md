# Independent review — package-humanmotionlib

Verdict: **PASS WITH NOTES** for automated/package acceptance. **Human Gate 2 is APPROVED** by the human's explicit response “одобряю” on 2026-10-24 after presentation of the independent visual pack. Archiving remains a separate workflow action.

Reviewed final commit: `e5f36cfd19fc273079467710e8c0781a78a3e7e5`. Package source payload is unchanged from frozen developer try-6 wheel SHA-256 `4953912362473e56d42783b0593f148f1dd70cd25813c65c6f2d8d1c45bf2ed5`. Reviewer independently rebuilt both distributions, installed them, ran checks, and generated the native build and two clean render passes from sources. Developer logs were not substituted for reviewer checks.

Evidence paths below use these repository-relative roots:

- **checks**: `build/package-humanmotionlib_r1_reviewer_try-2_checks/`
- **build**: `build/package-humanmotionlib_r1_reviewer_try-1_build/`
- **pack**: `build/package-humanmotionlib_r1_reviewer_try-1_pack/`

## Findings and disposition

All discovered implementation defects are closed. No open blocker, major or minor implementation finding remains.

| ID | Severity | Requirement / scenario originally violated | Independent evidence and final disposition | Suggested direction applied by developer |
|---|---|---|---|---|
| F-1 | major | Installed commands cover supported workflow / Complete installed generation and presentation | Original occupied-output rejection made render reuse impossible. Historical reproduction retained in checks/history. Final actual completed-pack `--reuse-renders` passes with distinct original input and same existing output; 172 retained input/frame/receipt files unchanged, `Popen` forbidden. Positive/negative identity/inventory preflight tests pass. `actual-reuse.json`, `actual-reuse.log`. **Closed**. | Validate both completed passes and active package identity before any write; reuse without render/fallback. |
| F-2 | minor | Distribution identity and namespace are explicit / Install and identify the wheel | Active tools/README commands migrated to `hml`, imports to `humanmotionlib`, explicit source/test roots and non-editable contributor execution; obsolete script names remain only in migration history. Final docs rechecked. **Closed**. | Replace active obsolete examples and clarify contributor invocation. |
| F-3 | major | Installed commands cover supported workflow / Use installed host commands | Console and module `check-environment --not-an-option` now exit 2; help exits 0. `cli-replay.json`. **Closed**. | Preserve command argument parsing. |
| F-4 | major | Invocation evidence survives failures / Identify a wheel-installed invocation | Original early-failure receipt omitted installed identity/workspace. Three final actual failure receipts and six native build/render/probe receipts independently verified against package/resource/implementation/runtime identity and workspace. `failure-safe-identity.json`, `real-backend-identity-and-attribution.json`, archived original receipts. **Closed**. | Capture complete identity in the durable initial receipt before spawn. |
| F-5 | major | CI builds and checks the distributable artifact / Check the actual wheel in CI | Invalid renamed wheel independently rejected by uv; corrected workflow retains canonical wheel name. Final actual CI installation succeeds. `history/superseded-review-candidate/ci-wheel-filename-repro.log`, `ci-artifact-audit.json`. **Closed**. | Retain a valid distribution wheel basename. |
| F-6 | minor | CI builds and checks the distributable artifact / Check the actual wheel in CI | Numeric smoke checks now run outside checkout with no PYTHONPATH; downloaded artifact includes installed origin/resources and before/after hashes. Independently audited final artifact. **Closed**. | Run checks in external cwd and retain identity/write-audit evidence. |
| F-7 | major | CI builds and checks the distributable artifact / Check the actual wheel in CI | Actual first CI failed external numeric test helper import. Reviewer independently reproduced old Git blob failure and final corrected external context passed. Final CI green on e5f36cf. `ci-original-namespace-failure.log`, `ci-context-replay.log`, `ci-remote-run.json`. **Closed**. | Make test-helper imports compatible with installed external-cwd execution. |

## Requirement/scenario checklist

A = automatable check; N = numeric metric; H = human visual judgement. Every delta scenario is listed. PASS covers the stated package regression scope, not broader anatomical acceptance.

| Capability / scenario | Type | Result and evidence |
|---|---|---|
| backend-execution / Inspect and build with the pinned backend | A | PASS: actual Blender 5.2.2 LTS build d13f752e3b9c, Darwin arm64; native build/pack command logs and receipt identities. |
| Keep presentation-only work independent of Blender | A | PASS: actual installed HTML-only dispatcher, 556 predecessor files unchanged; subprocess launch forbidden. `html-only-audit.json`. Actual completed-pass reuse also launches no Blender. |
| Launch an installed backend without the checkout | A | PASS: installed module origins, external cwd, host site-packages read-only, explicit HML-only bootstrap. `backend-isolation.json`. |
| Contend for a running backend | A | PASS: full host supervision suite plus actual two-installed-callers serialized intervals; second starts after owner ends. `final-two-install-workspace.json`. |
| Recover ownership after supervisor death | A | PASS: applicable final host supervision tests exercise recovery/fail-closed state; no stale reviewer active process remains. `full-host.log`. |
| Share ownership across installed callers | A | PASS: two genuine non-editable installations, same workspace via symlink serializes; separate workspace has distinct state. `final-two-install-workspace.json` and archived raw receipts. |
| Diagnose a native failure before the script starts | A | PASS: actual spawn-error receipts include initial identity, final host failure-path checks. `failure-safe-identity.json`. |
| Distinguish script execution and process shutdown | A | PASS: final host supervisor tests and actual native receipts distinguish script result, process return and cleanup. `full-host.log`, native process receipts. |
| Identify a wheel-installed invocation | A | PASS: initial/failure and successful native identities independently equal installed package snapshots. `real-backend-identity-and-attribution.json`. |
| build-artifact-lifecycle / Allocate an identifiable review attempt | A | PASS: fresh explicitly allocated flat reviewer roots; protected historical/developer roots untouched. `cleanup-final.json`. |
| Reject ambiguous or nested run identity before writing | A | PASS: invalid path rejection and host root validation tests. `workspace-default-and-invalid-path.json`, `full-host.log`. |
| Allocate an installed-workflow run | A | PASS: explicit workspace, invocation-cwd default, relative output, canonical symlink workspace ownership. `workspace-default-and-invalid-path.json`, installed replay receipts. Disposable fixture workspaces are test content, not independent reviewer runs. |
| host-python-runtime / Recreate the host environment from the committed lock | A | PASS: clean locked non-editable installation and lock check; build contract remained byte-identical through final source changes. `unchanged-locked-build-contract.json`, historical locked-sync log. |
| Install complete runtime dependencies from the wheel | A | PASS: fresh direct-wheel installations without contributor lock; uv dependency consistency, actual complete host and installed commands. `dependencies.log`, `install-audit.json`. |
| python-distribution / Install and identify the wheel | A | PASS: distribution/import `humanmotionlib` 0.2.0, console `hml`, module `python -m humanmotionlib`; origins in non-editable site-packages. `candidate-identity.json`, `cli-replay.json`. |
| Audit both distribution resource closures | A | PASS: independently built wheel/sdist and extracted-sdist rebuild, exactly 92 logical package files, 50 canonical resources, 40 implementation files. All package file bytes equal frozen candidate. `whole-archive-inventory.json`, `sdist-parity.json`. |
| Reject an incomplete or altered installation | A | PASS: actual run_blender preflight rejects missing/corrupt resource or implementation before probe/spawn/output. `incomplete-install-rejections.json`. |
| Use installed host commands | A | PASS: external-cwd validate 32 fixtures, prepare all 900 samples, environment/CLI/module forms; negative arguments preserved. `install-audit.json`, `cli-replay.json`. |
| Complete installed generation and presentation | A | PASS: focused native build and two clean passes, HTML-only and render-reuse replays; complete self-contained visual pack. `backend-build.command.json`, `backend-pack.command.json`, `actual-reuse.json`. |
| Generate with a read-only installation | A | PASS: entire host site-packages tree physically read-only; 416 files unchanged after native runs; relocated installation produces identical canonical identities. `site-packages-before.json`, `site-packages-after.json`, `install-audit.json`. |
| Verify and reject prepared identities | A | PASS: canonical installed identity accepted; five resealed legacy/release/manifest/implementation/schema mismatch variants rejected with regeneration guidance. `install-audit.json`. |
| Audit commercial redistribution and output attribution | A | PASS: exact code/data license bytes, resource provenance, direct/transitive runtime/build/action licenses and generated attribution checked. `distribution-license-audit.json`, pack/attribution-and-limitations.md. |
| Check the actual wheel in CI | A | PASS: real GitHub Actions run and downloaded installed artifact independently audited. `ci-remote-run.json`, `ci-artifact-audit.json`. |
| Compare the package regression pack | N + H | Numeric PASS: exact evaluated geometry and all 76 decoded image pairs against verified baseline; required counts, GIFs, onions, all-frame/comparison sheets delivered. Human visual decision APPROVED on 2026-10-24. |

## Independent execution and distribution evidence

Final frozen-wheel host suite: **174 tests, 95.175 s, OK, zero skipped** (`full-host.log`). Only the two documented real-backend modules were excluded (six backend tests and one fault test); this report does not claim those full modules ran. Instead, the required installed native focused acceptance was independently executed. Preliminary 168-test results on changing sources are not used as final acceptance.

Host CPython 3.14.6; approved uv 0.13.5; build-only setuptools 83.0.0. Runtime dependency check reports eight compatible installed packages. Four direct runtime requirements are complete; setuptools is absent from the runtime environment. Strict wheel inventory is 100 members (92 package + 8 standard dist-info); strict sdist inventory 108 members (92 package, 10 build/root files including standard generated setup.cfg, 6 egg-info). The extracted-sdist wheel rebuild is independent of Git authoring directories. File hashes, build logs and exact archives are retained.

The full supported collection was validated and host-prepared: **32 fixtures / 900 samples**. Native/render scope is the approved **neutral/rest/arm-raise, 31 distinct samples**. The compact all-fixture preparation summary retains input content identity and source/package hashes after disposal of the large temporary prepared input.

Actual Blender embedded Python **3.13.13** was verified separately from host Python 3.14.6. Explicit importlib bootstrap loads only installed humanmotionlib; Blender sys.path remains unchanged, and a sentinel adjacent to HML in host site-packages is unavailable inside Blender. Host PYTHONPATH is not inherited. No GUI/MCP scene was used. The native build exited 0 in 8.39 s; the two-pass pack command exited 0 in 24.23 s. Receipts are durable, complete and finalized; no reviewer-owned native process remains active.

Baseline commit `b9dc38d74b60e839e41446a1e08264f5153cb34c` was independently checked against 83 Git source/code blob hashes. All 44 canonical rig/schema/scene files remain unchanged, focused prepared data matches exactly, and final evaluated samples and reference geometry match exactly. Baseline frames and evidence were copied into the pack; original protected baseline runs were not modified.

## Measured quality gates

| Metric | Measured | Acceptance |
|---|---:|---:|
| Clean render decoded RGBA comparison | 76/76 exact, max error 0 | Exact equality |
| Package vs verified baseline decoded pixels | 76/76 exact, max error 0 | Exact equality |
| Focused numeric checks | 198,593 PASS, 31 samples | All applicable focused checks |
| Contact sliding | 0 m, 186 checks | ≤ 0.0017 m |
| Root translation / rotation | 0 m / 0° | ≤ 0.00017 m / 0.1° |
| Minimum mesh height | 0 m | ≥ −0.00017 m |
| Scene camera/floor/light stability | 0 changed states | 0 |
| Outside-character RGB background/floor crops | 224 comparisons, 0 changed pixels | 0 |
| Loop origin / rotation | 0 m / 0.0143961° | ≤ 0.00017 m / 0.1° |
| Mirror position / rotation | 0 m / 0.0238984° | ≤ 0.00017 m / 0.1° |
| 60 BPM | 5 intervals/beat, 21 animation + 5 count samples; 200 ms | ≥ 3 intervals/beat, ≤ 200 ms |
| 120 BPM | 3 intervals/beat, 13 animation + 5 count samples; 166.667 ms | Same |
| 180 BPM | 3 intervals/beat, 13 animation + 5 count samples; 111.111 ms | Same |
| Six GIF timing checks | All pass; max duration error 3.333 ms | ≤ 10 ms |

Static and animation frames use the same keyed sample IDs. GIF durations are 4000/2000/1330 ms versus 4000/2000/1333.333 ms; terminal duplicate coalescing is documented. Full detail: `quality-gates.json`, `background-pixel-audit.json`, pack/metrics.json and authoritative pack/collection-metrics-samples/ shards.

The generic collection-wide report retains its truthful `diagnostic_fixture_coverage` failure (29 of 32 fixtures not native-rendered). This is outside the explicitly approved focused packaging regression and is not an exception to a required packaging check. The focused summary clearly labels its scope. No complete new anatomical acceptance is claimed. Via-circle direction and exported-clip bake round trip are not applicable: this change introduces neither circular motions nor distribution export behavior; existing FK/rest/mirror tests pass.

## Actual CI artifact

Independent read-only GitHub query confirms [package run 40049069576](https://github.com/bormotov/humanmotionlib/actions/runs/40049069576) completed successfully at final commit e5f36cf, including direct wheel/sdist build, extracted-sdist parity, installed isolated smoke checks and artifact upload. The initial GitHub connector returned 404; approved gh fallback supplied the actual run evidence. Main also supplied the successful [Host Python run 40049069483](https://github.com/bormotov/humanmotionlib/actions/runs/40049069483); reviewer final acceptance additionally rests on its own full host suite.

Downloaded CI wheel SHA-256: `6711a6352c2e2c169565fbee0555eab54bf262ff74d822e735960c813dce2938`, equal to the uploaded checksum. All **92 logical payload files** equal reviewer and frozen developer packages. All CI installed hashes equal this wheel and before/after inventories are identical; all 50 resource hashes and runtime manifest match. Import origin is the installed venv site-packages. Linux CI used Python 3.14.8 / uv 0.13.5 and explicitly did not run Blender or publish the package. ZIP file hashes differ between independent builds due archive metadata; byte equality is established per logical member, not inferred from version strings.

Original downloaded artifact root is main-owned `build/package-humanmotionlib_r1_main_try-1_ci/` and was read only. The accepted pack contains its own checked wheel, checksum, identity/hash inventories, installed logs, remote status and audit, so visual/reproduction evidence does not depend on that original root. Artifact ID 12543135157; configured retention 90 days.

## Licensing and scope

Canonical code is Apache-2.0 and authored data CC-BY 4.0. Packaged copies match root license bytes, third-party notices and used-materials register; provenance validation passes. Exact-version primary license evidence checked for runtime dependencies, uv, setuptools 83.0.0 and pinned GitHub actions; MIT notices/conditions permit commercial modification/distribution. setup-uv exact-SHA license text is retained. Setuptools advisory and its evidence-license conditions were checked. Existing external anatomical references retain their recorded licenses and output limitations; no new external character, rig, asset, font or motion material was introduced. Generated attribution carries the required register and notices.

Changes remain within approved package namespace/CLI/resources/runtime/CI/test/documentation scope. Canonical rig/schema/scene and diagnostic data are unchanged; no undeclared rotation, naming, unit or asset convention change was observed. No implementation/spec repairs were made by the reviewer.

## Human visual gate

Start at **pack/index.md**. It links all 76 delivered images, neutral/rest three-view sheet, five count frames, both panels covering all 13 samples at 120 BPM, colored front/side onion overlays, baseline/package/difference sheets for every delivered view/sample, and paired front/side GIFs at 60/120/180 BPM. Native inputs, sources, baseline copies, metric shards, attribution and compact package/CI evidence are included.

Reviewer visual opinion after directly viewing contact sheets, count/animation panels, side onion and baseline difference sheet: framing/floor appear stable; no new silhouette or visible penetration change is apparent versus baseline. Front beats 1 and 3 foreshorten the arms over the upper thorax; side views clearly reveal forward raise and return. The skeleton remains thin/pale at full-body framing, as in baseline. This observation is not a human visual decision.

**Human decision:** APPROVED on 2026-10-24. In response to the explicit request to approve the independent visual pack, the human replied “одобряю”. This closes Gate 2 for silhouette/stature, fixed framing/floor, forward arm direction/readability, count alignment and planted-contact appearance within the reviewed packaging regression scope. The main orchestrator records this human decision separately from the reviewer's technical verdict.

## Cleanup and dependency closure

Cleanup completed for reviewer-owned obsolete outputs only. Exact inventory, symlink targets, reasons and logical bytes are retained in checks/cleanup-before.json and checks/cleanup-final.json; no symlink target was followed or removed. Ten obsolete roots/disposable directories removed, **1,079,651,763 logical file/symlink bytes unlinked** (not a claim of physical disk bytes freed):

- Whole obsolete `build/package-humanmotionlib_r1_reviewer_try-1_checks/` (selected original failing-candidate diagnostics and locked-install/baseline proof first copied into current checks/history).
- Current checks subdirectories `environment/`, `secondary-environment/`, `fixtures/`, `relocated/`, `corrupt/`, `sdist-source/`, `rebuilt/`, `tmp/`, `cases/`: completed non-editable installations, caches, full-collection prepared/negative copies, HTML predecessor, test workspaces and host-suite fixtures. Original failure/concurrency receipts were copied without editing into checks/evidence and pack/evidence/original-receipts; retained-receipt-map.json resolves old diagnostic locations.

Additionally removed a redundant 91,467,322-byte monolithic numeric copy by replacing it with a 7,373-byte clearly scoped summary (91,459,949-byte reduction); all unabridged authoritative per-sample metric shards remain. `metric-deduplication.json` records this.

Retained roots and concrete reasons:

- **checks**: final wheel/sdist and inventories, independent logs, actual initial/success/failure receipts, CI/license/baseline/identity summaries and minimal superseded-defect diagnostics needed to reproduce this review. Revisit only after superseding review or explicitly accepted lifecycle cleanup.
- **build**: native source/input/evaluated geometry/blend and receipts used by the final pack and numeric audit.
- **pack**: complete human Gate 2 bundle with baseline and generated sources, frame/metric/attribution/evidence closure.

Dependency checks before and after cleanup passed; final **481 HTML/Markdown local links** resolve and remain inside the pack, including all comparison originals, images, metric links and copied evidence. All 31 referenced metric shards and their 33 distinct image references were separately resolved inside the pack (`metric-dependency-audit.json`). No developer, main, accepted-history or unrelated root was edited or removed. No reviewer cleanup is pending. Main/developer cleanup remains their responsibility and is not claimed here. Human visual approval is recorded above; the change has not been archived.
