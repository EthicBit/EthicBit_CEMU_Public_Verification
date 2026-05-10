"""
Tests for v2.0 PR 12 — Disaster recovery evidence gate.

C-01–C-08 pass on file presence and content inspection (no live infra needed).
C-09–C-10 are skipped without AEM_DR_TESTER / AEM_DR_TEST_DATE.
"""
import sys
from pathlib import Path

import pytest

DEMO_ROOT = Path(__file__).resolve().parents[1]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from disaster_recovery.disaster_recovery_gate import (
    DisasterRecoveryGate,
    _REQUIRED_RTO_RPO_FIELDS,
    _REQUIRED_BACKUP_FIELDS,
    _REQUIRED_DR_SCENARIOS,
    _REQUIRED_RECOVERY_PROCEDURE_TERMS,
    _DR_PLAN_FILE,
    _DR_TOOLS_DIR,
)


# ── Gate construction ────────────────────────────────────────────────────────

class TestDisasterRecoveryGateInit:
    def test_from_env_returns_gate(self):
        gate = DisasterRecoveryGate.from_env()
        assert isinstance(gate, DisasterRecoveryGate)

    def test_no_tester_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_DR_TESTER", raising=False)
        gate = DisasterRecoveryGate.from_env()
        assert gate._dr_tester is None

    def test_no_test_date_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_DR_TEST_DATE", raising=False)
        gate = DisasterRecoveryGate.from_env()
        assert gate._dr_test_date is None

    def test_captures_tester(self, monkeypatch):
        monkeypatch.setenv("AEM_DR_TESTER", "ops@example.com")
        gate = DisasterRecoveryGate.from_env()
        assert gate._dr_tester == "ops@example.com"

    def test_captures_test_date(self, monkeypatch):
        monkeypatch.setenv("AEM_DR_TEST_DATE", "2026-06-01")
        gate = DisasterRecoveryGate.from_env()
        assert gate._dr_test_date == "2026-06-01"


# ── Constants ────────────────────────────────────────────────────────────────

class TestConstants:
    def test_four_rto_rpo_fields(self):
        assert len(_REQUIRED_RTO_RPO_FIELDS) == 4

    def test_rto_minutes_in_fields(self):
        assert "rto_minutes" in _REQUIRED_RTO_RPO_FIELDS

    def test_rpo_minutes_in_fields(self):
        assert "rpo_minutes" in _REQUIRED_RTO_RPO_FIELDS

    def test_three_backup_fields(self):
        assert len(_REQUIRED_BACKUP_FIELDS) >= 3

    def test_five_dr_scenarios(self):
        assert len(_REQUIRED_DR_SCENARIOS) == 5

    def test_data_loss_scenario_present(self):
        assert "dr_scenario_data_loss" in _REQUIRED_DR_SCENARIOS

    def test_key_compromise_scenario_present(self):
        assert "dr_scenario_key_compromise" in _REQUIRED_DR_SCENARIOS

    def test_audit_chain_scenario_present(self):
        assert "dr_scenario_audit_chain_corruption" in _REQUIRED_DR_SCENARIOS

    def test_five_recovery_procedure_terms(self):
        assert len(_REQUIRED_RECOVERY_PROCEDURE_TERMS) >= 5


# ── C-01: DR plan ────────────────────────────────────────────────────────────

class TestDRPlan:
    def test_dr_plan_file_exists(self):
        assert _DR_PLAN_FILE.exists(), f"DISASTER_RECOVERY.md not found at {_DR_PLAN_FILE}"

    def test_check_returns_ok(self):
        gate = DisasterRecoveryGate()
        result = gate.check_dr_plan()
        assert result["ok"] is True

    def test_check_has_sha256(self):
        gate = DisasterRecoveryGate()
        result = gate.check_dr_plan()
        assert len(result["sha256"]) == 64

    def test_dr_plan_not_empty(self):
        gate = DisasterRecoveryGate()
        result = gate.check_dr_plan()
        assert result["size_bytes"] > 500


# ── C-02: RTO / RPO targets ──────────────────────────────────────────────────

class TestRtoRpo:
    def test_check_returns_ok(self):
        gate = DisasterRecoveryGate()
        result = gate.check_rto_rpo()
        assert result["ok"] is True

    def test_has_rto(self):
        gate = DisasterRecoveryGate()
        result = gate.check_rto_rpo()
        assert result["has_rto"] is True

    def test_has_rpo(self):
        gate = DisasterRecoveryGate()
        result = gate.check_rto_rpo()
        assert result["has_rpo"] is True

    def test_no_missing_fields(self):
        gate = DisasterRecoveryGate()
        result = gate.check_rto_rpo()
        assert result["missing_fields"] == []


