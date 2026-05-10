# AEM-EVOLVE™ Rollback Runbook

**Version:** 2.0 | **Gate:** ROLLBACK_PROCEDURE_CHECK | **PR:** 11  
**Status:** RUNBOOK DOCUMENTED — dry-run tested, not yet executed in production  
**Prepared:** 2026-05-10

---

## Non-Claims

- This runbook documents rollback procedures. It does NOT claim a production rollback has been executed.
- Rollback test evidence is from a dry-run simulation, not a live production rollback.
- Rollback tester identity and test date require `AEM_ROLLBACK_TESTER` and `AEM_ROLLBACK_TEST_DATE`.
- No regulatory approval is claimed.

---

## 1. Rollback Decision Criteria

A rollback is triggered when any of the following occur after deployment:

| Trigger | Gate Impacted | Severity |
|---------|--------------|---------|
| OIDC token verification failure rate > 1% | PR1 — PRODUCTION_OIDC_PROVIDER_CHECK | P1 |
| KMS signing failure rate > 0.01% | PR2 — HSM_KMS_SIGNING_CHECK | P1 |
| Database write failure rate > 0.1% | PR3 — POSTGRES_PRODUCTION_PERSISTENCE_CHECK | P1 |
| Migration rollback required | PR4 — MIGRATION_RECOVERY_CHECK | P1 |
| Alert rule delivery failure | PR5 — MONITORING_ALERTING_CHECK | P2 |
| Incident response SLA breach | PR6 — INCIDENT_RESPONSE_CHECK | P2 |
| Security scan finds HIGH severity finding | PR7 — SECURITY_REVIEW_CHECK | P1 |
| Audit chain integrity failure | PR8 — EXTERNAL_REPRODUCTION_CHECK | P1 |
| Deployment audit artifact mismatch | PR9 — PRODUCTION_DEPLOYMENT_AUDIT_CHECK | P1 |

---

## 2. Rollback Procedure (7 Steps)

### Step 1 — Stop Traffic

Remove the deployment from the load balancer / ingress to prevent further requests:

```bash
# Kubernetes
kubectl scale deployment aem-evolve --replicas=0 -n production

# Docker Compose
docker-compose stop aem-evolve

# Manual — remove from load balancer target group
aws elbv2 deregister-targets --target-group-arn $TARGET_GROUP_ARN \
  --targets Id=$INSTANCE_ID
```

**Rollback decision authority:** Governance Lead or on-call engineer (P1) / Governance Lead approval required (P2).

### Step 2 — Identify the Failing Gate

Check `/health` for gate status and run the failing gate's verifier:

```bash
# Check all gate statuses
curl -s http://<host>:8000/health | python3 -m json.tool | grep -A3 '"status"'

# Run individual gate verifiers
python tools/production_readiness/verify_oidc_provider.py         # PR1
python tools/production_readiness/verify_kms_signing.py           # PR2
python tools/production_readiness/verify_postgres_persistence.py  # PR3
python tools/production_readiness/verify_migration_recovery.py    # PR4
python tools/production_readiness/verify_monitoring_alerting.py   # PR5
python tools/production_readiness/verify_incident_response.py     # PR6
python tools/production_readiness/verify_security_review.py       # PR7
python tools/production_readiness/verify_reproduction.py          # PR8
python tools/production_readiness/verify_deployment_audit.py      # PR9
python tools/production_readiness/verify_rollback_procedure.py    # PR11
```

### Step 3 — Roll Back the Container

Redeploy the previous known-good image tag:

```bash
# Identify the previous image tag from deployment audit
cat tools/deployment/deployment_audit_2026_05.json | python3 -m json.tool

# Redeploy previous version
docker run -d \
  --name aem-evolve-rollback \
  -p 8000:8000 \
  -e OIDC_ISSUER=$OIDC_ISSUER \
  -e AEM_KMS_PROVIDER=$AEM_KMS_PROVIDER \
  -e AEM_KMS_KEY_ID=$AEM_KMS_KEY_ID \
  -e AEM_DB_URL=$AEM_DB_URL \
  -e AEM_DB_ADAPTER=$AEM_DB_ADAPTER \
  -e HITL_SECRET=$HITL_SECRET \
  -e AEM_DEMO_AUTH_KEYS_JSON=$AEM_DEMO_AUTH_KEYS_JSON \
  aem-evolve:v1.x.x-previous

# Kubernetes
kubectl set image deployment/aem-evolve \
  aem-evolve=aem-evolve:v1.x.x-previous -n production
```

