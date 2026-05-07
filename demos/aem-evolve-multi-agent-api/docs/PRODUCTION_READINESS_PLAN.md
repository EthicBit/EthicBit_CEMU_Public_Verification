# AEM-EVOLVE Multi-Agent Governance API — Production-Readiness Plan

**Version:** 0.3.1-demo  
**Assurance ladder milestone:** PR 7 — Production-Readiness Hardening  
**Status:** DOCUMENTED — not implemented, not deployed

---

## Scope of This Document

This plan documents the concrete steps required to advance the AEM-EVOLVE Multi-Agent Governance API from its current demo status (`v0.3.1-demo`) toward a production-grade system.  It is a forward-looking specification, **not a claim of production readiness**.

---

## Non-Claims (Preserved)

| Claim | Status |
|---|---|
| Production ready | **false** |
| Independently reproduced | false |
| Regulatory approved | false |
| Clinical or diagnostic | false |
| Externally certified | false |
| Production-grade database storage | **false** (SQLite demo only) |
| HSM-backed key custody | false |
| Production authentication/authorization | false |

---

## Hardening Areas

### 1. Database

| Item | Current State | Target State |
|---|---|---|
| Storage engine | SQLite (single file) | PostgreSQL or equivalent RDBMS |
| Connection management | `sqlite3.connect()` direct | Connection pool (e.g. SQLAlchemy + psycopg2) |
| Migrations | None | Alembic or Flyway migration scripts |
| Concurrency | `check_same_thread=False` workaround | RDBMS-native concurrent writes |
| Backups | None | Point-in-time recovery (PITR) enabled |

**Migration path:** See `db_adapter.py` — `DBAdapter` abstract base class + `SQLiteAdapter` demo implementation. Swap in `PostgresAdapter` without changing `main.py`.

---

### 2. Authentication and Authorization

| Item | Current State | Target State |
|---|---|---|
| Key store | JSON flat file / env var | Secrets manager (Vault, AWS Secrets Manager) |
| Key rotation | Manual file replacement | Automated rotation with audit log |
| Key strength | 32-char demo strings | Cryptographically random, min 256-bit entropy |
| Multi-tenancy | Single key store | Per-tenant key namespacing |
| Session tokens | Stateless per-request | Consider short-lived JWT with JWKS validation |

---

### 3. Cryptographic Key Custody

| Item | Current State | Target State |
|---|---|---|
| Ed25519 signing key | Local PEM file (demo) | HSM-backed (e.g. AWS CloudHSM, Google Cloud HSM) |
| Key backup | None | Secure key escrow |
| Attestation | None | Third-party key attestation report |

---

### 4. Audit and Observability

| Item | Current State | Target State |
|---|---|---|
| Audit chain | SQLite `audit_chain` table | Replicated, immutable audit log (e.g. QLDB, append-only PostgreSQL partition) |
| Log transport | stdout JSON (local) | Structured log ingestion (Datadog, Splunk, OpenTelemetry) |
| Metrics | None | Prometheus/OpenTelemetry counters for events, receipts, HITL decisions |
| Alerting | None | PagerDuty / OpsGenie on HITL queue depth, chain verification failures |
| Distributed tracing | None | OpenTelemetry trace IDs propagated through agent graph |

---

### 5. API Hardening

| Item | Current State | Target State |
|---|---|---|
| TLS | None (HTTP only) | TLS termination at reverse proxy (Nginx / cloud LB) |
| Rate limiting | None | Per-key rate limits (e.g. slowapi or API gateway) |
| Input validation | Pydantic field validators | Centralized schema registry, versioned API contracts |
| Error responses | FastAPI default detail strings | Opaque error codes (no internal detail leakage) |
| CORS | Not configured | Origin allowlist |

---

### 6. Deployment

| Item | Current State | Target State |
|---|---|---|
| Runtime | `uvicorn` local dev mode | Gunicorn + uvicorn workers, or containerized (Docker) |
| Process supervision | None | systemd / Kubernetes Deployment |
| Health checks | None | `GET /healthz` liveness + readiness probes |
| Secrets injection | `.env` file / env var | Kubernetes Secrets or cloud secrets manager sidecar |
| CI/CD | None | GitHub Actions: lint → test → build → deploy pipeline |

---

### 7. Testing

| Item | Current State | Target State |
|---|---|---|
| E2E smoke test | `run_demo_e2e.sh` (bash curl) | pytest integration suite with fixtures |
| Auth control checks | `verify_auth_controls.sh` | pytest parametrized auth matrix |
| Chain verification | `verify_aem_evolve_multi_agent_audit_chain.py` | pytest + CI gate |
| Load testing | None | k6 or Locust baseline |
| Fuzz testing | None | Schemathesis API fuzzing on OpenAPI spec |

---

## Assurance Ladder Position

| PR | Milestone | Status |
|---|---|---|
| 1 | Demo Package | merged |
| 2 | Demo Mainnet Anchor | merged |
| 3 | Signed Demo Evolution Receipts | merged |
| 4 | Tamper-Evident Audit Chain | merged |
| 5 | Independent Reproduction Challenge | merged |
| 6 | Production Authentication / Authorization | merged |
| **7** | **Production-Readiness Hardening** | **this PR** |
| 8+ | External Review / Certification | conditional |
| 9+ | Regulatory Pathway | conditional |
| 10+ | Clinical / Diagnostic Pathway | conditional |

---

## Artifacts Introduced in PR 7

| Artifact | Purpose |
|---|---|
| `demos/aem-evolve-multi-agent-api/db_adapter.py` | Abstract `DBAdapter` + `SQLiteAdapter`; documents PostgreSQL migration path |
| `demos/aem-evolve-multi-agent-api/docs/PRODUCTION_READINESS_PLAN.md` | This document |
| Structured JSON logging in `main.py` | `_JsonFormatter`, `logging.config.dictConfig`, `_log_requests` middleware, `log.info()` in audit chain + HITL decision paths |
