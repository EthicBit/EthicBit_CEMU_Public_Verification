"""
Tests for v2.0 PR 1 — production OIDC provider enforcement.

When OIDC_ISSUER is not set: gate is NOT_CONFIGURED (correct — the gate is not satisfied).
When OIDC_ISSUER is set: the production path loads and gate_check() runs.
"""
import os
import sys
import pytest
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[1]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from security.oidc_config import load_oidc_config, ProductionOidcConfig


# ── Config loading ──────────────────────────────────────────────────────────

class TestOidcConfig:
    def test_no_issuer_returns_none(self, monkeypatch):
        monkeypatch.delenv("OIDC_ISSUER", raising=False)
        assert load_oidc_config() is None

    def test_issuer_only_infers_jwks_uri(self, monkeypatch):
        monkeypatch.setenv("OIDC_ISSUER", "https://example.okta.com")
        monkeypatch.delenv("OIDC_JWKS_URI", raising=False)
        monkeypatch.delenv("OIDC_AUDIENCE", raising=False)
        cfg = load_oidc_config()
        assert cfg is not None
        assert cfg.issuer == "https://example.okta.com"
        assert cfg.jwks_uri == "https://example.okta.com/.well-known/jwks.json"

    def test_explicit_jwks_uri_used(self, monkeypatch):
        monkeypatch.setenv("OIDC_ISSUER", "https://example.okta.com")
        monkeypatch.setenv("OIDC_JWKS_URI", "https://example.okta.com/oauth2/v1/keys")
        monkeypatch.delenv("OIDC_AUDIENCE", raising=False)
        cfg = load_oidc_config()
        assert cfg.jwks_uri == "https://example.okta.com/oauth2/v1/keys"

    def test_audience_defaults_to_aem_evolve(self, monkeypatch):
        monkeypatch.setenv("OIDC_ISSUER", "https://example.okta.com")
        monkeypatch.delenv("OIDC_JWKS_URI", raising=False)
        monkeypatch.delenv("OIDC_AUDIENCE", raising=False)
        cfg = load_oidc_config()
        assert cfg.audience == "aem-evolve"

    def test_explicit_audience(self, monkeypatch):
        monkeypatch.setenv("OIDC_ISSUER", "https://example.okta.com")
        monkeypatch.delenv("OIDC_JWKS_URI", raising=False)
        monkeypatch.setenv("OIDC_AUDIENCE", "my-api")
        cfg = load_oidc_config()
        assert cfg.audience == "my-api"

    def test_ttl_defaults_300(self, monkeypatch):
        monkeypatch.setenv("OIDC_ISSUER", "https://example.okta.com")
        monkeypatch.delenv("OIDC_JWKS_URI", raising=False)
        monkeypatch.delenv("OIDC_AUDIENCE", raising=False)
        monkeypatch.delenv("OIDC_JWKS_TTL_SECONDS", raising=False)
        cfg = load_oidc_config()
        assert cfg.jwks_ttl_seconds == 300

    def test_custom_ttl(self, monkeypatch):
        monkeypatch.setenv("OIDC_ISSUER", "https://example.okta.com")
        monkeypatch.delenv("OIDC_JWKS_URI", raising=False)
        monkeypatch.delenv("OIDC_AUDIENCE", raising=False)
        monkeypatch.setenv("OIDC_JWKS_TTL_SECONDS", "600")
        cfg = load_oidc_config()
        assert cfg.jwks_ttl_seconds == 600

    def test_config_is_frozen(self, monkeypatch):
        monkeypatch.setenv("OIDC_ISSUER", "https://example.okta.com")
        monkeypatch.delenv("OIDC_JWKS_URI", raising=False)
        monkeypatch.delenv("OIDC_AUDIENCE", raising=False)
        cfg = load_oidc_config()
        with pytest.raises((AttributeError, TypeError)):
            cfg.issuer = "mutated"  # type: ignore


# ── Provider loading ────────────────────────────────────────────────────────

class TestProductionOidcProviderInit:
    def test_from_env_returns_none_without_issuer(self, monkeypatch):
        monkeypatch.delenv("OIDC_ISSUER", raising=False)
        from security.oidc_provider import ProductionOidcProvider
        assert ProductionOidcProvider.from_env() is None

    def test_from_env_returns_provider_with_issuer(self, monkeypatch):
        monkeypatch.setenv("OIDC_ISSUER", "https://example.okta.com")
        monkeypatch.delenv("OIDC_JWKS_URI", raising=False)
        monkeypatch.delenv("OIDC_AUDIENCE", raising=False)
        from security.oidc_provider import ProductionOidcProvider
        provider = ProductionOidcProvider.from_env()
        assert provider is not None
        assert provider.config.issuer == "https://example.okta.com"

    def test_gate_check_not_configured(self, monkeypatch):
        monkeypatch.delenv("OIDC_ISSUER", raising=False)
        from security.oidc_provider import ProductionOidcProvider
        provider = ProductionOidcProvider.from_env()
        assert provider is None

    def test_gate_check_fail_when_jwks_unreachable(self, monkeypatch):
        monkeypatch.setenv("OIDC_ISSUER", "https://localhost:19999/nonexistent")
        monkeypatch.delenv("OIDC_JWKS_URI", raising=False)
        monkeypatch.delenv("OIDC_AUDIENCE", raising=False)
        from security.oidc_provider import ProductionOidcProvider
        provider = ProductionOidcProvider.from_env()
        assert provider is not None
        result = provider.gate_check()
        assert result["gate"] == "PRODUCTION_OIDC_PROVIDER_CHECK"
        assert result["status"] == "FAIL"
        assert result["jwks_reachable"] is False

    def test_verify_token_invalid_without_provider(self, monkeypatch):
        monkeypatch.setenv("OIDC_ISSUER", "https://localhost:19999/nonexistent")
        monkeypatch.delenv("OIDC_JWKS_URI", raising=False)
        monkeypatch.delenv("OIDC_AUDIENCE", raising=False)
        from security.oidc_provider import ProductionOidcProvider
        provider = ProductionOidcProvider.from_env()
        assert provider is not None
        ok, reason, claims = provider.verify_token("not.a.jwt")
        assert ok is False
        assert claims == {}


# ── Health endpoint reflects gate status ───────────────────────────────────

_SKIP_NO_SERVER = pytest.mark.skipif(
    True,  # always skip — health endpoint tests require running server
    reason="Health endpoint tests require running server",
)

_OIDC_ISSUER = os.getenv("OIDC_ISSUER", "")
_SKIP_NO_PROD_OIDC = pytest.mark.skipif(
    not _OIDC_ISSUER,
    reason="OIDC_ISSUER not set — production OIDC gate requires external IdP",
)


class TestHealthOidcGate:
    @_SKIP_NO_PROD_OIDC
    def test_production_oidc_gate_present_in_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "production_oidc_gate" in data
        gate = data["production_oidc_gate"]
        assert gate["gate"] == "PRODUCTION_OIDC_PROVIDER_CHECK"

    def test_gate_not_configured_when_no_issuer(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        gate = data.get("production_oidc_gate", {})
        # When OIDC_ISSUER not set, gate status is NOT_CONFIGURED — correct behavior
        if not _OIDC_ISSUER:
            assert gate.get("status") == "NOT_CONFIGURED"

    def test_hitl_oidc_mode_field_present(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "hitl_oidc_mode" in data
        assert data["hitl_oidc_mode"] in ("PRODUCTION", "DEMO")
