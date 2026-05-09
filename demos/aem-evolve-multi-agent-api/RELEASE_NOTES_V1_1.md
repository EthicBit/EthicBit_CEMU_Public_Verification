# AEM-EVOLVE™ Multi-Agent Governance API — Release Notes v1.1.0

**Release date:** 2026-05-09
**Git tag:** `v1.1.0`
**Branch:** `main`
**Base:** v1.0.0 public controlled-environment release

---

## What is v1.1.0?

v1.1.0 is the first governed-change assurance update to AEM-EVOLVE™.

It does not change the core API surface. It extends v1.0.0 with a documented assurance layer: regulatory mapping evidence, governance-effectiveness metrics, multi-anchor verification, HITL signature verification, receipt-forgery testing, signed official status, and canonical claim-language controls.

**v1.1 definition:**

```
v1.0 = public controlled-environment release
v1.1 = regulator-mappable, governance-measurable, multi-anchor-verifiable,
       HITL-hardened, receipt-forgery-tested, official-status-signed
```

---

## What's new in v1.1.0

### PR #99 — Historical baseline

- `docs/history/ETHICBIT_CEERV_CEMU_V10_1_MASTER_REPO_TREE.md`

Preserves the historical EthicBit / CEERV / CEMU v10.1 declared-scope assurance architecture as the baseline that preceded AEM-EVOLVE™. Factual cutoff: 2026-04-04.

### PR #100 — Architectural alignment

- `docs/architecture/AEM_AEM_EVOLVE_ALIGNMENT_WITH_ETHICBIT_CEERV_CEMU_V10_1.md`

Formal layer-by-layer alignment mapping from EthicBit doctrine → CEERV evidence → CEMU capsule → AEM artifact assurance → AEM-EVOLVE™ governed change assurance.

### PR #101 — Regulatory mapping evidence

- `demos/aem-evolve-multi-agent-api/tools/regulatory/regulatory_mapping_checker.py`
- `demos/aem-evolve-multi-agent-api/docs/regulatory/EU_AI_ACT_MAPPING.json`
- `demos/aem-evolve-multi-agent-api/docs/regulatory/NIST_AI_RMF_MAPPING.json`
- `demos/aem-evolve-multi-agent-api/docs/regulatory/ISO_42001_MAPPING.json`
- `assurance/evolve-multi-agent/v1_1/regulatory_mapping_check_report.json`
- `demos/aem-evolve-multi-agent-api/docs/regulatory/REGULATORY_MAPPING_README.md`

Technical mapping of AEM-EVOLVE™ capabilities to EU AI Act (2024/1689), NIST AI RMF 1.0, and ISO/IEC 42001:2023. Each mapping declares `approval_claimed=false`, `certification_claimed=false`, `legal_compliance_claimed=false`, `conformity_assessment_claimed=false`.

### PR #102 — Governance-effectiveness metrics

- `demos/aem-evolve-multi-agent-api/tools/metrics/governance_effectiveness_metrics.py`
- `assurance/evolve-multi-agent/v1_1/governance_effectiveness_report.json`
- `demos/aem-evolve-multi-agent-api/docs/GOVERNANCE_EFFECTIVENESS_METRICS.md`

Metrics measuring governance boundary preservation and outcome correctness in controlled demonstration scenarios — not runtime performance alone.

New metrics: `scope_limited_rate`, `fail_closed_rate`, `unauthorized_action_prevention_rate`, `receipt_boundary_preservation_rate`, `tamper_detection_rate`, `hitl_required_rate`, `hitl_approval_rate`, `claim_boundary_violation_block_rate`.

### PR #103 — Multi-anchor verification

- `demos/aem-evolve-multi-agent-api/tools/anchors/multi_anchor_verifier.py`
- `assurance/evolve-multi-agent/v1_1/multi_anchor_verification_report.json`
- `demos/aem-evolve-multi-agent-api/docs/MULTI_ANCHOR_VERIFICATION.md`

Unified verification report across Ethereum mainnet anchor and EthicBit triple public anchor, with manifest SHA-256 consistency check.

### PR #104 — HITL signature verification + receipt-forgery testing

- `demos/aem-evolve-multi-agent-api/tools/hitl/HITL_signature_verifier.py`
- `demos/aem-evolve-multi-agent-api/adversarial_tests/test_receipt_forgery.py`
- `assurance/evolve-multi-agent/v1_1/hitl_signature_verification_report.json`
- `assurance/evolve-multi-agent/v1_1/receipt_forgery_test_report.json`
- `demos/aem-evolve-multi-agent-api/docs/HITL_SIGNATURE_VERIFICATION.md`
- `demos/aem-evolve-multi-agent-api/docs/RECEIPT_FORGERY_TESTING.md`

Demo HITL signature verifier checks HUMAN_DECISIONS.json for structure, role, and canonical SHA-256 per decision.

