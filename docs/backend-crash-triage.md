# Backend Crash Triage

This document records four supplied application crash reports and explains how to investigate future failures from repository-owned backend work. It does not identify a vendor or operating-system root cause.

## Incident evidence

The elapsed times below are measured from the launch timestamp recorded in each report to its crash timestamp. The report hashes were checked against the supplied evidence while preparing this summary; the private reports remain outside the repository.

| Case | Application and event | Recorded failure | Elapsed time |
|---|---|---|---:|
| C1 | Chrome 153.0.8010.52, 2026-10-22 02:54:50.2254 (+0400) | SIGABRT on the main thread in the macOS application-registration path (`abort` → `HIServices` registration → `TransformProcessType` → `ChromeMain`) | 0.5723 s |
| B1 | Blender 5.2.2, 2026-10-22 03:03:30.9845 (+0400) | SIGSEGV; thread 2 was waiting in `libIlmThread` (`semaphore_wait_trap` → dispatch semaphore wait → `DefaultThreadPoolProvider::threadLoop`) | 0.6164 s |
| B2 | Blender 5.2.2, 2026-10-22 02:56:36.6160 (+0400) | SIGSEGV with the same reported thread and symbol sequence as B1 | 0.6577 s |
| B3 | Blender 5.2.2, 2026-10-21 23:36:20.5045 (+0400) | SIGSEGV with the same reported thread and symbol sequence as B1 | 0.7297 s |

The reports identify ARM64 and macOS 27.0.1. They associate the incidents with the automation session, but do not provide repository command arguments, a run identity, captured command output, script phase markers, or the Blender executable build hash. The reported Blender version string alone does not show whether the executable matched this repository's pinned build. The reports do not establish memory exhaustion or a Metal failure. The waiting `libIlmThread` stack does not identify the original fault or show whether the process was initializing or shutting down.

Concurrency, launch or sandbox context, native-library initialization, and shutdown behavior are possible investigation hypotheses only. Do not record any of them as a cause without new evidence. Do not infer memory capacity or worker count from virtual-address totals.

## Correlate a future failure

For repository-owned Blender work, correlate a user-provided incident identifier with its owning build or review run and the supervisor's invocation record. Record the run identity, invocation identifier, operation, command, source or prepared-input identity, resolved executable and platform, start/end times, effective deadline, raw exit status or directly observed signal, stdout/stderr log references, last observed script phase, output-validation result, and cleanup status. Use the incident time and identifier supplied by the operator to match an application report; do not copy private crash reports or unrelated user, device, or environment details into the repository.

The invocation receipt and phase markers distinguish observed facts from missing evidence. A missing `script_started` marker leaves the script phase unknown; it does not prove the failure happened during startup. A `script_complete` marker confirms that the script emitted its completion phase, but a later nonzero process exit remains a failed invocation. Do not infer GPU, memory, source-data, or shutdown causes from a generic nonzero status.

If a controlled backend startup fails again, stop the attempt and retain its owned diagnostics for investigation. Do not automatically retry a crashed invocation or reuse its partial outputs as a successful result. Any proposed backend version or renderer change requires a separate evidence-based change.

An additional macOS report was later correlated with the already-recorded try-4 native failure. The application crash report and the invocation-specific crash text provide complementary stacks for that same process; they are not separate incidents, and neither establishes a root cause. The evidence source and correlation are recorded in [operator-decisions.md](../openspec/changes/archive/2026-10-22-harden-backend-process-execution/operator-decisions.md#supplemental-user-report-for-the-recorded-native-failure), without copying the private report into this document.

## Browser checks after C1

This repository has no Chrome launcher. When interactive browser verification is needed, use an already supported browser surface if one is available. Do not launch a GUI browser binary from a shell as an automatic recovery step, disable its sandbox, or create a GUI relaunch loop. Static HTML and link checks may continue independently. If the supported browser surface is unavailable or fails, record interactive geometry and visual checks as **pending** under their owning check; static checks do not pass or replace them. This procedure does not claim that an upstream browser defect has been repaired.
