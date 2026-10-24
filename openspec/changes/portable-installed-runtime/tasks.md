# Tasks

Implementation begins only after human approval of proposal, deltas and design (Gate 1). The dev owns implementation and its tests/docs; the independent reviewer owns verification and `review.md`. All source filenames below are under `src/humanmotionlib/` unless qualified. Coordinate shared runtime/CLI edits through one dev before assigning independent work.

## 1. Record the unchanged baseline

- [ ] 1.1 Dev: identify or capture the unchanged installed-wheel baseline described in design section 6, using explicit workspace and fresh valid run roots; verify and record commit/release, wheel checksum, package/resource identity, backend pins and protected-input hashes in the developer hand-off.
- [ ] 1.2 Dev: retain neutral/rest and four-beat arm-raise baseline evidence at the specified tempos and views; verify existing numeric/timing checks and required comparison inputs, with no modification of accepted historical packs.

## 2. Require workspace and unify path resolution

- [ ] 2.1 Dev: replace ambient workspace selection in `runtime.py` with required absolute workspace validation and workspace-relative read/write resolution, retaining fresh five-component runs, same-run exceptions and resolved containment; verify missing/empty/relative workspace, traversal, escaping build/run/content symlinks, occupied roots and disjoint input/output cases in focused runtime tests before any mutation.
- [ ] 2.2 Dev: propagate the explicit context through `cli.py`, `prepare_skeleton.py` and maintained writer callers; update `tests/test_cli.py`, `tests/test_runtime.py` and affected caller fixtures, verifying console/module/API parity and identical prepared bytes/path choices from two unrelated invocation directories.
- [ ] 2.3 Dev: document the interface break and source/installed examples in `docs/usage.md` and `tools/README.md`; verify the documented option placement and relative-operand behavior against both entry points, including help/version/validate/check-environment without workspace and without HML filesystem allocation.

## 3. Contain numerical verification outputs

- [ ] 3.1 Dev: route `verify_skeleton.py` and `verification_run.py` report and sample-shard writers through the selected workspace and owning fresh check run; add focused workspace-contract tests covering full, preview and transforms-only modes, relative stature inputs, explicit external read inputs, and rejection of invalid report/shard destinations before file creation.
- [ ] 3.2 Dev: update numeric verification usage and direct API examples alongside the implementation; verify every documented output stays inside its owning run and report/shard numerical contents and failure thresholds match existing verifier tests.

## 4. Bind supervision and scratch to caller ownership

- [ ] 4.1 Dev: propagate validated workspace/run context through `run_blender.py`, `runtime.py` and `build_skeleton.py` as needed, configuring explicit backend cwd and run-local temporary/cache/config/log locations in child environments; verify launch arguments, bootstrap/import isolation, bytecode behavior, unchanged parent environment and before/after write inventories in `tests/test_run_blender.py` and `tests/test_blender_bootstrap.py`.
- [ ] 4.2 Dev: retain package-owned backend closure and manifest/implementation validation without checkout fallback; verify missing/corrupt runtime files fail before probe/spawn even with valid-looking neighboring resources, and retain existing prepared-content, source-hash and completion-evidence negative tests.
- [ ] 4.3 Dev: extend `tests/test_runtime.py` supervision coverage for distinct installations/cwds and symlink aliases targeting one workspace, and for distinct workspaces; verify serialization, finite wait/cancellation, orphan handling, owned-child cleanup and failure receipts with resolved run/scratch paths.
- [ ] 4.4 Dev: update backend command and diagnostic-path documentation, including `docs/backend-crash-triage.md` where affected; verify documented receipt/log/lock locations against successful and injected-failure runs without changing backend pins, retry policy or acceptance thresholds.

## 5. Make review and presentation portable

