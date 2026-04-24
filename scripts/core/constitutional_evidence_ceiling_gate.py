#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "constitutional_evidence_ceiling.json"
RUNTIME = ROOT / "results" / "runtime_evidence_strength_report.json"
ME_GATE = ROOT / "results" / "mechanical_ethics_gate.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

runtime = load_json(RUNTIME) or {}
me_gate = load_json(ME_GATE) or {}

confidence = float(runtime.get("confidence", 0.0) or 0.0)
evidence_mode = str(runtime.get("evidence_mode", "UNKNOWN"))
health_score = str(runtime.get("health_score", "UNKNOWN"))
real_sources_used = runtime.get("real_sources_used", []) or []
mechanical_ethics_status = str(runtime.get("mechanical_ethics_status", "UNKNOWN"))
validated_sectors = int(runtime.get("validated_sectors", 0) or 0)

reasons = []

if mechanical_ethics_status != "PASS":
    reasons.append("MECHANICAL_ETHICS_NOT_PASS")

if validated_sectors < 7:
    reasons.append("VALIDATED_SECTORS_BELOW_7")

if len(real_sources_used) < 2:
    reasons.append("NO_SUFFICIENT_REAL_SOURCES_FOR_L4")

if confidence < 0.85:
    reasons.append("CONFIDENCE_BELOW_L4_THRESHOLD")

if health_score == "SIMULATED":
    reasons.append("HEALTH_SCORE_SIMULATED")

if evidence_mode in {"SELF_ATTESTED_FALLBACK", "SELF_ATTESTED_ONLY", "UNKNOWN"}:
    reasons.append("SELF_ATTESTED_ONLY_NOT_ALLOWED_FOR_L4_PLUS")

eligible_for_l4 = len(reasons) == 0
eligible_for_l5 = False

current_ceiling = runtime.get("claim_level_ceiling", "L1")
if eligible_for_l4:
    current_ceiling = "L4"

status = "PASS" if eligible_for_l4 else "FAIL_CLOSED"

report = {
    "schema_id": "ETHICBIT_CONSTITUTIONAL_EVIDENCE_CEILING_V1",
    "generated_at": now(),
    "status": status,
    "mechanical_ethics_status": mechanical_ethics_status,
    "current_ceiling": current_ceiling,
    "target_ceiling": "L4",
    "eligible_for_l4": eligible_for_l4,
    "eligible_for_l5": eligible_for_l5,
    "evidence_mode": evidence_mode,
    "confidence": confidence,
    "health_score": health_score,
    "validated_sectors": validated_sectors,
    "real_sources_used": real_sources_used,
    "reasons": reasons
}

OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"constitutional_evidence_ceiling={OUT}")
print(f"status={status}")
print(f"current_ceiling={current_ceiling}")
print(f"eligible_for_l4={eligible_for_l4}")
if reasons:
    print("reasons=" + ",".join(reasons))
