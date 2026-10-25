# SPDX-License-Identifier: Apache-2.0
"""Host-only validation and replay of persisted consumer motion snapshots."""

from humanmotionlib.prepared import PackageResourceError, canonical_bytes


def verify_consumer_prepared(value):
    """Re-resolve and reconstruct a consumer preparation before backend launch."""
    from humanmotionlib.consumer_motion import verify_consumer_snapshot
    from humanmotionlib.prepare_skeleton import _prepare_sources
    from humanmotionlib.validate import load_sources

    snapshot = value["consumer_motion"]
    profile_id = value["sources"]["profile"]["id"]
    stature = value["sources"]["profile"]["stature_m"]
    try:
        source_plans = value["sampling"]
        if len(source_plans) != 1:
            raise ValueError("Consumer preparation must contain exactly one movement")
        consumer_id = next(iter(source_plans))
        bpms = tuple(plan["bpm"] for plan in source_plans[consumer_id])
        base_sources, _ = load_sources(profile_id)
        resolved = verify_consumer_snapshot(snapshot, base_sources, value["source_hashes"],
                                            profile_id, bpms, stature)
        if resolved["id"] != consumer_id:
            raise ValueError("Consumer identifier does not match prepared sample joins")
        consumer = {"resolved": resolved, "snapshot": snapshot}
        rebuilt = _prepare_sources(profile_id, base_sources,
                                   {"source_hashes": value["source_hashes"]},
                                   stature, (consumer_id,), bpms, consumer)
        if canonical_bytes(rebuilt) != canonical_bytes(value):
            raise ValueError("Consumer prepared payload does not match its validated source and solved samples")
    except (KeyError, TypeError, ValueError, OSError, PackageResourceError) as error:
        raise ValueError("Consumer prepared input integrity failure: " + str(error)) from error
