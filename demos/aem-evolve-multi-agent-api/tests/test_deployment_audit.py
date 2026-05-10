"""
Tests for v2.0 PR 9 — Production deployment audit evidence gate.

C-01–C-08 pass on file presence and content inspection (no live infra needed).
C-09–C-10 are skipped without AEM_DEPLOYMENT_TARGET / AEM_DEPLOYMENT_TIMESTAMP.
"""
import sys
from pathlib import Path

import pytest

DEMO_ROOT = Path(__file__).resolve().parents[1]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from deployment.deployment_gate import (
    DeploymentGate,
    _REQUIRED_ENV_VARS,
    _REQUIRED_GATES,
    _REQUIRED_GATE_VERIFIERS,
    _HEALTH_ENDPOINTS,
    _MANIFEST_FILE,
    _DEPLOY_TOOLS_DIR,
    _PR_VERIFIERS_DIR,
)


# ── Gate construction ────────────────────────────────────────────────────────

class TestDeploymentGateInit:
    def test_from_env_returns_gate(self):
        gate = DeploymentGate.from_env()
        assert isinstance(gate, DeploymentGate)

    def test_no_target_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_DEPLOYMENT_TARGET", raising=False)
        gate = DeploymentGate.from_env()
        assert gate._deployment_target is None

    def test_no_timestamp_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_DEPLOYMENT_TIMESTAMP", raising=False)
        gate = DeploymentGate.from_env()
        assert gate._deployment_timestamp is None

    def test_captures_deployment_target(self, monkeypatch):
        monkeypatch.setenv("AEM_DEPLOYMENT_TARGET", "aws-us-east-1-prod")
        gate = DeploymentGate.from_env()
        assert gate._deployment_target == "aws-us-east-1-prod"

    def test_captures_deployment_timestamp(self, monkeypatch):
        monkeypatch.setenv("AEM_DEPLOYMENT_TIMESTAMP", "2026-06-01T12:00:00Z")
        gate = DeploymentGate.from_env()
        assert gate._deployment_timestamp == "2026-06-01T12:00:00Z"


# ── Constants ────────────────────────────────────────────────────────────────

class TestConstants:
    def test_fourteen_required_env_vars(self):
        assert len(_REQUIRED_ENV_VARS) == 14

    def test_nine_required_gates(self):
        assert len(_REQUIRED_GATES) == 9

    def test_nine_gate_verifiers(self):
        assert len(_REQUIRED_GATE_VERIFIERS) == 9

    def test_three_health_endpoints(self):
        assert len(_HEALTH_ENDPOINTS) == 3

    def test_oidc_issuer_in_env_vars(self):
        assert "OIDC_ISSUER" in _REQUIRED_ENV_VARS

    def test_hitl_secret_in_env_vars(self):
        assert "HITL_SECRET" in _REQUIRED_ENV_VARS

    def test_pr9_in_required_gates(self):
        assert "PR9" in _REQUIRED_GATES

    def test_health_endpoints_contain_metrics(self):
        assert "/metrics" in _HEALTH_ENDPOINTS

    def test_verify_deployment_audit_in_verifiers(self):
        assert "verify_deployment_audit.py" in _REQUIRED_GATE_VERIFIERS


# ── C-01: Manifest exists ────────────────────────────────────────────────────

class TestManifestExists:
    def test_manifest_file_exists(self):
        assert _MANIFEST_FILE.exists(), f"DEPLOYMENT_MANIFEST.md not found at {_MANIFEST_FILE}"

    def test_check_returns_ok(self):
        gate = DeploymentGate()
        result = gate.check_manifest()
        assert result["ok"] is True

    def test_check_has_sha256(self):
        gate = DeploymentGate()
        result = gate.check_manifest()
        assert len(result["sha256"]) == 64

    def test_manifest_not_empty(self):
        gate = DeploymentGate()
        result = gate.check_manifest()
        assert result["size_bytes"] > 500


# ── C-02: Target environment fields ─────────────────────────────────────────

class TestTargetEnvironment:
    def test_check_returns_ok(self):
        gate = DeploymentGate()
        result = gate.check_target_environment()
        assert result["ok"] is True

    def test_all_six_fields_present(self):
        gate = DeploymentGate()
        result = gate.check_target_environment()
        assert result["fields_present"] == 6
        assert result["missing_fields"] == []

    def test_fields_required_count(self):
        gate = DeploymentGate()
        result = gate.check_target_environment()
        assert result["fields_required"] == 6


# ── C-03: Env vars documented ────────────────────────────────────────────────

