"""
AEM-EVOLVE™ v2.0 PR 10 — SLO Evidence Gate.

C-01–C-08 pass on file presence and content inspection (no live infra needed).
C-09 requires AEM_SLO_REVIEWER env var (external SLO reviewer identity).
C-10 requires AEM_SLO_REVIEW_DATE env var (ISO8601 date of SLO review).

Non-claims:
  This gate verifies that SLO evidence artifacts exist and are structurally
  complete. It does NOT claim SLOs are being measured in production.
  slo_evidence_verified is always False until C-09 and C-10 are both set.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

_DEMO_ROOT = Path(__file__).resolve().parents[1]
_DOCS_DIR = _DEMO_ROOT / "docs"
_SLO_TOOLS_DIR = _DEMO_ROOT / "tools" / "slo"

_SLO_FILE = _DOCS_DIR / "SLO.md"
_ALERT_RULES_FILE = _DEMO_ROOT / "monitoring" / "alert_rules.yaml"
_SLO_EVIDENCE_GLOB = "slo_evidence_*.json"

_REQUIRED_SLO_DIMENSIONS = [
    "availability",
    "latency_p99",
    "error_rate",
    "governance_gate_pass_rate",
]

_REQUIRED_BUDGET_FIELDS = [
    "error budget",
    "burn rate",
    "budget",
]

_REQUIRED_GATES = [
    "PR1", "PR2", "PR3", "PR4", "PR5", "PR6", "PR7", "PR8", "PR9",
]

_REQUIRED_METHODOLOGY_TERMS = [
    "measurement",
    "counter",
    "prometheus",
    "scrape",
]

_REQUIRED_BURN_RATE_TERMS = [
    "fast burn",
    "slow burn",
    "burn rate",
    "budget",
]


class SLOGate:
    """Gate verifier for SLO evidence (PR 10)."""

    def __init__(
        self,
        slo_reviewer: str | None = None,
        slo_review_date: str | None = None,
    ) -> None:
        self._slo_reviewer = slo_reviewer
        self._slo_review_date = slo_review_date

    @classmethod
    def from_env(cls) -> "SLOGate":
        return cls(
            slo_reviewer=os.getenv("AEM_SLO_REVIEWER", "").strip() or None,
            slo_review_date=os.getenv("AEM_SLO_REVIEW_DATE", "").strip() or None,
        )

    # ── C-01: SLO document exists ─────────────────────────────────────────────

    def check_slo_document(self) -> dict[str, Any]:
        if not _SLO_FILE.exists():
            return {"ok": False, "detail": f"SLO.md not found at {_SLO_FILE}"}
        content = _SLO_FILE.read_text(encoding="utf-8")
        sha256 = hashlib.sha256(content.encode()).hexdigest()
        return {
            "ok": True,
            "file": str(_SLO_FILE),
            "sha256": sha256,
            "size_bytes": len(content.encode()),
        }

    # ── C-02: SLO targets cover all 4 required dimensions ────────────────────

    def check_slo_targets(self) -> dict[str, Any]:
        if not _SLO_FILE.exists():
            return {"ok": False, "detail": "SLO.md missing"}
        content = _SLO_FILE.read_text(encoding="utf-8")
        missing = [d for d in _REQUIRED_SLO_DIMENSIONS if d not in content]
        return {
            "ok": not missing,
            "dimensions_required": len(_REQUIRED_SLO_DIMENSIONS),
            "dimensions_present": len(_REQUIRED_SLO_DIMENSIONS) - len(missing),
            "missing_dimensions": missing,
        }

    # ── C-03: Error budget calculations documented ────────────────────────────

    def check_error_budgets(self) -> dict[str, Any]:
        if not _SLO_FILE.exists():
            return {"ok": False, "detail": "SLO.md missing"}
        content = _SLO_FILE.read_text(encoding="utf-8")
        lower = content.lower()
        missing = [f for f in _REQUIRED_BUDGET_FIELDS if f.lower() not in lower]
        has_budget_table = "error budget" in lower
        has_burn_threshold = "burn rate" in lower
        return {
            "ok": not missing and has_budget_table and has_burn_threshold,
            "has_budget_table": has_budget_table,
            "has_burn_threshold": has_burn_threshold,
            "missing_fields": missing,
        }

    # ── C-04: Burn rate alert rules documented ────────────────────────────────

    def check_burn_rate_alerts(self) -> dict[str, Any]:
        if not _SLO_FILE.exists():
            return {"ok": False, "detail": "SLO.md missing"}
        content = _SLO_FILE.read_text(encoding="utf-8")
        lower = content.lower()
        missing = [t for t in _REQUIRED_BURN_RATE_TERMS if t.lower() not in lower]
        has_fast_burn = "fast burn" in lower or "fastburn" in lower
        has_slow_burn = "slow burn" in lower or "slowburn" in lower
        return {
            "ok": not missing and has_fast_burn and has_slow_burn,
            "has_fast_burn": has_fast_burn,
            "has_slow_burn": has_slow_burn,
            "missing_terms": missing,
        }

    # ── C-05: Measurement methodology documented ──────────────────────────────

    def check_measurement_methodology(self) -> dict[str, Any]:
        if not _SLO_FILE.exists():
            return {"ok": False, "detail": "SLO.md missing"}
        content = _SLO_FILE.read_text(encoding="utf-8")
        lower = content.lower()
        missing = [t for t in _REQUIRED_METHODOLOGY_TERMS if t.lower() not in lower]
        has_methodology = "measurement methodology" in lower
        has_counter_mapping = "counter" in lower and "slo" in lower
        return {
            "ok": not missing and has_methodology and has_counter_mapping,
            "has_methodology_section": has_methodology,
            "has_counter_mapping": has_counter_mapping,
            "missing_terms": missing,
        }

    # ── C-06: Governance gate SLO coverage (PR1–PR9) ─────────────────────────

    def check_governance_gate_coverage(self) -> dict[str, Any]:
        if not _SLO_FILE.exists():
            return {"ok": False, "detail": "SLO.md missing"}
        content = _SLO_FILE.read_text(encoding="utf-8")
        missing = [g for g in _REQUIRED_GATES if g not in content]
        return {
            "ok": not missing,
            "gates_required": len(_REQUIRED_GATES),
            "gates_covered": len(_REQUIRED_GATES) - len(missing),
            "missing_gates": missing,
        }

    # ── C-07: SLO evidence artifact with SHA256 checksums ────────────────────

    def check_slo_evidence_artifact(self) -> dict[str, Any]:
        artifacts = sorted(_SLO_TOOLS_DIR.glob(_SLO_EVIDENCE_GLOB)) if _SLO_TOOLS_DIR.exists() else []
        if not artifacts:
            return {
                "ok": False,
                "detail": (
                    f"No slo_evidence_*.json found in {_SLO_TOOLS_DIR}. "
                    "Run: python tools/production_readiness/verify_slo_evidence.py --generate"
                ),
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
        gate_coverage = data.get("gate_coverage", "")
        return {
            "ok": hashed >= 15 and hashed == total and has_sha,
            "file": str(latest),
            "sha256": sha256,
            "artifact_sha256": data.get("artifact_sha256", ""),
            "subjects_hashed": hashed,
            "subjects_total": total,
            "has_artifact_sha256": has_sha,
            "gate_coverage": gate_coverage,
        }

    # ── C-08: Artifact fingerprint recorded ──────────────────────────────────

    def check_artifact_fingerprint(self) -> dict[str, Any]:
        artifacts = sorted(_SLO_TOOLS_DIR.glob(_SLO_EVIDENCE_GLOB)) if _SLO_TOOLS_DIR.exists() else []
        if not artifacts:
            return {"ok": False, "detail": f"No slo_evidence_*.json found in {_SLO_TOOLS_DIR}"}
        latest = artifacts[-1]
        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "detail": f"Invalid JSON: {exc}"}

        artifact_sha = data.get("artifact_sha256", "")
        return {
            "ok": bool(artifact_sha) and len(artifact_sha) == 64,
            "has_artifact_sha256": bool(artifact_sha),
            "artifact_sha256": artifact_sha,
        }

    # ── C-09: SLO reviewer identity set ──────────────────────────────────────

    def check_slo_reviewer(self) -> dict[str, Any]:
        if not self._slo_reviewer:
            return {
                "ok": False,
                "skipped": True,
                "reason": (
                    "AEM_SLO_REVIEWER not set — set to external SLO reviewer identity "
                    "before claiming SLO evidence verified"
                ),
            }
        return {"ok": True, "slo_reviewer": self._slo_reviewer}

    # ── C-10: SLO review date set ─────────────────────────────────────────────

    def check_slo_review_date(self) -> dict[str, Any]:
        if not self._slo_review_date:
            return {
                "ok": False,
                "skipped": True,
                "reason": "AEM_SLO_REVIEW_DATE not set — set to ISO8601 date of SLO review",
            }
        return {"ok": True, "slo_review_date": self._slo_review_date}

    # ── Full gate ─────────────────────────────────────────────────────────────

    def gate_check(self) -> dict[str, Any]:
        c01 = self.check_slo_document()
        c02 = self.check_slo_targets()
        c03 = self.check_error_budgets()
        c04 = self.check_burn_rate_alerts()
        c05 = self.check_measurement_methodology()
        c06 = self.check_governance_gate_coverage()
        c07 = self.check_slo_evidence_artifact()
        c08 = self.check_artifact_fingerprint()
        c09 = self.check_slo_reviewer()
        c10 = self.check_slo_review_date()

        checks = {
            "C-01_slo_document": c01,
            "C-02_slo_targets": c02,
            "C-03_error_budgets": c03,
            "C-04_burn_rate_alerts": c04,
            "C-05_measurement_methodology": c05,
            "C-06_governance_gate_coverage": c06,
            "C-07_slo_evidence_artifact": c07,
            "C-08_artifact_fingerprint": c08,
            "C-09_slo_reviewer": c09,
            "C-10_slo_review_date": c10,
        }

        passed = sum(1 for v in checks.values() if v.get("ok"))
        failed = len(checks) - passed
        status = "PASS" if failed == 0 else "FAIL"

        fail_reason = None
        if status == "FAIL":
            missing_live = []
            if not self._slo_reviewer:
                missing_live.append("AEM_SLO_REVIEWER")
            if not self._slo_review_date:
                missing_live.append("AEM_SLO_REVIEW_DATE")
            if missing_live:
                fail_reason = (
                    f"SLO evidence not yet reviewed: "
                    f"{', '.join(missing_live)} not set. slo_evidence_verified=false"
                )
            else:
                failing = [k for k, v in checks.items() if not v.get("ok")]
                fail_reason = f"Failing checks: {', '.join(failing)}"

        return {
            "gate": "SLO_EVIDENCE_CHECK",
            "status": status,
            "checks_passed": passed,
            "checks_failed": failed,
            "slo_evidence_verified": (
                self._slo_reviewer is not None
                and self._slo_review_date is not None
            ),
            "slo_reviewer": self._slo_reviewer,
            "slo_review_date": self._slo_review_date,
            "fail_reason": fail_reason,
            "checks": checks,
        }
