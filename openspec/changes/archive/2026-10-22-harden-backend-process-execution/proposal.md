# Proposal

## Why

The supplied reports show three early Blender 5.2.2 native crashes with the same `libIlmThread` signature and one Chrome startup abort. Repository launch sites currently lack consistent deadlines, process outcome records, and Python exception exit handling, so an external failure can stall work or leave ambiguous partial outputs; the reports alone do not establish the underlying vendor or operating-system defect.

## What Changes

- Introduce one supervised execution contract for repository-owned Blender probes, builds, renders, and integration tests: bounded execution and cancellation, one active Blender child per checkout, persistent diagnostics, explicit Python exception exit codes, and no automatic crash retries.
- Reject failed or incomplete executions even when some output files exist; preserve their evidence without presenting a successful pack.
- Document the evidence from all four incidents, the limits of causal attribution, and a safe triage procedure. Chrome has no launcher in this repository; browser verification uses the available supported browser surface and records unavailable checks without repeatedly launching a GUI executable from a shell.
- Provide synthetic process-failure coverage and a small clean build/render comparison to prove that supervision preserves the existing animation and image contracts.

The single logical change is control and observability of external execution used by project checks. It does not patch Blender, Chrome, macOS, or the Codex host, promise zero third-party crashes, change pinned versions/render settings, or introduce new motion data.

## Capabilities

### New Capabilities

- `backend-execution`: Bounded, serialized and diagnosable repository-owned Blender execution with explicit success and failure evidence.

### Modified Capabilities

None. Existing anatomy, joint mobility, timing, render determinism, licensing, and build artifact lifecycle requirements remain applicable. Adding process evidence does not redefine their numerical or visual acceptance.

## Impact

Implementation will affect `tools/runtime.py`, a documented supervised build entry point, `tools/build_skeleton.py` phase reporting, `tools/review_pack.py`, the existing Blender integration tests, and `tools/README.md`. New process tests and an operational triage document are expected. Existing Python 3.12/uv dependencies and Blender 5.2.2 LTS build `d13f752e3b9c` remain pinned; no dependency is planned. Raw Blender invocation remains a low-level diagnostic interface, while documented routine automation moves to the supervised entry point. Existing artifact formats, pose/segment/motion semantics, body group controls/rest policy, contact interpretation, and bake conventions do not change.

Human gate 1 approves this bounded scope and the defaults in `design.md` before implementation. A subsequent independent review and focused visual gate verify the execution changes.
