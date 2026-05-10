"""
Fast-path pytest tests for v1.9.0 OIDC key persistence:
oidc_key.pem exists, deterministic kid, cross-reload verification.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main as _main
from main import DEMO_ROOT, _OIDC_KEY_FILE_NAME

_OIDC_KEY_FILE = DEMO_ROOT / _OIDC_KEY_FILE_NAME


class TestOidcKeyPersistence:
    def test_oidc_key_pem_exists(self):
        assert _OIDC_KEY_FILE.exists(), f"oidc_key.pem missing at {_OIDC_KEY_FILE}"

    def test_oidc_key_pem_is_rsa(self):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
        pem = _OIDC_KEY_FILE.read_bytes()
        key = serialization.load_pem_private_key(pem, password=None)
        assert isinstance(key, RSAPrivateKey)

    def test_oidc_key_size_2048(self):
        from cryptography.hazmat.primitives import serialization
        pem = _OIDC_KEY_FILE.read_bytes()
        key = serialization.load_pem_private_key(pem, password=None)
        assert key.key_size == 2048

    def test_load_or_generate_same_kid(self):
        from hitl.oidc_token_generator import OidcTestKeyPair
        kp1 = OidcTestKeyPair.load_or_generate(_OIDC_KEY_FILE)
        kp2 = OidcTestKeyPair.load_or_generate(_OIDC_KEY_FILE)
        assert kp1.key_id == kp2.key_id, "kid must be deterministic from public key"

    def test_load_or_generate_same_kid_as_main(self):
        from hitl.oidc_token_generator import OidcTestKeyPair
        kp = OidcTestKeyPair.load_or_generate(_OIDC_KEY_FILE)
        assert kp.key_id == _main._oidc_key_pair.key_id

    def test_sign_and_verify_roundtrip(self):
        from hitl.oidc_token_generator import OidcTestKeyPair, generate_token
        from hitl.oidc_hitl_identity_verifier import verify_oidc_token
        kp = OidcTestKeyPair.load_or_generate(_OIDC_KEY_FILE)
        policy = _main._OIDC_POLICY
        token = generate_token(kp, sub="approver-001", event_id="test-evt",
                               issuer=policy["issuer"], audience=policy["audience"])
        ok, reason, _ = verify_oidc_token(token, kp.jwks(), policy)
        assert ok, f"verify failed: {reason}"

    def test_cross_reload_verify(self):
        from hitl.oidc_token_generator import OidcTestKeyPair, generate_token
        from hitl.oidc_hitl_identity_verifier import verify_oidc_token
        policy = _main._OIDC_POLICY
        kp_orig = OidcTestKeyPair.load_or_generate(_OIDC_KEY_FILE)
        token = generate_token(kp_orig, sub="approver-001", event_id="cross-test",
                               issuer=policy["issuer"], audience=policy["audience"])
        kp_reload = OidcTestKeyPair.load_or_generate(_OIDC_KEY_FILE)
        ok, reason, _ = verify_oidc_token(token, kp_reload.jwks(), policy)
        assert ok, f"cross-reload verify failed: {reason}"

    def test_oidc_key_persistence_health_field(self, client):
        body = client.get("/health").json()
        assert body.get("oidc_key_persistence") == "FILE_BASED"

    def test_oidc_key_persistence_field_in_non_claims(self, client):
        body = client.get("/health").json()
        assert "no_production_oidc_idp" in body.get("non_claims", [])

    def test_jwks_kid_matches_key_file(self, client):
        from hitl.oidc_token_generator import OidcTestKeyPair
        kp = OidcTestKeyPair.load_or_generate(_OIDC_KEY_FILE)
        r = client.get("/oidc/jwks")
        assert r.status_code == 200
        keys = r.json().get("keys", [])
        assert keys[0]["kid"] == kp.key_id
