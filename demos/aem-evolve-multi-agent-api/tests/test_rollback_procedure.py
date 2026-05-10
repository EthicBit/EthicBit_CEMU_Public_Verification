"""
Tests for v2.0 PR 11 — Rollback procedure evidence gate.

C-01–C-08 pass on file presence and content inspection (no live infra needed).
C-09–C-10 are skipped without AEM_ROLLBACK_TESTER / AEM_ROLLBACK_TEST_DATE.
"""
import sys
from pathlib import Path

import pytest

DEMO_ROOT = Path(__file__).resolve().parents[1]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from rollback.rollback_gate import (
    RollbackGate,
    _REQUIRED_RUNBOOK_STEPS,
    _REQUIRED_GATE_COVERAGE,
    _ROLLBACK_SQL_SCRIPTS,
    _REQUIRED_ROLLBACK_SCENARIOS,
    _RUNBOOK_FILE,
    _ROLLBACK_TOOLS_DIR,
    _MIGRATIONS_DIR,
)


# ── Gate construction ────────────────────────────────────────────────────────

class TestRollbackGateInit:
    def test_from_env_returns_gate(self):
        gate = RollbackGate.from_env()
        assert isinstance(gate, RollbackGate)

    def test_no_tester_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_ROLLBACK_TESTER", raising=False)
        gate = RollbackGate.from_env()
        assert gate._rollback_tester is None

    def test_no_test_date_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_ROLLBACK_TEST_DATE", raising=False)
        gate = RollbackGate.from_env()
        assert gate._rollback_test_date is None

    def test_captures_tester(self, monkeypatch):
        monkeypatch.setenv("AEM_ROLLBACK_TESTER", "ops@example.com")
        gate = RollbackGate.from_env()
        assert gate._rollback_tester == "ops@example.com"

    def test_captures_test_date(self, monkeypatch):
        monkeypatch.setenv("AEM_ROLLBACK_TEST_DATE", "2026-06-01")
        gate = RollbackGate.from_env()
        assert gate._rollback_test_date == "2026-06-01"


# ── Constants ────────────────────────────────────────────────────────────────

class TestConstants:
    def test_seven_runbook_steps(self):
        assert len(_REQUIRED_RUNBOOK_STEPS) == 7

    def test_nine_gate_coverage_items(self):
        assert len(_REQUIRED_GATE_COVERAGE) == 9

    def test_three_rollback_sql_scripts(self):
        assert len(_ROLLBACK_SQL_SCRIPTS) == 3

    def test_five_rollback_scenarios(self):
        assert len(_REQUIRED_ROLLBACK_SCENARIOS) == 5

    def test_pr9_in_gate_coverage(self):
        assert "PR9" in _REQUIRED_GATE_COVERAGE

    def test_db_scenario_in_required_scenarios(self):
        assert "rollback_scenario_db" in _REQUIRED_ROLLBACK_SCENARIOS

    def test_container_scenario_in_required_scenarios(self):
        assert "rollback_scenario_container" in _REQUIRED_ROLLBACK_SCENARIOS

    def test_governance_scenario_in_required_scenarios(self):
        assert "rollback_scenario_governance_signoff" in _REQUIRED_ROLLBACK_SCENARIOS


# ── C-01: Rollback runbook ───────────────────────────────────────────────────

class TestRollbackRunbook:
    def test_runbook_file_exists(self):
        assert _RUNBOOK_FILE.exists(), f"ROLLBACK_RUNBOOK.md not found at {_RUNBOOK_FILE}"

    def test_check_returns_ok(self):
        gate = RollbackGate()
        result = gate.check_runbook()
        assert result["ok"] is True

    def test_check_has_sha256(self):
        gate = RollbackGate()
        result = gate.check_runbook()
        assert len(result["sha256"]) == 64

    def test_runbook_not_empty(self):
        gate = RollbackGate()
        result = gate.check_runbook()
        assert result["size_bytes"] > 500


# ── C-02: Runbook steps ──────────────────────────────────────────────────────

class TestRunbookSteps:
    def test_check_returns_ok(self):
        gate = RollbackGate()
        result = gate.check_runbook_steps()
        assert result["ok"] is True

    def test_all_seven_steps_present(self):
        gate = RollbackGate()
        result = gate.check_runbook_steps()
        assert result["steps_present"] == 7
        assert result["missing_steps"] == []

    def test_steps_required_count(self):
        gate = RollbackGate()
        result = gate.check_runbook_steps()
        assert result["steps_required"] == 7


# ── C-03: DB rollback scripts ────────────────────────────────────────────────

