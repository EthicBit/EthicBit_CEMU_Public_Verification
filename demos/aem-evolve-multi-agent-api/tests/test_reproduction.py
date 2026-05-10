"""
Tests for v2.0 PR 8 — External reproduction report evidence gate.

C-01–C-08 pass based on file presence, content, and real checksum artifact.
C-09–C-10 are skipped without AEM_REPRODUCER_ID / AEM_REPRODUCTION_DATE.
"""
import sys
from pathlib import Path

import pytest

DEMO_ROOT = Path(__file__).resolve().parents[1]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from reproduction.reproduction_gate import (
    ReproductionGate,
    _REQUIRED_PR_COVERAGE,
    _REQUIRED_OUTCOMES,
    _REQUIRED_HITL_TERMS,
    _REQUIRED_CHAIN_TERMS,
    _REPRO_REPORT_V2,
    _REPRO_CHALLENGE,
    _REPRO_TOOLS_DIR,
)


# ── Gate construction ────────────────────────────────────────────────────────

class TestReproductionGateInit:
    def test_from_env_returns_gate(self):
        gate = ReproductionGate.from_env()
        assert isinstance(gate, ReproductionGate)

    def test_no_reproducer_id_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_REPRODUCER_ID", raising=False)
        gate = ReproductionGate.from_env()
        assert gate._reproducer_id is None

    def test_no_reproduction_date_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_REPRODUCTION_DATE", raising=False)
        gate = ReproductionGate.from_env()
        assert gate._reproduction_date is None

    def test_captures_reproducer_id(self, monkeypatch):
        monkeypatch.setenv("AEM_REPRODUCER_ID", "external-org@example.com")
        gate = ReproductionGate.from_env()
        assert gate._reproducer_id == "external-org@example.com"

    def test_captures_reproduction_date(self, monkeypatch):
        monkeypatch.setenv("AEM_REPRODUCTION_DATE", "2026-06-15")
        gate = ReproductionGate.from_env()
        assert gate._reproduction_date == "2026-06-15"


# ── Constants ────────────────────────────────────────────────────────────────

class TestConstants:
    def test_seven_prs_required(self):
        assert len(_REQUIRED_PR_COVERAGE) == 7

    def test_three_outcomes_required(self):
        assert len(_REQUIRED_OUTCOMES) == 3

    def test_outcomes_include_all_paths(self):
        assert "PASS" in _REQUIRED_OUTCOMES
        assert "SCOPE_LIMITED" in _REQUIRED_OUTCOMES
        assert "FAIL_CLOSED" in _REQUIRED_OUTCOMES

    def test_pr1_through_pr7_covered(self):
        for i in range(1, 8):
            assert f"PR{i}" in _REQUIRED_PR_COVERAGE

    def test_hitl_terms_include_replay(self):
        assert any("replay" in t for t in _REQUIRED_HITL_TERMS)

    def test_chain_terms_include_tamper(self):
        assert any("tamper" in t for t in _REQUIRED_CHAIN_TERMS)


# ── C-01: v2.0 reproduction report ──────────────────────────────────────────

class TestReportV2:
    def test_report_file_exists(self):
        assert _REPRO_REPORT_V2.exists(), f"REPRODUCTION_REPORT_V2.md not found at {_REPRO_REPORT_V2}"

    def test_check_returns_ok(self):
        gate = ReproductionGate()
        result = gate.check_report_v2()
        assert result["ok"] is True

    def test_check_has_sha256(self):
        gate = ReproductionGate()
        result = gate.check_report_v2()
        assert len(result["sha256"]) == 64

    def test_report_not_empty(self):
        gate = ReproductionGate()
        result = gate.check_report_v2()
        assert result["size_bytes"] > 1000


# ── C-02: Challenge document ─────────────────────────────────────────────────

class TestChallengeDoc:
    def test_challenge_doc_exists(self):
        assert _REPRO_CHALLENGE.exists()

    def test_check_returns_ok(self):
        gate = ReproductionGate()
        result = gate.check_challenge_doc()
        assert result["ok"] is True

    def test_challenge_has_sha256(self):
        gate = ReproductionGate()
        result = gate.check_challenge_doc()
        assert len(result["sha256"]) == 64


# ── C-03: PR coverage ────────────────────────────────────────────────────────

class TestPrCoverage:
    def test_check_returns_ok(self):
        gate = ReproductionGate()
        result = gate.check_pr_coverage()
        assert result["ok"] is True

    def test_all_seven_prs_covered(self):
        gate = ReproductionGate()
        result = gate.check_pr_coverage()
        assert result["prs_covered"] == 7
        assert result["missing_prs"] == []


# ── C-04: Outcome coverage ───────────────────────────────────────────────────

class TestOutcomeCoverage:
    def test_check_returns_ok(self):
        gate = ReproductionGate()
        result = gate.check_outcome_coverage()
        assert result["ok"] is True

    def test_all_three_outcomes_covered(self):
        gate = ReproductionGate()
        result = gate.check_outcome_coverage()
        assert result["outcomes_covered"] == 3
        assert result["missing_outcomes"] == []


# ── C-05: Evidence artifact ──────────────────────────────────────────────────

