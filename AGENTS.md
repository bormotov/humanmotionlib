# AGENTS.md

Open library of humanoid **poses, segments and motions** for exercise (morning gymnastics) animations.
Blender is a backend: the source of truth is plain data in this repo; Blender turns it into frames and clips.

Talk to the human in Russian. Everything in the repo (code, specs, docs, commits) is in English.

> If `openspec init` adds a managed block to this file, leave it untouched and keep project content outside it.

---

## 1. Goals

1. From a text description of an exercise ("count 1: raise arms, count 2: lower them") produce one set of frames for two uses:
   - **Static**: one image per count, flipped on the beat.
   - **Animation**: low fps, frame interval ≤ 200 ms, at least two in-between frames between counts, so the direction of movement is unambiguous (e.g. clockwise vs counter-clockwise arm circle).
2. Frames are geometrically stable: fixed camera, distance and floor; no character drift unless the motion requires it.
3. A reusable library (poses, segments, motions, rig description) that others can use under a free license.

**Non-goals**: mocap-quality realism, a real-time runtime, a new skeleton standard, web/mobile players, image-model frame generation (it drifts).

---

## 2. Concepts

| Term | Meaning |
|---|---|
| **Pose** | Named static configuration: bone rotations (FK) and/or IK targets for a set of body groups. |
| **Segment** | Named transition between poses: `from`, `to`, optional `via`, duration in beats, easing, `controls`. E.g. `step_right`. |
| **Motion** | Composition of segments: sequence, repeat, parallel layers over different body groups. E.g. `march_in_place`. |
| **Body group** | Unit of masking: `pelvis`, `torso`, `head_neck`, `arm_L`, `arm_R`, `leg_L`, `leg_R` (hands/fingers may be added later). Larger masks are unions (lower body = pelvis + legs). |
| **Controls / rest policy** | `controls` = groups a segment writes. All other groups follow the rest policy: `hold` (keep previous pose), `base` (follow the base pose), `free` (driven by another parallel layer). |
| **IK target / contact** | Intent data: where a foot/hand must be and when it is pinned to floor/object. Coordinate space, normalization and units are defined by the change that introduces contacts. |
| **Beat** | Unit of time in sources; seconds come from BPM at render/bake time. |
| **Bake** | Converting solved IK, constraints and procedural layers into plain FK keyframes. |

Rules:
- A segment writes keys only on its `controls` (this is the mask). List every group that really moves: a squat controls pelvis and torso too, not only legs.
- Circular movements need explicit `via` poses (interpolation takes the shortest path).
- Mirror left/right in code; prefer parameters (e.g. `knee_height`) to copies of variants.
- Procedural layers (noise, overlap) are separate and off for static frames.
- Feet stay planted and the root does not drift unless the segment says otherwise.

---

## 3. Data and formats

1. **Source (canonical)**: YAML in `poses/`, `segments/`, `motions/`, validated by JSON Schema in `schema/`.
   - Bones: VRM humanoid names, mapped explicitly from the MPFB/Rigify rig.
   - Rotations: local, relative to the rest (T-)pose. The convention is fixed in the foundation change and changes only via a MODIFIED requirement.
   - Time in beats; named easing (`linear`, `ease_in_out`, ...).
   - Every pose, segment and motion has `description` (English) and `provenance` (section 8).
2. **Baked clips** (`dist/`): glTF/GLB, VRMA (`.vrma`), BVH, `.blend` with Pose Library assets.
   - glTF has no IK/constraints: bake to FK before export.
   - VRMA: translation only on hips, no scale animation.
3. **Contacts sidecar** (`*.contacts.json`): contact intervals and IK target trajectories, so consumers with other proportions can fix foot sliding. Format per the contacts change. (Whether VRMA can carry helper nodes is unverified, so the sidecar is the reliable path.)
4. **Reference renders** (contact sheets, GIFs): documentation, not a source of truth.

### Timing
- One count = one beat, `T_beat = 60 / BPM` s.
- Static and animation frames are sampled from the **same** keyed animation; no separate hand-made sets.
- Static: one frame at each count.
- Animation: per beat, `n = max(3, ceil(T_beat / 200 ms))` intervals, i.e. ≥ 2 in-between frames and a step ≤ 200 ms.
- Segment boundaries land on frame boundaries; allocation for fractional-beat segments is defined by the timing change.

### Scene and render
- Camera: fixed, orthographic (or long-focal), defined once in `scenes/`, never moved per exercise. Floor and light fixed.
- Same character, resolution and file naming for all frames.
- Eevee or Workbench for iteration; Freestyle contours optional.
- Deterministic: same sources + same Blender version = same frames. Pin Blender and MPFB versions in the repo and record them in render metadata.

---

## 4. Process: OpenSpec