class TestDbRollbackScripts:
    def test_rollback_scripts_exist(self):
        for script in _ROLLBACK_SQL_SCRIPTS:
            assert (_MIGRATIONS_DIR / script).exists(), f"Missing: {script}"

    def test_check_returns_ok(self):
        gate = RollbackGate()
        result = gate.check_db_rollback_scripts()
        assert result["ok"] is True

    def test_all_three_scripts_present(self):
        gate = RollbackGate()
        result = gate.check_db_rollback_scripts()
        assert result["scripts_present"] == 3
        assert result["missing_scripts"] == []

    def test_scripts_required_count(self):
        gate = RollbackGate()
        result = gate.check_db_rollback_scripts()
        assert result["scripts_required"] == 3


# ── C-04: Gate coverage ──────────────────────────────────────────────────────

class TestGateCoverage:
    def test_check_returns_ok(self):
        gate = RollbackGate()
        result = gate.check_gate_coverage()
        assert result["ok"] is True

    def test_all_nine_gates_covered(self):
        gate = RollbackGate()
        result = gate.check_gate_coverage()
        assert result["gates_covered"] == 9
        assert result["missing_gates"] == []

    def test_gates_required_count(self):
        gate = RollbackGate()
        result = gate.check_gate_coverage()
        assert result["gates_required"] == 9


# ── C-05: Container rollback documented ──────────────────────────────────────

class TestContainerRollback:
    def test_check_returns_ok(self):
        gate = RollbackGate()
        result = gate.check_container_rollback()
        assert result["ok"] is True

    def test_has_docker_command(self):
        gate = RollbackGate()
        result = gate.check_container_rollback()
        assert result["has_docker_command"] is True

    def test_has_previous_image_reference(self):
        gate = RollbackGate()
        result = gate.check_container_rollback()
        assert result["has_previous_image_reference"] is True

    def test_has_kubernetes_reference(self):
        gate = RollbackGate()
        result = gate.check_container_rollback()
        assert result["has_kubernetes_reference"] is True


# ── C-06: Test evidence artifact ─────────────────────────────────────────────

class TestTestEvidence:
    def test_evidence_artifact_exists(self):
        artifacts = list(_ROLLBACK_TOOLS_DIR.glob("rollback_test_evidence_*.json"))
        assert len(artifacts) >= 1

    def test_check_returns_ok(self):
        gate = RollbackGate()
        result = gate.check_test_evidence()
        assert result["ok"] is True, result.get("detail", "")

    def test_all_subjects_hashed(self):
        gate = RollbackGate()
        result = gate.check_test_evidence()
        assert result["subjects_hashed"] == result["subjects_total"]
        assert result["subjects_hashed"] >= 15

    def test_has_artifact_sha256(self):
        gate = RollbackGate()
        result = gate.check_test_evidence()
        assert result["has_artifact_sha256"] is True
        assert len(result["artifact_sha256"]) == 64

    def test_five_scenarios_documented(self):
        gate = RollbackGate()
        result = gate.check_test_evidence()
        assert result["scenarios_tested"] >= 5

    def test_no_missing_scenarios(self):
        gate = RollbackGate()
        result = gate.check_test_evidence()
        assert result["missing_scenarios"] == []


# ── C-07: All scenarios passed ───────────────────────────────────────────────

class TestScenariosPassed:
    def test_check_returns_ok(self):
        gate = RollbackGate()
        result = gate.check_scenarios_passed()
        assert result["ok"] is True

    def test_all_scenarios_passed(self):
        gate = RollbackGate()
        result = gate.check_scenarios_passed()
        assert result["scenarios_passed"] == result["scenarios_total"]
        assert result["failed_scenarios"] == []

    def test_at_least_five_scenarios(self):
        gate = RollbackGate()
        result = gate.check_scenarios_passed()
        assert result["scenarios_total"] >= 5


# ── C-08: Artifact fingerprint ───────────────────────────────────────────────

class TestArtifactFingerprint:
    def test_check_returns_ok(self):
        gate = RollbackGate()
        result = gate.check_artifact_fingerprint()
        assert result["ok"] is True

    def test_has_artifact_sha256(self):
        gate = RollbackGate()
        result = gate.check_artifact_fingerprint()
        assert result["has_artifact_sha256"] is True
        assert len(result["artifact_sha256"]) == 64


# ── C-09/C-10: Rollback tester (skipped without env vars) ────────────────────

