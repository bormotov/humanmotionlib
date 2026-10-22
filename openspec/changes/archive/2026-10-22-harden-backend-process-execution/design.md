# Design

## Context

See `proposal.md` for motivation. Planning inspected the four user-supplied reports, all current capability specs, the backend pin, launch sites, integration tests, render-pack assembly and command documentation. No application was launched to reproduce a crash and no external reference was needed.

### Incident evidence and limits

Attachment labels below identify the containing attachment directory; every supplied file is named `Вставленный текст.txt`. Dates retain the reports' `+0400` offset. Hashes identify exact supplied files, not generated reproductions.

| Label / attachment directory | Incident | Recorded event | Time after launch |
|---|---|---|---|
| C1 / `29bfd0a5-eb13-4e39-9254-8c1b5d89015d` | `48BBC425-9965-4064-8616-541F8643FCCF` | Chrome 153.0.8010.52, 2026-10-22 02:54:50.2254; SIGABRT, main-thread `abort → HIServices ___RegisterApplication_block_invoke → _RegisterApplication → TransformProcessType → ChromeMain` | 0.5723 s |
| B1 / `682fc7bc-ad66-489a-9273-04b515826e99` | `FE6BB3BB-C093-4D9B-B2F6-A39F791A92DE` | Blender 5.2.2, 2026-10-22 03:03:30.9845; SIGSEGV, thread 2, `semaphore_wait_trap → dispatch semaphore wait → libIlmThread DefaultThreadPoolProvider::threadLoop` | 0.6164 s |
| B2 / `04fbb27b-a82b-46c8-8731-6fd3ebdea6a6` | `F08397E8-2467-4B5E-B31D-28B99DE51E85` | Blender 5.2.2, 2026-10-22 02:56:36.6160; same exception/thread/symbol sequence as B1 | 0.6577 s |
| B3 / `10a18c99-6123-4bbe-875d-eb23e99dcb28` | `DED29F52-1CA3-4528-AFAB-CD0ABFA78EB4` | Blender 5.2.2, 2026-10-21 23:36:20.5045; same exception/thread/symbol sequence as B1 | 0.7297 s |

| Label | SHA-256 of supplied report |
|---|---|
| C1 | `cf541247e7679777b64928c12c79ca8db731c7f07457bc9dd195d605fef512fd` |
| B1 | `f470ce348bb4eecdc58121554c1a2316e0e7e07f98248bc0724b1139e8f9cb31` |
| B2 | `10ad9339df7fd39d10756ad5331a72896bcc5636281e15849da9fd256263939c` |
| B3 | `dd7b9b24d8ffb3578c81b89a9aae2ec75b1181e51da04aeeebf7809cb89db4d5` |

All reports record ARM64 on macOS 27.0.1 (26A434), the Codex coalition and ChatGPT as responsible process. The Blender reports name Python parents; Chrome names an exited parent. This associates them with the automation session, not a particular repository command. The Chrome stack establishes failure during application registration. The Blender reports establish a repeated native signature and early process lifetime; their main-thread stacks are empty. A waiting `libIlmThread` stack is insufficient to identify the original fault, the project script or whether termination was during initialization or fast shutdown.

The reports do not contain argv, captured stderr, a project run identity, script phase markers or the Blender CLI build hash. The crash header's `5.2.2` does not establish that the executable satisfies the repository's `5.2.2 LTS` / `d13f752e3b9c` pin. They contain no demonstrated memory-exhaustion termination or Metal failure. Concurrency, sandbox/launch context, native library initialization and shutdown are hypotheses, not established causes. No memory capacity or worker count is inferred from virtual address-region totals.

### Observed project exposure

