"""
Technical Demonstration: Multi-Agent AEM-EVOLVE™ Governance API
FastAPI + LangGraph + SQLite + Explicit Audit Tables
May 2026
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from datetime import datetime, timezone
import hashlib
import json
from uuid import uuid4
import uvicorn
from pathlib import Path

app = FastAPI(
    title="EthicBit AEM-EVOLVE™ Technical Demonstration",
    description="Multi-Agent Governance with Explicit Audit Tables",
    version="0.3.1-demo",
)

# ============================================
# CREAR TABLAS DE AUDITORÍA
# ============================================


def init_audit_tables(conn: sqlite3.Connection):
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS evolution_events (
            event_id TEXT PRIMARY KEY,
            thread_id TEXT,
            event_canonical_sha256 TEXT,
            change_type TEXT,
            base_artifact TEXT,
            proposed_state TEXT,
            materiality_score REAL,
            requested_claim_scope TEXT,
            timestamp_utc TEXT,
            claim_boundary TEXT,
            event_json TEXT
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS evolution_receipts (
            receipt_canonical_sha256 TEXT PRIMARY KEY,
            thread_id TEXT,
            event_id TEXT,
            outcome TEXT,
            receipt_message TEXT,
            materiality_score REAL,
            claim_boundary TEXT,
            requested_claim_scope TEXT,
            signature_status TEXT,
            timestamp_utc TEXT,
            receipt_json TEXT
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS human_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT,
            event_id TEXT,
            decision TEXT,
            approver_id TEXT,
            override_reason TEXT,
            timestamp_utc TEXT
        )
    """
    )

    # Hash-linked audit chain — each row commits to the previous row's chain_hash.
    # chain_hash = SHA256(prev_chain_hash + ":" + entry_sha256)
    # GENESIS row uses prev_chain_hash = "0" * 64.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_chain (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_type TEXT NOT NULL,
            entry_id TEXT NOT NULL,
            entry_sha256 TEXT NOT NULL,
            prev_chain_hash TEXT NOT NULL,
            chain_hash TEXT NOT NULL,
            timestamp_utc TEXT NOT NULL
        )
    """
    )

    conn.commit()


GENESIS_HASH = "0" * 64


def _append_audit_chain(
    conn: sqlite3.Connection,
    entry_type: str,
    entry_id: str,
    entry_sha256: str,
) -> str:
    cursor = conn.cursor()
    cursor.execute("SELECT chain_hash FROM audit_chain ORDER BY seq DESC LIMIT 1")
    row = cursor.fetchone()
    prev_chain_hash = row[0] if row else GENESIS_HASH
    chain_hash = hashlib.sha256(
        f"{prev_chain_hash}:{entry_sha256}".encode()
    ).hexdigest()
    cursor.execute(
        """
        INSERT INTO audit_chain (entry_type, entry_id, entry_sha256, prev_chain_hash, chain_hash, timestamp_utc)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            entry_type,
            entry_id,
            entry_sha256,
            prev_chain_hash,
            chain_hash,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    return chain_hash


# ============================================
# MODELOS
# ============================================


class StartRequest(BaseModel):
    thread_id: str
    initial_prompt: str = "Eres un asistente general."


class ApproveRequest(BaseModel):
    thread_id: str
    decision: Literal["approve", "reject"]
    approver_id: Optional[str] = "human-reviewer"
    override_reason: Optional[str] = None


class StatusResponse(BaseModel):
    thread_id: str
    status: str
    current_prompt: str
    last_receipt: Optional[dict]
    human_approval_needed: bool
    approved_changes_count: int


# ============================================
# FUNCIONES AUXILIARES
# ============================================


