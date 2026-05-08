# AEM-EVOLVE Multi-Agent Governance API — Claims and Non-Claims

**Version:** 0.3.1-demo  
**Date:** May 2026  
**Status:** Technical Demonstration Package

This document is the canonical, versioned record of what AEM-EVOLVE™ claims and explicitly does not claim. Claims are updated with each assurance phase. Non-claims are additive — no prior non-claim is retracted without explicit justification.

---

## Allowed Claims (Cumulative through Phase 3)

### Phase 0 — Anchored Controlled Demonstration

> AEM-EVOLVE™ Multi-Agent Governance API v0.3.1-demo includes an anchored Financial Risk & Cybersecurity Response controlled execution demonstration, with the execution manifest anchored on Ethereum mainnet (TX `0x30fc9e6c…`, block 25045091) as a public timestamped integrity reference.

### Phase 1 — Independent Verification Package

> AEM-EVOLVE™ publishes a reproducible 30-minute quickstart (`QUICKSTART_30_MIN.md`), a public reproduction guide (`REPRODUCTION_GUIDE.md`), and a structured external report template (`REPRODUCTION_REPORT_TEMPLATE.md`) enabling independent third-party reproduction.

### Phase 2 — Adversarial Resilience

> AEM-EVOLVE™ includes basic adversarial-resilience test coverage (27 vectors across prompt injection, unauthorized approval, malformed payloads, and audit-chain tampering). All 27 vectors pass fail-closed or tamper-detection as expected.

### Phase 3 — Performance, Metrics & Architecture

> AEM-EVOLVE™ publishes quantitative demo metrics (server-side, SQLite, localhost): e2e median 4.08 ms, P95 31.49 ms, POST /approve mean 1.16 ms. Documents a PostgreSQL migration path via `PostgresAdapter` and SQL migration scripts.

### Phase 4 — Quality, Documentation & Polish

> AEM-EVOLVE™ provides an automated test suite with 88% coverage on core modules (`main.py`, `metrics.py`), CI verification via GitHub Actions, complete developer documentation (`API_REFERENCE.md`, `ARCHITECTURE.md`, `CLAIMS_AND_NON_CLAIMS.md`, ADRs), and an initial Python SDK.

---

## Non-Claims (Cumulative)

### Scope

| Non-claim | Value |
|---|---|
| Production-ready | **false** |
| Independently reproduced (≥3 reports) | **false** (0 received at time of writing) |
| Regulatory approved | **false** |
| Clinical or diagnostic | **false** |
| Financial advice | **false** |
| Cybersecurity certification | **false** |
| Externally certified | **false** |
| Banking approved | **false** |

### Cryptography

| Non-claim | Value |
|---|---|
| Receipt-level Ed25519 signatures | **false** — receipts are canonically hashed, not individually signed |
| HSM-backed key custody | **false** |
| Third-party key attestation | **false** |
| Manifest signing is demo-only | **true** — local Ed25519 demo key, not production |

### Storage & Persistence

| Non-claim | Value |
|---|---|
| Production-grade database | **false** — SQLite demo only |
| Tamper-proof audit chain | **false** — tamper-evident (hash-linked), not tamper-proof |
| Persistent in-memory metrics | **false** — resets on server restart |
| PostgresAdapter tested under load | **false** — documented skeleton only |

### Performance

| Non-claim | Value |
|---|---|
| Production throughput benchmark | **false** — single-process, SQLite, localhost |
| Horizontally scalable | **false** — single process, in-memory metrics |
| Thread-safe across multiple workers | **false** — MetricsRegistry not guarded |

### Authentication

| Non-claim | Value |
|---|---|
| Production identity provider | **false** — hardcoded demo API keys |
| Production authentication | **false** |

### Testing & CI

| Non-claim | Value |
|---|---|
| 100% test coverage | **false** — 88% on core modules |
| End-to-end CI on PostgreSQL | **false** — CI tests SQLite only |
| SDK production-hardened | **false** — initial client SDK, no retry/timeout hardening |

---

## Claim Evidence Map

| Claim | Evidence location |
|---|---|
| Ethereum mainnet anchor | `assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_ANCHOR_RECEIPT.json` |
| Adversarial resilience (27 vectors) | `docs/ADVERSARIAL_RESILIENCE_REPORT.md`, `adversarial_tests/` |
| Quantitative metrics | `docs/BENCHMARK_REPORT_V1.md`, `GET /metrics` |
| Test coverage (88%) | `pytest --cov` output, `pytest.ini` |
| CI pipeline | `.github/workflows/aem-evolve-ci.yml` |
| Assurance manifest | `assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_MANIFEST.json` |
| Ed25519 manifest signature | `assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_SIGNATURE_SET.json` |
| Hash record (35 files) | `assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_HASH_RECORD.txt` |

---

## How to Verify

```bash
# 1. Verify manifest Ed25519 signature
python3 -c "
import json
with open('assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_MANIFEST.json') as f:
    data = json.load(f)
import json as j; canonical = j.dumps(data, sort_keys=True, separators=(',',':'), ensure_ascii=False)
open('/tmp/manifest.bin', 'w').write(canonical)
"
openssl pkeyutl -verify \
  -pubin -inkey assurance/keys/ed25519_public.pem \
  -rawin -in /tmp/manifest.bin \
  -sigfile <(cat assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_SIGNATURE_SET.json \
             | python3 -c "import json,sys,base64; d=json.load(sys.stdin); [sys.stdout.buffer.write(base64.b64decode(s['signature_b64'])) for s in d['subjects'] if s['name']=='manifest']")

# 2. Run test suite
cd demos/aem-evolve-multi-agent-api
python -m pytest tests/ --cov=main --cov=metrics -q

# 3. Verify audit chain integrity (server running)
curl -s http://127.0.0.1:8000/chain/verify \
  -H "X-API-Key: demo-observer-key-001" | python3 -m json.tool
```
