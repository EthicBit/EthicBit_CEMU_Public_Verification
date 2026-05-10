"""
Tests for v2.0 PR 7 — Security review evidence gate.

C-01–C-08 pass based on file presence, content, and real scan artifacts.
C-09–C-10 are skipped without AEM_SECURITY_REVIEWER / AEM_SECURITY_REVIEW_DATE.
"""
import sys
from pathlib import Path

import pytest

DEMO_ROOT = Path(__file__).resolve().parents[1]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from security_review.security_review_gate import (
    SecurityReviewGate,
    _REQUIRED_CONTROLS,
    _REQUIRED_OWASP_ITEMS,
    _SECURITY_REVIEW_FILE,
    _THREAT_MODEL_FILE,
    _SECURITY_DIR,
)


# ── Gate construction ────────────────────────────────────────────────────────

class TestSecurityReviewGateInit:
    def test_from_env_returns_gate(self):
        gate = SecurityReviewGate.from_env()
        assert isinstance(gate, SecurityReviewGate)

    def test_no_reviewer_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_SECURITY_REVIEWER", raising=False)
        gate = SecurityReviewGate.from_env()
        assert gate._security_reviewer is None

    def test_no_review_date_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_SECURITY_REVIEW_DATE", raising=False)
        gate = SecurityReviewGate.from_env()
        assert gate._security_review_date is None

    def test_captures_reviewer(self, monkeypatch):
        monkeypatch.setenv("AEM_SECURITY_REVIEWER", "external-sec@example.com")
        gate = SecurityReviewGate.from_env()
        assert gate._security_reviewer == "external-sec@example.com"

    def test_captures_review_date(self, monkeypatch):
        monkeypatch.setenv("AEM_SECURITY_REVIEW_DATE", "2026-06-01")
        gate = SecurityReviewGate.from_env()
        assert gate._security_review_date == "2026-06-01"


# ── Constants ────────────────────────────────────────────────────────────────

class TestConstants:
    def test_seven_required_controls(self):
        assert len(_REQUIRED_CONTROLS) == 7

    def test_hitl_in_required_controls(self):
        assert any("HITL" in c for c in _REQUIRED_CONTROLS)

    def test_kms_in_required_controls(self):
        assert any("KMS" in c for c in _REQUIRED_CONTROLS)

    def test_owasp_items_include_auth(self):
        assert "API2" in _REQUIRED_OWASP_ITEMS


# ── C-01: Security review document ──────────────────────────────────────────

class TestReviewDocument:
    def test_security_review_file_exists(self):
        assert _SECURITY_REVIEW_FILE.exists()

    def test_check_returns_ok(self):
        gate = SecurityReviewGate()
        result = gate.check_review_document()
        assert result["ok"] is True

    def test_check_has_sha256(self):
        gate = SecurityReviewGate()
        result = gate.check_review_document()
        assert len(result["sha256"]) == 64

    def test_review_document_not_empty(self):
        gate = SecurityReviewGate()
        result = gate.check_review_document()
        assert result["size_bytes"] > 500


# ── C-02: Threat model ───────────────────────────────────────────────────────

class TestThreatModel:
    def test_threat_model_file_exists(self):
        assert _THREAT_MODEL_FILE.exists()

    def test_check_returns_ok(self):
        gate = SecurityReviewGate()
        result = gate.check_threat_model()
        assert result["ok"] is True

    def test_no_missing_threats(self):
        gate = SecurityReviewGate()
        result = gate.check_threat_model()
        assert result["missing_threats"] == []

    def test_threat_model_has_sha256(self):
        gate = SecurityReviewGate()
        result = gate.check_threat_model()
        assert len(result["sha256"]) == 64


# ── C-03: Controls coverage ──────────────────────────────────────────────────

class TestControlsCoverage:
    def test_check_returns_ok(self):
        gate = SecurityReviewGate()
        result = gate.check_controls_coverage()
        assert result["ok"] is True

    def test_all_seven_controls_present(self):
        gate = SecurityReviewGate()
        result = gate.check_controls_coverage()
        assert result["controls_present"] == 7
        assert result["missing_controls"] == []


# ── C-04: Dependency scan ────────────────────────────────────────────────────

class TestDependencyScan:
    def test_dep_scan_artifact_exists(self):
        artifacts = list(_SECURITY_DIR.glob("dependency_scan_*.json"))
        assert len(artifacts) >= 1

    def test_check_returns_ok(self):
        gate = SecurityReviewGate()
        result = gate.check_dependency_scan()
        assert result["ok"] is True, result.get("detail", "")

    def test_zero_vulnerabilities(self):
        gate = SecurityReviewGate()
        result = gate.check_dependency_scan()
        assert result["vulnerabilities_found"] == 0

    def test_dependencies_scanned(self):
        gate = SecurityReviewGate()
        result = gate.check_dependency_scan()
        assert result["dependencies_scanned"] > 0

    def test_scan_result_clean(self):
        gate = SecurityReviewGate()
        result = gate.check_dependency_scan()
        assert result["scan_result"] == "CLEAN"


# ── C-05: Static analysis ────────────────────────────────────────────────────

class TestStaticAnalysis:
    def test_static_analysis_artifact_exists(self):
        artifacts = list(_SECURITY_DIR.glob("static_analysis_*.json"))
        assert len(artifacts) >= 1

    def test_check_returns_ok(self):
        gate = SecurityReviewGate()
        result = gate.check_static_analysis()
        assert result["ok"] is True, result.get("detail", "")

    def test_zero_high_severity_findings(self):
        gate = SecurityReviewGate()
        result = gate.check_static_analysis()
        assert result["issues_high"] == 0

    def test_scan_result_pass(self):
        gate = SecurityReviewGate()
        result = gate.check_static_analysis()
        assert "PASS" in result["scan_result"]

    def test_production_blocking_zero(self):
        gate = SecurityReviewGate()
        result = gate.check_static_analysis()
        assert result["production_blocking"] == 0


