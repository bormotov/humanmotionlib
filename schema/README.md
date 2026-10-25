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
| `consumer-motion.schema.json` | External API input envelope (`hml-consumer-motion/v1`): one complete diagnostic or one packaged-fixture variant plus clearance declarations |
| `consumer-motion-snapshot.schema.json` | Integrity-sealed consumer source and resolved-base lineage persisted in prepared input |
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

## Consumer motion inputs

The public API accepts one consumer document at a time using the closed
`hml-consumer-motion/v1` envelope. Its `motion` is either a complete
`skeleton-diagnostic/v1` definition or a `skeleton-motion-variant/v1` of one
packaged diagnostic. A variant names a packaged `base_fixture` and may scale
existing track key values or replace whole tracks; it cannot alter duration,
constructor, contacts, controls, root, or rest policy. This is a bounded input
contract over the existing diagnostic action language, not a general
pose/segment/motion compositor.

Time values are integer beats, anatomical action tracks use degrees, meter
vectors use the existing source contract, and the existing profile defines
stature scaling. Consumer definitions support durations through 256 beats and
at most 100000 distinct delivered pose samples per request. A source duration
above 256 beats is a `source-validation` error; a requested BPM set that would
exceed the delivered-sample budget is an `invalid-request`, checked before
sample allocation. These are resource limits, not exercise limits. HML checks structure and resolved
kinematic/contact constraints before writing prepared data. That check does
not claim evaluated-mesh, clinical, or human visual acceptance.

The envelope requires `materials`, an array that can be empty for an authored
source. Adapted consumer provenance must resolve to package entries or
structured supplied clearance records. The schema closes record fields and
permission/obligation flags; runtime semantic validation checks license
profiles, source closure, and inherited package attribution. It validates
caller declarations offline and does not independently verify legal
permission. Results preserve the supplied terms and obligations.

The pinned obligation profiles require these flags: CC-BY-4.0 requires
`retain_attribution`, `retain_license_text`, and `retain_change_notice`; MIT
requires `retain_license_text` and `retain_copyright_notice`; Apache-2.0
requires `retain_license_text`, `retain_copyright_notice`,
`retain_change_notice`, and `retain_notice_if_present`; CC0-1.0 requires no
obligation flags. A record may declare additional supported flags; each must
be true and remains in the returned provenance. CC-BY-4.0, MIT, and
Apache-2.0 records require a nonempty attribution string. These are the HML
input profiles, not a complete legal analysis of every license term.

Prepared files carry the original canonical envelope, its hash, the resolved
diagnostic and hash, package base hashes, and a summary of the preflight. The
snapshot schema deliberately distinguishes canonical consumer-content hashes
from raw package-resource hashes. Rendering verifies the sealed snapshot and
resolves it again without consulting the original external file.
