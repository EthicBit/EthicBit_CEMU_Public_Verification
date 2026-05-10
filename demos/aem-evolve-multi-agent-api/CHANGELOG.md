# Changelog

All notable changes to AEM-EVOLVE Multi-Agent Governance API.

Format: [version] — date — description.  
Non-claims are additive; no prior non-claim is retracted without explicit record.

---

## [1.9.0] — 2026-05-10

### Added
- `RELEASE_NOTES_V1_9.md`
- `tools/hitl/oidc_token_generator.py` — `OidcTestKeyPair.load_or_generate(path)`: deterministic kid from public key DER; persists to `oidc_key.pem`
- `main.py` — `_OIDC_KEY_FILE_NAME = "oidc_key.pem"`; `_init_oidc_provider()` uses `load_or_generate` instead of ephemeral `OidcTestKeyPair()`
- `main.py` — `StartRequest.materiality_score: float = 78.0` (0.0–100.0); `writer_agent` reads from state; all 3 governance paths reachable
- `main.py` — version bumped to `0.7.0-demo`; `/health` adds `oidc_key_persistence`, `materiality_parametrized`, `governance_paths`
- `tests/test_oidc_key_persistence.py` — 10 tests: file exists, RSA 2048, deterministic kid, cross-reload verify
- `tests/test_materiality_paths.py` — 11 tests: FAIL_CLOSED / SCOPE_LIMITED / PASS paths, receipt outcomes, validation errors
- `tests/test_postgres_live.py` — 9 tests (skipped if AEM_DB_URL not set)
- `tools/signing/verify_oidc_key_persistence.py` — 10 checks: `OIDC_KEY_PERSISTENCE_VERIFICATION=PASS (10/10)`
- `tools/governance/verify_materiality_paths.py` — 10 checks: `MATERIALITY_PATHS_VERIFICATION=PASS (10/10)`
- `tools/db/verify_postgres_live.py` — 10 checks: `POSTGRES_LIVE_VERIFICATION=PASS` (SKIP if no AEM_DB_URL)
- `tools/reproduction/verify_all_v1_9.py` — 27-check full-stack verifier
- `assurance/evolve-multi-agent/v1_9/` — all assurance reports

### Non-claims (v1.9.0)
```
OIDC key file is not HSM-backed key custody.
Key stored unencrypted on disk — not enterprise key management.
PostgreSQL live test skipped when AEM_DB_URL not set.
Materiality score is caller-supplied — not externally audited.
HITL enforcement uses HMAC shared secret — not enterprise IAM.
SQLiteAdapter is demo storage — not production audit storage.
External independent reproductions remain at 0 received.
This release is not regulatory approval.
This release is not external certification.
v1.9 closes the v1.x hardening sequence — v2.0 gate is required for production-readiness evidence.
```

---

## [1.8.0] — 2026-05-09

### Added
- `RELEASE_NOTES_V1_8.md`
- `main.py` — `_oidc_key_pair` + `_OIDC_POLICY`: module-level OIDC state; `_init_oidc_provider()` at startup
- `main.py` — `_verify_hitl_token_oidc()`: RS256 JWT verification (sig, sub, event_id, registry, replay)
- `main.py` — `_verify_hitl_token()`: dual-path dispatch via `token.count(".") == 2`
- `main.py` — `_build_db_adapter()`: `AEM_DB_ADAPTER` env var factory; SQLite/Postgres with fallback
- `main.py` — `GET /oidc/jwks`: ephemeral RSA-2048 public key as JWKS (RS256)
- `main.py` — version bumped to `0.6.0-demo`; `/health` adds `hitl_oidc_path`, `db_adapter`, `db_adapter_switch`; `/healthz` `db` field reflects adapter
- `tests/test_signing_controls.py` — `TestKeyPersistence` (8 tests), `TestDbAdapterLabel` (2 tests)
- `tests/test_oidc_hitl.py` — `TestOIDCProviderInit` (4 tests), `TestOIDCApproval` (6 tests)
- `tools/hitl/verify_oidc_wired.py` — 10-check OIDC wired verifier
- `tools/db/verify_db_adapter_switch.py` — 10-check DB adapter switch verifier
- `tools/reproduction/verify_all_v1_8.py` — 24-check full-stack verifier
- `assurance/evolve-multi-agent/v1_8/oidc_wired_report.json`
- `assurance/evolve-multi-agent/v1_8/db_adapter_switch_report.json`
- `assurance/evolve-multi-agent/v1_8/REPRODUCTION_REPORT.json`
- `docs/whitepapers/WHITEPAPER_V1_8_AEM_EVOLVE_PRODUCTION_HARDENING.md`
- `docs/STATUS_BULLETIN_PUBLIC_2026-05-09_V1_8.md`
- Git tag `v1.8.0` + GitHub Release

