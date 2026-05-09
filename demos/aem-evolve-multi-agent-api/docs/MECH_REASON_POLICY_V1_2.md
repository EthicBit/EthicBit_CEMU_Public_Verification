# MECH-REASON™ Policy v1.2 — AEM-EVOLVE™

**Type:** Policy-as-code constitutional baseline
**Version:** v1.2.0

---

## Purpose

`AEM_EVOLVE_POLICY_V1_2.json` is the constitutional policy document for MECH-REASON™. All governance rules are evaluated deterministically by the mechanical engine. No LLM evaluates or overrides these rules.

## Rule families

| Family | Rules | Trigger outcome |
|---|---|---|
| R-CLAIM-* | 10 claim boundary rules | FAIL_CLOSED |
| R-HITL-* | 4 HITL inference rules | ESCALATE_TO_HITL |
| R-SCOPE-* | 3 scope-limiting rules | SCOPE_LIMITED |

## Decision priority

```
FAIL_CLOSED > ESCALATE_TO_HITL > SCOPE_LIMITED > PASS
```

## How to run

```bash
python3 demos/aem-evolve-multi-agent-api/tools/reasoning/claim_boundary_checker.py
# CLAIM_BOUNDARY_CHECK=PASS
```

## Supported claim

> AEM-EVOLVE™ v1.2 adds deterministic policy-as-code and claim-boundary checking for controlled governance evidence.
