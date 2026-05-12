# AEM-EVOLVE v4.0 — Externalized Mechanical Ethics Assurance Roadmap

**Document type:** External Validation Roadmap  
**Version:** 4.0 (Roadmap)  
**Status:** `FUTURE_ROADMAP`  
**Constitutional dependency:** EthicBit / CEMU v3.7.0+  
**Prerequisites:** v3.1 AI-ME Gate evidence execution (not yet complete)  
**Date:** 2026-05-12

---

## 1. External Validation Goals

v4.0 targets externalized validation of the complete EthicBit AEM-EVOLVE Mechanical Ethics Assurance stack. It is not a version release — it is a validation gate.

v4.0 is reached only when the following are independently verified:

1. Third-party reproduction of v3.1 AI-ME evidence
2. External security review of the governance infrastructure
3. Managed cloud deployment at a validated target
4. HSM / CloudHSM evidence for key operations
5. AEM v1.1 artifact reverification by third party
6. Triple Anchor external verification of selected artifacts
7. Fast Path independent benchmark review
8. External claim review and public auditability

**Current status:** ROADMAP. None of these have been completed.

---

## 2. Constitutional Dependency

v4.0 is subordinated to the EthicBit / CEMU v3.7.0+ constitutional-operational regime. External validation does not replace the Constitution. It verifies that the technology correctly operationalizes it.

The order of validation in v4.0 mirrors the architectural dependency order:

```
Constitutional equivalence verification
  → AEM v1.1 artifact reverification
    → AI-ME evidence reproduction
      → Claim boundary review
        → Fast Path benchmark review
          → Triple Anchor external verification
            → Strong Closure external evaluation
              → v4.0 External Validation Release
```

---

## 3. Third-Party Reproduction

v4.0 requires third-party reproduction of v3.1 AI-ME evidence by an independent party using the Reproduction Kit (see Section 12).

Requirements for valid third-party reproduction:
- Independent environment (not EthicBit-controlled)
- Execution against published reproduction kit
- Results compared against declared expected outputs
- Hash verification of reproduced artifacts against declared hashes
- AEM v1.1 verification procedures applied to reproduced artifacts
- Report published using the Third-Party Reproduction Report Template

**This is not internal reproduction.** Internal reproduction (Controlled Reproduction) was achieved in v2.0. v4.0 requires externally independent reproduction.

---

## 4. External Security Review

v4.0 requires an external security review of the governance infrastructure, covering:

- AEM v1.1 artifact verification mechanisms
- Fast Path enforcement logic and snapshot security
- Signing key management and key lifecycle
- AI-ME gate implementation security
- Claim boundary enforcement security
- API and endpoint security
- Threat model validation

The security review must be conducted by an independent party with no affiliation to EthicBit.

---

## 5. Managed Cloud Deployment Target

v4.0 targets a managed cloud deployment environment. Requirements:

- Managed compute (not local / developer machine)
- Managed networking with defined ingress/egress controls
- Infrastructure-as-code deployment (reproducible)
- Deployment audit trail

The managed cloud target provides the execution environment for externally reproduced evidence.

---

## 6. Managed PostgreSQL

v4.0 uses a managed PostgreSQL instance for governance record persistence. Requirements:

- Managed PostgreSQL service (not embedded/local)
- Automated backup with tested restore
- Migration history verifiable
- Connection security (TLS, authentication)
- Persistence evidence collected and verified through AEM v1.1

---

## 7. Managed Prometheus / Grafana

v4.0 monitoring requirements:

- Managed Prometheus metrics collection
- Grafana dashboard for governance observability
- Alerting configured for governance events
- Monitoring evidence collected and versioned

---

## 8. HSM / CloudHSM Evidence

v4.0 requires hardware-backed key operations for signing:

- HSM or CloudHSM for signing key operations
- HSM usage logs preserved as evidence artifacts
- AEM v1.1 verification of HSM evidence artifacts
- HSM attestation where available

**Non-claim:** v4.0 does not claim HSM-backed custody of all artifacts. It requires HSM evidence for key signing operations in the external validation target environment.

---

## 9. AEM v1.1 Artifact Reverification

v4.0 requires external reverification of AEM v1.1 artifacts:

- Third party verifies artifact hashes against declared manifests
- Verification procedure follows AEM v1.1 verification model
- Reverification receipts issued by third party
- Discrepancies documented and resolved

