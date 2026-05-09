#!/usr/bin/env python3
"""LLM Advisory Adapter — AEM-EVOLVE™ v1.3.

Reads the sealed MECH_REASON_REPORT.json (read-only, post-hoc) and calls
the Claude API to generate an advisory narrative for human reviewers.

Constitutional constraints (from OPTIONAL_LLM_ADVISORY_ADAPTER_BOUNDARY.md):
  - LLM receives only sealed outputs — never raw evidence
  - LLM writes to advisory namespace only (advisory_only: true)
  - LLM output is NOT a report_hash input
  - LLM output CANNOT modify recommended_outcome
  - LLM interaction is logged separately (governance_binding: false)

EthicBit does not outsource governance reasoning to an LLM.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT   = Path(__file__).resolve().parents[4]
V1_2        = REPO_ROOT / "assurance/evolve-multi-agent/v1_2"
V1_3        = REPO_ROOT / "assurance/evolve-multi-agent/v1_3"
REPORT_PATH = V1_2 / "MECH_REASON_REPORT.json"
LOG_OUT     = V1_3 / "LLM_ADVISORY_LOG.json"

ADVISORY_NON_CLAIMS = [
    "LLM advisory output is not governance.",
    "LLM advisory output does not override MECH-REASON™ recommended_outcome.",
    "LLM advisory output is not a receipt.",
    "LLM advisory output is not regulatory approval.",
    "LLM advisory output is not legal compliance.",
    "LLM advisory output does not satisfy HITL approval requirements.",
    "LLM advisory output is not an anchor event.",
    "LLM advisory output is tagged advisory_only: true.",
]


def _load_sealed_report() -> dict:
    with open(REPORT_PATH) as f:
        return json.load(f)


def _build_prompt(report: dict) -> str:
    outcome    = report.get("recommended_outcome", "UNKNOWN")
    hitl       = report.get("hitl_required", False)
    triggered  = report.get("triggered_rules", [])
    scores     = report.get("scores", {})
    explanation = report.get("mechanical_explanation", "")

    return f"""You are providing an advisory narrative for a human reviewer (HITL) about a governance decision.

IMPORTANT: You are reading a sealed governance report. You do NOT make governance decisions.
Your output is advisory only. It does not modify any governance outcome.

Sealed MECH-REASON™ report summary:
- recommended_outcome: {outcome}
- hitl_required: {hitl}
- triggered_rules: {triggered if triggered else "none"}
- evidence_completeness_score: {scores.get("evidence_completeness_score", "N/A")}
- governance_risk_score: {scores.get("governance_risk_score", "N/A")}
- mechanical_explanation: {explanation}

Provide a concise advisory narrative (3-5 sentences) for the human reviewer that:
1. States the recommended outcome and what it means for the reviewer
2. Summarizes the key scores in plain language
3. If hitl_required is true, explains what the reviewer needs to decide
4. Ends with a clear statement that this is advisory only and the final decision rests with the human reviewer

Do not invent data. Do not override the recommended_outcome. Do not add non-claims or legal language."""


def _call_claude(prompt: str) -> str:
    try:
        import anthropic  # type: ignore[import]
    except ImportError:
        return (
            "[SIMULATION MODE — anthropic package not installed] "
            "Advisory narrative would be generated here by Claude API. "
            "Install with: pip install anthropic"
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return (
            "[SIMULATION MODE — ANTHROPIC_API_KEY not set] "
            "Advisory narrative would be generated here by Claude API."
        )

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def main() -> int:
    print("[LLM ADVISORY ADAPTER] Reading sealed MECH_REASON_REPORT...")

    if not REPORT_PATH.exists():
        print(f"ERROR: MECH_REASON_REPORT.json not found at {REPORT_PATH}", file=sys.stderr)
        return 1

    report        = _load_sealed_report()
    sealed_hash   = report.get("report_hash", "")
    recommended   = report.get("recommended_outcome", "UNKNOWN")

    print(f"  sealed report_hash: {sealed_hash[:16]}…")
    print(f"  recommended_outcome (sealed, read-only): {recommended}")
    print("[LLM ADVISORY ADAPTER] Generating advisory narrative (does not modify governance)...")

    prompt    = _build_prompt(report)
    narrative = _call_claude(prompt)

    simulation = narrative.startswith("[SIMULATION MODE")

    advisory_hash = hashlib.sha256(narrative.encode()).hexdigest()

    log_entry = {
        "schema_id":          "AEM_EVOLVE_LLM_ADVISORY_LOG_V1_3",
        "generated_at":       datetime.now(timezone.utc).isoformat(),
        "source_report_hash": sealed_hash,
        "recommended_outcome_at_read_time": recommended,
        "advisory_only":      True,
        "governance_binding": False,
        "llm_model":          "claude-sonnet-4-6",
        "simulation_mode":    simulation,
        "advisory_narrative": narrative,
        "advisory_hash":      advisory_hash,
        "non_claims":         ADVISORY_NON_CLAIMS,
    }

    V1_3.mkdir(parents=True, exist_ok=True)
    with open(LOG_OUT, "w") as f:
        json.dump(log_entry, f, indent=2)

    print(f"  advisory_only: true")
    print(f"  governance_binding: false")
    print(f"  simulation_mode: {simulation}")
    print(f"  advisory_hash: {advisory_hash[:16]}…")
    print("LLM_ADVISORY_STATUS=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
