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
2. The change is drafted (main agent, with architect for design). **Gate 1**: the human approves the spec before implementation.
3. dev implements. Independent tasks may run concurrently when file ownership does not conflict; gates stay ordered.
4. reviewer writes `review.md` in the change folder and its review pack in its own build run.
5. **Gate 2 (visual)**: the human reviews the pack (contact sheets, GIF, onion-skin) and approves or rejects. Required before archiving any change touching poses, motions, scene or rendering.
6. Fixes go back to dev (to the spec if requirements change). Then `openspec archive`.

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
- Cleanup before hand-off, also after failed checks: inventory outputs and dependencies, then remove obsolete whole run roots (including residual logs/JSON) unless a concrete dependency, active or resumable work, unresolved diagnostic or explicit preservation requirement justifies keeping them. Check links before and after; never follow symlinks outside `build/`; never remove another agent's active run.
- Record removed paths and bytes, retained paths with reasons, dependency-check results and pending cleanup in an existing review or hand-off record. Failed or interrupted cleanup stays pending; do not report completion until it is resolved.

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

- Python via `uv`. Blender headless: `blender --background <scene> --python tools/<script>.py -- <args>`.
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