# ── C-06: OWASP coverage ─────────────────────────────────────────────────────

class TestOwaspCoverage:
    def test_check_returns_ok(self):
        gate = SecurityReviewGate()
        result = gate.check_owasp_coverage()
        assert result["ok"] is True

    def test_all_required_owasp_items_present(self):
        gate = SecurityReviewGate()
        result = gate.check_owasp_coverage()
        assert result["missing_items"] == []


# ── C-07: Findings documented ────────────────────────────────────────────────

class TestFindingsDocumented:
    def test_check_returns_ok(self):
        gate = SecurityReviewGate()
        result = gate.check_findings_documented()
        assert result["ok"] is True

    def test_has_findings_table(self):
        gate = SecurityReviewGate()
        result = gate.check_findings_documented()
        assert result["has_findings_table"] is True

    def test_has_known_limitations(self):
        gate = SecurityReviewGate()
        result = gate.check_findings_documented()
        assert result["has_known_limitations"] is True

    def test_has_mitigations(self):
        gate = SecurityReviewGate()
        result = gate.check_findings_documented()
        assert result["has_mitigations"] is True


# ── C-08: Artifact fingerprints ──────────────────────────────────────────────

class TestArtifactFingerprints:
    def test_check_returns_ok(self):
        gate = SecurityReviewGate()
        result = gate.check_artifact_fingerprints()
        assert result["ok"] is True

    def test_both_artifacts_have_sha256(self):
        gate = SecurityReviewGate()
        result = gate.check_artifact_fingerprints()
        for label, artifact in result["artifacts"].items():
            assert artifact.get("has_sha256") is True, f"{label} missing sha256"


# ── C-09/C-10: External review (skipped without env vars) ────────────────────

class TestExternalReviewChecks:
    def test_reviewer_skipped_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_SECURITY_REVIEWER", raising=False)
        gate = SecurityReviewGate(security_reviewer=None)
        result = gate.check_external_reviewer()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_review_date_skipped_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_SECURITY_REVIEW_DATE", raising=False)
        gate = SecurityReviewGate(security_review_date=None)
        result = gate.check_review_date()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_reviewer_passes_with_identity(self):
        gate = SecurityReviewGate(security_reviewer="sec@example.com")
        result = gate.check_external_reviewer()
        assert result["ok"] is True

    def test_review_date_passes_with_date(self):
        gate = SecurityReviewGate(security_review_date="2026-06-01")
        result = gate.check_review_date()
        assert result["ok"] is True


# ── Full gate_check ───────────────────────────────────────────────────────────

class TestGateCheck:
    def test_gate_check_has_required_fields(self):
        gate = SecurityReviewGate()
        result = gate.gate_check()
        assert result["gate"] == "SECURITY_REVIEW_CHECK"
        assert result["status"] in ("PASS", "FAIL")
        assert "checks_passed" in result
        assert "checks" in result

    def test_gate_fails_without_external_review(self, monkeypatch):
        monkeypatch.delenv("AEM_SECURITY_REVIEWER", raising=False)
        monkeypatch.delenv("AEM_SECURITY_REVIEW_DATE", raising=False)
        gate = SecurityReviewGate()
        result = gate.gate_check()
        assert result["status"] == "FAIL"

    def test_eight_config_checks_pass(self, monkeypatch):
        monkeypatch.delenv("AEM_SECURITY_REVIEWER", raising=False)
        monkeypatch.delenv("AEM_SECURITY_REVIEW_DATE", raising=False)
        gate = SecurityReviewGate()
        result = gate.gate_check()
        checks = result["checks"]
        config_keys = [k for k in checks if k.startswith(
            ("C-01", "C-02", "C-03", "C-04", "C-05", "C-06", "C-07", "C-08")
        )]
        passed = sum(1 for k in config_keys if checks[k].get("ok"))
        assert passed == 8, f"Expected 8 config checks to pass, got {passed}: {checks}"

    def test_gate_passes_with_external_review_vars(self):
        gate = SecurityReviewGate(
            security_reviewer="external-sec@example.com",
            security_review_date="2026-06-01",
        )
        result = gate.gate_check()
        assert result["status"] == "PASS"
        assert result["checks_passed"] == 10

    def test_fail_reason_mentions_missing_env_vars(self, monkeypatch):
        monkeypatch.delenv("AEM_SECURITY_REVIEWER", raising=False)
        monkeypatch.delenv("AEM_SECURITY_REVIEW_DATE", raising=False)
        gate = SecurityReviewGate()
        result = gate.gate_check()
        assert "AEM_SECURITY_REVIEWER" in result["fail_reason"]


# ── Health endpoint ───────────────────────────────────────────────────────────

class TestHealthSecurityReviewGate:
    def test_security_review_gate_in_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert "security_review_gate" in resp.json()

    def test_gate_has_required_fields(self, client):
        resp = client.get("/health")
        gate = resp.json()["security_review_gate"]
        assert gate["gate"] == "SECURITY_REVIEW_CHECK"
        assert "status" in gate

    def test_version_bumped_to_pr7(self, client):
        resp = client.get("/health")
        assert resp.json()["version"] == "0.21.0-demo"
