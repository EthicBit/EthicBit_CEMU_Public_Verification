"""
Tests for v2.0 PR 14 — Governance Sign-Off Gate.

C-01–C-08 pass on file presence and content inspection (no live infra needed).
C-09–C-10 are skipped without AEM_GOVERNANCE_APPROVER / AEM_GOVERNANCE_SIGNOFF_DATE.
"""
import sys
from pathlib import Path

import pytest

DEMO_ROOT = Path(__file__).resolve().parents[1]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from governance_signoff.governance_signoff_gate import (
    GovernanceSignoffGate,
    _REQUIRED_REGULATORY_FILES,
    _REQUIRED_ASSURANCE_REPORTS,
    _REQUIRED_CLAIMS_TERMS,
    _EXPECTED_GATE_IDS,
    _GOVERNANCE_SIGNOFF_FILE,
    _GOVERNANCE_TOOLS_DIR,
)


# ── Gate construction ────────────────────────────────────────────────────────

class TestGovernanceSignoffGateInit:
    def test_from_env_returns_gate(self):
        gate = GovernanceSignoffGate.from_env()
        assert isinstance(gate, GovernanceSignoffGate)

    def test_no_approver_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_GOVERNANCE_APPROVER", raising=False)
        gate = GovernanceSignoffGate.from_env()
        assert gate._governance_approver is None

    def test_no_signoff_date_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_GOVERNANCE_SIGNOFF_DATE", raising=False)
        gate = GovernanceSignoffGate.from_env()
        assert gate._governance_signoff_date is None

    def test_captures_approver(self, monkeypatch):
        monkeypatch.setenv("AEM_GOVERNANCE_APPROVER", "gov-lead@example.com")
        gate = GovernanceSignoffGate.from_env()
        assert gate._governance_approver == "gov-lead@example.com"

    def test_captures_signoff_date(self, monkeypatch):
        monkeypatch.setenv("AEM_GOVERNANCE_SIGNOFF_DATE", "2026-06-01")
        gate = GovernanceSignoffGate.from_env()
        assert gate._governance_signoff_date == "2026-06-01"


# ── Constants ────────────────────────────────────────────────────────────────

class TestConstants:
    def test_three_regulatory_files(self):
        assert len(_REQUIRED_REGULATORY_FILES) == 3

    def test_eu_ai_act_in_regulatory_files(self):
        assert "EU_AI_ACT_MAPPING.json" in _REQUIRED_REGULATORY_FILES

    def test_iso_42001_in_regulatory_files(self):
        assert "ISO_42001_MAPPING.json" in _REQUIRED_REGULATORY_FILES

    def test_nist_ai_rmf_in_regulatory_files(self):
        assert "NIST_AI_RMF_MAPPING.json" in _REQUIRED_REGULATORY_FILES

    def test_nine_assurance_reports(self):
        assert len(_REQUIRED_ASSURANCE_REPORTS) == 9

    def test_production_readiness_report_in_required(self):
        assert "production_readiness_gate_report.json" in _REQUIRED_ASSURANCE_REPORTS

    def test_five_claims_terms(self):
        assert len(_REQUIRED_CLAIMS_TERMS) >= 5

    def test_non_claim_in_terms(self):
        assert "non-claim" in _REQUIRED_CLAIMS_TERMS

    def test_regulatory_in_terms(self):
        assert "regulatory" in _REQUIRED_CLAIMS_TERMS

    def test_eight_expected_gate_ids(self):
        assert len(_EXPECTED_GATE_IDS) == 8

    def test_monitoring_gate_id_in_expected(self):
        assert "MONITORING_ALERTING_CHECK" in _EXPECTED_GATE_IDS

    def test_disaster_recovery_gate_id_in_expected(self):
        assert "DISASTER_RECOVERY_CHECK" in _EXPECTED_GATE_IDS


# ── C-01: Governance sign-off document ──────────────────────────────────────

class TestSignoffDocument:
    def test_governance_signoff_file_exists(self):
        assert _GOVERNANCE_SIGNOFF_FILE.exists(), f"GOVERNANCE_SIGNOFF.md not found at {_GOVERNANCE_SIGNOFF_FILE}"

    def test_check_returns_ok(self):
        gate = GovernanceSignoffGate()
        result = gate.check_signoff_document()
        assert result["ok"] is True

    def test_check_has_sha256(self):
        gate = GovernanceSignoffGate()
        result = gate.check_signoff_document()
        assert len(result["sha256"]) == 64

    def test_signoff_doc_not_empty(self):
        gate = GovernanceSignoffGate()
        result = gate.check_signoff_document()
        assert result["size_bytes"] > 500


# ── C-02: Regulatory mapping documents ──────────────────────────────────────