class TestEnvVarsDocumented:
    def test_check_returns_ok(self):
        gate = DeploymentGate()
        result = gate.check_env_vars_documented()
        assert result["ok"] is True

    def test_all_fourteen_vars_documented(self):
        gate = DeploymentGate()
        result = gate.check_env_vars_documented()
        assert result["env_vars_documented"] == 14
        assert result["missing_env_vars"] == []

    def test_env_vars_required_count(self):
        gate = DeploymentGate()
        result = gate.check_env_vars_documented()
        assert result["env_vars_required"] == 14


# ── C-04: Gate checklist ─────────────────────────────────────────────────────

class TestGateChecklist:
    def test_check_returns_ok(self):
        gate = DeploymentGate()
        result = gate.check_gate_checklist()
        assert result["ok"] is True

    def test_all_nine_gates_in_checklist(self):
        gate = DeploymentGate()
        result = gate.check_gate_checklist()
        assert result["gates_in_checklist"] == 9
        assert result["missing_gates"] == []

    def test_gates_required_count(self):
        gate = DeploymentGate()
        result = gate.check_gate_checklist()
        assert result["gates_required"] == 9


# ── C-05: Gate verifiers exist ───────────────────────────────────────────────

class TestGateVerifiers:
    def test_verifiers_dir_exists(self):
        assert _PR_VERIFIERS_DIR.exists()

    def test_check_returns_ok(self):
        gate = DeploymentGate()
        result = gate.check_gate_verifiers()
        assert result["ok"] is True, result.get("missing_verifiers", "")

    def test_all_nine_verifiers_present(self):
        gate = DeploymentGate()
        result = gate.check_gate_verifiers()
        assert result["verifiers_present"] == 9
        assert result["missing_verifiers"] == []

    def test_verifiers_required_count(self):
        gate = DeploymentGate()
        result = gate.check_gate_verifiers()
        assert result["verifiers_required"] == 9


# ── C-06: Rollback plan ──────────────────────────────────────────────────────

class TestRollbackPlan:
    def test_check_returns_ok(self):
        gate = DeploymentGate()
        result = gate.check_rollback_plan()
        assert result["ok"] is True

    def test_has_rollback_section(self):
        gate = DeploymentGate()
        result = gate.check_rollback_plan()
        assert result["has_rollback_section"] is True

    def test_has_rollback_steps(self):
        gate = DeploymentGate()
        result = gate.check_rollback_plan()
        assert result["has_rollback_steps"] is True

    def test_has_db_rollback_reference(self):
        gate = DeploymentGate()
        result = gate.check_rollback_plan()
        assert result["has_db_rollback_reference"] is True


# ── C-07: Health endpoints ───────────────────────────────────────────────────

class TestHealthEndpoints:
    def test_check_returns_ok(self):
        gate = DeploymentGate()
        result = gate.check_health_endpoints()
        assert result["ok"] is True

    def test_all_three_endpoints_documented(self):
        gate = DeploymentGate()
        result = gate.check_health_endpoints()
        assert result["endpoints_documented"] == 3
        assert result["missing_endpoints"] == []

    def test_endpoints_required_count(self):
        gate = DeploymentGate()
        result = gate.check_health_endpoints()
        assert result["endpoints_required"] == 3


# ── C-08: Audit artifact ─────────────────────────────────────────────────────

class TestAuditArtifact:
    def test_audit_artifact_exists(self):
        artifacts = list(_DEPLOY_TOOLS_DIR.glob("deployment_audit_*.json"))
        assert len(artifacts) >= 1

    def test_check_returns_ok(self):
        gate = DeploymentGate()
        result = gate.check_audit_artifact()
        assert result["ok"] is True, result.get("detail", "")

    def test_all_subjects_hashed(self):
        gate = DeploymentGate()
        result = gate.check_audit_artifact()
        assert result["subjects_hashed"] == result["subjects_total"]
        assert result["subjects_hashed"] >= 15

    def test_has_artifact_sha256(self):
        gate = DeploymentGate()
        result = gate.check_audit_artifact()
        assert result["has_artifact_sha256"] is True
        assert len(result["artifact_sha256"]) == 64

    def test_artifact_file_sha256(self):
        gate = DeploymentGate()
        result = gate.check_audit_artifact()
        assert len(result["sha256"]) == 64


# ── C-09/C-10: Production deployment (skipped without env vars) ───────────────