# ── C-03: Backup strategy ────────────────────────────────────────────────────

class TestBackupStrategy:
    def test_check_returns_ok(self):
        gate = DisasterRecoveryGate()
        result = gate.check_backup_strategy()
        assert result["ok"] is True

    def test_has_backup_section(self):
        gate = DisasterRecoveryGate()
        result = gate.check_backup_strategy()
        assert result["has_backup_section"] is True

    def test_has_retention(self):
        gate = DisasterRecoveryGate()
        result = gate.check_backup_strategy()
        assert result["has_retention"] is True

    def test_no_missing_backup_fields(self):
        gate = DisasterRecoveryGate()
        result = gate.check_backup_strategy()
        assert result["missing_fields"] == []


# ── C-04: DR scenarios documented ────────────────────────────────────────────

class TestDRScenarios:
    def test_evidence_artifact_exists(self):
        artifacts = list(_DR_TOOLS_DIR.glob("dr_test_evidence_*.json"))
        assert len(artifacts) >= 1

    def test_check_returns_ok(self):
        gate = DisasterRecoveryGate()
        result = gate.check_dr_scenarios()
        assert result["ok"] is True, result.get("missing_scenarios", "")

    def test_all_five_scenarios_documented(self):
        gate = DisasterRecoveryGate()
        result = gate.check_dr_scenarios()
        assert result["scenarios_documented"] == 5
        assert result["missing_scenarios"] == []

    def test_scenarios_required_count(self):
        gate = DisasterRecoveryGate()
        result = gate.check_dr_scenarios()
        assert result["scenarios_required"] == 5


# ── C-05: Recovery procedures ────────────────────────────────────────────────

class TestRecoveryProcedures:
    def test_check_returns_ok(self):
        gate = DisasterRecoveryGate()
        result = gate.check_recovery_procedures()
        assert result["ok"] is True

    def test_all_terms_present(self):
        gate = DisasterRecoveryGate()
        result = gate.check_recovery_procedures()
        assert result["missing_terms"] == []

    def test_terms_required_count(self):
        gate = DisasterRecoveryGate()
        result = gate.check_recovery_procedures()
        assert result["terms_required"] >= 5


# ── C-06: DR evidence artifact ───────────────────────────────────────────────

class TestDREvidence:
    def test_check_returns_ok(self):
        gate = DisasterRecoveryGate()
        result = gate.check_dr_evidence()
        assert result["ok"] is True, result.get("detail", "")

    def test_all_subjects_hashed(self):
        gate = DisasterRecoveryGate()
        result = gate.check_dr_evidence()
        assert result["subjects_hashed"] == result["subjects_total"]
        assert result["subjects_hashed"] >= 15

    def test_has_artifact_sha256(self):
        gate = DisasterRecoveryGate()
        result = gate.check_dr_evidence()
        assert result["has_artifact_sha256"] is True
        assert len(result["artifact_sha256"]) == 64

    def test_five_scenarios_tested(self):
        gate = DisasterRecoveryGate()
        result = gate.check_dr_evidence()
        assert result["dr_scenarios_tested"] >= 5

    def test_rto_target_set(self):
        gate = DisasterRecoveryGate()
        result = gate.check_dr_evidence()
        assert result["rto_target_minutes"] == 240

    def test_rpo_target_set(self):
        gate = DisasterRecoveryGate()
        result = gate.check_dr_evidence()
        assert result["rpo_target_minutes"] == 60


# ── C-07: All scenarios passed ───────────────────────────────────────────────

class TestScenariosPassed:
    def test_check_returns_ok(self):
        gate = DisasterRecoveryGate()
        result = gate.check_scenarios_passed()
        assert result["ok"] is True

    def test_all_scenarios_passed(self):
        gate = DisasterRecoveryGate()
        result = gate.check_scenarios_passed()
        assert result["scenarios_passed"] == result["scenarios_total"]
        assert result["failed_scenarios"] == []

    def test_at_least_five_scenarios(self):
        gate = DisasterRecoveryGate()
        result = gate.check_scenarios_passed()
        assert result["scenarios_total"] >= 5


# ── C-08: Artifact fingerprint ───────────────────────────────────────────────

class TestArtifactFingerprint:
    def test_check_returns_ok(self):
        gate = DisasterRecoveryGate()
        result = gate.check_artifact_fingerprint()
        assert result["ok"] is True

    def test_has_artifact_sha256(self):
        gate = DisasterRecoveryGate()
        result = gate.check_artifact_fingerprint()
        assert result["has_artifact_sha256"] is True
        assert len(result["artifact_sha256"]) == 64


# ── C-09/C-10: DR tester (skipped without env vars) ──────────────────────────

