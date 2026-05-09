# Changelog

All notable changes to AEM-EVOLVE Multi-Agent Governance API.

Format: [version] — date — description.  
Non-claims are additive; no prior non-claim is retracted without explicit record.

---

## [1.3.0] — 2026-05-09

### Added
- `RELEASE_NOTES_V1_3.md` — v1.3 release notes
- `docs/roadmap/AEM_EVOLVE_V1_3_PR_ROADMAP.md` — v1.3 gap closure roadmap (PR #113)
- `tools/advisory/llm_advisory_adapter.py` — LLM advisory adapter, advisory_only=true (PR #114)
- `tools/crypto/mlkem768_wrapper.py` + `verify_mlkem768.py` — ML-KEM768 KEM runtime (PR #115)
- `tools/hitl/HITL_QUORUM_POLICY.json` + `hitl_quorum_verifier.py` — HITL N-of-M quorum model (PR #116)
- `tools/db/validate_postgres_adapter.py` + `migrations/003_langraph_checkpointer.sql` (PR #117)
- `tools/reproduction/verify_all_v1_3.py` — 12-check full-stack verifier (PR #118)
- `challenge/independent-reproduction/AEM_V1_3_INDEPENDENT_REPRODUCTION_CHALLENGE.md`
- `docs/whitepapers/WHITEPAPER_V1_3_AEM_EVOLVE_GAPS_CLOSURE.md`
- `docs/STATUS_BULLETIN_PUBLIC_2026-05-09_V1_3.md`
- Git tag `v1.3.0` + GitHub Release

### Changed
- `db_adapter.py` — PostgresAdapter upgraded: `ThreadedConnectionPool`, `ping()`, `close_pool()`
- `README.md` — promoted v1.3.0 as latest release
- `FINAL_AUDIT_CONCLUSION.md` — updated with v1.3.0 release record

### No breaking changes
API surface, RBAC, receipt schema, audit chain, and storage layer are unchanged.

### Verification
```
FULL_STACK_VERIFICATION=PASS  (12/12)
  v1.1: 6/6  ·  v1.2: 2/2  ·  v1.3: 4/4
```

---

## [1.2.0] — 2026-05-09

### Added
- `RELEASE_NOTES_V1_2.md` — v1.2 release notes
- `tools/reasoning/policies/AEM_EVOLVE_POLICY_V1_2.json` — 17-rule policy-as-code (R-CLAIM-*, R-HITL-*, R-SCOPE-*) (PR #107)
- `tools/reasoning/claim_boundary_checker.py` — deterministic R-CLAIM-* evaluator (PR #107)
- `tools/reasoning/evidence_completeness_scorer.py` — 8-artifact weighted scorer (PR #108)
- `tools/reasoning/governance_risk_scorer.py` — 7-dimension composite risk scorer (PR #108)
- `tools/reasoning/mech_reason.py` — MECH-REASON™ engine: decision table, state machine, HITL inference, explanation, SHA-256 sealing (PR #109)
- `tools/reasoning/mechanical_explanation.py` — deterministic LLM-free explanation generator (PR #109)
- `tools/reasoning/verify_mech_reason.py` — 10-check deterministic verifier (PR #110)
- `docs/MECH_REASON_ENGINE.md`, `docs/MECH_REASON_POLICY_V1_2.md`, `docs/MECH_REASON_SCORING.md` (PRs #107–#109)
- `docs/OPTIONAL_LLM_ADVISORY_ADAPTER_BOUNDARY.md` — constitutional LLM boundary definition (PR #111)
- `docs/whitepapers/WHITEPAPER_V1_2_AEM_EVOLVE_MECHANICAL_REASONING_LAYER.md` (PR #112)
- `assurance/evolve-multi-agent/v1_2/` — MECH_REASON_REPORT.json, MECH_REASON_VERIFICATION_REPORT.json, MECH_REASON_VERIFICATION.md, V1_2_HASH_RECORD.txt, claim_boundary_check_report.json, evidence_completeness_report.json, governance_risk_score_report.json
- `docs/STATUS_BULLETIN_PUBLIC_2026-05-09_V1_2.md`
- Git tag `v1.2.0` + GitHub Release

### Changed
- `README.md` — promoted v1.2.0 as latest release, v1.1.0 as previous release
- `FINAL_AUDIT_CONCLUSION.md` — updated with v1.2.0 release record

### No breaking changes
API surface, RBAC, receipt schema, audit chain, and storage layer are unchanged.

### Verification
```
MECH_REASON_STATUS=PASS
  recommended_outcome: PASS
  hitl_required:       true
  triggered_rules:     []
MECH_REASON_VERIFICATION=PASS  (10/10 checks)
llm_involved: false
```

---

## [1.1.0] — 2026-05-09

### Added
- `RELEASE_NOTES_V1_1.md` — v1.1 release notes
- `docs/history/ETHICBIT_CEERV_CEMU_V10_1_MASTER_REPO_TREE.md` — historical v10.1 baseline (PR #99)
- `docs/architecture/AEM_AEM_EVOLVE_ALIGNMENT_WITH_ETHICBIT_CEERV_CEMU_V10_1.md` — alignment mapping (PR #100)
- `tools/regulatory/regulatory_mapping_checker.py` + 3 framework JSONs + check report (PR #101)
- `tools/metrics/governance_effectiveness_metrics.py` + report (PR #102)
- `tools/anchors/multi_anchor_verifier.py` + report (PR #103)
- `tools/hitl/HITL_signature_verifier.py` + report (PR #104)
- `adversarial_tests/test_receipt_forgery.py` + report — 8-scenario forgery battery (PR #104)
- `tools/status/official_status_signer.py` + `OFFICIAL_STATUS_SIGNED.json` + `V1_1_HASH_RECORD.txt` (PR #105)
- `docs/LINGO_AND_CLAIM_DICTIONARY.md` — canonical claim-language controls (PR #105)
- `docs/whitepapers/WHITEPAPER_V1_1_AEM_EVOLVE_GOVERNED_CHANGE_ASSURANCE.md` (PR #106)
- `docs/STATUS_BULLETIN_PUBLIC_2026-05-09.md`
- Git tag `v1.1.0` + GitHub Release

### Changed
- `README.md` — added latest release section for v1.1.0
- `FINAL_AUDIT_CONCLUSION.md` — updated with v1.1.0 release record

### No breaking changes
API surface, RBAC, receipt schema, audit chain, and storage layer are unchanged.

### Verification
```
REGULATORY_MAPPING_CHECK=PASS
GOVERNANCE_EFFECTIVENESS_METRICS_STATUS=PASS
MULTI_ANCHOR_VERIFICATION=PASS
HITL_SIGNATURE_VERIFICATION=PASS_DEMO
RECEIPT_FORGERY_TESTS=PASS
OFFICIAL_STATUS_SIGNED=PASS
```

---

## [1.0.0] — 2026-05-08

### Added
- `RELEASE_NOTES_V1_0.md` — v1.0 release notes
- `CHANGELOG.md` — this file
- Whitepaper v1.0 (`docs/whitepaper/AEM_EVOLVE_WHITEPAPER_V1_0.md`)
- Git tag `v1.0.0` + GitHub Release

### Feature freeze
No new features. All Phase 0–4 deliverables locked.

---

## [0.6 / Phase 4] — 2026-05-08

### Added
- `tests/` — 75-test pytest suite (88% coverage on `main.py` + `metrics.py`)
  - `test_auth.py` — RBAC: missing/unknown/wrong-role/valid key coverage
  - `test_governance_logic.py` — SHA-256, gate outcomes, audit chain linking
  - `test_metrics.py` — MetricsRegistry timer, counter, snapshot, reset
  - `test_endpoints.py` — all endpoints via TestClient
- `pytest.ini` — test configuration
- `.github/workflows/aem-evolve-ci.yml` — CI: test job + assurance hash check
- `docs/API_REFERENCE.md` — full endpoint reference
- `docs/ARCHITECTURE.md` — component map, data flows, security design
- `docs/CLAIMS_AND_NON_CLAIMS.md` — canonical versioned claims + evidence map
- `docs/adr/ADR-001-sqlite-demo-storage.md`
- `docs/adr/ADR-002-langgraph-state-machine.md`
- `docs/adr/ADR-003-rbac-api-keys.md`
- `sdk/aem_evolve_client.py` — `AEMEvolveClient` Python SDK

### Fixed
- `GET /chain/verify` was shadowed by `GET /chain/{thread_id}` (FastAPI route ordering); moved `verify` before parameterized route

### Assurance
- Manifest milestone → Phase 4; 10 `phase4_*` flags added
- Re-signed (SHA `00d314b1`)
- Hash record → 50 files

---

## [0.5 / Phase 3] — 2026-05-08

### Added
- `metrics.py` — `MetricsRegistry` singleton (per-operation timer context manager, counters, snapshot with p95)
- `GET /metrics` endpoint (any authenticated role)
- `GET /healthz` endpoint (no auth required; DB liveness probe)
- `db_adapter.py` — `PostgresAdapter` skeleton (documented migration target; not active)
- `migrations/001_initial_schema.sql` — PostgreSQL 14+ schema
- `migrations/002_metrics_table.sql` — optional persistent metrics table
- `scripts/run_benchmark.sh` — reproducible N-iteration benchmark
- `docs/BENCHMARK_REPORT_V1.md` — real measured values (e2e median 4.077 ms, P95 31.49 ms)
- `docs/METRICS_SCHEMA.json` — formal `/metrics` field definitions
- Whitepaper v0.5

### Changed
- `main.py` — `end_to_end` timer wraps `graph.invoke()`; counter increments in `create_evolution_event` and `evaluate_evolution_gate`; `duration_ms` per request in HTTP log entries

### Fixed
- `_JsonFormatter` class reference in `dictConfig` changed from string `"__main__._JsonFormatter"` to direct class reference — resolves `ValueError` when server started from non-standard directory

### Assurance
- Manifest milestone → Phase 3; `phase3_*` flags added
- Re-signed (SHA `b1bf95d8`)
- Hash record → 35 files

---

## [0.4 / Phase 2] — 2026-05-07

### Added
- `adversarial_tests/` — 27-vector test suite:
  - `test_prompt_injection.sh` (8 vectors)
  - `test_unauthorized_approval.sh` (7 vectors)
  - `test_malformed_payloads.sh` (7 vectors)
  - `test_tampering_detection.py` (5 vectors)
  - `run_all_adversarial_tests.sh`
- `docs/THREAT_MODEL.md` — attack surface, threat actors, mitigations
- `docs/ADVERSARIAL_RESILIENCE_REPORT.md` — all 27 vectors pass
- Whitepaper v0.4

### Assurance
- Manifest milestone → Phase 2; `phase2_*` flags added
- Re-signed
- Hash record updated

---

## [0.3.5 / Phase 1] — 2026-05-07

### Added
- `QUICKSTART_30_MIN.md` — 30-minute guided reproduction
- `docs/reproduction/REPRODUCTION_GUIDE.md` — extended guide
- `docs/reproduction/REPRODUCTION_REPORT_TEMPLATE.md` — external report template
- `independent-reproductions/README.md` — submission process; threshold tracker (0/3 min, 0/5 v1.0)
- Whitepaper v0.3
- `docs/roadmap/AEM_EVOLVE_V1_0_ROADMAP.md`
- `docs/ASSURANCE_LADDER_CONDITIONS.md` — PR 8/9/10 gate conditions

### Assurance
- Manifest milestone → Phase 1
- Hash record updated

---

## [0.3.1-demo / Phase 0] — 2026-05-07

### Added (initial release)
- FastAPI governance API with LangGraph `StateGraph`
- Evolution Events (`evolution_events` table) with canonical SHA-256
- Evolution Receipts (`evolution_receipts` table) with canonical SHA-256
- Governance gate: PASS (≤70) / SCOPE_LIMITED (70–85) / FAIL_CLOSED (>85)
- Human-in-the-Loop approval (`POST /approve`, APPROVER role)
- Hash-linked audit chain (`audit_chain` table); `GET /chain/verify`
- RBAC: INITIATOR / APPROVER / OBSERVER via `X-API-Key`
- Structured JSON logging (`_JsonFormatter`, `dictConfig`)
- `DBAdapter` ABC + `SQLiteAdapter`
- `configs/auth_demo_keys.json` — demo keys
- Ethereum mainnet anchor (TX `0x30fc9e6c…`, block 25045091)
- Execution export package (11 signed artifacts)
- `docs/ASSURANCE_LADDER.md`, `docs/PRODUCTION_READINESS_PLAN.md`
- `docs/EVOLUTION_RECEIPTS_SPECIFICATION.md`, `docs/SCOPE_BOUNDARY.md`
- `scripts/run_demo_e2e.sh`, `scripts/run_tamper_checklist.sh`
