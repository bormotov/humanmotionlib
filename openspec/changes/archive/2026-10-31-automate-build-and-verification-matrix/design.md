# Design

## Context

The matrix is a convenience wrapper for manually producing and checking one character at one height. Existing public generation APIs and validators already perform the substantive work. A generic build system duplicates their contracts and complicates an operation that can be expressed as a short sequential function.

This change affects tooling only: no canonical data, geometry, motion, scene, sampling rule or acceptance tolerance changes. The paused character change, accepted R6 and historical evidence remain under their original identities.

## Goals / Non-Goals

Expose list, build and check; use predictable current paths; repeat actions completely; retain only logs from past attempts. Use an already prepared offline environment.

Do not provide plans, candidates, recipes as user selections, action graphs, status/present/continue commands, package preparation, generic comparison orchestration, automatic retries, locks, owner discovery or a new process supervisor. Accidental overlapping commands are operator errors outside the supported model.

## Decisions

### 1. Three commands and one small table

```sh
make matrix-list
make matrix-build CHARACTER=male HEIGHT=1.70
make matrix-check CHARACTER=male HEIGHT=1.70
```

Keep a small character-by-height table using the existing registry and heights 1.50, 1.70 and 1.90. List prints every supported pair and its fixed path without performing work. Build/check require one valid pair and affect only it. Every pair uses neutral, rest and arm-raise at 120 BPM, in existing render-only mode. This is the human-selected short set. Preserve authoritative views without numeric/native generation or full managed review-pack passes. No serialized plan or candidate object is needed.

The exact expected outputs follow the canonical fixtures and fixed 1024×1024 scene:

| Fixture | Timeline | Views / source PNG count per pair |
|---|---|---|
| neutral, rest | one beat-zero sample each | male/female: front/side/rear, 6 total; skeleton: those plus thorax-front/side/three-quarter and their isolated variants, 18 total |
| arm-raise | four beats = 2s; 13 samples at beats k/3, k=0..12; static at beats 0..4 | front/side, 26 total for any character |

Thus one male/female pair has 32 source PNGs and one skeleton pair has 44. Static and animation share the same samples. Presentation uses the existing assembler: 8 count sheets for male/female or 20 for skeleton; two arm-raise GIFs and two onion skins; index.html and presentation-inventory.json. A count sheet has one character column: 320×346 for neutral/rest or 320×1730 for arm-raise. Each GIF is 512×512, 12 frames, 2000ms total with [170,160,170]ms repeated four times; its terminal duplicate remains in the source PNG/count samples. Onion skins are 1024×1024. No extra crop set or static-fixture GIF is required. These are local preview outputs, not complete character acceptance.

### 2. One current directory per pair

For male H1.70 the predetermined path is:

```text
build/automate-build-and-verification-matrix_r1_dev_current_male-h170/
  prepared/
  render/
  presentation/
  build.json
  check.json
  logs/
    build-<utc-time>-<pid>.log
    check-<utc-time>-<pid>.log
  .tmp/
```

For other pairs, replace male-h170 by <character>-h150, <character>-h170 or <character>-h190. The runner derives the existing five outer components automatically; the caller supplies no change/revision/role/attempt parameters. The fixed r1/dev/current components identify this contributor table, not a claimed independent reviewer attempt. Independently managed developer and reviewer verification still uses its own fresh five-component run roots under the project rules.

Only content required by the selected fixed generation set exists. Preparation, render and presentation are tool content, not independent runs. There are no UUID directories, old generated-result copies, publication directories, latest pointers or archived reports. Temporary content is removed at terminal completion and stale temporary/partial content is removed before a repeat. Ordinary log filenames distinguish attempts without directory allocation.

### 3. Build is a straight sequence

