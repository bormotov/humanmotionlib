# Skeleton source contracts

All schemas use JSON Schema Draft 2020-12. Object shapes are closed, including
nested records. `common.schema.json` holds shared vectors, quaternions,
landmarks, attachments, and provenance. References resolve only against the
repository schema registry; validation does not fetch schemas from the web.

| Schema | Canonical source |
|---|---|
| `profile.schema.json` | `rig/profiles/adult-reference-v1.yaml` |
| `mobility.schema.json` | `rig/mobility/adult-reference-v1.yaml` |
| `body-groups.schema.json` | `rig/body-groups.yaml` |
| `humanoid-map.schema.json` | `rig/humanoid-map.yaml` |
| `diagnostic.schema.json` | `rig/diagnostics/*.yaml` |
| `review-scene.schema.json` | `scenes/skeleton-review.yaml` |

Distances are meters, clinical actions are degrees, source timing is beats,
and reference proportions/tolerances are explicitly normalized to stature.
Records have version 1 and required English descriptions and provenance.
Diagnostic records also identify the scoped `skeleton-diagnostic/v1` format.
Mobility `units: degrees` applies to anatomical actions; the separate
`placements` records explicitly store `neutral_m` and `bounds_m` for pelvis
placement, preventing a meter-valued channel from being treated as joint ROM.
Couplings use a closed list of types and numeric parameter shapes; executable
expressions are rejected. Geometry uses explicit numeric primitive records.

`tools.source_validation.validate_document(document, schema_name)` checks the
finite-number guard before JSON Schema validation. This is essential because
in-memory Python/YAML NaN is not a valid canonical number even when ordinary
numeric comparisons cannot reject it. Errors include the source identifier
and field path. Schema verification tests include synthetic positive records
and mutations for unknown fields, unsupported versions/units, missing
metadata/provenance, non-finite coordinates, and non-positive stature.

Schema validity alone does not establish anatomical coverage, unique IDs,
resolved references, joint-frame correctness, writer ownership, cleared
sources, or acceptance metrics. Those cross-record and dossier checks are
required by `tools/validate.py` and the numerical verifier; their absence is
not a pass. See `tools/README.md` for the command contract and current status.
