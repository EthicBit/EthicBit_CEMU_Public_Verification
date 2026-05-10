"""
Tests for v2.0 PR 2 — HSM/KMS-backed production signing enforcement.

When AEM_KMS_PROVIDER is not set: gate is NOT_CONFIGURED (correct).
When AEM_KMS_PROVIDER is set: ProductionKmsProvider loads and gate_check() runs.
"""
import os
import sys
import pytest
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = DEMO_ROOT / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from signing.production_kms_provider import (
    ProductionKmsProvider,
    ProductionKmsConfig,
    load_kms_config,
    _SUPPORTED_PROVIDERS,
)


# ── Config loading ──────────────────────────────────────────────────────────

class TestKmsConfig:
    def test_no_provider_returns_none(self, monkeypatch):
        monkeypatch.delenv("AEM_KMS_PROVIDER", raising=False)
        assert load_kms_config() is None

    def test_provider_set_returns_config(self, monkeypatch):
        monkeypatch.setenv("AEM_KMS_PROVIDER", "aws_kms")
        monkeypatch.setenv("AEM_KMS_KEY_ID", "arn:aws:kms:us-east-1:123456789012:key/test")
        monkeypatch.delenv("AEM_KMS_REGION", raising=False)
        cfg = load_kms_config()
        assert cfg is not None
        assert cfg.provider == "aws_kms"
        assert "test" in cfg.key_id

    def test_non_exportable_is_always_true(self, monkeypatch):
        monkeypatch.setenv("AEM_KMS_PROVIDER", "aws_kms")
        monkeypatch.setenv("AEM_KMS_KEY_ID", "arn:test")
        cfg = load_kms_config()
        assert cfg.non_exportable is True

    def test_algorithm_defaults_to_ecdsa(self, monkeypatch):
        monkeypatch.setenv("AEM_KMS_PROVIDER", "aws_kms")
        monkeypatch.setenv("AEM_KMS_KEY_ID", "arn:test")
        monkeypatch.delenv("AEM_KMS_ALGORITHM", raising=False)
        cfg = load_kms_config()
        assert cfg.algorithm == "ECDSA_SHA_256"

    def test_custom_algorithm(self, monkeypatch):
        monkeypatch.setenv("AEM_KMS_PROVIDER", "aws_kms")
        monkeypatch.setenv("AEM_KMS_KEY_ID", "arn:test")
        monkeypatch.setenv("AEM_KMS_ALGORITHM", "RSASSA_PSS_SHA_256")
        cfg = load_kms_config()
        assert cfg.algorithm == "RSASSA_PSS_SHA_256"

    def test_config_is_frozen(self, monkeypatch):
        monkeypatch.setenv("AEM_KMS_PROVIDER", "aws_kms")
        monkeypatch.setenv("AEM_KMS_KEY_ID", "arn:test")
        cfg = load_kms_config()
        with pytest.raises((AttributeError, TypeError)):
            cfg.provider = "mutated"  # type: ignore

    def test_all_four_providers_documented(self):
        assert "aws_kms" in _SUPPORTED_PROVIDERS
        assert "gcp_kms" in _SUPPORTED_PROVIDERS
        assert "azure_key_vault" in _SUPPORTED_PROVIDERS
        assert "pkcs11" in _SUPPORTED_PROVIDERS


# ── Provider init ───────────────────────────────────────────────────────────

