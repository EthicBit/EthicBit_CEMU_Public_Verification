"""
Tests for v2.0 PR 10 — SLO evidence gate.

C-01–C-08 pass on file presence and content inspection (no live infra needed).
C-09–C-10 are skipped without AEM_SLO_REVIEWER / AEM_SLO_REVIEW_DATE.
"""
import sys
from pathlib import Path

import pytest

DEMO_ROOT = Path(__file__).resolve().parents[1]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from slo.slo_gate import (
    SLOGate,
    _REQUIRED_SLO_DIMENSIONS,
    _REQUIRED_GATES,
    _REQUIRED_METHODOLOGY_TERMS,
    _REQUIRED_BURN_RATE_TERMS,
    _SLO_FILE,
    _SLO_TOOLS_DIR,
)


# ── Gate construction ────────────────────────────────────────────────────────

class TestSLOGateInit:
    def test_from_env_returns_gate(self):
        gate = SLOGate.from_env()
        assert isinstance(gate, SLOGate)

    def test_no_reviewer_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_SLO_REVIEWER", raising=False)
        gate = SLOGate.from_env()
        assert gate._slo_reviewer is None

    def test_no_review_date_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_SLO_REVIEW_DATE", raising=False)
        gate = SLOGate.from_env()
        assert gate._slo_review_date is None

    def test_captures_reviewer(self, monkeypatch):
        monkeypatch.setenv("AEM_SLO_REVIEWER", "slo-team@example.com")
        gate = SLOGate.from_env()
        assert gate._slo_reviewer == "slo-team@example.com"

    def test_captures_review_date(self, monkeypatch):
        monkeypatch.setenv("AEM_SLO_REVIEW_DATE", "2026-06-01")
        gate = SLOGate.from_env()
        assert gate._slo_review_date == "2026-06-01"


# ── Constants ────────────────────────────────────────────────────────────────

class TestConstants:
    def test_four_slo_dimensions(self):
        assert len(_REQUIRED_SLO_DIMENSIONS) == 4

    def test_availability_in_dimensions(self):
        assert "availability" in _REQUIRED_SLO_DIMENSIONS

    def test_governance_gate_pass_rate_in_dimensions(self):
        assert "governance_gate_pass_rate" in _REQUIRED_SLO_DIMENSIONS

    def test_nine_required_gates(self):
        assert len(_REQUIRED_GATES) == 9

    def test_pr9_in_required_gates(self):
        assert "PR9" in _REQUIRED_GATES

    def test_four_methodology_terms(self):
        assert len(_REQUIRED_METHODOLOGY_TERMS) >= 4

    def test_prometheus_in_methodology_terms(self):
        assert any("prometheus" in t.lower() for t in _REQUIRED_METHODOLOGY_TERMS)

    def test_burn_rate_terms_include_fast_slow(self):
        assert any("fast" in t for t in _REQUIRED_BURN_RATE_TERMS)
        assert any("slow" in t for t in _REQUIRED_BURN_RATE_TERMS)


# ── C-01: SLO document ───────────────────────────────────────────────────────

class TestSLODocument:
    def test_slo_file_exists(self):
        assert _SLO_FILE.exists(), f"SLO.md not found at {_SLO_FILE}"

    def test_check_returns_ok(self):
        gate = SLOGate()
        result = gate.check_slo_document()
        assert result["ok"] is True

    def test_check_has_sha256(self):
        gate = SLOGate()
        result = gate.check_slo_document()
        assert len(result["sha256"]) == 64

    def test_slo_document_not_empty(self):
        gate = SLOGate()
        result = gate.check_slo_document()
        assert result["size_bytes"] > 500


# ── C-02: SLO targets ────────────────────────────────────────────────────────

class TestSLOTargets:
    def test_check_returns_ok(self):
        gate = SLOGate()
        result = gate.check_slo_targets()
        assert result["ok"] is True

    def test_all_four_dimensions_present(self):
        gate = SLOGate()
        result = gate.check_slo_targets()
        assert result["dimensions_present"] == 4
        assert result["missing_dimensions"] == []

    def test_dimensions_required_count(self):
        gate = SLOGate()
        result = gate.check_slo_targets()
        assert result["dimensions_required"] == 4


# ── C-03: Error budgets ──────────────────────────────────────────────────────

