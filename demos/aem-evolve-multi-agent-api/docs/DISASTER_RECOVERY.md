# AEM-EVOLVE™ Disaster Recovery Plan

**Version:** 2.0 | **Gate:** DISASTER_RECOVERY_CHECK | **PR:** 12  
**Status:** DR PLAN DOCUMENTED — dry-run tested, not yet executed in production  
**Prepared:** 2026-05-10

---

## Non-Claims

- This document defines the disaster recovery plan. It does NOT claim a production DR exercise has been executed.
- DR test evidence is from a dry-run simulation, not a live production recovery event.
- DR tester identity and test date require `AEM_DR_TESTER` and `AEM_DR_TEST_DATE`.
- No regulatory approval is claimed.

---

## 1. Recovery Objectives

| Objective | Target | Scope |
|-----------|--------|-------|
| `rto_minutes` | **240** (4 hours) | P1 — full service loss |
| `rpo_minutes` | **60** (1 hour) | Maximum data loss window |
| RTO (P2) | 24 hours | Partial degradation |
| RPO (P2) | 4 hours | Non-critical data loss |

**Definitions:**
- **RTO (Recovery Time Objective):** Maximum acceptable time from disaster onset to service restoration.
- **RPO (Recovery Point Objective):** Maximum acceptable data loss measured in time (last backup point).

---

## 2. Backup Strategy

| Field | Value |
|-------|-------|
| `backup_frequency` | Continuous WAL archiving + hourly snapshots (PostgreSQL PITR) |
| `retention_period` | 30 days for snapshots; 7 days for WAL archives |
| Backup location | Cross-region S3 / GCS bucket (separate from primary region) |
| Backup verification | Daily automated restore test to isolated environment |
| Encryption | AES-256 at rest; TLS 1.2+ in transit |
| Backup scope | Database (all audit tables), signing keys (KMS-managed), config artifacts |

### Backup Coverage

| Component | Backup Method | Frequency | Verified |
|-----------|--------------|-----------|---------|
| PostgreSQL audit tables | pg_dump + WAL streaming | Continuous + hourly | Daily restore test |
| KMS signing keys | KMS managed — provider backup | Provider SLA | N/A (provider managed) |
| Config artifacts (DEPLOYMENT_MANIFEST, runbooks) | Git-backed + S3 mirror | Per-commit | Weekly |
| Audit chain integrity proofs | Archived with each evolution_receipt | Per event | On-read hash verify |

---

## 3. Disaster Scenarios

Five scenarios are covered by this DR plan. All scenarios have been dry-run tested.

### Scenario DR-01: Database Loss / Corruption

**Trigger:** PostgreSQL data loss, table corruption, or accidental DROP.  
**Severity:** P1  
**RTO:** 4 hours | **RPO:** 1 hour

Recovery steps:
1. Stop the AEM-EVOLVE service (prevent further writes to corrupted state).
2. Identify the last verified backup: `aws s3 ls s3://<backup-bucket>/postgres/ --recursive | tail -5`
3. Restore from hourly snapshot:
   ```bash
   pg_restore --clean --if-exists -d $AEM_DB_URL backup_<timestamp>.dump
   ```
4. Apply WAL segments to reach RPO boundary:
   ```bash
   # PostgreSQL PITR recovery — set recovery_target_time in recovery.conf
   recovery_target_time = '<RPO_TIMESTAMP>'
   ```
5. Verify audit chain integrity after restore:
   ```bash
   python tools/production_readiness/verify_postgres_persistence.py
   python tools/production_readiness/verify_migration_recovery.py
   ```
6. Re-run all gate verifiers to confirm PASS.

### Scenario DR-02: Region Failure

**Trigger:** Cloud provider region outage (AWS us-east-1 / GCP us-central1 unavailable).  
**Severity:** P1  
**RTO:** 4 hours | **RPO:** 1 hour

Recovery steps:
1. Activate secondary region (pre-provisioned standby):
   ```bash
   export AEM_REGION=us-west-2
   export AEM_DB_URL=postgres://<standby-host>/aem_evolve
   export AEM_KMS_REGION=us-west-2
   ```
2. Promote read replica to primary (PostgreSQL streaming replication):
   ```bash
   pg_ctl promote -D /var/lib/postgresql/data
   ```
3. Update load balancer / DNS to point to secondary region.
4. Verify KMS signing works in secondary region:
   ```bash
   python tools/production_readiness/verify_kms_signing.py
   ```
5. Run full gate verifier suite against secondary region deployment.

### Scenario DR-03: KMS Key Compromise

**Trigger:** Signing key material exposed, KMS key compromised, or unauthorized key access detected.  
**Severity:** P1  
**RTO:** 2 hours (signing suspended during recovery) | **RPO:** N/A (key rotation, not data loss)

