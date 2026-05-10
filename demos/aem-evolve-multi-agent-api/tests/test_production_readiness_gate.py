"""
Tests for v2.0 PR 13 — Production readiness gate aggregator.

C-01–C-08 pass on verifier presence, module import, and gate result inspection.
C-09–C-10 are skipped without AEM_READINESS_REVIEWER / AEM_READINESS_REVIEW_DATE.
"""
import sys
from pathlib import Path

import pytest

DEMO_ROOT = Path(__file__).resolve().parents[1]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from readiness.readiness_gate import (
    ReadinessGate,
    _REQUIRED_VERIFIERS,
    _IMPORTABLE_GATE_MODULES,
    _EXPECTED_GATE_IDS,
    _MIN_FILE_CHECKS_PASSING,
    _PR_VERIFIERS_DIR,
    _READINESS_TOOLS_DIR,
)


# ── Gate construction ────────────────────────────────────────────────────────

class TestReadinessGateInit:
    def test_from_env_returns_gate(self):
        gate = ReadinessGate.from_env()
        assert isinstance(gate, ReadinessGate)

    def test_no_reviewer_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_READINESS_REVIEWER", raising=False)
        gate = ReadinessGate.from_env()
        assert gate._readiness_reviewer is None

    def test_no_review_date_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_READINESS_REVIEW_DATE", raising=False)
        gate = ReadinessGate.from_env()
        assert gate._readiness_review_date is None

    def test_captures_reviewer(self, monkeypatch):
        monkeypatch.setenv("AEM_READINESS_REVIEWER", "gov-lead@example.com")
        gate = ReadinessGate.from_env()
        assert gate._readiness_reviewer == "gov-lead@example.com"

    def test_captures_review_date(self, monkeypatch):
        monkeypatch.setenv("AEM_READINESS_REVIEW_DATE", "2026-06-01")
        gate = ReadinessGate.from_env()
        assert gate._readiness_review_date == "2026-06-01"


# ── Constants ────────────────────────────────────────────────────────────────

class TestConstants:
    def test_twelve_required_verifiers(self):
        assert len(_REQUIRED_VERIFIERS) == 12

    def test_eight_importable_gate_modules(self):
        assert len(_IMPORTABLE_GATE_MODULES) == 8

    def test_min_file_checks_passing_is_eight(self):
        assert _MIN_FILE_CHECKS_PASSING == 8

    def test_verify_production_readiness_not_in_required_verifiers(self):
        # aggregator verifier is not required to verify itself
        assert "verify_production_readiness.py" not in _REQUIRED_VERIFIERS

    def test_all_pr1_through_pr12_verifiers_present(self):
        names = set(_REQUIRED_VERIFIERS)
        assert "verify_oidc_provider.py" in names
        assert "verify_disaster_recovery.py" in names

    def test_eight_expected_gate_ids(self):
        assert len(_EXPECTED_GATE_IDS) == 8

    def test_production_readiness_gate_in_expected_ids(self):
        assert "PRODUCTION_DEPLOYMENT_AUDIT_CHECK" in _EXPECTED_GATE_IDS.values()

    def test_disaster_recovery_check_in_expected_ids(self):
        assert "DISASTER_RECOVERY_CHECK" in _EXPECTED_GATE_IDS.values()


# ── C-01: Verifiers present ──────────────────────────────────────────────────

class TestVerifiersPresent:
    def test_check_returns_ok(self):
        gate = ReadinessGate()
        result = gate.check_verifiers_present()
        assert result["ok"] is True, result.get("missing_verifiers", "")

    def test_all_twelve_present(self):
        gate = ReadinessGate()
        result = gate.check_verifiers_present()
        assert result["verifiers_present"] == 12
        assert result["missing_verifiers"] == []

    def test_verifiers_required_count(self):
        gate = ReadinessGate()
        result = gate.check_verifiers_present()
        assert result["verifiers_required"] == 12


# ── C-02: Gate modules load ──────────────────────────────────────────────────

class TestGateModulesLoad:
    def test_check_returns_ok(self):
        gate = ReadinessGate()
        result = gate.check_gate_modules_load()
        assert result["ok"] is True, result.get("failed_modules", "")

    def test_all_eight_modules_load(self):
        gate = ReadinessGate()
        result = gate.check_gate_modules_load()
        assert result["modules_loaded"] == 8
        assert result["failed_modules"] == []

    def test_modules_required_count(self):
        gate = ReadinessGate()
        result = gate.check_gate_modules_load()
        assert result["modules_required"] == 8


# ── C-03: PR5 + PR6 file-based checks ───────────────────────────────────────