class TestErrorBudgets:
    def test_check_returns_ok(self):
        gate = SLOGate()
        result = gate.check_error_budgets()
        assert result["ok"] is True

    def test_has_budget_table(self):
        gate = SLOGate()
        result = gate.check_error_budgets()
        assert result["has_budget_table"] is True

    def test_has_burn_threshold(self):
        gate = SLOGate()
        result = gate.check_error_budgets()
        assert result["has_burn_threshold"] is True

    def test_no_missing_fields(self):
        gate = SLOGate()
        result = gate.check_error_budgets()
        assert result["missing_fields"] == []


# ── C-04: Burn rate alerts ───────────────────────────────────────────────────

class TestBurnRateAlerts:
    def test_check_returns_ok(self):
        gate = SLOGate()
        result = gate.check_burn_rate_alerts()
        assert result["ok"] is True

    def test_has_fast_burn(self):
        gate = SLOGate()
        result = gate.check_burn_rate_alerts()
        assert result["has_fast_burn"] is True

    def test_has_slow_burn(self):
        gate = SLOGate()
        result = gate.check_burn_rate_alerts()
        assert result["has_slow_burn"] is True

    def test_no_missing_terms(self):
        gate = SLOGate()
        result = gate.check_burn_rate_alerts()
        assert result["missing_terms"] == []


# ── C-05: Measurement methodology ───────────────────────────────────────────

class TestMeasurementMethodology:
    def test_check_returns_ok(self):
        gate = SLOGate()
        result = gate.check_measurement_methodology()
        assert result["ok"] is True

    def test_has_methodology_section(self):
        gate = SLOGate()
        result = gate.check_measurement_methodology()
        assert result["has_methodology_section"] is True

    def test_has_counter_mapping(self):
        gate = SLOGate()
        result = gate.check_measurement_methodology()
        assert result["has_counter_mapping"] is True

    def test_no_missing_methodology_terms(self):
        gate = SLOGate()
        result = gate.check_measurement_methodology()
        assert result["missing_terms"] == []


# ── C-06: Governance gate coverage ──────────────────────────────────────────

class TestGovernanceGateCoverage:
    def test_check_returns_ok(self):
        gate = SLOGate()
        result = gate.check_governance_gate_coverage()
        assert result["ok"] is True

    def test_all_nine_gates_covered(self):
        gate = SLOGate()
        result = gate.check_governance_gate_coverage()
        assert result["gates_covered"] == 9
        assert result["missing_gates"] == []

    def test_gates_required_count(self):
        gate = SLOGate()
        result = gate.check_governance_gate_coverage()
        assert result["gates_required"] == 9


# ── C-07: SLO evidence artifact ─────────────────────────────────────────────

class TestSLOEvidenceArtifact:
    def test_evidence_artifact_exists(self):
        artifacts = list(_SLO_TOOLS_DIR.glob("slo_evidence_*.json"))
        assert len(artifacts) >= 1

    def test_check_returns_ok(self):
        gate = SLOGate()
        result = gate.check_slo_evidence_artifact()
        assert result["ok"] is True, result.get("detail", "")

    def test_all_subjects_hashed(self):
        gate = SLOGate()
        result = gate.check_slo_evidence_artifact()
        assert result["subjects_hashed"] == result["subjects_total"]
        assert result["subjects_hashed"] >= 15

    def test_covers_pr1_through_pr9(self):
        gate = SLOGate()
        result = gate.check_slo_evidence_artifact()
        assert "PR1" in result["gate_coverage"]
        assert "PR9" in result["gate_coverage"]

    def test_artifact_has_sha256(self):
        gate = SLOGate()
        result = gate.check_slo_evidence_artifact()
        assert result["has_artifact_sha256"] is True
        assert len(result["artifact_sha256"]) == 64

    def test_artifact_file_sha256(self):
        gate = SLOGate()
        result = gate.check_slo_evidence_artifact()
        assert len(result["sha256"]) == 64


# ── C-08: Artifact fingerprint ───────────────────────────────────────────────

class TestArtifactFingerprint:
    def test_check_returns_ok(self):
        gate = SLOGate()
        result = gate.check_artifact_fingerprint()
        assert result["ok"] is True

    def test_has_artifact_sha256(self):
        gate = SLOGate()
        result = gate.check_artifact_fingerprint()
        assert result["has_artifact_sha256"] is True
        assert len(result["artifact_sha256"]) == 64


# ── C-09/C-10: External SLO review (skipped without env vars) ────────────────