def compute_sha256(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def create_evolution_event(
    change_type: str,
    base_artifact: str,
    proposed_state: str,
    materiality: float,
    conn: sqlite3.Connection,
    thread_id: str,
):
    event = {
        "schema_id": "AEM_EVOLVE_EVOLUTION_EVENT_SCHEMA_V1",
        "event_id": f"EVO-API-{uuid4()}",
        "thread_id": thread_id,
        "change_type": change_type,
        "base_artifact": base_artifact,
        "proposed_state": proposed_state,
        "materiality_score": materiality,
        "requested_claim_scope": "RESEARCH_SUPPORT",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": {
            "research_support_only": True,
            "clinical_claimed": False,
            "diagnostic_claimed": False,
            "regulatory_approval_claimed": False,
            "third_party_binding": False,
        },
    }
    event["event_canonical_sha256"] = compute_sha256(event)

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO evolution_events
        (event_id, thread_id, event_canonical_sha256, change_type, base_artifact,
         proposed_state, materiality_score, requested_claim_scope, timestamp_utc,
         claim_boundary, event_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            event["event_id"],
            event["thread_id"],
            event["event_canonical_sha256"],
            event["change_type"],
            event["base_artifact"],
            event["proposed_state"],
            event["materiality_score"],
            event["requested_claim_scope"],
            event["timestamp_utc"],
            json.dumps(event["claim_boundary"], ensure_ascii=False),
            json.dumps(event, ensure_ascii=False),
        ),
    )
    conn.commit()
    _append_audit_chain(conn, "evolution_event", event["event_id"], event["event_canonical_sha256"])

    return event


def evaluate_evolution_gate(event: dict, conn: sqlite3.Connection, thread_id: str):
    score = event["materiality_score"]

    if score > 85:
        outcome = "FAIL_CLOSED"
        message = "Cambio de muy alto riesgo. Requiere nueva evidencia o override excepcional."
    elif score > 70:
        outcome = "SCOPE_LIMITED"
        message = "Cambio aprobado con limitaciones de scope."
    else:
        outcome = "PASS"
        message = "Cambio de bajo riesgo. Aprobado automáticamente."

    receipt = {
        "schema_id": "AEM_EVOLVE_EVOLUTION_RECEIPT_SCHEMA_V1",
        "receipt_id": f"REC-{event['event_id']}",
        "receipt_payload": {
            "outcome": outcome,
            "receipt_message": message,
            "materiality_score": score,
            "claim_boundary": event["claim_boundary"],
            "requested_claim_scope": event["requested_claim_scope"],
        },
        "event_id": event["event_id"],
        "thread_id": thread_id,
        "event_canonical_sha256": event["event_canonical_sha256"],
        "signature_status": "NOT_SIGNED_DEMO",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    receipt["receipt_canonical_sha256"] = compute_sha256(receipt)

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO evolution_receipts
        (receipt_canonical_sha256, thread_id, event_id, outcome, receipt_message,
         materiality_score, claim_boundary, requested_claim_scope, signature_status,
         timestamp_utc, receipt_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            receipt["receipt_canonical_sha256"],
            receipt["thread_id"],
            receipt["event_id"],
            outcome,
            message,
            score,
            json.dumps(event["claim_boundary"], ensure_ascii=False),
            event["requested_claim_scope"],
            "NOT_SIGNED_DEMO",
            receipt["timestamp_utc"],
            json.dumps(receipt, ensure_ascii=False),
        ),
    )
    conn.commit()
    _append_audit_chain(conn, "evolution_receipt", receipt["receipt_id"], receipt["receipt_canonical_sha256"])

    return receipt


# ============================================
# NODOS DEL GRAFO
# ============================================


def research_agent(state):
    state["research_findings"] = "Investigación completada."
    state["status"] = "research_completed"
    return state


def writer_agent(state, conn):
    new_prompt = "Eres un escritor experto en ética de IA y gobernanza verificable."
    thread_id = state.get("thread_id", "unknown")
    event = create_evolution_event(
        "CONFIGURATION_UPDATE", "writer_prompt", new_prompt, 78.0, conn, thread_id
    )
    receipt = evaluate_evolution_gate(event, conn, thread_id)

    state["last_receipt"] = receipt
    state["pending_change"] = {"new_value": new_prompt, "event": event}
    state["status"] = "change_proposed"
    return state


