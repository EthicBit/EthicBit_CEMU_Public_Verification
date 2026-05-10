"""
AEM-EVOLVE™ v2.0 PR 12 — Disaster Recovery Evidence Gate.

C-01–C-08 pass on file presence and content inspection (no live infra needed).
C-09 requires AEM_DR_TESTER env var (identity of person who ran DR dry-run).
C-10 requires AEM_DR_TEST_DATE env var (ISO8601 date of DR test).

Non-claims:
  This gate verifies that DR evidence artifacts exist and are structurally
  complete. It does NOT claim a production DR exercise has been executed.
  dr_tested is always False until C-09 and C-10 are both set.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

_DEMO_ROOT = Path(__file__).resolve().parents[1]
_DOCS_DIR = _DEMO_ROOT / "docs"
_DR_TOOLS_DIR = _DEMO_ROOT / "tools" / "disaster_recovery"

_DR_PLAN_FILE = _DOCS_DIR / "DISASTER_RECOVERY.md"
_EVIDENCE_GLOB = "dr_test_evidence_*.json"

_REQUIRED_RTO_RPO_FIELDS = [
    "rto_minutes",
    "rpo_minutes",
    "RTO",
    "RPO",
]

_REQUIRED_BACKUP_FIELDS = [
    "backup_frequency",
    "retention_period",
    "backup",
]

_REQUIRED_DR_SCENARIOS = [
    "dr_scenario_data_loss",
    "dr_scenario_region_failure",
    "dr_scenario_key_compromise",
    "dr_scenario_service_outage",
    "dr_scenario_audit_chain_corruption",
]

_REQUIRED_RECOVERY_PROCEDURE_TERMS = [
    "restore",
    "failover",
    "rotation",
    "restart",
    "chain",
]


class DisasterRecoveryGate:
    """Gate verifier for disaster recovery evidence (PR 12)."""

    def __init__(
        self,
        dr_tester: str | None = None,
        dr_test_date: str | None = None,
    ) -> None:
        self._dr_tester = dr_tester
        self._dr_test_date = dr_test_date

    @classmethod
    def from_env(cls) -> "DisasterRecoveryGate":
        return cls(
            dr_tester=os.getenv("AEM_DR_TESTER", "").strip() or None,
            dr_test_date=os.getenv("AEM_DR_TEST_DATE", "").strip() or None,
        )

    # ── C-01: DR plan document exists ─────────────────────────────────────────

    def check_dr_plan(self) -> dict[str, Any]:
        if not _DR_PLAN_FILE.exists():
            return {"ok": False, "detail": f"DISASTER_RECOVERY.md not found at {_DR_PLAN_FILE}"}
        content = _DR_PLAN_FILE.read_text(encoding="utf-8")
        sha256 = hashlib.sha256(content.encode()).hexdigest()
        return {
            "ok": True,
            "file": str(_DR_PLAN_FILE),
            "sha256": sha256,
            "size_bytes": len(content.encode()),
        }

    # ── C-02: RTO / RPO targets defined ──────────────────────────────────────

    def check_rto_rpo(self) -> dict[str, Any]:
        if not _DR_PLAN_FILE.exists():
            return {"ok": False, "detail": "DISASTER_RECOVERY.md missing"}
        content = _DR_PLAN_FILE.read_text(encoding="utf-8")
        missing = [f for f in _REQUIRED_RTO_RPO_FIELDS if f not in content]
        has_rto = "rto_minutes" in content or "RTO" in content
        has_rpo = "rpo_minutes" in content or "RPO" in content
        return {
            "ok": not missing and has_rto and has_rpo,
            "has_rto": has_rto,
            "has_rpo": has_rpo,
            "missing_fields": missing,
        }

    # ── C-03: Backup strategy documented ─────────────────────────────────────

    def check_backup_strategy(self) -> dict[str, Any]:
        if not _DR_PLAN_FILE.exists():
            return {"ok": False, "detail": "DISASTER_RECOVERY.md missing"}
        content = _DR_PLAN_FILE.read_text(encoding="utf-8")
        lower = content.lower()
        missing = [f for f in _REQUIRED_BACKUP_FIELDS if f.lower() not in lower]
        has_backup_section = "backup" in lower
        has_retention = "retention" in lower
        return {
            "ok": not missing and has_backup_section and has_retention,
            "has_backup_section": has_backup_section,
            "has_retention": has_retention,
            "missing_fields": missing,
        }

    # ── C-04: Five DR scenarios documented ───────────────────────────────────

    def check_dr_scenarios(self) -> dict[str, Any]:
        artifacts = sorted(_DR_TOOLS_DIR.glob(_EVIDENCE_GLOB)) if _DR_TOOLS_DIR.exists() else []
        if not artifacts:
            return {"ok": False, "detail": f"No dr_test_evidence_*.json found in {_DR_TOOLS_DIR}"}
        try:
            data = json.loads(artifacts[-1].read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "detail": f"Invalid JSON: {exc}"}

        scenario_ids = {s["scenario_id"] for s in data.get("scenarios", [])}
        missing = [s for s in _REQUIRED_DR_SCENARIOS if s not in scenario_ids]
        return {
            "ok": not missing,
            "scenarios_required": len(_REQUIRED_DR_SCENARIOS),
            "scenarios_documented": len(_REQUIRED_DR_SCENARIOS) - len(missing),
            "missing_scenarios": missing,
        }

    # ── C-05: Recovery procedures documented ─────────────────────────────────

    def check_recovery_procedures(self) -> dict[str, Any]:
        if not _DR_PLAN_FILE.exists():
            return {"ok": False, "detail": "DISASTER_RECOVERY.md missing"}
        content = _DR_PLAN_FILE.read_text(encoding="utf-8")
        lower = content.lower()
        missing = [t for t in _REQUIRED_RECOVERY_PROCEDURE_TERMS if t.lower() not in lower]
        return {
            "ok": not missing,
            "terms_required": len(_REQUIRED_RECOVERY_PROCEDURE_TERMS),
            "terms_present": len(_REQUIRED_RECOVERY_PROCEDURE_TERMS) - len(missing),
            "missing_terms": missing,
        }

    # ── C-06: DR test evidence artifact with SHA256 ───────────────────────────

    def check_dr_evidence(self) -> dict[str, Any]:
        artifacts = sorted(_DR_TOOLS_DIR.glob(_EVIDENCE_GLOB)) if _DR_TOOLS_DIR.exists() else []
        if not artifacts:
            return {
                "ok": False,
                "detail": (
                    f"No dr_test_evidence_*.json found in {_DR_TOOLS_DIR}. "
                    "Run: python tools/production_readiness/verify_disaster_recovery.py --generate"
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
        scenarios_tested = data.get("dr_scenarios_tested", 0)
        scenarios_passed = data.get("dr_scenarios_passed", 0)

        return {
            "ok": hashed >= 15 and hashed == total and has_sha and scenarios_tested >= 5,
            "file": str(latest),
            "sha256": sha256,
            "artifact_sha256": data.get("artifact_sha256", ""),
            "subjects_hashed": hashed,
            "subjects_total": total,
            "has_artifact_sha256": has_sha,
            "dr_scenarios_tested": scenarios_tested,
            "dr_scenarios_passed": scenarios_passed,
            "rto_target_minutes": data.get("rto_target_minutes"),
            "rpo_target_minutes": data.get("rpo_target_minutes"),
        }

    # ── C-07: All 5 DR scenarios passed ──────────────────────────────────────

    def check_scenarios_passed(self) -> dict[str, Any]:
        artifacts = sorted(_DR_TOOLS_DIR.glob(_EVIDENCE_GLOB)) if _DR_TOOLS_DIR.exists() else []
        if not artifacts:
            return {"ok": False, "detail": f"No dr_test_evidence_*.json found"}
        try:
            data = json.loads(artifacts[-1].read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "detail": f"Invalid JSON: {exc}"}

        scenarios = data.get("scenarios", [])
        failed = [s["scenario_id"] for s in scenarios if s.get("status") != "PASS"]
        return {
            "ok": not failed and len(scenarios) >= 5,
            "scenarios_total": len(scenarios),
            "scenarios_passed": sum(1 for s in scenarios if s.get("status") == "PASS"),
            "failed_scenarios": failed,
        }

    # ── C-08: Artifact fingerprint recorded ──────────────────────────────────

    def check_artifact_fingerprint(self) -> dict[str, Any]:
        artifacts = sorted(_DR_TOOLS_DIR.glob(_EVIDENCE_GLOB)) if _DR_TOOLS_DIR.exists() else []
        if not artifacts:
            return {"ok": False, "detail": f"No dr_test_evidence_*.json found"}
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

    # ── C-09: DR tester identity ──────────────────────────────────────────────

    def check_dr_tester(self) -> dict[str, Any]:
        if not self._dr_tester:
            return {
                "ok": False,
                "skipped": True,
                "reason": (
                    "AEM_DR_TESTER not set — set to identity of person who executed "
                    "the DR dry-run test before claiming dr_tested=true"
                ),
            }
        return {"ok": True, "dr_tester": self._dr_tester}

    # ── C-10: DR test date ────────────────────────────────────────────────────

    def check_dr_test_date(self) -> dict[str, Any]:
        if not self._dr_test_date:
            return {
                "ok": False,
                "skipped": True,
                "reason": "AEM_DR_TEST_DATE not set — set to ISO8601 date of DR dry-run test",
            }
        return {"ok": True, "dr_test_date": self._dr_test_date}

    # ── Full gate ─────────────────────────────────────────────────────────────

    def gate_check(self) -> dict[str, Any]:
        c01 = self.check_dr_plan()
        c02 = self.check_rto_rpo()
        c03 = self.check_backup_strategy()
        c04 = self.check_dr_scenarios()
        c05 = self.check_recovery_procedures()
        c06 = self.check_dr_evidence()
        c07 = self.check_scenarios_passed()
        c08 = self.check_artifact_fingerprint()
        c09 = self.check_dr_tester()
        c10 = self.check_dr_test_date()

        checks = {
            "C-01_dr_plan": c01,
            "C-02_rto_rpo": c02,
            "C-03_backup_strategy": c03,
            "C-04_dr_scenarios": c04,
            "C-05_recovery_procedures": c05,
            "C-06_dr_evidence": c06,
            "C-07_scenarios_passed": c07,
            "C-08_artifact_fingerprint": c08,
            "C-09_dr_tester": c09,
            "C-10_dr_test_date": c10,
        }

        passed = sum(1 for v in checks.values() if v.get("ok"))
        failed = len(checks) - passed
        status = "PASS" if failed == 0 else "FAIL"

        fail_reason = None
        if status == "FAIL":
            missing_live = []
            if not self._dr_tester:
                missing_live.append("AEM_DR_TESTER")
            if not self._dr_test_date:
                missing_live.append("AEM_DR_TEST_DATE")
            if missing_live:
                fail_reason = (
                    f"DR procedure not yet dry-run tested: "
                    f"{', '.join(missing_live)} not set. dr_tested=false"
                )
            else:
                failing = [k for k, v in checks.items() if not v.get("ok")]
                fail_reason = f"Failing checks: {', '.join(failing)}"

        return {
            "gate": "DISASTER_RECOVERY_CHECK",
            "status": status,
            "checks_passed": passed,
            "checks_failed": failed,
            "dr_tested": (
                self._dr_tester is not None
                and self._dr_test_date is not None
            ),
            "dr_tester": self._dr_tester,
            "dr_test_date": self._dr_test_date,
            "fail_reason": fail_reason,
            "checks": checks,
        }
