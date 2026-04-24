import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from agentic.support.real_local_evidence import RULE_EVIDENCE_MAP, resolve_real_local_evidence

results = {}
failed = []

for rule_id in RULE_EVIDENCE_MAP:
    try:
        resolved = resolve_real_local_evidence(rule_id)
        results[rule_id] = {
            "status": "PASS",
            "evidence_count": len(resolved),
            "evidence_keys": sorted(resolved.keys()),
        }
    except Exception as e:
        results[rule_id] = {
            "status": "FAIL_CLOSED",
            "reason": str(e),
        }
        failed.append(rule_id)

out = {
    "schema_id": "ETHICBIT_REAL_LOCAL_CONSTITUTIONAL_GATE_V1",
    "status": "PASS" if not failed else "FAIL_CLOSED",
    "mode": "REAL_LOCAL_STRICT",
    "rules_checked": len(RULE_EVIDENCE_MAP),
    "failed_rules": failed,
    "results": results,
    "claim_level_ceiling": "L2" if not failed else "L1"
}

out_path = ROOT / "results" / "real_local_constitutional_gate.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"wrote {out_path}")
print(f"status={out['status']}")
print(f"claim_level_ceiling={out['claim_level_ceiling']}")