- [ ] 5.1 Dev: migrate `review_pack.py` input/output preflight and all modes to explicit workspace-relative operands and permit valid explicit cross-workspace build inputs as read-only; verify fresh/disjoint output allocation and unchanged input bytes in `tests/test_review_pack_supervision.py`.
- [ ] 5.2 Dev: replace lexical `build` ancestry inference in `presentation.py` with the design's explicit predecessor location and existing provenance identity, validating the complete dependency closure before writing; verify HTML-only predecessors outside any build directory and beneath misleading multiple build ancestors in `tests/test_review_presentation.py`, including required links, preserved hashes and no Blender launch.
- [ ] 5.3 Dev: retain render-reuse and managed-asset checks while changing path resolution; verify stale/incomplete/tampered predecessor and reuse evidence fails closed, HTML/reuse spawn no backend, and affected `tests/test_review_graphics.py` and supervision/presentation regressions pass.
- [ ] 5.4 Dev: document external predecessor, cross-workspace review, HTML-only and reuse examples in active usage guidance; run those examples against controlled inputs and audit local visuals, required predecessor links and protected-input hashes.

## 6. Check the actual installed artifact outside HML

- [ ] 6.1 Dev: add a documented installed-wheel check harness with controlled fixture closure, copied to an externally owned check run instead of importing checkout test helpers; verify non-editable import/resource origins, read-only installation, both entry points/direct writer APIs, all canonical fixture validation/preparation and numeric/presentation host coverage from two unrelated external cwds.
- [ ] 6.2 Dev: add hostile-neighbor, missing-workspace, path-escape, symlink and resource/implementation/prepared/reuse tamper cases to that harness; verify expected failures, unchanged sentinel/package/source/cwd inventories and all HML-directed writes confined to selected workspace build trees, including scratch, report shards and locks.
- [ ] 6.3 Dev: update `.github/workflows/package.yml` to allocate its installed acceptance run outside the checkout and retain exact wheel checksum, direct/sdist resource parity, supported interpreter/tool versions and scoped results; verify the actual candidate CI run and retain its link, with synthetic/host evidence explicitly separated from unexecuted real Blender scope.
- [ ] 6.4 Dev: migrate remaining maintained callers and `.github/workflows/host-python.yml` where needed without shipping contributor test discovery into the runtime; verify the complete locked host suite and active command documentation, keeping explicit real-backend exclusions and no cwd fallback.
- [ ] 6.5 Dev: audit license/provenance and the used-materials register for files/tools actually used; verify no new dependencies/actions or external sources were introduced without required clearance, and installed attribution/resource inventories remain complete.

## 7. Independent acceptance and hand-off

- [ ] 7.1 Dev: complete integration checks and dependency-aware cleanup before hand-off; record removed whole run roots/bytes, retained outputs/dependencies with concrete reasons, link checks and any pending cleanup in the durable hand-off, preserving protected history and other agents' active outputs.
- [ ] 7.2 Reviewer: independently install the exact candidate wheel in a fresh external caller workspace, execute the design's host/isolation/integrity/supervision matrix and audit actual CI evidence; produce scenario-to-evidence results in `review.md`, reporting any unexecuted scope and findings against exact requirement names.
- [ ] 7.3 Reviewer: run the pinned real backend from installed sources for the focused neutral/rest and arm-raise regression, including two clean passes and specified tempos; verify unchanged numeric/contact/timing limits, canonical source inventory and decoded-pixel determinism/baseline comparison, then deliver the labeled sheets, GIFs, onion skins and difference panels specified in design section 6.
- [ ] 7.4 Reviewer: generate and link-audit the HTML-only derivative of a protected external predecessor, verify no backend spawn and unchanged dependency/media evidence, and include it in the human review pack without extending the predecessor's numeric verdict.
- [ ] 7.5 Reviewer: complete owned-run cleanup and retained-dependency audits on success or failure; record removed paths/bytes, retained paths/reasons and pending items in `review.md`, requesting dev cleanup for developer-owned roots and preserving final review/baseline dependencies.

## Workflow follow-up

- Present the independent review pack for explicit human visual approval (Gate 2). Route implementation findings to dev and requirement changes back through architect/spec approval.
- Archive only after required checks, resolved findings, completed cleanup and human visual approval; synchronize the deltas through the archive workflow and verify the archived result.
