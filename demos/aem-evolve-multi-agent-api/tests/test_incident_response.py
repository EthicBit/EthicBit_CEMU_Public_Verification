"""
Tests for v2.0 PR 6 — Incident response runbook and drill evidence gate.

C-01–C-08 pass based on file presence and content.
C-09–C-10 are skipped without AEM_DRILL_COMPLETED_AT / AEM_DRILL_SIGNOFF_APPROVER.
"""
import sys
from pathlib import Path

import pytest

DEMO_ROOT = Path(__file__).resolve().parents[1]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from incident_response.incident_response_gate import (
    IncidentResponseGate,
    _REQUIRED_INCIDENTS,
    _REQUIRED_ALERT_NAMES,
    _RUNBOOK_FILE,
    _DRILL_SCRIPT,
    _IR_DIR,
)


# ── Gate construction ────────────────────────────────────────────────────────

class TestIncidentResponseGateInit:
    def test_from_env_returns_gate(self):
        gate = IncidentResponseGate.from_env()
        assert isinstance(gate, IncidentResponseGate)

    def test_no_drill_completed_at_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_DRILL_COMPLETED_AT", raising=False)
        gate = IncidentResponseGate.from_env()
        assert gate._drill_completed_at is None

    def test_no_signoff_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_DRILL_SIGNOFF_APPROVER", raising=False)
        gate = IncidentResponseGate.from_env()
        assert gate._drill_signoff_approver is None

    def test_captures_drill_completed_at(self, monkeypatch):
        monkeypatch.setenv("AEM_DRILL_COMPLETED_AT", "2026-05-10T14:00:00Z")
        gate = IncidentResponseGate.from_env()
        assert gate._drill_completed_at == "2026-05-10T14:00:00Z"

    def test_captures_signoff_approver(self, monkeypatch):
        monkeypatch.setenv("AEM_DRILL_SIGNOFF_APPROVER", "governance-lead@example.com")
        gate = IncidentResponseGate.from_env()
        assert gate._drill_signoff_approver == "governance-lead@example.com"


# ── Constants ────────────────────────────────────────────────────────────────

class TestConstants:
    def test_seven_required_incidents(self):
        assert len(_REQUIRED_INCIDENTS) == 7

    def test_seven_required_alert_names(self):
        assert len(_REQUIRED_ALERT_NAMES) == 7

    def test_incidents_numbered_inc01_through_inc07(self):
        for i, inc in enumerate(_REQUIRED_INCIDENTS, 1):
            assert inc == f"INC-0{i}"

    def test_alert_names_match_pr5(self):
        assert "AEM_HITLApprovalFailed" in _REQUIRED_ALERT_NAMES
        assert "AEM_KMSSigningFailed" in _REQUIRED_ALERT_NAMES
        assert "AEM_OIDCProviderOutage" in _REQUIRED_ALERT_NAMES


# ── C-01: Runbook exists ─────────────────────────────────────────────────────

class TestRunbookExists:
    def test_runbook_file_exists_on_disk(self):
        assert _RUNBOOK_FILE.exists(), f"INCIDENT_RESPONSE.md not found at {_RUNBOOK_FILE}"

    def test_check_returns_ok(self):
        gate = IncidentResponseGate()
        result = gate.check_runbook_exists()
        assert result["ok"] is True

    def test_check_has_sha256(self):
        gate = IncidentResponseGate()
        result = gate.check_runbook_exists()
        assert len(result["sha256"]) == 64

    def test_runbook_not_empty(self):
        gate = IncidentResponseGate()
        result = gate.check_runbook_exists()
        assert result["size_bytes"] > 1000


# ── C-02: Runbook coverage ───────────────────────────────────────────────────

class TestRunbookCoverage:
    def test_check_returns_ok(self):
        gate = IncidentResponseGate()
        result = gate.check_runbook_coverage()
        assert result["ok"] is True

    def test_all_seven_incidents_present(self):
        gate = IncidentResponseGate()
        result = gate.check_runbook_coverage()
        assert result["incidents_present"] == 7
        assert result["missing_incidents"] == []

    def test_incidents_required_count(self):
        gate = IncidentResponseGate()
        result = gate.check_runbook_coverage()
        assert result["incidents_required"] == 7


