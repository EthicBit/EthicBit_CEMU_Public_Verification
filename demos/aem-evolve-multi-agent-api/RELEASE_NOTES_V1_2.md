# AEM-EVOLVE™ Multi-Agent Governance API — Release Notes v1.2.0

**Release date:** 2026-05-09
**Git tag:** `v1.2.0`
**Branch:** `main`
**Base:** v1.1.0 governed change assurance release
**Commit SHA:** `202367ee`

---

## What is v1.2.0?

v1.2.0 introduces MECH-REASON™ — a deterministic Mechanical Reasoning Engine that produces policy-bound, evidence-based governance recommendations without LLM involvement.

v1.1.0 established the governed change assurance lifecycle. v1.2.0 closes the last informal gap: the process of evaluating evidence and producing a governance outcome recommendation is now fully deterministic, machine-verifiable, and cryptographically sealed before any human or LLM review occurs.

**v1.2 definition:**

```
v1.1 = regulator-mappable, governance-measurable, multi-anchor-verifiable,
       HITL-hardened, receipt-forgery-tested, official-status-signed

v1.2 = v1.1 + mechanically-reasoning, policy-bound, LLM-free in governance path,
       10/10 verified, SHA-256 sealed
```

**Constitutional rule:**

```
MECH-REASON™ recommends mechanically.
MechanicalGate decides deterministically.
ReceiptSealer seals.
EthicBit audits, hashes, anchors, and preserves the claim boundary.
```

---

## What's new in v1.2.0

### PR #107 — Policy-as-code + claim boundary checker

- `demos/aem-evolve-multi-agent-api/tools/reasoning/policies/AEM_EVOLVE_POLICY_V1_2.json`
- `demos/aem-evolve-multi-agent-api/tools/reasoning/claim_boundary_checker.py`
- `demos/aem-evolve-multi-agent-api/docs/MECH_REASON_POLICY_V1_2.md`
- `assurance/evolve-multi-agent/v1_2/claim_boundary_check_report.json`

`AEM_EVOLVE_POLICY_V1_2.json` is the policy-as-code document containing 17 deterministic rules across 3 families:

| Rule family | Count | Effect |
|---|---|---|
| `R-CLAIM-*` | 10 | Any trigger → `FAIL_CLOSED` |
| `R-HITL-*` | 4 | Score threshold breach → `ESCALATE_TO_HITL` |
| `R-SCOPE-*` | 3 | Partial evidence band → `SCOPE_LIMITED` |

`claim_boundary_checker.py` evaluates all R-CLAIM-* rules against the evidence bundle using deterministic field comparisons (eq, ne, gt, lt, range). Emits `claim_boundary_check_report.json` with per-rule results and `claim_boundary_risk_score`.

### PR #108 — Evidence completeness scorer + governance risk scorer

- `demos/aem-evolve-multi-agent-api/tools/reasoning/evidence_completeness_scorer.py`
- `demos/aem-evolve-multi-agent-api/tools/reasoning/governance_risk_scorer.py`
- `demos/aem-evolve-multi-agent-api/docs/MECH_REASON_SCORING.md`
- `assurance/evolve-multi-agent/v1_2/evidence_completeness_report.json`
- `assurance/evolve-multi-agent/v1_2/governance_risk_score_report.json`

**Evidence completeness scorer** — weights 8 artifact categories on a 0.0–1.0 scale:

| Score | Outcome |
|---|---|
| ≥ 0.80 | Sufficient — `PASS` |
| 0.50 – 0.79 | Partial — `SCOPE_LIMITED` |
| < 0.50 | Insufficient — `FAIL_CLOSED` or `ESCALATE` |

**Governance risk scorer** — 7-dimension composite (lower = safer):

| Dimension | Weight |
|---|---|
| Receipt integrity | 0.25 |
| Anchor integrity | 0.20 |
| Regulatory mapping | 0.15 |
| HITL completeness | 0.15 |
| Claim boundary risk | 0.15 |
| Evidence completeness | 0.10 |

### PR #109 — MECH-REASON™ engine

- `demos/aem-evolve-multi-agent-api/tools/reasoning/mech_reason.py`
- `demos/aem-evolve-multi-agent-api/tools/reasoning/mechanical_explanation.py`
- `demos/aem-evolve-multi-agent-api/docs/MECH_REASON_ENGINE.md`
- `assurance/evolve-multi-agent/v1_2/MECH_REASON_REPORT.json`

Main orchestrator executing the full reasoning sequence:

1. Sub-component execution (claim boundary → evidence completeness → governance risk)
2. Decision table with strict priority: `FAIL_CLOSED > ESCALATE_TO_HITL > SCOPE_LIMITED > PASS`
3. State machine validation — confirms outcome reachability from current score values
4. HITL requirement inference
5. Mechanical explanation generation — deterministic, rule-derived, LLM-free
6. SHA-256 `report_hash` sealing over `recommended_outcome + triggered_rules + scores + input_hashes`

`MECH_REASON_REPORT.json` records `llm_involved: false` and 9 non-claim statements on every run.

### PR #110 — Mechanical reasoning verifier + assurance artifacts

- `demos/aem-evolve-multi-agent-api/tools/reasoning/verify_mech_reason.py`
- `assurance/evolve-multi-agent/v1_2/MECH_REASON_VERIFICATION_REPORT.json`
- `assurance/evolve-multi-agent/v1_2/MECH_REASON_VERIFICATION.md`
- `assurance/evolve-multi-agent/v1_2/V1_2_HASH_RECORD.txt`

