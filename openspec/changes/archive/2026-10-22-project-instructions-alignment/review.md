# Independent review — project-instructions-alignment

**Verdict: PASS**, 2026-10-22, scoped to local instruction-policy reconciliation.

No blocker, major or minor findings. This is a text review pack/report; no new human visual gate applies. Existing anatomical/render acceptance and human decisions are not reopened or extended by this verdict.

## Sources and actual checks

Read the reconciled proposal, design, tasks and complete `project-governance` delta after the implementation-ready freeze. Independently audited current `AGENTS.md`, `.codex/config.toml`, all three role TOMLs, `tools/README.md`, the register introduction/configuration-reference entry in `docs/used-materials.md`, license declarations, and the existing main `anatomical-skeleton`, `joint-mobility` and `build-artifact-lifecycle` contracts. The literal `/AGENTS.md` is absent; repository `AGENTS.md` was used.

Allocated fresh `build/project-instructions-alignment_r1_reviewer_try-1_review/` and generated `policy-checks.json` (3136 bytes) plus text-pack `index.md` (176 bytes). These recorded commands/results, 17 policy assertions, exact-rational arithmetic, the four-file TOML parse and source SHA-256 snapshots. The compact durable results are consolidated below; the disposable run has been removed.

- `python3` with standard-library `tomllib`, `fractions`, `math`, `hashlib`, `json`: **4/4 TOMLs parsed**, **17/17 local policy assertions passed**. No dependency installation or permanent validator was introduced.
- `.codex/config.toml`: `[agents].max_concurrent_threads_per_session = 3`, `max_depth = 1`; comments distinguish host/runtime availability and V1-only depth behavior from OpenSpec lifecycle ordering. Parsing is verified; active runtime support/enforcement of these keys is **not verified**.
- `openspec validate project-instructions-alignment --strict`: **PASS**.
- `git diff --check`: **PASS**. At review time, tracked changes were only the four reconciled planning artifacts in this change. Current instruction/configuration files were read, not modified. The new main governance specification is intentionally absent pending the orchestrator's separately authorized post-PASS sync; sync is not claimed complete here.

## Requirement/scenario checklist

`A` = automatable text/TOML audit; `N` = numeric policy arithmetic. Every result below is **PASS within its stated local scope**, not a runtime implementation verdict.

| Requirement or scenario | Check | Result / evidence |
| --- | --- | --- |
| Beat sampling is explicit | A/N | PASS: AGENTS timing section defines `60 / BPM`, count boundaries, shared keyed animation and `max(3, ceil(T_beat / 200 ms))`; unchanged joint-mobility timing contract agrees. |
| Sampling a full-beat transition | N | PASS: exact rational checks at 60/120/180 BPM below; beat endpoints lie on interval boundaries; static boundaries included by policy. |
| Project licenses and motion provenance are explicit | A | PASS: AGENTS licensing/data sections assign Apache-2.0 and CC-BY 4.0 and require pose, segment and motion provenance; LICENSE-CODE/LICENSE-DATA declarations agree. |
| A motion is authored or composed | A | PASS: AGENTS requires source motion/segment identifiers, external references when used and applicable license; dev role explicitly requires all three source types' provenance. No runtime schema enforcement claimed. |
| An external reference or input is considered | A | PASS: AGENTS requires explicit commercial/derivative and distribution-compatible permission before use, rejecting missing/ambiguous/non-commercial/no-derivative or incompatible terms. Architect/dev carry clearance obligations; reviewer treats omitted/ambiguous/incompatible licenses as findings. |
| A cleared source informs project work | A | PASS: register introduction/template requires material/portion, URL, license/version/link, permission basis, conditions, date and outputs including CC0/no-attribution sources. AGENTS/dev require provenance links. Existing Codex configuration entry identifies AgentsToml/role fields, source/Apache-2.0 links, permission basis/conditions, date 2026-10-20 and related config/guidance. |
| Open IK representation remains unresolved until scoped | A | PASS: glossary explicitly defers new target choices until a concrete contact feature is designed; architect must define checkable acceptance. This conditional deferral does not revoke accepted capability contracts. |
| A contact feature is proposed | A | PASS: glossary, OpenSpec-before-implementation rule and architect scenario/verification requirements require scoped definition before implementation; no new representation is introduced here. |
| A scoped contact contract already exists | A | PASS: anatomical-skeleton canonical right-handed meters, +X right/+Y anterior/+Z superior and Z=0 floor remain; joint-mobility already fixes foot-local anchors, world-space targets, stature scaling and beat intervals. None is edited or required to be rebuilt. |
| OpenSpec lifecycle stays ordered while independent tasks may run in parallel | A | PASS: AGENTS Flow orders architect/human approval, dev, independent reviewer, human visual gate when applicable, archive; dev parallelism requires explicit non-conflicting ownership within an approved change. |
| Independent implementation tasks | A | PASS: AGENTS Flow step 3 and dev rules permit independent concurrent tasks while retaining change-level gates; configuration comments make no runtime ordering claim. |
| Implementation and acceptance use separate responsibilities | A | PASS: AGENTS confines main agent to orchestration/OpenSpec; role files separate specs, implementation and independent verification. Reviewer cannot fix sources or archive; visual-affecting changes require human visual approval. |
| Reviewer cleanup is bounded | A | PASS: reviewer write scope is report plus exact owned flat root; AGENTS/README/lifecycle require owned-unprotected cleanup, protected history/dependencies, explicit receipt and pending status. |
| Start a fresh owned review run | A | PASS: actual fresh path `build/project-instructions-alignment_r1_reviewer_try-1_review/` is a direct child with five lowercase-kebab components; previous outputs were not reused, deleted or relocated. |
| Complete checks and clean owned outputs | A/N | PASS: current instructions cover success/failure/interruption, inventory, dependencies, no external symlink traversal, ownership and justified retention; actual text pack consolidated and whole owned run removed with receipt below. |
| Verification needs cleanup outside reviewer ownership | A | PASS: reviewer instructions require exact-path developer hand-off and pause when obstructed; dev owns its outputs. No unrelated output obstructed this local review, so no actual developer deletion request was needed. |

