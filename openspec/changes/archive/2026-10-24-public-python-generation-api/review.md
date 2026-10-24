# Independent review: public-python-generation-api

## Verdict: PASS WITH NOTES

No open implementation blocker or major finding remains for the frozen candidate. Automated host, installed-workspace, real-backend, numerical and exact image comparisons pass. Human Gate 2 was subsequently **APPROVED** on 2026-10-24 by the human after viewing the focused review pack. The reviewer verdict and human decision are separate records.

Candidate wheel: `build/public-python-generation-api_r1_dev_try-1_distribution/dist/humanmotionlib-0.2.0-py3-none-any.whl`, SHA256 `c6e44fb366193ce615acc727708f25e91f603027413619d2429b2ec2af808907`. Independently installed non-editably under reviewer host and installed environments with CPython 3.14.6. Runtime manifest SHA256: `6ba4bc665af9902dcbcf7c87e9e03707337e0dc65089225749662362756f1d56`. Backend: Blender 5.2.2 LTS, build `d13f752e3b9c`, Darwin-arm64; MPFB/Rigify not used. Frozen wheel hash rechecked after rendering and pack assembly.

## Requirement and scenario checklist

Aliases below mean direct children of `build/public-python-generation-api_r1_reviewer_`: `host2` = `try-2_host`, `installed3` = `try-3_installed`, `numeric` = `try-1_numeric`, `pack` = `try-1_pack`, `api-render` = `try-1_api-render`, `api-repeat` = `try-1_api-repeat`. Repository instructions were read from `AGENTS.md`; `/AGENTS.md` does not exist. Proposal, delta specs, design and tasks were read before review. No project code, schema, canonical source or task checkbox was modified by the reviewer.

| Requirement or scenario | Verification class | Independent evidence |
|---|---|---|
| Public generation has a small importable contract | automatable check | PASS: host2/host.log; installed3/installed-acceptance.json |
| Import and call from a Python application | automatable check | PASS: host2/host.log; installed3/installed-acceptance.json |
| Preparation accepts explicit generation parameters | automatable check | PASS: host2/host.log; installed3/installed-acceptance.json |
| Prepare the existing supported coverage | automatable check | PASS: host2/host.log; installed3/installed-acceptance.json |
| Override and validate request parameters | automatable check | PASS: host2/host.log; installed3/installed-acceptance.json |
| Results expose pose and exact playback context | numeric metric | PASS: numeric/comparison.json timing and exact public joins; host API rational/BPM matrix |
| Interpret returned frames without parsing pipeline JSON | numeric metric | PASS: numeric/comparison.json timing and exact public joins; host API rational/BPM matrix |
| Rendering returns complete validated image results | automatable check | PASS: api-render/api-repeat receipts; CLI custom-frames receipt; pack-audit.json; host image inventory/mode/fault tests |
| Render a prepared subset | automatable check | PASS: api-render/api-repeat receipts; CLI custom-frames receipt; pack-audit.json; host image inventory/mode/fault tests |
| Preserve existing construction modes | automatable check | PASS: api-render/api-repeat receipts; CLI custom-frames receipt; pack-audit.json; host image inventory/mode/fault tests |
| Generation exposes resolvable provenance | automatable check | PASS: numeric/comparison.json provenance; 51 hashed sources, 14 registered material IDs; unchanged register/notices; no new external material |
| Follow generated-data attribution | automatable check | PASS: numeric/comparison.json provenance; 51 hashed sources, 14 registered material IDs; unchanged register/notices; no new external material |
| Reject uncleared new reference use | automatable check | PASS: numeric/comparison.json provenance; 51 hashed sources, 14 registered material IDs; unchanged register/notices; no new external material |
| API failures are catchable and retain evidence | automatable check | PASS: host2 API/supervisor fault and cancellation cases; installed3 structured missing-backend receipt; no partial success |
| Diagnose validation and backend failures | automatable check | PASS: host2 API/supervisor fault and cancellation cases; installed3 structured missing-backend receipt; no partial success |
| API execution preserves installation and workspace boundaries | automatable check | PASS: installed3 read-only-permissions.json and installed-acceptance.json; all host paths/freshness scenarios; real supervised external backend |
| Use an installed API from an unrelated directory | automatable check | PASS: installed3 read-only-permissions.json and installed-acceptance.json; all host paths/freshness scenarios; real supervised external backend |
| CLI generation delegates to the public contract | automatable check | PASS: host CLI delegation matrix, installed console/module parity; actual CLI custom-frames render exact with API and baseline |
| Compare Python and command callers | automatable check | PASS: host CLI delegation matrix, installed console/module parity; actual CLI custom-frames render exact with API and baseline |
| Public results have a documented portable projection | automatable check | PASS: host mutation/hash/JSON projection cases; pack/public-result.json image/time/provenance links audited |
| Consume and serialize a result safely | automatable check | PASS: host mutation/hash/JSON projection cases; pack/public-result.json image/time/provenance links audited |
| API integration preserves generation output and visual review | numeric metric + human visual judgement | Numeric PASS: numeric/comparison.json and stability-contacts.json; design pack complete. Human Gate 2 APPROVED on 2026-10-24. |
| Compare API generation with the existing workflow | numeric metric + human visual judgement | Numeric PASS: numeric/comparison.json and stability-contacts.json; design pack complete. Human Gate 2 APPROVED on 2026-10-24. |
| Human pose/time correspondence, movement readability, stable contacts/framing, baseline/API/CLI agreement | human visual judgement | APPROVED: explicit human decision after reviewing the pack on 2026-10-24; no visual errors reported. |