class TestEvidenceArtifact:
    def test_evidence_artifact_exists(self):
        artifacts = list(_REPRO_TOOLS_DIR.glob("reproduction_evidence_v2_*.json"))
        assert len(artifacts) >= 1

    def test_check_returns_ok(self):
        gate = ReproductionGate()
        result = gate.check_evidence_artifact()
        assert result["ok"] is True, result.get("detail", "")

    def test_all_subjects_hashed(self):
        gate = ReproductionGate()
        result = gate.check_evidence_artifact()
        assert result["subjects_hashed"] == result["subjects_total"]
        assert result["subjects_hashed"] >= 15

    def test_covers_pr1_through_pr7(self):
        gate = ReproductionGate()
        result = gate.check_evidence_artifact()
        assert "PR1" in result["pr_coverage"]
        assert "PR7" in result["pr_coverage"]

    def test_artifact_has_sha256(self):
        gate = ReproductionGate()
        result = gate.check_evidence_artifact()
        assert len(result["sha256"]) == 64


# ── C-06: HITL coverage ──────────────────────────────────────────────────────

class TestHitlCoverage:
    def test_check_returns_ok(self):
        gate = ReproductionGate()
        result = gate.check_hitl_coverage()
        assert result["ok"] is True

    def test_all_hitl_terms_present(self):
        gate = ReproductionGate()
        result = gate.check_hitl_coverage()
        assert result["missing_terms"] == []


# ── C-07: Audit chain coverage ───────────────────────────────────────────────

class TestChainCoverage:
    def test_check_returns_ok(self):
        gate = ReproductionGate()
        result = gate.check_chain_coverage()
        assert result["ok"] is True

    def test_all_chain_terms_present(self):
        gate = ReproductionGate()
        result = gate.check_chain_coverage()
        assert result["missing_terms"] == []


# ── C-08: Artifact fingerprint ───────────────────────────────────────────────

class TestArtifactFingerprint:
    def test_check_returns_ok(self):
        gate = ReproductionGate()
        result = gate.check_artifact_fingerprint()
        assert result["ok"] is True

    def test_has_artifact_sha256(self):
        gate = ReproductionGate()
        result = gate.check_artifact_fingerprint()
        assert result["has_artifact_sha256"] is True
        assert len(result["artifact_sha256"]) == 64


# ── C-09/C-10: External reproduction (skipped without env vars) ───────────────

class TestExternalReproductionChecks:
    def test_reproducer_id_skipped_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_REPRODUCER_ID", raising=False)
        gate = ReproductionGate(reproducer_id=None)
        result = gate.check_reproducer_id()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_reproduction_date_skipped_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_REPRODUCTION_DATE", raising=False)
        gate = ReproductionGate(reproduction_date=None)
        result = gate.check_reproduction_date()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_reproducer_id_passes_with_identity(self):
        gate = ReproductionGate(reproducer_id="external@example.com")
        result = gate.check_reproducer_id()
        assert result["ok"] is True

    def test_reproduction_date_passes_with_date(self):
        gate = ReproductionGate(reproduction_date="2026-06-15")
        result = gate.check_reproduction_date()
        assert result["ok"] is True


# ── Full gate_check ───────────────────────────────────────────────────────────

class TestGateCheck:
    def test_gate_check_has_required_fields(self):
        gate = ReproductionGate()
        result = gate.gate_check()
        assert result["gate"] == "EXTERNAL_REPRODUCTION_CHECK"
        assert result["status"] in ("PASS", "FAIL")
        assert "checks_passed" in result
        assert "independent_reproduction_claimed" in result

    def test_independent_reproduction_never_claimed(self):
        gate = ReproductionGate()
        result = gate.gate_check()
        assert result["independent_reproduction_claimed"] is False

    def test_gate_fails_without_external_evidence(self, monkeypatch):
        monkeypatch.delenv("AEM_REPRODUCER_ID", raising=False)
        monkeypatch.delenv("AEM_REPRODUCTION_DATE", raising=False)
        gate = ReproductionGate()
        result = gate.gate_check()
        assert result["status"] == "FAIL"

    def test_eight_local_checks_pass(self, monkeypatch):
        monkeypatch.delenv("AEM_REPRODUCER_ID", raising=False)
        monkeypatch.delenv("AEM_REPRODUCTION_DATE", raising=False)
        gate = ReproductionGate()
        result = gate.gate_check()
        checks = result["checks"]
        config_keys = [k for k in checks if k.startswith(
            ("C-01", "C-02", "C-03", "C-04", "C-05", "C-06", "C-07", "C-08")
        )]
        passed = sum(1 for k in config_keys if checks[k].get("ok"))
        assert passed == 8, f"Expected 8 local checks to pass, got {passed}: {checks}"

    def test_gate_passes_with_external_vars(self):
        gate = ReproductionGate(
            reproducer_id="external-org@example.com",
            reproduction_date="2026-06-15",
        )
        result = gate.gate_check()
        assert result["status"] == "PASS"
        assert result["checks_passed"] == 10

    def test_fail_reason_mentions_independent_reproduction(self, monkeypatch):
        monkeypatch.delenv("AEM_REPRODUCER_ID", raising=False)
        monkeypatch.delenv("AEM_REPRODUCTION_DATE", raising=False)
        gate = ReproductionGate()
        result = gate.gate_check()
        assert "AEM_REPRODUCER_ID" in result["fail_reason"]


# ── Health endpoint ───────────────────────────────────────────────────────────

class TestHealthReproductionGate:
    def test_reproduction_gate_in_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert "reproduction_gate" in resp.json()

    def test_gate_has_required_fields(self, client):
        resp = client.get("/health")
        gate = resp.json()["reproduction_gate"]
        assert gate["gate"] == "EXTERNAL_REPRODUCTION_CHECK"
        assert gate["independent_reproduction_claimed"] is False

    def test_version_bumped_to_pr8(self, client):
        resp = client.get("/health")
        assert resp.json()["version"] == "0.15.0-demo"