### Non-claims (v1.8.0)
```
OIDC key pair is locally generated — not a real IdP.
JWKS is served in-process — not a real OIDC provider endpoint.
Production requires external OIDC provider (Okta, Auth0, Keycloak).
PostgreSQL path not tested with a live database in this verifier.
Connection pool sizing is demo-grade.
File-based signing key is not HSM-backed key custody.
HITL enforcement uses HMAC shared secret — not enterprise IAM.
SQLiteAdapter is demo storage — not production audit storage.
External independent reproductions remain at 0 received.
This release is not regulatory approval.
This release is not external certification.
```

---

## [1.7.0] — 2026-05-10

### Added
- `RELEASE_NOTES_V1_7.md`
- `main.py` — `_init_signing_provider()`: file-based key persistence (`signing_key.pem`); survives restarts (gap 2)
- `main.py` — `_verify_artifact_signature()`: read-time Ed25519 signature verification on GET /receipt, /event, /audit (gap 1)
- `main.py` — `hitl_used_tokens` table + `_is_token_used()` + `_mark_token_used()`: one-time-use HITL tokens, 409 on replay (gap 3)
- `main.py` — version bumped to `0.5.0-demo`; `/health` reflects all three new controls
- `tools/signing/verify_read_time_signatures.py` — 10-check read-time verification verifier
- `tools/hitl/verify_replay_mitigation.py` — 10-check replay mitigation verifier
- `tools/signing/verify_key_persistence.py` — 10-check key persistence verifier
- `tools/integration/e2e_api_test.py` — extended to 14 checks (C-11 through C-14)
- `tools/reproduction/verify_all_v1_7.py` — 21-check full-stack verifier
- `assurance/evolve-multi-agent/v1_7/read_time_sig_report.json`
- `assurance/evolve-multi-agent/v1_7/replay_mitigation_report.json`
- `assurance/evolve-multi-agent/v1_7/key_persistence_report.json`
- `assurance/evolve-multi-agent/v1_7/REPRODUCTION_REPORT.json`
- `docs/whitepapers/WHITEPAPER_V1_7_AEM_EVOLVE_READ_VERIFY_PERSIST_ANTIREPLAY.md`
- `docs/STATUS_BULLETIN_PUBLIC_2026-05-10_V1_7.md`
- Git tag `v1.7.0` + GitHub Release

### Changed
- `tests/test_endpoints.py` — version assertions updated to `0.5.0-demo`; `test_approve_replay_returns_409` added
- `tests/test_governance_logic.py` — `TestReadTimeSignatureVerification` + `TestReplayMitigation` classes added

### Non-claims (v1.7.0)
```
File-based signing key is not HSM-backed key custody.
Key stored unencrypted on disk — not enterprise key management.
Replay nonce store is SQLite-backed — not tamper-proof.
HITL enforcement uses HMAC shared secret — not enterprise IAM.
SQLiteAdapter is demo storage — not production audit storage.
External independent reproductions remain at 0 received.
This release is not regulatory approval.
This release is not external certification.
```

---

## [1.6.0] — 2026-05-09

