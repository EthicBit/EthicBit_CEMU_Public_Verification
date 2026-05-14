# v4.0 HSM / KMS Signing Evidence Plan

**Criterion:** 4 — hsm_signing
**Status:** PENDING_EXTERNAL
**Controlled assessment:** CONTROLLED_ASSESSMENT_PASS_SOFTWARE_SIGNING_CODE_TIER (2026-05-14)
**Artifact:** `assurance/v4_0/evidence/V4_0_04_HSM_SIGNING_ARTIFACT.json`
**Constitutional dependency:** EthicBit / CEMU v3.7.0+

---

## What this criterion requires

AEM-EVOLVE governance events and receipts must be signed using a managed HSM or cloud KMS with a non-exportable key. Software-tier Ed25519 file-based signing does NOT satisfy this criterion. `AEM_KMS_PROVIDER` must be set to a live managed KMS endpoint.

---

## What was already verified internally (software tier — 48/48 checks)

| Verifier | Result | Checks |
|---|---|---|
| verify_hsm_signing_providers.py | PASS | 10/10 — PKCS11 + KMS classes importable, software fallback drop-in |
| verify_key_persistence.py | PASS | 10/10 — Ed25519 load, sign/verify roundtrip, same pubkey |
| verify_signing_provider.py | PASS | 8/8 — ABC interface, tamper rejected, missing sig fields handled |
| verify_signed_receipts.py | PASS | 10/10 — /start event and /receipt endpoint signature valid |
| verify_read_time_signatures.py | PASS | 10/10 — read-time verification, tampered sig rejected |
| verify_kms_signing.py (PR2) | FAIL | 9/10 — AEM_KMS_PROVIDER not set (correct fail-closed) |

Current signing state: `Ed25519 FILE_BASED` — software key, not HSM-backed.

---

## What must be provisioned externally

### Supported KMS providers

| Provider | Value for AEM_KMS_PROVIDER |
|---|---|
| AWS KMS | `aws_kms` |
| GCP Cloud KMS | `gcp_kms` |
| Azure Key Vault | `azure_key_vault` |
| PKCS11 HSM | `pkcs11` |

### Environment variables required

```bash
AEM_KMS_PROVIDER=<aws_kms|gcp_kms|azure_key_vault|pkcs11>
AEM_KMS_KEY_ID=<key ARN (AWS) / resource name (GCP) / key ID (Azure) / PKCS11 URI>
AEM_KMS_REGION=<cloud region — AWS and GCP only>
```

### Key provisioning requirements

```
Key algorithm:     RSA-4096 or EC P-256 (provider-dependent)
Exportable:        False (non-exportable posture required)
Rotation policy:   Define and document
Access policy:     Least-privilege — AEM-EVOLVE service account only
Audit logs:        Active in KMS provider
```

### Steps to complete criterion 4

```bash
# 1. Provision managed KMS key (non-exportable)
# AWS example:
aws kms create-key --description "AEM-EVOLVE signing key" --key-usage SIGN_VERIFY

# 2. Set env vars
export AEM_KMS_PROVIDER=aws_kms
export AEM_KMS_KEY_ID=arn:aws:kms:<region>:<account>:key/<key-id>
export AEM_KMS_REGION=<region>

# 3. Run KMS signing verifier (must now PASS)
python3 demos/aem-evolve-multi-agent-api/tools/signing/verify_kms_signing.py
# Expected: HSM_KMS_SIGNING_CHECK=PASS 10/10

# 4. Run sign/verify roundtrip with live KMS endpoint
python3 demos/aem-evolve-multi-agent-api/tools/signing/verify_key_persistence.py
python3 demos/aem-evolve-multi-agent-api/tools/signing/verify_signed_receipts.py

# 5. Collect KMS audit log entry confirming signing operation
```

KMS provider module: `demos/aem-evolve-multi-agent-api/tools/signing/production_kms_provider.py`

---

## Required output

- KMS provider selected (aws_kms / gcp_kms / azure_key_vault / pkcs11)
- Key ID (ARN or resource name — redact sensitive parts as needed)
- Non-exportable posture confirmed
- Sign/verify roundtrip output with live KMS endpoint
- verify_kms_signing.py output (PASS 10/10 expected)
- Audit log entry from KMS provider confirming signing operation
- Key rotation policy documented
- Access policy documented

---

## Non-claim

All software-tier signing verifiers pass (48/48). `AEM_KMS_PROVIDER` is not set. Current signing uses Ed25519 file-based key, not a managed HSM. The PR2 gate `HSM_KMS_SIGNING_CHECK` fails correctly with fail-closed behavior. HSM/KMS signing evidence requires `AEM_KMS_PROVIDER` configured against a real external managed KMS with a non-exportable key.