## Numeric policy results

Computed with `Fraction(60, BPM)`, `n = max(3, ceil(T_beat / Fraction(1,5)))`, `dt = T_beat / n`; these checks did not import or exercise a runtime sampler.

| BPM | Beat seconds | Intervals/beat | In-between frames | Interval ms (limit <=200) | Four-beat animation samples | Static samples |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 60 | 1 | 5 | 4 | 200 | 21 | 5 |
| 120 | 1/2 | 3 | 2 | 166.666667 | 13 | 5 |
| 180 | 1/3 | 3 | 2 | 111.111111 | 13 | 5 |

Each beat has at least two intermediate frames and its endpoint at `n * dt = T_beat`. Counts use `4*n+1` and five beat boundaries, matching the existing scoped diagnostic policy. Fractional-beat allocation remains assigned to its owning timing/contact design.

## Findings and limitations

| ID | Severity | Violated requirement/scenario | Evidence | Suggested direction |
| --- | --- | --- | --- | --- |
| — | — | None within reconciled instruction scope | Local checks above | — |

The existing Codex configuration register entry was cross-checked locally; no upstream URL, current implementation semantics or license was revalidated online. Its recorded Apache-2.0 commercial/derivative permission, no-copied-code statement and conditions are explicit. No new external source, asset, or reference informed this reconciliation/review, and no new register entry was added. No blanket recertification of unrelated anatomical source licenses is claimed.

Runtime config-key support, concurrency/depth behavior, schema provenance enforcement and actual sampler/render behavior remain outside this local review. Blender/MPFB, browser checks, animation stability/contacts/direction/loops/mirror/bake round-trip/determinism and visual comparisons were not run: no source data, executable code, scene or media changes exist in this reconciliation. These exclusions follow the approved instruction-only design rather than waive feature-level acceptance requirements.

## Cleanup receipt

- Removed whole owned run: `build/project-instructions-alignment_r1_reviewer_try-1_review/` — **3312 logical regular-file bytes**, comprising `policy-checks.json` **3136** and `index.md` **176**. No symlinks or additional content were present; no residual directory/log/JSON remained.
- Retained generated roots/files: **none**. Durable evidence: this `review.md`, containing all necessary results and limits. The temporary text pack was obsolete after consolidation; nothing retained depends on it.
- Dependency checks: before removal, inventory matched exactly the two named files; source snapshots for all ten audited instruction/register/main-spec files matched their post-check hashes. The report preserves the path as a historical receipt, not an unresolved artifact link. After removal, its exact run root is absent and this report exists. No operational reference requires the temporary files.
- Protected/other ownership: no historical R2/R3 media was opened for mutation, scanned, regenerated or cleaned; no developer/other reviewer/accepted/protected root was changed. No broad historical hash claim is made.
- Developer cleanup hand-off: **none required**. Pending cleanup: **none**. No source fixes, checkbox edits, main-spec sync, archive or commit was performed by this reviewer.