class TestRegulatoryMappings:
    def test_check_returns_ok(self):
        gate = GovernanceSignoffGate()
        result = gate.check_regulatory_mappings()
        assert result["ok"] is True, result.get("missing_regulatory_files", "")

    def test_all_three_present(self):
        gate = GovernanceSignoffGate()
        result = gate.check_regulatory_mappings()
        assert result["regulatory_files_present"] == 3
        assert result["missing_regulatory_files"] == []

    def test_regulatory_files_required_count(self):
        gate = GovernanceSignoffGate()
        result = gate.check_regulatory_mappings()
        assert result["regulatory_files_required"] == 3


# ── C-03: All v2.0 assurance reports present ────────────────────────────────

class TestAssuranceReports:
    def test_check_returns_ok(self):
        gate = GovernanceSignoffGate()
        result = gate.check_assurance_reports()
        assert result["ok"] is True, result.get("missing_reports", "")

    def test_all_nine_present(self):
        gate = GovernanceSignoffGate()
        result = gate.check_assurance_reports()
        assert result["assurance_reports_present"] == 9
        assert result["missing_reports"] == []

    def test_assurance_reports_required_count(self):
        gate = GovernanceSignoffGate()
        result = gate.check_assurance_reports()
        assert result["assurance_reports_required"] == 9


# ── C-04: PR13 evidence complete ────────────────────────────────────────────

class TestPr13EvidenceComplete:
    def test_check_returns_ok(self):
        gate = GovernanceSignoffGate()
        result = gate.check_pr13_evidence_complete()
        assert result["ok"] is True, result.get("detail", "")

    def test_has_pr13_report(self):
        gate = GovernanceSignoffGate()
        result = gate.check_pr13_evidence_complete()
        assert result["has_pr13_report"] is True

    def test_gates_evidence_complete_true(self):
        gate = GovernanceSignoffGate()
        result = gate.check_pr13_evidence_complete()
        assert result["gates_evidence_complete"] is True


# ── C-05: Claims and non-claims document ────────────────────────────────────

class TestClaimsDocument:
    def test_check_returns_ok(self):
        gate = GovernanceSignoffGate()
        result = gate.check_claims_document()
        assert result["ok"] is True, result.get("missing_terms", "")

    def test_has_claims_doc(self):
        gate = GovernanceSignoffGate()
        result = gate.check_claims_document()
        assert result["has_claims_doc"] is True

    def test_no_missing_terms(self):
        gate = GovernanceSignoffGate()
        result = gate.check_claims_document()
        assert result["missing_terms"] == []

    def test_five_terms_required(self):
        gate = GovernanceSignoffGate()
        result = gate.check_claims_document()
        assert result["terms_required"] >= 5


# ── C-06: Sign-off evidence artifact ────────────────────────────────────────

class TestSignoffEvidence:
    def test_evidence_artifact_exists(self):
        artifacts = list(_GOVERNANCE_TOOLS_DIR.glob("governance_signoff_evidence_*.json"))
        assert len(artifacts) >= 1

    def test_check_returns_ok(self):
        gate = GovernanceSignoffGate()
        result = gate.check_signoff_evidence()
        assert result["ok"] is True, result.get("detail", "")

    def test_all_subjects_hashed(self):
        gate = GovernanceSignoffGate()
        result = gate.check_signoff_evidence()
        assert result["subjects_hashed"] == result["subjects_total"]
        assert result["subjects_hashed"] >= 15

    def test_has_artifact_sha256(self):
        gate = GovernanceSignoffGate()
        result = gate.check_signoff_evidence()
        assert result["has_artifact_sha256"] is True
        assert len(result["artifact_sha256"]) == 64


# ── C-07: Gate IDs verified ──────────────────────────────────────────────────

class TestGateIdsVerified:
    def test_check_returns_ok(self):
        gate = GovernanceSignoffGate()
        result = gate.check_gate_ids_verified()
        assert result["ok"] is True, result.get("missing_gate_ids", "")

    def test_all_eight_ids_verified(self):
        gate = GovernanceSignoffGate()
        result = gate.check_gate_ids_verified()
        assert result["gates_verified"] == 8
        assert result["missing_gate_ids"] == []

    def test_gates_required_count(self):
        gate = GovernanceSignoffGate()
        result = gate.check_gate_ids_verified()
        assert result["gates_required"] == 8


# ── C-08: Artifact fingerprint ───────────────────────────────────────────────

class TestArtifactFingerprint:
    def test_check_returns_ok(self):
        gate = GovernanceSignoffGate()
        result = gate.check_artifact_fingerprint()
        assert result["ok"] is True

    def test_has_artifact_sha256(self):
        gate = GovernanceSignoffGate()
        result = gate.check_artifact_fingerprint()
        assert result["has_artifact_sha256"] is True
        assert len(result["artifact_sha256"]) == 64


# ── C-09/C-10: Governance approver (skipped without env vars) ────────────────

