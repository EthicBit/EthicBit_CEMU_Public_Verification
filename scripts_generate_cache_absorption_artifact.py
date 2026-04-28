from agentic.runtime.canonical_cache import CanonicalTieredCache

cache = CanonicalTieredCache()

agent_state = {
    "mode": "REALTIME_100MS",
    "canonical_state": "ACTIVE_CANONICAL",
    "pre_execution_guard": "OK"
}

state_hash = cache.state_hash(agent_state)
cache.invalidate_if_state_changed(state_hash)

key = cache.make_key(
    tier="TIER0_LOCAL_FAST",
    rule_id="REALTIME_SUPERVISOR_LOCAL",
    state_hash=state_hash,
    source_version="local",
    rule_version="v1"
)

result = cache.get(key)
if result is None:
    result = cache.set(
        tier="TIER0_LOCAL_FAST",
        key=key,
        state_hash=state_hash,
        source="real_local",
        value={
            "rule_id": "REALTIME_SUPERVISOR_LOCAL",
            "status": "PASS",
            "confidence": 0.95,
            "sources_used": ["real_local"]
        }
    )

cache.record_fast_loop_sources(result["sources_used"])
cache.verify_entry_fingerprint(result)
status = cache.write_status()

print("CACHE_ABSORPTION_STATUS=", status["status"])
print("ADDENDUM_17A_CACHE_ABSORPTION=", status["addendum_17a_cache_absorption"])
print("RIT_DETECTED=", status["rit_detected"])
