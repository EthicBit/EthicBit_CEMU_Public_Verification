# Signing Key Migration Record — Software Key → AWS KMS

**Block:** B1  
**Status:** COMPLETE  
**Date:** 2026-05-18  
**HEAD commit:** `8f7e141b`  
**Constitutional dependency:** EthicBit / CEMU v3.7.0+

---

## Summary

This document records the migration of the EthicBit/CEMU artifact signing posture from
software-held keys stored as GitHub Secrets (`github_secrets_pem`, TRANSITIONAL_COMPLIANT)
to non-exportable AWS KMS keys (PRODUCTION_HSM_READY) for in-toto chain and SBOM signing.

The migration does **not** change the active claim posture — all in-toto statements remain
`KMS_SIGNED_PENDING_EXTERNAL_WITNESS`. External witness is a separate gate (criterion 1/2).

---

## Pre-Migration Posture

| Property | Value |
|----------|-------|
| Signing backend | `github_secrets_pem` |
| Key source (Ed25519) | `trusted_secrets` (GitHub Actions secret) |
| Key source (ML-DSA) | `trusted_secrets` (GitHub Actions secret) |
| Key posture status | `TRANSITIONAL_COMPLIANT` |
| Eligible for sovereign release | `false` |
| Effective mode | `compatibility_fallback` |
| Last signed under this posture | 2026-05-01T20:20:30Z |
| Algorithms | ED25519 + ML-DSA (hybrid, compatibility mode) |

**Why TRANSITIONAL_COMPLIANT and not SOVEREIGN_COMPLIANT:**  
Software keys loaded from environment variables are exportable — a CI runner with access
to the secret environment can extract the key material. This satisfies CI-grade signing
requirements but not production sovereign signing requirements.

**Artifacts signed under pre-migration posture:**
- `assurance/signatures/AEM_V1_1_SUPPLY_CHAIN_SIGNATURE_SET.json` — Ed25519 + ML-DSA hybrid
- `assurance/signatures/AEM_V1_1_SUPPLY_CHAIN_CRYPTO_TRUTH.json` — crypto posture record

---

## Migration Trigger

The v4.0 External Validation process (criterion 4: HSM/KMS signing) requires that
production-class artifact signing use a non-exportable key source. AWS KMS provides:

1. Non-exportable key material — key never leaves the HSM boundary
2. Per-operation audit trail via AWS CloudTrail
3. IAM-controlled access (least-privilege policy)
4. Rotation policy support
5. ECC_NIST_P256 key type — produces ECDSA_SHA_256 signatures verifiable with standard tooling

---

## Migration Steps Executed

### Step 1 — KMS Key Provisioning (pre-Block B2)

Two KMS keys were provisioned in `us-east-2`:

| Alias | Purpose | Key type |
|-------|---------|----------|
| `alias/ethicbit-intoto-signing` | in-toto statements + SBOM (assurance artifacts) | ECC_NIST_P256 |
| `alias/ethicbit-kms-signing` | API runtime signing operations | ECC_NIST_P256 |

Key IDs are treated as infrastructure identifiers and are sanitized from public state blocks
per the `check_no_aws_ids.py` pre-commit hook. They are retained in signing scripts and
assurance artifacts under the allowlisted paths only.

### Step 2 — Signing Script Implementation (Block B2)

`scripts/crypto/sign_intoto_statements_kms.py` — signs all 6 in-toto statements:

```
intake → provenance → governance → fixation → sealing → closure
```

Signing approach:
- `canonical_payload()` serializes the statement JSON excluding the `signature` field
- `hashlib.sha256()` computes the payload digest (SHA256 before KMS call)
- `kms.sign(SigningAlgorithm="ECDSA_SHA_256", MessageType="DIGEST")` via boto3
- DER-encoded signature stored as base64 in each statement's `signature` field
- `payloadSHA256` stored alongside for independent verification

`scripts/crypto/sign_sbom_kms.py` — signs the CycloneDX SBOM (654 components):

- JSF-style `signature` block embedded at BOM root
- Detached sidecar written to `assurance/sbom/aem_v1_1_sbom.cyclonedx.sig.json`

### Step 3 — Signing Execution (Block B2, 2026-05-18)

All 6 in-toto statements signed: `2026-05-18T02:39:56.333340+00:00`  
SBOM signed: `2026-05-18T02:52:13.301282+00:00`

### Step 4 — Policy Updates

`assurance/slsa/l4/level4-policy.json` updated:
- `in_toto_signing_status`: `SCHEMA_DEFINED_NOT_SIGNED` → `KMS_SIGNED_PENDING_EXTERNAL_WITNESS`

`assurance/anchor/anchor-policy.json` created (Block B5):
- `current_release_class: EXTERNAL_VALIDATION`
- `sbom_kms_signed: true`, `in_toto_kms_signed: true`

---

## Post-Migration Posture