Every non-trivial work item is an **OpenSpec change**: specs describe behavior, code follows.

```
openspec/changes/<change-id>/
  proposal.md                  # why, what, impact
  specs/<capability>/spec.md   # delta: ADDED / MODIFIED / REMOVED requirements + scenarios
  design.md                    # technical approach (when needed)
  tasks.md                     # checklist for dev
```
CLI (slash commands vary by version, check `openspec --help`): `openspec list`, `openspec validate <id>`, `openspec archive <id> --yes`.

### Roles
**Main agent = orchestrator.** It answers the human and manages OpenSpec changes (create, update, validate, archive proposals, specs, tasks). It must NOT design, write, modify or review project code; that is delegated.

**Subagents** (`.codex/agents/`): the human explicitly instructs the main agent to spawn them, by role name, for all design, implementation and review work. This is a standing instruction: do not wait for a per-task request. When unsure whether to delegate, delegate. Run independent tasks in parallel.

| Role | Does | Does not |
|---|---|---|
| **architect** | Technical design and architecture decisions. | Write implementation code. |
| **dev** | Implements `tasks.md`: schemas, tools, Blender scripts, poses/segments/motions, bake/export. Headless Blender CLI; Blender MCP only for exploration. | Change requirements or acceptance criteria. If a spec is wrong or ambiguous: stop, report to the architect. |
| **reviewer** | Verifies the change against the specs from a clean state: validators, tests, re-render, metrics, license/provenance. Produces review pack and verdict. | Fix code (reports findings; dev fixes). |

### Flow
1. The human states the task.
2. The change is drafted (main agent, with architect for design). **Gate 1**: the human approves the spec and, for visual-affecting work, its bounded early-preview plan before implementation.
3. dev implements the smallest coherent visual result, clears/registers external sources before use, and runs only selected source/schema/identity/environment checks plus focused checks needed to produce the preview. The plan names exact fixture/pose/segment, visible variants, views/details, stature and tempo, and deferred full scopes. Do not start full suites, full diagnostic/tempo/stature matrices, dense audits, repeated render comparisons or full acceptance packs before an explicit human early decision.
4. dev produces the bounded preview from canonical sources and the fixed scene. The orchestrator presents its identity, artifacts, scope and limitations and records **Early visual gate: accepted / rejected / pending** with the exact human-message reference in the existing change hand-off. Silence, a generic request to continue, developer opinion, passing metrics or a running process is not acceptance. Rejection or no decision blocks expensive verification for that visual direction; make only the approved correction and a fresh preview.
5. After early acceptance, conduct the existing joint pre-freeze audit, resolve in-scope discrepancies, freeze and identify the candidate, then run required full verification and independent review. Early acceptance does not replace technical checks, independent review or final human visual approval. Nonvisual changes record `not applicable` with a reason.
6. reviewer writes `review.md` and any final pack in its own build run. **Gate 2 (visual)**: the human reviews the independently verified final pack (contact sheets, GIF, onion-skin). Required before archiving any change touching poses, motions, visible characters, scene or rendering.
7. Assess later source changes: appearance/pose/motion/scene/render changes require a fresh preview and renewed early acceptance before further expensive checks; technical-only changes record applicability while renewing checks required by identity rules. For in-flight changes, preserve completed evidence and its identity, do not invent retrospective early approval, and do not rerun completed expensive work only to simulate the new order. Keep final Gate 2. Fixes go back to dev (to the spec if requirements change). Then clean the role-assigned work area, record removals and pending failures, and archive only after required gates. Explicit Make cleanup uses the fixed build areas in section 5; no historical result inside a selected area is exempt.

### Before the final candidate freeze

- Before starting expensive final builds and independent review, the orchestrator, architect, dev and reviewer conduct a short joint audit of the approved requirements and scenarios, documentation and runnable examples, negative and integrity cases and their positive controls, supported API/CLI modes and combinations, environment/process preflight, source/package closure, and the evidence and review plan. The orchestrator records the result and unresolved findings in the change hand-off. Each role checks its own scope; this audit does not replace independent review or either human gate.
- Resolve discrepancies within the approved scope before freezing the candidate; refer requirement or acceptance changes to the architect and the human as required by the flow. Record the candidate's source and package identity after the audit. If those inputs later change, reassess and rerun the identity-bound checks required by the change; never relabel earlier evidence.

For visual-affecting work, the early preview and explicit human decision happen before this pre-freeze audit and before full verification. Preview prerequisites may include source clearance, selected schema/identity validation, uv/process/environment preflight, focused smoke checks and one candidate packaging step required by the installed workflow. They do not authorize the deferred full workloads above. If no safe bounded route exists, return to the architect before running those workloads. The final candidate audit and identity-bound checks remain mandatory after acceptance.

