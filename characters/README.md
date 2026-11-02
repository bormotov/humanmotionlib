# Character source layout

- `registry.yaml` declares the stable ordered IDs `skeleton`, `male`, `female`.
- `definitions/` selects a compatible profile and renderer. The standalone skeleton has no surface dependency.
- `templates/` defines shared procedural topology, shape construction and carrier binding. Revision 4 assembles torso and distal arm loft sources into one welded shoulder component, locally refines and gently relaxes the shoulder bridge, then authors a shallow arms-down upper-shoulder contour through the same canonical neutral dual-quaternion binding. The surface remains a static rest mesh with the existing frame-by-frame skinning rule; no runtime corrective shape is evaluated. The remaining body regions retain the two-influence limit.
- `appearances/` contains data-only surface dimensions and materials.

All local documents are CC-BY-4.0 authored sources and validate against the corresponding versioned schemas in `schema/`. See [the character data guide](../docs/character-models.md) for the authored approximation and validation contract.
