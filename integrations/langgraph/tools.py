"""
EthicBit LangGraph Integration — Tool definitions.

Three tools spanning all risk levels:
  LOW    — search_knowledge_base
  MEDIUM — draft_document
  HIGH   — publish_external (requires HITL)

No external API calls. All tools are deterministic for reproducibility.
"""
from __future__ import annotations

from datetime import datetime, timezone


def search_knowledge_base(query: str) -> dict:
    """LOW-risk: read-only search over an in-memory knowledge base."""
    KB = {
        "ethics":       "Mechanical ethics requires verifiable, auditable decision traces.",
        "langgraph":    "LangGraph is a framework for building stateful multi-agent applications.",
        "claim boundary": "A claim boundary prevents overclaiming evidence posture.",
        "hitl":         "Human-in-the-loop approval is required before high-risk actions.",
        "cemu":         "CEMU is the EthicBit constitutional regime for mechanical ethics assurance.",
    }
    results = {k: v for k, v in KB.items() if query.lower() in k.lower() or query.lower() in v.lower()}
    return {
        "tool": "search_knowledge_base",
        "query": query,
        "hits": len(results),
        "results": results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def draft_document(content: str, doc_type: str) -> dict:
    """MEDIUM-risk: compose a document in memory (no external publish)."""
    allowed_types = {"memo", "report", "summary", "analysis"}
    if doc_type.lower() not in allowed_types:
        return {
            "tool": "draft_document",
            "status": "REJECTED",
            "reason": f"doc_type '{doc_type}' not in allowed set {allowed_types}",
        }
    word_count = len(content.split())
    return {
        "tool": "draft_document",
        "status": "DRAFTED",
        "doc_type": doc_type,
        "word_count": word_count,
        "preview": content[:120] + ("..." if len(content) > 120 else ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def publish_external(content: str, destination: str) -> dict:
    """HIGH-risk: simulate external publish (HITL must approve before execution)."""
    return {
        "tool": "publish_external",
        "status": "PUBLISHED_SIMULATED",
        "destination": destination,
        "content_length": len(content),
        "note": "Simulated publish — no real external call made in demo.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


TOOL_REGISTRY: dict[str, callable] = {
    "search_knowledge_base": search_knowledge_base,
    "draft_document":        draft_document,
    "publish_external":      publish_external,
}
