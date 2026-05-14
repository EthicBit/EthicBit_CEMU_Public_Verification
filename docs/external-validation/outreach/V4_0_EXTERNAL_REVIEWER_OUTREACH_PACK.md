# AEM-EVOLVE™ v4.0 External Reviewer Outreach Pack

**Status:** ACTIVE — external validation process initiated  
**Initiation date:** 2026-05-14  
**Posture:** EXTERNAL_VALIDATION_IN_PROGRESS  
**Constitutional dependency:** EthicBit / CEMU v3.7.0+

---

## Outreach Message

We are inviting you to perform an external validation review for EthicBit / AEM-EVOLVE.

Current state:
AEM-EVOLVE v3.1 evidence PASS
Fast Path v1.0 evidence PASS
v4.0 controlled evidence partial: 3/8 criteria controlled pass, 5/8 pending external

Scope:
third-party reproduction, external security review, managed cloud deployment evidence, HSM/KMS signing evidence, and external claim review.

Public verification mirror:
https://github.com/EthicBit/EthicBit_CEMU_Public_Verification

Latest release:
https://github.com/EthicBit/EthicBit_CEMU_Public_Verification/releases/tag/aem-evolve-v3.1-v4-controlled-evidence-2026-05-12

Important boundary:
This is not a request for regulatory approval, clinical validation, financial advice, cybersecurity certification, or universal production-readiness certification. The review should be limited to the evidence actually inspected and reproduced.

---

## Current Evidence State

| Layer | Status |
|---|---|
| AEM v2.0 baseline | PASS — 14/14 gates, 140/140 checks |
| AEM-EVOLVE v3.0 | RELEASED |
| AI-ME v3.1 | EVIDENCE_PASS — 12/12 gates, artifact_verified=true all |
| Fast Path v1.0 | EVIDENCE_PASS — 9/9 scenarios, 7/7 mandatory rules |
| Sepolia anchor | ONCHAIN — block 10840044 — covers v3.1+FastPath hashes |
| v4.0 controlled | 3/8 CONTROLLED_PASS |

Sepolia anchor TX: `0xc5908653fa5fc60db913a21ae021d7037f6d35365e8dbaf90c55a6fb86ec4bc0`

---

## Pending External Criteria (5/8)

| # | Criterion | What reviewer provides |
|---|---|---|
| 1 | Third-party reproduction | Independent reproduction in a separate environment |
| 2 | External security review | Independent security review with no EthicBit affiliation |
| 3 | Managed cloud deployment | Deployment evidence in a managed cloud environment |
| 4 | HSM / KMS signing | Signing evidence using a managed HSM or cloud KMS |
| 5 | External claim review | Independent review of claim boundaries |

---

## Reviewer Request

We are seeking external review for one or more of the following:

1. Reproduce selected evidence from a fresh clone in an independent environment.
2. Review repository security posture and claim boundaries.
3. Review managed cloud deployment evidence.
4. Review HSM / managed-key signing evidence when available.
5. Review public claims and non-claims for accuracy.

---

## Quick Start (Reproduction)

```bash
git clone https://github.com/EthicBit/EthicBit_CEMU_Public_Verification
cd EthicBit_CEMU_Public_Verification
git checkout aem-evolve-v3.1-v4-controlled-evidence-2026-05-12

# Run AI-ME v3.1 evidence
python3 demos/aem-evolve-multi-agent-api/tools/ai_me/run_ai_me_evidence_v3_1.py
# Expected: PASS 12/12

# Run Fast Path v1.0 evidence
python3 demos/aem-evolve-multi-agent-api/tools/fast_path/run_fast_path_evidence_v1_0.py
# Expected: EVIDENCE_PASS 9/9

# Run v4.0 controlled evidence
python3 demos/aem-evolve-multi-agent-api/tools/v4_0/run_v4_0_evidence.py
# Expected: CONTROLLED_EVIDENCE_PARTIAL 3/8
```

Full instructions: `docs/reproduction/THIRD_PARTY_REPRODUCTION_KIT_V4_0.md`

---

## Scope Boundary

This review does not ask reviewers to:
- Certify EthicBit or AEM-EVOLVE
- Approve regulatory compliance
- Validate clinical use
- Validate financial advice
- Confirm production readiness

The review should be limited to the evidence actually inspected and reproduced.

---

## Review Output Requested

- Reviewer name / organization
- Review date
- Environment used (OS, Python version, cloud provider if applicable)
- Commit or tag reviewed
- Commands executed
- Evidence reviewed
- PASS / FAIL / PARTIAL conclusion per criterion
- Deviations or limitations observed
- Claim boundary edits recommended, if any
- Signature or attestation, if applicable

Use template: `docs/reproduction/THIRD_PARTY_REPRODUCTION_REPORT_TEMPLATE.md`

---

## Non-Claims

This outreach pack does not claim:

```
v4.0 validated — NOT claimed
third-party reproduced — NOT claimed
externally certified — NOT claimed
production-ready — NOT claimed
regulatory-approved — NOT claimed
clinical validation — NOT claimed
financial advice — NOT claimed
cybersecurity certification — NOT claimed
universal production-readiness — NOT claimed
```

---

*AEM-EVOLVE™ v4.0 External Reviewer Outreach Pack — EthicBit / CEMU v3.7.0+ — 2026-05-14*
