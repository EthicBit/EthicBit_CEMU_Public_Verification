# AEM-EVOLVE™ Service Level Objectives

**Version:** 2.0 | **Gate:** SLO_EVIDENCE_CHECK | **PR:** 10  
**Status:** SLO DOCUMENTED — not yet measured in production  
**Prepared:** 2026-05-10

---

## Non-Claims

- This document defines target SLOs for a production deployment. It does NOT claim these SLOs have been achieved or measured in production.
- Error budget tracking requires a running Prometheus + Alertmanager receiving live traffic.
- SLO verification evidence requires `AEM_SLO_REVIEWER` and `AEM_SLO_REVIEW_DATE` to be set.
- No regulatory approval is claimed.

---

## 1. SLO Definitions

### 1.1 Availability

| Field | Value |
|-------|-------|
| `availability` | Target availability: **99.9%** over a 30-day rolling window |
| Measurement window | 30 days (2,592,000 seconds) |
| Error budget | 0.1% → **43.8 minutes/month** |
| Indicator | `1 - (http_5xx_total / http_requests_total)` |
| Exclusions | Planned maintenance windows (pre-announced ≥48h) |

### 1.2 Latency (P99)

| Field | Value |
|-------|-------|
| `latency_p99` | P99 request latency < **500ms** for 99.5% of requests |
| Measurement | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` |
| Scope | All non-streaming API endpoints |
| Exclusions | LLM advisory calls (unbounded, advisory-only) |

### 1.3 Error Rate

| Field | Value |
|-------|-------|
| `error_rate` | HTTP 5xx error rate < **0.1%** over 5-minute rolling window |
| Indicator | `rate(http_5xx_total[5m]) / rate(http_requests_total[5m])` |
| Governance failure counters | Separately tracked; gate-level SLOs defined in §4 |

### 1.4 Governance Gate Pass Rate

| Field | Value |
|-------|-------|
| `governance_gate_pass_rate` | HITL approval success rate > **99.0%** |
| Indicator | `1 - (aem_hitl_approval_failed_total / hitl_approval_requests_total)` |
| Supporting counters | All 7 governance failure counters (§4) |

---

## 2. Error Budgets

| SLO Dimension | Target | Error Budget | Budget Period |
|---------------|--------|-------------|---------------|
| availability | 99.9% | 43.8 min/month | 30 days |
| latency_p99 | 99.5% at <500ms | 7.2 min/month | 30 days |
| error_rate | <0.1% | 43.8 min downtime equivalent | 30 days |
| governance_gate_pass_rate | >99.0% | 14.4 min/month | 30 days |

### Error Budget Burn Rate Thresholds

| Alert Window | Burn Rate Multiplier | Budget Consumed | Action |
|-------------|---------------------|-----------------|--------|
| Fast burn: 1h | **14×** (error rate > 1.4%) | 2% of monthly budget | Page on-call immediately |
| Slow burn: 6h | **3×** (error rate > 0.3%) | 5% of monthly budget | Alert governance lead |
| Budget exhausted | 100% consumed | 0 minutes remaining | Freeze new deployments |

---

## 3. Burn Rate Alert Rules

The following burn rate expressions are referenced in `monitoring/alert_rules.yaml`:

```yaml
# Fast burn — availability (1h window, 14x burn rate)
- alert: AEM_SLOFastBurn_Availability
  expr: >
    (
      rate(http_5xx_total[1h]) / rate(http_requests_total[1h]) > 0.014
    ) and (
      rate(http_5xx_total[5m]) / rate(http_requests_total[5m]) > 0.014
    )
  for: 2m
  labels:
    severity: critical
    slo: availability
  annotations:
    summary: "Fast burn: availability SLO error budget consuming at 14x rate"

# Slow burn — availability (6h window, 3x burn rate)
- alert: AEM_SLOSlowBurn_Availability
  expr: >
    (
      rate(http_5xx_total[6h]) / rate(http_requests_total[6h]) > 0.003
    ) and (
      rate(http_5xx_total[30m]) / rate(http_requests_total[30m]) > 0.003
    )
  for: 15m
  labels:
    severity: warning
    slo: availability
  annotations:
    summary: "Slow burn: availability SLO error budget consuming at 3x rate"

