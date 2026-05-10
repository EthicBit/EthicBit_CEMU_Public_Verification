# Release Notes — AEM-EVOLVE™ v2.0 PR 2

**Date:** 2026-05-10  
**Tag:** `v2.0-pr2`  
**Type:** v2.0 gate — HSM/KMS-backed production signing layer  
**Version:** `0.9.0-demo`

---

## Summary

PR 2 installs the production KMS/HSM signing layer required by the v2.0 Production
Readiness Gate. When `AEM_KMS_PROVIDER` is configured, the server routes all signing
operations through an external KMS/HSM (AWS KMS, GCP Cloud KMS, Azure Key Vault, or
PKCS#11). When not configured, the server falls back to the v1.9 file-based Ed25519
path — the gate honestly reports `HSM_KMS_SIGNING_CHECK=FAIL`.

**Gate result (local/demo environment):** `HSM_KMS_SIGNING_CHECK=FAIL`  
*Expected — gate requires a real external KMS/HSM.*

**Test suite:** `164 passed, 10 skipped`

---

## Changes

### `tools/signing/production_kms_provider.py` (new)
- `ProductionKmsConfig` frozen dataclass: `provider`, `key_id`, `region`, `project`, `vault_url`, `algorithm`, `non_exportable`
- `load_kms_config()` reads `AEM_KMS_PROVIDER`, `AEM_KMS_KEY_ID`, and provider-specific env vars
- `_AuditLog` — thread-safe key-usage audit log (sign/verify counts + entry list)
- `ProductionKmsProvider(SigningProvider)` — wraps backend + audit log
  - `from_env()` — returns None when `AEM_KMS_PROVIDER` not set
  - `sign()` / `verify()` / `public_key_pem()` — delegate to backend + audit log
  - `algorithm()` — returns `KMS/<provider>/<algorithm>`
  - `gate_check()` — structured gate status dict for /health and assurance
- `_load_backend()` — routes to KmsSigningProvider, Pkcs11SigningProvider, _GcpKmsSigningProvider, _AzureKeyVaultSigningProvider
- `_GcpKmsSigningProvider` — GCP Cloud KMS via google-cloud-kms (graceful ImportError)
- `_AzureKeyVaultSigningProvider` — Azure Key Vault via azure-keyvault-keys (graceful ImportError)

### `main.py` (modified)
- `_init_signing_provider()` — KMS path added as priority (0) before env/file paths
- `_production_kms_provider` — module-level ref to KMS provider when active
- `/health` adds `kms_signing_gate` structured dict
- Version bumped to `0.9.0-demo`

### `tools/production_readiness/verify_kms_signing.py` (new)
- 10-check gate verifier
- C-01: AEM_KMS_PROVIDER configured (FAIL in demo — correct)
- C-02: production_kms_provider importable
- C-03: all four provider types supported
- C-04: load_kms_config returns None when unset
- C-05: from_env() mirrors config result
- C-06–C-10: key accessibility, sign/verify round-trip, non-exportable posture, audit log

### `tests/test_kms_signing_enforcement.py` (new)
- `TestKmsConfig` — 7 tests: config loading, frozen dataclass, defaults
- `TestProductionKmsProviderInit` — 5 tests: from_env, gate_check, error handling
- `TestAuditLog` — 4 tests with mock backend: sign/verify counts, gate_check pass
- `TestHealthKmsGate` — 4 tests: health fields, NOT_CONFIGURED, version
- **20 passed** in isolation

### Assurance artifact
- `assurance/evolve-multi-agent/v2_0/kms_signing_check_report.json`

---

## Gate result (assurance artifact)

```json
{
  "gate": "HSM_KMS_SIGNING_CHECK",
  "result": "FAIL",
  "fail_reason": "AEM_KMS_PROVIDER not configured — KMS/HSM provider required"
}
```

`FAIL` is the honest and correct result for a local/demo environment.

---

## Supported backends

| `AEM_KMS_PROVIDER` | Backend | SDK required |
|---|---|---|
| `aws_kms` | AWS KMS | boto3 |
| `gcp_kms` | GCP Cloud KMS | google-cloud-kms |
| `azure_key_vault` | Azure Key Vault | azure-keyvault-keys, azure-identity |
| `pkcs11` | PKCS#11 HSM | pkcs11 |

---

## Non-claims

```
HSM_KMS_SIGNING_CHECK=FAIL — gate not satisfied in local/demo environment.
This PR does not certify FIPS compliance.
This PR does not certify HSM tamper-proof status.
This PR does not grant regulatory approval.
This PR is not production-ready by itself.
PASS requires a real KMS/HSM — not a local software key.
This release is not regulatory approval.
This release is not external certification.
```
