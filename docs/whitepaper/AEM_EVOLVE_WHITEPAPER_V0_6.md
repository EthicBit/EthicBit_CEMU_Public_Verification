# AEM-EVOLVE™ — Whitepaper v0.6

**Verifiable Multi-Agent Governance — Quality, Documentation & Polish**

**Version:** 0.6 (Phase 4 — Quality, Documentation & Polish)  
**Base system version:** v0.3.1-demo  
**Date:** May 2026

---

## Changes from v0.5

| Addition | Detail |
|---|---|
| Automated test suite | `tests/` — 75 tests, 88% coverage on `main.py` + `metrics.py` |
| `pytest.ini` | Test configuration; `pythonpath = .`, `testpaths = tests` |
| CI/CD workflow | `.github/workflows/aem-evolve-ci.yml` — test + assurance integrity check on push/PR |
| `docs/API_REFERENCE.md` | Full endpoint reference with auth, request/response schemas, outcome logic |
| `docs/ARCHITECTURE.md` | Component overview, data flow diagrams, security design |
| `docs/CLAIMS_AND_NON_CLAIMS.md` | Canonical versioned claims/non-claims record with evidence map |
| ADR-001 | SQLite for demo storage — rationale and migration path |
| ADR-002 | LangGraph state machine — rationale and migration path |
| ADR-003 | RBAC API key scheme — rationale and migration path |
| Python SDK | `sdk/aem_evolve_client.py` — `AEMEvolveClient` covering all endpoints |
| Route fix | `GET /chain/verify` moved before `GET /chain/{thread_id}` — prevents FastAPI shadow routing |

---

## Test Coverage (Phase 4)

| Module | Statements | Covered | Coverage |
|---|---|---|---|
| `main.py` | 363 | 318 | **88%** |
| `metrics.py` | 40 | 36 | **90%** |
| **Total** | **403** | **354** | **88%** |

Test categories:

- **RBAC** — missing key, unknown key, wrong role, valid keys
- **Governance logic** — SHA-256 determinism, PASS/SCOPE_LIMITED/FAIL_CLOSED boundaries, receipt persistence, audit chain hash linking
- **MetricsRegistry** — timer accumulation, increment, snapshot statistics, outcome distribution, reset
- **Endpoint integration** — `/health`, `/healthz`, `/start`, `/approve`, `/status`, `/receipt`, `/audit`, `/chain`, `/chain/verify`, `/metrics`

---

## CI/CD

GitHub Actions workflow (`.github/workflows/aem-evolve-ci.yml`) runs on push/PR to `main` and phase branches:

1. **`test` job** — installs dependencies, runs `pytest --cov --cov-fail-under=65`, verifies server starts and `/healthz` returns `status: ok`
2. **`assurance-check` job** — walks `AEM_EVOLVE_MULTI_AGENT_API_HASH_RECORD.txt` and recomputes SHA-256 for every listed file; fails if any file is missing or hash-mismatched

---

## Documentation Coverage

| Document | Purpose |
|---|---|
| `docs/API_REFERENCE.md` | Every endpoint: auth, request, response, error codes |
| `docs/ARCHITECTURE.md` | System design, data flows, component map, non-claims |
| `docs/CLAIMS_AND_NON_CLAIMS.md` | Canonical versioned claims and evidence map |
| `docs/adr/ADR-001` | Why SQLite (and when to migrate) |
| `docs/adr/ADR-002` | Why LangGraph (and migration path) |
| `docs/adr/ADR-003` | Why static API keys (and migration path) |
| `QUICKSTART_30_MIN.md` | 30-minute reproduction guide |
| `docs/REPRODUCTION_GUIDE.md` | Extended reproduction guide |
| `docs/ADVERSARIAL_RESILIENCE_REPORT.md` | Phase 2 adversarial test results |
| `docs/BENCHMARK_REPORT_V1.md` | Phase 3 benchmark results |

---

## Python SDK

`sdk/aem_evolve_client.py` — `AEMEvolveClient` class covering all API endpoints:

```python
from sdk.aem_evolve_client import AEMEvolveClient

# Initiator starts a session
initiator = AEMEvolveClient("http://127.0.0.1:8000", api_key="demo-initiator-key-001")
result = initiator.start("session-001", "Initial prompt")
# → {"thread_id": "session-001", "status": "awaiting_human_approval"}

# Approver reviews and approves
approver = AEMEvolveClient("http://127.0.0.1:8000", api_key="demo-approver-key-001")
decision = approver.approve("session-001", "approve", override_reason="Scope reviewed")
# → {"status": "completed"}

# Observer reads audit trail
observer = AEMEvolveClient("http://127.0.0.1:8000", api_key="demo-observer-key-001")
audit = observer.audit("session-001")
chain_status = observer.verify_chain()
# → {"status": "PASS", "entries_checked": 2, ...}
```

Non-claims on the SDK: no retry logic, no timeout hardening, no async support in this initial version.

---

## Non-Claims (v0.6)

All prior non-claims preserved, plus:

- Test suite does not cover `db_adapter.py` (`PostgresAdapter` not tested — skeleton only)
- CI runs SQLite only; no PostgreSQL integration tests
- SDK has no retry, circuit-breaker, or authentication refresh logic
- 88% coverage leaves uncovered: env-var key store path, error branches in `/status` / `/receipt`, `__main__` block

---

## Allowed Claim (v0.6)

> AEM-EVOLVE™ provides an automated test suite with 88% coverage on core modules, CI verification via GitHub Actions, complete developer documentation (`API_REFERENCE.md`, `ARCHITECTURE.md`, `CLAIMS_AND_NON_CLAIMS.md`, ADRs), and an initial Python SDK for controlled-environment multi-agent governance workflows.

---

## Roadmap Position

| Phase | Version | Status |
|---|---|---|
| 0 | v0.3.1-demo | Complete |
| 1 | v0.3.5 | Complete |
| 2 | v0.4 | Complete |
| 3 | v0.5 | Complete |
| **4** | **v0.6** | **Current** |
| 5 | v1.0.0 | Target 2026-Q3 |
