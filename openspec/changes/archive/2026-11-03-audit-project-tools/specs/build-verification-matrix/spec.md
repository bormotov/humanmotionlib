# Spec Delta

## MODIFIED Requirements

### Requirement: Build executes one complete sequence in a stable result directory

The Make build SHALL prepare its tools, rebuild/install the current library package, then prepare, generate and present the selected pair. It SHALL replace only that pair's current results and invalidate its old check before generation. Success requires every stage to finish. Automatic retry, selective continuation and unselected variants SHALL NOT run. Direct advanced commands SHALL still require prepared tools.

#### Scenario: Build or repeat the selected pair
- **WHEN** the contributor runs or repeats the Make build with one supported character/height
- **THEN** tool preparation and an unconditional library rebuild/install finish before the selected preparation, generation and presentation run again at their fixed paths
- **AND** existing source, completed-operation, Blender-version and output checks apply
- **AND** the current result reports success only after every stage finishes
- **AND** logs and unrelated/protected files remain, without retaining copies of old generated results
- **AND** the command supplies ordinary work/cache/output paths without extra caller arguments
- **Verification:** literal clean-checkout command, selected-operation tests, repeated library-build observations and a late-stage failure followed by a complete repeat.

#### Scenario: Setup fails before generation
- **WHEN** a valid selection encounters missing uv, unavailable required dependencies, unsupported Python or failed package preparation
- **THEN** the command reports the failed prerequisite/stage and exits nonzero before generation or replacement of previous results
- **AND** no later stage runs and no successful result or source record is invented
- **Verification:** preparation/build/install failure controls, unchanged-result hashes and checks that generation was not started.

### Requirement: Check verifies the current selected result

Check SHALL rerun the applicable validators against actual files from the selected successful build and its recorded package. It SHALL report failure for absent, damaged, incomplete or incompatible data. Check SHALL NOT prepare/install tools, generate, repair, change the recorded source/package information or reuse an earlier verdict. Both the Make route and the direct advanced check command SHALL perform read-only prerequisite checks before starting a check attempt. If the selected result root or its build record is absent, they SHALL fail with the exact selected Make build command without creating or modifying directories, logs or reports. This refusal SHALL NOT count as a started check attempt. Missing compatible tools SHALL likewise produce the Make build remedy without preparing tools.

#### Scenario: Check complete and damaged files
- **WHEN** the contributor checks a complete current build or repeats the check
- **THEN** every configured check runs again and replaces the current check report
- **AND** generated build files remain unchanged
- **AND** missing completion, wrong selection, absent/corrupt files or invalid image/animation properties cannot pass
- **Verification:** real-validator positive control, file/media/selection failures, repeated-check observations and checks that install/generation did not run.

#### Scenario: Check has no compatible current package
- **WHEN** a successful build or its tools are absent, or the installed library differs from the package recorded for that build
- **THEN** check fails with a concrete build command rather than preparing tools or calling old results a new build
- **AND** original build records, prepared input, images and source/package information remain unchanged
- **Verification:** clean-checkout check, removed-tool and changed-package controls with before/after file hashes.

#### Scenario: Refuse checking an absent result before starting an attempt
- **WHEN** the selected result root or its build record is absent, including after clean or distclean, and the contributor invokes Make matrix-check or the direct advanced check command
- **THEN** the command exits nonzero and names `make matrix-build CHARACTER=<selected-character> HEIGHT=<selected-height>` with the actual selected values
- **AND** no result directory, log, check report, tools or cache is created or modified
- **AND** the refusal does not start a check attempt or restore deleted history
- **Verification:** both routes against absent-root and absent-build-record fixtures, with complete fixture before/after comparison and exact remedy assertion.

### Requirement: Matrix success has a limited and explicit meaning

Guides and results SHALL distinguish tool preparation, local build/file checking and full library acceptance. Package checks, full host/domain checks, comparisons across variants, baseline/repeatability packs and process-safety checks remain separate workflows. Matrix SHALL not run or imply them. Existing human decisions and the paused character change remain applicable.

#### Scenario: Follow the manual offline workflow
- **WHEN** the contributor follows documented advanced list/build/check commands for male H1.70 with prepared offline tools
- **THEN** commands use the selected character/height, explicit work directory and listed result/log paths without requiring a caller-created execution plan or run names
- **AND** missing installation/Blender prerequisites produce an error rather than automatic repair in that advanced route
- **AND** local success grants no human visual approval, complete matrix acceptance or permission to resume paused work
- **Verification:** independent prepared-tool walkthrough, missing-prerequisite controls and result/guide scope checks.