# ── C-03: Severity levels ────────────────────────────────────────────────────

class TestSeverityLevels:
    def test_check_returns_ok(self):
        gate = IncidentResponseGate()
        result = gate.check_severity_levels()
        assert result["ok"] is True

    def test_all_three_severity_levels(self):
        gate = IncidentResponseGate()
        result = gate.check_severity_levels()
        assert result["missing_severity_levels"] == []
        assert "P1" in result["severity_levels_present"]
        assert "P2" in result["severity_levels_present"]
        assert "P3" in result["severity_levels_present"]


# ── C-04: Escalation matrix ──────────────────────────────────────────────────

class TestEscalationMatrix:
    def test_check_returns_ok(self):
        gate = IncidentResponseGate()
        result = gate.check_escalation_matrix()
        assert result["ok"] is True

    def test_has_escalation_matrix(self):
        gate = IncidentResponseGate()
        result = gate.check_escalation_matrix()
        assert result["has_escalation_matrix"] is True

    def test_required_roles_present(self):
        gate = IncidentResponseGate()
        result = gate.check_escalation_matrix()
        assert result["missing_roles"] == []


# ── C-05: Recovery procedures ────────────────────────────────────────────────

class TestRecoveryProcedures:
    def test_check_returns_ok(self):
        gate = IncidentResponseGate()
        result = gate.check_recovery_procedures()
        assert result["ok"] is True

    def test_has_recovery_steps(self):
        gate = IncidentResponseGate()
        result = gate.check_recovery_procedures()
        assert result["has_recovery_steps"] is True

    def test_has_postmortem_template(self):
        gate = IncidentResponseGate()
        result = gate.check_recovery_procedures()
        assert result["has_postmortem_template"] is True


# ── C-06: Alert cross-reference ──────────────────────────────────────────────

class TestAlertCrossReference:
    def test_check_returns_ok(self):
        gate = IncidentResponseGate()
        result = gate.check_alert_cross_reference()
        assert result["ok"] is True

    def test_all_seven_alerts_cross_referenced(self):
        gate = IncidentResponseGate()
        result = gate.check_alert_cross_reference()
        assert result["alerts_cross_referenced"] == 7
        assert result["missing_alerts"] == []


# ── C-07: Drill script ───────────────────────────────────────────────────────

class TestDrillScript:
    def test_drill_script_exists(self):
        assert _DRILL_SCRIPT.exists(), f"drill_scenario.py not found at {_DRILL_SCRIPT}"

    def test_check_returns_ok(self):
        gate = IncidentResponseGate()
        result = gate.check_drill_script()
        assert result["ok"] is True

    def test_script_has_seven_scenarios(self):
        gate = IncidentResponseGate()
        result = gate.check_drill_script()
        assert result["scenarios_defined"] >= 7

    def test_script_has_sha256(self):
        gate = IncidentResponseGate()
        result = gate.check_drill_script()
        assert len(result["sha256"]) == 64


# ── C-08: Drill evidence artifact ────────────────────────────────────────────

class TestDrillEvidence:
    def test_drill_evidence_file_exists(self):
        artifacts = list(_IR_DIR.glob("drill_evidence_*.json"))
        assert len(artifacts) >= 1, "No drill_evidence_*.json found — run drill_scenario.py"

    def test_check_returns_ok(self):
        gate = IncidentResponseGate()
        result = gate.check_drill_evidence()
        assert result["ok"] is True, result.get("detail", "")

    def test_evidence_has_seven_scenarios(self):
        gate = IncidentResponseGate()
        result = gate.check_drill_evidence()
        assert result["scenarios_documented"] >= 7

    def test_evidence_has_sha256(self):
        gate = IncidentResponseGate()
        result = gate.check_drill_evidence()
        assert len(result["sha256"]) == 64