`verify_mech_reason.py` applies 10 deterministic checks against a sealed `MECH_REASON_REPORT.json`:

| Check | Verifies |
|---|---|
| C-01-SCHEMA | Required fields, schema_id, `llm_involved=false` |
| C-02-POLICY-VER | `policy_version = 1.2.0` |
| C-03-INPUT-HASHES | Re-hashes all 4 input files, compares to recorded values |
| C-04-REPORT-HASH | Re-derives `report_hash`, compares |
| C-05-SCORES | All 7 scores in `[0.0, 1.0]` |
| C-06-TRIGGERED-RULES | `triggered_rules` is a list of strings |
| C-07-OUTCOME | `recommended_outcome` in `ALLOWED_OUTCOMES` |
| C-08-EXPLANATION | Non-LLM marker present in `mechanical_explanation` |
| C-09-NON-CLAIMS | All 9 required non-claim statements present |
| C-10-DETERMINISM | Two consecutive engine runs produce identical outcomes |

`V1_2_HASH_RECORD.txt` records SHA-256 of all 5 v1.2 assurance artifacts.

### PR #111 — Optional LLM advisory adapter boundary

- `demos/aem-evolve-multi-agent-api/docs/OPTIONAL_LLM_ADVISORY_ADAPTER_BOUNDARY.md`

Constitutional definition of the precise role any LLM may play relative to MECH-REASON™:

**Permitted:** narrative summarization, HITL briefing generation, risk context surfacing — all post-hoc, read-only, tagged `advisory_only: true`.

**Prohibited:** evaluating evidence bundles, setting governance scores, recommending outcomes, triggering rules, sealing receipts, anchoring artifacts, approving HITL events.

> EthicBit does not outsource governance reasoning to an LLM.

The adapter is intentionally not implemented in v1.2.0 — this document defines its boundary for any future implementer.

### PR #112 — Whitepaper v1.2

- `docs/whitepapers/WHITEPAPER_V1_2_AEM_EVOLVE_MECHANICAL_REASONING_LAYER.md`

Full documentation of the Mechanical Reasoning Layer: constitutional rules, 8-component architecture, 10-check verification layer, LLM advisory adapter boundary, claim boundary discipline, integration with v1.1 foundations, and all release artifacts.

---

## Verification results

All scripts verified on `main` at commit `202367ee`:

| Script | Result |
|---|---|
| `mech_reason.py` | `MECH_REASON_STATUS=PASS` |
| `verify_mech_reason.py` | `MECH_REASON_VERIFICATION=PASS (10/10)` |

Run:

```bash
python3 demos/aem-evolve-multi-agent-api/tools/reasoning/mech_reason.py
# MECH_REASON_STATUS=PASS
#   recommended_outcome: PASS
#   hitl_required:       True
#   triggered_rules:     []

python3 demos/aem-evolve-multi-agent-api/tools/reasoning/verify_mech_reason.py
# MECH_REASON_VERIFICATION=PASS
#   ✓ C-01-SCHEMA · ✓ C-02-POLICY-VER · ✓ C-03-INPUT-HASHES · ✓ C-04-REPORT-HASH
#   ✓ C-05-SCORES · ✓ C-06-TRIGGERED-RULES · ✓ C-07-OUTCOME · ✓ C-08-EXPLANATION
#   ✓ C-09-NON-CLAIMS · ✓ C-10-DETERMINISM
```

---

## Known limitations and non-claims

| Item | Status |
|---|---|
| LLM advisory adapter | Boundary defined — not implemented in v1.2.0 |
| HITL identity | Demo-grade — not HSM-backed, not enterprise IAM |
| Signed official status | Demo Ed25519 — not production key custody |
| Independent reproductions | Challenge open — 0 external reports received |
| Regulatory approval | Not claimed — reasoning engine only |
| Legal compliance | Not claimed |
| External certification | Not certified |
| Production readiness | Controlled-environment scope only |

---

## API surface changes

None. v1.2.0 is additive. No breaking changes to:

- endpoints (`/events`, `/gate`, `/approve`, `/chain/verify`, `/metrics`, `/healthz`)
- RBAC roles (INITIATOR / APPROVER / OBSERVER)
- receipt schema
- audit chain
- SQLite storage

All new components are standalone Python scripts in `tools/reasoning/` with no dependencies on the API runtime.

---

## Upgrade notes from v1.1.0

No migration required. Pull `main` at tag `v1.2.0` and run the new scripts.

```bash
git pull origin main
git checkout v1.2.0
python3 demos/aem-evolve-multi-agent-api/tools/reasoning/mech_reason.py
# MECH_REASON_STATUS=PASS
python3 demos/aem-evolve-multi-agent-api/tools/reasoning/verify_mech_reason.py
# MECH_REASON_VERIFICATION=PASS
```

---

## Core claim

> AEM-EVOLVE™ v1.2 introduces MECH-REASON™, a deterministic reasoning engine for policy-bound, evidence-based governance recommendations.

## Non-claims (transversal v1.2)

```
LLM output is not final governance.
LLM output is not official status.
LLM output is not regulatory approval.
LLM output is not legal compliance.
LLM output is not certification.
LLM output is not receipt sealing.
This recommendation is not regulatory approval.
This recommendation is not legal compliance.
This recommendation is not external certification.
```
