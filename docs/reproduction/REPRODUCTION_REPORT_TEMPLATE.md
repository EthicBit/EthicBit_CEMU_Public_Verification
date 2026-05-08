# AEM-EVOLVE™ v0.3.1-demo — Independent Reproduction Report

**Template version:** 1.0  
**Instructions:** Fill in every field. Do not omit failures. Submit to `independent-reproductions/` via pull request.  
**Filename convention:** `REPORT_<your-handle>_<YYYY-MM-DD>.md`

---

## Reproducer Information

| Field | Value |
|---|---|
| Handle / Name | <!-- your GitHub handle or name --> |
| Organization (optional) | <!-- institution or employer, if applicable --> |
| Date of reproduction | <!-- YYYY-MM-DD --> |
| Environment | <!-- e.g. Ubuntu 22.04 VM / macOS 14 / Docker python:3.11-slim / GitHub Codespaces --> |
| Python version | <!-- output of: python3 --version --> |
| openssl version | <!-- output of: openssl version --> |
| Relationship to EthicBit | <!-- none / collaborator / employee — be honest --> |

---

## Repository

| Field | Value |
|---|---|
| Repo cloned from | `https://github.com/EthicBit/EthicBit_CEMU.git` |
| Commit checked out | <!-- output of: git log --oneline -1 --> |
| Expected commit | `c634f906` |
| Commit match | <!-- YES / NO --> |

---

## Check Results

### Check 1 — File integrity

```
# Command run:
python3 scripts/core/run_aem_evolve_multi_agent_reproduction_challenge.py

# Full output:
[paste here]
```

**Result:** <!-- ALL_MATCH / FAIL / ERROR -->  
**Notes:** <!-- any deviations, warnings, or observations -->

---

### Check 2 — Ed25519 signature verification

```
# Command run:
bash demos/aem-evolve-multi-agent-api/scripts/verify_demo_receipt_signatures.sh

# Full output:
[paste here]
```

**Result:** <!-- PASS / FAIL -->  
**Notes:**

---

### Check 3 — E2E smoke test

```
# Command run:
bash demos/aem-evolve-multi-agent-api/scripts/run_demo_e2e.sh

# Full output:
[paste here]
```

**Result:** <!-- PASS / PARTIAL / FAIL -->  
**Sub-checks:**

| Sub-check | Result |
|---|---|
| `EVOLUTION_EVENT_CREATED` | <!-- PASS / FAIL --> |
| `EVOLUTION_RECEIPT_CREATED` | <!-- PASS / FAIL --> |
| `HITL_APPROVAL_GATE` | <!-- PASS / FAIL --> |
| `AUDIT_TABLES` | <!-- PASS / FAIL --> |
| `AEM_EVOLVE_MULTI_AGENT_API_DEMO_STATUS` | <!-- PASS / FAIL --> |

**Notes:**

---

### Check 4 — Auth controls

```
# Command run:
bash demos/aem-evolve-multi-agent-api/scripts/verify_auth_controls.sh

# Full output:
[paste here]
```

**Result:** <!-- PASS / FAIL -->  
**Notes:**

---

### Check 5 — Tamper checklist

```
# Command run:
bash demos/aem-evolve-multi-agent-api/scripts/run_tamper_checklist.sh

# Full output:
[paste here]
```

**Result:** <!-- PASS / FAIL -->  
**Notes:**

---

### Check 6 — Audit chain verification

```
# Command run:
python3 scripts/core/verify_aem_evolve_multi_agent_audit_chain.py

# Full output:
[paste here]
```

**Result:** <!-- PASS / FAIL -->  
**Notes:**

---

## Overall Reproduction Result

| Metric | Value |
|---|---|
| Checks attempted | <!-- N of 6 --> |
| Checks passed | <!-- N --> |
| Checks failed | <!-- N --> |
| Overall result | <!-- FULL_PASS / PARTIAL / FAIL --> |
| Time to complete | <!-- approximate, e.g. 22 minutes --> |

---

## Observations

<!-- Any deviations from the guide, environmental issues, unexpected behavior, or suggestions for improving the reproduction package. Failures and partial results are valuable — do not omit them. -->

---

## Reproduction Statement

> I confirm that I executed the above checks independently, in a separate environment not controlled by EthicBit, using only the publicly available repository at the pinned commit. The results above are accurate to the best of my knowledge.

**Signed:** <!-- your handle or name -->  
**Date:** <!-- YYYY-MM-DD -->

---

## Non-Claims

This report confirms behavioral reproduction of a technical demonstration. It does not constitute:
- A security audit.
- A production readiness assessment.
- Regulatory or clinical validation.
- An endorsement of any commercial claim.