class TestDRTesterChecks:
    def test_tester_skipped_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_DR_TESTER", raising=False)
        gate = DisasterRecoveryGate(dr_tester=None)
        result = gate.check_dr_tester()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_test_date_skipped_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_DR_TEST_DATE", raising=False)
        gate = DisasterRecoveryGate(dr_test_date=None)
        result = gate.check_dr_test_date()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_tester_passes_with_identity(self):
        gate = DisasterRecoveryGate(dr_tester="ops@example.com")
        result = gate.check_dr_tester()
        assert result["ok"] is True
        assert result["dr_tester"] == "ops@example.com"

    def test_test_date_passes_with_date(self):
        gate = DisasterRecoveryGate(dr_test_date="2026-06-01")
        result = gate.check_dr_test_date()
        assert result["ok"] is True
        assert result["dr_test_date"] == "2026-06-01"


# ── Full gate_check ───────────────────────────────────────────────────────────

class TestGateCheck:
    def test_gate_check_has_required_fields(self):
        gate = DisasterRecoveryGate()
        result = gate.gate_check()
        assert result["gate"] == "DISASTER_RECOVERY_CHECK"
        assert result["status"] in ("PASS", "FAIL")
        assert "checks_passed" in result
        assert "dr_tested" in result

    def test_dr_tested_false_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_DR_TESTER", raising=False)
        monkeypatch.delenv("AEM_DR_TEST_DATE", raising=False)
        gate = DisasterRecoveryGate()
        result = gate.gate_check()
        assert result["dr_tested"] is False

    def test_dr_tested_false_with_only_tester(self):
        gate = DisasterRecoveryGate(dr_tester="ops@example.com", dr_test_date=None)
        result = gate.gate_check()
        assert result["dr_tested"] is False

    def test_dr_tested_true_with_both(self):
        gate = DisasterRecoveryGate(
            dr_tester="ops@example.com",
            dr_test_date="2026-06-01",
        )
        result = gate.gate_check()
        assert result["dr_tested"] is True

    def test_gate_fails_without_tester_vars(self, monkeypatch):
        monkeypatch.delenv("AEM_DR_TESTER", raising=False)
        monkeypatch.delenv("AEM_DR_TEST_DATE", raising=False)
        gate = DisasterRecoveryGate()
        result = gate.gate_check()
        assert result["status"] == "FAIL"

    def test_eight_local_checks_pass(self, monkeypatch):
        monkeypatch.delenv("AEM_DR_TESTER", raising=False)
        monkeypatch.delenv("AEM_DR_TEST_DATE", raising=False)
        gate = DisasterRecoveryGate()
        result = gate.gate_check()
        checks = result["checks"]
        config_keys = [k for k in checks if k.startswith(
            ("C-01", "C-02", "C-03", "C-04", "C-05", "C-06", "C-07", "C-08")
        )]
        passed = sum(1 for k in config_keys if checks[k].get("ok"))
        assert passed == 8, f"Expected 8 local checks to pass, got {passed}: {checks}"

    def test_gate_passes_with_tester_vars(self):
        gate = DisasterRecoveryGate(
            dr_tester="ops@example.com",
            dr_test_date="2026-06-01",
        )
        result = gate.gate_check()
        assert result["status"] == "PASS"
        assert result["checks_passed"] == 10

    def test_fail_reason_mentions_missing_env_vars(self, monkeypatch):
        monkeypatch.delenv("AEM_DR_TESTER", raising=False)
        monkeypatch.delenv("AEM_DR_TEST_DATE", raising=False)
        gate = DisasterRecoveryGate()
        result = gate.gate_check()
        assert "AEM_DR_TESTER" in result["fail_reason"]

    def test_fail_reason_mentions_dr_tested_false(self, monkeypatch):
        monkeypatch.delenv("AEM_DR_TESTER", raising=False)
        monkeypatch.delenv("AEM_DR_TEST_DATE", raising=False)
        gate = DisasterRecoveryGate()
        result = gate.gate_check()
        assert "dr_tested=false" in result["fail_reason"]


# ── Health endpoint ───────────────────────────────────────────────────────────

class TestHealthDisasterRecoveryGate:
    def test_disaster_recovery_gate_in_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert "disaster_recovery_gate" in resp.json()

    def test_gate_has_required_fields(self, client):
        resp = client.get("/health")
        gate = resp.json()["disaster_recovery_gate"]
        assert gate["gate"] == "DISASTER_RECOVERY_CHECK"
        assert "status" in gate
        assert gate["dr_tested"] is False

    def test_version_bumped_to_pr12(self, client):
        resp = client.get("/health")
        assert resp.json()["version"] == "0.19.0-demo"
