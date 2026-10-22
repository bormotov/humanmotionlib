# AGENTS.md

Project: an open library of humanoid **poses, motion segments and compound motions**
for building exercise (morning gymnastics) animations. Blender is a **backend**:
the source of truth is plain data in this repo; Blender turns it into frames and clips.

Language: talk to the human in Russian. Repo content (code, specs, docs, commit messages) is in English.

> If `openspec init` adds its own managed block to this file, leave that block untouched
> and keep project content outside it.

---

## 1. Goals

1. From a text description of an exercise ("on count 1 raise arms, on count 2 lower them")
   produce **one set of illustrations** that serves two uses:
   - **Static mode**: one image per count; images flip on the beat of the music.
   - **Low-fps animation mode**: base frame interval 200 ms; between two counts there are
     **at least two in-between frames**, so the direction of a movement is unambiguous
     (e.g. arm circle clockwise vs counter-clockwise).
2. Frames must be **geometrically stable**: fixed camera, fixed distance, fixed floor,
   no drift of the character between frames unless the motion requires it.
3. Build a **reusable library** (poses, segments, motions, rig description) that other people
   can use under a free license, not only this project.

### Non-goals
- No realistic mocap-quality motion, no real-time game runtime, no new skeleton standard,
  no web/mobile player (consumers bring their own).
- No frame-by-frame image-model generation for the final frames (it drifts).

---

## 2. Core concepts (use these words consistently)

| Term | Meaning |
|---|---|
| **Pose** | Named static body configuration. Stored as bone rotations (FK) and/or IK targets, for a set of body groups. |
| **Segment** | Named transition between poses: `from`, `to`, optional `via` poses, `beats` duration, easing, controlled body groups. Example: `step_right`. |
| **Motion** | Composition of segments: sequence, repeat, and parallel layers over different body groups. Example: `march_in_place`. |
| **Body group** | Unit of masking. Smallest groups: `pelvis`, `torso`, `head_neck`, `arm_L`, `arm_R`, `leg_L`, `leg_R`. Larger masks are unions (lower body = pelvis+legs, upper body = torso+head_neck+arms). Hands/fingers may be added later as `hand_L`, `hand_R`. |
| **Controls** | The body groups a segment writes. Everything else follows its **rest policy**. |
| **Rest policy** | For channels a segment does not control: `hold` (keep previous pose), `base` (follow the base pose), `free` (driven by another parallel layer). |
| **IK target / contact** | Intent data: where a foot/hand must be, and when it is pinned to floor/object. Coordinate space, normalization, and units are open and must be specified when a concrete contact feature is designed. |
| **Beat** | Unit of time in sources. Seconds are derived from tempo (BPM) at render/bake time. |
| **Bake** | Converting solved IK/constraints/procedural layers into plain FK keyframes for export. |

### Modeling rules
- A segment writes keys **only** on its controlled body groups (this is the mask).
- A squat is not "legs only": pelvis and torso are controlled too (balance); list them in `controls`.
- Circular movements **must** carry explicit `via` poses (interpolation takes the shortest path and would be ambiguous).
- Left/right variants are produced by `mirror`, not duplicated by hand.
- Parameterize instead of multiplying variants (e.g. `knee_height`, `arm_swing`) where it is natural.
- Procedural layer (noise, overlap/follow-through) is separate and **off** for static frames; static frames are clean poses.
- Feet stay planted unless the segment says otherwise. Root does not drift.

---

## 3. Data and formats

Layers, from source of truth to distribution:

1. **Source (canonical)**: YAML in `poses/`, `segments/`, `motions/`, validated by JSON Schema in `schema/`.
   - Bone vocabulary: VRM humanoid bone names (map from the MPFB/Rigify rig explicitly).
   - Rotations: local, relative to the rest (T-)pose; exact convention is fixed in the first foundation change and then never changes silently.
   - Time: beats. Easing: named (`linear`, `ease_in_out`, ...).
   - Every pose, segment, and motion has `description` (English, extensible to other languages) and `provenance` (see Licensing).
2. **Baked clips** (generated, in `dist/`): glTF/GLB and **VRMA** (`.vrma`, rig-independent humanoid animation), BVH, and a `.blend` with Pose Library assets.
   - IK/constraints are not exported by glTF: always bake to FK before export.
   - VRMA constraints: translation only on hips, no scale animation.
3. **Sidecar contacts** (`*.contacts.json`): normalized contact intervals and IK target trajectories, so consumers with different proportions can fix foot sliding. (Whether VRMA can carry non-humanoid helper nodes is unverified; keep the sidecar as the reliable path.)
4. **Reference renders**: contact sheets / GIFs per segment. Documentation, not a source of truth.

