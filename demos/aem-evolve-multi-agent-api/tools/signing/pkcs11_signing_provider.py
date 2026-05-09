"""
Pkcs11SigningProvider — SigningProvider backed by a PKCS#11 token.

Requires: pip install pkcs11
Hardware: any PKCS#11-compliant HSM (SoftHSM, AWS CloudHSM, Thales, YubiHSM…)

Configuration (environment variables):
  ETHICBIT_PKCS11_LIB      Path to the PKCS#11 shared library (.so / .dll / .dylib)
  ETHICBIT_PKCS11_SLOT     Slot number (default: 0)
  ETHICBIT_PKCS11_PIN      User PIN
  ETHICBIT_PKCS11_KEY_LABEL  CKA_LABEL of the EC/RSA private key object

Non-claims:
  This provider is not production-tested against real hardware.
  SoftHSM is a software HSM suitable for testing only.
  Production use requires a FIPS 140-2/3 certified HSM.
"""

from __future__ import annotations

import os
from typing import Any

from .signing_provider import SigningProvider

_LIB_ENV   = "ETHICBIT_PKCS11_LIB"
_SLOT_ENV  = "ETHICBIT_PKCS11_SLOT"
_PIN_ENV   = "ETHICBIT_PKCS11_PIN"
_LABEL_ENV = "ETHICBIT_PKCS11_KEY_LABEL"


class Pkcs11SigningProvider(SigningProvider):
    """Ed25519 / EC signing via a PKCS#11 token.

    Falls back to a clear ImportError when `pkcs11` is not installed so that
    the rest of the verification suite can still run.
    """

    def __init__(
        self,
        lib_path: str | None = None,
        slot: int | None = None,
        pin: str | None = None,
        key_label: str | None = None,
    ) -> None:
        try:
            import pkcs11  # type: ignore[import]
            from pkcs11 import KeyType, Mechanism  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "pkcs11 library is required for Pkcs11SigningProvider. "
                "Install with: pip install pkcs11  "
                "Then configure a PKCS#11 library path (e.g. SoftHSM: "
                "ETHICBIT_PKCS11_LIB=/usr/lib/softhsm/libsofthsm2.so)"
            ) from exc

        lib_path  = lib_path  or os.environ.get(_LIB_ENV)
        slot      = slot      if slot is not None else int(os.environ.get(_SLOT_ENV, "0"))
        pin       = pin       or os.environ.get(_PIN_ENV, "")
        key_label = key_label or os.environ.get(_LABEL_ENV, "aem-evolve-signing-key")

        if not lib_path:
            raise EnvironmentError(
                f"PKCS#11 library path not set. "
                f"Set {_LIB_ENV} or pass lib_path= to Pkcs11SigningProvider."
            )

        lib = pkcs11.lib(lib_path)
        token = lib.get_token(slot_id=slot)
        self._session = token.open(user_pin=pin)
        self._priv_key = self._session.get_key(
            key_type=KeyType.EC,
            label=key_label,
        )
        self._pub_key = self._session.get_key(
            key_type=KeyType.EC,
            label=key_label,
            object_class=pkcs11.constants.ObjectClass.PUBLIC_KEY,
        )

    def sign(self, message: bytes) -> bytes:
        import pkcs11  # type: ignore[import]
        return self._priv_key.sign(message, mechanism=pkcs11.Mechanism.ECDSA_SHA256)

    def verify(self, message: bytes, signature: bytes) -> bool:
        import pkcs11  # type: ignore[import]
        try:
            self._pub_key.verify(message, signature, mechanism=pkcs11.Mechanism.ECDSA_SHA256)
            return True
        except pkcs11.exceptions.SignatureInvalid:
            return False

    def public_key_pem(self) -> bytes:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey
        der = bytes(self._pub_key[pkcs11.Attribute.VALUE])
        from cryptography.hazmat.primitives.serialization import load_der_public_key
        key = load_der_public_key(der)
        return key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def algorithm(self) -> str:
        return "EC/PKCS11"
