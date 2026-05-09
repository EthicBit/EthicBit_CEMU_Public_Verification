# Governance Effectiveness Metrics — AEM-EVOLVE™ v1.1

**Type:** Controlled-demonstration governance metrics
**Version:** v1.1.0
**Scope:** Controlled-environment release only

---

## Purpose

AEM-EVOLVE™ v1.1 publishes governance-effectiveness metrics for controlled demonstration scenarios.

These metrics measure whether governance preserved boundaries, detected unauthorized attempts, and applied correct outcomes — not only whether the system ran.

## Metrics

| Metric | Description |
|---|---|
| `pass_count` | Executions that passed governance gate |
| `scope_limited_count` | Executions limited by scope boundary |
| `fail_closed_count` | Executions that triggered fail-closed policy |
| `scope_limited_rate` | Fraction of executions scope-limited |
| `fail_closed_rate` | Fraction of executions fail-closed |
| `unauthorized_action_prevention_rate` | Rate at which unauthorized actions were blocked |
| `receipt_boundary_preservation_rate` | Rate at which receipts preserved claim boundaries |
| `tamper_detection_rate` | Rate at which tamper attempts were detected |
| `hitl_required_rate` | Fraction of executions requiring HITL approval |
| `hitl_approval_rate` | Fraction of HITL-required events that received approval |
| `claim_boundary_violation_block_rate` | Rate at which claim language violations were blocked |

## How to run

```bash
python3 demos/aem-evolve-multi-agent-api/tools/metrics/governance_effectiveness_metrics.py
```

Expected output:

```
GOVERNANCE_EFFECTIVENESS_METRICS_STATUS=PASS
```

Report generated at: `assurance/evolve-multi-agent/v1_1/governance_effectiveness_report.json`

## Supported claim

> AEM-EVOLVE™ v1.1 publishes governance-effectiveness metrics for controlled demonstration scenarios.

## Boundary

These metrics are controlled-demonstration metrics, not production guarantees, regulatory proof, or external certification.
