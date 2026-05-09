"""
FileSigningProvider — reads Ed25519 private key from a file path (dev use).

Non-claims:
  Not HSM-backed.  Key is read from disk into process memory.
  Intended for local development and CI test key injection only.
"""

from __future__ import annotations

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .signing_provider import SigningProvider


class FileSigningProvider(SigningProvider):
    """Loads an Ed25519 private key from a PEM file at *key_path*."""

    def __init__(self, key_path: str | Path, password: bytes | None = None) -> None:
        key_path = Path(key_path)
        if not key_path.exists():
            raise FileNotFoundError(f"Key file not found: {key_path}")
        pem_bytes = key_path.read_bytes()
        self._private_key: Ed25519PrivateKey = serialization.load_pem_private_key(
            pem_bytes, password=password
        )

    def sign(self, message: bytes) -> bytes:
        return self._private_key.sign(message)

    def verify(self, message: bytes, signature: bytes) -> bool:
        from cryptography.exceptions import InvalidSignature

        try:
            self._private_key.public_key().verify(signature, message)
            return True
        except InvalidSignature:
            return False

    def public_key_pem(self) -> bytes:
        return self._private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def algorithm(self) -> str:
        return "Ed25519"