### Step 4 — Roll Back the Database

Execute if schema migration was applied and data loss is acceptable after verified backup:

```bash
# Step 4a — Take a backup before rollback
pg_dump $AEM_DB_URL > backup_pre_rollback_$(date +%Y%m%d_%H%M%S).sql

# Step 4b — Execute rollback migrations in reverse order
psql $AEM_DB_URL -f migrations/rollback/003_rollback_langraph_checkpointer.sql
psql $AEM_DB_URL -f migrations/rollback/002_rollback_metrics_table.sql
psql $AEM_DB_URL -f migrations/rollback/001_rollback_initial_schema.sql

# Step 4c — Verify rollback
python tools/production_readiness/verify_migration_recovery.py
```

**CAUTION:** `migrations/rollback/001_rollback_initial_schema.sql` drops all audit tables. Backup is mandatory before execution.

### Step 5 — Verify Previous Version is Stable

Run the full gate verifier suite against the rolled-back deployment:

```bash
for verifier in \
  verify_oidc_provider.py \
  verify_kms_signing.py \
  verify_postgres_persistence.py \
  verify_migration_recovery.py \
  verify_monitoring_alerting.py \
  verify_incident_response.py \
  verify_security_review.py \
  verify_reproduction.py \
  verify_deployment_audit.py; do
  echo "=== $verifier ==="
  python tools/production_readiness/$verifier
done
```

All gates must report PASS (or FAIL only for live-infra checks that were also failing before rollback).

### Step 6 — Root Cause Analysis

Document the incident using `docs/INCIDENT_RESPONSE.md` template:

```
Incident ID  : INC-<YYYY-MM-DD>-<seq>
Severity     : P1 / P2 / P3
Gate impacted: <gate name>
Timeline     :
  - <HH:MM> Deployment initiated
  - <HH:MM> Gate regression detected
  - <HH:MM> Rollback decision taken
  - <HH:MM> Container rolled back
  - <HH:MM> DB rolled back (if applicable)
  - <HH:MM> All gates restored to previous PASS state
Root cause   : <description>
Prevention   : <remediation action>
```

### Step 7 — Governance Lead Sign-Off

Required before re-attempting deployment:

- [ ] Post-mortem document completed and reviewed
- [ ] Root cause identified and remediation plan documented
- [ ] Governance Lead approval recorded as `human_decision` in audit chain
- [ ] Updated gate verifier artifacts generated
- [ ] All 9 gates passing before re-deployment

---

## 3. Container Rollback Reference

| Scenario | Command |
|----------|---------|
| Docker single container | `docker stop aem-evolve && docker run ... aem-evolve:v1.x.x-previous` |
| Docker Compose | `docker-compose down && docker-compose up -d` (with previous image in compose file) |
| Kubernetes | `kubectl rollout undo deployment/aem-evolve -n production` |
| Kubernetes (specific revision) | `kubectl rollout undo deployment/aem-evolve --to-revision=<N> -n production` |

---

## 4. Database Rollback Reference

| Script | Tables Affected | CAUTION |
|--------|----------------|---------|
| `migrations/rollback/001_rollback_initial_schema.sql` | Drops: evolution_events, evolution_receipts, human_decisions, audit_chain, hitl_used_tokens | DATA LOSS — backup required |
| `migrations/rollback/002_rollback_metrics_table.sql` | Drops: operation_metrics | DATA LOSS — backup required |
| `migrations/rollback/003_rollback_langraph_checkpointer.sql` | Drops: LangGraph checkpoint tables | DATA LOSS — backup required |

---

## 5. Rollback Test Evidence

Rollback procedure is dry-run tested before production deployment. Test evidence is stored in:

```
tools/rollback/rollback_test_evidence_2026_05.json
```

Test covers:
- `rollback_scenario_container` — container rollback simulation
- `rollback_scenario_db` — database rollback SQL syntax validation
- `rollback_scenario_gate_verification` — gate verifier execution after simulated rollback
- `rollback_scenario_rca_template` — RCA document template validation
- `rollback_scenario_governance_signoff` — governance sign-off checklist validation

---

## 6. Rollback Checklist Summary

| Step | Action | Required |
|------|--------|---------|
| 1 | Stop traffic | Yes |
| 2 | Identify failing gate | Yes |
| 3 | Roll back container | Yes |
| 4 | Roll back database | If migration applied |
| 5 | Verify stability | Yes |
| 6 | Root cause analysis | Yes |
| 7 | Governance Lead sign-off | Yes |
