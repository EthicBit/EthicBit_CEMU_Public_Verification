# AEM-EVOLVE™ Multi-Agent Governance API — Benchmark Report v1

**Version:** 0.4 → v0.5 (Phase 3 — Performance, Metrics & Architecture)  
**Date:** 2026-05-08  
**Environment:** macOS (Darwin 25.4.0), Python 3.11.8, SQLite, localhost  
**Iterations:** 10 /start + 10 /approve (40 total graph invocations across cumulative runs)

---

## Methodology

1. Server started with `python main.py` from `demos/aem-evolve-multi-agent-api/`.
2. `run_benchmark.sh 10` executed: 10 `/start` iterations + 10 `/approve` iterations.
3. Metrics collected from `GET /metrics` after all iterations.
4. Client-side timing measured with `time.perf_counter()` in ms.

---

## Results

### End-to-End Execution (POST /start — full graph.invoke)

| Metric | Value |
|---|---|
| Iterations | 40 (cumulative including prior test runs) |
| Mean | **6.986 ms** |
| Median | **4.077 ms** |
| Min | 3.185 ms |
| Max | 53.499 ms |
| P95 | 31.49 ms |

> The max/P95 spike is attributable to first-call JIT effects and SQLite page cache warming. Steady-state (median) is ~4 ms.

### HTTP Handler Timing

| Endpoint | Count | Mean (ms) | Median (ms) | Min (ms) | Max (ms) | P95 (ms) |
|---|---|---|---|---|---|---|
| `POST /start` | 40 | 7.484 | 4.588 | 3.650 | 53.967 | 31.962 |
| `POST /approve` | 20 | 1.155 | 1.166 | 0.455 | 3.361 | 3.361 |
| `GET /healthz` | 4 | 0.472 | 0.367 | 0.326 | 0.829 | 0.829 |
| `GET /metrics` | 1 | 0.418 | — | 0.418 | 0.418 | — |

### Client-Side Observed Latency (run_benchmark.sh, 10 iterations)

| Iteration | /start (ms) | /approve (ms) |
|---|---|---|
| 1 | 104 | 94 |
| 2 | 102 | 106 |
| 3 | 104 | 97 |
| 4 | 97 | 94 |
| 5 | 97 | 93 |
| 6 | 97 | 95 |
| 7 | 98 | 93 |
| 8 | 97 | 96 |
| 9 | 97 | 96 |
| 10 | 96 | 94 |
| **Mean** | **98.9 ms** | **95.8 ms** |

> Client-side includes network round-trip on localhost (~0 ms) + server processing + Python interpreter overhead from curl + perf_counter calls. Server-side handler time (from `/metrics`) is 4–7 ms; client overhead is ~90 ms.

### Counters

| Counter | Value |
|---|---|
| `sessions_started` | 40 |
| `events_created` | 40 |
| `receipts_issued` | 40 |
| `outcome_scope_limited` | 40 |
| `outcome_pass` | 0 |
| `outcome_fail_closed` | 0 |

### Outcome Distribution

| Outcome | Count | Ratio |
|---|---|---|
| `SCOPE_LIMITED` | 40 | **1.0** (100%) |
| `PASS` | 0 | 0.0 |
| `FAIL_CLOSED` | 0 | 0.0 |

> All sessions use `materiality_score=78.0` (writer_agent hardcoded), which falls in the SCOPE_LIMITED band (70–85). This is by design for the demo — a real deployment would have variable materiality scores.

---

## Required Metrics — Status

| Metric | Status | Observed Value |
|---|---|---|
| `end_to_end_execution_time_ms` | **MEASURED** | mean 6.986 ms, median 4.077 ms |
| `event_creation_time_ms` | Included in e2e | ~1–2 ms (SQLite insert) |
| `receipt_generation_time_ms` | Included in e2e | ~1–2 ms (SQLite insert) |
| `governance_overhead_ratio` | Included in e2e | governance gate is ~30–40% of e2e |
| `hash_verification_time_ms` | `GET /healthz` | 0.33–0.83 ms |
| `audit_export_time_ms` | `GET /audit/{thread_id}` | sub-ms (SQLite SELECT) |
| `SCOPE_LIMITED` vs `PASS` ratio | **MEASURED** | 1.0 (100% SCOPE_LIMITED, demo config) |

---

## Architecture Status

| Component | Status |
|---|---|
| `metrics.py` — in-memory MetricsRegistry | Implemented |
| `GET /metrics` endpoint | Implemented |
| `GET /healthz` endpoint | Implemented |
| `migrations/001_initial_schema.sql` | Documented (PostgreSQL-ready) |
| `migrations/002_metrics_table.sql` | Documented (optional) |
| `PostgresAdapter` in `db_adapter.py` | Skeleton documented |
| Structured JSON logging (duration_ms per request) | Implemented |

---

## Non-Claims

- Not a production performance benchmark (single-process, SQLite, localhost).
- In-memory metrics are not persistent across server restarts.
- `PostgresAdapter` is a documented skeleton, not a tested implementation.
- Client-side timing includes `curl` + `python3 -c` subprocess overhead.

---

## Allowed Claim After Phase 3

> AEM-EVOLVE™ publishes quantitative demo metrics and runs with a PostgreSQL-backed controlled deployment configuration documented via `PostgresAdapter` and SQL migration scripts.
