# HITL Signature Verification — AEM-EVOLVE™ v1.1

**Type:** Demo HITL signature verification
**Version:** v1.1.0

---

## Purpose

AEM-EVOLVE™ v1.1 adds demo HITL signature verification to harden the human-in-the-loop boundary.

The verifier checks that:
- `HUMAN_DECISIONS.json` exists and is well-formed
- Each decision has a valid actor, role, timestamp, and decision value
- A canonical SHA-256 hash can be computed per decision (demo signing)

## Explicit identity boundary

| Claim | Status |
|---|---|
| Demo-grade verification | ✓ |
| HSM-backed signing | Not claimed |
| Enterprise IAM | Not claimed |
| Production identity provider | Not claimed |
| Cybersecurity certified | Not claimed |

## How to run

```bash
python3 demos/aem-evolve-multi-agent-api/tools/hitl/HITL_signature_verifier.py
```

Expected output:

```
HITL_SIGNATURE_VERIFICATION=PASS_DEMO
```

Report generated at: `assurance/evolve-multi-agent/v1_1/hitl_signature_verification_report.json`

## Supported claim

> AEM-EVOLVE™ v1.1 adds demo HITL signature verification for controlled governance evidence.
