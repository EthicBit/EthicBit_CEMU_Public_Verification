# EthicBit LangGraph Integration

**Constitutional dependency:** EthicBit / CEMU v3.7.0+  
**Status:** PASS — `ETHICBIT_LANGGRAPH_INTEGRATION_STATUS=PASS`  
**Version:** 1.0.0 | **Date:** 2026-05-19

Functional integration demo: EthicBit constitutional governance applied to a real LangGraph/LangChain agentic workflow governing tool-calls, state transitions, HITL approval, claim boundaries, and audit receipts.

---

## Quick start

```bash
git clone https://github.com/EthicBit/EthicBit_CEMU_Public_Verification
cd EthicBit_CEMU_Public_Verification/integrations/langgraph

pip install -r requirements.txt
python3 demo_agent.py
```

Expected output:
```
Tool-call trace:
  1. [✓] search_knowledge_base     risk=LOW    decision=AUTO_PASS
  2. [✓] draft_document            risk=MEDIUM decision=AUTO_PASS
  3. [✓] publish_external          risk=HIGH   decision=HITL_APPROVED

Overall: PASS
```

No LLM API key required. The agent is scripted and fully deterministic.

---

## What it demonstrates

| Capability | Result |
|---|---|
| Tool-call governance (risk gate) | PASS |
| Claim Boundary Engine enforcement | PASS |
| HITL required for HIGH-risk action | PASS |
| HITL approval (simulated) resolves to execution | PASS |
| Audit receipt generated per tool call | PASS |
| Audit log persisted | PASS |

---

## How it works

```
HumanMessage
    │
    ▼
[agent node]  ─── scripted tool decision ──►  [governance_gate]
                                                     │
                                        ┌────────────┴────────────┐
                                   AUTO_PASS              HITL_REQUIRED
                                   BLOCK                  → HITL_APPROVED
                                        └────────────┬────────────┘
                                                     ▼
                                             [tool_executor]
                                                     │
                                              (next step or END)
```

**Three tools, three risk levels:**
- `search_knowledge_base` — LOW → AUTO_PASS (read-only)
- `draft_document` — MEDIUM → AUTO_PASS (bounded state mutation)
- `publish_external` — HIGH → HITL_REQUIRED → HITL_APPROVED (external side effect)

---

## Files

```
integrations/langgraph/
  README.md                        — this file
  requirements.txt                 — langgraph, langchain-core
  claim_policy.json                — risk registry + claim boundary
  tools.py                         — 3 governed tools
  ethicbit_langgraph_adapter.py    — governance gate, HITL, CBE, audit log
  demo_agent.py                    — LangGraph StateGraph + scripted agent
  scripts/
    run_langgraph_demo_e2e.sh      — E2E runner (install + run + verify)
  results/
    LANGGRAPH_INTEGRATION_REPORT.json
    audit_log.json
  docs/
    SCOPE_BOUNDARY.md              — what this IS and IS NOT
```

---

## Simulate HITL rejection

```bash
DEMO_HITL_APPROVE=false python3 demo_agent.py
```

Step 3 (`publish_external`) will receive `HITL_REJECTED` — the tool does not execute. The governance receipt records the rejection.

---

## E2E script

```bash
bash scripts/run_langgraph_demo_e2e.sh
```

Installs deps, runs the demo, verifies the report JSON, checks non-claims.

---

## Non-claims

```
integration_is_production_deployment  = false
integration_is_externally_validated   = false
integration_is_security_certified     = false
integration_is_regulatory_approved    = false
hitl_simulation_equals_real_hitl      = false
```

See `docs/SCOPE_BOUNDARY.md` for full boundary definition and production extension path.

---

*EthicBit / CEMU v3.7.0+ — 2026-05-19*
