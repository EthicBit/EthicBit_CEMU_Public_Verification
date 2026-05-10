"""
AEM-EVOLVE™ v2.0 PR 6 — Incident Response Runbook and Drill Evidence Gate.

C-01–C-08 pass on file presence and content inspection (no live infra needed).
C-09 requires AEM_DRILL_COMPLETED_AT env var (live drill timestamp).
C-10 requires AEM_DRILL_SIGNOFF_APPROVER env var (approver sign-off).

Non-claims:
  Alert delivery verification and live drill execution require a running
  environment. File-based checks prove configuration, not execution.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

_DEMO_ROOT = Path(__file__).resolve().parents[1]
_DOCS_DIR = _DEMO_ROOT / "docs"
_IR_DIR = _DEMO_ROOT / "tools" / "incident_response"

_RUNBOOK_FILE = _DOCS_DIR / "INCIDENT_RESPONSE.md"
_DRILL_SCRIPT = _IR_DIR / "drill_scenario.py"
_DRILL_EVIDENCE_GLOB = "drill_evidence_*.json"

# All 7 mandatory incident types that must appear in the runbook
_REQUIRED_INCIDENTS = [
    "INC-01",
    "INC-02",
    "INC-03",
    "INC-04",
    "INC-05",
    "INC-06",
    "INC-07",
]

# Alert names from PR 5 that the runbook must cross-reference
_REQUIRED_ALERT_NAMES = [
    "AEM_HITLApprovalFailed",
    "AEM_SignatureVerificationFailed",
    "AEM_ReplayAttemptDetected",
    "AEM_AuditChainMismatch",
    "AEM_DatabaseUnavailable",
    "AEM_KMSSigningFailed",
    "AEM_OIDCProviderOutage",
]

_SEVERITY_LEVELS = ["P1", "P2", "P3"]
_ESCALATION_ROLES = ["Governance Lead", "Security Lead", "Database Admin"]


class IncidentResponseGate:
    """Gate verifier for incident response runbook and drill evidence (PR 6)."""

    def __init__(
        self,
        drill_completed_at: str | None = None,
        drill_signoff_approver: str | None = None,
    ) -> None:
        self._drill_completed_at = drill_completed_at
        self._drill_signoff_approver = drill_signoff_approver

    @classmethod
    def from_env(cls) -> "IncidentResponseGate":
        return cls(
            drill_completed_at=os.getenv("AEM_DRILL_COMPLETED_AT", "").strip() or None,
            drill_signoff_approver=os.getenv("AEM_DRILL_SIGNOFF_APPROVER", "").strip() or None,
        )

    # ── C-01: Runbook file exists ─────────────────────────────────────────────

    def check_runbook_exists(self) -> dict[str, Any]:
        if not _RUNBOOK_FILE.exists():
            return {"ok": False, "detail": f"INCIDENT_RESPONSE.md not found at {_RUNBOOK_FILE}"}
        content = _RUNBOOK_FILE.read_text(encoding="utf-8")
        sha256 = hashlib.sha256(content.encode()).hexdigest()
        return {
            "ok": True,
            "file": str(_RUNBOOK_FILE),
            "sha256": sha256,
            "size_bytes": len(content.encode()),
        }

    # ── C-02: Runbook covers all 7 incident types ─────────────────────────────

    def check_runbook_coverage(self) -> dict[str, Any]:
        if not _RUNBOOK_FILE.exists():
            return {"ok": False, "detail": "INCIDENT_RESPONSE.md missing — run C-01 first"}
        content = _RUNBOOK_FILE.read_text(encoding="utf-8")
        missing = [inc for inc in _REQUIRED_INCIDENTS if inc not in content]
        return {
            "ok": not missing,
            "incidents_required": len(_REQUIRED_INCIDENTS),
            "incidents_present": len(_REQUIRED_INCIDENTS) - len(missing),
            "missing_incidents": missing,
        }

    # ── C-03: Severity levels defined (P1/P2/P3) ─────────────────────────────

    def check_severity_levels(self) -> dict[str, Any]:
        if not _RUNBOOK_FILE.exists():
            return {"ok": False, "detail": "INCIDENT_RESPONSE.md missing"}
        content = _RUNBOOK_FILE.read_text(encoding="utf-8")
        present = [s for s in _SEVERITY_LEVELS if s in content]
        missing = [s for s in _SEVERITY_LEVELS if s not in content]
        return {
            "ok": not missing,
            "severity_levels_present": present,
            "missing_severity_levels": missing,
        }

    # ── C-04: Escalation matrix defined ──────────────────────────────────────

    def check_escalation_matrix(self) -> dict[str, Any]:
        if not _RUNBOOK_FILE.exists():
            return {"ok": False, "detail": "INCIDENT_RESPONSE.md missing"}
        content = _RUNBOOK_FILE.read_text(encoding="utf-8")
        present_roles = [r for r in _ESCALATION_ROLES if r in content]
        missing_roles = [r for r in _ESCALATION_ROLES if r not in content]
        has_matrix = "Escalation Matrix" in content
        return {
            "ok": has_matrix and not missing_roles,
            "has_escalation_matrix": has_matrix,
            "roles_present": present_roles,
            "missing_roles": missing_roles,
        }

    # ── C-05: Recovery procedures section present ─────────────────────────────

    def check_recovery_procedures(self) -> dict[str, Any]:
        if not _RUNBOOK_FILE.exists():
            return {"ok": False, "detail": "INCIDENT_RESPONSE.md missing"}
        content = _RUNBOOK_FILE.read_text(encoding="utf-8")
        has_recovery = "Recovery steps" in content or "Recovery procedure" in content
        has_postmortem = "Post-Mortem" in content or "Post-mortem" in content
        return {
            "ok": has_recovery and has_postmortem,
            "has_recovery_steps": has_recovery,
            "has_postmortem_template": has_postmortem,
        }

    # ── C-06: Alert names from PR 5 cross-referenced ─────────────────────────

    def check_alert_cross_reference(self) -> dict[str, Any]:
        if not _RUNBOOK_FILE.exists():
            return {"ok": False, "detail": "INCIDENT_RESPONSE.md missing"}
        content = _RUNBOOK_FILE.read_text(encoding="utf-8")
        missing = [a for a in _REQUIRED_ALERT_NAMES if a not in content]
        return {
            "ok": not missing,
            "alerts_required": len(_REQUIRED_ALERT_NAMES),
            "alerts_cross_referenced": len(_REQUIRED_ALERT_NAMES) - len(missing),
            "missing_alerts": missing,
        }

    # ── C-07: Drill scenario script exists ───────────────────────────────────

    def check_drill_script(self) -> dict[str, Any]:
        if not _DRILL_SCRIPT.exists():
            return {"ok": False, "detail": f"drill_scenario.py not found at {_DRILL_SCRIPT}"}
        content = _DRILL_SCRIPT.read_text(encoding="utf-8")
        sha256 = hashlib.sha256(content.encode()).hexdigest()
        scenarios_count = content.count('"INC-')
        return {
            "ok": scenarios_count >= 7,
            "file": str(_DRILL_SCRIPT),
            "sha256": sha256,
            "scenarios_defined": scenarios_count,
        }

    # ── C-08: Drill evidence artifact exists ─────────────────────────────────

    def check_drill_evidence(self) -> dict[str, Any]:
        artifacts = sorted(_IR_DIR.glob(_DRILL_EVIDENCE_GLOB)) if _IR_DIR.exists() else []
        if not artifacts:
            return {
                "ok": False,
                "detail": (
                    f"No drill_evidence_*.json found in {_IR_DIR}. "
                    "Run: python tools/incident_response/drill_scenario.py --all"
                ),
            }
        latest = artifacts[-1]
        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "detail": f"Invalid JSON in {latest.name}: {exc}"}

        sha256 = hashlib.sha256(latest.read_bytes()).hexdigest()
        scenarios_count = len(data.get("scenarios", []))
        return {
            "ok": scenarios_count >= 7,
            "file": str(latest),
            "sha256": sha256,
            "scenarios_documented": scenarios_count,
            "drill_date_utc": data.get("drill_date_utc", ""),
            "dry_run": data.get("dry_run", True),
        }

    # ── C-09: Drill completed timestamp present ───────────────────────────────

    def check_drill_completed(self) -> dict[str, Any]:
        if not self._drill_completed_at:
            return {
                "ok": False,
                "skipped": True,
                "reason": "AEM_DRILL_COMPLETED_AT not set — set to ISO8601 timestamp of live drill",
            }
        return {
            "ok": True,
            "drill_completed_at": self._drill_completed_at,
        }

    # ── C-10: Drill sign-off approver present ────────────────────────────────

    def check_drill_signoff(self) -> dict[str, Any]:
        if not self._drill_signoff_approver:
            return {
                "ok": False,
                "skipped": True,
                "reason": "AEM_DRILL_SIGNOFF_APPROVER not set — set to approver identity for sign-off",
            }
        return {
            "ok": True,
            "signoff_approver": self._drill_signoff_approver,
        }

    # ── Full gate ─────────────────────────────────────────────────────────────

    def gate_check(self) -> dict[str, Any]:
        c01 = self.check_runbook_exists()
        c02 = self.check_runbook_coverage()
        c03 = self.check_severity_levels()
        c04 = self.check_escalation_matrix()
        c05 = self.check_recovery_procedures()
        c06 = self.check_alert_cross_reference()
        c07 = self.check_drill_script()
        c08 = self.check_drill_evidence()
        c09 = self.check_drill_completed()
        c10 = self.check_drill_signoff()

        checks = {
            "C-01_runbook_exists": c01,
            "C-02_runbook_coverage": c02,
            "C-03_severity_levels": c03,
            "C-04_escalation_matrix": c04,
            "C-05_recovery_procedures": c05,
            "C-06_alert_cross_reference": c06,
            "C-07_drill_script": c07,
            "C-08_drill_evidence": c08,
            "C-09_drill_completed": c09,
            "C-10_drill_signoff": c10,
        }

        passed = sum(1 for v in checks.values() if v.get("ok"))
        failed = len(checks) - passed
        status = "PASS" if failed == 0 else "FAIL"

        fail_reason = None
        if status == "FAIL":
            missing_live = []
            if not self._drill_completed_at:
                missing_live.append("AEM_DRILL_COMPLETED_AT")
            if not self._drill_signoff_approver:
                missing_live.append("AEM_DRILL_SIGNOFF_APPROVER")
            if missing_live:
                fail_reason = f"Live drill evidence missing: {', '.join(missing_live)}"
            else:
                failing = [k for k, v in checks.items() if not v.get("ok")]
                fail_reason = f"Failing checks: {', '.join(failing)}"

        return {
            "gate": "INCIDENT_RESPONSE_CHECK",
            "status": status,
            "checks_passed": passed,
            "checks_failed": failed,
            "drill_completed_at": self._drill_completed_at,
            "drill_signoff_approver": self._drill_signoff_approver,
            "fail_reason": fail_reason,
            "checks": checks,
        }
