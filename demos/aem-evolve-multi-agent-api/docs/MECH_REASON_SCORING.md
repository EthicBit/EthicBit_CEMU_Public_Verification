# MECH-REASON™ Scoring — AEM-EVOLVE™ v1.2

**Type:** Deterministic evidence and governance scoring
**Version:** v1.2.0

---

## Scores produced

| Score | Range | Script |
|---|---|---|
| `evidence_completeness_score` | 0.0 – 1.0 | `evidence_completeness_scorer.py` |
| `governance_risk_score` | 0.0 – 1.0 (lower = safer) | `governance_risk_scorer.py` |
| `claim_boundary_risk_score` | 0.0 – 1.0 | `governance_risk_scorer.py` |
| `hitl_necessity_score` | 0.0 – 1.0 | `governance_risk_scorer.py` |
| `anchor_integrity_score` | 0.0 – 1.0 | `governance_risk_scorer.py` |
| `receipt_integrity_score` | 0.0 – 1.0 | `governance_risk_scorer.py` |
| `regulatory_mapping_presence_score` | 0.0 – 1.0 | `governance_risk_scorer.py` |

## Thresholds

| Score | PASS | SCOPE_LIMITED | FAIL_CLOSED |
|---|---|---|---|
| `evidence_completeness_score` | ≥ 0.80 | 0.50 – 0.80 | < 0.50 |
| `governance_risk_score` | ≤ 0.40 | 0.40 – 0.70 | > 0.70 |

## How to run

```bash
python3 demos/aem-evolve-multi-agent-api/tools/reasoning/evidence_completeness_scorer.py
# EVIDENCE_COMPLETENESS_SCORE=PASS

python3 demos/aem-evolve-multi-agent-api/tools/reasoning/governance_risk_scorer.py
# GOVERNANCE_RISK_SCORE=PASS
```

## Supported claim

> AEM-EVOLVE™ v1.2 adds deterministic evidence-completeness and governance-risk scoring for controlled demonstration scenarios.