| Property | Value |
|----------|-------|
| Signing backend | `aws_kms` (us-east-2) |
| Key alias (assurance signing) | `alias/ethicbit-intoto-signing` |
| Key type | ECC_NIST_P256 |
| Signing algorithm | ECDSA_SHA_256 |
| Key posture status | `PRODUCTION_HSM_READY` |
| Non-exportable | `true` (KMS guarantee) |
| Eligible for sovereign release | `true` (posture; claim still requires human attestation) |
| in-toto chain status | `KMS_SIGNED_PENDING_EXTERNAL_WITNESS` |
| SBOM status | `KMS_SIGNED` |
| in-toto signed at | 2026-05-18T02:39:56.333340+00:00 |
| SBOM signed at | 2026-05-18T02:52:13.301282+00:00 |

---

## Verification Instructions

To independently verify a KMS-signed in-toto statement:

```python
import base64, hashlib, json
from cryptography.hazmat.primitives.asymmetric.ec import ECDSA
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.serialization import load_pem_public_key

# 1. Export the KMS public key
#    aws kms get-public-key --key-id alias/ethicbit-intoto-signing --region us-east-2

# 2. Load a signed statement
statement = json.load(open("assurance/in-toto/attestations/intake.statement.json"))

# 3. Recompute canonical payload (exclude signature fields)
EXCLUDE = {"signature", "signedBy", "signedAt", "signingAlgorithm",
           "payloadSHA256", "verificationStatus"}
payload = json.dumps(
    {k: v for k, v in statement.items() if k not in EXCLUDE},
    sort_keys=True, separators=(",", ":")
).encode()
digest = hashlib.sha256(payload).digest()

# 4. Verify — digest must match payloadSHA256
assert hashlib.sha256(payload).hexdigest() == statement["payloadSHA256"]

# 5. Verify signature
pub = load_pem_public_key(kms_public_key_pem)
sig_bytes = base64.b64decode(statement["signature"])
pub.verify(sig_bytes, digest, ECDSA(SHA256()))  # raises if invalid
```

Full verification script: `scripts/crypto/sign_intoto_statements_kms.py` (contains
`verify_signature()` helper).

---

## Signing Architecture Diagram

```
Pre-migration (TRANSITIONAL_COMPLIANT):
  GitHub Secret (PEM) ─► EnvSigningProvider ─► Ed25519 sig
                       └► ML-DSA fallback     ─► ML-DSA sig
  Combined → hybrid_signature_set.json  (key_posture_status: TRANSITIONAL)

Post-migration (PRODUCTION_HSM_READY):
  AWS KMS (ECC_NIST_P256, non-exportable)
    ├─► sign_intoto_statements_kms.py ─► 6 × statement.json (KMS_SIGNED)
    └─► sign_sbom_kms.py             ─► sbom.cyclonedx.json + .sig.json

  in-toto chain status: KMS_SIGNED_PENDING_EXTERNAL_WITNESS
  (next gate: external witness by criterion 1/2 reviewer)
```

---

## Remaining Migration Gap

The hybrid signature artifacts (`AEM_V1_1_SUPPLY_CHAIN_SIGNATURE_SET.json`) retain
Ed25519 + ML-DSA signatures made under the pre-migration posture. These artifacts are
**not re-signed** under the KMS key because:

1. The hybrid signature set attests the supply chain manifest, which is a different
   artifact class from the in-toto governance chain.
2. Re-signing would invalidate the prior audit trail without adding assurance value.
3. The in-toto chain now provides the authoritative assurance anchor for governance
   operations; the hybrid set remains as a historical CI-grade record.

This gap is documented and does not block EXTERNAL_VALIDATION class operations.

---

## Non-Claims

```
kms_signing_is_fips_validated: false
kms_signing_is_hsm_hardware_certified: false
   (AWS KMS uses HSM internally; EthicBit does not hold separate HSM cert)
kms_signing_constitutes_production_authorization: false
kms_signing_replaces_external_witness_requirement: false
kms_signing_elevates_to_external_validation_pass: false
migration_complete_means_sovereign_release_authorized: false
```

---

## Related Artifacts

| Artifact | Role |
|----------|------|
| `scripts/crypto/sign_intoto_statements_kms.py` | Signing script — in-toto chain |
| `scripts/crypto/sign_sbom_kms.py` | Signing script — SBOM |
| `assurance/in-toto/attestation-index.json` | Chain status record |
| `assurance/sbom/aem_v1_1_sbom.cyclonedx.sig.json` | Detached SBOM signature sidecar |
| `assurance/anchor/anchor-policy.json` | Machine-readable anchor + signing posture policy |
| `assurance/slsa/l4/level4-policy.json` | SLSA enforcement — records `in_toto_signing_status` |
| `assurance/signatures/AEM_V1_1_SUPPLY_CHAIN_CRYPTO_TRUTH.json` | Pre-migration posture record |

---

*Block B1 — EthicBit / CEMU v3.7.0+ — 2026-05-18*
