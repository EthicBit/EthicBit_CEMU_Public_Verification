# AEM-EVOLVE™ v2.0 External Reproduction Report

**Version:** 2.0 | **Gate:** EXTERNAL_REPRODUCTION_CHECK | **PR:** 8  
**Coverage:** PR1 (OIDC) through PR7 (Security Review)  
**Report type:** Internal self-check — external reproduction in progress  
**Generated:** 2026-05-10  
**External reproducer:** _(required — set AEM_REPRODUCER_ID before production deploy)_

---

## Non-claims

- This document is an internal self-check report. It does NOT claim independent external reproduction.
- External reproduction requires execution in a separate environment by a third party who has not participated in development.
- `independent_reproduction_claimed: false`
- `third_party_attested: false`

---

## 1. What Is Being Reproduced

The AEM-EVOLVE™ v2.0 governance API production-readiness gate evidence, covering PRs 1-7:

| PR | Gate | What Was Added |
|----|------|---------------|
| PR1 | `PRODUCTION_OIDC_PROVIDER_CHECK` | External OIDC provider enforcement (`ProductionOidcProvider`) |
| PR2 | `HSM_KMS_SIGNING_CHECK` | KMS/HSM-backed signing (`ProductionKmsProvider`) |
| PR3 | `POSTGRES_PRODUCTION_PERSISTENCE_CHECK` | PostgreSQL production persistence gate |
| PR4 | `MIGRATION_RECOVERY_CHECK` | Migration and rollback evidence |
| PR5 | `MONITORING_ALERTING_CHECK` | 7 Prometheus alert rules, Grafana dashboard, counter instrumentation |
| PR6 | `INCIDENT_RESPONSE_CHECK` | Incident response runbook, drill scenario, escalation matrix |
| PR7 | `SECURITY_REVIEW_CHECK` | Security review, bandit scan (0 HIGH), pip-audit (0 CVEs) |

---

## 2. Reproduction Prerequisites

```
git >= 2.30
python3 >= 3.10
pip
openssl (for signature verification)
curl (for live endpoint checks)
```

Optional for full gate PASS:
```
PostgreSQL >= 14   (AEM_DB_URL)
AWS/GCP/Azure KMS  (AEM_KMS_PROVIDER + AEM_KMS_KEY_ID)
OIDC provider      (OIDC_ISSUER + OIDC_JWKS_URI)
Prometheus         (AEM_PROMETHEUS_URL)
```

---

## 3. Reproduction Steps

### Step 1 — Clone and install

```bash
git clone https://github.com/EthicBit/EthicBit_CEMU.git
cd EthicBit_CEMU/demos/aem-evolve-multi-agent-api
pip install -r requirements.txt
```

### Step 2 — Run the test suite

```bash
python -m pytest --tb=short
```

Expected: all tests pass (live-infra tests skipped without env vars):
```
XXX passed, YY skipped, 1 warning
```

### Step 3 — Run all production-readiness gate verifiers

```bash
python tools/production_readiness/verify_oidc_provider.py
python tools/production_readiness/verify_kms_signing.py
python tools/production_readiness/verify_postgres_persistence.py
python tools/production_readiness/verify_migration_recovery.py
python tools/production_readiness/verify_monitoring_alerting.py
python tools/production_readiness/verify_incident_response.py
python tools/production_readiness/verify_security_review.py
python tools/production_readiness/verify_reproduction.py
```

Expected (local/demo — no live infra):
```
Gate status: FAIL
Fail reason: <env var> not configured
Checks passed: N/10 (N ≥ 7 for each gate)
```

### Step 4 — Verify governance outcomes (all 3 paths)

Start the API:
```bash
python main.py &
```

```bash
# PASS path (materiality_score ≤ 70)
curl -s -X POST http://localhost:8000/start \
  -H "X-API-Key: initiator-key-001" \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"repr-pass-01","materiality_score":50.0}' | python3 -m json.tool

# SCOPE_LIMITED path (70 < score ≤ 85)
curl -s -X POST http://localhost:8000/start \
  -H "X-API-Key: initiator-key-001" \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"repr-scope-01","materiality_score":78.0}' | python3 -m json.tool

# FAIL_CLOSED path (score > 85)
curl -s -X POST http://localhost:8000/start \
  -H "X-API-Key: initiator-key-001" \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"repr-fail-01","materiality_score":90.0}' | python3 -m json.tool
```

### Step 5 — Verify HITL token enforcement

```bash
# Generate a valid HITL token
python tools/hitl/hitl_token_generator.py \
  --approver-id reproducer-001 \
  --event-id <event_id_from_step4>

# Submit approval with valid token
curl -s -X POST http://localhost:8000/approve \
  -H "X-API-Key: approver-key-001" \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"repr-scope-01","decision":"approve","hitl_token":"<token>","hitl_approver_id":"reproducer-001"}' \
  | python3 -m json.tool

# Attempt replay — must return 409
curl -s -X POST http://localhost:8000/approve \
  -H "X-API-Key: approver-key-001" \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"repr-scope-01","decision":"approve","hitl_token":"<same_token>","hitl_approver_id":"reproducer-001"}' \
  | python3 -m json.tool
```

Expected: first approval succeeds; second returns `{"detail": "HITL token already used (replay detected)..."}`.

### Step 6 — Verify audit chain integrity

```bash
curl -s http://localhost:8000/chain/verify \
  -H "X-API-Key: observer-key-001" | python3 -m json.tool
```

Expected: `"status": "PASS"`, `"tamper_evident": true`.

### Step 7 — Verify gate file checksums

```bash
python tools/production_readiness/verify_reproduction.py
```

---

## 4. Governance Outcomes Covered

| Outcome | Trigger | Expected Response |
|---------|---------|------------------|
| `PASS` | `materiality_score ≤ 70` | `status: change_completed` |
| `SCOPE_LIMITED` | `70 < materiality_score ≤ 85` | `status: change_human_approved` (after HITL) |
| `FAIL_CLOSED` | `materiality_score > 85` | `status: initialized` (blocked) |

---

## 5. v2.0 Gate File Fingerprints

Checksums of all 20 key v2.0 gate files are recorded in:

`tools/reproduction/reproduction_evidence_v2_2026_05.json`

This artifact includes SHA256 hashes of every gate module, runbook, alert rule, and security scan result added in PRs 1-7.

---

## 6. Previous Reproduction Evidence (v1.x)

The v1.x local self-check passed at commit `7aa52723`:
- 16/16 subjects matched
- Ed25519 signatures verified
- Audit chain verified

Reference: `assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_REPRODUCTION_REPORT.json`

---

## 7. External Reproduction Sign-off

| Role | Identity | Date | Notes |
|------|----------|------|-------|
| Internal self-check | AEM-EVOLVE team | 2026-05-10 | _(this document)_ |
| External reproducer | _(set `AEM_REPRODUCER_ID`)_ | _(set `AEM_REPRODUCTION_DATE`)_ | _(required for gate PASS)_ |
