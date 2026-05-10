"""
AEM-EVOLVE™ v2.0 PR 14 — Governance Sign-Off Gate.

Verifies that all v2.0 assurance evidence, regulatory mappings, and PR13
production readiness artifacts are in place before a governance lead may
claim governance_signed_off=true.

C-01–C-08 pass on file presence and content inspection (no live infra needed).
C-09 requires AEM_GOVERNANCE_APPROVER env var (identity of governance lead).
C-10 requires AEM_GOVERNANCE_SIGNOFF_DATE env var (ISO8601 date of sign-off).

Non-claims:
  governance_signed_off is always False until both env vars are set AND all
  file-based checks pass. This gate does not constitute regulatory approval.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

_DEMO_ROOT = Path(__file__).resolve().parents[1]
_TOOLS_DIR = _DEMO_ROOT / "tools"
_DOCS_DIR = _DEMO_ROOT / "docs"
_ASSURANCE_V2_DIR = _DEMO_ROOT / "assurance" / "evolve-multi-agent" / "v2_0"
_REGULATORY_DIR = _DOCS_DIR / "regulatory"
_GOVERNANCE_TOOLS_DIR = _TOOLS_DIR / "governance_signoff"

_GOVERNANCE_SIGNOFF_FILE = _DOCS_DIR / "GOVERNANCE_SIGNOFF.md"
_CLAIMS_FILE = _DOCS_DIR / "CLAIMS_AND_NON_CLAIMS.md"
_PR13_REPORT_FILE = _ASSURANCE_V2_DIR / "production_readiness_gate_report.json"

_REQUIRED_REGULATORY_FILES = [
    "EU_AI_ACT_MAPPING.json",
    "ISO_42001_MAPPING.json",
    "NIST_AI_RMF_MAPPING.json",
]

_REQUIRED_ASSURANCE_REPORTS = [
    "monitoring_alerting_check_report.json",
    "incident_response_check_report.json",
    "security_review_check_report.json",
    "reproduction_check_report.json",
    "deployment_audit_check_report.json",
    "slo_evidence_check_report.json",
    "rollback_procedure_check_report.json",
    "disaster_recovery_check_report.json",
    "production_readiness_gate_report.json",
]

_REQUIRED_CLAIMS_TERMS = [
    "non-claim",
    "production-ready",
    "regulatory",
    "independently reproduced",
    "assurance",
]

_EXPECTED_GATE_IDS = [
    "MONITORING_ALERTING_CHECK",
    "INCIDENT_RESPONSE_CHECK",
    "SECURITY_REVIEW_CHECK",
    "EXTERNAL_REPRODUCTION_CHECK",
    "PRODUCTION_DEPLOYMENT_AUDIT_CHECK",
    "SLO_EVIDENCE_CHECK",
    "ROLLBACK_PROCEDURE_CHECK",
    "DISASTER_RECOVERY_CHECK",
]

_EVIDENCE_GLOB = "governance_signoff_evidence_*.json"


class GovernanceSignoffGate:
    """Final governance sign-off gate (PR 14)."""

    def __init__(
        self,
        governance_approver: str | None = None,
        governance_signoff_date: str | None = None,
    ) -> None:
        self._governance_approver = governance_approver
        self._governance_signoff_date = governance_signoff_date

    @classmethod
    def from_env(cls) -> "GovernanceSignoffGate":
        return cls(
            governance_approver=os.getenv("AEM_GOVERNANCE_APPROVER", "").strip() or None,
            governance_signoff_date=os.getenv("AEM_GOVERNANCE_SIGNOFF_DATE", "").strip() or None,
        )

    # ── C-01: Governance sign-off document ───────────────────────────────────

    def check_signoff_document(self) -> dict[str, Any]:
        if not _GOVERNANCE_SIGNOFF_FILE.exists():
            return {"ok": False, "detail": f"GOVERNANCE_SIGNOFF.md not found at {_GOVERNANCE_SIGNOFF_FILE}"}
        data = _GOVERNANCE_SIGNOFF_FILE.read_bytes()
        size = len(data)
        sha256 = hashlib.sha256(data).hexdigest()
        return {
            "ok": size > 500,
            "file": str(_GOVERNANCE_SIGNOFF_FILE),
            "sha256": sha256,
            "size_bytes": size,
        }

    # ── C-02: Regulatory mapping documents present ────────────────────────────

    def check_regulatory_mappings(self) -> dict[str, Any]:
        missing = [f for f in _REQUIRED_REGULATORY_FILES
                   if not (_REGULATORY_DIR / f).exists()]
        present = [f for f in _REQUIRED_REGULATORY_FILES
                   if (_REGULATORY_DIR / f).exists()]
        return {
            "ok": not missing,
            "regulatory_files_required": len(_REQUIRED_REGULATORY_FILES),
            "regulatory_files_present": len(present),
            "missing_regulatory_files": missing,
        }

    # ── C-03: All v2.0 assurance reports present ──────────────────────────────

    def check_assurance_reports(self) -> dict[str, Any]:
        missing = [r for r in _REQUIRED_ASSURANCE_REPORTS
                   if not (_ASSURANCE_V2_DIR / r).exists()]
        present = [r for r in _REQUIRED_ASSURANCE_REPORTS
                   if (_ASSURANCE_V2_DIR / r).exists()]
        return {
            "ok": not missing,
            "assurance_reports_required": len(_REQUIRED_ASSURANCE_REPORTS),
            "assurance_reports_present": len(present),
            "missing_reports": missing,
        }

    # ── C-04: PR13 production readiness report has gates_evidence_complete ───

    def check_pr13_evidence_complete(self) -> dict[str, Any]:
        if not _PR13_REPORT_FILE.exists():
            return {
                "ok": False,
                "has_pr13_report": False,
                "detail": f"production_readiness_gate_report.json not found at {_PR13_REPORT_FILE}",
            }
        try:
            data = json.loads(_PR13_REPORT_FILE.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "has_pr13_report": True, "detail": f"Invalid JSON: {exc}"}
        gates_evidence_complete = data.get("result", {}).get("gates_evidence_complete", False)
        return {
            "ok": bool(gates_evidence_complete),
            "has_pr13_report": True,
            "gates_evidence_complete": gates_evidence_complete,
        }

    # ── C-05: Claims and non-claims document present ──────────────────────────

    def check_claims_document(self) -> dict[str, Any]:
        if not _CLAIMS_FILE.exists():
            return {"ok": False, "detail": f"CLAIMS_AND_NON_CLAIMS.md not found"}
        content = _CLAIMS_FILE.read_text(encoding="utf-8")
        lower = content.lower()
        missing = [t for t in _REQUIRED_CLAIMS_TERMS if t.lower() not in lower]
        return {
            "ok": not missing,
            "has_claims_doc": True,
            "terms_required": len(_REQUIRED_CLAIMS_TERMS),
            "missing_terms": missing,
        }

    # ── C-06: Sign-off evidence artifact ─────────────────────────────────────

    def check_signoff_evidence(self) -> dict[str, Any]:
        artifacts = sorted(_GOVERNANCE_TOOLS_DIR.glob(_EVIDENCE_GLOB)) if _GOVERNANCE_TOOLS_DIR.exists() else []
        if not artifacts:
            return {
                "ok": False,
                "detail": f"No {_EVIDENCE_GLOB} found in {_GOVERNANCE_TOOLS_DIR}",
            }
        latest = artifacts[-1]
        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "detail": f"Invalid JSON: {exc}"}

        sha256 = hashlib.sha256(latest.read_bytes()).hexdigest()
        summary = data.get("summary", {})
        hashed = summary.get("subjects_hashed", 0)
        total = summary.get("subjects_total", 0)
        has_sha = "artifact_sha256" in data
        return {
            "ok": hashed >= 15 and hashed == total and has_sha,
            "file": str(latest),
            "sha256": sha256,
            "artifact_sha256": data.get("artifact_sha256", ""),
            "subjects_hashed": hashed,
            "subjects_total": total,
            "has_artifact_sha256": has_sha,
        }

    # ── C-07: All 8 gate IDs verified in PR13 aggregate report ───────────────

    def check_gate_ids_verified(self) -> dict[str, Any]:
        if not _PR13_REPORT_FILE.exists():
            return {"ok": False, "detail": "production_readiness_gate_report.json not found"}
        try:
            data = json.loads(_PR13_REPORT_FILE.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "detail": f"Invalid JSON: {exc}"}

        gate_summary = data.get("result", {}).get("gate_summary", {})
        found_ids = {g.get("gate") for g in gate_summary.values() if g.get("gate")}
        missing = [gid for gid in _EXPECTED_GATE_IDS if gid not in found_ids]
        return {
            "ok": not missing,
            "gates_required": len(_EXPECTED_GATE_IDS),
            "gates_verified": len(_EXPECTED_GATE_IDS) - len(missing),
            "missing_gate_ids": missing,
        }

    # ── C-08: Artifact fingerprint recorded ──────────────────────────────────

    def check_artifact_fingerprint(self) -> dict[str, Any]:
        artifacts = sorted(_GOVERNANCE_TOOLS_DIR.glob(_EVIDENCE_GLOB)) if _GOVERNANCE_TOOLS_DIR.exists() else []
        if not artifacts:
            return {"ok": False, "detail": "No governance_signoff_evidence_*.json found"}
        try:
            data = json.loads(artifacts[-1].read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "detail": f"Invalid JSON: {exc}"}
        artifact_sha = data.get("artifact_sha256", "")
        return {
            "ok": bool(artifact_sha) and len(artifact_sha) == 64,
            "has_artifact_sha256": bool(artifact_sha),
            "artifact_sha256": artifact_sha,
        }

    # ── C-09: Governance approver identity ────────────────────────────────────

    def check_governance_approver(self) -> dict[str, Any]:
        if not self._governance_approver:
            return {
                "ok": False,
                "skipped": True,
                "reason": (
                    "AEM_GOVERNANCE_APPROVER not set — set to governance lead identity "
                    "before claiming governance_signed_off=true"
                ),
            }
        return {"ok": True, "governance_approver": self._governance_approver}

    # ── C-10: Governance sign-off date ────────────────────────────────────────

    def check_governance_signoff_date(self) -> dict[str, Any]:
        if not self._governance_signoff_date:
            return {
                "ok": False,
                "skipped": True,
                "reason": (
                    "AEM_GOVERNANCE_SIGNOFF_DATE not set — set to ISO8601 date of "
                    "governance sign-off before claiming governance_signed_off=true"
                ),
            }
        return {"ok": True, "governance_signoff_date": self._governance_signoff_date}

    # ── Full gate ─────────────────────────────────────────────────────────────

    def gate_check(self) -> dict[str, Any]:
        c01 = self.check_signoff_document()
        c02 = self.check_regulatory_mappings()
        c03 = self.check_assurance_reports()
        c04 = self.check_pr13_evidence_complete()
        c05 = self.check_claims_document()
        c06 = self.check_signoff_evidence()
        c07 = self.check_gate_ids_verified()
        c08 = self.check_artifact_fingerprint()
        c09 = self.check_governance_approver()
        c10 = self.check_governance_signoff_date()

        checks = {
            "C-01_signoff_document":         c01,
            "C-02_regulatory_mappings":      c02,
            "C-03_assurance_reports":        c03,
            "C-04_pr13_evidence_complete":   c04,
            "C-05_claims_document":          c05,
            "C-06_signoff_evidence":         c06,
            "C-07_gate_ids_verified":        c07,
            "C-08_artifact_fingerprint":     c08,
            "C-09_governance_approver":      c09,
            "C-10_governance_signoff_date":  c10,
        }

        passed = sum(1 for v in checks.values() if v.get("ok"))
        failed = len(checks) - passed
        status = "PASS" if failed == 0 else "FAIL"

        governance_signed_off = (
            self._governance_approver is not None
            and self._governance_signoff_date is not None
        )

        fail_reason = None
        if status == "FAIL":
            missing_live = []
            if not self._governance_approver:
                missing_live.append("AEM_GOVERNANCE_APPROVER")
            if not self._governance_signoff_date:
                missing_live.append("AEM_GOVERNANCE_SIGNOFF_DATE")
            if missing_live:
                fail_reason = (
                    f"Governance sign-off not yet completed: "
                    f"{', '.join(missing_live)} not set. governance_signed_off=false"
                )
            else:
                failing = [k for k, v in checks.items() if not v.get("ok")]
                fail_reason = f"Failing checks: {', '.join(failing)}"

        return {
            "gate": "GOVERNANCE_SIGNOFF_CHECK",
            "status": status,
            "checks_passed": passed,
            "checks_failed": failed,
            "governance_signed_off": governance_signed_off,
            "governance_approver": self._governance_approver,
            "governance_signoff_date": self._governance_signoff_date,
            "fail_reason": fail_reason,
            "checks": checks,
        }
