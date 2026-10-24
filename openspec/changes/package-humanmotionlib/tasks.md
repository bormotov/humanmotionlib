# Tasks

Implementation starts only after Human gate 1 approval of this proposal, deltas and design. All tasks below are pending. The developer owns implementation and its tests/documentation; the reviewer owns independent verification and `review.md`, and does not fix code.

## Run allocation

All paths are direct children of the repository workspace's `build/`. Allocate a fresh empty root per independent attempt; a retry changes `try-1` to a new attempt. Tool content lives inside the owning run. The smoke-test workspaces are controlled fixtures inside the install check run, not new independently managed runs.

| Run | Responsibility and retained result |
|---|---|
| `build/package-humanmotionlib_r1_dev_try-1_baseline/` | Coordinated pre-migration build/render baseline and source/commit/backend identity; retain until verified comparison closure exists |
| `build/package-humanmotionlib_r1_dev_try-1_checks/` | Incremental host/contract checks; retain concise final results or unresolved named findings |
| `build/package-humanmotionlib_r1_dev_try-1_wheel/` | Direct wheel/sdist build, staged package and inventory; retain candidate archives and hashes |
| `build/package-humanmotionlib_r1_dev_try-1_sdist/` | Independent sdist extraction/rebuilt wheel and parity evidence; retain concise comparison, remove redundant stages after verification |
| `build/package-humanmotionlib_r1_dev_try-1_install/` | Non-editable isolated install checks, negative fixtures and secondary workspaces; retain results, remove environments/caches after dependency checks |
| `build/package-humanmotionlib_r1_dev_try-1_build/` | Installed real-backend evaluated subset and receipts; retain required inputs/numeric evidence |
| `build/package-humanmotionlib_r1_dev_try-1_pack/` | Developer installed render/presentation integration; retain only media/evidence still needed by hand-off |
| `build/package-humanmotionlib_commit-<sha>_ci_run-<id>-<attempt>_package/` | CI direct build/install evidence and candidate wheel; substitute valid lowercase kebab-case components |
| `build/package-humanmotionlib_commit-<sha>_ci_run-<id>-<attempt>_sdist/` | Independent CI sdist rebuild parity; retain comparison summary, not duplicate stages |
| `build/package-humanmotionlib_r1_reviewer_try-1_checks/` | Reviewer clean build, direct/sdist inventories, host/install checks and scenario evidence |
| `build/package-humanmotionlib_r1_reviewer_try-1_build/` | Reviewer installed evaluated build and numeric checks |
| `build/package-humanmotionlib_r1_reviewer_try-1_pack/` | Final visual pack including its internal clean passes and verified baseline comparison closure |

## 1. Baseline and cleared build inputs

- [x] 1.1 Before modifying implementation, capture the design's coordinated focused source baseline in the baseline run, with neutral/rest/arm-raise samples, fixed views, evaluated measurements, timing and receipts. Verify source/commit hashes, pinned backend identity, successful numeric checks and readable baseline media inventory; record exact commands in `developer-handoff.md`.
- [x] 1.2 Verify the approved `setuptools==83.0.0` build backend and directly declared registry dependency on CPython 3.14, and clear every actually used new tool/action/reference before use. Verify the exact archive allowlist during the build check. Update `docs/used-materials.md` and applicable notices, including the advisory/release-history basis for the approved backend version. Verify exact-version source/license URLs, commercial/derivative permission, conditions, date and output linkage; report incompatibility to the architect instead of changing the design silently.

## 2. Package code and dependency metadata

- [ ] 2.1 Move runtime modules to `src/humanmotionlib/`, update internal/test imports and remove executable checkout-path bootstrapping. Preserve a minimal Blender-safe initializer. Verify migrated host tests, no installed `tools` namespace and no eager host `bpy` dependency in the checks run; update the import migration documentation with the change.
- [x] 2.2 Configure the build backend, version `0.2.0`, source package discovery, direct runtime/build-only requirements and an installable locked contributor project. Verify `uv lock --check`, fresh locked installation, runtime dependency imports/consistency, metadata Python bounds and version agreement; document dependency rationale and source-vs-installed setup separately.
- [ ] 2.3 Implement deterministic build staging, the explicit resource allowlist, backend-contract/version generation and runtime manifest for direct wheel and sdist builds. Verify archive inventories, all canonical byte hashes, implementation hash coverage and absence of runtime tests/history/environments/caches; add focused missing-resource and sdist-closure tests with this implementation.

## 3. Installed resources, integrity and commands

