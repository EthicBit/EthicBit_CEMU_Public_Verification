#!/usr/bin/env python3
import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Stub temporal para EvidenceBroker
sys.path.insert(0, str(Path(__file__).parent))
try:
    # Preferred module name in this repository.
    from EvidenceBroker import EvidenceBroker  # type: ignore
except ImportError:
    try:
        # Backward-compatible fallback.
        from evidence_broker import EvidenceBroker  # type: ignore
    except ImportError:
        class EvidenceBroker:
            def __init__(self, config_path: str = ""):
                pass

            async def fetch_evidence(self, rule: Dict[str, Any], state: Dict[str, Any]):
                return {}, None

@dataclass
class EvaluationResult:
    ruleId: str
    sector: str
    status: str
    severity: str
    evidenceMissing: List[str]
    evidenceProvided: List[str]
    reason: str
    actionTaken: str
    timestamp: str

class RegistryManager:
    def __init__(self, config_path: str = "config/registry-manager-config.json"):
        self.config = self._load_config(config_path)
        self.registries: Dict[str, Dict] = {}
        self.rule_index: Dict[str, Dict] = {}
        self._loaded_sectors: Set[str] = set()
        self._base_path = Path(".")
        self.evidence_broker = EvidenceBroker(config_path)
        self.severity_mapping = self.config["evaluationSettings"]["defaultSeverityMapping"]
        print(f"✅ RegistryManager v2.1 (Lazy Loading) inicializado correctamente | 0 sectores cargados")

    def _load_config(self, path: str) -> Dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_registry(self, sector: str) -> None:
        if sector in self._loaded_sectors:
            return
        for reg_info in self.config["registries"]:
            if reg_info["sector"] == sector:
                file_path = self._base_path / reg_info["file"]
                with open(file_path, "r", encoding="utf-8") as f:
                    registry_data = json.load(f)
                self.registries[sector] = registry_data
                for rule in registry_data.get("rules", []):
                    rule["sector"] = sector
                    self.rule_index[rule["rule_id"]] = rule
                self._loaded_sectors.add(sector)
                print(f"📦 Sector cargado: {sector}")
                return
        raise ValueError(f"Sector desconocido: {sector}")

    def _ensure_sector_loaded(self, sector: Optional[str] = None) -> None:
        if sector and sector not in self._loaded_sectors:
            self._load_registry(sector)
        if self.config["evaluationSettings"].get("fallbackToCore", True) and "CORE" not in self._loaded_sectors:
            self._load_registry("CORE")

    def _get_rule(self, rule_id: str, sector: Optional[str] = None) -> Optional[Dict]:
        self._ensure_sector_loaded(sector)
        return self.rule_index.get(rule_id)

    @staticmethod
    def _extract_required_evidence(rule: Dict[str, Any]) -> List[str]:
        # Canonical field in JSON registries is "evidence_sources".
        # Keep backward compatibility with legacy "evidenceRequired".
        required = rule.get("evidence_sources")
        if required is None:
            required = rule.get("evidenceRequired", [])
        if not isinstance(required, list):
            return []
        return [str(item) for item in required if isinstance(item, str)]

    def evaluate(
        self,
        rule_id: str,
        state: Dict[str, Any],
        extra_evidence: Optional[Dict[str, Any]] = None,
        sector: Optional[str] = None,
    ) -> EvaluationResult:
        rule = self._get_rule(rule_id, sector)
        if not rule:
            return self._create_fail_result(rule_id, "Regla no encontrada")

        state_evidence = state.get("evidence", {})
        if not isinstance(state_evidence, dict):
            state_evidence = {}
        evidence = {**state_evidence, **(extra_evidence or {})}
        required_evidence = self._extract_required_evidence(rule)
        missing = [e for e in required_evidence if e not in evidence]

        status = (
            "PASS"
            if not missing
            else rule.get(
                "outcomeOnViolation",
                self.severity_mapping.get(rule["severity"], "FAIL_CLOSED"),
            )
        )

        result = EvaluationResult(
            ruleId=rule["rule_id"],
            sector=rule["sector"],
            status=status,
            severity=rule["severity"],
            evidenceMissing=missing,
            evidenceProvided=list(evidence.keys()),
            reason="Faltan evidencias" if missing else "Regla satisfecha",
            actionTaken=status,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )

        if status == "FAIL_CLOSED":
            print(f"🚨 FAIL_CLOSED → {rule_id} ({rule['sector']})")
        return result

    def evaluate_batch(self, sectors: List[str], data: Dict, state: Dict) -> bool:
        for sector in sectors:
            self._ensure_sector_loaded(sector)
            if sector not in self.registries:
                continue
            for rule in self.registries[sector].get("rules", []):
                if rule.get("severity") == "CRITICAL":
                    result = self.evaluate(rule["rule_id"], state, data, sector=sector)
                    if result.status == "FAIL_CLOSED":
                        return False
        return True

    def _create_fail_result(self, rule_id: str, reason: str) -> EvaluationResult:
        return EvaluationResult(
            ruleId=rule_id,
            sector="UNKNOWN",
            status="FAIL_CLOSED",
            severity="CRITICAL",
            evidenceMissing=["rule_not_found"],
            evidenceProvided=[],
            reason=reason,
            actionTaken="FAIL_CLOSED",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _build_cli_evidence(
    manager: RegistryManager,
    rule_id: str,
    sector: str,
    evidence_ok: bool,
) -> Dict[str, Any]:
    if not evidence_ok:
        return {}

    rule = manager._get_rule(rule_id, sector)
    if not rule:
        return {}

    required = manager._extract_required_evidence(rule)
    return {key: {"present": True} for key in required}


def main() -> int:
    parser = argparse.ArgumentParser(description="RegistryManager CLI (fail-closed)")
    parser.add_argument("--config", default="config/registry-manager-config.json", help="Ruta de config JSON")
    parser.add_argument("--rule-id", required=True, help="Rule ID a evaluar")
    parser.add_argument("--sector", default="CORE", help="Sector esperado para carga lazy")
    parser.add_argument(
        "--evidence-ok",
        default="true",
        help="Si true, inyecta evidencia mínima requerida para PASS",
    )
    parser.add_argument(
        "--extra-evidence-json",
        default="",
        help="JSON object con evidencia extra (opcional)",
    )
    args = parser.parse_args()

    manager = RegistryManager(config_path=args.config)
    evidence_ok = _parse_bool(args.evidence_ok)
    state = {"evidence": _build_cli_evidence(manager, args.rule_id, args.sector, evidence_ok)}

    extra_evidence: Dict[str, Any] = {}
    if args.extra_evidence_json.strip():
        try:
            loaded = json.loads(args.extra_evidence_json)
            if not isinstance(loaded, dict):
                print("ERROR: --extra-evidence-json debe ser objeto JSON", file=sys.stderr)
                return 2
            extra_evidence = loaded
        except json.JSONDecodeError as exc:
            print(f"ERROR: invalid JSON en --extra-evidence-json: {exc}", file=sys.stderr)
            return 2

    result = manager.evaluate(
        args.rule_id,
        state=state,
        extra_evidence=extra_evidence,
        sector=args.sector,
    )

    print(json.dumps(result.__dict__, ensure_ascii=False))
    return 0 if result.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
