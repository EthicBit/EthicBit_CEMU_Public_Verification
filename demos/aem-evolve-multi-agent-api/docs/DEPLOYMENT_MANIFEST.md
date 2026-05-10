# AEM-EVOLVE™ Production Deployment Manifest

**Version:** 2.0 | **Gate:** PRODUCTION_DEPLOYMENT_AUDIT_CHECK | **PR:** 9  
**Status:** MANIFEST DOCUMENTED — not yet deployed  
**Prepared:** 2026-05-10

---

## Non-claims

- This manifest is a pre-deployment specification. It does NOT claim a production deployment has occurred.
- Deployment evidence requires `AEM_DEPLOYMENT_TARGET` and `AEM_DEPLOYMENT_TIMESTAMP` to be set.
- No regulatory approval is claimed.

---

## 1. Target Environment

| Field | Value |
|-------|-------|
| `environment_name` | `production-v2` |
| `cloud_provider` | `aws` _(or gcp / azure — set at deploy time)_ |
| `region` | `us-east-1` _(or equivalent — set at deploy time)_ |
| `deployment_date` | _(set AEM_DEPLOYMENT_TIMESTAMP at deploy time)_ |
| `version_tag` | `v2.0.0` |
| `container_image_digest` | _(set AEM_CONTAINER_IMAGE_DIGEST at build time — e.g. sha256:abc123...)_ |

---

## 2. Required Environment Variables

All of the following must be set before production deployment. Gates FAIL without them.

| Variable | Gate | Description |
|----------|------|-------------|
| `OIDC_ISSUER` | PR1 | External OIDC provider issuer URL |
| `OIDC_JWKS_URI` | PR1 | JWKS endpoint (inferred if not set) |
| `OIDC_AUDIENCE` | PR1 | Expected JWT audience claim |
| `AEM_KMS_PROVIDER` | PR2 | KMS backend: `aws_kms`, `gcp_kms`, `azure_key_vault`, `pkcs11` |
| `AEM_KMS_KEY_ID` | PR2 | KMS key ARN / resource ID |
| `AEM_KMS_REGION` | PR2 | KMS region (AWS/GCP) |
| `AEM_DB_URL` | PR3 | PostgreSQL connection URL |
| `AEM_DB_ADAPTER` | PR3 | Must be `postgres` (not `sqlite`) |
| `AEM_PROMETHEUS_URL` | PR5 | Prometheus base URL for alert rule loading |
| `AEM_DRILL_COMPLETED_AT` | PR6 | ISO8601 timestamp of last incident response drill |
| `AEM_DRILL_SIGNOFF_APPROVER` | PR6 | Identity of drill sign-off approver |
| `AEM_SECURITY_REVIEWER` | PR7 | External security reviewer identity |
| `AEM_SECURITY_REVIEW_DATE` | PR7 | ISO8601 date of external security review |
| `AEM_REPRODUCER_ID` | PR8 | External reproduction identity |
| `AEM_REPRODUCTION_DATE` | PR8 | ISO8601 date of external reproduction |
| `HITL_SECRET` | AUTH | HMAC secret for HITL token signing |
| `AEM_DEMO_AUTH_KEYS_JSON` | AUTH | API key store JSON |
| `AEM_LOG_LEVEL` | OPS | Log level (`INFO` in production) |

---

## 3. Pre-Deployment Gate Checklist

All gates must report `PASS` before production deployment. Run:

```bash
python tools/production_readiness/verify_oidc_provider.py       # PR1
python tools/production_readiness/verify_kms_signing.py         # PR2
python tools/production_readiness/verify_postgres_persistence.py # PR3
python tools/production_readiness/verify_migration_recovery.py  # PR4
python tools/production_readiness/verify_monitoring_alerting.py  # PR5
python tools/production_readiness/verify_incident_response.py   # PR6
python tools/production_readiness/verify_security_review.py     # PR7
python tools/production_readiness/verify_reproduction.py        # PR8
python tools/production_readiness/verify_deployment_audit.py    # PR9
```

| PR | Gate | Required Status |
|----|------|----------------|
| PR1 | `PRODUCTION_OIDC_PROVIDER_CHECK` | PASS |
| PR2 | `HSM_KMS_SIGNING_CHECK` | PASS |
| PR3 | `POSTGRES_PRODUCTION_PERSISTENCE_CHECK` | PASS |
| PR4 | `MIGRATION_RECOVERY_CHECK` | PASS |
| PR5 | `MONITORING_ALERTING_CHECK` | PASS |
| PR6 | `INCIDENT_RESPONSE_CHECK` | PASS |
| PR7 | `SECURITY_REVIEW_CHECK` | PASS |
| PR8 | `EXTERNAL_REPRODUCTION_CHECK` | PASS |
| PR9 | `PRODUCTION_DEPLOYMENT_AUDIT_CHECK` | PASS |

---

## 4. Container Image

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Non-root user
RUN useradd -r -u 1001 aem && chown -R aem:aem /app
USER aem

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

Build with digest pinning:
```bash
docker build -t aem-evolve:v2.0.0 .
docker inspect --format='{{index .RepoDigests 0}}' aem-evolve:v2.0.0
# Set: export AEM_CONTAINER_IMAGE_DIGEST=sha256:<digest>
```

---

## 5. Health Check Verification

After deployment, verify all three endpoints:

```bash
# Liveness
curl -s http://<host>:8000/healthz | python3 -m json.tool
# Expected: {"status": "ok", "version": "0.16.0-demo"}

# Readiness + gate status
curl -s http://<host>:8000/health | python3 -m json.tool
# Expected: all gate statuses present; version matches

# Metrics
curl -s http://<host>:8000/metrics | python3 -m json.tool
# Expected: counters dict with governance failure counters
```

---

## 6. Rollback Plan

If a deployment fails or a gate regresses to FAIL after deployment:

1. **Stop traffic** — remove the deployment from the load balancer / ingress.
2. **Identify the failing gate** — check `/health` for gate status; run the failing gate's verifier.
3. **Roll back the container** — redeploy the previous image tag:
   ```bash
   docker run -e ... aem-evolve:v1.x.x-previous
   ```
4. **Roll back the database** (if schema migration was applied):
   ```bash
   psql $AEM_DB_URL -f migrations/rollback/001_rollback_initial_schema.sql
   # Verify: python tools/production_readiness/verify_migration_recovery.py
   ```
5. **Verify previous version is stable** — run full gate verifier suite.
6. **Root cause analysis** — document in post-mortem using `docs/INCIDENT_RESPONSE.md` template.
7. **Governance Lead sign-off** — required before re-attempting deployment.

---

## 7. Deployment Audit Trail

All deployment events must be recorded in the audit chain:

- Deployment initiation event (`evolution_event` with `change_type: deployment`)
- Gate verification receipt (`evolution_receipt` with outcome)
- Governance Lead approval (`human_decision` record)

Deployment audit artifact: `tools/deployment/deployment_audit_2026_05.json`
