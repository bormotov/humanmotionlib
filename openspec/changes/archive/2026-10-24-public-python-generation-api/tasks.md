# Tasks

Implementation begins only after Human gate 1 approval. Each run below is an independent fresh direct child of the explicitly selected workspace's `build/`. For a retry, change the attempt component; never reuse an occupied root or nest an independent run. Internal `frames/`, `assets/`, `environment/`, logs and required tool content stay inside the owning run. These roots are planned, not created by this proposal.

| Purpose | Planned run root |
|---|---|
| Pre-change preparation | `build/public-python-generation-api_r1_dev_try-1_baseline-prepare/` |
| Pre-change pinned build/render | `build/public-python-generation-api_r1_dev_try-1_baseline-render/` |
| Developer host checks | `build/public-python-generation-api_r1_dev_try-1_host/` |
| Distribution build/content checks | `build/public-python-generation-api_r1_dev_try-1_distribution/` |
| Installed host workflow check | `build/public-python-generation-api_r1_dev_try-1_installed-host/` |
| Developer API preparation | `build/public-python-generation-api_r1_dev_try-1_api-prepare/` |
| Developer API build/render | `build/public-python-generation-api_r1_dev_try-1_api-render/` |
| Independent reviewer host checks | `build/public-python-generation-api_r1_reviewer_try-1_host/` |
| Independent installed acceptance | `build/public-python-generation-api_r1_reviewer_try-1_installed/` |
| Reviewer API preparation | `build/public-python-generation-api_r1_reviewer_try-1_api-prepare/` |
| Reviewer API build/render | `build/public-python-generation-api_r1_reviewer_try-1_api-render/` |
| Reviewer clean API repeat | `build/public-python-generation-api_r1_reviewer_try-1_api-repeat/` |
| Reviewer CLI preparation | `build/public-python-generation-api_r1_reviewer_try-1_cli-prepare/` |
| Reviewer CLI build/render | `build/public-python-generation-api_r1_reviewer_try-1_cli-render/` |
| Reviewer numerical verification | `build/public-python-generation-api_r1_reviewer_try-1_numeric/` |
| Reviewer comparison/visual pack | `build/public-python-generation-api_r1_reviewer_try-1_pack/` |

The installed check roots own environments, inventories and logs. Any generation they launch uses separately named flat run roots as above in their selected workspace, not independent runs nested under an environment/check root. Additional independent checks use the same naming rule and are recorded in the hand-off. A test suite's synthetic fixture directories are internal test content, not separately managed acceptance runs.

## 1. Freeze baseline and ownership

- [x] 1.1 Record approved artifact/source identity, actual supported host/backend identities and pre-change CLI commands in a developer hand-off record in this change; verify `openspec validate public-python-generation-api` succeeds and Human gate 1 approval is present before changing code.
- [x] 1.2 Before editing generation code, prepare `neutral`, `rest`, `arm-raise` at H=1.70 m and default BPMs through the current CLI into the baseline-prepare run, then construct/render through the supervised CLI into the separate baseline-render run; verify source hashes, complete expected images, valid receipts and recorded version/build/platform, and retain both roots as read-only comparison dependencies.
- [x] 1.3 Inventory every external material actually used during implementation, including reference-only examples or tools; verify commercial and derivative permission and complete any required `docs/used-materials.md` entries before use. Record explicitly if no new external material is used; retain existing source attribution and make no new anatomical claims.

## 2. Public preparation and result records

- [x] 2.1 Add the documented public record types, `GenerationError` fields/codes and JSON projection under `humanmotionlib.api` without eager root-package imports; verify import/signature/serialization tests, no `bpy`, no command-line consumption, no process or filesystem writes, and a short API reference documenting supported diagnostic-only coverage.
- [x] 2.2 Implement public `prepare` by reusing existing source validation/evaluation and path/persistence policy; verify default all-fixture results against the internal evaluator and the parameter/path matrix, including 1.50-m stature, fixture subsets, custom BPMs, duplicate/empty selections, booleans/nonfinite values and no state on invalid destinations.
- [x] 2.3 Project poses and static/animation timelines through sample IDs with exact per-BPM `Fraction` values; verify all joins, stable order, 60/90/120/180 BPM sample counts and beat-2 seconds, shared static/animation pose identity, and unchanged controls/rest/contact/unit semantics.
- [x] 2.4 Project full source hashes/provenance, recursively referenced material IDs, packaged register/license/notice contents and limitations; verify nested reference resolution, exact text/source agreement, absent provenance represented explicitly and detached metadata mutation safety. Document the attribution fields and exact-time serialization.

## 3. Supervised render facade

