#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

RULE_ID="${1:-}"
SECTOR="${2:-CORE}"
EVIDENCE_OK="${3:-true}"

if [[ -z "$RULE_ID" ]]; then
  echo "ERROR: missing RULE_ID" >&2
  exit 2
fi

cd "$ROOT_DIR"

python3 - "$ROOT_DIR" "$RULE_ID" "$SECTOR" "$EVIDENCE_OK" <<'PY'
import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path

root_dir = Path(sys.argv[1]).resolve()
rule_id = sys.argv[2]
sector = sys.argv[3]
evidence_ok = sys.argv[4].lower() == "true"

sys.path.insert(0, str(root_dir))

from scripts.core.RegistryManager import RegistryManager


def build_evidence_value(key: str):
    mapping = {
        "audit_log": {"entries": 3, "sealed": True},
        "decision_chain": {"steps": ["capture", "review", "decision"]},
        "timestamped_snapshot": "2026-04-17T00:00:00Z",
        "judicial_reasoning_log": {"case_ref": "JUS-001", "traceable": True},
        "evidence_chain": {"hashes": ["0xabc", "0xdef"]},
        "transaction_ledger": {"entries": 12, "balanced": True},
        "source_funds_proof": {"verified": True},
        "audit_trail": {"complete": True},
        "security_event_log": {"events": 5, "immutable": True},
        "immutable_storage": {"backend": "worm", "enabled": True},
        "cryptographic_hash": "0x" + "a" * 64,
        "source_snapshot": {"commit": "abc123", "clean": True},
        "build_config": {"reproducible": True},
        "dependency_lock": {"present": True},
        "evidence_chain_log": {"records": 4},
        "source_reference_record": {"references": ["SRC-001"]},
        "control_decision_log": {"decisions": 2},
        "input_snapshot": {"captured": True},
        "regulatory_trace_record": {"trace_id": "REG-TRACE-001"},
        "humanApproval": {
            "approved": True,
            "approver": "ops-controller",
            "timestamp": "2026-04-17T00:00:00Z",
            "signature": "attest::human-approval-test",
        },
        "kycVerification": True,
        "identity": {"verified": True},
        "price": 2456.78,
        "financialTxHash": "0xfin" + "b" * 40,
        "cryptographicSignature": "0x" + "c" * 64,
    }
    return mapping.get(key, f"mock_{key}_value")


async def main():
    manager = RegistryManager(str(root_dir / "config/registry-manager-config.json"))
    rule = manager._get_rule(rule_id, sector)

    evidence = {}
    if evidence_ok and rule:
        required = manager._normalize_required_evidence(rule)
        for key in required:
            evidence[key] = build_evidence_value(key)

    if evidence_ok:
        state = {
            "evidence": evidence,
            "audit": {
                "canonical": False
            }
        }
    else:
        state = {
            "evidence": {
                "force_fail": True,
                "force_fail_providers": ["self-attested", "chainlink", "jumio"]
            },
            "audit": {
                "canonical": False
            }
        }

    result = await manager.evaluate_async(
        rule_id=rule_id,
        state=state,
        extra_evidence=None,
        sector=sector,
    )

    broker_report = result.brokerReport or {}
    final_gate = broker_report.get("final_gate", "N/A")
    fail_closed_reason = broker_report.get("fail_closed_reason", "N/A")

    print(f"brokerReport.final_gate={final_gate}")
    print(f"fail_closed_reason={fail_closed_reason}")
    print(json.dumps(asdict(result), ensure_ascii=False))

    if result.status in {"PASS", "WARN", "WARN_DEGRADE"}:
        return 0
    return 1


raise SystemExit(asyncio.run(main()))
PY
