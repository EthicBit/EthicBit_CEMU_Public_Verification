"""
EthicBit LangGraph Adapter — v1.0.0

Wraps LangGraph tool-call execution with EthicBit constitutional governance:
  - Risk-based pre-execution gate (LOW/MEDIUM → AUTO_PASS, HIGH → HITL_REQUIRED)
  - Blocked pattern detection
  - Claim boundary enforcement
  - Governance receipt generation per tool call
  - Audit log persistence

Non-claims (per claim_policy.json):
  Not production deployment. Not externally validated. Not security certified.
  HITL in demo mode is simulated.
"""
from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent


class GovernanceDecision(str, Enum):
    AUTO_PASS     = "AUTO_PASS"
    BLOCK         = "BLOCK"
    HITL_REQUIRED = "HITL_REQUIRED"
    HITL_APPROVED = "HITL_APPROVED"
    HITL_REJECTED = "HITL_REJECTED"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class ClaimBoundaryEngine:
    """Enforces the claim boundary defined in claim_policy.json."""

    def __init__(self, policy: dict) -> None:
        self._boundary = policy.get("claim_boundary", {})
        self._non_claims = policy.get("non_claims", [])

    def check(self) -> dict:
        violations = [k for k, v in self._boundary.items() if v is True]
        return {
            "claim_boundary_enforced": True,
            "violations": violations,
            "passed": len(violations) == 0,
            "non_claims": self._non_claims,
        }


class GovernanceGate:
    """Pre-execution gate: classify risk, detect blocked patterns, decide."""

    def __init__(self, policy: dict) -> None:
        self._risk_registry: dict[str, str] = policy.get("tool_risk_registry", {})
        self._risk_levels: dict[str, dict] = policy.get("risk_levels", {})
        self._blocked_patterns: list[str] = policy.get("blocked_patterns", [])

    def _detect_blocked(self, args: dict) -> str | None:
        payload = json.dumps(args).lower()
        for p in self._blocked_patterns:
            if p.lower() in payload:
                return p
        return None

    def evaluate(self, tool_name: str, args: dict) -> tuple[GovernanceDecision, str]:
        blocked = self._detect_blocked(args)
        if blocked:
            return GovernanceDecision.BLOCK, f"blocked pattern detected: {blocked!r}"

        risk = self._risk_registry.get(tool_name, "MEDIUM")
        level_cfg = self._risk_levels.get(risk, {})

        if level_cfg.get("hitl_required", False):
            return GovernanceDecision.HITL_REQUIRED, f"risk_level={risk} requires HITL"
        return GovernanceDecision.AUTO_PASS, f"risk_level={risk} auto-approved"


class HITLSimulator:
    """
    Demo-mode HITL simulator.

    In a real deployment this would pause the graph and wait for a human
    to approve via API (/approve endpoint). In demo mode the decision is
    driven by the DEMO_HITL_APPROVE env var (default: true).
    """

    def __init__(self) -> None:
        self._auto_approve = os.environ.get("DEMO_HITL_APPROVE", "true").lower() == "true"

    def request_approval(self, tool_name: str, args: dict, reason: str) -> tuple[bool, str]:
        if self._auto_approve:
            return True, "DEMO_HITL_APPROVE=true — simulated approval"
        return False, "DEMO_HITL_APPROVE=false — simulated rejection"


class AuditLog:
    """Thread-simple in-process audit log for the demo run."""

    def __init__(self) -> None:
        self._entries: list[dict] = []

    def record(self, receipt: dict) -> None:
        self._entries.append(receipt)

    def all_entries(self) -> list[dict]:
        return list(self._entries)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._entries, indent=2))


class EthicBitLangGraphAdapter:
    """
    Core adapter — call evaluate_tool_call() before every tool execution
    inside the LangGraph graph.
    """

    def __init__(self, policy_path: Path | None = None) -> None:
        path = policy_path or ROOT / "claim_policy.json"
        self._policy = json.loads(path.read_text())
        self._gate = GovernanceGate(self._policy)
        self._cbe = ClaimBoundaryEngine(self._policy)
        self._hitl = HITLSimulator()
        self.audit_log = AuditLog()
        self._run_id = str(uuid.uuid4())[:8]

        cbe_result = self._cbe.check()
        if not cbe_result["passed"]:
            raise RuntimeError(f"Claim boundary violations at init: {cbe_result['violations']}")

    def evaluate_tool_call(
        self,
        tool_name: str,
        args: dict,
        call_id: str | None = None,
    ) -> dict:
        """
        Evaluate a tool call through the governance gate.

        Returns a governance receipt dict with final_decision, approved, and
        all audit fields. Does NOT execute the tool — the caller decides.
        """
        receipt_id = str(uuid.uuid4())
        cid = call_id or receipt_id[:8]

        decision, reason = self._gate.evaluate(tool_name, args)
        hitl_details: dict = {}

        if decision == GovernanceDecision.HITL_REQUIRED:
            approved, hitl_note = self._hitl.request_approval(tool_name, args, reason)
            if approved:
                decision = GovernanceDecision.HITL_APPROVED
                hitl_details = {"hitl_simulated": True, "hitl_note": hitl_note}
            else:
                decision = GovernanceDecision.HITL_REJECTED
                hitl_details = {"hitl_simulated": True, "hitl_note": hitl_note}

        approved = decision in (GovernanceDecision.AUTO_PASS, GovernanceDecision.HITL_APPROVED)
        risk = self._policy["tool_risk_registry"].get(tool_name, "MEDIUM")

        receipt = {
            "schema_id": "ETHICBIT_LANGGRAPH_GOVERNANCE_RECEIPT_V1",
            "receipt_id": receipt_id,
            "call_id": cid,
            "run_id": self._run_id,
            "tool_name": tool_name,
            "risk_level": risk,
            "governance_decision": decision.value,
            "approved": approved,
            "reason": reason,
            "args_sha256": _sha256(args),
            "claim_boundary_enforced": True,
            "constitutional_dependency": "EthicBit/CEMU/v3.7.0+",
            "timestamp": _now(),
            **hitl_details,
        }

        self.audit_log.record(receipt)
        return receipt

    def summary(self) -> dict:
        entries = self.audit_log.all_entries()
        return {
            "run_id": self._run_id,
            "total_tool_calls": len(entries),
            "approved": sum(1 for e in entries if e["approved"]),
            "blocked":  sum(1 for e in entries if e["governance_decision"] == GovernanceDecision.BLOCK.value),
            "hitl_approved":  sum(1 for e in entries if e["governance_decision"] == GovernanceDecision.HITL_APPROVED.value),
            "hitl_rejected":  sum(1 for e in entries if e["governance_decision"] == GovernanceDecision.HITL_REJECTED.value),
            "claim_boundary_enforced": True,
            "constitutional_dependency": "EthicBit/CEMU/v3.7.0+",
            "non_claims": self._policy.get("non_claims", []),
        }
