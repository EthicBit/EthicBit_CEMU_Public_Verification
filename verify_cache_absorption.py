from __future__ import annotations

import json
import sys
from pathlib import Path

path = Path("results/cache_absorption_status.json")

if not path.exists():
    print("CACHE_ABSORPTION=FAIL")
    print("reason=MISSING results/cache_absorption_status.json")
    sys.exit(2)

data = json.loads(path.read_text(encoding="utf-8"))

errors = []

checks = {
    "cache_enabled": True,
    "tiered_cache": True,
    "rit_detected": False,
    "status": "PASS",
    "addendum_17a_cache_absorption": "PASS"
}

for key, expected in checks.items():
    if data.get(key) != expected:
        errors.append(f"{key} expected {expected!r}, got {data.get(key)!r}")

ttl = data.get("ttl_policy", {})
for key in [
    "TIER0_LOCAL_FAST_ms",
    "TIER1_LIGHT_ORACLE_ms",
    "TIER2_HEAVY_ANCHOR_ms",
    "TIER4_CANONICAL_SNAPSHOT_ms"
]:
    if key not in ttl:
        errors.append(f"missing ttl_policy.{key}")

fast = data.get("fast_loop_policy", {})
if fast.get("heavy_external_calls_in_fast_loop") is not False:
    errors.append("heavy_external_calls_in_fast_loop must be false")

fp = data.get("fingerprint_policy", {})
if fp.get("enabled") is not True:
    errors.append("fingerprint_policy.enabled must be true")

inv = data.get("invalidation_policy", {})
for key in ["by_state_hash", "by_rule_version", "by_source_version", "by_ttl_expiry"]:
    if inv.get(key) is not True:
        errors.append(f"invalidation_policy.{key} must be true")

if errors:
    print("CACHE_ABSORPTION=FAIL")
    for e in errors:
        print(f"reason={e}")
    sys.exit(1)

print("CACHE_ABSORPTION=PASS")
print("cache_enabled=true")
print("tiered_cache=true")
print("ttl_policy=present")
print("invalidation=verifiable")
print("fingerprint=enabled")
print("heavy_external_calls_in_fast_loop=false")
print("rit_detected=false")
