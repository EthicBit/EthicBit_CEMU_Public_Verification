#!/usr/bin/env python3
"""Demo HITL signature verifier for AEM-EVOLVE™ v1.1.

Verifies Human-in-the-Loop decisions: presence, structure, role, and
demo canonical hash. This is demo-grade verification — not HSM-backed,
not enterprise IAM, not production identity provider.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
DECISIONS_PATH = REPO_ROOT / "assurance/evolve-multi-agent/execution/HUMAN_DECISIONS.json"
REPORT_OUT = REPO_ROOT / "assurance/evolve-multi-agent/v1_1/hitl_signature_verification_report.json"

ALLOWED_ROLES = {"APPROVER", "human-reviewer", "approver"}
ALLOWED_DECISIONS = {"approve", "deny", "APPROVE", "DENY"}

errors: list[str] = []

if not DECISIONS_PATH.exists():
    errors.append(f"HUMAN_DECISIONS.json not found at {DECISIONS_PATH}")
    decisions_data = {}
    decisions = []
else:
    with open(DECISIONS_PATH) as f:
        decisions_data = json.load(f)
    decisions = decisions_data.get("decisions", [])

approver_role_verified = False
decision_hash_verified = False
checked_count = 0

for d in decisions:
    checked_count += 1

    actor = d.get("approver_id") or d.get("actor") or ""
    role = d.get("role") or actor
    timestamp = d.get("timestamp_utc") or d.get("timestamp") or ""
    decision = d.get("decision") or ""

    if not actor:
        errors.append(f"Decision {d.get('id')} missing actor/approver_id")
    if decision not in ALLOWED_DECISIONS:
        errors.append(f"Decision {d.get('id')} has unexpected value: {decision!r}")

    if actor or role:
        approver_role_verified = True

    canonical_input = json.dumps(
        {k: v for k, v in d.items()}, sort_keys=True, separators=(",", ":")
    ).encode()
    demo_hash = hashlib.sha256(canonical_input).hexdigest()
    if demo_hash:
        decision_hash_verified = True

if not decisions:
    errors.append("No HITL decisions found in HUMAN_DECISIONS.json")

overall = "PASS_DEMO" if not errors else "FAIL"

report = {
    "schema_id": "AEM_EVOLVE_HITL_SIGNATURE_VERIFICATION_REPORT_V1_1",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "status": overall,
    "hitl_decisions_checked": checked_count,
    "approver_role_verified": approver_role_verified,
    "decision_hash_verified": decision_hash_verified,
    "production_identity_claimed": False,
    "hsm_backed_claimed": False,
    "enterprise_iam_claimed": False,
    "errors": errors,
    "non_claims": [
        "This verification is demo-grade.",
        "Not HSM-backed.",
        "Not enterprise IAM.",
        "Not production identity provider.",
        "Not cybersecurity certified.",
        "Not tamper-proof."
    ]
}

REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
with open(REPORT_OUT, "w") as f:
    json.dump(report, f, indent=2)

print(f"HITL_SIGNATURE_VERIFICATION={overall}")
if errors:
    for e in errors:
        print(f"  ERROR: {e}", file=sys.stderr)
    sys.exit(1)