- `tools/runtime.py` already resolves executable symlinks and checks the version/build. Its `--version` subprocess has no timeout or durable outcome log. Preserve its resource-discovery fix.
- `tools/review_pack.py::render_pass` already uses background/factory startup and captures combined output to `render.log`. It lacks a deadline, explicit Python exception exit code, phase evidence and structured native-exit details. A nonzero first pass already stops assembly; preserve that behavior.
- `tests/test_blender_backend.py` and `tests/test_pipeline_faults.py` spawn Blender directly with no deadline. Only the fault harness consistently supplies `--python-exit-code 1`.
- `tools/build_skeleton.py` catches Python exceptions and writes output files, but cannot capture a native failure itself. It saves the blend after several JSON outputs, so a partially populated directory is possible.
- `tools/README.md` presents a raw Blender command as the normal construction entry point. No tracked project tool launches Chrome, Chromium, Playwright or a browser executable.

## Goals / Non-Goals

**Goals:** one auditable process boundary, bounded failure handling, reduced unnecessary overlap, and preserved existing data/render behavior. Native failures should become actionable evidence instead of a stall, repeated app launch or ambiguous success.

**Non-Goals:** vendor crash patches, a background service, a cross-platform job scheduler, machine-wide browser/process management, automatic version upgrades, disabling crash handlers, tuning native thread environment variables, changing rendering quality, or proving that these controls repair the supplied native defects. Initial implementation targets the existing POSIX Darwin-arm64 reference environment; unsupported supervision primitives fail explicitly rather than silently running unprotected.

## Decisions

### 1. A small shared supervisor and an explicit routine build command

Extend `tools/runtime.py` with a shared invocation policy and add `tools/run_blender.py` as the documented Python-side build launcher. It forwards the current build input/output/render options to `tools/build_skeleton.py`; it does not import `bpy` or solve poses. Record this entry point in `tools/README.md` with the implementation, rather than introducing an undocumented command.

Normal command shape becomes:

```sh
uv run python tools/run_blender.py --input build/harden-backend-process-execution_r1_dev_try-1_build/input.json --output build/harden-backend-process-execution_r1_dev_try-1_build
```

Route `inspect_blender`, render passes and the existing backend/fault-harness tests through the shared policy. Keep the returned version/build/platform keys and existing input/evaluated/render manifest semantics compatible. Script argv includes `--background --factory-startup --python-exit-code 1`; use argument arrays and the resolved PATH executable, without a shell. Version probe receives only its supported probe arguments. A successful pinned probe precedes script work; a failed probe stops immediately. Probe and script are separate logged invocations and each takes the checkout slot, with no nested lock acquisition.

The existing raw Blender command remains documented as a low-level diagnostic interface outside supervised guarantees. Routine automated checks use the launcher. HTML-only generation performs no Blender probe. Prefer this to wrapping every project command in a generic task scheduler or relying on the agent to remember flags.

### 2. Finite defaults with explicit overrides

The supervisor uses monotonic time for waiting/deadlines and records wall-clock times for correlation. Initial authored operational defaults, not measurements of the reported failures:

| Operation | Execution deadline | Slot wait |
|---|---:|---:|
| Version/build probe | 30 s | 30 s |
| Geometry build or backend integration child | 1,800 s | 30 s |
| One clean render pass | 14,400 s | 30 s |

Graceful child-tree termination allows 5 s, then forced termination/reaping allows 5 s. Thus cleanup allowance is 10 s, separate from slot wait and execution deadline. Caller cancellation uses the same bounded cleanup. A one-second injected test deadline has a 13 s upper bound including the spec's two-second scheduling tolerance.

Build and review-pack commands expose `--timeout-seconds` and `--slot-timeout-seconds`; they apply to each script invocation, not the entire multi-pass pack. Internal probe deadline remains separately 30 s. Runtime API callers/tests can pass shorter finite values. Reject zero, negative, NaN, infinity or values over 86,400 s before spawn. No disable-timeout option. Do not put these execution settings inside the existing backend contract or prepared-content hash; record them separately in invocation evidence so source/geometry identity is unchanged. Longer work needs an explicit bounded override, not removal of the guard.