- [x] 3.1 Implement public `render` for preparation-result and prepared-file inputs using the existing supervised `run_blender.run` path; verify persisted-input revalidation/hash matching, current workspace/freshness/lock/deadline rules, default images and existing independent images/render-only combinations with focused host tests.
- [x] 3.2 Share complete sample/view/path/readability validation with the existing review manifest contract and assemble ordered image/artifact/receipt/backend results; verify rejected missing/extra/duplicate/stale/escaping manifest entries, valid image-to-pose/timeline joins, no fabricated optional outputs and `not-run`/`pending` acceptance labels.
- [x] 3.3 Translate expected failures into the documented stable API codes using structured source/supervisor outcomes, retaining causes and evidence paths; verify invalid input, tampering, filesystem failure, missing/mismatched Blender, contention, timeout, spawn/nonzero failure, invalid outputs and pending cleanup with synthetic fault tests. Verify cancellation cleans the owned process tree and re-raises `KeyboardInterrupt` without retry.
- [x] 3.4 Execute one pinned developer API preparation/build/render of the focused subset in its separate api-prepare/api-render runs; verify readable result paths, complete manifest/receipt identity and unchanged numerical inputs, and add the working two-call application example plus error handling to `docs/usage.md` and the central command documentation.

## 4. CLI and installed distribution integration

- [x] 4.1 Delegate `prepare-skeleton` and `run-blender` to the public operations while keeping parser/presentation at the edge and preserving the internal managed review-pass path; verify delegation tests, console/module/API parity, existing command options/defaults/nonzero exits, construction without images, render-only without images and the designated shared input/build run exception. Keep unrelated command regression tests passing.
- [x] 4.2 Add API tests to the normal host and installed acceptance scopes and include new modules/documentation in the package's existing resource/implementation inventory; verify the complete locked host suite and all-source validation in the host run without weakening existing tests, pins or tolerances.
- [x] 4.3 Build wheel/sdist in the distribution run and check the rebuilt-wheel inventory; verify public imports, metadata/dependency consistency, code/data/license closure and that no new runtime dependency or `tools` namespace is introduced.
- [x] 4.4 Install that wheel non-editably in the installed-host environment and execute public preparation/serialization plus controlled render-failure and CLI-parity cases outside the checkout; verify CPython 3.14, unset checkout imports, misleading neighbors ignored, immutable installation/invocation trees, workspace-contained writes and explicit host-only/backend scope in retained machine-readable evidence.
- [x] 4.5 Finish developer cleanup and hand-off: inventory output sizes/dependencies and symlinks, remove obsolete owned whole runs, and verify before/after links. Record removed paths/bytes, retained roots/reasons and pending cleanup in the hand-off; retain baseline dependencies, the candidate wheel and the evidence needed for independent review, with a named reconsideration event for each.

## 5. Independent acceptance and human visual gate

- [x] 5.1 Reviewer independently installs the candidate wheel and runs the complete host/source/API/CLI and installed-workspace scenarios in fresh reviewer host/installed runs; verify every `public-generation-api` scenario against evidence and report exact exclusions rather than implying backend acceptance from host checks.
- [x] 5.2 Reviewer prepares and builds/renders the focused subset through the public API in separate reviewer api-prepare/api-render roots, repeats API rendering cleanly in api-repeat, and prepares/builds the equivalent candidate CLI subset in cli-prepare/cli-render; verify pinned external Blender, independent receipts, no shared mutable inputs/outputs and both public render input forms.
- [x] 5.3 Run the existing numerical verifier and independent baseline/API/repeat/CLI pose, timing, geometry and decoded-pixel comparisons into the numeric run; verify unchanged applicable limits, exact decoded pixels and public-result image/time/provenance consistency, separating package/implementation identity changes from content comparison.
- [x] 5.4 Assemble the focused visual pack in the pack run exactly as design specifies: neutral/rest three-column views, five-count arm-raise comparison sheets, complete 21/13/13 animation inventories, paired timed GIFs, listed 120-BPM onion skins and machine-readable result export; verify every media/result link, frame label, timing and comparison before presenting it to the human.
- [x] 5.5 Write `review.md` with requirement/scenario evidence, numeric/backend/source-clearance verdicts, focused coverage limits and the pending Human gate 2; verify every finding cites its violated requirement and that generation success is not labeled human visual approval.
- [x] 5.6 Complete reviewer dependency-aware cleanup, including failed attempts: inventory runs/bytes and inbound evidence links, remove obsolete owned whole roots without following external symlinks or touching active/protected runs, and verify remaining links. Record removals, retained reasons and unresolved cleanup in `review.md`; retain pack, source renders/prepared inputs, numeric evidence and candidate-wheel identity while the human gate or final review depends on them.
- [x] 5.7 Present the review pack and record explicit human acceptance or rejection of pose/time labels, movement readability, stable contacts/framing and baseline/API/CLI agreement; verify approval is present before marking the visual gate complete, otherwise return findings to dev or architect according to whether implementation or requirements must change.

## Workflow follow-up

- Archive only after implementation, independent acceptance, completed cleanup and explicit Human gate 2 approval. Archiving and package publication are not part of this planning request.