Validate selection and destinations, open the log, invalidate the current check and prior build success, and remove only declared old generated content. Then call the existing preparation API, render API and required media assembler in order. Write the small successful build result last, only when all configured work and required output assertions succeed. On failure return nonzero, preserve the log, remove partial generated output and leave no successful build marker. Repeat starts the same entire sequence.

Keep the previously agreed narrow public API matrix-destination binding: it permits these declared nested destinations within the stable root, validates containment and producer input/output separation, and preserves original receipt paths. Standalone callers retain fresh flat-run defaults. Do not stage elsewhere, relocate receipts or introduce a second producer-snapshot/publication protocol; existing receipts and manifests remain authoritative. Assembly reads those originals; the final small build result is only a completion marker and selection summary.

### 4. Check reads what is there

Require the selected current successful build. Run the existing applicable validators anew over its actual files: configured membership, producer evidence, required outputs, image dimensions/decoding, animation timing and links as applicable to the approved set. Preserve the validators' substantive assertions. A missing or changed output fails; check never generates, installs, repairs or accepts a previous verdict. Replace only the small current check result and append a new attempt log. Generated build files remain unchanged.

Keep results small: selection, success/failure, time, log path and validator outcomes. Logs capture commands, start/end time, package/backend diagnostics, output/error streams, exit outcome and cleanup facts. Do not duplicate the package/source/producer contract into another matrix identity format. Prior current results are replaced; their diagnostic history is already in the logs.

### 5. Prerequisites and boundaries

The selected package, dependencies and pinned Blender/MPFB are already installed before matrix use. Use that environment offline through existing API calls. Missing prerequisites fail with an actionable message; matrix commands do not create/adopt environments, build wheels or repair installation. Existing uv installation/audit, distribution closure and installed-workflow commands remain separate documented prerequisites or acceptance tools, with their existing requirements unchanged.

Cross-stature comparisons, baseline/determinism packs and full host/installed/distribution acceptance remain their separate tools. Matrix local success neither orchestrates nor implies them. Existing supervision stays inside the public API; the matrix adds no special process worker or group-inspection protocol.

The unresolved backend PGID finding recorded at the start of review.md remains separate work: a reaped leader can leave a saved numeric PGID unsafe to signal. Removing backend hardening from this change does not fix that finding or weaken the main backend-execution specification. Do not claim backend safety acceptance from this scope reduction.

### 6. Replacement and migration

Clean only known generated content for the selected pair; preserve logs, unrelated files, other pairs, installed tooling and protected/accepted evidence. Never follow an output symlink outside the owned tree. Record removed paths/bytes and cleanup errors in the same log; incomplete cleanup prevents a successful terminal claim. No rollback, quarantine or additional history tree is required.

Implementation removes the obsolete matrix control plane and updates its tests and guide, while preserving separately supported domain/packaging tools. Inventory existing UUID/work/publication data and dependencies before removing owned obsolete data. This planning revision changes no generated data or historical evidence. Earlier completed candidate/process tasks are no longer matrix deliverables and their old evidence does not prove the newly reduced contract.

## Verification and gates

Use focused selection/path tests, real-validator positive/negative controls, sequential full build/check repeats, and a late failure followed by a whole repeat. After the required short joint pre-freeze audit, an independent reviewer uses a fresh installed environment and own fresh run roots to follow the literal offline guide. Record exactly which fixed-set paths were actually exercised; do not launch a full character/tempo matrix merely to verify wrapper behavior or relabel prior evidence.

Early visual gate: not applicable, because this change preserves rendering semantics and data. No new final visual pack is required for this tooling-only change. Any visible change returns to its own preview and human gate; the paused character change and its final gate remain separate. Existing licensing/provenance requirements apply; this revision introduces no external source material.

## Risks / Trade-offs

- Repeating overwrites current generated data: this is intentional; only logs preserve past attempts.
- Overlapping commands may interfere: this is an operator error, diagnosed from the logs rather than supported by runtime infrastructure.
- A local check is narrower than library acceptance: the guide and results must state that scope.
