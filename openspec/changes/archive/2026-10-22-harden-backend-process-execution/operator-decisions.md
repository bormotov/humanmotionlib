# Operator decisions

## Implementation approval

On 2026-10-22 the human explicitly invoked `openspec-apply-change harden-backend-process-execution` after reviewing the proposal. This authorizes implementation and satisfies human gate 1. Human gate 2 remains pending until an independent visual pack exists and is explicitly accepted.

## Native failure and bounded diagnostic authorization

The supervised fault-harness invocation recorded in `build/harden-backend-process-execution_r1_dev_try-4_checks/processes/863901adb32c49f99abc7009a6df1ca4/outcome.json` failed with native signal 11 before any script phase. Development stopped real Blender work and retained the evidence.

The human then explicitly answered yes to **one** new diagnostic attempt outside the execution sandbox, retaining the same Blender pin, prepared input and arguments, using a fresh owned run, with immediate stop on a repeated native failure. This authorizes a diagnostic comparison, not a GPU/renderer/version change or an automatic retry loop.

The attempt is owned by `build/harden-backend-process-execution_r1_dev_try-6_checks/`. Two earlier tool requests were interrupted by the orchestrator while waiting for an execution result; they were not human rejections. The developer subsequently verified that this run contained no invocation receipts, the checkout coordination state was finished and no recorded process group was live. These interrupted requests therefore did not consume the authorized Blender diagnostic attempt. The short helper request that follows retains the same authorization; its actual outcome must be recorded in the developer hand-off before any success or resumed real-work claim.

Do not treat this authorization or the separate successful version probe as evidence that the fault-harness, build, render or independent review passed.

## Authorized diagnostic outcome

The human confirmed the workspace's separate execution-approval prompt. The single authorized outside-sandbox attempt then completed successfully: pinned probe matched `5.2.2 LTS` / `d13f752e3b9c`; the harness exited zero, emitted `script_complete`, validated its output and passed all ten fault rows with the original prepared-input hash. Evidence is in `build/harden-backend-process-execution_r1_dev_try-6_checks/processes/b9b7a5833462497e9f1481e3e029d5e9/outcome.json`.

The earlier sandboxed native failure remains diagnostic evidence. This comparison establishes different observed outcomes in the two recorded launch contexts; it does not prove a sandbox defect or a common cause with the original reports. The diagnostic attempt has been consumed. Ordinary remaining implementation/build/render tasks may resume under the original apply authorization using the successful launch context and standard workspace execution approvals. Any new native failure again stops real work without automatic retries. Independent review and human gate 2 are still pending.

## Supplemental user report for the recorded native failure

The human supplied another macOS report during implementation and requested that unplanned errors be added to the original evidence. This was an unexpected native crash, not an intentionally induced synthetic failure. The new report supplements the existing try-4 incident; it does not represent an additional launch or crash.

- Source: user attachment directory `1e688a5e-0278-4c02-9350-64af3102450e`, file `Вставленный текст.txt`; SHA-256 `586c6c065945585dc34280d19a138a7d1c058f80336ec5213b4c08b58a66e1ab`. The full report remains outside repository outputs.
- Incident: `68826117-91D0-446A-A235-CB4B2C847C81`, Blender 5.2.2 ARM64, PID 93350, `SIGSEGV 11`.
- Report launch: 2026-10-22 17:03:38.8424 +0400; crash: 17:03:39.5400 +0400. PID matches the recorded process group, and times agree with the try-4 invocation (start 17:03:38.839321, finish 17:03:39.522373 +0400).
- The macOS report has an empty main-thread stack and a waiting `libIlmThread::DefaultThreadPoolProvider::threadLoop` stack on thread 2, resembling B1–B3. The invocation-specific `blender.crash.txt` supplies the additional Metal capability-detection stack for this same incident. These are complementary reports, not separate failures. This correlation does not establish the cause of the original B1–B3 incidents.

No new process launch, version/configuration change or additional incident was required to incorporate this evidence. The existing stop-on-native-failure and bounded diagnostic decisions remain unchanged.

## Resumption of technical verification

The human requested archive, but the required decision about incomplete tasks and spec synchronization was not confirmed; no archive or main-spec sync took place. After discussing remaining integration work, the human explicitly instructed execution to continue (`запускай`). This resumes the approved implementation, integration checks, numerical builds, clean renders and independent review before human visual acceptance. It does not authorize automatic retries after a new native failure or waive human gate 2. Agents must stop issuing execution requests at the final reported checkpoint rather than silently continuing after the user-facing completion message.