AEM v1.1 reverification is distinct from original verification. It is performed by an independent party to confirm integrity.

---

## 10. Triple Anchor External Material Anchor Layer

v4.0 includes Triple Anchor external verification for selected artifacts:

**Triple Anchor safe claim:** Triple Anchor is a subordinate external anchoring layer for selected evidence artifacts.

**Triple Anchor non-claim:** Triple Anchor does not mean every artifact is anchored across Ethereum mainnet, L2, Arweave and AO unless specific anchor receipts exist.

v4.0 external verification requires:
- Verification of existing anchor receipts (`docs/anchors/AEM_V1_1_MAINNET_ANCHOR_RECEIPT.json`)
- Confirmation that anchored hashes match v4.0 reproduced artifacts
- New anchor receipts for v4.0 evidence where applicable

---

## 11. Fast Path Independent Benchmark Review

v4.0 includes an independent benchmark review of Fast Path enforcement:

- Independent measurement of Fast Path enforcement latency
- Latency measured in the managed cloud target environment
- Benchmark methodology documented and reproducible
- Results published with scope qualifiers (Fast Path enforcement only, not full-system)

**Non-claim:** Fast Path benchmark review does not claim full-system validation latency. Full Triple Anchor, Strong Closure, and AI-ME evidence are not recomputed per tick. The benchmark covers Fast Path enforcement scope only.

---

## 12. Reproduction Kit

The v4.0 Reproduction Kit (see `docs/reproduction/THIRD_PARTY_REPRODUCTION_KIT_V4_0.md`) includes:

- Quickstart guide (reproducible in under 30 minutes for scaffold, longer for full evidence)
- Docker / Colima setup or managed cloud setup instructions
- Expected evidence outputs for each AI-ME gate
- Hash verification instructions using AEM v1.1 procedures
- AEM v1.1 artifact verification checklist
- Triple Anchor verification checklist
- Fast Path benchmark checklist
- Report template (see `docs/reproduction/THIRD_PARTY_REPRODUCTION_REPORT_TEMPLATE.md`)
- Claim boundary checklist
- Known limitations
- Submission instructions

---

## 13. Evidence Acceptance Criteria

For v4.0 to be declared as External Validation Release:

| Criterion | Required state |
|---|---|
| Third-party reproduction | Completed by independent party |
| Security review | Completed by independent party |
| Managed cloud deployment | Deployed and evidenced |
| HSM signing | Evidenced |
| AEM v1.1 reverification | Completed by independent party |
| Triple Anchor verification | Selected receipts verified |
| Fast Path benchmark | Independent measurement completed |
| External claim review | Claim boundaries reviewed externally |
| All evidence AEM v1.1 verified | Artifact_verified = true for all required artifacts |

All criteria must be met before v4.0 is claimed as External Validation Release.

---

## 14. External Claim Review

v4.0 includes an external review of claim boundaries:

- Independent reviewer evaluates whether declared claims are supported by reproduced evidence
- Overclaims identified and documented
- Claim boundary adjustments made before v4.0 release
- Final claim set reviewed and published with evidence references

---

## 15. Non-Claims

This document does not claim:

- Third-party reproduction (not yet conducted)
- External certification of any kind
- Managed cloud readiness (not yet deployed)
- HSM-backed custody (not yet implemented for v4.0 target)
- Regulatory approval
- Production readiness
- Complete AI ethics coverage
- Universal public anchoring
- That v4.0 is a current release (it is a future roadmap gate)

---

## 16. Conclusion

v4.0 is EthicBit's external validation gate. It is not claimed as achieved. It is defined as a future milestone with explicit, verifiable criteria.

The path to v4.0 requires:
1. v3.1 AI-ME evidence execution
2. v3.1 implementation completion
3. Fast Path production hardening
4. Third-party reproduction kit finalization
5. External validation engagement

v4.0 seeks external validation of EthicBit AEM-EVOLVE Mechanical Ethics Assurance, including AEM v1.1 artifact reverification, selected Triple Anchor pathways and Fast Path benchmark review.

---

*AEM-EVOLVE v4.0 Externalized Mechanical Ethics Assurance Roadmap — EthicBit / CEMU v3.7.0+ — 2026-05-12*
