# AEM-EVOLVE™ Multi-Agent Governance API — Release Notes v1.0.0

**Release date:** May 2026  
**Git tag:** `v1.0.0`  
**Branch:** `release/aem-evolve-v1.0.0`

---

## What is v1.0.0?

v1.0.0 is the first versioned release of AEM-EVOLVE™ Multi-Agent Governance API. It marks the transition from an anchored controlled demonstration to a measured, adversarially tested, documented system with an automated test suite and CI/CD.

**v1.0 definition:**  
Measured + Adversarially Tested + Documented + Usable in Controlled Environments.

---

## What's included in v1.0.0

### Core API (unchanged from v0.3.1-demo base)
- FastAPI + LangGraph governance pipeline
- Evolution Events, Receipts, and SCOPE_LIMITED / PASS / FAIL_CLOSED gate outcomes
- RBAC (INITIATOR / APPROVER / OBSERVER) via `X-API-Key`
- Human-in-the-Loop approval (`POST /approve`)
- Hash-linked audit chain (`GET /chain/verify`)
- Structured JSON logging (`duration_ms` per request)

### Phase 3 additions (v0.5)
- `MetricsRegistry` — in-memory per-operation timers and counters
- `GET /metrics` — live timing snapshot (count/mean/median/min/max/p95)
- `GET /healthz` — DB liveness probe
- `PostgresAdapter` — documented skeleton migration target
- `migrations/001_initial_schema.sql` + `002_metrics_table.sql` — PostgreSQL 14+
- `scripts/run_benchmark.sh` — reproducible N-iteration benchmark

### Phase 4 additions (v0.6)
- **Test suite** (`tests/`) — 75 tests, 88% coverage on `main.py` + `metrics.py`
- **CI** (`.github/workflows/aem-evolve-ci.yml`) — pytest + assurance hash check on every push/PR
- **`docs/API_REFERENCE.md`** — full endpoint reference
- **`docs/ARCHITECTURE.md`** — component map, data flows, security design
- **`docs/CLAIMS_AND_NON_CLAIMS.md`** — canonical claims/non-claims + evidence map
- **ADRs** — SQLite (ADR-001), LangGraph (ADR-002), RBAC (ADR-003)
- **`sdk/aem_evolve_client.py`** — Python SDK (`AEMEvolveClient`)
- **Route fix** — `GET /chain/verify` no longer shadowed by `GET /chain/{thread_id}`

---

## Known limitations and non-claims

| Item | Status |
|---|---|
| Independent reproductions | **0 of 5 received** — reproduction challenge open |
| Production readiness | Not production-ready |
| PostgresAdapter | Documented skeleton — not tested under load |
| In-memory metrics | Not persistent across restarts |
| SDK | Initial client — no retry, async, or timeout hardening |
| External certification | Not certified; PRs 8–10 gates not satisfied |

---

## Measured performance (server-side, SQLite, localhost)

| Metric | Value |
|---|---|
| E2E median | 4.077 ms |
| E2E P95 | 31.49 ms |
| POST /approve mean | 1.155 ms |
| GET /healthz mean | 0.472 ms |

---

## How to run

```bash
git clone https://github.com/EthicBit/EthicBit_CEMU.git
cd demos/aem-evolve-multi-agent-api
pip install -r requirements.txt
python main.py
# → http://127.0.0.1:8000/docs
```

See `QUICKSTART_30_MIN.md` for the full 30-minute guided walkthrough.

---

## How to run the test suite

```bash
cd demos/aem-evolve-multi-agent-api
pip install pytest pytest-cov httpx
python -m pytest tests/ --cov=main --cov=metrics -q
# 75 passed, 88% coverage
```

---

## Assurance verification

```bash
# Verify Ed25519 manifest signature
openssl pkeyutl -verify \
  -pubin -inkey assurance/keys/ed25519_public.pem \
  -rawin -in /tmp/manifest.canonical \
  -sigfile /tmp/manifest.sig

# Verify audit chain integrity (server running)
curl -s http://127.0.0.1:8000/chain/verify \
  -H "X-API-Key: demo-observer-key-001" | python3 -m json.tool
# → {"status": "PASS", ...}
```

---

## Upgrade notes from v0.3.1-demo

No breaking changes to the API surface. Additive changes only:
- New endpoints: `GET /healthz`, `GET /metrics`
- New modules: `metrics.py`, `db_adapter.py` (PostgresAdapter)
- Route fix: `GET /chain/verify` now correctly routes before `GET /chain/{thread_id}`
- Logging: `duration_ms` added to every HTTP log entry
