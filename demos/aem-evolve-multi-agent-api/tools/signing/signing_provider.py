"""
SigningProvider — abstract base for Ed25519 / ML-DSA signing.

Implementors:
- EnvSigningProvider  : reads PEM from env var (CI / staging)
- FileSigningProvider : reads PEM from file path (dev)
- HSM (external)      : implements this ABC against an HSM driver

Non-claims:
  This ABC is not HSM-backed.
  HSM integration requires an external implementation of this ABC.
"""

from __future__ import annotations

import abc


class SigningProvider(abc.ABC):
    """Abstract signing provider.  All methods are pure-python and synchronous."""

    @abc.abstractmethod
    def sign(self, message: bytes) -> bytes:
        """Return a raw signature over *message*."""

    @abc.abstractmethod
    def verify(self, message: bytes, signature: bytes) -> bool:
        """Return True iff *signature* is a valid signature over *message*."""

    @abc.abstractmethod
    def public_key_pem(self) -> bytes:
        """Return the PEM-encoded public key (bytes, UTF-8)."""

    def algorithm(self) -> str:
        """Human-readable algorithm name — override in subclasses."""
        return "Ed25519"
