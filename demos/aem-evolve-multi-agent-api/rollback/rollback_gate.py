"""
AEM-EVOLVE™ v2.0 PR 11 — Rollback Procedure Evidence Gate.

C-01–C-08 pass on file presence and content inspection (no live infra needed).
C-09 requires AEM_ROLLBACK_TESTER env var (identity of person who ran dry-run test).
C-10 requires AEM_ROLLBACK_TEST_DATE env var (ISO8601 date of rollback test).

Non-claims:
  This gate verifies that rollback procedure evidence exists and is structurally
  complete. It does NOT claim a production rollback has been executed.
  rollback_tested is always False until C-09 and C-10 are both set.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

_DEMO_ROOT = Path(__file__).resolve().parents[1]
_DOCS_DIR = _DEMO_ROOT / "docs"
_ROLLBACK_TOOLS_DIR = _DEMO_ROOT / "tools" / "rollback"
_MIGRATIONS_DIR = _DEMO_ROOT / "migrations"

_RUNBOOK_FILE = _DOCS_DIR / "ROLLBACK_RUNBOOK.md"
_EVIDENCE_GLOB = "rollback_test_evidence_*.json"

_ROLLBACK_SQL_SCRIPTS = [
    "rollback/001_rollback_initial_schema.sql",
    "rollback/002_rollback_metrics_table.sql",
    "rollback/003_rollback_langraph_checkpointer.sql",
]

_REQUIRED_RUNBOOK_STEPS = [
    "Stop Traffic",
    "Identify",
    "Roll Back",
    "database",
    "Verify",
    "Root Cause",
    "Sign-Off",
]

_REQUIRED_GATE_COVERAGE = [
    "PR1", "PR2", "PR3", "PR4", "PR5", "PR6", "PR7", "PR8", "PR9",
]

_REQUIRED_ROLLBACK_SCENARIOS = [
    "rollback_scenario_container",
    "rollback_scenario_db",
    "rollback_scenario_gate_verification",
    "rollback_scenario_rca_template",
    "rollback_scenario_governance_signoff",
]


class RollbackGate:
    """Gate verifier for rollback procedure evidence (PR 11)."""

    def __init__(
        self,
        rollback_tester: str | None = None,
        rollback_test_date: str | None = None,
    ) -> None:
        self._rollback_tester = rollback_tester
        self._rollback_test_date = rollback_test_date

    @classmethod
    def from_env(cls) -> "RollbackGate":
        return cls(
            rollback_tester=os.getenv("AEM_ROLLBACK_TESTER", "").strip() or None,
            rollback_test_date=os.getenv("AEM_ROLLBACK_TEST_DATE", "").strip() or None,
        )

    # ── C-01: Rollback runbook exists ─────────────────────────────────────────

    def check_runbook(self) -> dict[str, Any]:
        if not _RUNBOOK_FILE.exists():
            return {"ok": False, "detail": f"ROLLBACK_RUNBOOK.md not found at {_RUNBOOK_FILE}"}
        content = _RUNBOOK_FILE.read_text(encoding="utf-8")
        sha256 = hashlib.sha256(content.encode()).hexdigest()
        return {
            "ok": True,
            "file": str(_RUNBOOK_FILE),
            "sha256": sha256,
            "size_bytes": len(content.encode()),
        }

    # ── C-02: Runbook covers all 7 steps ─────────────────────────────────────

    def check_runbook_steps(self) -> dict[str, Any]:
        if not _RUNBOOK_FILE.exists():
            return {"ok": False, "detail": "ROLLBACK_RUNBOOK.md missing"}
        content = _RUNBOOK_FILE.read_text(encoding="utf-8")
        lower = content.lower()
        missing = [s for s in _REQUIRED_RUNBOOK_STEPS if s.lower() not in lower]
        return {
            "ok": not missing,
            "steps_required": len(_REQUIRED_RUNBOOK_STEPS),
            "steps_present": len(_REQUIRED_RUNBOOK_STEPS) - len(missing),
            "missing_steps": missing,
        }

    # ── C-03: Database rollback scripts exist ─────────────────────────────────

    def check_db_rollback_scripts(self) -> dict[str, Any]:
        missing = [s for s in _ROLLBACK_SQL_SCRIPTS
                   if not (_MIGRATIONS_DIR / s).exists()]
        present = [s for s in _ROLLBACK_SQL_SCRIPTS
                   if (_MIGRATIONS_DIR / s).exists()]
        return {
            "ok": not missing,
            "scripts_required": len(_ROLLBACK_SQL_SCRIPTS),
            "scripts_present": len(present),
            "missing_scripts": missing,
        }

    # ── C-04: Gate failure scenarios covered ─────────────────────────────────

    def check_gate_coverage(self) -> dict[str, Any]:
        if not _RUNBOOK_FILE.exists():
            return {"ok": False, "detail": "ROLLBACK_RUNBOOK.md missing"}
        content = _RUNBOOK_FILE.read_text(encoding="utf-8")
        missing = [g for g in _REQUIRED_GATE_COVERAGE if g not in content]
        return {
            "ok": not missing,
            "gates_required": len(_REQUIRED_GATE_COVERAGE),
            "gates_covered": len(_REQUIRED_GATE_COVERAGE) - len(missing),
            "missing_gates": missing,
        }

    # ── C-05: Container rollback procedure documented ─────────────────────────

    def check_container_rollback(self) -> dict[str, Any]:
        if not _RUNBOOK_FILE.exists():
            return {"ok": False, "detail": "ROLLBACK_RUNBOOK.md missing"}
        content = _RUNBOOK_FILE.read_text(encoding="utf-8")
        has_docker = "docker" in content.lower()
        has_previous_image = "previous" in content.lower()
        has_kubernetes = "kubectl" in content.lower() or "kubernetes" in content.lower()
        return {
            "ok": has_docker and has_previous_image,
            "has_docker_command": has_docker,
            "has_previous_image_reference": has_previous_image,
            "has_kubernetes_reference": has_kubernetes,
        }

    # ── C-06: Rollback test evidence artifact exists ──────────────────────────

    def check_test_evidence(self) -> dict[str, Any]:
        artifacts = sorted(_ROLLBACK_TOOLS_DIR.glob(_EVIDENCE_GLOB)) if _ROLLBACK_TOOLS_DIR.exists() else []
        if not artifacts:
            return {
                "ok": False,
                "detail": (
                    f"No rollback_test_evidence_*.json found in {_ROLLBACK_TOOLS_DIR}. "
                    "Run: python tools/production_readiness/verify_rollback_procedure.py --generate"
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
        scenarios_tested = data.get("rollback_scenarios_tested", 0)
        scenarios_passed = data.get("rollback_scenarios_passed", 0)

        scenario_ids = {s["scenario_id"] for s in data.get("scenarios", [])}
        missing_scenarios = [s for s in _REQUIRED_ROLLBACK_SCENARIOS if s not in scenario_ids]

        return {
            "ok": hashed >= 15 and hashed == total and has_sha and not missing_scenarios,
            "file": str(latest),
            "sha256": sha256,
            "artifact_sha256": data.get("artifact_sha256", ""),
            "subjects_hashed": hashed,
            "subjects_total": total,
            "has_artifact_sha256": has_sha,
            "scenarios_tested": scenarios_tested,
            "scenarios_passed": scenarios_passed,
            "missing_scenarios": missing_scenarios,
        }

    # ── C-07: All 5 rollback scenarios passed ────────────────────────────────

    def check_scenarios_passed(self) -> dict[str, Any]:
        artifacts = sorted(_ROLLBACK_TOOLS_DIR.glob(_EVIDENCE_GLOB)) if _ROLLBACK_TOOLS_DIR.exists() else []
        if not artifacts:
            return {"ok": False, "detail": f"No rollback_test_evidence_*.json found"}
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
        artifacts = sorted(_ROLLBACK_TOOLS_DIR.glob(_EVIDENCE_GLOB)) if _ROLLBACK_TOOLS_DIR.exists() else []
        if not artifacts:
            return {"ok": False, "detail": f"No rollback_test_evidence_*.json found"}
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

    # ── C-09: Rollback tester identity ───────────────────────────────────────

    def check_rollback_tester(self) -> dict[str, Any]:
        if not self._rollback_tester:
            return {
                "ok": False,
                "skipped": True,
                "reason": (
                    "AEM_ROLLBACK_TESTER not set — set to identity of person who executed "
                    "the rollback dry-run test before claiming rollback_tested=true"
                ),
            }
        return {"ok": True, "rollback_tester": self._rollback_tester}

    # ── C-10: Rollback test date ──────────────────────────────────────────────

    def check_rollback_test_date(self) -> dict[str, Any]:
        if not self._rollback_test_date:
            return {
                "ok": False,
                "skipped": True,
                "reason": "AEM_ROLLBACK_TEST_DATE not set — set to ISO8601 date of rollback dry-run test",
            }
        return {"ok": True, "rollback_test_date": self._rollback_test_date}

    # ── Full gate ─────────────────────────────────────────────────────────────

    def gate_check(self) -> dict[str, Any]:
        c01 = self.check_runbook()
        c02 = self.check_runbook_steps()
        c03 = self.check_db_rollback_scripts()
        c04 = self.check_gate_coverage()
        c05 = self.check_container_rollback()
        c06 = self.check_test_evidence()
        c07 = self.check_scenarios_passed()
        c08 = self.check_artifact_fingerprint()
        c09 = self.check_rollback_tester()
        c10 = self.check_rollback_test_date()

        checks = {
            "C-01_runbook": c01,
            "C-02_runbook_steps": c02,
            "C-03_db_rollback_scripts": c03,
            "C-04_gate_coverage": c04,
            "C-05_container_rollback": c05,
            "C-06_test_evidence": c06,
            "C-07_scenarios_passed": c07,
            "C-08_artifact_fingerprint": c08,
            "C-09_rollback_tester": c09,
            "C-10_rollback_test_date": c10,
        }

        passed = sum(1 for v in checks.values() if v.get("ok"))
        failed = len(checks) - passed
        status = "PASS" if failed == 0 else "FAIL"

        fail_reason = None
        if status == "FAIL":
            missing_live = []
            if not self._rollback_tester:
                missing_live.append("AEM_ROLLBACK_TESTER")
            if not self._rollback_test_date:
                missing_live.append("AEM_ROLLBACK_TEST_DATE")
            if missing_live:
                fail_reason = (
                    f"Rollback procedure not yet dry-run tested: "
                    f"{', '.join(missing_live)} not set. rollback_tested=false"
                )
            else:
                failing = [k for k, v in checks.items() if not v.get("ok")]
                fail_reason = f"Failing checks: {', '.join(failing)}"

        return {
            "gate": "ROLLBACK_PROCEDURE_CHECK",
            "status": status,
            "checks_passed": passed,
            "checks_failed": failed,
            "rollback_tested": (
                self._rollback_tester is not None
                and self._rollback_test_date is not None
            ),
            "rollback_tester": self._rollback_tester,
            "rollback_test_date": self._rollback_test_date,
            "fail_reason": fail_reason,
            "checks": checks,
        }
