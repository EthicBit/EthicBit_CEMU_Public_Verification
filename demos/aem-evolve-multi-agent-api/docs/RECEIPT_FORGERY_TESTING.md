# Receipt Forgery Testing — AEM-EVOLVE™ v1.1

**Type:** Adversarial receipt-forgery test battery
**Version:** v1.1.0

---

## Purpose

AEM-EVOLVE™ v1.1 introduces a receipt-forgery test battery to verify that evolution receipts resist standard adversarial mutations.

## Test battery (8 scenarios)

| # | Test | What it attempts |
|---|---|---|
| 1 | `modify_outcome` | Change SCOPE_LIMITED → PASS |
| 2 | `modify_materiality_score` | Inflate materiality score |
| 3 | `remove_non_claims` | Strip all non-claims from receipt |
| 4 | `change_scope_boundary` | Replace declared scope with universal_production |
| 5 | `change_hitl_requirement` | Flip hitl_required flag |
| 6 | `replay_old_receipt` | Inject stale hash into modified receipt |
| 7 | `inject_production_ready_claim` | Add production_ready_claimed=true |
| 8 | `replace_receipt_hash` | Zero-out the receipt hash |

Each test must result in `tamper_detected=true`.

## How to run

```bash
python3 demos/aem-evolve-multi-agent-api/adversarial_tests/test_receipt_forgery.py
```

Expected output:

```
RECEIPT_FORGERY_TESTS=PASS
```

Report generated at: `assurance/evolve-multi-agent/v1_1/receipt_forgery_test_report.json`

## Boundary

These are controlled forgery-detection tests against a canonical hash mechanism. They do not prove tamper-proof operation in production, HSM-backed protection, or cybersecurity certification.

## Supported claim

> AEM-EVOLVE™ v1.1 adds receipt-forgery testing for controlled governance evidence.