Receipt-forgery test battery (8 adversarial scenarios): `modify_outcome`, `modify_materiality_score`, `remove_non_claims`, `change_scope_boundary`, `change_hitl_requirement`, `replay_old_receipt`, `inject_production_ready_claim`, `replace_receipt_hash`. All 8 detected at 100% tamper detection rate.

### PR #105 — Signed official status + lingo dictionary

- `demos/aem-evolve-multi-agent-api/tools/status/official_status_signer.py`
- `assurance/evolve-multi-agent/v1_1/OFFICIAL_STATUS_SIGNED.json`
- `assurance/evolve-multi-agent/v1_1/V1_1_HASH_RECORD.txt`
- `docs/LINGO_AND_CLAIM_DICTIONARY.md`

Demo Ed25519 signed official status artifact sealing all v1.1 input hashes. Canonical lingo dictionary governing allowed, restricted, and forbidden claim language across all v1.1 artifacts and documentation.

### PR #106 — Whitepaper v1.1

- `docs/whitepapers/WHITEPAPER_V1_1_AEM_EVOLVE_GOVERNED_CHANGE_ASSURANCE.md`

Full whitepaper documenting the v1.1 assurance update: historical baseline, alignment mapping, all six assurance capabilities, evidence package, verification commands, claims, non-claims, remaining gaps, and post-v1.1 roadmap.

---

## Verification results

All scripts verified on `main` at commit `0e5562a165eac38eb225ca5af8614d2316dfdd74`:

| Script | Result |
|---|---|
| `regulatory_mapping_checker.py` | `REGULATORY_MAPPING_CHECK=PASS` |
| `governance_effectiveness_metrics.py` | `GOVERNANCE_EFFECTIVENESS_METRICS_STATUS=PASS` |
| `multi_anchor_verifier.py` | `MULTI_ANCHOR_VERIFICATION=PASS` |
| `HITL_signature_verifier.py` | `HITL_SIGNATURE_VERIFICATION=PASS_DEMO` |
| `test_receipt_forgery.py` | `RECEIPT_FORGERY_TESTS=PASS` |
| `official_status_signer.py` | `OFFICIAL_STATUS_SIGNED=PASS` |

Run all at once:

```bash
python3 demos/aem-evolve-multi-agent-api/tools/regulatory/regulatory_mapping_checker.py
python3 demos/aem-evolve-multi-agent-api/tools/metrics/governance_effectiveness_metrics.py
python3 demos/aem-evolve-multi-agent-api/tools/anchors/multi_anchor_verifier.py
python3 demos/aem-evolve-multi-agent-api/tools/hitl/HITL_signature_verifier.py
python3 demos/aem-evolve-multi-agent-api/adversarial_tests/test_receipt_forgery.py
python3 demos/aem-evolve-multi-agent-api/tools/status/official_status_signer.py
```

---

## Known limitations and non-claims

| Item | Status |
|---|---|
| HITL identity | Demo-grade — not HSM-backed, not enterprise IAM, not production identity provider |
| Signed official status | Demo Ed25519 — not production key custody, not HSM-backed |
| Independent reproductions | Challenge open — 0 external reports received |
| Regulatory approval | Not claimed — mapping evidence only |
| Tamper-proof | Not claimed — canonical hash detection in controlled tests |
| Production readiness | Controlled-environment scope only |
| External certification | Not certified |
| Legal compliance | Not claimed |
| Conformity assessment | Not conducted |
| Cybersecurity certification | Not conducted |

---

## API surface changes

None. v1.1.0 is additive. No breaking changes to:

- endpoints (`/events`, `/gate`, `/approve`, `/chain/verify`, `/metrics`, `/healthz`)
- RBAC roles (INITIATOR / APPROVER / OBSERVER)
- receipt schema
- audit chain
- SQLite storage

New tools and assurance artifacts are standalone Python scripts with no dependencies on the API runtime.

---

## Upgrade notes from v1.0.0

No migration required. Clone or pull `main` at tag `v1.1.0` and run the new verification scripts.

```bash
git pull origin main
git checkout v1.1.0
python3 demos/aem-evolve-multi-agent-api/tools/regulatory/regulatory_mapping_checker.py
# REGULATORY_MAPPING_CHECK=PASS
```

---

## Core claim

> AEM-EVOLVE™ v1.1 extends the v1.0 public controlled-environment release with regulatory mapping evidence, governance-effectiveness metrics, multi-anchor verification, HITL signature verification, receipt-forgery testing, signed official status evidence, and canonical claim-language controls.

## Non-claims (transversal v1.1)

```
Not regulatory-approved.
Not externally certified.
Not legal compliance.
Not conformity assessed.
Not production-ready universal.
Not independently reproduced unless external reports exist.
Not cybersecurity certified.
Not financial advice.
Not clinical or diagnostic.
Not tamper-proof.
Not HSM-backed unless separately implemented.
```