### Frame timing rule
- One count corresponds to one beat. The beat duration is `T_beat = 60 / BPM` seconds.
- Static frames: render one frame at every beat/count boundary, sampled from the same keyed animation.
- Animation frames: for each full beat, use `n = max(3, ceil(T_beat / 200 ms))` intervals. This gives at least two in-between frames between count boundaries and a frame interval no longer than 200 ms.
- Segment boundaries must land on frame boundaries. Allocation for fractional-beat segments is defined by the timing OpenSpec change that introduces them.
- Static and animation sets come from the **same** keyed animation; no separate hand-made versions.

### Scene and render rules
- Camera: fixed, orthographic (or long-focal), fixed distance; defined once in a scene file, never moved per exercise.
- Floor and light fixed; floor must not shift between frames.
- Same character, same resolution, same output naming for all frames.
- Render with Eevee or Workbench for iteration; contours via Freestyle are optional. Rendering must be deterministic (same sources + same Blender version = same frames).
- Pin the Blender version (and MPFB version) in the repo; record it in each render's metadata.

---

## 4. Repository layout (target)

```
AGENTS.md
.codex/
  config.toml                 # subagent limits
  agents/                     # architect, dev, reviewer
openspec/
  specs/                      # source-of-truth capability specs
  changes/                    # in-flight changes (proposal, specs deltas, design, tasks)
schema/                       # JSON Schema: pose, segment, motion, rig map
poses/  segments/  motions/   # YAML sources
rig/                          # bone map (MPFB/Rigify -> VRM humanoid), body groups
scenes/                       # fixed camera/floor/light definitions
tools/                        # python: validate, sample, render, bake, contacts
tests/
dist/                         # baked outputs (committed only at release)
build/                        # scratch renders and review packs (gitignored)
docs/
  used-materials.md          # verified external materials used as references or inputs
LICENSE-DATA  LICENSE-CODE
```
Python tooling is managed with `uv`. Blender is invoked headless:
`blender --background <scene> --python tools/<script>.py -- <args>`.
Keep commands in one place (`tools/README.md` or a task runner) as they are established; do not invent new entry points silently.

---

## 5. Process: OpenSpec

Every non-trivial work item is an **OpenSpec change**. Specs describe behavior and requirements; code follows.

```
openspec/changes/<change-id>/
  proposal.md    # why, what, impact
  specs/<capability>/spec.md   # delta: ADDED / MODIFIED / REMOVED requirements + scenarios
  design.md      # technical approach (when needed)
  tasks.md       # checklist for the dev
```
CLI (check `openspec --help` for the installed version; slash commands differ between versions):
`openspec list`, `openspec validate <id>`, `openspec archive <id> --yes`.

## Main agent role

The main agent acts strictly as an orchestrator. Its only responsibilities are:

1. Answering the human's questions in the chat.
2. Managing OpenSpec changes (creating, updating, validating, and archiving
   proposals, specs, and task lists).

The main agent MUST NOT design, write, modify, or review project code itself.
All of that work MUST be delegated to subagents.

### Roles (Codex custom subagents in `.codex/agents/`)
Codex spawns subagents for specific tasks

| Role | Does | Does not |
|---|---|---|
| **architect** | Technical design, architecture decisions | Write implementation code. |
| **dev** | Implements `tasks.md`: schemas, tools, Blender scripts, poses/segments/motions, bake/export. Uses headless Blender CLI; Blender MCP only for interactive exploration. | Change requirements or acceptance criteria. If a spec is wrong or ambiguous, stop and report back to the architect. |
| **reviewer** | Independently verifies the change against the specs: validators, tests, clean re-render from sources, metrics, license/provenance. Produces the review pack and a verdict. | Fix code (reports findings; dev fixes). |

### Flow
1. Human states the task (any level of detail, in Russian is fine).
2. **architect** drafts the change. **Human gate 1**: approve or adjust the spec before any implementation.
3. **dev** implements; marks tasks done; runs its own checks. Independent tasks in the approved change may be delegated concurrently when their file ownership does not conflict; the change-level gates remain ordered.
4. **reviewer** verifies from a clean state and writes `review.md` in the change folder plus a review pack in `build/review/<change-id>/`.
5. **Human gate 2 (visual)**: the human looks at the review pack (contact sheets, GIF, onion-skin overlays) and approves or rejects with notes. Nothing is archived without this for changes that affect poses, motions, scene or rendering.
6. Fixes loop back to dev (or to architect if the spec changes). Then `openspec archive`.

Rules of the process:
- One logical change per proposal. Small changes still get a (short) proposal.
- Tasks are small and verifiable. A task without a way to check it is a spec defect.
- The dev never marks a requirement as met because it "looks fine"; the reviewer checks against scenarios.
- Findings reference the spec requirement/scenario they violate.

---

## 6. Quality gates (automatable checks; the reviewer runs them)