### Long-running work and context

- Prefer event-driven completion notifications or waits that return when state changes. Otherwise use the longest wait allowed by the tool and higher-priority instructions (blocking waits must not exceed 60 seconds), and back off rather than repeatedly polling unchanged state. Assign one monitor per long-running process, batch related status checks and combine progress messages around meaningful changes, while still satisfying required user updates and responding to new input. Do not interrupt or restart an active process merely because it has no new output; check liveness and ownership before recovery.
- When context approaches its limit or compaction repeatedly disrupts progress, write a concise checkpoint in an existing change hand-off or review record, preferably no more than 1–2k tokens. Include the objective and decisions, exact candidate and evidence paths/identities and scopes, completed and pending checks, active process ownership and resumable runs, blockers, cleanup and human gates. Prefer references and measured facts over copied logs. Do not treat a checkpoint as acceptance or interrupt an active process merely to create it.
- Continue from the checkpoint in a fresh context when the available workflow supports it and required user authorization is present. Recheck project instructions and current files and processes, preserve the original task and constraints, and avoid redoing completed work or inferring approval. Keep using the current context if a fresh one cannot be created. Do not create a Git branch or worktree merely as a context-management step.

### Rules
- One logical change per proposal; small changes get a short one.
- Tasks are small and verifiable; a task without a check is a spec defect.
- "Looks fine" never marks a requirement as met; the reviewer checks scenarios and cites the violated requirement in each finding.
- If the exercise description is ambiguous (direction, amplitude, tempo), ask the human; do not guess.
- Record decisions in `design.md`.
- No new dependencies, formats or conventions (rotation order, bone names, units) without an OpenSpec change (MODIFIED requirement + migration).

---

## 5. Build runs

- Every new independent build, check or review run is a direct child of `build/` (gitignored) named `<change>_<revision>_<role>_<attempt>_<kind>/`: five components joined by `_`, each lowercase kebab-case (`[a-z0-9]+(-[a-z0-9]+)*`).
- Fresh, empty run root per attempt; retries are not nested. Tool-required subdirectories (`frames/`, `assets/`, ...) may live inside a run.
- Input and output roots of independent runs are distinct and disjoint, also after resolving symlinks. Accepted or protected legacy paths may be read, stay unchanged and are not relocated.
- Normal allocation remains sibling-only and never replaces earlier runs. Role-scoped automatic cleanup remains inside the role's assigned work area; do not broaden it or remove another role's active work.
- Explicit Make cleanup selects fixed areas: `mostlyclean` removes every direct `build/*_stage` and `build/*_check` entry except the configured reusable tools root; `clean` removes every direct build entry except that tools root; `distclean` removes all of `build/`. The tools-root exception applies even when its basename ends in `_stage` or `_check`. Every object inside a selected area is disposable, including unknown files, local history/R6 and matrix logs. Do not add owner markers, file inventories, reference scans or history exemptions.
- Cleanup checks activity and real path containment before removal. Enumerate without following symlinks and unlink a selected link entry without traversing its target. Unavailable process visibility, active work or an escaping boundary blocks removal. Record removed paths/bytes and pending failures in the existing hand-off/review; a failed/interrupted cleanup remains pending.
- Keep durable decisions/reports and releases outside the selected cleanup areas. Do not run broad Make cleanup against real build data merely to test it; verify those rules on disposable trees.

---

## 6. Quality gates (automatable; the reviewer runs them)

- **Schema**: YAML validates; bone names resolve via the rig map.
- **Timing**: frame count and times match the timing rule for the given BPM.
- **Stability**: camera, floor and light identical across frames (background and floor pixels match outside the character mask); root drift within tolerance unless declared.
- **Contacts**: foot sliding on declared floor contacts below tolerance; no floor penetration.
- **Direction**: for motions with `via`, swept angle and direction match the declared ones.
- **Loops**: last pose equals first within tolerance.
- **Mirror**: a mirrored segment equals the original with L/R swapped.
- **Bake round trip**: the baked clip applied to the rig reproduces the source frames within tolerance.
- **Determinism**: two clean renders from the same sources are identical, unless the spec states a tolerance.
- **Licensing**: provenance and register entries present (section 8).

Visual judgement (readable? looks like the exercise?) stays with the human.

---

## 7. Tooling

- From a checkout, the ordinary repository entry point is `make`: it prints
  requirements and goals without Python, uv or Blender. Require Make and a
  POSIX shell to read help; repository `dev`/`package` goals additionally
  require uv `>=0.11.21` and first-use network access, and selected rendering
  requires the pinned Blender below. The Make workflow prepares its reusable
  CPython 3.14 environment and uv cache under the configured project `build/`
  tools root, rebuilds the current package before source-consuming operations,
  and keeps command details in `tools/README.md` and `docs/build-matrix.md`.