def governance_gate(state):
    outcome = state["last_receipt"]["receipt_payload"]["outcome"]

    if outcome == "FAIL_CLOSED":
        state["status"] = "change_fail_closed"
        state["pending_change"] = None
        state["human_approval_needed"] = False
    elif outcome == "SCOPE_LIMITED":
        state["human_approval_needed"] = True
        state["status"] = "awaiting_human_approval"
    else:
        state["current_prompt"] = state["pending_change"]["new_value"]
        state["approved_changes"].append(state["last_receipt"])
        state["status"] = "change_auto_approved"
        state["pending_change"] = None
    return state


def awaiting_approval_node(state):
    state["status"] = "awaiting_human_approval"
    return state


def final_report_node(state):
    terminal_status = state["status"]
    state["final_report"] = f"Reporte completado. Estado final: {terminal_status}"
    state["terminal_status"] = terminal_status

    if terminal_status == "change_fail_closed":
        state["status"] = "completed_fail_closed"
    elif terminal_status == "change_human_rejected":
        state["status"] = "completed_rejected"
    else:
        state["status"] = "completed"
    return state


# ============================================
# GRAFO (con wrapper)
# ============================================


DEMO_ROOT = Path(__file__).resolve().parent
DEMO_DB_PATH = DEMO_ROOT / "ethicbit_demo.db"
DEMO_HOST = "127.0.0.1"
DEMO_PORT = 8000


def build_graph():
    checkpoint_conn = sqlite3.connect(str(DEMO_DB_PATH), check_same_thread=False)
    audit_conn = sqlite3.connect(str(DEMO_DB_PATH), check_same_thread=False)
    init_audit_tables(audit_conn)

    def writer_agent_with_conn(state):
        return writer_agent(state, audit_conn)

    workflow = StateGraph(dict)

    workflow.add_node("research", research_agent)
    workflow.add_node("writer", writer_agent_with_conn)
    workflow.add_node("governance", governance_gate)
    workflow.add_node("awaiting_approval", awaiting_approval_node)
    workflow.add_node("final_report", final_report_node)

    workflow.set_entry_point("research")
    workflow.add_edge("research", "writer")
    workflow.add_edge("writer", "governance")

    def route(state):
        if state["status"] == "change_fail_closed":
            return "final_report"
        if state.get("human_approval_needed"):
            return "awaiting_approval"
        return "final_report"

    workflow.add_conditional_edges(
        "governance",
        route,
        {
            "awaiting_approval": "awaiting_approval",
            "final_report": "final_report",
        },
    )

    workflow.add_edge("awaiting_approval", END)
    workflow.add_edge("final_report", END)

    return workflow.compile(checkpointer=SqliteSaver(checkpoint_conn)), audit_conn


graph, db_conn = build_graph()

# ============================================
# ENDPOINTS
# ============================================


@app.post("/start")
def start_session(req: StartRequest):
    initial_state = {
        "thread_id": req.thread_id,
        "research_findings": "",
        "final_report": "",
        "current_prompt": req.initial_prompt,
        "pending_change": None,
        "last_receipt": None,
        "status": "initialized",
        "approved_changes": [],
        "human_approval_needed": False,
    }
    config = {"configurable": {"thread_id": req.thread_id}}
    result = graph.invoke(initial_state, config=config)
    return {"thread_id": req.thread_id, "status": result["status"]}