## Reproduction and scope

- Full locked installed-wheel host suite: `HUMANMOTIONLIB_TEST_RUN_ROOT=<host2> HUMANMOTIONLIB_SOURCE_ROOT=<checkout> PYTHONDONTWRITEBYTECODE=1 <host1>/environment/bin/python -m humanmotionlib.check_host --test-root <checkout>/tests`. **204/204 pass, zero skips**. Only the configured real-Blender modules were excluded: `tests.test_blender_backend` (6 tests), `tests.test_pipeline_faults` (1 test). These are not claimed as real-backend fault acceptance.
- All-source schema/integrity validation: `<host1>/environment/bin/python -m humanmotionlib validate --profile adult-reference-v1`; `host1/source-validation.json`: **180 structures, 67 actions, 3 placements, 32 fixtures**.
- Installed workflow fixture: `<installed2>/environment/bin/python <installed3>/run-readonly.py --python <installed2>/environment/bin/python --workspace <installed3>/fixture-workspace --run-root <installed3>`. The disposable reviewer copy retains all repository runner assertions and adds removal of write permission bits from the installation and unrelated invocation/hostile directories. `installed3/readonly-permissions.json`: **124 entries, all write bits zero**. `installed3/installed-acceptance.json`: **PASS**, 900 prepared all-fixture samples, public subset 18 poses/4 timelines, complete attribution, console/module parity, immutable package/cwd, controlled missing-backend error and receipt, synthetic presentation/path negatives. This fixture workspace is disposable workflow-check content within the reviewer-owned root, not an independent production generation run.
- Source builds were independently prepared from the frozen installed wheel. First API render accepts an explicit prepared-file path; the clean repeat prepares anew and passes `PreparedResult`. Candidate CLI independently prepares and renders with `--render-dir .../custom-frames`, exercising the repaired non-default directory contract. All three have disjoint direct-child preparation/render roots and successful pinned probe/render receipts. `host1/render-api.py`, `host1/render-repeat.py`, logs and exported results retain the Python calls; `pack/pack-audit.json` identifies the six exact receipts.
- Numerical reproduction: `PYTHONDONTWRITEBYTECODE=1 <host1>/environment/bin/python <numeric>/check.py`, plus `stability.py`; existing `verify_transforms` and `verify_backend` run against 31 independently evaluated samples. Full anatomical collection coverage is deliberately not asserted for this three-fixture integration comparison.
- Baseline is read-only: developer `try-2_baseline-prepare` and `try-3_baseline-render`. Baseline data, geometry and decoded pixels were independently compared, rather than accepting developer claims. Substantive sources, poses, expected actions, controls/rest policy, contacts, timing, units and backend contract agree exactly. Package/implementation identity and packaged documentation hashes legitimately changed; those are separated from content comparison. `.blend` byte ordering and timestamps are not equality gates.