- **Schema**: all YAML validates against JSON Schema; bone names resolve via the rig map.
- **Timing**: frame count and times match the frame timing rule for the given BPM.
- **Stability**: camera/floor/light identical across frames (e.g. background and floor pixels match between frames outside the character mask); root drift within tolerance unless declared.
- **Contacts**: foot sliding during declared floor contacts below tolerance; no floor penetration.
- **Direction**: for motions with `via`, the swept angle/direction matches the declared direction.
- **Loops**: looping motions close (last pose equals first within tolerance).
- **Mirror**: mirrored segment equals the original with L/R swapped.
- **Bake round trip**: baked clip applied to the rig reproduces the source frames within tolerance.
- **Determinism**: two clean renders from the same sources are identical (or within a stated tolerance).
- **Licensing**: every new pose, segment, and motion has provenance; no data derived from non-free sources.

Visual judgement (is it readable, does it look like the exercise) stays with the human.

---

## 7. Licensing and provenance

- Library data and authored assets (poses, segments, motions, baked clips, renders): CC-BY 4.0 (record in `LICENSE-DATA`).
- Code (tools, scripts): Apache-2.0 (record in `LICENSE-CODE`).
- Third-party character, rig, scene, and other imported assets retain their own licenses; clear and record those licenses before using them in project outputs.
- **Commercial-use clearance is required for every source material** used to perform a task or inform project content. This includes textbooks, papers, illustrations, descriptions, videos, datasets, web pages, and third-party assets, even when consulted only as a reference.
  - Before using a source, verify that its license and terms explicitly and unambiguously permit commercial use of the resulting work and are compatible with this library's distribution license. Public availability, educational purpose, or the absence of a visible restriction is not permission.
  - If the license is missing, ambiguous, non-commercial, prohibits derivatives, or has conditions that conflict with the intended distribution, do not use the material. Find a clearly permitted alternative or ask the human to resolve the source choice before proceeding.
  - Do not copy joint angles, illustrations, text, or other protected expression from a source unless the verified license permits the intended commercial derivative and distribution.
- **Used-materials register**: every external material that is actually used to inform a task or project output must be listed in `docs/used-materials.md`, including CC0/public-domain sources and sources whose license does not require attribution. Record the material and specific part used, source URL, license name/version and license URL, the basis for commercial/derivative permission, applicable conditions or attribution, date checked, and related project outputs. Do not list materials that were merely discovered but not used.
- Provenance on each pose, segment, and motion identifies its source and points to the used-materials register entry when an external material informed it. A cleared license does not remove the requirement to follow its conditions.
- CMU Mocap, Mixamo, and non-commercial research datasets are not approved sources unless the specific material's current license is checked and explicitly permits the intended commercial derivative and distribution.
- Check MPFB character asset licenses before using them in project outputs.
- Every pose, segment, and motion has provenance. For a composed motion, record the source motion/segment identifiers and any external references used; record the applicable license. The exact schema is defined in the foundation data-model change.

---

## 8. Tooling notes for agents

- Prefer **headless Blender CLI** for anything reproducible (rendering, baking, tests). Use **Blender MCP** only to inspect or prototype interactively; results from MCP sessions must be turned into scripts in `tools/` before they count.
- Do not rely on Blender GUI state. Scenes and rigs come from files in the repo.
- Rigify gives FK/IK controls; arms are normally posed in FK, legs in IK (feet planted). Property names depend on the Rigify version: inspect the actual rig rather than assuming.
- Keep binary artifacts out of git except releases in `dist/`; scratch goes to `build/`.
- Never use browser/global state, absolute paths, or machine-specific settings in tools.

---

## 9. Suggested first changes (backlog for the architect)

1. `foundation-data-model`: body groups, bone map (MPFB/Rigify -> VRM humanoid), rotation convention, schemas for pose/segment/motion, rest policy, provenance.
2. `scene-and-render`: fixed camera/floor/light scene, character import, deterministic headless render, review pack generator (contact sheet, GIF, onion-skin).
3. `timing-and-sampling`: beats -> frames rule, static vs animation sets from one animation, tests.
4. `motion-march-in-place`: first full motion on the new data model (migrate the existing march), with mirror and parallel arm layer.
5. `motion-squat-contacts`: IK targets + contacts, normalized storage, foot-sliding check.
6. `bake-and-export`: bake to FK, export glTF/VRMA/BVH, contacts sidecar, round-trip check.

---

## 10. Do / don't

Do:
- Keep sources small, named, reviewable; prefer data over code.
- Ask the human when the exercise description is ambiguous (e.g. direction, amplitude, tempo) instead of guessing.
- Check commercial-use and derivative permissions before using any external source material; log each source actually used in `docs/used-materials.md`.
- Record decisions in `design.md` and keep specs up to date through delta specs.

Don't:
- Move the camera or floor to "fix" a frame; fix the data.
- Hand-edit generated files in `dist/` or `build/`.
- Add dependencies or new formats without an OpenSpec change.
- Change a convention (rotation order, bone names, units) without a MODIFIED requirement and migration.