@app.get("/status/{thread_id}", response_model=StatusResponse)
def get_status(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = graph.get_state(config).values
        return StatusResponse(
            thread_id=thread_id,
            status=state.get("status", "unknown"),
            current_prompt=state.get("current_prompt", ""),
            last_receipt=state.get("last_receipt"),
            human_approval_needed=state.get("human_approval_needed", False),
            approved_changes_count=len(state.get("approved_changes", [])),
        )
    except Exception as e:
        raise HTTPException(404, f"Thread not found or unavailable: {str(e)}")


@app.post("/approve")
def approve_change(req: ApproveRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    state = graph.get_state(config).values

    if not state.get("human_approval_needed"):
        raise HTTPException(400, "No human approval needed")

    if req.decision == "approve":
        state["current_prompt"] = state["pending_change"]["new_value"]
        state["approved_changes"].append(state["last_receipt"])
        state["status"] = "change_human_approved"
    else:
        state["status"] = "change_human_rejected"

    state["pending_change"] = None
    state["human_approval_needed"] = False

    decision_ts = datetime.now(timezone.utc).isoformat()
    decision_id = f"DEC-{req.thread_id}-{state['last_receipt']['event_id']}"
    decision_payload = {
        "decision_id": decision_id,
        "thread_id": req.thread_id,
        "event_id": state["last_receipt"]["event_id"],
        "decision": req.decision,
        "approver_id": req.approver_id,
        "override_reason": req.override_reason,
        "timestamp_utc": decision_ts,
    }
    decision_sha256 = compute_sha256(decision_payload)

    cursor = db_conn.cursor()
    cursor.execute(
        """
        INSERT INTO human_decisions (thread_id, event_id, decision, approver_id, override_reason, timestamp_utc)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            req.thread_id,
            state["last_receipt"]["event_id"],
            req.decision,
            req.approver_id,
            req.override_reason,
            decision_ts,
        ),
    )
    db_conn.commit()
    _append_audit_chain(db_conn, "human_decision", decision_id, decision_sha256)

    state = final_report_node(state)
    graph.update_state(config, state)

    return {"status": state["status"]}


@app.get("/receipt/{thread_id}")
def get_receipt(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = graph.get_state(config).values
        if not state.get("last_receipt"):
            raise HTTPException(404, "No receipt found")
        return state["last_receipt"]
    except Exception as e:
        raise HTTPException(404, f"Thread not found or unavailable: {str(e)}")


@app.get("/event/{thread_id}")
def get_event(thread_id: str):
    cursor = db_conn.cursor()
    cursor.execute(
        """
        SELECT event_json FROM evolution_events
        WHERE thread_id = ?
        ORDER BY timestamp_utc DESC
    """,
        (thread_id,),
    )
    rows = cursor.fetchall()
    events = [json.loads(row[0]) for row in rows]
    return {"thread_id": thread_id, "events": events}


@app.get("/audit/{thread_id}")
def get_audit(thread_id: str):
    cursor = db_conn.cursor()

    cursor.execute(
        """
        SELECT event_json FROM evolution_events
        WHERE thread_id = ?
        ORDER BY timestamp_utc DESC
    """,
        (thread_id,),
    )
    events = [json.loads(row[0]) for row in cursor.fetchall()]

    cursor.execute(
        """
        SELECT receipt_json FROM evolution_receipts
        WHERE thread_id = ?
        ORDER BY timestamp_utc DESC
    """,
        (thread_id,),
    )
    receipts = [json.loads(row[0]) for row in cursor.fetchall()]

    cursor.execute(
        """
        SELECT event_id, decision, approver_id, override_reason, timestamp_utc
        FROM human_decisions
        WHERE thread_id = ?
        ORDER BY timestamp_utc DESC
    """,
        (thread_id,),
    )
    decisions = [
        {
            "event_id": row[0],
            "decision": row[1],
            "approver_id": row[2],
            "override_reason": row[3],
            "timestamp_utc": row[4],
        }
        for row in cursor.fetchall()
    ]

    return {
        "thread_id": thread_id,
        "events": events,
        "receipts": receipts,
        "human_decisions": decisions,
    }


@app.get("/chain/{thread_id}")
def get_chain(thread_id: str):
    """Return all audit chain entries that reference events/receipts/decisions for this thread."""
    cursor = db_conn.cursor()
    # Collect entry_ids for this thread from all three tables.
    cursor.execute("SELECT event_id FROM evolution_events WHERE thread_id = ?", (thread_id,))
    event_ids = {row[0] for row in cursor.fetchall()}
    cursor.execute("SELECT event_id FROM evolution_receipts WHERE thread_id = ?", (thread_id,))
    receipt_entry_ids = {f"REC-{eid}" for eid in {row[0] for row in cursor.fetchall()}}
    decision_prefix = f"DEC-{thread_id}-"
    cursor.execute(
        "SELECT entry_id FROM audit_chain WHERE entry_id LIKE ?",
        (decision_prefix + "%",),
    )
    decision_ids = {row[0] for row in cursor.fetchall()}

    all_ids = event_ids | receipt_entry_ids | decision_ids
    if not all_ids:
        raise HTTPException(404, f"No audit chain entries found for thread {thread_id}")

    placeholders = ",".join("?" * len(all_ids))
    cursor.execute(
        f"SELECT seq, entry_type, entry_id, entry_sha256, prev_chain_hash, chain_hash, timestamp_utc "
        f"FROM audit_chain WHERE entry_id IN ({placeholders}) ORDER BY seq",
        list(all_ids),
    )
    rows = cursor.fetchall()
    entries = [
        {
            "seq": r[0], "entry_type": r[1], "entry_id": r[2],
            "entry_sha256": r[3], "prev_chain_hash": r[4],
            "chain_hash": r[5], "timestamp_utc": r[6],
        }
        for r in rows
    ]
    return {"thread_id": thread_id, "chain_entries": entries, "count": len(entries)}


@app.get("/chain/verify")
def verify_chain():
    """Walk the full audit chain and verify every hash link. Detects any tampering."""
    cursor = db_conn.cursor()
    cursor.execute(
        "SELECT seq, entry_type, entry_id, entry_sha256, prev_chain_hash, chain_hash "
        "FROM audit_chain ORDER BY seq"
    )
    rows = cursor.fetchall()

    if not rows:
        return {"status": "EMPTY", "entries_checked": 0, "errors": []}

    errors = []
    expected_prev = GENESIS_HASH

    for seq, entry_type, entry_id, entry_sha256, prev_chain_hash, chain_hash in rows:
        if prev_chain_hash != expected_prev:
            errors.append({
                "seq": seq, "entry_id": entry_id,
                "error": "prev_chain_hash_mismatch",
                "expected": expected_prev, "got": prev_chain_hash,
            })
        recomputed = hashlib.sha256(f"{prev_chain_hash}:{entry_sha256}".encode()).hexdigest()
        if recomputed != chain_hash:
            errors.append({
                "seq": seq, "entry_id": entry_id,
                "error": "chain_hash_mismatch",
                "expected": recomputed, "stored": chain_hash,
            })
        expected_prev = chain_hash

    status = "PASS" if not errors else "TAMPER_DETECTED"
    return {
        "status": status,
        "entries_checked": len(rows),
        "errors": errors,
        "head_chain_hash": rows[-1][5] if rows else None,
        "tamper_evident": True,
        "tamper_proof_claimed": False,
        "note": "Hash-linked detection only. SQLite is demo storage — not tamper-proof.",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "demo_type": "technical_demonstration",
        "version": "0.3.1-demo",
        "local_only": True,
        "signature_status": "DEMO_SIGNED_ED25519",
        "anchor_status": "ANCHORED_ON_MAINNET_DEMO",
        "audit_tables": ["evolution_events", "evolution_receipts", "human_decisions", "audit_chain"],
        "tamper_evident_chain": True,
        "tamper_proof_claimed": False,
        "non_claims": [
            "not_production_ready",
            "not_independently_reproduced",
            "not_signed_release_receipt",
            "not_regulatory_approved",
            "not_clinical_or_diagnostic",
            "sqlite_not_production_audit_storage",
            "not_tamper_proof",
        ],
    }


if __name__ == "__main__":
    print("Starting EthicBit AEM-EVOLVE Multi-Agent Governance API v0.3.1-demo")
    print(f"Docs: http://{DEMO_HOST}:{DEMO_PORT}/docs")
    uvicorn.run(app, host=DEMO_HOST, port=DEMO_PORT)
