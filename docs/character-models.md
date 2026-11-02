# Character data

The character registry is `characters/registry.yaml`. Its identifiers are ordered and stable:

| ID | Renderer | Sources | Default |
|---|---|---|---|
| `skeleton` | Existing anatomical skeleton | `characters/definitions/skeleton.yaml` and `adult-reference-v1` | Yes |
| `male` | Shared skinned surface | `characters/definitions/male.yaml`, `characters/templates/exercise-mannequin-v1.yaml`, `characters/appearances/male-v1.yaml` | No |
| `female` | Shared skinned surface | `characters/definitions/female.yaml`, `characters/templates/exercise-mannequin-v1.yaml`, `characters/appearances/female-v1.yaml` | No |

Each YAML source uses the versioned JSON Schema with the matching name under `schema/character-*.schema.json`. Character descriptors have explicit CC-BY-4.0 provenance. The surfaces, dimensions, topology, materials and weights are original authored rendering choices; there are no external character meshes, image textures, runtime downloads or copied motion data.

## Source fields and units

The canonical YAML files listed above are the complete, schema-validated examples. Fields are closed by their JSON Schemas; extra keys and unknown selectors are rejected.

| Source | Important fields | Units and meaning |
|---|---|---|
| `registry.yaml` | `schema_version`, ordered `characters[]`, each entry's `id` and `definition` | Stable character IDs and package-relative descriptor paths; order is the normalization order. |
| `definitions/<id>.yaml` | `renderer_kind`, `profile_id`, optional `template_id` and `appearance_id` | IDs only. A `skeletal` definition has no surface references; a `skinned-surface` definition names exactly one shared template and appearance preset. |
| `templates/exercise-mannequin-v1.yaml` | `template_revision`, `binding_revision`, `expected_rest_contract_sha256`, `rest_contract_structures`, `space`, `topology`, component `control_rings`, `weighting` | `*_h` values are fractions of stature `H`; each torso control ring owns a positive shared `radius_h` base pair; `t` is a dimensionless position on a declared centerline span; topology counts are integers; the digest binds the unscaled profile hierarchy and named attachments. |
| `appearances/<id>-v1.yaml` | `radius_scales`, `torso_radii_delta_h`, `head_radii_h`, `materials_rgb` | Radius scales and RGB channels are dimensionless; torso delta pairs are signed multiples of `H` added to the shared template base before interpolation; head radii are positive multiples of `H`; material channels are in `[0,1]`. Presets affect only surface coordinates/materials. |
| prepared profile | `stature_m` | Stature is supplied in meters and uniformly scales surface coordinates; it does not alter rig proportions or animation. |

For example, `definitions/skeleton.yaml` is the validated surface-free descriptor, while `definitions/male.yaml` and `definitions/female.yaml` show surface references. `appearances/male-v1.yaml` and `appearances/female-v1.yaml` contain the only current shape deltas: male torso deltas are ten zero pairs, while female torso deltas are signed values relative to the one shared base in the template. The female preset's upper-arm multiplier is `0.90`, thigh multiplier `1.06`, and shank multiplier `0.97`; no runtime body-type selector exists.

## Shared construction

The skeleton definition references only `adult-reference-v1`. It does not reference or load a surface template. Both surface definitions reference the same `exercise-mannequin-v1` template and profile, and differ only through their declarative appearance preset. The presets preserve the same component, vertex and face identities and carrier weights. They do not select mass coefficients, mobility observations, movement sources or skeletal proportions.

The template describes six smooth-shaded output pieces: one torso component with welded shoulders and both distal arms, head, mirrored left/right legs and mirrored left/right feet. Shoulder source loft patches are joined through shared boundary vertices and three intermediate loops; source cap and patch faces at that junction are removed. Other mannequin junctions remain separate overlaps. Torso and limb surfaces use 32-vertex loft rings, four subdivisions per control-ring interval and stable source-region/ring/sector vertex IDs. Head uses a 32 by 16 ellipsoid grid. Each torso ring stores the common base `radius_h` pair; both appearances provide exactly ten signed `torso_radii_delta_h` pairs. The male delta is all zeros. The effective radius is base plus delta per axis, and must remain finite and positive before interpolation or output allocation. There is no absolute torso-radius appearance fallback. This remains a stylized render surface, not an anatomical or tissue simulation.

