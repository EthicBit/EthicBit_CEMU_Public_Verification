import asyncio
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from scripts.core.EvidenceBroker import EvidenceBroker


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
    brokerReport: Dict[str, Any]
    metadata: Dict[str, Any]


class RegistryManager:
    ALLOWED_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    ALLOWED_OUTCOMES = {"PASS", "WARN", "WARN_DEGRADE", "REJECT", "FAIL_CLOSED"}

    def __init__(self, config_path: str = "config/registry-manager-config.json"):
        self.config = self._load_config(config_path)
        self.registries: Dict[str, Dict[str, Any]] = {}
        self.rule_index: Dict[str, Dict[str, Any]] = {}
        self._loaded_sectors: Set[str] = set()
        self._base_path = Path(".")
        self.evidence_broker = EvidenceBroker(config_path)

        evaluation_settings = self.config.get("evaluationSettings", {})
        self.severity_mapping = evaluation_settings.get("defaultSeverityMapping", {})
        self.fallback_to_core = bool(evaluation_settings.get("fallbackToCore", True))
        self.fail_closed_on_broker_error = bool(
            evaluation_settings.get("failClosedOnBrokerError", True)
        )
        self.fail_closed_on_conflict = bool(
            evaluation_settings.get("failClosedOnConflict", True)
        )
        self.require_human_approval_verification = bool(
            evaluation_settings.get("requireHumanApprovalVerification", True)
        )

        self._validate_config()

        print("✅ RegistryManager v2.2b inicializado correctamente | Lazy Loading activo")

    def _load_config(self, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _validate_config(self) -> None:
        for severity in self.ALLOWED_SEVERITIES:
            if severity not in self.severity_mapping:
                raise ValueError(f"defaultSeverityMapping no define severidad: {severity}")

        for severity, outcome in self.severity_mapping.items():
            if severity not in self.ALLOWED_SEVERITIES:
                raise ValueError(f"Severity no permitida en config: {severity}")
            if outcome not in self.ALLOWED_OUTCOMES:
                raise ValueError(f"Outcome no permitido en config: {outcome}")

    def _normalize_required_evidence(self, rule: Dict[str, Any]) -> List[str]:
        evidence_required = rule.get("evidenceRequired")
        if isinstance(evidence_required, list):
            return evidence_required

        evidence_sources = rule.get("evidence_sources")
        if isinstance(evidence_sources, list):
            return evidence_sources

        return []

    def _load_registry(self, sector: str) -> None:
        if sector in self._loaded_sectors:
            return

        for reg_info in self.config["registries"]:
            if reg_info["sector"] != sector:
                continue

            file_path = self._base_path / reg_info["file"]
            with open(file_path, "r", encoding="utf-8") as f:
                registry_data = json.load(f)

            self._validate_registry(sector, registry_data)

            self.registries[sector] = registry_data
            for rule in registry_data.get("rules", []):
                rule["sector"] = sector
                rule["evidenceRequired"] = self._normalize_required_evidence(rule)
                rule_id = rule["rule_id"]

                if rule_id in self.rule_index:
                    raise ValueError(f"rule_id duplicado detectado: {rule_id}")

                self.rule_index[rule_id] = rule

            self._loaded_sectors.add(sector)
            print(f"📦 Sector cargado: {sector}")
            return

        raise ValueError(f"Sector desconocido: {sector}")

    def _validate_registry(self, sector: str, registry_data: Dict[str, Any]) -> None:
        rules = registry_data.get("rules", [])
        if not isinstance(rules, list):
            raise ValueError(f"Registry inválido para sector {sector}: 'rules' debe ser lista")

        seen = set()
        for rule in rules:
            rule_id = rule.get("rule_id")
            severity = rule.get("severity")
            evidence_required = self._normalize_required_evidence(rule)
            outcome_on_violation = rule.get("outcomeOnViolation")

            if not rule_id:
                raise ValueError(f"Regla inválida en {sector}: falta rule_id")
            if rule_id in seen:
                raise ValueError(f"rule_id duplicado dentro de {sector}: {rule_id}")
            seen.add(rule_id)

            if severity not in self.ALLOWED_SEVERITIES:
                raise ValueError(f"Severity inválida en {rule_id}: {severity}")

            if not isinstance(evidence_required, list):
                raise ValueError(f"evidenceRequired/evidence_sources inválido en {rule_id}: debe ser lista")

            if outcome_on_violation and outcome_on_violation not in self.ALLOWED_OUTCOMES:
                raise ValueError(
                    f"outcomeOnViolation inválido en {rule_id}: {outcome_on_violation}"
                )

    def _ensure_sector_loaded(self, sector: Optional[str] = None) -> None:
        if sector and sector not in self._loaded_sectors:
            self._load_registry(sector)

        if self.fallback_to_core and "CORE" not in self._loaded_sectors:
            self._load_registry("CORE")

    def _get_rule(self, rule_id: str, sector: Optional[str] = None) -> Optional[Dict[str, Any]]:
        self._ensure_sector_loaded(sector)
        return self.rule_index.get(rule_id)

    def _requires_external_broker(self, rule: Dict[str, Any]) -> bool:
        tags = set(rule.get("tags", []))
        required = set(self._normalize_required_evidence(rule))

        external_keys = {
            "price",
            "identity",
            "kycVerification",
            "financialTxHash",
            "cryptographicSignature",
            "humanApproval",
        }

        if rule.get("externalEvidenceRequired") is True:
            return True

        if "EXTERNAL_EVIDENCE" in tags or "BROKER_REQUIRED" in tags:
            return True

        return bool(required & external_keys)

    def _is_critical_rule(self, rule: Dict[str, Any]) -> bool:
        tags = set(rule.get("tags", []))
        decision_mode = rule.get("decisionMode", "")
        return (
            rule.get("severity") == "CRITICAL"
            or "CRITICAL" in tags
            or "ANCHOR_REQUIRED" in tags
            or "ONCHAIN_VERIFIED" in tags
            or decision_mode == "HUMAN_REQUIRED"
        )

    def _requires_human_approval(self, rule: Dict[str, Any]) -> bool:
        decision_mode = rule.get("decisionMode", "")
        evidence_required = set(self._normalize_required_evidence(rule))
        tags = set(rule.get("tags", []))
        return (
            decision_mode == "HUMAN_REQUIRED"
            or "humanApproval" in evidence_required
            or "HUMAN_REQUIRED" in tags
        )

    def _verify_human_approval(self, merged_evidence: Dict[str, Any]) -> bool:
        human_approval = merged_evidence.get("humanApproval")
        if not isinstance(human_approval, dict):
            return False

        approved = human_approval.get("approved") is True
        approver = bool(human_approval.get("approver"))
        timestamp = bool(human_approval.get("timestamp"))
        signature = human_approval.get("signature")

        signature_ok = isinstance(signature, str) and signature.startswith("attest::")
        return approved and approver and timestamp and signature_ok

    def _now(self) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

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
            timestamp=self._now(),
            brokerReport={},
            metadata={"final_gate": "FAIL_CLOSED"},
        )

    async def _evaluate_external_evidence(
        self,
        rule: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        evidence, broker_report = await self.evidence_broker.fetch_evidence(rule, state)

        quorum_met = bool(broker_report.get("quorum_met", False))
        final_gate = broker_report.get("final_gate", "FAIL_CLOSED")
        conflicts = broker_report.get("conflicts", {}) or {}
        errors = broker_report.get("errors", []) or []
        consensus = float(broker_report.get("evidence_consensus_score", 0.0))

        fail_closed = False

        if not quorum_met:
            fail_closed = True
        if final_gate != "PASS":
            fail_closed = True
        if conflicts and self.fail_closed_on_conflict:
            fail_closed = True
        if errors and self.fail_closed_on_broker_error:
            fail_closed = True

        return {
            "evidence": evidence,
            "broker_report": broker_report,
            "quorum_met": quorum_met,
            "final_gate": final_gate,
            "conflicts": conflicts,
            "errors": errors,
            "evidence_consensus_score": consensus,
            "fail_closed": fail_closed,
            "fail_closed_reason": broker_report.get("fail_closed_reason", "UNKNOWN"),
        }

    async def evaluate_async(
        self,
        rule_id: str,
        state: Dict[str, Any],
        extra_evidence: Optional[Dict[str, Any]] = None,
        sector: Optional[str] = None,
    ) -> EvaluationResult:
        rule = self._get_rule(rule_id, sector)
        if not rule:
            return self._create_fail_result(rule_id, "Regla no encontrada")

        fallback_used = sector is None and self.fallback_to_core
        metadata: Dict[str, Any] = {
            "fallback_used": fallback_used,
            "fallback_source": "CORE" if fallback_used else None,
            "fallback_reason": "sector_not_specified" if fallback_used else None,
            "sector_requested": sector,
            "sector_resolved": rule.get("sector"),
        }

        internal_evidence = {**state.get("evidence", {}), **(extra_evidence or {})}
        evidence_required = self._normalize_required_evidence(rule)

        broker_report: Dict[str, Any] = {}
        broker_evidence: Dict[str, Any] = {}

        if evidence_required and self._requires_external_broker(rule):
            broker_eval = await self._evaluate_external_evidence(rule, state)
            broker_evidence = broker_eval["evidence"]
            broker_report = broker_eval["broker_report"]

            metadata.update(
                {
                    "quorum_met": broker_eval["quorum_met"],
                    "final_gate": broker_eval["final_gate"],
                    "conflicts": broker_eval["conflicts"],
                    "evidence_errors": broker_eval["errors"],
                    "evidence_consensus_score": broker_eval["evidence_consensus_score"],
                }
            )

            if broker_eval["fail_closed"] and self._is_critical_rule(rule):
                return EvaluationResult(
                    ruleId=rule["rule_id"],
                    sector=rule["sector"],
                    status="FAIL_CLOSED",
                    severity=rule["severity"],
                    evidenceMissing=evidence_required,
                    evidenceProvided=list(internal_evidence.keys()),
                    reason=f"EVIDENCE_FAIL_CLOSED::{broker_eval['fail_closed_reason']}",
                    actionTaken="FAIL_CLOSED",
                    timestamp=self._now(),
                    brokerReport=broker_report,
                    metadata=metadata,
                )

        merged_evidence = {**broker_evidence, **internal_evidence}
        missing = [e for e in evidence_required if e not in merged_evidence]

        if self.require_human_approval_verification and self._requires_human_approval(rule):
            if not self._verify_human_approval(merged_evidence):
                metadata["final_gate"] = "FAIL_CLOSED"
                metadata["human_approval_verified"] = False
                return EvaluationResult(
                    ruleId=rule["rule_id"],
                    sector=rule["sector"],
                    status="FAIL_CLOSED",
                    severity=rule["severity"],
                    evidenceMissing=["humanApproval"],
                    evidenceProvided=list(merged_evidence.keys()),
                    reason="HUMAN_APPROVAL_NOT_VERIFIED",
                    actionTaken="FAIL_CLOSED",
                    timestamp=self._now(),
                    brokerReport=broker_report,
                    metadata=metadata,
                )

            metadata["human_approval_verified"] = True

        if missing:
            status = rule.get(
                "outcomeOnViolation",
                self.severity_mapping.get(rule["severity"], "FAIL_CLOSED"),
            )
            reason = "Faltan evidencias requeridas"
        else:
            status = "PASS"
            reason = "Regla satisfecha"

        if self._is_critical_rule(rule) and broker_report:
            threshold = float(
                self.config.get("evidenceBroker", {}).get(
                    "consensus_threshold_critical", 0.90
                )
            )
            score = float(metadata.get("evidence_consensus_score", 0.0))
            if score < threshold:
                status = "FAIL_CLOSED"
                reason = "EVIDENCE_CONSENSUS_BELOW_THRESHOLD"
                metadata["final_gate"] = "FAIL_CLOSED"

        if status == "FAIL_CLOSED":
            print(f"🚨 FAIL_CLOSED → {rule_id} ({rule['sector']})")

        return EvaluationResult(
            ruleId=rule["rule_id"],
            sector=rule["sector"],
            status=status,
            severity=rule["severity"],
            evidenceMissing=missing,
            evidenceProvided=list(merged_evidence.keys()),
            reason=reason,
            actionTaken=status,
            timestamp=self._now(),
            brokerReport=broker_report,
            metadata=metadata,
        )

    def evaluate(
        self,
        rule_id: str,
        state: Dict[str, Any],
        extra_evidence: Optional[Dict[str, Any]] = None,
        sector: Optional[str] = None,
    ) -> EvaluationResult:
        return asyncio.run(self.evaluate_async(rule_id, state, extra_evidence, sector))

    async def evaluate_batch_async(
        self,
        sectors: List[str],
        data: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        results = []

        for sector in sectors:
            self._ensure_sector_loaded(sector)
            if sector not in self.registries:
                continue

            for rule in self.registries[sector].get("rules", []):
                if rule.get("severity") != "CRITICAL":
                    continue

                result = await self.evaluate_async(
                    rule_id=rule["rule_id"],
                    state=state,
                    extra_evidence=data,
                    sector=sector,
                )
                results.append(asdict(result))

                if result.status == "FAIL_CLOSED":
                    return {
                        "status": "FAIL_CLOSED",
                        "sector": sector,
                        "blocking_rule": rule["rule_id"],
                        "results": results,
                    }

        return {
            "status": "PASS",
            "results": results,
        }

    def evaluate_batch(
        self,
        sectors: List[str],
        data: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        return asyncio.run(self.evaluate_batch_async(sectors, data, state))


if __name__ == "__main__":
    rm = RegistryManager()
    print("✅ RegistryManager v2.2b cargado correctamente")