class TestGovernanceApproverChecks:
    def test_approver_skipped_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_GOVERNANCE_APPROVER", raising=False)
        gate = GovernanceSignoffGate(governance_approver=None)
        result = gate.check_governance_approver()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_signoff_date_skipped_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_GOVERNANCE_SIGNOFF_DATE", raising=False)
        gate = GovernanceSignoffGate(governance_signoff_date=None)
        result = gate.check_governance_signoff_date()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_approver_passes_with_identity(self):
        gate = GovernanceSignoffGate(governance_approver="gov-lead@example.com")
        result = gate.check_governance_approver()
        assert result["ok"] is True
        assert result["governance_approver"] == "gov-lead@example.com"

    def test_signoff_date_passes_with_date(self):
        gate = GovernanceSignoffGate(governance_signoff_date="2026-06-01")
        result = gate.check_governance_signoff_date()
        assert result["ok"] is True
        assert result["governance_signoff_date"] == "2026-06-01"


# ── Full gate_check ───────────────────────────────────────────────────────────

class TestGateCheck:
    def test_gate_check_has_required_fields(self):
        gate = GovernanceSignoffGate()
        result = gate.gate_check()
        assert result["gate"] == "GOVERNANCE_SIGNOFF_CHECK"
        assert result["status"] in ("PASS", "FAIL")
        assert "checks_passed" in result
        assert "governance_signed_off" in result

    def test_governance_signed_off_false_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_GOVERNANCE_APPROVER", raising=False)
        monkeypatch.delenv("AEM_GOVERNANCE_SIGNOFF_DATE", raising=False)
        gate = GovernanceSignoffGate()
        result = gate.gate_check()
        assert result["governance_signed_off"] is False

    def test_governance_signed_off_false_with_only_approver(self):
        gate = GovernanceSignoffGate(governance_approver="gov-lead@example.com", governance_signoff_date=None)
        result = gate.gate_check()
        assert result["governance_signed_off"] is False

    def test_governance_signed_off_true_with_both(self):
        gate = GovernanceSignoffGate(
            governance_approver="gov-lead@example.com",
            governance_signoff_date="2026-06-01",
        )
        result = gate.gate_check()
        assert result["governance_signed_off"] is True

    def test_gate_fails_without_approver_vars(self, monkeypatch):
        monkeypatch.delenv("AEM_GOVERNANCE_APPROVER", raising=False)
        monkeypatch.delenv("AEM_GOVERNANCE_SIGNOFF_DATE", raising=False)
        gate = GovernanceSignoffGate()
        result = gate.gate_check()
        assert result["status"] == "FAIL"

    def test_eight_local_checks_pass(self, monkeypatch):
        monkeypatch.delenv("AEM_GOVERNANCE_APPROVER", raising=False)
        monkeypatch.delenv("AEM_GOVERNANCE_SIGNOFF_DATE", raising=False)
        gate = GovernanceSignoffGate()
        result = gate.gate_check()
        checks = result["checks"]
        config_keys = [k for k in checks if k.startswith(
            ("C-01", "C-02", "C-03", "C-04", "C-05", "C-06", "C-07", "C-08")
        )]
        passed = sum(1 for k in config_keys if checks[k].get("ok"))
        assert passed == 8, f"Expected 8 local checks to pass, got {passed}: {checks}"

    def test_gate_passes_with_approver_vars(self):
        gate = GovernanceSignoffGate(
            governance_approver="gov-lead@example.com",
            governance_signoff_date="2026-06-01",
        )
        result = gate.gate_check()
        assert result["status"] == "PASS"
        assert result["checks_passed"] == 10

    def test_fail_reason_mentions_missing_env_vars(self, monkeypatch):
        monkeypatch.delenv("AEM_GOVERNANCE_APPROVER", raising=False)
        monkeypatch.delenv("AEM_GOVERNANCE_SIGNOFF_DATE", raising=False)
        gate = GovernanceSignoffGate()
        result = gate.gate_check()
        assert "AEM_GOVERNANCE_APPROVER" in result["fail_reason"]

    def test_fail_reason_mentions_governance_signed_off_false(self, monkeypatch):
        monkeypatch.delenv("AEM_GOVERNANCE_APPROVER", raising=False)
        monkeypatch.delenv("AEM_GOVERNANCE_SIGNOFF_DATE", raising=False)
        gate = GovernanceSignoffGate()
        result = gate.gate_check()
        assert "governance_signed_off=false" in result["fail_reason"]


# ── Health endpoint ───────────────────────────────────────────────────────────

class TestHealthGovernanceSignoffGate:
    def test_governance_signoff_gate_in_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert "governance_signoff_gate" in resp.json()

    def test_gate_has_required_fields(self, client):
        resp = client.get("/health")
        gate = resp.json()["governance_signoff_gate"]
        assert gate["gate"] == "GOVERNANCE_SIGNOFF_CHECK"
        assert "status" in gate
        assert gate["governance_signed_off"] is False

    def test_version_bumped_to_pr14(self, client):
        resp = client.get("/health")
        assert resp.json()["version"] == "0.21.0-demo"
