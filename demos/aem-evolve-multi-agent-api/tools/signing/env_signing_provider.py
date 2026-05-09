"""
EnvSigningProvider — reads Ed25519 private key from environment variable.

Environment variable: ETHICBIT_ED25519_PRIVATE_KEY_PEM
  Value: PEM-encoded PKCS8 Ed25519 private key (base64, standard PEM headers).

Non-claims:
  Not HSM-backed.  Key is in process memory.
  For production, replace with an HSM-backed SigningProvider.
"""

from __future__ import annotations

import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .signing_provider import SigningProvider

_ENV_VAR = "ETHICBIT_ED25519_PRIVATE_KEY_PEM"


class EnvSigningProvider(SigningProvider):
    """Loads an Ed25519 private key from the ``ETHICBIT_ED25519_PRIVATE_KEY_PEM`` env var."""

    def __init__(self) -> None:
        pem = os.environ.get(_ENV_VAR)
        if not pem:
            raise EnvironmentError(
                f"Environment variable {_ENV_VAR!r} is not set. "
                "Set it to a PEM-encoded Ed25519 private key."
            )
        self._private_key: Ed25519PrivateKey = serialization.load_pem_private_key(
            pem.encode() if isinstance(pem, str) else pem,
            password=None,
        )

    def sign(self, message: bytes) -> bytes:
        return self._private_key.sign(message)

    def verify(self, message: bytes, signature: bytes) -> bool:
        from cryptography.exceptions import InvalidSignature

        pub = self._private_key.public_key()
        try:
            pub.verify(signature, message)
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