# ── C-09/C-10: Live drill evidence (skipped without env vars) ─────────────────

class TestLiveDrillChecks:
    def test_drill_completed_skipped_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_DRILL_COMPLETED_AT", raising=False)
        gate = IncidentResponseGate(drill_completed_at=None)
        result = gate.check_drill_completed()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_drill_signoff_skipped_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_DRILL_SIGNOFF_APPROVER", raising=False)
        gate = IncidentResponseGate(drill_signoff_approver=None)
        result = gate.check_drill_signoff()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_drill_completed_passes_with_timestamp(self):
        gate = IncidentResponseGate(drill_completed_at="2026-05-10T14:00:00Z")
        result = gate.check_drill_completed()
        assert result["ok"] is True
        assert result["drill_completed_at"] == "2026-05-10T14:00:00Z"

    def test_drill_signoff_passes_with_approver(self):
        gate = IncidentResponseGate(drill_signoff_approver="lead@example.com")
        result = gate.check_drill_signoff()
        assert result["ok"] is True
        assert result["signoff_approver"] == "lead@example.com"


# ── Full gate_check ───────────────────────────────────────────────────────────

class TestGateCheck:
    def test_gate_check_has_required_fields(self):
        gate = IncidentResponseGate()
        result = gate.gate_check()
        assert result["gate"] == "INCIDENT_RESPONSE_CHECK"
        assert result["status"] in ("PASS", "FAIL")
        assert "checks_passed" in result
        assert "checks_failed" in result
        assert "checks" in result

    def test_gate_fails_without_live_drill_env(self, monkeypatch):
        monkeypatch.delenv("AEM_DRILL_COMPLETED_AT", raising=False)
        monkeypatch.delenv("AEM_DRILL_SIGNOFF_APPROVER", raising=False)
        gate = IncidentResponseGate()
        result = gate.gate_check()
        assert result["status"] == "FAIL"

    def test_eight_config_checks_pass(self, monkeypatch):
        monkeypatch.delenv("AEM_DRILL_COMPLETED_AT", raising=False)
        monkeypatch.delenv("AEM_DRILL_SIGNOFF_APPROVER", raising=False)
        gate = IncidentResponseGate()
        result = gate.gate_check()
        checks = result["checks"]
        config_keys = [k for k in checks if k.startswith(
            ("C-01", "C-02", "C-03", "C-04", "C-05", "C-06", "C-07", "C-08")
        )]
        passed = sum(1 for k in config_keys if checks[k].get("ok"))
        assert passed == 8, f"Expected 8 config checks to pass, got {passed}"

    def test_gate_passes_with_live_drill_vars(self):
        gate = IncidentResponseGate(
            drill_completed_at="2026-05-10T14:00:00Z",
            drill_signoff_approver="governance-lead@example.com",
        )
        result = gate.gate_check()
        assert result["status"] == "PASS"
        assert result["checks_passed"] == 10

    def test_fail_reason_mentions_missing_env_vars(self, monkeypatch):
        monkeypatch.delenv("AEM_DRILL_COMPLETED_AT", raising=False)
        monkeypatch.delenv("AEM_DRILL_SIGNOFF_APPROVER", raising=False)
        gate = IncidentResponseGate()
        result = gate.gate_check()
        assert "AEM_DRILL_COMPLETED_AT" in result["fail_reason"]


# ── Health endpoint ───────────────────────────────────────────────────────────

class TestHealthIncidentResponseGate:
    def test_incident_response_gate_in_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert "incident_response_gate" in resp.json()

    def test_gate_has_required_fields(self, client):
        resp = client.get("/health")
        gate = resp.json()["incident_response_gate"]
        assert gate["gate"] == "INCIDENT_RESPONSE_CHECK"
        assert "status" in gate

    def test_version_bumped_to_pr6(self, client):
        resp = client.get("/health")
        assert resp.json()["version"] == "0.17.0-demo"
