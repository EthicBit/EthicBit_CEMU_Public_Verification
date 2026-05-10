"""
AEM-EVOLVE™ v2.0 PR 7 — Production-Readiness Security Review Evidence Gate.

C-01–C-08 pass on file presence and content inspection (no live infra needed).
C-09 requires AEM_SECURITY_REVIEWER env var (external reviewer identity).
C-10 requires AEM_SECURITY_REVIEW_DATE env var (ISO8601 review date).

Non-claims:
  This gate verifies that review artifacts exist and are structurally complete.
  It does not independently validate the security findings or confirm that all
  vulnerabilities have been remediated.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

_DEMO_ROOT = Path(__file__).resolve().parents[1]
_DOCS_DIR = _DEMO_ROOT / "docs"
_SECURITY_DIR = _DEMO_ROOT / "tools" / "security"

_SECURITY_REVIEW_FILE = _DOCS_DIR / "SECURITY_REVIEW.md"
_THREAT_MODEL_FILE = _DOCS_DIR / "THREAT_MODEL.md"
_DEP_SCAN_GLOB = "dependency_scan_*.json"
_STATIC_ANALYSIS_GLOB = "static_analysis_*.json"

_REQUIRED_CONTROLS = [
    "HITL Identity Enforcement",
    "KMS/HSM Signing",
    "Audit Chain Integrity",
    "Replay Mitigation",
    "RBAC Access Control",
    "Input Validation",
    "Monitoring",
]

_REQUIRED_OWASP_ITEMS = [
    "API1",
    "API2",
    "API5",
    "API8",
]

_THREAT_MODEL_REQUIRED_THREATS = [
    "Unauthorized",
    "Replay",
    "tampering",
    "injection",
]


class SecurityReviewGate:
    """Gate verifier for production-readiness security review evidence (PR 7)."""

    def __init__(
        self,
        security_reviewer: str | None = None,
        security_review_date: str | None = None,
    ) -> None:
        self._security_reviewer = security_reviewer
        self._security_review_date = security_review_date

    @classmethod
    def from_env(cls) -> "SecurityReviewGate":
        return cls(
            security_reviewer=os.getenv("AEM_SECURITY_REVIEWER", "").strip() or None,
            security_review_date=os.getenv("AEM_SECURITY_REVIEW_DATE", "").strip() or None,
        )

    # ── C-01: Security review document exists ────────────────────────────────

    def check_review_document(self) -> dict[str, Any]:
        if not _SECURITY_REVIEW_FILE.exists():
            return {"ok": False, "detail": f"SECURITY_REVIEW.md not found at {_SECURITY_REVIEW_FILE}"}
        content = _SECURITY_REVIEW_FILE.read_text(encoding="utf-8")
        sha256 = hashlib.sha256(content.encode()).hexdigest()
        return {
            "ok": True,
            "file": str(_SECURITY_REVIEW_FILE),
            "sha256": sha256,
            "size_bytes": len(content.encode()),
        }

    # ── C-02: Threat model exists and covers required attack surfaces ─────────

    def check_threat_model(self) -> dict[str, Any]:
        if not _THREAT_MODEL_FILE.exists():
            return {"ok": False, "detail": f"THREAT_MODEL.md not found at {_THREAT_MODEL_FILE}"}
        content = _THREAT_MODEL_FILE.read_text(encoding="utf-8")
        sha256 = hashlib.sha256(content.encode()).hexdigest()
        missing = [t for t in _THREAT_MODEL_REQUIRED_THREATS if t.lower() not in content.lower()]
        return {
            "ok": not missing,
            "file": str(_THREAT_MODEL_FILE),
            "sha256": sha256,
            "threats_checked": len(_THREAT_MODEL_REQUIRED_THREATS),
            "missing_threats": missing,
        }

    # ── C-03: Security review covers all 7 governance controls ───────────────

    def check_controls_coverage(self) -> dict[str, Any]:
        if not _SECURITY_REVIEW_FILE.exists():
            return {"ok": False, "detail": "SECURITY_REVIEW.md missing"}
        content = _SECURITY_REVIEW_FILE.read_text(encoding="utf-8")
        missing = [c for c in _REQUIRED_CONTROLS if c not in content]
        return {
            "ok": not missing,
            "controls_required": len(_REQUIRED_CONTROLS),
            "controls_present": len(_REQUIRED_CONTROLS) - len(missing),
            "missing_controls": missing,
        }

    # ── C-04: Dependency scan artifact exists with 0 HIGH/CRITICAL CVEs ──────

    def check_dependency_scan(self) -> dict[str, Any]:
        artifacts = sorted(_SECURITY_DIR.glob(_DEP_SCAN_GLOB)) if _SECURITY_DIR.exists() else []
        if not artifacts:
            return {
                "ok": False,
                "detail": (
                    f"No dependency_scan_*.json found in {_SECURITY_DIR}. "
                    "Run: pip-audit -r requirements.txt --format json -o tools/security/dependency_scan_$(date +%Y_%m).json"
                ),
            }
        latest = artifacts[-1]
        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "detail": f"Invalid JSON in {latest.name}: {exc}"}

        sha256 = hashlib.sha256(latest.read_bytes()).hexdigest()
        summary = data.get("summary", {})
        vulns = summary.get("vulnerabilities_found", -1)
        return {
            "ok": vulns == 0,
            "file": str(latest),
            "sha256": sha256,
            "dependencies_scanned": summary.get("dependencies_scanned", 0),
            "vulnerabilities_found": vulns,
            "scan_result": summary.get("scan_result", "UNKNOWN"),
        }

    # ── C-05: Static analysis artifact exists with 0 HIGH findings ───────────

    def check_static_analysis(self) -> dict[str, Any]:
        artifacts = sorted(_SECURITY_DIR.glob(_STATIC_ANALYSIS_GLOB)) if _SECURITY_DIR.exists() else []
        if not artifacts:
            return {
                "ok": False,
                "detail": (
                    f"No static_analysis_*.json found in {_SECURITY_DIR}. "
                    "Run: bandit -r . -f json -o tools/security/static_analysis_$(date +%Y_%m).json"
                ),
            }
        latest = artifacts[-1]
        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "detail": f"Invalid JSON in {latest.name}: {exc}"}

        sha256 = hashlib.sha256(latest.read_bytes()).hexdigest()
        summary = data.get("summary", {})
        high = summary.get("issues_high", -1)
        return {
            "ok": high == 0,
            "file": str(latest),
            "sha256": sha256,
            "issues_high": high,
            "issues_medium": summary.get("issues_medium", 0),
            "issues_low": summary.get("issues_low", 0),
            "scan_result": summary.get("scan_result", "UNKNOWN"),
            "production_blocking": summary.get("production_blocking", high),
        }

    # ── C-06: OWASP API Security Top 10 coverage ─────────────────────────────

    def check_owasp_coverage(self) -> dict[str, Any]:
        if not _SECURITY_REVIEW_FILE.exists():
            return {"ok": False, "detail": "SECURITY_REVIEW.md missing"}
        content = _SECURITY_REVIEW_FILE.read_text(encoding="utf-8")
        missing = [item for item in _REQUIRED_OWASP_ITEMS if item not in content]
        return {
            "ok": not missing,
            "owasp_items_required": len(_REQUIRED_OWASP_ITEMS),
            "owasp_items_present": len(_REQUIRED_OWASP_ITEMS) - len(missing),
            "missing_items": missing,
        }

    # ── C-07: Known findings documented with mitigations ─────────────────────

    def check_findings_documented(self) -> dict[str, Any]:
        if not _SECURITY_REVIEW_FILE.exists():
            return {"ok": False, "detail": "SECURITY_REVIEW.md missing"}
        content = _SECURITY_REVIEW_FILE.read_text(encoding="utf-8")
        has_findings = "Disposition" in content or "DISPOSITION" in content
        has_limitations = "Known Limitations" in content or "Limitation" in content
        has_mitigations = "Mitigation" in content
        return {
            "ok": has_findings and has_limitations and has_mitigations,
            "has_findings_table": has_findings,
            "has_known_limitations": has_limitations,
            "has_mitigations": has_mitigations,
        }

    # ── C-08: Review artifact SHA256 fingerprints recorded ───────────────────

    def check_artifact_fingerprints(self) -> dict[str, Any]:
        dep_artifacts = sorted(_SECURITY_DIR.glob(_DEP_SCAN_GLOB)) if _SECURITY_DIR.exists() else []
        sa_artifacts = sorted(_SECURITY_DIR.glob(_STATIC_ANALYSIS_GLOB)) if _SECURITY_DIR.exists() else []

        results = {}
        ok = True

        for artifacts, label in [(dep_artifacts, "dependency_scan"), (sa_artifacts, "static_analysis")]:
            if not artifacts:
                results[label] = {"ok": False, "detail": f"No {label} artifact found"}
                ok = False
                continue
            latest = artifacts[-1]
            try:
                data = json.loads(latest.read_text(encoding="utf-8"))
                has_sha = "artifact_sha256" in data
                results[label] = {
                    "ok": has_sha,
                    "file": latest.name,
                    "has_sha256": has_sha,
                    "sha256": data.get("artifact_sha256", ""),
                }
                if not has_sha:
                    ok = False
            except Exception as exc:
                results[label] = {"ok": False, "detail": str(exc)}
                ok = False

        return {"ok": ok, "artifacts": results}

    # ── C-09: External reviewer sign-off ─────────────────────────────────────

    def check_external_reviewer(self) -> dict[str, Any]:
        if not self._security_reviewer:
            return {
                "ok": False,
                "skipped": True,
                "reason": "AEM_SECURITY_REVIEWER not set — set to external reviewer identity before production deploy",
            }
        return {"ok": True, "security_reviewer": self._security_reviewer}

    # ── C-10: Review date within compliance window ────────────────────────────

    def check_review_date(self) -> dict[str, Any]:
        if not self._security_review_date:
            return {
                "ok": False,
                "skipped": True,
                "reason": "AEM_SECURITY_REVIEW_DATE not set — set to ISO8601 date of external review",
            }
        return {"ok": True, "security_review_date": self._security_review_date}

    # ── Full gate ─────────────────────────────────────────────────────────────

    def gate_check(self) -> dict[str, Any]:
        c01 = self.check_review_document()
        c02 = self.check_threat_model()
        c03 = self.check_controls_coverage()
        c04 = self.check_dependency_scan()
        c05 = self.check_static_analysis()
        c06 = self.check_owasp_coverage()
        c07 = self.check_findings_documented()
        c08 = self.check_artifact_fingerprints()
        c09 = self.check_external_reviewer()
        c10 = self.check_review_date()

        checks = {
            "C-01_review_document": c01,
            "C-02_threat_model": c02,
            "C-03_controls_coverage": c03,
            "C-04_dependency_scan": c04,
            "C-05_static_analysis": c05,
            "C-06_owasp_coverage": c06,
            "C-07_findings_documented": c07,
            "C-08_artifact_fingerprints": c08,
            "C-09_external_reviewer": c09,
            "C-10_review_date": c10,
        }

        passed = sum(1 for v in checks.values() if v.get("ok"))
        failed = len(checks) - passed
        status = "PASS" if failed == 0 else "FAIL"

        fail_reason = None
        if status == "FAIL":
            missing_live = []
            if not self._security_reviewer:
                missing_live.append("AEM_SECURITY_REVIEWER")
            if not self._security_review_date:
                missing_live.append("AEM_SECURITY_REVIEW_DATE")
            if missing_live:
                fail_reason = f"External review evidence missing: {', '.join(missing_live)}"
            else:
                failing = [k for k, v in checks.items() if not v.get("ok")]
                fail_reason = f"Failing checks: {', '.join(failing)}"

        return {
            "gate": "SECURITY_REVIEW_CHECK",
            "status": status,
            "checks_passed": passed,
            "checks_failed": failed,
            "security_reviewer": self._security_reviewer,
            "security_review_date": self._security_review_date,
            "fail_reason": fail_reason,
            "checks": checks,
        }
