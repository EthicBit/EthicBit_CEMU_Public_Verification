#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.core.RegistryManager import RegistryManager

CONFIG = ROOT / "config/registry-manager-config.json"
OUT = ROOT / "results/constitutional_amendment_snapshot.json"

RULE_IDS = [
    "RULE-ETHIC-TEC-DET-001-v1.0",
    "RULE-ETHIC-TEC-DET-002-v1.0",
    "RULE-ETHIC-TEC-DET-003-v1.0",
    "RULE-ETHIC-TEC-DET-004-v1.0",
]

rm = RegistryManager(str(CONFIG))

rules = []
for rid in RULE_IDS:
    rule = rm._get_rule(rid, "TECHNICAL")
    if not rule:
        continue
    rules.append({
        "rule_id": rule.get("rule_id"),
        "description": rule.get("description"),
        "severity": rule.get("severity"),
        "evidence_sources": rule.get("evidence_sources", []),
        "entity_visibility": rule.get("entity_visibility"),
        "entity_detectability": rule.get("entity_detectability"),
        "detection_mode": rule.get("detection_mode"),
        "constitutional_scope": rule.get("constitutional_scope"),
        "cross_sector_activation": rule.get("cross_sector_activation", False),
        "externalEvidenceRequired": rule.get("externalEvidenceRequired", False),
        "outcomeOnViolation": rule.get("outcomeOnViolation"),
    })

payload = {
    "artifactType": "constitutional_amendment_snapshot",
    "amendment_id": "AMENDMENT-TECHNICAL-SCOPE-DETECTABLE-ENTITIES-v1.0",
    "constitutional_scope": "TECHNICAL_EXPANDED",
    "rule_count": len(rules),
    "rules": rules,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(str(OUT))
