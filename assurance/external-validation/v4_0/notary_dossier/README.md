# AEM-EVOLVE v4.0 Notary Dossier

**Status:** `DOSSIER_STRUCTURE_DEFINED`  
**Human attestation:** `PENDING`  
**External validation pass claimed:** `false`

This directory is the canonical scaffold for the AEM-EVOLVE v4.0 Notary Dossier.

The dossier packages automated, hash-verifiable support evidence for scoped external human review. It is intended to support review of integrity, methodology, scope, limitations, and claim-boundary sufficiency.

## Current Contents

```text
README.md
DOSSIER_MANIFEST.json
HUMAN_ATTESTATION_TEMPLATE.md
NON_CLAIMS.md
```

## Future Generated Contents

Future PRs may add generated evidence artifacts such as:

```text
DOSSIER_HASH_RECORD.txt
AUTOMATED_REPRODUCTION_REPORT.json
AUTOMATED_SECURITY_REVIEW_SUMMARY.json
CLAIM_BOUNDARY_RED_TEAM_REPORT.json
CLOUD_KMS_EVIDENCE_SUMMARY.json
ANCHOR_REFERENCE_SUMMARY.json
METHODOLOGY_REVIEW.md
```

## Builder / Verifier Scaffold

HV-4 adds local scaffold tools for dossier construction and verification:

```bash
python3 tools/external_validation/build_v4_notary_dossier.py --dry-run
python3 tools/external_validation/verify_v4_notary_dossier.py --structure-only
```

The builder can generate `DOSSIER_HASH_RECORD.txt` when run without `--dry-run`. The verifier can validate the scaffold in `--structure-only` mode or validate a generated hash record when present.

These tools may emit `DOSSIER_BUILT`, `DOSSIER_VERIFIED`, `DOSSIER_INCOMPLETE`, `DOSSIER_FAIL_CLOSED`, or `HUMAN_ATTESTATION_PENDING`. They must not emit or claim `EXTERNAL_VALIDATION_PASS`.

## Boundary

This scaffold does not claim completed external validation, completed human attestation, completed third-party reproduction, completed external security review, completed external claim review, external certification, regulatory approval, cybersecurity certification, clinical readiness, financial advice, legal compliance, or universal production readiness.