#### Scenario: Follow the self-preparing selected workflow
- **WHEN** a contributor follows Make list/build/check commands for male H1.70 from a clean supported checkout
- **THEN** build requires only character/height choices and uses project defaults for tools, cache and results
- **AND** callers do not supply an execution plan, package selection or internal run naming
- **AND** setup failures give an actionable remedy without changing the dependency lock or substituting Blender
- **AND** local success grants no human visual approval, full matrix acceptance or permission to resume paused work
- **AND** the prepared offline advanced route remains documented
- **Verification:** independent literal walkthrough using controlled generation, stage-order observations and scope/pause checks.

### Requirement: Every attempt leaves a log while current data is replaced

Each started build/check SHALL write a distinct ordinary log file in the selected pair's log directory. A check attempt starts only after its read-only prerequisite checks establish that the selected result root and build record exist and their paths are safe. A refusal for an absent result is therefore outside this logging obligation. Once a check attempt starts, failed validation SHALL still write its distinct log and current failure report, including failures caused by a malformed or incompatible build record or damaged result files. The log SHALL retain the selection, command, start/end time, diagnostic package/backend information, output/error messages and final exit outcome. Current reports SHALL remain small and need no separate allocation, publication or latest-pointer protocol. Only logs SHALL remain as history of previous matrix attempts during ordinary matrix operations. Explicit Make clean/distclean SHALL remove those logs with the rest of their selected local build areas; historical status SHALL not exempt them.

#### Scenario: Diagnose a failed or repeated action
- **WHEN** an action fails, is interrupted or is later repeated
- **THEN** its log remains readable independently of temporary/generated data removed by that matrix action, until an explicit Make cleanup selects the log area
- **AND** its current result cannot claim success unless the action completed
- **AND** accidental duplicate/overlapping commands carry no supported-result or successful-start guarantee; their logs record observed results without locks or owner discovery
- **Verification:** failure/interruption/repeat logs and current-result assertions; overlap correctness is not an acceptance criterion.

#### Scenario: Preserve diagnostics for failed validation of an existing result
- **WHEN** the selected result root and build record exist at safe paths but the record is malformed or incompatible, or declared result data is damaged
- **THEN** each Make or direct check attempt writes a distinct failure log and current failure report
- **AND** the build record, prepared input, generated images and recorded source/package information remain unchanged
- **Verification:** malformed-record, package-mismatch and damaged-file controls with failure-log/report assertions and unchanged original-file hashes.

#### Scenario: Explicit cleanup removes local matrix history
- **WHEN** make clean or make distclean selects a local matrix result area
- **THEN** its logs and result files are removed completely, including unknown nested files, without an ownership inventory or legacy-reference scan
- **AND** Make matrix-check and the direct advanced check command afterwards report the exact selected build remedy without creating any directories, logs or reports when the selected result or build record is absent
- **Verification:** disposable matrix tree, unknown/log removal controls, both check routes and unchanged-tree/no-generation assertions.

### Requirement: Temporary and failed data is removed safely

A terminal action SHALL remove its temporary data and, after failed build, its partial generated output. A new build SHALL clear only the declared current output of its selected pair. Ordinary matrix-action cleanup SHALL preserve logs, unrelated files, installed tooling and other variants. Explicit Make cleanup SHALL instead remove everything in its fixed selected areas, including local history and unknown files; no historical label or reference SHALL create an exemption. An uncompleted cleanup SHALL be recorded as such rather than silently reported successful.

#### Scenario: Replace only the selected current data
- **WHEN** build succeeds, fails or repeats after abrupt termination
- **THEN** old temporary/partial data is removed from its declared location
- **AND** earlier attempts survive only in their logs until explicit Make cleanup selects those areas, not in UUID/stage/archive trees
- **AND** ordinary action cleanup never follows a symlink or removes other variants; explicit Make cleanup follows its declared wider areas without traversing link targets
- **Verification:** success/failure/leftover fixtures, containment/symlink/foreign-content negatives and cleanup accounting.

## ADDED Requirements

### Requirement: Matrix discovery works before environment setup

Default Make help, explicit help and matrix listing SHALL work with Make and a POSIX shell before Python, HML, uv or Blender is prepared. Help SHALL describe prerequisites and goals. Missing matrix choices SHALL show the required values and start no preparation or generation; build/check SHALL retain their explicit character/height choice.

#### Scenario: Discover commands and required selection
- **WHEN** a contributor runs `make`, `make help`, `make matrix-list`, or a matrix action without character/height
- **THEN** readable help/list or choice guidance appears before any tool preparation and gives the nine supported pairs and fixed result paths where appropriate
- **AND** no tools, cache, output, installation or Blender process is created
- **AND** unknown/invalid supplied choices remain nonzero failures before work
- **Verification:** literal commands with no Python/uv/Blender on PATH, before/after filesystem comparison and agreement with the direct command's table.
