# AEM-EVOLVE™ v1.3 — Independent Reproduction Challenge

**Version:** 1.3.0
**Tag:** `v1.3.0` (pending release)
**Challenge status:** Open
**External reproductions received:** 0

---

## What counts as a valid reproduction

A valid independent reproduction must:

1. Clone this repository at tag `v1.3.0` on a machine you control
2. Run `python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_3.py`
3. Obtain `FULL_STACK_VERIFICATION=PASS` (12/12 checks)
4. Submit a reproduction report using the template below

You do NOT need an Anthropic API key — the LLM advisory adapter runs in simulation mode without one and still emits `LLM_ADVISORY_STATUS=PASS`.

---

## Minimum environment

| Requirement | Version |
|---|---|
| Python | ≥ 3.11 |
| OS | macOS / Linux / Windows WSL |
| Git | Any |
| Network | Not required (all checks are local) |

No additional packages required for the default verification run.

---

## How to reproduce

```bash
git clone https://github.com/EthicBit/EthicBit_CEMU.git
cd EthicBit_CEMU
git checkout v1.3.0

python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_3.py
# Expected: FULL_STACK_VERIFICATION=PASS  (12/12)
```

---

## Reproduction report template

```markdown
## AEM-EVOLVE™ v1.3 Independent Reproduction Report

**Date:** YYYY-MM-DD
**Reproducer:** [name or handle — can be anonymous]
**Tag verified:** v1.3.0
**Environment:** [OS, Python version]

### Results

FULL_STACK_VERIFICATION=PASS | FAIL
Passed: X/12

[Paste output of verify_all_v1_3.py here]

### Deviations (if any)

[Note any checks that failed and why]

### Declaration

I independently cloned and ran the verification suite.
I have no affiliation with EthicBit unless disclosed here.
```

Submit reports via GitHub Issue with label `independent-reproduction`.

---

## What this challenge does NOT certify

- Regulatory approval of any kind
- Legal compliance certification
- External audit equivalence
- Production readiness certification
