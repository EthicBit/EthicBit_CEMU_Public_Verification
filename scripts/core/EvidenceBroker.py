import asyncio
import json
import os
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class EvidenceResult:
    provider: str
    status: str
    evidence: Dict[str, Any]
    timestamp: str
    confidence: float
    signature: str = ""
    error: str = ""


class EvidenceBroker:
    DEFAULT_CONFIG = {
        "mode": "MOCK",
        "providers": ["self-attested", "chainlink", "jumio"],
        "quorum": 2,
        "timeout_seconds": 5.0,
        "max_providers": 3,
        "consensus_threshold_critical": 0.90,
        "consensus_threshold_default": 0.75,
        "allow_mock_in_canonical_audit": False,
        "mock_mode_status": "NON_PRODUCTION",
        "providerTrust": {
            "self-attested": 0.40,
            "chainlink": 0.90,
            "jumio": 0.85
        },
        "mock_delays": {
            "self-attested": 0.05,
            "chainlink": 0.30,
            "jumio": 0.80,
            "onfido": 0.90
        }
    }

    def __init__(self, config_path: str = "config/registry-manager-config.json"):
        self.config_path = config_path
        self.config = self._load_config(config_path)

        broker_cfg = self.config.get("evidenceBroker", {})

        self.mode = os.getenv(
            "EVIDENCE_BROKER_MODE",
            broker_cfg.get("mode", self.DEFAULT_CONFIG["mode"])
        ).upper()

        self.trusted_providers = broker_cfg.get(
            "providers",
            self.DEFAULT_CONFIG["providers"]
        )
        self.quorum_threshold = int(
            broker_cfg.get("quorum", self.DEFAULT_CONFIG["quorum"])
        )
        self.timeout = float(
            broker_cfg.get("timeout_seconds", self.DEFAULT_CONFIG["timeout_seconds"])
        )
        self.max_providers = int(
            broker_cfg.get("max_providers", self.DEFAULT_CONFIG["max_providers"])
        )
        self.consensus_threshold_critical = float(
            broker_cfg.get(
                "consensus_threshold_critical",
                self.DEFAULT_CONFIG["consensus_threshold_critical"]
            )
        )
        self.consensus_threshold_default = float(
            broker_cfg.get(
                "consensus_threshold_default",
                self.DEFAULT_CONFIG["consensus_threshold_default"]
            )
        )
        self.allow_mock_in_canonical_audit = bool(
            broker_cfg.get(
                "allow_mock_in_canonical_audit",
                self.DEFAULT_CONFIG["allow_mock_in_canonical_audit"]
            )
        )
        self.mock_mode_status = broker_cfg.get(
            "mock_mode_status",
            self.DEFAULT_CONFIG["mock_mode_status"]
        )
        self.provider_trust = broker_cfg.get(
            "providerTrust",
            self.DEFAULT_CONFIG["providerTrust"]
        )
        self.mock_delays = broker_cfg.get(
            "mock_delays",
            self.DEFAULT_CONFIG["mock_delays"]
        )

        self._validate_config()

        print(
            "✅ EvidenceBroker v2.2b inicializado | "
            f"modo={self.mode} | providers={self.trusted_providers} | "
            f"quorum={self.quorum_threshold} | timeout={self.timeout}s"
        )

    def _load_config(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"evidenceBroker": dict(self.DEFAULT_CONFIG)}

    def _validate_config(self) -> None:
        if self.quorum_threshold < 1:
            raise ValueError("evidenceBroker.quorum debe ser >= 1")
        if self.max_providers < 1:
            raise ValueError("evidenceBroker.max_providers debe ser >= 1")
        if self.quorum_threshold > self.max_providers:
            raise ValueError("Configuración inválida: quorum no puede ser mayor que max_providers")
        if len(self.trusted_providers) < self.quorum_threshold:
            raise ValueError("Configuración inválida: cantidad de providers menor que quorum")

        for threshold_name, threshold_value in (
            ("consensus_threshold_critical", self.consensus_threshold_critical),
            ("consensus_threshold_default", self.consensus_threshold_default),
        ):
            if threshold_value < 0.0 or threshold_value > 1.0:
                raise ValueError(f"{threshold_name} debe estar entre 0 y 1")

        for provider in self.trusted_providers:
            if provider not in self.provider_trust:
                raise ValueError(f"providerTrust no define peso para provider configurado: {provider}")

        for provider, weight in self.provider_trust.items():
            if weight < 0.0 or weight > 1.0:
                raise ValueError(f"providerTrust inválido para {provider}: debe estar entre 0 y 1")

    async def fetch_evidence(
        self,
        rule: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        required = rule.get("evidenceRequired", [])
        if not required:
            return {}, self._empty_report("NO_EVIDENCE_REQUIRED", rule)

        selected_providers = self.trusted_providers[: self.max_providers]
        tasks = [
            self._safe_call_provider(provider, required, state)
            for provider in selected_providers
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        evidence, report = self._cross_validate(results, rule, state)
        report["ruleId"] = rule.get("rule_id", rule.get("ruleId", "unknown"))
        report["mode"] = self.mode
        report["mock_mode_status"] = self.mock_mode_status if self.mode == "MOCK" else "N/A"
        return evidence, report

    async def _safe_call_provider(
        self,
        provider: str,
        required: List[str],
        state: Dict[str, Any]
    ) -> EvidenceResult:
        try:
            return await asyncio.wait_for(
                self._call_provider(provider, required, state),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            return EvidenceResult(
                provider=provider,
                status="TIMEOUT",
                evidence={},
                timestamp=self._now(),
                confidence=0.0,
                error=f"timeout after {self.timeout}s"
            )
        except Exception as exc:
            return EvidenceResult(
                provider=provider,
                status="ERROR",
                evidence={},
                timestamp=self._now(),
                confidence=0.0,
                error=str(exc)
            )

    async def _call_provider(
        self,
        provider: str,
        required: List[str],
        state: Dict[str, Any]
    ) -> EvidenceResult:
        if self.mode == "REAL":
            return await self._call_real_provider(provider, required, state)

        if self.mode == "STUB":
            return EvidenceResult(
                provider=provider,
                status="NOT_IMPLEMENTED",
                evidence={},
                timestamp=self._now(),
                confidence=0.0,
                error="STUB mode active"
            )

        return await self._call_mock_provider(provider, required, state)

    async def _call_mock_provider(
        self,
        provider: str,
        required: List[str],
        state: Dict[str, Any]
    ) -> EvidenceResult:
        await asyncio.sleep(float(self.mock_delays.get(provider, 0.5)))

        evidence_state = state.get("evidence", {})
        force_fail = bool(evidence_state.get("force_fail", False))
        force_fail_providers = evidence_state.get("force_fail_providers", [])

        if force_fail and (not force_fail_providers or provider in force_fail_providers):
            return EvidenceResult(
                provider=provider,
                status="FAILED",
                evidence={},
                timestamp=self._now(),
                confidence=0.0,
                error="forced failure"
            )

        evidence = self._build_mock_evidence(provider, required)
        confidence = self._provider_confidence(provider)
        signature = self._generate_signature(provider, evidence)

        return EvidenceResult(
            provider=provider,
            status="SUCCESS",
            evidence=evidence,
            timestamp=self._now(),
            confidence=confidence,
            signature=signature
        )

    async def _call_real_provider(
        self,
        provider: str,
        required: List[str],
        state: Dict[str, Any]
    ) -> EvidenceResult:
        return EvidenceResult(
            provider=provider,
            status="NOT_IMPLEMENTED",
            evidence={},
            timestamp=self._now(),
            confidence=0.0,
            error=f"REAL provider not implemented: {provider}"
        )

    def _build_mock_evidence(self, provider: str, required: List[str]) -> Dict[str, Any]:
        evidence: Dict[str, Any] = {}

        for key in required:
            if key == "price":
                evidence["price"] = 2456.78
            elif key == "identity":
                evidence["identity_verified"] = provider in {"jumio", "onfido", "self-attested"}
            elif key == "kycVerification":
                evidence["kycVerification"] = provider in {"jumio", "onfido", "self-attested"}
            elif key == "cryptographicSignature":
                evidence["cryptographicSignature"] = "0x" + uuid.uuid4().hex
            elif key == "financialTxHash":
                evidence["financialTxHash"] = "0xfin" + uuid.uuid4().hex[:40]
            elif key == "humanApproval":
                evidence["humanApproval"] = {
                    "approved": provider == "self-attested",
                    "approver": "ops-controller",
                    "timestamp": self._now(),
                    "signature": "attest::human-approval-mock"
                }
            else:
                evidence[key] = f"mock_{key}_{provider}"

        if provider == "self-attested":
            evidence["self_attested"] = True
            evidence["self_attested_signature"] = "0x" + ("a" * 64)

        return evidence

    def _provider_confidence(self, provider: str) -> float:
        return float(self.provider_trust.get(provider, 0.5))

    def _cross_validate(
        self,
        results: List[EvidenceResult],
        rule: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        successful = [r for r in results if r.status == "SUCCESS"]
        quorum_met = len(successful) >= self.quorum_threshold

        evidence_by_key: Dict[str, Dict[str, Any]] = {}
        errors: List[Dict[str, str]] = []

        for result in results:
            if result.status != "SUCCESS":
                errors.append({
                    "provider": result.provider,
                    "status": result.status,
                    "error": result.error
                })
                continue

            for key, value in result.evidence.items():
                evidence_by_key.setdefault(key, {})
                evidence_by_key[key][result.provider] = value

        merged_evidence: Dict[str, Any] = {}
        conflicts: Dict[str, Dict[str, Any]] = {}

        for key, provider_values in evidence_by_key.items():
            normalized = {
                provider: self._stable_serialize(value)
                for provider, value in provider_values.items()
            }
            unique_values = set(normalized.values())

            if len(unique_values) == 1:
                first_provider = next(iter(provider_values))
                merged_evidence[key] = provider_values[first_provider]
            else:
                conflicts[key] = provider_values

        consensus_score = self._weighted_consensus_score(successful)
        final_gate = self._derive_final_gate(
            quorum_met=quorum_met,
            conflicts=conflicts,
            errors=errors,
            state=state
        )

        report = {
            "quorum_met": quorum_met,
            "final_gate": final_gate,
            "successful_count": len(successful),
            "providers_used": [r.provider for r in results],
            "trusted_providers": self.get_trusted_providers(),
            "attestations": {
                r.provider: {
                    "signature": r.signature,
                    "verified": self.verify_signature(r.signature)
                }
                for r in successful
            },
            "cross_validated_evidence": merged_evidence,
            "conflicts": conflicts,
            "errors": errors,
            "evidence_consensus_score": consensus_score,
            "fail_closed_reason": self._derive_fail_closed_reason(
                quorum_met=quorum_met,
                conflicts=conflicts,
                errors=errors,
                state=state
            ),
            "timestamp": self._now(),
            "raw_results": [asdict(r) for r in results],
            "canonical_audit_mock_blocked": self._is_mock_blocked_for_canonical_audit(state)
        }

        return merged_evidence, report

    def _weighted_consensus_score(self, successful: List[EvidenceResult]) -> float:
        if not successful:
            return 0.0

        weighted_sum = 0.0
        weight_total = 0.0

        for result in successful:
            weight = float(self.provider_trust.get(result.provider, 0.5))
            weighted_sum += result.confidence * weight
            weight_total += weight

        if weight_total == 0:
            return 0.0

        return round(weighted_sum / weight_total, 4)

    def _is_mock_blocked_for_canonical_audit(self, state: Dict[str, Any]) -> bool:
        canonical_audit = bool(state.get("audit", {}).get("canonical", False))
        return self.mode == "MOCK" and canonical_audit and not self.allow_mock_in_canonical_audit

    def _derive_final_gate(
        self,
        quorum_met: bool,
        conflicts: Dict[str, Dict[str, Any]],
        errors: List[Dict[str, str]],
        state: Dict[str, Any]
    ) -> str:
        if self._is_mock_blocked_for_canonical_audit(state):
            return "FAIL_CLOSED"
        if not quorum_met:
            return "FAIL_CLOSED"
        if conflicts:
            return "FAIL_CLOSED"
        if errors:
            return "FAIL_CLOSED"
        return "PASS"

    def _derive_fail_closed_reason(
        self,
        quorum_met: bool,
        conflicts: Dict[str, Dict[str, Any]],
        errors: List[Dict[str, str]],
        state: Dict[str, Any]
    ) -> str:
        if self._is_mock_blocked_for_canonical_audit(state):
            return "MOCK_NOT_ALLOWED_IN_CANONICAL_AUDIT"
        if not quorum_met:
            return "INSUFFICIENT_QUORUM"
        if conflicts:
            return "EVIDENCE_CONFLICT"
        if errors:
            return "PROVIDER_ERROR"
        return "NONE"

    def _empty_report(self, reason: str, rule: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ruleId": rule.get("rule_id", rule.get("ruleId", "unknown")),
            "quorum_met": True,
            "final_gate": "PASS",
            "successful_count": 0,
            "providers_used": [],
            "trusted_providers": self.get_trusted_providers(),
            "attestations": {},
            "cross_validated_evidence": {},
            "conflicts": {},
            "errors": [],
            "evidence_consensus_score": 1.0,
            "fail_closed_reason": reason,
            "timestamp": self._now(),
            "raw_results": [],
            "canonical_audit_mock_blocked": False,
            "mode": self.mode,
            "mock_mode_status": self.mock_mode_status if self.mode == "MOCK" else "N/A"
        }

    def _generate_signature(self, provider: str, evidence: Dict[str, Any]) -> str:
        payload = f"{provider}|{self._stable_serialize(evidence)}|{uuid.uuid4().hex}"
        return "attest::" + str(uuid.uuid5(uuid.NAMESPACE_DNS, payload))

    def verify_signature(self, signature: str) -> bool:
        return isinstance(signature, str) and signature.startswith("attest::")

    def get_trusted_providers(self) -> List[str]:
        return self.trusted_providers[: self.max_providers]

    def _stable_serialize(self, value: Any) -> str:
        try:
            return json.dumps(value, sort_keys=True, separators=(",", ":"))
        except TypeError:
            return str(value)

    def _now(self) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
