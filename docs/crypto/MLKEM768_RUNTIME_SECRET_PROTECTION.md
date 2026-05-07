# ML-KEM768 Hybrid Runtime Secret Protection

## Purpose

EthicBit/CEMU uses hybrid runtime secret protection for Mechanical Ethics assurance flows. The implementation combines ML-KEM768 with X25519 and derives a runtime secret through HKDF-SHA256.

This document records the current posture, evidence boundary, and non-claims for the Mechanical Ethics runtime secret protection layer.

## Supported Claim

EthicBit/CEMU includes ML-KEM768 + X25519 hybrid runtime secret protection for Mechanical Ethics, with HKDF-derived hybrid secrets, fail-closed behavior, and non-sensitive canonical metadata recording.

## Implementation References

- `assurance/crypto/pq_kem.go`
- `mechanical_ethics/gate.go`
- `mechanical_ethics/gate_test.go`
- `results/pq_runtime_secret_protection.json`

## Cryptographic Flow

The current implementation derives a runtime secret from two independent components:

1. ML-KEM768 shared secret generated with the Go standard-library `crypto/mlkem` implementation.
2. X25519 ECDH shared secret generated with the Go standard-library `crypto/ecdh` implementation.
3. HKDF-SHA256 expansion over the combined secret material.

The resulting `HybridSecret` is process-local runtime material. It is intentionally excluded from JSON serialization and must not be written to canonical artifacts, receipts, logs, reports, or public evidence bundles.

## ML-KEM768 Posture

ML-KEM security relies on the assumed hardness of Module-LWE and is standardized by NIST FIPS 203. The repository uses ML-KEM768 as a post-quantum runtime secret protection primitive.

This posture is an implementation-level assurance statement. It is not a statement of FIPS module validation or third-party cryptographic certification.

## Hybrid Construction

The hybrid construction combines:

- a post-quantum KEM component: `ML-KEM768`;
- a classical elliptic-curve ECDH component: `X25519`;
- a key derivation step: `HKDF-SHA256`.

This is defense-in-depth. It does not convert the repository into a certified cryptographic module and does not imply absolute quantum security.

## Mechanical Ethics Fail-Closed Behavior

Mechanical Ethics initializes runtime secret protection through the configured runtime secret protector. If the protector is missing or ML-KEM768 hybrid encapsulation fails, the gate returns a fail-closed error and invokes the configured logger/stopper path.

Expected failure posture:

```text
runtime secret protector missing -> FAIL_CLOSED
ML-KEM768 hybrid encapsulation failure -> FAIL_CLOSED
invalid protected secret metadata -> FAIL_CLOSED
```

## Canonical Metadata Boundary

Canonical evidence may record only non-sensitive metadata, such as:

- algorithm identifier;
- key identifier;
- ciphertext length;
- public key length;
- protector name;
- protection status.

Canonical evidence must not record:

- `HybridSecret`;
- decapsulation key material;
- X25519 private keys;
- raw shared secrets;
- private seed material.

## Evidence Posture

Current evidence posture:

```text
ML-KEM768 + X25519 hybrid runtime protection: PRESENT
HKDF-derived runtime secret: PRESENT
Fail-closed gate integration: PRESENT
Non-sensitive metadata recording: PRESENT
Runtime protection artifact: PRESENT
```

## Explicit Non-Claims

This posture does not claim:

- FIPS module validation;
- cryptographic module certification;
- absolute quantum security;
- production cryptographic certification;
- third-party cryptographic certification;
- regulatory approval;
- SLSA L4 cryptographic closure;
- clinical, diagnostic, or safety certification.

## Publication-Safe Wording

Use:

```text
EthicBit/CEMU includes ML-KEM768 + X25519 hybrid runtime secret protection for Mechanical Ethics, with HKDF-derived hybrid secrets, fail-closed behavior, and non-sensitive canonical metadata recording. The security posture relies on NIST FIPS 203 ML-KEM assumptions and does not claim FIPS module validation, cryptographic module certification, absolute quantum security, or third-party cryptographic certification.
```