Use a new owned process session/group for each child on the supported platform. Drain stdout/stderr to files rather than unbounded in-memory capture. Only signal that known invocation group; never terminate by executable name, scan/kill all Blender processes, or use an old PID as authority. Restore caller signal handling after cleanup. A child/group that cannot be confirmed ended leaves `cleanup_pending` and prevents a success claim.

### 3. Checkout-scoped serialization, not a native-crash cure

Use an OS advisory lock with a stable coordination file at `build/.backend-execution.lock`, plus compact current-ownership state at `build/.backend-execution-state.json`. These are checkout coordination files, not independent build runs. They persist for the protocol and are not unlinked while callers may exist. Implementation uses Python's standard library and adds no package. Unrelated Python-only checks are not serialized and separately checked-out projects have separate locks.

The live supervisor holds the slot through probe or child execution and cleanup. Poll acquisition with cancellation and the slot deadline; expiry records contention without starting Blender. This reduces simultaneous repository-owned native workloads; there is no claim that concurrency caused B1–B3. External GUI Blender sessions and other checkouts remain outside this coordination scope.

An advisory lock alone is insufficient if its owner dies before the child. Write ownership state before spawn and atomically update it with the invocation/process-group identity immediately after spawn. On later acquisition, a prior unfinished invocation with a still-existing group blocks a new launch, bounded by the slot deadline. Do not kill that group automatically. A confirmed absent group permits closing the prior state as interrupted and proceeding. Ambiguous ownership, permission errors, or death in the pre-PID spawn window require operator resolution and a failed/pending record. PID/group reuse is treated conservatively as possible live ownership, never justification for a kill. Test supervisor death with synthetic processes; no daemon, watchdog service or automatic orphan remediation is introduced.

### 4. Small durable receipts, explicit child phases and fail-closed outputs

Each invocation writes `processes/<operation-id>/outcome.json`, `stdout.log` and `stderr.log` under its owning run, using unique operation IDs. These directories are tool-managed content, not retry/run identities. Before spawn, atomically write `backend-invocation/v1` with `state: running`, invocation ID, operation kind, command, cwd, source/prepared hash where applicable, resolved executable, platform/Python metadata, configured deadlines and log references. After termination, atomically finalize with elapsed/wall times, raw return code, signal when directly known, outcome classification, last observed phase, output checks and cleanup result. Do not infer signals from generic positive exit codes; retain the raw code. Probe receipts additionally record parsed backend identity or its parse error. Do not capture the entire environment, browser profile, unrelated diagnostics or user crash-report directory.

`build_skeleton.py` emits flushed, prefixed JSON phase records to stdout: `script_started` (before backend construction), `input_loaded`, `backend_ready`, `samples_progress` (sample ID/index), `outputs_written`, `script_complete` (only after the blend save). The supervisor records observed phases with receipt time. Marker lines never change the input or artifact data. No marker means `last_script_phase: unknown`; a complete marker with a later nonzero process exit is still failure. Missing finalization after a killed supervisor is an unfinished receipt, not success.

Success for a probe requires zero exit and parsed matching version/build. Success for a build/render requires zero exit, the current invocation's script-complete marker and operation-specific checks. Build checks require readable current `input.json`, `evaluated.json`, `geometry-reference.json`, `build-metadata.json` and nonempty `skeleton.blend`, matching prepared identity and required existing structure. Render checks require current input/build metadata/blend, a readable matching `render-manifest.json`, the expected sample/view inventory and readable image files. Existing detailed numerical verification remains separate. Record file hashes for expected outputs in the receipt; outputs cannot preexist the invocation, except the already prepared matching `input.json` in a shared preparation/build root. Fresh-output/path preflight preserves the lifecycle rules and rejects stale result files.