## Measured gates

| Gate | Actual | Tolerance / expectation | Evidence |
|---|---|---|---|
| Existing evaluated numerical verifier | 198,593 checks / 31 samples; 0 failures | Existing unmodified per-metric tolerances | numeric/existing-backend-metrics.json |
| Baseline/API, API/repeat, API/CLI pixels | 76 corresponding images per group; 0 differing decoded pixels | Exact equality | numeric/comparison.json |
| Pose / evaluated geometry | Exact substantive prepared fields, evaluated samples and geometry-reference content | Exact baseline/API/repeat/CLI agreement | numeric/comparison.json |
| Arm-raise animation | 21 / 13 / 13 samples at 60 / 120 / 180 BPM; static 5 each | Exact sampling plan; ≥2 in-between samples per beat | numeric/comparison.json; pack/png-timing.json |
| Maximum animation interval | 200 / 166.6666667 / 111.1111111 ms | ≤200 ms | numeric/comparison.json |
| Custom 90 BPM host timeline | 17 entries, beat 2 = 4/3 s | Exact Fraction values, distinct from legacy 120 BPM seconds | host2 API tests; installed3 API scenario |
| Camera / floor / light | Evaluated scene identical across 31 samples | Exact equality | numeric/comparison.json |
| Outside-body background / floor pixels | 0 differences across 23,993,940 front and 27,977,640 side comparisons | Exact equality outside conservative warm-bone silhouette bbox dilated by 8 pixels | numeric/stability-contacts.json |
| Root drift | 0 m | ≤0.00017 m (=1e-4 H) | numeric/comparison.json |
| Floor / contacts | Minimum evaluated floor height 0 m; maximum sliding residual 0 m across 186 checks | Floor ≥−0.00017 m; sliding ≤0.0017 m | numeric/stability-contacts.json |
| Loop closure | Position and rotation matrix component differences 0 for neutral/rest/arm-raise | Position ≤0.00017 m; rotation component ≤1e-6 | numeric/comparison.json |
| Bilateral mirror | 5,456 evaluated frame pairs; position residual 0 m; maximum angle error 0.0238983563° | ≤0.00017 m; ≤0.1° | numeric/mirror.json |
| GIF loop duration | 0 ms error at 60/120 BPM; 3.3333333333 ms at 180 BPM | <10 ms centisecond quantization bound; terminal duplicate represented by next loop start | pack/gif-timing.json |
| Pack integrity | 77 evidence links, 17 decoded media files, all 76 public image paths and PNG timing paths resolve | No broken links or missing media | pack/pack-audit.json |

Via-based circular direction and bake round-trip/export are not introduced by this change and do not apply to the diagnostic arm raise. Existing action-direction, FK round-trip and mirror host tests passed. No new rotation convention, dependency, canonical format, rig, camera, light or floor change was found. The `review_pack` refactor re-exports existing private helper names and preserves its regression tests while sharing validation through `render_contract`.

## Findings

No open finding remains in the frozen candidate.

| ID | Severity | Requirement / scenario | Evidence | Suggested direction / disposition |
|---|---|---|---|---|
| R1 (resolved) | major | Rendering returns complete validated image results / Preserve existing construction modes; CLI compatibility | Pre-freeze validator hardcoded `frames/`; shared `render_contract` now uses the actual output-relative directory. Independent real CLI custom-frames receipt and exact 76-image comparison pass. | Resolved before candidate freeze; retain regression coverage. |
| R2 (resolved) | major | API failures are catchable and retain evidence / Diagnose validation and backend failures | Pre-freeze malformed manifest returned invalid-request or raw AttributeError; static/static-faults.json. Candidate catches malformed output at backend/public validation boundaries; independent host malformed-manifest tests pass. | Resolved before candidate freeze; retain structured output-integrity classification. |

