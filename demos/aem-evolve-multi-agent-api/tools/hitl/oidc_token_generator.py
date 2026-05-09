#!/usr/bin/env python3
"""
oidc_token_generator.py — generates RS256 JWTs for CI OIDC HITL testing.

Generates a self-signed RSA-2048 key pair and issues OIDC-style ID tokens.
No external IdP or network required.  Keys are ephemeral (generated per run).

Usage:
  from tools.hitl.oidc_token_generator import OidcTestKeyPair, generate_token
  kp = OidcTestKeyPair()
  token = generate_token(kp, sub="approver-001", event_id="evt-abc")
  jwks = kp.jwks()
"""

from __future__ import annotations

import base64
import json
import os
import struct
import time
from dataclasses import dataclass, field

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
    generate_private_key,
)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _int_to_b64url(n: int) -> str:
    length = (n.bit_length() + 7) // 8
    return _b64url(n.to_bytes(length, "big"))


@dataclass
class OidcTestKeyPair:
    """Ephemeral RSA-2048 key pair for CI OIDC token signing."""

    key_id: str = field(default_factory=lambda: _b64url(os.urandom(8)))
    _private_key: RSAPrivateKey = field(init=False)

    def __post_init__(self) -> None:
        self._private_key = generate_private_key(public_exponent=65537, key_size=2048)

    def jwks(self) -> dict:
        """Return inline JWKS (JSON Web Key Set) for this key pair."""
        pub = self._private_key.public_key()
        pub_numbers = pub.public_key().public_numbers() if hasattr(pub, "public_key") else pub.public_numbers()
        return {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "kid": self.key_id,
                    "n": _int_to_b64url(pub_numbers.n),
                    "e": _int_to_b64url(pub_numbers.e),
                }
            ]
        }

    def sign_jwt(self, header: dict, payload: dict) -> str:
        """Return a signed JWT string (header.payload.signature)."""
        h = _b64url(json.dumps(header, separators=(",", ":")).encode())
        p = _b64url(json.dumps(payload, separators=(",", ":")).encode())
        signing_input = f"{h}.{p}".encode()
        signature = self._private_key.sign(
            signing_input,
            asym_padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return f"{h}.{p}.{_b64url(signature)}"


def generate_token(
    key_pair: OidcTestKeyPair,
    sub: str,
    event_id: str,
    issuer: str = "https://hitl.ethicbit.internal",
    audience: str = "aem-evolve-hitl",
    ttl_seconds: int = 600,
    now: float | None = None,
) -> str:
    """Generate a signed RS256 OIDC ID token."""
    now = now if now is not None else time.time()
    header = {"alg": "RS256", "typ": "JWT", "kid": key_pair.key_id}
    payload = {
        "iss": issuer,
        "aud": audience,
        "sub": sub,
        "iat": int(now),
        "exp": int(now) + ttl_seconds,
        "event_id": event_id,
    }
    return key_pair.sign_jwt(header, payload)
