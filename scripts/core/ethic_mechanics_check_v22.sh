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
from scripts.core.real_local_evidence import resolve_required_evidence


async def main():
    manager = RegistryManager(str(root_dir / "config/registry-manager-config.json"))
    rule = manager._get_rule(rule_id, sector)

    evidence = {}
    missing = []
    resolver_trace = {}
    if evidence_ok and rule:
        required = manager._normalize_required_evidence(rule)
        evidence, missing, resolver_trace = resolve_required_evidence(required, root_dir)

    if evidence_ok:
        state = {
            "evidence": {},
            "audit": {
                "canonical": True
            },
            "real_local_evidence": evidence,
        }
        extra_evidence = evidence
    else:
        state = {
            "evidence": {
                "force_fail": True,
                "force_fail_providers": ["self-attested", "chainlink", "jumio"]
            },
            "audit": {
                "canonical": True
            },
            "real_local_evidence": {},
        }
        extra_evidence = {}

    result = await manager.evaluate_async(
        rule_id=rule_id,
        state=state,
        extra_evidence=extra_evidence,
        sector=sector,
    )

    broker_report = result.brokerReport or {}
    final_gate = broker_report.get("final_gate", "N/A")
    fail_closed_reason = broker_report.get("fail_closed_reason", "N/A")

    print(f"brokerReport.final_gate={final_gate}")
    print(f"fail_closed_reason={fail_closed_reason}")
    print(f"resolver.mode=REAL_LOCAL")
    print(f"resolver.missing={json.dumps(missing, ensure_ascii=False)}")
    if resolver_trace:
        print(f"resolver.trace={json.dumps(resolver_trace, ensure_ascii=False)}")
    print(json.dumps(asdict(result), ensure_ascii=False))

    if result.status in {"PASS", "WARN", "WARN_DEGRADE"}:
        return 0
    return 1


raise SystemExit(asyncio.run(main()))
PY