Pack assembly proceeds only after both clean-pass receipts succeed and manifest/input checks pass. Existing `--reuse-renders` accepts newly supervised renders only with successful matching receipts and unchanged recorded output hashes. Explicitly protected legacy input packs retain their documented read/HTML-only workflows without fabricated historical receipts; they are not evidence of supervised execution. No automatic crash retry or fallback renderer/version is added. Keep failed artifacts as diagnostic evidence until dependency-aware cleanup, not as a success cache.

### 5. Triage documentation and source handling

Add `docs/backend-crash-triage.md` and link it from `tools/README.md`. Summarize C1/B1–B3 using the evidence above without copying full reports, user IDs, hardware UUIDs or attachment paths. Correlate future failures by owned run, invocation time, command/exit/log/phase evidence and a user-provided incident ID. A missing marker cannot prove startup failure; an explicit script-complete marker helps distinguish later termination. If the same controlled startup fails again, stop and hand off the retained diagnostics for environment/vendor investigation; propose any version or renderer change separately with evidence.

For C1, use an already supported browser surface for interactive checks when available; do not launch `/Applications/...` binaries, disable browser sandboxing, automate GUI relaunch loops or install a browser dependency to work around the abort. Static HTML/link checks can continue independently. Unavailable browser geometry/visual checks remain pending under their owning spec; static checks never replace them. This is operational guidance because this repository has no Chrome launcher to fix. It does not certify an upstream browser repair.

The only new evidence inputs are user-supplied diagnostic reports and repository sources. Full private reports stay outside project outputs. No external material was consulted for this proposal. If implementation or review uses any external manual, bug report, code, asset or other reference, first verify explicit commercial-use and derivative/distribution permission; reject missing/ambiguous/NC/ND or incompatible terms. Record each actually used cleared material in `docs/used-materials.md`, including no-attribution materials, with portion, URLs/license, permission basis/conditions, check date and related outputs. Do not copy proprietary vendor reports into the library. Reuse existing authored diagnostic data with its current provenance.

### 6. Independent verification and human acceptance pack

Synthetic tests exercise missing executable/spawn errors, version mismatch, controlled nonzero return/signal classification, a Python exception with exit code, timeout with SIGTERM-resistant child/descendant, caller cancellation, two callers, owner death, incomplete receipts, partial/stale outputs and first-pass failure. Use authored helper processes and mocked signal results rather than deliberately crashing Blender or Chrome. An unrelated sentinel process proves termination scope. Assert exact spawn counts to catch hidden retries. Real integration checks use the pinned backend serially and stop on the first native failure.

Use `adult-reference-v1`, H=1.70 m and existing fixtures `neutral`, `rest`, `arm-raise`, prepared with the existing BPM 60/120/180 plans. This is a focused regression subset. It cannot satisfy complete diagnostic-coverage checks and must say so in its index/report. Check existing build repeatability bounds (`1e-6 H` position, `1e-6` rotation-matrix elements), source/input hash identity, fixed scene metadata, matching evaluated source evidence and exact decoded RGBA equality across two clean render passes. No source pose, amplitude, body group controls, rest policy, via pose, mirror, contact target, convention or bake behavior is changed.

The reviewer supplies a focused index linking process receipts/logs, numerical checks, repeatability and timing reports, plus:

- Neutral/rest: a 4-column × 2-row sheet, columns `clean-a front`, `clean-b front`, `clean-a side`, `clean-b side`; rows `neutral` and `rest`. Use existing fixed cameras and original PNGs.
- Arm raise static: a 5-column × 4-row sheet at beats 0/1/2/3/4; rows `clean-a front`, `clean-b front`, `clean-a side`, `clean-b side`. Label count and pass. Preserve the original resolution; compose cells without reframing the character.
- Arm raise animation: ordinary front/side sheets for all sampled frames at BPM 60/120/180 (21/13/13 animation samples and five static samples), front/side GIFs at each BPM with existing timing validation, and front/side onion-skin overlays at the five count boundaries for BPM 120. At least two in-betweens remain between each full count.
- A readable process-case table with one row per synthetic failure/serialization case, expected result, actual result, evidence link and cleanup status. Label simulated failures so they cannot be mistaken for new vendor incidents.