class TestRollbackTesterChecks:
    def test_tester_skipped_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_ROLLBACK_TESTER", raising=False)
        gate = RollbackGate(rollback_tester=None)
        result = gate.check_rollback_tester()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_test_date_skipped_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_ROLLBACK_TEST_DATE", raising=False)
        gate = RollbackGate(rollback_test_date=None)
        result = gate.check_rollback_test_date()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_tester_passes_with_identity(self):
        gate = RollbackGate(rollback_tester="ops@example.com")
        result = gate.check_rollback_tester()
        assert result["ok"] is True
        assert result["rollback_tester"] == "ops@example.com"

    def test_test_date_passes_with_date(self):
        gate = RollbackGate(rollback_test_date="2026-06-01")
        result = gate.check_rollback_test_date()
        assert result["ok"] is True
        assert result["rollback_test_date"] == "2026-06-01"


# ── Full gate_check ───────────────────────────────────────────────────────────

class TestGateCheck:
    def test_gate_check_has_required_fields(self):
        gate = RollbackGate()
        result = gate.gate_check()
        assert result["gate"] == "ROLLBACK_PROCEDURE_CHECK"
        assert result["status"] in ("PASS", "FAIL")
        assert "checks_passed" in result
        assert "rollback_tested" in result

    def test_rollback_tested_false_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_ROLLBACK_TESTER", raising=False)
        monkeypatch.delenv("AEM_ROLLBACK_TEST_DATE", raising=False)
        gate = RollbackGate()
        result = gate.gate_check()
        assert result["rollback_tested"] is False

    def test_rollback_tested_false_with_only_tester(self):
        gate = RollbackGate(rollback_tester="ops@example.com", rollback_test_date=None)
        result = gate.gate_check()
        assert result["rollback_tested"] is False

    def test_rollback_tested_true_with_both(self):
        gate = RollbackGate(
            rollback_tester="ops@example.com",
            rollback_test_date="2026-06-01",
        )
        result = gate.gate_check()
        assert result["rollback_tested"] is True

    def test_gate_fails_without_tester_vars(self, monkeypatch):
        monkeypatch.delenv("AEM_ROLLBACK_TESTER", raising=False)
        monkeypatch.delenv("AEM_ROLLBACK_TEST_DATE", raising=False)
        gate = RollbackGate()
        result = gate.gate_check()
        assert result["status"] == "FAIL"

    def test_eight_local_checks_pass(self, monkeypatch):
        monkeypatch.delenv("AEM_ROLLBACK_TESTER", raising=False)
        monkeypatch.delenv("AEM_ROLLBACK_TEST_DATE", raising=False)
        gate = RollbackGate()
        result = gate.gate_check()
        checks = result["checks"]
        config_keys = [k for k in checks if k.startswith(
            ("C-01", "C-02", "C-03", "C-04", "C-05", "C-06", "C-07", "C-08")
        )]
        passed = sum(1 for k in config_keys if checks[k].get("ok"))
        assert passed == 8, f"Expected 8 local checks to pass, got {passed}: {checks}"

    def test_gate_passes_with_tester_vars(self):
        gate = RollbackGate(
            rollback_tester="ops@example.com",
            rollback_test_date="2026-06-01",
        )
        result = gate.gate_check()
        assert result["status"] == "PASS"
        assert result["checks_passed"] == 10

    def test_fail_reason_mentions_missing_env_vars(self, monkeypatch):
        monkeypatch.delenv("AEM_ROLLBACK_TESTER", raising=False)
        monkeypatch.delenv("AEM_ROLLBACK_TEST_DATE", raising=False)
        gate = RollbackGate()
        result = gate.gate_check()
        assert "AEM_ROLLBACK_TESTER" in result["fail_reason"]

    def test_fail_reason_mentions_rollback_tested_false(self, monkeypatch):
        monkeypatch.delenv("AEM_ROLLBACK_TESTER", raising=False)
        monkeypatch.delenv("AEM_ROLLBACK_TEST_DATE", raising=False)
        gate = RollbackGate()
        result = gate.gate_check()
        assert "rollback_tested=false" in result["fail_reason"]


# ── Health endpoint ───────────────────────────────────────────────────────────

class TestHealthRollbackGate:
    def test_rollback_gate_in_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert "rollback_gate" in resp.json()

    def test_gate_has_required_fields(self, client):
        resp = client.get("/health")
        gate = resp.json()["rollback_gate"]
        assert gate["gate"] == "ROLLBACK_PROCEDURE_CHECK"
        assert "status" in gate
        assert gate["rollback_tested"] is False

    def test_version_bumped_to_pr11(self, client):
        resp = client.get("/health")
        assert resp.json()["version"] == "0.19.0-demo"
