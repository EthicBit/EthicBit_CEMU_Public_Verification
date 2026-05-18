# Criterion 2 — External Security Review Package

**Criterion:** Independent external security review  
**Status:** `PENDING_EXTERNAL` — awaiting external reviewer  
**Package version:** 2.0 | **Date:** 2026-05-18  
**HEAD commit:** `66fbce1d`

---

## What the reviewer must do

1. Review the threat model and assess coverage and accuracy.
2. Evaluate KMS signing implementation (key management, IAM posture, signing scripts).
3. Review the SBOM for completeness and any high-severity components.
4. Assess the CI/CD pipeline security (workflow permissions, supply chain).
5. Review the pre-commit and PR gate security hooks.
6. Issue a scoped attestation covering the items actually reviewed.

---

## Primary artifacts for review

### Threat model (STRIDE / LINDDUN / MITRE ATLAS)
`assurance/threat-model/threat-model.json`  
21 threats across 7 components. 9 HIGH, 10 MEDIUM, 2 LOW.  
Reviewer should: confirm or challenge risk ratings; identify threats not in scope; verify mitigations are implemented.

### KMS key management
- Signing key: `alias/ethicbit-intoto-signing` (ECC_NIST_P256, us-east-2)
- Runtime key: `alias/ethicbit-kms-signing` (separate, not used for artifact signing)
- Scripts: `scripts/crypto/sign_intoto_statements_kms.py`, `scripts/crypto/sign_sbom_kms.py`
- Signed artifacts: 6 in-toto statements (`assurance/in-toto/attestations/*.json`) + SBOM sidecar (`assurance/sbom/aem_v1_1_sbom.cyclonedx.sig.json`)

Reviewer should: verify ECDSA_SHA_256 signatures are structurally valid; assess IAM least-privilege posture; check for key ID exposure in public files.

### SBOM
`assurance/sbom/aem_v1_1_sbom.cyclonedx.json` — 654 components, CycloneDX 1.5, KMS-signed  
`assurance/sbom/aem_v1_1_sbom.cyclonedx.sig.json` — detached signature sidecar  
Reviewer should: scan for known CVEs in listed components; verify signature block is present and correctly structured; check for any `purl` entries with known-vulnerable versions.

### CI/CD security
`.github/workflows/slsa-build.yml` — minimal permissions (`contents: read`, `id-token: write`), `persist-credentials: false`, `--ignore-scripts`  
`.github/workflows/pr-gate.yml` — 5 jobs on all PRs  
`.github/workflows/slsa_hybrid_attest.yml` — hybrid signing workflow  
Reviewer should: check for permission escalation paths; verify action version pinning; assess `workflow_dispatch` exposure (STR-003 in threat model).

### Security hooks
`scripts/hooks/check_no_aws_ids.py` — blocks RDS, EC2, Cognito, KMS UUIDs  
`.pre-commit-config.yaml` — `detect-private-key` hook included  
Reviewer should: test hook effectiveness against sample inputs; verify allowlist paths are appropriate.

### Internal bug bounty simulation
`assurance/security/INTERNAL_BUG_BOUNTY_SIMULATION.md`  
5 simulated reports. 2 open known gaps (SIM-003: `workflow_dispatch` exposure; SIM-004: non-DSSE in-toto envelope).  
Reviewer should: agree or disagree with severity ratings; identify gaps not covered.

---

## NIST AI RMF and ISO 42001 alignment
`docs/assurance/NIST_AI_RMF_MAPPING.md` — MEASURE section covers testing and monitoring  
`docs/assurance/ISO_42001_MAPPING.md` — Clause 6.1 covers risk assessment  
Reviewer may reference these for compliance framing but is not required to evaluate them.

---

## What constitutes a SECURITY_REVIEW_PASS

- Threat model reviewed; no critical unmitigated HIGH threats identified that are absent from the model.
- KMS signing implementation assessed as structurally sound.
- SBOM reviewed; no critical CVEs in core components (or exceptions documented).
- CI/CD permissions reviewed; no privilege escalation path identified.
- Reviewer issues scoped attestation identifying what was reviewed and what was not.

## Non-claims

- Security review does **not** constitute penetration testing.
- Security review does **not** constitute regulatory cybersecurity certification.
- A scoped SECURITY_REVIEW_PASS applies only to the declared review scope and snapshot.

---

## Attestation template

```
CRITERION_2_EXTERNAL_SECURITY_REVIEW_ATTESTATION
Reviewer: [name / org / affiliation]
Date: [ISO date]
Commit reviewed: [git SHA]
Items reviewed: [threat model / KMS signing / SBOM / CI-CD / hooks / all]
Threat model: [agreed / disagreed / additions noted]
Critical unmitigated threats found: [yes/no — list if yes]
KMS implementation: [sound / concerns noted]
SBOM: [no critical CVEs / CVEs noted]
CI/CD: [no escalation path / concerns noted]
Result: [SECURITY_REVIEW_PASS / SECURITY_REVIEW_PARTIAL / SECURITY_REVIEW_FAIL]
Scope: [explicit limitations]
Signature: [PGP / GitHub commit / other]
```

---

## New since 2026-05-14 (relevant to this criterion)

- `assurance/threat-model/threat-model.json` — STRIDE/LINDDUN/MITRE ATLAS (Block D, new)
- `docs/assurance/NIST_AI_RMF_MAPPING.md` — MEASURE + MANAGE sections (Block D, new)
- `docs/assurance/ISO_42001_MAPPING.md` — Annex A.2.2 AI risk assessment (Block D, new)
- `assurance/sbom/aem_v1_1_sbom.cyclonedx.sig.json` — SBOM now KMS-signed (Block B4, new)
- `scripts/hooks/check_no_aws_ids.py` — AWS ID sanitization hook (Block E, new)
- `assurance/security/INTERNAL_BUG_BOUNTY_SIMULATION.md` — 5 SIMs, 2 open gaps (Block E, new)
- `docs/assurance/INCIDENT_RUNBOOK.md` — 5 incident runbooks (Block E, new)
- `docs/assurance/FRAMEWORK_COMPARATIVE_ANALYSIS.md` — vs SLSA/in-toto/SSDF (Block D, new)
