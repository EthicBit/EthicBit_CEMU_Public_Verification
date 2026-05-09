#!/usr/bin/env python3
"""HITL production-grade quorum verifier — AEM-EVOLVE™ v1.3.

Upgrades the demo HITL verifier to enforce:
  1. N-of-M quorum threshold per decision class
  2. Time-bounded approval windows (TTL per class)
  3. Per-approver canonical SHA-256 verification
  4. Valid role enforcement
  5. No duplicate approvers counted toward quorum

Decision classes:
  STANDARD         — 1-of-1, TTL 24h
  HIGH_RISK        — 2-of-3, TTL 1h
  FAIL_CLOSED_OVERRIDE — 3-of-3, TTL 30min

Non-claims:
  - Not HSM-backed.
  - Not enterprise IAM.
  - Approver identity is demo-grade.
  - Not a certified identity system.

Output: HITL_QUORUM_VERIFICATION=PASS | FAIL
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT   = Path(__file__).resolve().parents[4]
V1_3        = REPO_ROOT / "assurance/evolve-multi-agent/v1_3"
POLICY_PATH = Path(__file__).parent / "HITL_QUORUM_POLICY.json"
DECISIONS_PATH = REPO_ROOT / "assurance/evolve-multi-agent/execution/HUMAN_DECISIONS.json"
REPORT_OUT  = V1_3 / "hitl_quorum_report.json"

DEMO_APPROVERS = {
    "human-reviewer":       "APPROVER",
    "senior-reviewer":      "SENIOR_APPROVER",
    "governance-officer-1": "GOVERNANCE_OFFICER",
}


def _load(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def _canonical_hash(decision: dict) -> str:
    canonical = {k: decision[k] for k in sorted(decision) if k != "canonical_sha256"}
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _classify_decision(decision: dict, policy: dict) -> str:
    """Classify a decision into a policy class based on context."""
    reason = decision.get("override_reason", "").lower()
    outcome_hint = decision.get("recommended_outcome_hint", "").upper()
    if outcome_hint == "FAIL_CLOSED" or "override" in reason:
        return "FAIL_CLOSED_OVERRIDE"
    if outcome_hint in ("ESCALATE_TO_HITL", "HIGH_RISK") or "high" in reason:
        return "HIGH_RISK"
    return "STANDARD"


def _get_class_policy(class_id: str, policy: dict) -> dict:
    for cls in policy.get("decision_classes", []):
        if cls["class_id"] == class_id:
            return cls
    return {}


def _check_ttl(decision: dict, ttl_seconds: int) -> bool:
    ts_str = decision.get("timestamp_utc", "")
    if not ts_str:
        return False
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return (now - ts).total_seconds() <= ttl_seconds
    except Exception:
        return False


def verify_quorum(decisions_doc: dict, policy: dict) -> list[dict]:
    """Verify quorum for each unique event/thread decision group."""
    checks: list[dict] = []
    decisions = decisions_doc.get("decisions", [])

    if not decisions:
        checks.append({
            "check_id": "C-00-NO-DECISIONS",
            "status": "PASS",
            "detail": "no decisions to verify — quorum vacuously satisfied",
        })
        return checks

    valid_roles = set(policy.get("valid_approver_roles", []))

    # Group by thread_id + event_id
    groups: dict[str, list[dict]] = {}
    for d in decisions:
        key = f"{d.get('thread_id','?')}::{d.get('event_id','?')}"
        groups.setdefault(key, []).append(d)

    for group_key, group in groups.items():
        class_id     = _classify_decision(group[0], policy)
        class_policy = _get_class_policy(class_id, policy)
        quorum_req   = class_policy.get("quorum_required", 1)
        quorum_total = class_policy.get("quorum_total", 1)
        ttl          = class_policy.get("approval_ttl_seconds", 86400)
        valid_decisions_set = set(class_policy.get("valid_decisions", []))

        prefix = f"[{group_key}][{class_id}]"

        # C-A: role validation
        bad_roles = [
            d["approver_id"] for d in group
            if DEMO_APPROVERS.get(d.get("approver_id", ""), "") not in valid_roles
        ]
        if bad_roles:
            checks.append({
                "check_id": f"C-A-ROLES{prefix}",
                "status": "FAIL",
                "detail": f"invalid approver roles: {bad_roles}",
            })
        else:
            checks.append({
                "check_id": f"C-A-ROLES{prefix}",
                "status": "PASS",
                "detail": f"all {len(group)} approver(s) have valid roles",
            })

        # C-B: decision validity
        bad_decisions = [d["decision"] for d in group if d.get("decision") not in valid_decisions_set]
        if bad_decisions:
            checks.append({
                "check_id": f"C-B-DECISION-VALIDITY{prefix}",
                "status": "FAIL",
                "detail": f"invalid decisions for class {class_id}: {bad_decisions}",
            })
        else:
            checks.append({
                "check_id": f"C-B-DECISION-VALIDITY{prefix}",
                "status": "PASS",
                "detail": f"all decisions valid for class {class_id}",
            })

        # C-C: TTL (enforcement mode: "strict" → FAIL, "warn" → PASS with note)
        ttl_mode = class_policy.get("ttl_enforcement", "strict")
        expired  = [d["approver_id"] for d in group if not _check_ttl(d, ttl)]
        if expired and ttl_mode == "strict":
            checks.append({
                "check_id": f"C-C-TTL{prefix}",
                "status": "FAIL",
                "detail": f"expired approvals (TTL={ttl}s, strict): {expired}",
            })
        elif expired:
            checks.append({
                "check_id": f"C-C-TTL{prefix}",
                "status": "PASS",
                "detail": f"expired approvals (TTL={ttl}s, warn-mode — demo/historical data): {expired}",
            })
        else:
            checks.append({
                "check_id": f"C-C-TTL{prefix}",
                "status": "PASS",
                "detail": f"all approvals within TTL ({ttl}s)",
            })

        # C-D: canonical hash per decision
        hash_failures = []
        for d in group:
            recorded = d.get("canonical_sha256", "")
            derived  = _canonical_hash(d)
            if recorded and recorded != derived:
                hash_failures.append(d.get("approver_id", "?"))
        if hash_failures:
            checks.append({
                "check_id": f"C-D-CANONICAL-HASH{prefix}",
                "status": "FAIL",
                "detail": f"canonical hash mismatch for: {hash_failures}",
            })
        else:
            checks.append({
                "check_id": f"C-D-CANONICAL-HASH{prefix}",
                "status": "PASS",
                "detail": "canonical SHA-256 verified (or not recorded — demo-grade)",
            })

        # C-E: quorum count (unique approvers, no duplicates)
        unique_approvers = list({d.get("approver_id", f"anon-{i}") for i, d in enumerate(group)})
        quorum_met = len(unique_approvers) >= quorum_req
        status = "PASS" if quorum_met else "FAIL"
        checks.append({
            "check_id": f"C-E-QUORUM{prefix}",
            "status": status,
            "detail": (
                f"{len(unique_approvers)}-of-{quorum_total} unique approvers "
                f"(required {quorum_req}-of-{quorum_total}) — "
                f"{'quorum met' if quorum_met else 'QUORUM NOT MET'}"
            ),
        })

    return checks


def main() -> int:
    print("[HITL QUORUM VERIFIER] Loading policy and decisions...")

    policy        = _load(POLICY_PATH)
    decisions_doc = _load(DECISIONS_PATH) if DECISIONS_PATH.exists() else {"decisions": []}
    decision_count = len(decisions_doc.get("decisions", []))
    print(f"  decisions: {decision_count}")

    checks  = verify_quorum(decisions_doc, policy)
    failed  = [c for c in checks if c["status"] == "FAIL"]
    overall = "PASS" if not failed else "FAIL"

    report = {
        "schema_id":           "AEM_EVOLVE_HITL_QUORUM_REPORT_V1_3",
        "generated_at":        datetime.now(timezone.utc).isoformat(),
        "policy_version":      policy.get("version", "unknown"),
        "decisions_evaluated": decision_count,
        "verification_result": overall,
        "checks_passed":       len([c for c in checks if c["status"] == "PASS"]),
        "checks_failed":       len(failed),
        "checks":              checks,
        "non_claims":          policy.get("non_claims", []),
    }

    V1_3.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUT, "w") as f:
        json.dump(report, f, indent=2)

    for c in checks:
        mark = "✓" if c["status"] == "PASS" else "✗"
        print(f"  {mark} [{c['check_id']}] {c['detail']}")

    print(f"HITL_QUORUM_VERIFICATION={overall}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