### Added
- `RELEASE_NOTES_V1_6.md`
- `main.py` — `_init_signing_provider()`: Ed25519 signing wired into events + receipts (PR #133)
- `main.py` — `ApproveRequest.hitl_token + hitl_approver_id`: HMAC HITL token enforced in /approve (PR #133)
- `main.py` — `SQLiteAdapter` activated: all DB calls routed through DBAdapter interface (PR #133)
- `main.py` — `/health` + `/healthz` report actual `signing_status` (PR #133)
- `tools/__init__.py`, `tools/signing/__init__.py`, `tools/hitl/__init__.py` — package markers (PR #133)
- `tools/integration/e2e_api_test.py` — 10-check end-to-end TestClient test (PR #134)
- `tools/signing/verify_signed_receipts.py` — 10-check signed receipts verifier (PR #134)
- `tools/reproduction/verify_all_v1_6.py` — 18-check full-stack verifier (PR #134)
- `.github/workflows/aem-evolve-reproduction.yml` — updated: v1.5 + v1.6 verifiers + E2E test (PR #134)
- `assurance/evolve-multi-agent/v1_6/signed_receipts_report.json`
- `assurance/evolve-multi-agent/v1_6/e2e_api_report.json`
- `assurance/evolve-multi-agent/v1_6/REPRODUCTION_REPORT.json`
- `docs/whitepapers/WHITEPAPER_V1_6_AEM_EVOLVE_CRITICAL_GAPS_CLOSURE.md` (PR #138)
- `docs/STATUS_BULLETIN_PUBLIC_2026-05-09_V1_6.md`
- Git tag `v1.6.0` + GitHub Release

### Changed
- `tests/test_endpoints.py` — approve tests now generate valid HITL tokens
- `tests/test_governance_logic.py` — fixture uses SQLiteAdapter; new signature assertions
- API version bumped to `0.4.0-demo`

### Non-claims (v1.6 additions)
- Ephemeral signing key is not persisted across server restarts.
- HITL enforcement uses HMAC shared secret — not enterprise IAM.
- SQLiteAdapter is demo storage — not production audit storage.

---

## [1.5.0] — 2026-05-09

### Added
- `RELEASE_NOTES_V1_5.md`
- `docs/roadmap/AEM_EVOLVE_V1_5_PR_ROADMAP.md` (PR #126)
- `tools/signing/pkcs11_signing_provider.py` — PKCS#11 signing stub (PR #127)
- `tools/signing/kms_signing_provider.py` — AWS KMS signing stub (PR #127)
- `tools/signing/verify_hsm_signing_providers.py` — 10-check HSM verifier (PR #127)
- `tools/hitl/HITL_OIDC_POLICY.json` — OIDC provider config (PR #128)
- `tools/hitl/oidc_token_generator.py` — ephemeral RSA-2048 JWT generator (PR #128)
- `tools/hitl/oidc_hitl_identity_verifier.py` — 10-check RS256 JWT verifier (PR #128)
- `tools/runtime/dependency_validator.py` — REQUIRED/OPTIONAL tiering (PR #129)
- `tools/runtime/server_smoke_test.py` — in-process FastAPI health check (PR #129)
- `tools/db/async_postgres_concurrency_test.py` — N=20 concurrent mock test (PR #130)
- `docs/PGBOUNCER_INTEGRATION_GUIDE.md` — transaction-pooling config (PR #130)
- `challenge/independent-reproduction/AEM_V1_4_INDEPENDENT_REPRODUCTION_CHALLENGE.md` (PR #131)
- `tools/reproduction/verify_all_v1_5.py` — 16-check full-stack verifier (PR #131)
- `docs/whitepapers/WHITEPAPER_V1_5_AEM_EVOLVE_ENTERPRISE_HARDENING.md` (PR #132)
- `docs/STATUS_BULLETIN_PUBLIC_2026-05-09_V1_5.md`
- Git tag `v1.5.0` + GitHub Release

### Changed
- `README.md` — promoted v1.5.0 as latest release
- `FINAL_AUDIT_CONCLUSION.md` — updated with v1.5.0 release record

### No breaking changes

### Verification
```
FULL_STACK_VERIFICATION=PASS  (16/16)
  v1.1: 6/6  ·  v1.2: 2/2  ·  v1.3: 4/4  ·  v1.4: 2/2  ·  v1.5: 2/2
```

---

## [1.4.0] — 2026-05-09

### Added
- `RELEASE_NOTES_V1_4.md` — v1.4 release notes
- `docs/roadmap/AEM_EVOLVE_V1_4_PR_ROADMAP.md` — v1.4 production hardening roadmap (PR #119)
- `tools/signing/signing_provider.py` — `SigningProvider` ABC (PR #120)
- `tools/signing/env_signing_provider.py` — Ed25519 env-var provider (PR #120)
- `tools/signing/file_signing_provider.py` — Ed25519 file provider (PR #120)
- `tools/signing/verify_signing_provider.py` — 8-check round-trip verifier (PR #120)
- `tools/hitl/HITL_IDENTITY_POLICY.json` — HMAC token TTL + approver registry (PR #121)
- `tools/hitl/hitl_identity_verifier.py` — 10-check HMAC-SHA256 token verifier (PR #121)
- `tools/hitl/hitl_token_generator.py` — CI token generator (PR #121)
- `tools/crypto/mlkem768_setup_check.py` — 9-check library installation validator (PR #122)
- `tools/db/validate_async_postgres_adapter.py` — 10-check async adapter contract validator (PR #123)
- `tools/db/postgres_mock_integration_test.py` — 6-check async mock integration test (PR #123)
- `migrations/004_indexes.sql` — production performance indexes (PR #123)
- `.github/workflows/aem-evolve-reproduction.yml` — CI reproduction workflow (PR #124)
- `Dockerfile.reproduction` — Python 3.11-slim reproduction container (PR #124)
- `tools/reproduction/verify_all_v1_4.py` — 14-check full-stack verifier (PR #124)
- `docs/whitepapers/WHITEPAPER_V1_4_AEM_EVOLVE_PRODUCTION_HARDENING.md` (PR #125)
- `docs/STATUS_BULLETIN_PUBLIC_2026-05-09_V1_4.md`
- Git tag `v1.4.0` + GitHub Release

### Changed
- `tools/crypto/mlkem768_wrapper.py` — corrected `mlkem` library API (key_gen/encaps/decaps)
- `db_adapter.py` — adds `AsyncPostgresAdapter` using `asyncpg`
- `README.md` — promoted v1.4.0 as latest release
- `FINAL_AUDIT_CONCLUSION.md` — updated with v1.4.0 release record

### No breaking changes
API surface, RBAC, receipt schema, audit chain, and storage layer are unchanged.

### Verification
```
FULL_STACK_VERIFICATION=PASS  (14/14)
  v1.1: 6/6  ·  v1.2: 2/2  ·  v1.3: 4/4  ·  v1.4: 2/2
```

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
