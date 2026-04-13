#!/usr/bin/env python3
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

try:
    import jsonschema
except Exception:
    jsonschema = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EthicBit.RegistryManager")

class RegistryManager:
    def __init__(self, policy_dir: str = "ceerv/policy"):
        self.policy_dir = Path(policy_dir)
        self.registries: Dict[str, dict] = {}
        self.rule_index: Dict[Tuple[str, str], dict] = {}
        self.schema = None
        self._load_schema()

    def _load_schema(self):
        schema_path = self.policy_dir / "reason_registry.schema.json"
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                self.schema = json.load(f)
        else:
            logger.warning("reason_registry.schema.json not found; schema validation disabled")

    def load_all(self) -> Dict[str, dict]:
        self.registries.clear()
        self.rule_index.clear()

        for file in sorted(self.policy_dir.glob("reason_registry*.json")):
            if file.name == "reason_registry.schema.json":
                continue
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if self.schema and jsonschema is not None:
                jsonschema.validate(instance=data, schema=self.schema)

            sector = data.get("sector", "CORE")
            self.registries[sector] = data

            for rule in data.get("rules", []):
                self.rule_index[(sector, rule["rule_id"])] = {**rule, "sector": sector}

        return self.registries

    def _get_rule(self, rule_id: str, sector: str = "CORE") -> Optional[dict]:
        if (sector, rule_id) in self.rule_index:
            return self.rule_index[(sector, rule_id)]
        if ("CORE", rule_id) in self.rule_index:
            return self.rule_index[("CORE", rule_id)]
        return None

    def evaluate_rule(self, rule_id: str, sector: str = "CORE", evidence_ok: bool = True) -> Dict[str, Any]:
        rule = self._get_rule(rule_id, sector)
        if not rule:
            return {
                "valid": False,
                "action": "REJECT",
                "error": f"Rule {rule_id} not found in sector {sector} or CORE",
                "severity": None,
                "rule": None
            }

        severity = rule["severity"]
        result = {
            "valid": evidence_ok,
            "action": "PASS",
            "rule": rule,
            "severity": severity,
            "sector": rule["sector"],
            "evidence_ok": evidence_ok
        }

        if not evidence_ok:
            if severity == "CRITICAL":
                result["valid"] = False
                result["action"] = "FAIL_CLOSED"
            elif severity == "HIGH":
                result["valid"] = False
                result["action"] = "WARN_DEGRADE"
            else:
                result["valid"] = False
                result["action"] = "WARN"

        return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rule-id", required=True)
    parser.add_argument("--sector", default="CORE")
    parser.add_argument("--evidence-ok", required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    evidence_ok = str(args.evidence_ok).lower() in ("true", "1", "yes", "y")

    rm = RegistryManager()
    rm.load_all()
    result = rm.evaluate_rule(args.rule_id, args.sector, evidence_ok=evidence_ok)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    action = result.get("action")
    if action == "PASS":
        raise SystemExit(0)
    if action == "FAIL_CLOSED":
        raise SystemExit(1)
    if action == "REJECT":
        raise SystemExit(2)
    if action == "WARN_DEGRADE":
        raise SystemExit(3)
    raise SystemExit(4 if args.strict else 0)

if __name__ == "__main__":
    main()
