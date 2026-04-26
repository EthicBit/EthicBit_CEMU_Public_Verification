from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class CacheEntry:
    tier: str
    key: str
    value: Dict[str, Any]
    created_at: float
    expires_at: float
    ttl_ms: int
    state_hash: str
    fingerprint: str
    source: str


class CanonicalTieredCache:
    DEFAULT_TTLS_MS = {
        "TIER0_LOCAL_FAST": 500,
        "TIER1_LIGHT_ORACLE": 2000,
        "TIER2_HEAVY_ANCHOR": 60000,
        "TIER4_CANONICAL_SNAPSHOT": 86400000
    }

    HEAVY_SOURCES = {"arweave", "sepolia", "kzg", "onchain", "blob"}

    def __init__(self, artifact_path: str = "results/cache_absorption_status.json"):
        self.store: Dict[str, CacheEntry] = {}
        self.artifact_path = Path(artifact_path)
        self.hits = 0
        self.misses = 0
        self.invalidations = 0
        self.heavy_external_calls_in_fast_loop = False
        self.rit_detected = False
        self.rit_reasons = []
        self.last_state_hash: Optional[str] = None
        self.started_at = time.time()

    def stable_hash(self, obj: Any) -> str:
        raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def state_hash(self, agent_state: Dict[str, Any]) -> str:
        return self.stable_hash(agent_state)[:32]

    def make_key(self, tier: str, rule_id: str, state_hash: str, source_version: str = "default", rule_version: str = "v1") -> str:
        return self.stable_hash({
            "tier": tier,
            "rule_id": rule_id,
            "state_hash": state_hash,
            "source_version": source_version,
            "rule_version": rule_version
        })

    def fingerprint(self, result: Dict[str, Any]) -> str:
        return self.stable_hash({
            "rule_id": result.get("rule_id"),
            "tier": result.get("tier"),
            "status": result.get("status"),
            "confidence": result.get("confidence"),
            "sources_used": result.get("sources_used", []),
            "state_hash": result.get("state_hash")
        })

    def invalidate_if_state_changed(self, state_hash: str) -> None:
        if self.last_state_hash is None:
            self.last_state_hash = state_hash
            return
        if state_hash != self.last_state_hash:
            self.store.clear()
            self.invalidations += 1
            self.last_state_hash = state_hash

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        now = time.time()
        entry = self.store.get(key)
        if entry is None:
            self.misses += 1
            return None
        if now > entry.expires_at:
            self.store.pop(key, None)
            self.invalidations += 1
            self.misses += 1
            return None
        self.hits += 1
        return dict(entry.value)

    def set(self, tier: str, key: str, value: Dict[str, Any], state_hash: str, source: str, ttl_ms: Optional[int] = None) -> Dict[str, Any]:
        ttl = int(ttl_ms if ttl_ms is not None else self.DEFAULT_TTLS_MS[tier])
        now = time.time()

        value = dict(value)
        value["tier"] = tier
        value["state_hash"] = state_hash
        value["cache_key"] = key
        value["ttl_ms"] = ttl
        value["cached_at"] = now

        fp = self.fingerprint(value)
        value["fingerprint"] = fp

        self.store[key] = CacheEntry(
            tier=tier,
            key=key,
            value=value,
            created_at=now,
            expires_at=now + ttl / 1000.0,
            ttl_ms=ttl,
            state_hash=state_hash,
            fingerprint=fp,
            source=source
        )
        return value

    def record_fast_loop_sources(self, sources_used: list[str]) -> None:
        normalized = {str(s).lower() for s in sources_used}
        if normalized.intersection(self.HEAVY_SOURCES):
            self.heavy_external_calls_in_fast_loop = True
            self.rit_detected = True
            reason = "HEAVY_EXTERNAL_SOURCE_USED_IN_FAST_LOOP"
            if reason not in self.rit_reasons:
                self.rit_reasons.append(reason)

    def verify_entry_fingerprint(self, value: Dict[str, Any]) -> bool:
        expected = value.get("fingerprint")
        if not expected:
            self.rit_detected = True
            self.rit_reasons.append("MISSING_FINGERPRINT")
            return False

        copy_value = dict(value)
        copy_value.pop("fingerprint", None)
        actual = self.fingerprint(copy_value)

        if actual != expected:
            self.rit_detected = True
            self.rit_reasons.append("FINGERPRINT_MISMATCH")
            return False

        return True

    def status(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        hit_rate = self.hits / total if total else 0.0

        return {
            "schema_id": "ETHICBIT_CANONICAL_CACHE_ABSORPTION_V1",
            "generated_at": time.time(),
            "cache_enabled": True,
            "tiered_cache": True,
            "ttl_policy": {
                "TIER0_LOCAL_FAST_ms": self.DEFAULT_TTLS_MS["TIER0_LOCAL_FAST"],
                "TIER1_LIGHT_ORACLE_ms": self.DEFAULT_TTLS_MS["TIER1_LIGHT_ORACLE"],
                "TIER2_HEAVY_ANCHOR_ms": self.DEFAULT_TTLS_MS["TIER2_HEAVY_ANCHOR"],
                "TIER4_CANONICAL_SNAPSHOT_ms": self.DEFAULT_TTLS_MS["TIER4_CANONICAL_SNAPSHOT"]
            },
            "invalidation_policy": {
                "by_state_hash": True,
                "by_rule_version": True,
                "by_source_version": True,
                "by_ttl_expiry": True
            },
            "fingerprint_policy": {
                "enabled": True,
                "algorithm": "sha256",
                "fields": [
                    "rule_id",
                    "tier",
                    "status",
                    "confidence",
                    "sources_used",
                    "state_hash"
                ]
            },
            "fast_loop_policy": {
                "fast_loop_tier": "TIER0_LOCAL_FAST",
                "heavy_external_sources_allowed_in_fast_loop": False,
                "heavy_external_calls_in_fast_loop": self.heavy_external_calls_in_fast_loop
            },
            "metrics": {
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "invalidations": self.invalidations,
                "entries": len(self.store),
                "uptime_seconds": time.time() - self.started_at
            },
            "rit_detected": self.rit_detected,
            "rit_reasons": self.rit_reasons,
            "status": "PASS" if not self.rit_detected else "FAIL",
            "addendum_17a_cache_absorption": "PASS" if not self.rit_detected else "FAIL"
        }

    def write_status(self) -> Dict[str, Any]:
        self.artifact_path.parent.mkdir(parents=True, exist_ok=True)
        status = self.status()
        self.artifact_path.write_text(json.dumps(status, indent=2, sort_keys=True), encoding="utf-8")
        return status