- [ ] 3.1 Introduce the package-resource boundary for source/schema loading, offline registry, backend contract, acceptance docs, notices and attribution. Verify all 32 fixtures and all seven schema files resolve from a non-editable wheel with no checkout or network access; verify missing/corrupt resources fail before process launch and document supported resource inventory.
- [ ] 3.2 Replace checkout/lock-based prepared and implementation identity with the design's packaged logical identities while preserving canonical serialization and content hashing. Verify relocated same-wheel prepared hashes, every source/implementation hash, tampered/mismatched/legacy rejection and explicit regeneration guidance; add regression tests and document legacy prepared-input behavior.
- [ ] 3.3 Add the `hml` console entry point and `python -m humanmotionlib` dispatcher, version reporting and installed environment inspection, retaining all supported operation options and `humanmotionlib.*` imports. Verify both invocation forms, `hml --version`, help, invalid inputs and all-fixture/subset preparation from an external cwd; write `docs/usage.md`, include it in the wheel/sdist resource inventory, and update the contributor command migration table. Keep contributor test discovery explicit and separate from installed environment inspection.

## 4. Workspace-owned supervised execution

- [ ] 4.1 Propagate explicit workspace context through ownership checks, slot paths, receipts, backend cwd and review clean passes. Verify default/explicit workspace selection, same-workspace contention across installations and symlink aliases, distinct-workspace ownership, flat-run rejection and stale-owner recovery with synthetic process tests; document relative-path semantics and unchanged repository slot locations.
- [ ] 4.2 Launch the absolute packaged Blender entry script with its complete HML import closure under Blender's embedded Python, without host site-packages/checkout injection. Verify launcher/failure-path assertions and one installed real-backend build in the build run, reporting host and embedded interpreter identities, package/resource metadata and unchanged timeout/completion behavior.
- [ ] 4.3 Migrate review attribution/acceptance loading, render reuse and HTML-only generator identity. Verify installed normal/reuse/HTML-only behavior and existing media/evidence integrity tests, including a legacy predecessor whose package identity differs; verify HTML-only spawns no Blender. Update review-pack usage documentation and retain source attribution/limitations.

## 5. Distribution and CI integration

- [ ] 5.1 Build a direct wheel/sdist in the wheel run and independently rebuild from the extracted sdist in the sdist run. Verify identical logical runtime resource/implementation inventories, consistent versions/licenses and no `.git` or original-checkout dependency; record archive hashes and build tool identity.
- [ ] 5.2 Install the exact direct wheel non-editably into fresh isolated environments in the install run. Run documented host commands with checkout imports disabled, unset `PYTHONPATH`, outside cwd and read-only installed files. Verify dependency consistency, no package writes, all-fixture validation/preparation, relocation parity, CLI failures, corruption rejection and synthetic standalone HTML presentation; retain import origins and before/after package hashes.
- [ ] 5.3 Add the push/PR wheel workflow and adapt existing host CI commands to the package layout without reducing host test scope. Verify pinned actions/uv, fresh five-component run allocation, sdist rebuild, exact-wheel external-cwd install checks, fail-closed status, scoped summary and 90-day artifact upload excluding caches/environments. Document that publication and reference Blender execution are separate.
- [ ] 5.4 Execute the GitHub Actions workflow for the candidate commit and record its successful run URL, wheel checksum, job outcomes and backend exclusions. Verify the downloadable wheel is exactly the installed/checked artifact; keep this task pending if no actual remote execution is available.
- [ ] 5.5 Complete developer integration: locked full host scope and the installed focused pinned-backend build/pack in the declared runs, including existing numeric audits appropriate to the subset and all-BPM timing. Verify source data/schema/scene hashes and existing tolerances are unchanged, and map results to scenario scope in `developer-handoff.md` before requesting independent review.

## 6. Independent review and human gate

- [ ] 6.1 Reviewer independently builds from clean candidate sources, checks the direct/sdist resource/license closure and runs complete host discovery plus installed-wheel positive/negative checks in the reviewer checks run. Verify all relevant spec scenarios, package identity/dependencies and build/source-clearance evidence; write findings with requirement names in `review.md` without fixing implementation.
- [ ] 6.2 Reviewer runs the installed evaluated subset and two clean render passes on the pinned reference platform in the reviewer build/pack runs. Verify unchanged numerical/contact limits, identical decoded clean-pass pixels, baseline equality, sampling/static agreement, fixed scene and complete links/attribution. Produce the exact labeled neutral/rest views, five-count sheets, 13-frame 120-BPM sheets, 60/120/180 paired GIFs, onion-skin overlays and baseline/candidate/difference comparisons defined in design.
- [ ] 6.3 Inventory owned outputs and retained dependencies, then clean obsolete whole runs and unnecessary environments/caches/stages after checking links/symlinks. Verify retained artifact/pack/evidence references before and after cleanup, preserve active/protected history, and record removed paths/bytes, retained paths/reasons and pending cleanup in existing hand-off/review records. Reviewer requests cleanup of developer-owned roots instead of deleting them.
- [ ] 6.4 Present the independent pack and scenario-based verdict for explicit Human gate 2 approval. Verify the human's decision is recorded in `review.md`; leave this task incomplete while approval, relevant findings or required cleanup remains pending.

## Workflow follow-up

- Archive only after implementation, actual CI evidence, independent review, resolved findings/cleanup and explicit Human gate 2 approval. This planning workflow neither implements nor archives the change.
