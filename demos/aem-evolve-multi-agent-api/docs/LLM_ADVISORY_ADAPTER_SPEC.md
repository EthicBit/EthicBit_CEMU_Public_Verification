# LLM Advisory Adapter — Specification
# AEM-EVOLVE™ v1.3

**Status:** Implemented
**Constitutional basis:** `docs/OPTIONAL_LLM_ADVISORY_ADAPTER_BOUNDARY.md`
**LLM model:** `claude-sonnet-4-6`

---

## What it does

Reads the sealed `MECH_REASON_REPORT.json` (already sealed by MECH-REASON™) and
calls the Claude API to generate a plain-language advisory narrative for human reviewers.

Writes output to `assurance/evolve-multi-agent/v1_3/LLM_ADVISORY_LOG.json` with:

```json
{
  "advisory_only": true,
  "governance_binding": false,
  "source_report_hash": "<sealed hash — unchanged>",
  "recommended_outcome_at_read_time": "<PASS | SCOPE_LIMITED | FAIL_CLOSED | ESCALATE_TO_HITL>"
}
```

## What it does NOT do

- Does NOT modify `recommended_outcome`
- Does NOT write to any assurance artifact
- Does NOT contribute to `report_hash`
- Does NOT satisfy HITL approval requirements
- Does NOT anchor, seal, or sign anything

## Simulation mode

If `ANTHROPIC_API_KEY` is not set or `anthropic` package is not installed,
the adapter runs in simulation mode and logs a placeholder narrative.
`LLM_ADVISORY_STATUS=PASS` in both cases — the adapter's job is to route
the sealed report to the LLM boundary correctly, not to validate LLM output.

## How to run

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 demos/aem-evolve-multi-agent-api/tools/advisory/llm_advisory_adapter.py
# LLM_ADVISORY_STATUS=PASS
```

## Non-claims

```
LLM advisory output is not governance.
LLM advisory output does not override MECH-REASON™ recommended_outcome.
LLM advisory output is not regulatory approval.
LLM advisory output is not legal compliance.
LLM advisory output does not satisfy HITL approval requirements.
```
