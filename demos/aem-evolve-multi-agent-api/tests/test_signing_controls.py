"""
Fast-path pytest tests for v1.7/v1.8 signing controls:
key persistence, FileSigningProvider, and adapter switch label.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main as _main
from main import _signing_provider, _SIGNING_STATUS, _db_adapter_label, DEMO_ROOT


class TestKeyPersistence:
    def test_signing_key_pem_exists(self):
        key_file = DEMO_ROOT / "signing_key.pem"
        # Either env-var key (no file needed) or file must exist
        if "ENV" in _SIGNING_STATUS:
            pytest.skip("EnvSigningProvider active — file not required")
        assert key_file.exists(), f"signing_key.pem missing at {key_file}"

    def test_signing_key_pem_valid_ed25519(self):
        if "ENV" in _SIGNING_STATUS:
            pytest.skip("EnvSigningProvider active")
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        pem = (DEMO_ROOT / "signing_key.pem").read_bytes()
        key = serialization.load_pem_private_key(pem, password=None)
        assert isinstance(key, Ed25519PrivateKey)

    def test_signing_status_not_ephemeral(self):
        assert "FILE" in _SIGNING_STATUS or "ENV" in _SIGNING_STATUS, \
            f"Expected FILE or ENV status, got {_SIGNING_STATUS!r}"

    def test_sign_produces_64_bytes(self):
        sig = _signing_provider.sign(b"test-persistence")
        assert len(sig) == 64

    def test_verify_roundtrip(self):
        msg = b"roundtrip-test-v1.8"
        sig = _signing_provider.sign(msg)
        assert _signing_provider.verify(msg, sig) is True

    def test_tampered_sig_fails(self):
        msg = b"tampered-message"
        sig = _signing_provider.sign(msg)
        bad_sig = bytes([b ^ 0xFF for b in sig])
        assert _signing_provider.verify(msg, bad_sig) is False

    def test_algorithm_is_ed25519(self):
        assert _signing_provider.algorithm() == "Ed25519"

    def test_public_key_pem_not_empty(self):
        pem = _signing_provider.public_key_pem()
        assert len(pem) > 0
        assert b"PUBLIC KEY" in pem


class TestDbAdapterLabel:
    def test_default_is_sqlite(self):
        if os.environ.get("AEM_DB_ADAPTER", "sqlite").lower() == "postgres":
            pytest.skip("AEM_DB_ADAPTER=postgres set in environment")
        assert _db_adapter_label == "SQLiteAdapter"

    def test_health_reflects_adapter(self, client=None):
        # Direct health check via imports
        assert _db_adapter_label in ("SQLiteAdapter", "PostgresAdapter")