class TestPr5Pr6:
    def test_check_returns_ok(self):
        gate = ReadinessGate()
        result = gate.check_pr5_pr6()
        assert result["ok"] is True, result.get("gates", "")

    def test_monitoring_gate_eight_checks_pass(self):
        gate = ReadinessGate()
        result = gate.check_pr5_pr6()
        assert result["gates"]["MonitoringGate"]["file_checks_passed"] >= 8

    def test_incident_response_gate_eight_checks_pass(self):
        gate = ReadinessGate()
        result = gate.check_pr5_pr6()
        assert result["gates"]["IncidentResponseGate"]["file_checks_passed"] >= 8


# ── C-04: PR7 + PR8 file-based checks ───────────────────────────────────────

class TestPr7Pr8:
    def test_check_returns_ok(self):
        gate = ReadinessGate()
        result = gate.check_pr7_pr8()
        assert result["ok"] is True, result.get("gates", "")

    def test_security_review_gate_eight_checks_pass(self):
        gate = ReadinessGate()
        result = gate.check_pr7_pr8()
        assert result["gates"]["SecurityReviewGate"]["file_checks_passed"] >= 8

    def test_reproduction_gate_eight_checks_pass(self):
        gate = ReadinessGate()
        result = gate.check_pr7_pr8()
        assert result["gates"]["ReproductionGate"]["file_checks_passed"] >= 8


# ── C-05: PR9 + PR10 file-based checks ──────────────────────────────────────

class TestPr9Pr10:
    def test_check_returns_ok(self):
        gate = ReadinessGate()
        result = gate.check_pr9_pr10()
        assert result["ok"] is True, result.get("gates", "")

    def test_deployment_gate_eight_checks_pass(self):
        gate = ReadinessGate()
        result = gate.check_pr9_pr10()
        assert result["gates"]["DeploymentGate"]["file_checks_passed"] >= 8

    def test_slo_gate_eight_checks_pass(self):
        gate = ReadinessGate()
        result = gate.check_pr9_pr10()
        assert result["gates"]["SLOGate"]["file_checks_passed"] >= 8


# ── C-06: PR11 + PR12 file-based checks ─────────────────────────────────────

class TestPr11Pr12:
    def test_check_returns_ok(self):
        gate = ReadinessGate()
        result = gate.check_pr11_pr12()
        assert result["ok"] is True, result.get("gates", "")

    def test_rollback_gate_eight_checks_pass(self):
        gate = ReadinessGate()
        result = gate.check_pr11_pr12()
        assert result["gates"]["RollbackGate"]["file_checks_passed"] >= 8

    def test_disaster_recovery_gate_eight_checks_pass(self):
        gate = ReadinessGate()
        result = gate.check_pr11_pr12()
        assert result["gates"]["DisasterRecoveryGate"]["file_checks_passed"] >= 8


# ── C-07: Aggregate evidence artifact ───────────────────────────────────────

class TestAggregateEvidence:
    def test_aggregate_artifact_exists(self):
        artifacts = list(_READINESS_TOOLS_DIR.glob("aggregate_readiness_evidence_*.json"))
        assert len(artifacts) >= 1

    def test_check_returns_ok(self):
        gate = ReadinessGate()
        result = gate.check_aggregate_evidence()
        assert result["ok"] is True, result.get("detail", "")

    def test_all_subjects_hashed(self):
        gate = ReadinessGate()
        result = gate.check_aggregate_evidence()
        assert result["subjects_hashed"] == result["subjects_total"]
        assert result["subjects_hashed"] >= 15

    def test_has_artifact_sha256(self):
        gate = ReadinessGate()
        result = gate.check_aggregate_evidence()
        assert result["has_artifact_sha256"] is True
        assert len(result["artifact_sha256"]) == 64


# ── C-08: Artifact fingerprint ───────────────────────────────────────────────

class TestArtifactFingerprint:
    def test_check_returns_ok(self):
        gate = ReadinessGate()
        result = gate.check_artifact_fingerprint()
        assert result["ok"] is True

    def test_has_artifact_sha256(self):
        gate = ReadinessGate()
        result = gate.check_artifact_fingerprint()
        assert result["has_artifact_sha256"] is True
        assert len(result["artifact_sha256"]) == 64


# ── C-09/C-10: Readiness reviewer (skipped without env vars) ─────────────────

class TestReadinessReviewerChecks:
    def test_reviewer_skipped_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_READINESS_REVIEWER", raising=False)
        gate = ReadinessGate(readiness_reviewer=None)
        result = gate.check_readiness_reviewer()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_review_date_skipped_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_READINESS_REVIEW_DATE", raising=False)
        gate = ReadinessGate(readiness_review_date=None)
        result = gate.check_readiness_review_date()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_reviewer_passes_with_identity(self):
        gate = ReadinessGate(readiness_reviewer="gov-lead@example.com")
        result = gate.check_readiness_reviewer()
        assert result["ok"] is True
        assert result["readiness_reviewer"] == "gov-lead@example.com"

    def test_review_date_passes_with_date(self):
        gate = ReadinessGate(readiness_review_date="2026-06-01")
        result = gate.check_readiness_review_date()
        assert result["ok"] is True