Dimensions are normalized by request stature `H` and scale uniformly. Ring coordinates are generated in the canonical skeletal rest T-pose. Limb centers follow existing profile landmarks and are mirrored in code across `X=0`; no negative scale is used. `radius_scales` in an appearance preset change only surface radii. The female thigh scale stops at the shared knee ring; the shank scale starts below it.

Carrier weights use the cubic smoothstep `3t^2 - 2t^3`. The shared shoulder bridge blends the existing torso boundary weights to the humerus across three intermediate loops and may use up to three influences; all other regions retain the two-influence limit. Arm, hip, knee and ankle bands are declared in the template; torso source loft weights use the ordered pelvis/spine chain. The foot is hindfoot-only through `y=0.065H`, blends hindfoot to MTP from `0.065H` to `0.075H`, and is MTP-only at or beyond `0.075H`; this preserves the authored heel/ball attachment and rocker behavior. No auto-weighting or correction of posed vertices is permitted.

The template lists the seed `rest_contract_structures` used for its binding identity. The host closes that set over all structure parents, sorts structures and attachments by ID, and hashes canonical compact JSON containing each structure's parent, origin, basis, rest translation, rest orientation and attachments. Changes to a bind-significant rest transform, hierarchy or named contact attachment require an intentional compatibility renewal and checks for every dependent surface. Appearance-only edits preserve the binding identity. Future alternate skeletal proportions and body-type presets are unsupported in this release and must be introduced through an approved change.

## Rendering and verification

`prepare` stays character-independent. Rendering selects `skeleton` by default or accepts one or more registered IDs; a batch uses one preparation and one solved movement. Skeleton image paths and geometry evidence retain their current meaning. Surface meshes and measurements are recorded separately under each character ID. Character identity and canonical source closure are included in render identity and provenance.

Saved Blender scenes keep the existing `Anatomy`, `Controls`, `Humanoid` and `Review` collections. Selected surface objects live in their own `CharacterSurface.<id>` collection (`CharacterSurface.male` or `CharacterSurface.female`); selecting only the skeleton creates no surface collection or mesh. These collections can be inspected and hidden independently. The shoulder junction is welded and manifold; other mannequin junctions remain intentional overlaps. The surface does not claim collision-free anatomy or muscle/skin simulation.

An `images=False, render_only=False` build still constructs and validates evaluated geometry and writes `skeleton.blend`, `evaluated.json`, `geometry-reference.json` and `build-metadata.json`; it omits rendered PNGs and `render-manifest.json`. Such a build supports numeric/native inspection only. A `render_only=True` build skips evaluated geometry and surface/deformation evidence. It produces images only when `images=True`; `images=False` produces no images. A passing numeric report therefore does not establish render repeatability or visual acceptance; those require an image-producing pass and a separately assessed review pack.

The `surface-evaluated/v1` evidence identifies `reference_metric: canonical-double-world-dq/v1`. For each sample and component, `maximum_reference_residual_m` and `worst_reference_vertex_id` describe the canonical world-space dual-quaternion reference computed from the profile's double-precision rest frames and the raw prepared pose frames. The verifier recomputes that metric from every observed world-space vertex and checks the reported maximum and ID. The Blender-local Mathutils residual is a separate `native_local_debug_metric`; its maximum is not combined into the normative world-reference metric. Both native and canonical residuals remain bounded by the same authored `1e-5H` criterion.

The versioned template gives the analytic rest-envelope tolerances, normalized-weight tolerance, native deformation residual, triangle-area threshold, floor bound and visible-sole-to-contact-anchor bound. Numeric results establish source and deformation conformance only. A separate fixed-scene comparison pack and explicit human review judge silhouette, readable movement, continuous-looking junctions and planted feet.