The human compares paired pass silhouettes, camera/floor/scale, planted feet, readable raise/lower direction, count poses and playback. No full anatomical reevaluation is requested. Review requires human gate 2 before archive because this change touches the render execution path, even though intended pixels/settings are unchanged. Chrome startup reproduction is not an acceptance step.

## Risks / Trade-offs

- [Unknown native defect] → Describe reduced exposure and improved diagnosis, not elimination; preserve pins and stop on a real failure.
- [Serialization reduces throughput] → Only backend children share a checkout slot; independent source/math/HTML checks stay parallel.
- [Timeout kills legitimate long work] → Use generous finite defaults, explicit bounded overrides and durable progress/log evidence; record the effective deadline.
- [Supervisor or machine dies] → Initial receipt/state remains unfinished; orphan ambiguity blocks new backend work and is resolved explicitly rather than by deleting locks or killing stale PIDs.
- [Local slot does not cover other checkouts/GUI] → State that limit in receipts/runbook; do not add machine-global control.
- [New launcher changes the documented normal command] → Keep artifact/data/CLI backend semantics and raw diagnostic command; migrate every tracked automated call site together.
- [Large regression rendering] → Use only the frozen three-fixture subset; do not rebuild the entire accepted anatomical library for this process-policy change.

## Migration Plan

After human gate 1, implement and fault-test the supervisor first, then migrate all tracked automated launch sites and command examples in one revision. Capture baseline tests before integration and rerun relevant source/runtime/backend/presentation tests afterward. Keep successful upstream acceptance history unchanged. Reverting this change removes the new supervisor/launcher integration and docs, with no canonical-data or historical-pack migration; retain any unresolved crash evidence required by the hand-off.

Each independent execution/check/review attempt receives its own fresh flat root:

- `build/harden-backend-process-execution_r1_dev_try-1_checks/`: synthetic process cases and automated test receipts.
- `build/harden-backend-process-execution_r1_dev_try-1_build/`: focused prepared input and supervised numerical build.
- `build/harden-backend-process-execution_r1_dev_try-1_pack/`: developer smoke render passes and focused pack.
- `build/harden-backend-process-execution_r1_reviewer_try-1_checks/`: independent synthetic/relevant-test evidence.
- `build/harden-backend-process-execution_r1_reviewer_try-1_build/`: independent prepared input and numerical build.
- `build/harden-backend-process-execution_r1_reviewer_try-1_pack/`: independent clean-a/clean-b renders and human pack.

Use a new attempt component for any retry and a new revision for changed source. Tool content (`processes/`, `cases/`, `clean-a/`, `clean-b/`, `frames/`) stays inside its owning run; standalone probes in tests also write there. A caller without an owning root must explicitly allocate a fresh valid run root rather than write to a global temporary evidence directory. Input and independently managed output runs are disjoint after symlink resolution. Preparation and construction may share the designated build root.

After verification, inventory owned roots and their dependencies; retain the independent pack and required build/check receipts for human acceptance, plus unresolved diagnostics with named issues. Developer smoke packs and duplicate successful scratch evidence are removable when no retained dependency needs them. Preserve existing accepted/protected legacy packs in place. Record removed paths and bytes, retained roots/files with concrete reasons and reconsideration events, before/after link/dependency checks and any pending cleanup in the developer hand-off and `review.md`. Reviewers clean only their owned roots. The two coordination files are retained as active protocol state, never as historical evidence; do not unlink a lock used by another caller. No generated root or cleanup was required during this planning-only turn.

## Open Questions

No unanswered question blocks implementation approval. The vendor/environment causes of C1 and B1–B3 remain unknown; that uncertainty does not change this scoped execution policy. Future evidence may justify a separate backend-version or environment change, which requires its own proposal.