class TestProductionDeploymentChecks:
    def test_target_skipped_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_DEPLOYMENT_TARGET", raising=False)
        gate = DeploymentGate(deployment_target=None)
        result = gate.check_deployment_target()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_timestamp_skipped_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_DEPLOYMENT_TIMESTAMP", raising=False)
        gate = DeploymentGate(deployment_timestamp=None)
        result = gate.check_deployment_timestamp()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_target_passes_with_value(self):
        gate = DeploymentGate(deployment_target="aws-us-east-1-prod")
        result = gate.check_deployment_target()
        assert result["ok"] is True
        assert result["deployment_target"] == "aws-us-east-1-prod"

    def test_timestamp_passes_with_value(self):
        gate = DeploymentGate(deployment_timestamp="2026-06-01T12:00:00Z")
        result = gate.check_deployment_timestamp()
        assert result["ok"] is True
        assert result["deployment_timestamp"] == "2026-06-01T12:00:00Z"


# ── Full gate_check ───────────────────────────────────────────────────────────

class TestGateCheck:
    def test_gate_check_has_required_fields(self):
        gate = DeploymentGate()
        result = gate.gate_check()
        assert result["gate"] == "PRODUCTION_DEPLOYMENT_AUDIT_CHECK"
        assert result["status"] in ("PASS", "FAIL")
        assert "checks_passed" in result
        assert "production_deployed" in result

    def test_production_deployed_false_without_env(self, monkeypatch):
        monkeypatch.delenv("AEM_DEPLOYMENT_TARGET", raising=False)
        monkeypatch.delenv("AEM_DEPLOYMENT_TIMESTAMP", raising=False)
        gate = DeploymentGate()
        result = gate.gate_check()
        assert result["production_deployed"] is False

    def test_production_deployed_false_with_only_target(self):
        gate = DeploymentGate(deployment_target="aws-us-east-1-prod", deployment_timestamp=None)
        result = gate.gate_check()
        assert result["production_deployed"] is False

    def test_production_deployed_true_with_both(self):
        gate = DeploymentGate(
            deployment_target="aws-us-east-1-prod",
            deployment_timestamp="2026-06-01T12:00:00Z",
        )
        result = gate.gate_check()
        assert result["production_deployed"] is True

    def test_gate_fails_without_deployment_vars(self, monkeypatch):
        monkeypatch.delenv("AEM_DEPLOYMENT_TARGET", raising=False)
        monkeypatch.delenv("AEM_DEPLOYMENT_TIMESTAMP", raising=False)
        gate = DeploymentGate()
        result = gate.gate_check()
        assert result["status"] == "FAIL"

    def test_eight_local_checks_pass(self, monkeypatch):
        monkeypatch.delenv("AEM_DEPLOYMENT_TARGET", raising=False)
        monkeypatch.delenv("AEM_DEPLOYMENT_TIMESTAMP", raising=False)
        gate = DeploymentGate()
        result = gate.gate_check()
        checks = result["checks"]
        config_keys = [k for k in checks if k.startswith(
            ("C-01", "C-02", "C-03", "C-04", "C-05", "C-06", "C-07", "C-08")
        )]
        passed = sum(1 for k in config_keys if checks[k].get("ok"))
        assert passed == 8, f"Expected 8 local checks to pass, got {passed}: {checks}"

    def test_gate_passes_with_deployment_vars(self):
        gate = DeploymentGate(
            deployment_target="aws-us-east-1-prod",
            deployment_timestamp="2026-06-01T12:00:00Z",
        )
        result = gate.gate_check()
        assert result["status"] == "PASS"
        assert result["checks_passed"] == 10

    def test_fail_reason_mentions_missing_env_vars(self, monkeypatch):
        monkeypatch.delenv("AEM_DEPLOYMENT_TARGET", raising=False)
        monkeypatch.delenv("AEM_DEPLOYMENT_TIMESTAMP", raising=False)
        gate = DeploymentGate()
        result = gate.gate_check()
        assert "AEM_DEPLOYMENT_TARGET" in result["fail_reason"]

    def test_fail_reason_mentions_production_deployed_false(self, monkeypatch):
        monkeypatch.delenv("AEM_DEPLOYMENT_TARGET", raising=False)
        monkeypatch.delenv("AEM_DEPLOYMENT_TIMESTAMP", raising=False)
        gate = DeploymentGate()
        result = gate.gate_check()
        assert "production_deployed=false" in result["fail_reason"]


# ── Health endpoint ───────────────────────────────────────────────────────────

class TestHealthDeploymentGate:
    def test_deployment_gate_in_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert "deployment_gate" in resp.json()

    def test_gate_has_required_fields(self, client):
        resp = client.get("/health")
        gate = resp.json()["deployment_gate"]
        assert gate["gate"] == "PRODUCTION_DEPLOYMENT_AUDIT_CHECK"
        assert "status" in gate
        assert gate["production_deployed"] is False

    def test_version_bumped_to_pr9(self, client):
        resp = client.get("/health")
        assert resp.json()["version"] == "0.21.0-demo"
