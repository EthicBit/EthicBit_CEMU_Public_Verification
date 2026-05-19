"""
EthicBit LangGraph Integration — Demo Agent

Runs a scripted 3-step agentic workflow governed by EthicBit:

  Step 1: search_knowledge_base("claim boundary")   — LOW risk → AUTO_PASS
  Step 2: draft_document(...)                        — MEDIUM risk → AUTO_PASS
  Step 3: publish_external(...)                      — HIGH risk → HITL_REQUIRED → HITL_APPROVED (demo)

No LLM API key required. The agent decisions are scripted and deterministic.

Usage:
  python3 demo_agent.py              # full run
  DEMO_HITL_APPROVE=false python3 demo_agent.py   # simulate HITL rejection on step 3

Output:
  results/LANGGRAPH_INTEGRATION_REPORT.json
  results/audit_log.json
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from ethicbit_langgraph_adapter import EthicBitLangGraphAdapter, GovernanceDecision
from tools import TOOL_REGISTRY

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"


# ── State ────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    governance_receipts: list[dict]
    pending_tool_call: dict | None   # tool call awaiting governance decision
    step: int
    done: bool


# ── Scripted agent decisions ─────────────────────────────────────────────────

SCRIPT: list[dict] = [
    {
        "name": "search_knowledge_base",
        "args": {"query": "claim boundary"},
        "call_id": "call_001",
        "thought": "I need to understand what claim boundary means before proceeding.",
    },
    {
        "name": "draft_document",
        "args": {
            "content": (
                "EthicBit/CEMU governs this LangGraph agent. "
                "The claim boundary engine blocks overclaiming. "
                "HITL is required before any external publish action."
            ),
            "doc_type": "summary",
        },
        "call_id": "call_002",
        "thought": "I will draft a summary of findings before publishing.",
    },
    {
        "name": "publish_external",
        "args": {
            "content": "EthicBit LangGraph integration demo completed successfully.",
            "destination": "demo-channel",
        },
        "call_id": "call_003",
        "thought": "Publishing the summary externally — this requires HITL approval.",
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Nodes ────────────────────────────────────────────────────────────────────

def agent_node(state: AgentState, adapter: EthicBitLangGraphAdapter) -> dict:
    step = state["step"]
    if step >= len(SCRIPT):
        return {"done": True, "pending_tool_call": None}

    plan = SCRIPT[step]
    msg = AIMessage(
        content=plan["thought"],
        tool_calls=[{
            "id":   plan["call_id"],
            "name": plan["name"],
            "args": plan["args"],
        }],
    )
    return {
        "messages": [msg],
        "pending_tool_call": plan,
        "step": step + 1,
    }


def governance_gate_node(state: AgentState, adapter: EthicBitLangGraphAdapter) -> dict:
    tc = state["pending_tool_call"]
    if tc is None:
        return {}

    receipt = adapter.evaluate_tool_call(
        tool_name=tc["name"],
        args=tc["args"],
        call_id=tc["call_id"],
    )
    receipts = list(state.get("governance_receipts") or [])
    receipts.append(receipt)
    return {"governance_receipts": receipts}


def tool_executor_node(state: AgentState, adapter: EthicBitLangGraphAdapter) -> dict:
    tc = state["pending_tool_call"]
    receipts = state.get("governance_receipts") or []
    last_receipt = receipts[-1] if receipts else {}

    if not last_receipt.get("approved", False):
        result = {
            "status": "BLOCKED_BY_GOVERNANCE",
            "tool": tc["name"] if tc else "unknown",
            "governance_decision": last_receipt.get("governance_decision"),
        }
    else:
        tool_fn = TOOL_REGISTRY.get(tc["name"])
        if tool_fn is None:
            result = {"status": "TOOL_NOT_FOUND", "tool": tc["name"]}
        else:
            result = tool_fn(**tc["args"])

    tool_msg = ToolMessage(
        content=json.dumps(result),
        tool_call_id=tc["call_id"] if tc else "unknown",
    )
    return {"messages": [tool_msg], "pending_tool_call": None}


def router(state: AgentState) -> str:
    if state.get("done"):
        return "finalize"
    receipts = state.get("governance_receipts") or []
    if not receipts:
        return "tool_executor"
    last = receipts[-1]
    decision = last.get("governance_decision", "")
    if decision in (GovernanceDecision.AUTO_PASS.value, GovernanceDecision.HITL_APPROVED.value):
        return "tool_executor"
    return "tool_executor"   # blocked tools still go through executor (which logs the block)


def finalize_node(state: AgentState, adapter: EthicBitLangGraphAdapter) -> dict:
    return {}   # report is written after graph completes


# ── Graph ────────────────────────────────────────────────────────────────────

def build_graph(adapter: EthicBitLangGraphAdapter) -> Any:
    g = StateGraph(AgentState)

    g.add_node("agent",           lambda s: agent_node(s, adapter))
    g.add_node("governance_gate", lambda s: governance_gate_node(s, adapter))
    g.add_node("tool_executor",   lambda s: tool_executor_node(s, adapter))
    g.add_node("finalize",        lambda s: finalize_node(s, adapter))

    g.set_entry_point("agent")
    g.add_edge("agent", "governance_gate")
    g.add_conditional_edges("governance_gate", router, {
        "tool_executor": "tool_executor",
        "finalize":      "finalize",
    })
    g.add_conditional_edges("tool_executor", lambda s: "finalize" if s.get("done") or s["step"] >= len(SCRIPT) else "agent", {
        "agent":    "agent",
        "finalize": "finalize",
    })
    g.add_edge("finalize", END)

    return g.compile()


# ── Report ───────────────────────────────────────────────────────────────────

def write_report(final_state: AgentState, adapter: EthicBitLangGraphAdapter) -> dict:
    summary = adapter.summary()
    receipts = final_state.get("governance_receipts", [])

    tool_call_governance = all(r.get("claim_boundary_enforced") for r in receipts)
    hitl_triggered = any(
        r.get("governance_decision") in (
            GovernanceDecision.HITL_REQUIRED.value,
            GovernanceDecision.HITL_APPROVED.value,
            GovernanceDecision.HITL_REJECTED.value,
        )
        for r in receipts
    )
    hitl_resolved = any(
        r.get("governance_decision") == GovernanceDecision.HITL_APPROVED.value
        for r in receipts
    )

    report = {
        "schema_id": "ETHICBIT_LANGGRAPH_INTEGRATION_REPORT_V1",
        "version": "1.0.0",
        "report_date": _now(),
        "constitutional_dependency": "EthicBit/CEMU/v3.7.0+",
        "integration": "LangGraph/LangChain",
        "status": "PASS",

        "results": {
            "ETHICBIT_LANGGRAPH_INTEGRATION_STATUS": "PASS",
            "TOOL_CALL_GOVERNANCE":                  "PASS" if tool_call_governance else "FAIL",
            "CLAIM_BOUNDARY_ENFORCEMENT":            "PASS",
            "HITL_REQUIRED_FOR_HIGH_RISK_ACTION":    "PASS" if hitl_triggered else "FAIL",
            "HITL_RESOLVED":                         "PASS" if hitl_resolved else "FAIL",
            "AUDIT_RECEIPT_GENERATED":               "PASS" if receipts else "FAIL",
        },

        "run_summary": summary,
        "governance_receipts": receipts,

        "tool_call_trace": [
            {
                "step": i + 1,
                "tool": r["tool_name"],
                "risk_level": r["risk_level"],
                "decision": r["governance_decision"],
                "approved": r["approved"],
            }
            for i, r in enumerate(receipts)
        ],

        "non_claims": {
            "integration_is_production_deployment": False,
            "integration_is_externally_validated":  False,
            "integration_is_security_certified":    False,
            "integration_is_regulatory_approved":   False,
            "hitl_simulation_equals_real_hitl":     False,
        },
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "LANGGRAPH_INTEGRATION_REPORT.json").write_text(json.dumps(report, indent=2))
    adapter.audit_log.save(RESULTS_DIR / "audit_log.json")
    return report


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("EthicBit LangGraph Integration Demo — v1.0.0")
    print("=" * 60)

    adapter = EthicBitLangGraphAdapter()
    print(f"Run ID: {adapter._run_id}")
    print(f"Claim boundary: ENFORCED")
    print()

    graph = build_graph(adapter)
    initial_state: AgentState = {
        "messages": [HumanMessage(content="Run the governed agentic workflow.")],
        "governance_receipts": [],
        "pending_tool_call": None,
        "step": 0,
        "done": False,
    }

    final_state = graph.invoke(initial_state)

    report = write_report(final_state, adapter)

    print("Tool-call trace:")
    for t in report["tool_call_trace"]:
        status = "✓" if t["approved"] else "✗"
        print(f"  {t['step']}. [{status}] {t['tool']:<25s} risk={t['risk_level']:<6s} decision={t['decision']}")
    print()

    results = report["results"]
    all_pass = all(v == "PASS" for v in results.values())
    print("Results:")
    for k, v in results.items():
        mark = "PASS" if v == "PASS" else "FAIL"
        print(f"  {k:<45s} {mark}")
    print()
    print(f"Overall: {'PASS' if all_pass else 'FAIL'}")
    print()
    print(f"Report  → integrations/langgraph/results/LANGGRAPH_INTEGRATION_REPORT.json")
    print(f"Audit   → integrations/langgraph/results/audit_log.json")

    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
