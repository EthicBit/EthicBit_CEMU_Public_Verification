#!/usr/bin/env python3
"""ML-KEM768 post-quantum KEM runtime wrapper — AEM-EVOLVE™ v1.4.

Implements key generation, encapsulation, and decapsulation using ML-KEM768
(FIPS 203 / formerly Kyber768). Used for runtime secret protection — does NOT
replace Ed25519/ML-DSA signing on the governance path.

Library priority:
  1. `mlkem` package  (pip install mlkem)  — real FIPS 203 implementation
  2. `kyber-py` package (pip install kyber-py)
  3. Simulation mode — deterministic test vectors, clearly marked

v1.4 change: uses correct mlkem library API (ML_KEM / ML_KEM_768).

Non-claims:
  - This wrapper is not a certified cryptographic implementation.
  - This wrapper does not replace Ed25519/ML-DSA signing.
  - Simulation mode is NOT cryptographically secure.
  - This wrapper has not been independently audited.
"""
from __future__ import annotations

import hashlib
import os
import struct
from dataclasses import dataclass
from typing import Literal

MODE = Literal["mlkem", "kyber_py", "simulation"]


@dataclass
class KEMKeyPair:
    public_key: bytes
    secret_key: bytes
    mode: str


@dataclass
class KEMResult:
    ciphertext: bytes
    shared_secret: bytes
    mode: str


def _detect_mode() -> MODE:
    try:
        from mlkem.ml_kem import ML_KEM  # type: ignore[import]
        from mlkem.parameter_set import ML_KEM_768  # type: ignore[import]
        return "mlkem"
    except ImportError:
        pass
    try:
        import kyber  # type: ignore[import]
        return "kyber_py"
    except ImportError:
        pass
    return "simulation"


# ── Simulation mode (deterministic test vectors — NOT cryptographically secure) ──

_SIM_PK_SIZE   = 1184   # ML-KEM768 public key bytes
_SIM_SK_CORE   = 1216   # Internal SK material (2400 - 1184)
_SIM_SK_SIZE   = 2400   # ML-KEM768 secret key bytes (sk_core || pk)
_SIM_CT_SIZE   = 1088   # ML-KEM768 ciphertext bytes
_SIM_SS_SIZE   = 32     # ML-KEM768 shared secret bytes
_SIM_NONCE_LEN = 32     # Nonce embedded in first 32 bytes of CT


def _sim_keygen(seed: bytes | None = None) -> KEMKeyPair:
    """Deterministic simulation keygen.

    sk = sk_core (1216 B) || pk (1184 B) — mirrors real ML-KEM768 sk layout
    where the public key is embedded in the secret key to enable decapsulation.
    """
    if seed is None:
        seed = os.urandom(64)
    pk      = hashlib.shake_256(b"mlkem768-sim-pk:" + seed).digest(_SIM_PK_SIZE)
    sk_core = hashlib.shake_256(b"mlkem768-sim-sk:" + seed).digest(_SIM_SK_CORE)
    sk      = sk_core + pk  # embed pk at the end of sk (real ML-KEM768 format)
    return KEMKeyPair(public_key=pk, secret_key=sk, mode="simulation")


def _sim_encapsulate(public_key: bytes) -> KEMResult:
    """ct = nonce (32 B) || padding (1056 B); ss = SHAKE256(pk || nonce)."""
    nonce   = os.urandom(_SIM_NONCE_LEN)
    padding = hashlib.shake_256(b"mlkem768-sim-pad:" + public_key + nonce).digest(
        _SIM_CT_SIZE - _SIM_NONCE_LEN
    )
    ct = nonce + padding
    ss = hashlib.shake_256(b"mlkem768-sim-ss:" + public_key + nonce).digest(_SIM_SS_SIZE)
    return KEMResult(ciphertext=ct, shared_secret=ss, mode="simulation")


def _sim_decapsulate(secret_key: bytes, ciphertext: bytes) -> bytes:
    """Recover pk from sk (last 1184 bytes), extract nonce from ct (first 32 bytes)."""
    pk    = secret_key[-_SIM_PK_SIZE:]   # embedded pk in last 1184 B of sk
    nonce = ciphertext[:_SIM_NONCE_LEN]  # nonce in first 32 B of ct
    return hashlib.shake_256(b"mlkem768-sim-ss:" + pk + nonce).digest(_SIM_SS_SIZE)


# ── Real library dispatch ─────────────────────────────────────────────────────

def keygen(seed: bytes | None = None) -> KEMKeyPair:
    mode = _detect_mode()
    if mode == "mlkem":
        from mlkem.ml_kem import ML_KEM  # type: ignore[import]
        from mlkem.parameter_set import ML_KEM_768  # type: ignore[import]
        kem = ML_KEM(ML_KEM_768)
        ek, dk = kem.key_gen()  # ek = encapsulation key (public), dk = decapsulation key (secret)
        return KEMKeyPair(public_key=ek, secret_key=dk, mode="mlkem")
    if mode == "kyber_py":
        from kyber import Kyber768  # type: ignore[import]
        pk, sk = Kyber768.keygen()
        return KEMKeyPair(public_key=pk, secret_key=sk, mode="kyber_py")
    return _sim_keygen(seed)


def encapsulate(public_key: bytes) -> KEMResult:
    mode = _detect_mode()
    if mode == "mlkem":
        from mlkem.ml_kem import ML_KEM  # type: ignore[import]
        from mlkem.parameter_set import ML_KEM_768  # type: ignore[import]
        kem = ML_KEM(ML_KEM_768)
        ss, ct = kem.encaps(public_key)  # returns (shared_secret, ciphertext)
        return KEMResult(ciphertext=ct, shared_secret=ss, mode="mlkem")
    if mode == "kyber_py":
        from kyber import Kyber768  # type: ignore[import]
        ct, ss = Kyber768.enc(public_key)
        return KEMResult(ciphertext=ct, shared_secret=ss, mode="kyber_py")
    return _sim_encapsulate(public_key)


def decapsulate(secret_key: bytes, ciphertext: bytes) -> bytes:
    mode = _detect_mode()
    if mode == "mlkem":
        from mlkem.ml_kem import ML_KEM  # type: ignore[import]
        from mlkem.parameter_set import ML_KEM_768  # type: ignore[import]
        kem = ML_KEM(ML_KEM_768)
        return kem.decaps(secret_key, ciphertext)
    if mode == "kyber_py":
        from kyber import Kyber768  # type: ignore[import]
        return Kyber768.dec(secret_key, ciphertext)
    return _sim_decapsulate(secret_key, ciphertext)


def detect_mode() -> str:
    return _detect_mode()
