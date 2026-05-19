# Scope Boundary — EthicBit LangGraph Integration

**Version:** 1.0.0  
**Date:** 2026-05-19  
**Constitutional dependency:** EthicBit / CEMU v3.7.0+

---

## What this integration IS

A functional demonstration that EthicBit constitutional governance can be applied to a real LangGraph/LangChain agentic workflow. It shows:

- **Tool-call governance**: every tool call passes through a risk-classification gate before execution.
- **Claim Boundary Engine**: the CBE is enforced at adapter initialization and per tool call — no overclaims are possible at the code level.
- **HITL gating**: HIGH-risk tool calls require human-in-the-loop approval before execution. In demo mode, this is simulated via `DEMO_HITL_APPROVE` env var.
- **Audit receipt**: every governed tool call produces a `GovernanceReceipt` JSON with decision, risk level, args hash, and constitutional dependency.
- **Reproducibility**: no LLM API key required. The agent script is deterministic. Any reviewer can clone and run `bash scripts/run_langgraph_demo_e2e.sh` and get `PASS`.

---

## What this integration IS NOT

```
integration_is_production_deployment   = false
integration_is_externally_validated    = false
integration_is_security_certified      = false
integration_is_regulatory_approved     = false
integration_is_universal_adapter       = false
hitl_simulation_equals_real_hitl       = false
```

- **Not a production deployment** — the integration runs in a controlled demo environment. No real external systems are called.
- **Not externally validated** — this integration has not been reviewed by an independent external party. It is governed internally by EthicBit/CEMU.
- **Not security certified** — no penetration test or formal security audit has been conducted on this integration.
- **Not regulatory approved** — does not constitute compliance with any regulatory framework.
- **HITL is simulated in demo mode** — `DEMO_HITL_APPROVE=true` auto-approves HIGH-risk actions. In a real deployment, HITL must be replaced with a real human approval mechanism (e.g., the `/approve` endpoint of the AEM-EVOLVE API).

---

## Extending to a real deployment

| Component | Demo | Production path |
|-----------|------|-----------------|
| LLM | Scripted (no API key) | Replace `SCRIPT` in `demo_agent.py` with a real `ChatModel` |
| HITL | `DEMO_HITL_APPROVE` env var | Wire to `POST /approve` on AEM-EVOLVE API |
| Audit log | JSON file | Stream to PostgreSQL adapter |
| Tool registry | 3 in-memory tools | Register real tools in `TOOL_REGISTRY` |
| Claim boundary | `claim_policy.json` | Extend with production claim classes |

---

*EthicBit / CEMU v3.7.0+ — 2026-05-19*