class TestProductionKmsProviderInit:
    def test_from_env_returns_none_without_provider(self, monkeypatch):
        monkeypatch.delenv("AEM_KMS_PROVIDER", raising=False)
        assert ProductionKmsProvider.from_env() is None

    def test_from_env_raises_with_invalid_provider(self, monkeypatch):
        monkeypatch.setenv("AEM_KMS_PROVIDER", "nonexistent_kms")
        monkeypatch.setenv("AEM_KMS_KEY_ID", "test-key")
        with pytest.raises((RuntimeError, ValueError)):
            ProductionKmsProvider.from_env()

    def test_aws_kms_fails_without_boto3_gracefully(self, monkeypatch):
        monkeypatch.setenv("AEM_KMS_PROVIDER", "aws_kms")
        monkeypatch.setenv("AEM_KMS_KEY_ID", "arn:aws:kms:us-east-1:123:key/test")
        # boto3 may or may not be installed; if installed it will fail at auth, not import
        try:
            provider = ProductionKmsProvider.from_env()
            # If we got here, boto3 is installed but credentials will fail on actual calls
            assert provider is not None
        except (RuntimeError, ImportError):
            pass  # Expected when boto3 not installed or key inaccessible

    def test_gate_check_not_configured_when_no_provider(self, monkeypatch):
        monkeypatch.delenv("AEM_KMS_PROVIDER", raising=False)
        provider = ProductionKmsProvider.from_env()
        assert provider is None

    def test_gate_check_structure_when_provider_set_but_key_unreachable(self, monkeypatch):
        monkeypatch.setenv("AEM_KMS_PROVIDER", "aws_kms")
        monkeypatch.setenv("AEM_KMS_KEY_ID", "arn:aws:kms:us-east-1:000000000000:key/nonexistent")
        try:
            provider = ProductionKmsProvider.from_env()
            if provider is not None:
                result = provider.gate_check()
                assert result["gate"] == "HSM_KMS_SIGNING_CHECK"
                assert result["status"] in ("PASS", "FAIL")
                assert "non_exportable_posture" in result
        except (RuntimeError, ImportError):
            pass  # Expected when boto3/credentials unavailable


# ── Audit log ───────────────────────────────────────────────────────────────

class TestAuditLog:
    def _make_provider_with_mock_backend(self):
        """Build a ProductionKmsProvider with a mock backend for unit testing."""
        from signing.production_kms_provider import _AuditLog
        from signing.signing_provider import SigningProvider
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization

        class MockBackend(SigningProvider):
            def __init__(self):
                self._key = Ed25519PrivateKey.generate()
            def sign(self, msg):
                return self._key.sign(msg)
            def verify(self, msg, sig):
                try:
                    self._key.public_key().verify(sig, msg)
                    return True
                except Exception:
                    return False
            def public_key_pem(self):
                return self._key.public_key().public_bytes(
                    serialization.Encoding.PEM,
                    serialization.PublicFormat.SubjectPublicKeyInfo,
                )

        cfg = ProductionKmsConfig(
            provider="aws_kms",
            key_id="arn:test",
            algorithm="ECDSA_SHA_256",
        )
        return ProductionKmsProvider(cfg, MockBackend())

    def test_audit_log_records_sign_operations(self):
        provider = self._make_provider_with_mock_backend()
        provider.sign(b"test message")
        provider.sign(b"another message")
        snap = provider.audit_log.snapshot()
        assert snap["sign_count"] == 2

    def test_audit_log_records_verify_operations(self):
        provider = self._make_provider_with_mock_backend()
        msg = b"test"
        sig = provider.sign(msg)
        provider.verify(msg, sig)
        snap = provider.audit_log.snapshot()
        assert snap["verify_count"] == 1

    def test_gate_check_returns_audit_log_active(self):
        provider = self._make_provider_with_mock_backend()
        result = provider.gate_check()
        assert result["audit_log_active"] is True

    def test_gate_check_passes_with_mock_backend(self):
        provider = self._make_provider_with_mock_backend()
        result = provider.gate_check()
        assert result["gate"] == "HSM_KMS_SIGNING_CHECK"
        assert result["status"] == "PASS"
        assert result["sign_verify_roundtrip"] is True
        assert result["non_exportable_posture"] is True


# ── Health endpoint reflects gate status ───────────────────────────────────

_KMS_PROVIDER = os.getenv("AEM_KMS_PROVIDER", "")


class TestHealthKmsGate:
    def test_kms_signing_gate_present_in_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "kms_signing_gate" in data

    def test_gate_not_configured_when_no_provider(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        gate = data.get("kms_signing_gate", {})
        if not _KMS_PROVIDER:
            assert gate.get("status") == "NOT_CONFIGURED"

    def test_gate_has_required_fields(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        gate = resp.json().get("kms_signing_gate", {})
        assert "gate" in gate
        assert gate["gate"] == "HSM_KMS_SIGNING_CHECK"
        assert "status" in gate

    def test_version_bumped(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["version"] == "0.9.0-demo"
