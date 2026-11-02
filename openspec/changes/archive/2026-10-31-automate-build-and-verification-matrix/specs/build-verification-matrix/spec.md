# Spec Delta

## Purpose

Let a contributor select one character and height, run a complete build, check its current files and repeat either action manually using stable paths and ordinary logs.

## ADDED Requirements

### Requirement: A fixed table selects one character and height

The workflow SHALL expose a read-only table of supported character/height pairs and their predetermined output directories. The table SHALL be skeleton/male/female × H1.50/H1.70/H1.90. Every row SHALL generate only neutral, rest and arm-raise at 120 BPM using existing render-only mode and unchanged authoritative views. The only matrix operations SHALL be list, build and check; neither a serialized plan nor package-candidate selection SHALL be required.

#### Scenario: List and select a variant
- **WHEN** the contributor lists the matrix or selects male at H1.70
- **THEN** list shows the supported pair and its output path without executing generation or checks
- **AND** build or check selects only that pair, using the fixed configured fixtures, BPMs and existing view rules
- **AND** missing, unknown or invalid selection fails before changing output
- **Verification:** literal CLI/Make calls, table membership and no-work/selection negative tests.


#### Scenario: Produce the agreed short set exactly
- **WHEN** any selected pair is built and checked
- **THEN** neutral and rest each have one beat-zero sample; arm-raise has 13 animation samples at beats k/3 (k=0..12), including its five integer-beat static samples, over 2 seconds
- **AND** male/female use front/side/rear for neutral/rest and front/side for arm-raise, yielding 32 source PNGs per pair; skeleton additionally preserves the three thorax views and their isolated counterparts for neutral/rest, yielding 44 source PNGs
- **AND** all source PNGs are 1024×1024 and no duplicate static render set is generated
- **AND** presentation contains one count sheet for each fixture/view (8 for male/female, 20 for skeleton), two front/side arm-raise GIFs, two arm-raise onion skins, index.html and its inventory
- **AND** each GIF is 512×512 with 12 frames, omits the duplicate loop endpoint and has decoded durations [170,160,170] repeated four times (2000 ms total); static neutral/rest have no GIF
- **AND** count sheets contain one selected character per row (320×346 for neutral/rest and 320×1730 for arm-raise); onion skins remain 1024×1024
- **Verification:** decoded source/media inventory and timing checks against the canonical fixtures and fixed scene; wrong/missing/extra member, wrong dimensions and damaged GIF controls.

### Requirement: Build executes one complete sequence in a stable result directory

Build SHALL use an already installed offline environment and existing public APIs to run preparation, generation and required presentation for the selected pair in order. It SHALL replace that pair's current generated content and invalidate its old check result before work. Success SHALL require completion of the full sequence and its expected files; package installation, automatic retry, selective continuation and unselected variants SHALL NOT run.

#### Scenario: Build or repeat the selected pair
- **WHEN** the contributor runs or repeats the build command
- **THEN** every step executes again at the same predetermined paths
- **AND** existing API source, producer-completion, backend-version and output assertions apply
- **AND** the final current build result records success only after all steps finish
- **AND** logs and unrelated/protected inputs are preserved, with no copy of old generated results
- **Verification:** selected-only API integration, two sequential builds and a controlled late-stage failure followed by complete repeat.

### Requirement: Check verifies the current selected result

Check SHALL run the existing applicable validators against the selected pair's current successful build and actual files. It SHALL verify its configured membership, producer identity, required files and declared media properties. Check SHALL write a current result and return a nonzero exit on missing, damaged, incomplete or changed data. It SHALL NOT generate, install or repair anything or reuse an earlier check verdict.

#### Scenario: Check complete and damaged files
- **WHEN** the contributor checks a complete current build or repeats the check
- **THEN** all configured checks execute again and replace the current check result
- **AND** current generated build files remain unchanged
- **AND** missing build completion, wrong selection, absent/corrupt files or invalid image/animation metadata cannot pass
- **Verification:** actual-validator positive control, file/membership/media negatives, repeated-check count and generation-spawn interception.

### Requirement: Every attempt leaves a log while current data is replaced

Each started build/check SHALL write a distinct ordinary log file in the selected pair's log directory. The log SHALL retain the selection, command, start/end time, diagnostic package/backend information, output/error messages and final exit outcome. Current reports SHALL remain small and need no separate allocation, publication or latest-pointer protocol. Only logs SHALL remain as history of previous matrix attempts.

#### Scenario: Diagnose a failed or repeated action
- **WHEN** an action fails, is interrupted or is later repeated
- **THEN** its log remains readable independently of removed temporary/generated data
- **AND** its current result cannot claim success unless the action completed
- **AND** accidental duplicate/overlapping commands carry no supported-result or successful-start guarantee; their logs record observed results without locks or owner discovery
- **Verification:** failure/interruption/repeat logs and current-result assertions; overlap correctness is not an acceptance criterion.

### Requirement: Temporary and failed data is removed safely

A terminal action SHALL remove its temporary data and, after failed build, its partial generated output. A new build SHALL clear only the declared current output of its selected pair. Cleanup SHALL preserve logs, unrelated files, installed tooling, other variants and protected historical evidence. An uncompleted cleanup SHALL be recorded as such rather than silently reported successful.

#### Scenario: Replace only the selected current data
- **WHEN** build succeeds, fails or repeats after abrupt termination
- **THEN** old temporary/partial data is removed from its declared location
- **AND** earlier attempts survive only in their logs, not in UUID/stage/archive trees
- **AND** cleanup neither follows a symlink outside the owned tree nor removes other variants or protected evidence
- **Verification:** success/failure/leftover fixtures, containment/symlink/foreign-content negatives and cleanup accounting.

### Requirement: Matrix success has a limited and explicit meaning

The guide and current results SHALL distinguish build completion, local file verification and full library acceptance. Package/distribution tests, host/installed acceptance, multi-variant comparisons, baseline/determinism packs and backend process-hardening SHALL remain their separate existing workflows. Matrix commands SHALL not orchestrate or imply them. Existing human gates and the paused character change SHALL remain applicable.

#### Scenario: Follow the manual offline workflow
- **WHEN** the contributor follows the documented list, build and check commands for male H1.70 in a prepared offline environment
- **THEN** the commands need only character and height and use the listed stable directory and logs
- **AND** neither a plan/candidate/role/revision/attempt nor an agent-generated command graph is required
- **AND** missing installation/backend prerequisites produce an error, not automatic repair
- **AND** a local pass does not grant human visual acceptance, complete matrix acceptance or permission to resume paused work
- **Verification:** independent literal walkthrough and a scope/pause assertion in the results and guide.