Recovery steps:
1. **Immediately** disable the compromised key in KMS:
   ```bash
   # AWS KMS
   aws kms disable-key --key-id $AEM_KMS_KEY_ID
   # GCP KMS
   gcloud kms keys versions disable <version> --key=<key-name> --keyring=<keyring> --location=<region>
   ```
2. Generate new signing key in KMS:
   ```bash
   aws kms create-key --description "aem-evolve-signing-key-v2" --key-usage SIGN_VERIFY
   export AEM_KMS_KEY_ID=<new-key-id>
   ```
3. Re-sign all pending evolution receipts with new key.
4. Audit all events signed with compromised key (quarantine suspicious events).
5. Notify Governance Lead and Security Lead.
6. Verify KMS signing resumes:
   ```bash
   python tools/production_readiness/verify_kms_signing.py
   ```

### Scenario DR-04: Full Service Outage

**Trigger:** AEM-EVOLVE service unresponsive, container crash loop, or irrecoverable process failure.  
**Severity:** P1  
**RTO:** 1 hour (cold restart) | **RPO:** 1 hour

Recovery steps:
1. Check service health and logs:
   ```bash
   docker logs aem-evolve --tail=100
   curl -s http://<host>:8000/healthz
   ```
2. Attempt graceful restart:
   ```bash
   docker restart aem-evolve
   # or Kubernetes:
   kubectl rollout restart deployment/aem-evolve -n production
   ```
3. If restart fails, perform cold start from last known-good image:
   ```bash
   docker stop aem-evolve
   docker run -d --name aem-evolve-recovery ... aem-evolve:v2.0.0
   ```
4. Verify `/health` returns all gates in expected state.
5. Run full gate verifier suite.

### Scenario DR-05: Audit Chain Corruption

**Trigger:** Audit chain integrity verification fails (`/chain/verify` returns tamper_detected=true or hash mismatch).  
**Severity:** P1  
**RTO:** 4 hours | **RPO:** 0 (no data loss — chain is append-only; corruption is detected, not caused by recovery)

Recovery steps:
1. Stop accepting new events (take service offline to prevent further writes).
2. Export the full audit chain for forensic analysis:
   ```bash
   psql $AEM_DB_URL -c "COPY audit_chain TO '/tmp/audit_chain_forensic.csv' CSV HEADER"
   ```
3. Identify the corruption boundary (last valid hash in the chain).
4. Restore the database to a pre-corruption snapshot (see DR-01).
5. Re-apply valid events from WAL up to the corruption point.
6. Re-run `/chain/verify` to confirm integrity restored.
7. Document in post-mortem using `docs/INCIDENT_RESPONSE.md` template.

---

## 4. RTO / RPO Summary Table

| Scenario | ID | Severity | RTO | RPO |
|----------|----|---------|-----|-----|
| Database loss / corruption | DR-01 | P1 | 4h | 1h |
| Region failure | DR-02 | P1 | 4h | 1h |
| KMS key compromise | DR-03 | P1 | 2h | N/A |
| Full service outage | DR-04 | P1 | 1h | 1h |
| Audit chain corruption | DR-05 | P1 | 4h | 0 |

---

## 5. Recovery Procedures Reference

| Procedure | Document | Script |
|-----------|---------|--------|
| Database rollback | `docs/ROLLBACK_RUNBOOK.md` §4 | `migrations/rollback/001_rollback_initial_schema.sql` |
| Container rollback | `docs/ROLLBACK_RUNBOOK.md` §3 | N/A (docker/kubectl command) |
| Gate verification suite | `docs/DEPLOYMENT_MANIFEST.md` §3 | `tools/production_readiness/verify_*.py` |
| Incident post-mortem | `docs/INCIDENT_RESPONSE.md` | N/A (template) |

---

## 6. DR Test Evidence

DR procedure is dry-run tested before production deployment. Test evidence is stored in:

```
tools/disaster_recovery/dr_test_evidence_2026_05.json
```

Test covers:
- `dr_scenario_data_loss` — database restore procedure validated
- `dr_scenario_region_failure` — secondary region failover steps validated
- `dr_scenario_key_compromise` — KMS key rotation procedure validated
- `dr_scenario_service_outage` — cold restart procedure validated
- `dr_scenario_audit_chain_corruption` — chain restore procedure validated

---

## 7. DR Exercise Schedule

| Exercise Type | Frequency | Responsible |
|---------------|-----------|-------------|
| DR dry-run (all scenarios) | Before each major deployment | Governance Lead |
| Live DR exercise (DR-01 only) | Quarterly | Database Admin + Governance Lead |
| Backup restore verification | Daily (automated) | Engineering |
| Full DR live exercise | Annually | All stakeholders |