- The ordinary routes are `make dev`, `make package`, `make matrix-list`,
  `make matrix-build CHARACTER=... HEIGHT=...`, and the matching
  `make matrix-check`. Cleanup is `make mostlyclean`, `make clean`, or
  `make distclean`; these need Make, POSIX shell and the basic system tools
  listed by `make` help, including process inspection, not Python/uv/Blender.
  Every object in a selected area is removed; unknown/history entries have no
  local exemption, while active work and paths outside the selected area remain safe.
- Python via `uv`. Blender headless: `blender --background <scene> --python tools/<script>.py -- <args>`.
- Create each new Python virtual environment with `uv venv` and install its dependencies and exact candidate package with `uv pip`; do not clone an existing virtual environment, copy its `site-packages`, or add `.pth` links to another environment or checkout. Keep the environment and a writable uv cache in its owned run root where applicable, preserve pinned dependency versions, and follow the applicable network and approval rules.
- Immediately after installation and before the first test in a new isolated environment, record the interpreter and `sys.prefix`, installed package and dependency import origins and versions, `.pth` contents and unexpected external paths, package identity, cache location, and `uv pip check`. Verify that tested imports and subprocesses use the intended interpreter. Before process-supervision tests, also check the required process-inspection permissions under the same privileges. If process visibility is unavailable, report the limitation and obtain the required access rather than bypassing ownership checks or treating the result as a product failure.
- Prefer headless CLI for everything reproducible (render, bake, tests). Blender MCP is for inspecting or prototyping; its results count only once turned into scripts in `tools/`.
- No reliance on Blender GUI state; scenes and rigs come from repo files. No absolute paths or machine-specific settings in tools.
- Rigify: arms normally FK, legs IK (feet planted). Property names depend on the version: inspect the actual rig.
- Keep commands in one place (`tools/README.md` or a task runner); do not add entry points silently.
- No binaries in git except releases in `dist/`. Never hand-edit generated files in `dist/` or `build/`.
- Never move the camera or floor to "fix" a frame; fix the data.

---

## 8. Licensing and provenance

- Data and authored assets (poses, segments, motions, baked clips, renders): **CC-BY 4.0** (`LICENSE-DATA`). Code: **Apache-2.0** (`LICENSE-CODE`).
- Third-party assets (character, rig, scene, MPFB assets, ...) keep their own licenses; clear and record them before use in outputs.
- **Every source material used to do a task or inform content needs commercial-use clearance**, even as a mere reference: textbooks, papers, illustrations, descriptions, videos, datasets, web pages, third-party assets.
  - Verify that the license and terms explicitly permit commercial use of the result and are compatible with the distribution license. Public availability, educational purpose or no visible restriction is not permission.
  - Missing, ambiguous, non-commercial, no-derivatives or conflicting license: do not use it. Find a clearly permitted alternative or ask the human.
  - Copy joint angles, illustrations, text or other protected expression only if the verified license permits the intended commercial derivative and distribution.
  - CMU Mocap, Mixamo and non-commercial research datasets are not approved unless the specific material's current license is checked and permits it.
- **Register** `docs/used-materials.md`: every external material actually used, including CC0/public domain and licenses without attribution; not materials merely found. Per entry: material and part used, source URL, license name/version and URL, basis for commercial and derivative permission, conditions/attribution, date checked, related outputs.
- **Provenance** on every pose, segment and motion: its source, the register entry for any external material, the applicable license; a composed motion lists its source segments/motions. A cleared license still has to be followed. Exact schema: foundation data-model change.

---

## 9. Layout (target)

```
AGENTS.md
.codex/              config.toml, agents/ (architect, dev, reviewer)
openspec/            specs/ (source-of-truth capabilities), changes/ (in flight)
schema/              JSON Schema: pose, segment, motion, rig map
poses/ segments/ motions/    YAML sources
rig/                 bone map (MPFB/Rigify -> VRM humanoid), body groups
scenes/              fixed camera/floor/light
tools/  tests/
dist/                baked outputs, committed only at release
build/               gitignored runs (section 5)
docs/used-materials.md
LICENSE-DATA  LICENSE-CODE
```

## 10. Backlog (first changes)

1. `foundation-data-model`: body groups, bone map, rotation convention, schemas, rest policy, provenance.
2. `scene-and-render`: fixed scene, character import, deterministic headless render, review-pack generator.
3. `timing-and-sampling`: beats to frames, static vs animation sets from one animation, tests.
4. `motion-march-in-place`: migrate the existing march; mirror and parallel arm layer.
5. `motion-squat-contacts`: IK targets, contacts, foot-sliding check.
6. `bake-and-export`: bake to FK, glTF/VRMA/BVH, contacts sidecar, round-trip check.
