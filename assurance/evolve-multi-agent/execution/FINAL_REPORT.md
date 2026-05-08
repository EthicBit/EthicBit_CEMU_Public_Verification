# AEM-EVOLVE Multi-Agent Governance API — Final Execution Report

**Version:** 0.3.1-demo  
**Exported:** 2026-05-07T22:30:00.000000+00:00  
**Source commit:** `46cf228d`  
**Source DB:** `demos/aem-evolve-multi-agent-api/ethicbit_demo.db`  
**Canonical thread:** `e2e-demo-1778190786`

---

## Execution Summary

| Metric | Value |
|---|---|
| Threads executed | 8 |
| Evolution Events emitted | 8 |
| Evolution Receipts issued | 7 |
| Human (HITL) decisions recorded | 1 |
| Audit chain entries | 10 |
| Outcome distribution | {"SCOPE_LIMITED": 7} |

---

## Threads

| Thread ID | Events | Receipts | Outcome |
|---|---|---|---|
| `auth-check-1778190594` | 1 | 1 | SCOPE_LIMITED |
| `auth-check-1778190658` | 1 | 1 | SCOPE_LIMITED |
| `demo-thread-001` | 1 | 1 | SCOPE_LIMITED |
| `direct-debug` | 1 | 0 | — |
| `direct-debug-2` | 1 | 1 | SCOPE_LIMITED |
| `e2e-demo-1778190731` | 1 | 1 | SCOPE_LIMITED |
| `e2e-demo-1778190786` | 1 | 1 | SCOPE_LIMITED |
| `t-authtest-1778189717` | 1 | 1 | SCOPE_LIMITED |

---

## Human Decisions

| Thread | Event ID | Decision | Approver | Override Reason | Timestamp |
|---|---|---|---|---|---|
| `demo-thread-001` | `EVO-API-906c936c-0a0…` | **approve** | human-reviewer | Approved for research-support scope only. | 2026-05-07T17:46:58.558093+00:00 |

---

## Audit Chain (tail)

| seq | entry_type | entry_id (prefix) | chain_hash (prefix) |
|---|---|---|---|
| 6 | evolution_receipt | `REC-EVO-API-5cbab70e-f1e…` | `3338e193013ec5d4…` |
| 7 | evolution_event | `EVO-API-d135727b-3983-41…` | `c370aee6a8e841d1…` |
| 8 | evolution_receipt | `REC-EVO-API-d135727b-398…` | `62f9298035ebe952…` |
| 9 | evolution_event | `EVO-API-dd9492d5-c75f-41…` | `374018ecd8784c22…` |
| 10 | evolution_receipt | `REC-EVO-API-dd9492d5-c75…` | `ecdb2f3032b8ce43…` |

---

## Non-Claims

- `production_execution: false` — demo environment, SQLite storage only.
- `tamper_proof: false` — tamper-evident (hash-linked chain), not tamper-proof.
- `clinical_or_diagnostic: false`
- `regulatory_approved: false`
- `independently_reproduced: false`

---

## Assurance Artifacts

| Artifact | Path |
|---|---|
| Execution manifest | `assurance/evolve-multi-agent/execution/EXECUTION_MANIFEST.json` |
| Audit export | `assurance/evolve-multi-agent/execution/AUDIT_EXPORT.json` |
| Signature set | `assurance/evolve-multi-agent/execution/EXECUTION_SIGNATURE_SET.json` |
| Hash record | `assurance/evolve-multi-agent/execution/EXECUTION_HASH_RECORD.txt` |