# ── Full gate_check ───────────────────────────────────────────────────────────

class TestGateCheck:
    def test_gate_check_has_required_fields(self):
        gate = ReadinessGate()
        result = gate.gate_check()
        assert result["gate"] == "PRODUCTION_READINESS_GATE"
        assert result["status"] in ("PASS", "FAIL")
        assert "checks_passed" in result
        assert "production_ready" in result
        assert "gates_evidence_complete" in result
        assert "gate_summary" in result

    def test_production_ready_false_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_READINESS_REVIEWER", raising=False)
        monkeypatch.delenv("AEM_READINESS_REVIEW_DATE", raising=False)
        gate = ReadinessGate()
        result = gate.gate_check()
        assert result["production_ready"] is False

    def test_gates_evidence_complete_true(self, monkeypatch):
        monkeypatch.delenv("AEM_READINESS_REVIEWER", raising=False)
        monkeypatch.delenv("AEM_READINESS_REVIEW_DATE", raising=False)
        gate = ReadinessGate()
        result = gate.gate_check()
        assert result["gates_evidence_complete"] is True

    def test_gate_summary_contains_all_eight_gates(self):
        gate = ReadinessGate()
        result = gate.gate_check()
        summary = result["gate_summary"]
        assert len(summary) == 8

    def test_gate_summary_all_gates_have_gate_id(self):
        gate = ReadinessGate()
        result = gate.gate_check()
        for class_name, g in result["gate_summary"].items():
            assert "gate" in g, f"{class_name} missing 'gate' key"
            assert g["gate"] in _EXPECTED_GATE_IDS.values(), f"Unexpected gate ID: {g['gate']}"

    def test_gate_summary_all_file_checks_pass(self):
        gate = ReadinessGate()
        result = gate.gate_check()
        for class_name, g in result["gate_summary"].items():
            assert g.get("file_checks_passed", 0) >= 8, (
                f"{class_name} only {g.get('file_checks_passed')} file checks passed"
            )

    def test_gate_fails_without_reviewer_vars(self, monkeypatch):
        monkeypatch.delenv("AEM_READINESS_REVIEWER", raising=False)
        monkeypatch.delenv("AEM_READINESS_REVIEW_DATE", raising=False)
        gate = ReadinessGate()
        result = gate.gate_check()
        assert result["status"] == "FAIL"

    def test_eight_local_checks_pass(self, monkeypatch):
        monkeypatch.delenv("AEM_READINESS_REVIEWER", raising=False)
        monkeypatch.delenv("AEM_READINESS_REVIEW_DATE", raising=False)
        gate = ReadinessGate()
        result = gate.gate_check()
        checks = result["checks"]
        config_keys = [k for k in checks if k.startswith(
            ("C-01","C-02","C-03","C-04","C-05","C-06","C-07","C-08")
        )]
        passed = sum(1 for k in config_keys if checks[k].get("ok"))
        assert passed == 8, f"Expected 8 local checks to pass, got {passed}: {checks}"

    def test_fail_reason_mentions_missing_env_vars(self, monkeypatch):
        monkeypatch.delenv("AEM_READINESS_REVIEWER", raising=False)
        monkeypatch.delenv("AEM_READINESS_REVIEW_DATE", raising=False)
        gate = ReadinessGate()
        result = gate.gate_check()
        assert "AEM_READINESS_REVIEWER" in result["fail_reason"]

    def test_fail_reason_mentions_production_ready_false(self, monkeypatch):
        monkeypatch.delenv("AEM_READINESS_REVIEWER", raising=False)
        monkeypatch.delenv("AEM_READINESS_REVIEW_DATE", raising=False)
        gate = ReadinessGate()
        result = gate.gate_check()
        assert "production_ready=false" in result["fail_reason"]


# ── Health endpoint ───────────────────────────────────────────────────────────

class TestHealthReadinessGate:
    def test_readiness_gate_in_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert "readiness_gate" in resp.json()

    def test_gate_has_required_fields(self, client):
        resp = client.get("/health")
        gate = resp.json()["readiness_gate"]
        assert gate["gate"] == "PRODUCTION_READINESS_GATE"
        assert "status" in gate
        assert gate["production_ready"] is False
        assert gate["gates_evidence_complete"] is True

    def test_version_bumped_to_pr13(self, client):
        resp = client.get("/health")
        assert resp.json()["version"] == "0.20.0-demo"