class TestExternalSLOReviewChecks:
    def test_reviewer_skipped_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_SLO_REVIEWER", raising=False)
        gate = SLOGate(slo_reviewer=None)
        result = gate.check_slo_reviewer()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_review_date_skipped_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_SLO_REVIEW_DATE", raising=False)
        gate = SLOGate(slo_review_date=None)
        result = gate.check_slo_review_date()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_reviewer_passes_with_identity(self):
        gate = SLOGate(slo_reviewer="slo-team@example.com")
        result = gate.check_slo_reviewer()
        assert result["ok"] is True
        assert result["slo_reviewer"] == "slo-team@example.com"

    def test_review_date_passes_with_date(self):
        gate = SLOGate(slo_review_date="2026-06-01")
        result = gate.check_slo_review_date()
        assert result["ok"] is True
        assert result["slo_review_date"] == "2026-06-01"


# ── Full gate_check ───────────────────────────────────────────────────────────

class TestGateCheck:
    def test_gate_check_has_required_fields(self):
        gate = SLOGate()
        result = gate.gate_check()
        assert result["gate"] == "SLO_EVIDENCE_CHECK"
        assert result["status"] in ("PASS", "FAIL")
        assert "checks_passed" in result
        assert "slo_evidence_verified" in result

    def test_slo_evidence_verified_false_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_SLO_REVIEWER", raising=False)
        monkeypatch.delenv("AEM_SLO_REVIEW_DATE", raising=False)
        gate = SLOGate()
        result = gate.gate_check()
        assert result["slo_evidence_verified"] is False

    def test_slo_evidence_verified_false_with_only_reviewer(self):
        gate = SLOGate(slo_reviewer="slo-team@example.com", slo_review_date=None)
        result = gate.gate_check()
        assert result["slo_evidence_verified"] is False

    def test_slo_evidence_verified_true_with_both(self):
        gate = SLOGate(slo_reviewer="slo-team@example.com", slo_review_date="2026-06-01")
        result = gate.gate_check()
        assert result["slo_evidence_verified"] is True

    def test_gate_fails_without_review_vars(self, monkeypatch):
        monkeypatch.delenv("AEM_SLO_REVIEWER", raising=False)
        monkeypatch.delenv("AEM_SLO_REVIEW_DATE", raising=False)
        gate = SLOGate()
        result = gate.gate_check()
        assert result["status"] == "FAIL"

    def test_eight_local_checks_pass(self, monkeypatch):
        monkeypatch.delenv("AEM_SLO_REVIEWER", raising=False)
        monkeypatch.delenv("AEM_SLO_REVIEW_DATE", raising=False)
        gate = SLOGate()
        result = gate.gate_check()
        checks = result["checks"]
        config_keys = [k for k in checks if k.startswith(
            ("C-01", "C-02", "C-03", "C-04", "C-05", "C-06", "C-07", "C-08")
        )]
        passed = sum(1 for k in config_keys if checks[k].get("ok"))
        assert passed == 8, f"Expected 8 local checks to pass, got {passed}: {checks}"

    def test_gate_passes_with_review_vars(self):
        gate = SLOGate(
            slo_reviewer="slo-team@example.com",
            slo_review_date="2026-06-01",
        )
        result = gate.gate_check()
        assert result["status"] == "PASS"
        assert result["checks_passed"] == 10

    def test_fail_reason_mentions_missing_env_vars(self, monkeypatch):
        monkeypatch.delenv("AEM_SLO_REVIEWER", raising=False)
        monkeypatch.delenv("AEM_SLO_REVIEW_DATE", raising=False)
        gate = SLOGate()
        result = gate.gate_check()
        assert "AEM_SLO_REVIEWER" in result["fail_reason"]

    def test_fail_reason_mentions_slo_evidence_verified_false(self, monkeypatch):
        monkeypatch.delenv("AEM_SLO_REVIEWER", raising=False)
        monkeypatch.delenv("AEM_SLO_REVIEW_DATE", raising=False)
        gate = SLOGate()
        result = gate.gate_check()
        assert "slo_evidence_verified=false" in result["fail_reason"]


# ── Health endpoint ───────────────────────────────────────────────────────────

class TestHealthSLOGate:
    def test_slo_gate_in_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert "slo_gate" in resp.json()

    def test_gate_has_required_fields(self, client):
        resp = client.get("/health")
        gate = resp.json()["slo_gate"]
        assert gate["gate"] == "SLO_EVIDENCE_CHECK"
        assert "status" in gate
        assert gate["slo_evidence_verified"] is False

    def test_version_bumped_to_pr10(self, client):
        resp = client.get("/health")
        assert resp.json()["version"] == "0.17.0-demo"