## Provenance and licensing audit

No new external reference, example, anatomical claim, dataset, asset, font or runtime dependency was used by this change or this review. Reviewer composites use repository-authored bitmap lettering and existing Pillow tooling. All 51 public source records were independently matched to exact packaged source bytes, including explicit absent provenance for resources without source-level records. All 14 recursively referenced material IDs resolve to the returned complete used-materials register. Nested profile/mobility provenance, locators and adaptations remain present. Returned LICENSE-DATA, LICENSE-CODE and THIRD-PARTY-NOTICES contents preserve CC-BY-4.0 data, Apache-2.0 code and third-party attribution/permission conditions. Existing registered material clearances and their portion restrictions were reused; no public-availability inference or newly introduced external material requires clearance. Full-fixture host/source coverage is distinct from focused visual acceptance.

## Reviewer visual observations (opinion only)

I inspected the full neutral/rest comparison, arm-raise count/animation sheets, original frames and front/side onion overlays. Neutral has arms down; rest has arms out horizontally. The side sequence shows the arms moving forward and upward to overhead by beat 2, then returning by beat 4. In the front projection, forward arms overlap the torso and each other, so direction is easier to read in the side view. Large empty margins and the thin low-contrast skeleton are unchanged from baseline. Feet and the horizontal floor line appear fixed, with no new drift or obvious floor penetration. Baseline/API/CLI rows appear identical, consistent with exact pixels. These observations do not approve readability, anatomical appearance or exercise correctness for the human.

## Human Gate 2 decision and scope

On 2026-10-24, the human explicitly approved the focused pack in response to the request to confirm pose/time correspondence, movement readability and stable feet/framing, stating (English translation): "Yes, visual inspection found no errors." This completes Human Gate 2 for the reviewed baseline/API/CLI comparison. The focused pack is `build/public-python-generation-api_r1_reviewer_try-1_pack/index.md` (HTML launcher `index.html`). All-frame/count/animation sheets, front/side/paired timed GIFs and the exact thirteen 120-BPM onion poses are included. No full anatomical/mobility visual re-approval, clinical validation, via circle or bake/export acceptance is implied. The generated pack's original pending labels describe its state before this human decision; this record captures the subsequent approval.

## Cleanup and retained dependency closure

Cleanup inventory, removed paths/bytes, symlink targets and before/after dependency checks are in `pack/cleanup.json`; post-cleanup links are in `pack/pack-audit.json`. Removed **833,570,357 bytes**: `build/public-python-generation-api_r1_reviewer_try-1_installed` (804,325,443 bytes); `build/public-python-generation-api_r1_reviewer_try-1_host/cache` (22,553,270 bytes); `build/public-python-generation-api_r1_reviewer_try-1_pack/paired-frames` (6,691,644 bytes). No symlink target was followed during removal; no inbound retained-evidence links targeted removed content. Post-cleanup audit still passes all 77 links, 17 media files and 76 public image paths. The first installed attempt was invalidated by concurrent bytecode writes from another reviewer command using its shared environment; a fresh isolated installed environment and then the explicit read-only fixture both passed. The first host attempt was affected by sandbox process-group inventory restrictions; the fresh escalated host attempt passed all 204 tests. These are reviewer execution corrections, not candidate failures.

Retain until Human Gate 2 and final review no longer depend on them: API/CLI/repeat preparation and render roots (source images and receipts), numeric (full metrics and reproducible comparison scripts), pack (accepted media/result/link evidence), host1 (candidate environment/package paths used by receipts, source validation, result exports and command scripts), host2 (final host evidence), installed2 (candidate environment referenced by installed3), installed3 (final read-only installed evidence), and tiny static (resolved-finding diagnostic). Baseline and final wheel are developer-owned read-only dependencies; the reviewer did not alter or clean them. Reconsider retained runs after the human gate/final review or a superseding candidate. No reviewer cleanup remains pending; developer cleanup is recorded separately by its owner.