## Independent technical completion and pending visual acceptance

Independent r3 review returned PASS WITH NOTES for technical checks on source snapshot `dc0b38051974d1a858bdeb25eca1d978f17878824fa859d9e328521803523233` (122 files unchanged). Both r2 implementation findings are closed. The reviewer independently passed 64 tests, two 31-sample numerical builds with zero measured differences, and two clean render passes with 76/76 exact decoded RGBA pairs and six valid GIF timings. The limited subset does not claim complete diagnostic fixture coverage; native incident causes remain unresolved. See `review.md` for scenario-level evidence and limitations.

The human-facing acceptance pack is `build/harden-backend-process-execution_r3_reviewer_try-1_pack/index.html`, with paired neutral/rest and arm-count sheets, six animations and count overlays. Human gate 2/task 4.5 remains unchecked until an explicit response accepts or rejects this actual source/pack for paired consistency, planted feet, movement readability and stable framing. No archive or main-spec synchronization is performed before that response.

Developer and reviewer cleanup is complete: 16 superseded developer roots (512,296,552 regular-file bytes) and obsolete reviewer evidence (52,454 bytes) were removed after dependency checks. Current reviewer checks/build/pack and unresolved native try-4 / authorized-comparison try-6 remain retained. The owners confirmed no active jobs, sessions or approval requests, with checkout coordination state finished. No further execution is scheduled at this hand-off.

## Human observation of the presented preview

The human explicitly confirmed that, in the presented image/animation, raising and lowering the arms is readable, framing is stable and the feet are stationary. This response is attached to the inline `composites/arm-raise-120-side.gif` in the r3 reviewer pack above and source snapshot `dc0b38051974d1a858bdeb25eca1d978f17878824fa859d9e328521803523233`.

These three observations are accepted for that preview. The response does not explicitly confirm the paired neutral/rest and arm-count comparison sheets or the remaining front/side tempo views. Task 4.5 remains pending until the human accepts or rejects the remaining focused pack criteria; no additional test, render, archive or source change is initiated by this response.

## Human gate 2 accepted

The human subsequently confirmed that the paired frames look identical, accepted the other views and tempos, and explicitly stated acceptance. Together with the preceding confirmation of readable raising/lowering, stable framing and stationary feet, this satisfies all focused visual acceptance criteria in task 4.5.

Acceptance applies to `build/harden-backend-process-execution_r3_reviewer_try-1_pack/index.html` and its linked paired sheets, front/side animations and tempo views, built from reviewed source snapshot `dc0b38051974d1a858bdeb25eca1d978f17878824fa859d9e328521803523233`. Human gate 2 and task 4.5 are complete. This acceptance does not broaden the limited diagnostic subset or resolve the unknown causes of the native incidents. The technical review remains in `review.md`; its references to a pending human decision describe the earlier review checkpoint and are superseded by this operator decision.

All 19 tracked tasks are complete. No additional tests, renders, source changes, archive or main-spec synchronization were initiated to record acceptance. Retain the accepted pack and its required evidence closure under the recorded dependency-aware lifecycle.

## Archive and specification synchronization

After full visual acceptance, the human explicitly requested archive and selected synchronization. The new main specification `openspec/specs/backend-execution/spec.md` contains the approved Purpose and all seven requirement blocks verbatim under canonical main-spec headings. Main-spec validation passed for all five capabilities; comparison with the delta confirmed no remaining changes to apply.

The completed change was moved to `openspec/changes/archive/2026-10-22-harden-backend-process-execution/`, preserving `.openspec.yaml`, the 19 completed tasks, technical review and human decisions. Relative document links are rebased to their original evidence targets at the new archive depth; the crash-triage document links to this archived decision record. These are archival document changes, not changes to executable code or rendered evidence. No new test, Blender invocation, render or cleanup of the accepted evidence closure is required or initiated for this move.

Archive link verification repaired 23 evidence links in the archived review and one inbound crash-triage link. The audit of nine archived Markdown files plus crash triage found 25 local links, all resolving; no stale live-change links remain in `docs/` or `tools/`. Whitespace validation passed. The active-change list is empty, and all five main specifications pass validation. All archival work is finished; no background execution or approval request remains.