# Fast burn — governance gate pass rate (1h window)
- alert: AEM_SLOFastBurn_GovernanceGate
  expr: >
    rate(aem_hitl_approval_failed_total[1h]) > 0.01
  for: 5m
  labels:
    severity: critical
    slo: governance_gate_pass_rate
  annotations:
    summary: "Fast burn: governance gate pass rate SLO breach"
```

---

## 4. Governance Gate SLOs (PR1-PR9)

Each gate maps to an operational SLO target. All 9 gates are covered.

| Gate | PR | SLO Dimension | Target |
|------|----|--------------|--------|
| `PRODUCTION_OIDC_PROVIDER_CHECK` | PR1 | availability | OIDC token verification success rate > 99.9% |
| `HSM_KMS_SIGNING_CHECK` | PR2 | availability | KMS signing success rate > 99.9% |
| `POSTGRES_PRODUCTION_PERSISTENCE_CHECK` | PR3 | availability | DB write success rate > 99.9% |
| `MIGRATION_RECOVERY_CHECK` | PR4 | availability | Migration rollback success rate = 100% |
| `MONITORING_ALERTING_CHECK` | PR5 | error_rate | Alert delivery latency < 5 min for critical alerts |
| `INCIDENT_RESPONSE_CHECK` | PR6 | latency_p99 | Incident acknowledged within SLA (P1 < 15 min) |
| `SECURITY_REVIEW_CHECK` | PR7 | governance_gate_pass_rate | 0 HIGH severity findings in production scans |
| `EXTERNAL_REPRODUCTION_CHECK` | PR8 | availability | Reproduction evidence checksum verification = 100% |
| `PRODUCTION_DEPLOYMENT_AUDIT_CHECK` | PR9 | availability | Deployment audit artifact integrity = 100% |

### Governance Failure Counter Targets

| Counter | SLO Target |
|---------|-----------|
| `aem_hitl_approval_failed_total` | < 1% of HITL requests |
| `aem_signature_verification_failed_total` | < 0.01% of signing operations |
| `aem_replay_attempt_detected_total` | Informational (no target — block all replays) |
| `aem_audit_chain_mismatch_total` | 0 (zero tolerance) |
| `aem_database_unavailable_total` | < 0.1% of DB operations |
| `aem_kms_signing_failed_total` | < 0.01% of KMS operations |
| `aem_oidc_provider_outage_total` | < 0.1% of OIDC validations |

---

## 5. Measurement Methodology

### 5.1 Counter-to-SLO Mapping

AEM-EVOLVE™ exposes governance failure counters via `/metrics`. These counters map to SLO indicators:

```
availability SLO    ← aem_database_unavailable_total, aem_kms_signing_failed_total,
                       aem_oidc_provider_outage_total
error_rate SLO      ← aem_hitl_approval_failed_total, aem_signature_verification_failed_total
governance SLO      ← aem_audit_chain_mismatch_total, aem_replay_attempt_detected_total
```

### 5.2 Prometheus Scrape Configuration

```yaml
scrape_configs:
  - job_name: aem-evolve
    static_configs:
      - targets: ['<host>:8000']
    metrics_path: /metrics
    scrape_interval: 15s
    params:
      api_key: ['<METRICS_API_KEY>']
```

### 5.3 SLO Recording Rules

```yaml
# 30-day availability SLO recording rule
- record: aem_availability_slo:ratio_rate30d
  expr: >
    1 - (
      rate(http_5xx_total[30d]) /
      rate(http_requests_total[30d])
    )
```

---

## 6. SLO Review Sign-Off

| Field | Value |
|-------|-------|
| Reviewer | _(set `AEM_SLO_REVIEWER` at review time)_ |
| Review date | _(set `AEM_SLO_REVIEW_DATE` at review time)_ |
| Review scope | SLO targets, error budgets, burn rate thresholds, governance gate SLO mapping |
| Next review | 90 days after initial production deployment |
