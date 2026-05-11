# AEM-EVOLVE™ v2.0 — Staging Controlled Cloud Target

**Document type:** Controlled live evidence target definition
**Version:** AEM-EVOLVE™ v2.0
**Target environment:** `staging_controlled_cloud`
**Status:** LIVE EVIDENCE COLLECTION TARGET
**Production-ready claimed:** false
**Regulatory approval claimed:** false
**Legal compliance claimed:** false
**Conformity assessment claimed:** false
**External certification claimed:** false
**Tamper-proof claimed:** false

---

## 1. Purpose

This document defines the controlled live environment where AEM-EVOLVE™ v2.0 production-readiness gates can collect real evidence without claiming production readiness.

The purpose of this environment is to move from local/demo evidence into controlled live infrastructure evidence.

This target is not a universal production environment.

---

## 2. Constitutional Rule

AEM-EVOLVE™ v2.0 follows the EthicBit rule:

- evidence first
- gate second
- claim last

This environment exists to generate evidence. It does not create a production-ready claim by itself.

---

## 3. Target Environment

- target_environment: staging_controlled_cloud
- target_type: controlled_live_evidence_environment
- production_ready_claimed: false
- production_deployment_claimed: false
- production_like_claimed: true

This environment may use real cloud services, real identity providers, real managed key custody, real PostgreSQL persistence, and real monitoring.

However, until all v2.0 gates pass and are reviewed for a defined target environment, production readiness remains not claimed.

---

## 4. Gates Targeted

- PR1 — Production OIDC Provider Enforcement
- PR2 — HSM/KMS-Backed Production Signing
- PR3 — PostgreSQL Production Persistence Validation
- PR4 — Migration and Recovery Evidence
- PR5 — Monitoring and Alerting Evidence
- PR6 — Incident Response Runbook and Drill Evidence
- PR7 — Production-Readiness Security Review Evidence
- PR8 — External Reproduction Report Evidence
- PR9 — Production Deployment Audit Evidence
- PR10 — SLO Evidence for Governance Workflows
- PR11 — Tested Rollback Procedure Evidence
- PR12 — Disaster Recovery Evidence
- PR13 — Production Readiness Gate Aggregator
- PR14 — Governance Sign-Off Gate

---

## 5. Required Live Services

### 5.1 OIDC Provider

Required for PR1.

Required environment variables:

- OIDC_ISSUER
- OIDC_JWKS_URI
- OIDC_AUDIENCE

Required evidence:

- issuer validation PASS
- JWKS validation PASS
- audience validation PASS
- token expiry enforcement PASS
- invalid token rejection PASS
- missing token rejection PASS
- HITL approver bound to verified OIDC identity

### 5.2 KMS/HSM Signing Provider

Required for PR2.

Required environment variables:

- AEM_KMS_PROVIDER
- AEM_KMS_KEY_ID
- AEM_KMS_REGION
- AEM_KMS_ALGORITHM

Required evidence:

- managed key configured
- non-exportable key posture documented
- local key fallback disabled in production-like mode
- sign/verify round-trip PASS
- key usage audit logs present
- least-privilege access policy documented

Non-claim: HSM-backed or KMS-backed signing is not claimed unless configured, used, and evidenced. Tamper-proof is not claimed.

### 5.3 PostgreSQL

Required for PR3 and PR4.

Required environment variables:

- AEM_DB_URL
- AEM_DB_ADAPTER=postgres

Required evidence:

- PostgreSQLAdapter active
- SQLite disabled for this target
- migrations executed
- schema validation PASS
- connection pooling configured
- concurrent writes tested
- audit-chain integrity verified under load
- backup and restore validation PASS
- migration and rollback evidence present

### 5.4 Monitoring and Alerting

Required for PR5 and PR10.

Required environment variables:

- AEM_PROMETHEUS_URL
- AEM_ONCALL_ROTATION

Required evidence:

- metrics endpoint reachable
- alert rules loaded
- governance counters queryable
- dashboard present
- alert delivery tested
- SLO evidence reviewed

---

## 6. Human Evidence Requirements

- AEM_DRILL_COMPLETED_AT
- AEM_DRILL_SIGNOFF_APPROVER
- AEM_SECURITY_REVIEWER
- AEM_SECURITY_REVIEW_DATE
- AEM_REPRODUCER_ID
- AEM_REPRODUCTION_DATE
- AEM_DEPLOYMENT_TARGET=staging_controlled_cloud
- AEM_DEPLOYMENT_TIMESTAMP
- AEM_SLO_REVIEWER
- AEM_SLO_REVIEW_DATE
- AEM_ROLLBACK_TESTER
- AEM_ROLLBACK_TEST_DATE
- AEM_DR_TESTER
- AEM_DR_TEST_DATE
- AEM_READINESS_REVIEWER
- AEM_READINESS_REVIEW_DATE
- AEM_GOVERNANCE_APPROVER
- AEM_GOVERNANCE_SIGNOFF_DATE

---

## 7. Evidence Path

Canonical target-run evidence path:

- demos/aem-evolve-multi-agent-api/assurance/evolve-multi-agent/v2_0/

Root-level evidence may exist under:

- assurance/evolve-multi-agent/v2_0/

If both paths are used, the documentation must state which one is canonical for the target run and which one is a mirror or stack-level evidence record.

---

## 8. Expected Gate Behavior

Before live services are configured:

- file-based checks: PASS
- live checks: SKIP or FAIL
- gate status: FAIL_EXPECTED
- production_ready: false

After live services and human evidence are configured:

- file-based checks: PASS
- live checks: PASS
- gate status: PASS, only per gate
- production_ready: false until PR13 and PR14 pass

Only after all mandatory gates pass and governance sign-off is complete may the system evaluate a limited production-readiness claim for the defined target environment.

---

## 9. Approved Claim for This Target

AEM-EVOLVE™ v2.0 is ready for controlled live evidence collection in a defined staging-controlled cloud environment.

Spanish: AEM-EVOLVE™ v2.0 está listo para recolección controlada de evidencia live en un entorno cloud staging definido.

---

## 10. Explicit Non-Claims

This target does not claim:

- production readiness
- universal production readiness
- regulatory approval
- legal compliance
- conformity assessment
- external certification
- cybersecurity certification
- financial advice
- clinical or diagnostic suitability
- tamper-proof storage
- HSM-backed custody unless configured and evidenced
- independent reproduction unless external reports exist
- contractual SLA unless a real contract exists

---

## 11. Initial Execution Order

1. Configure OIDC provider
2. Configure KMS/HSM signing provider
3. Configure PostgreSQL
4. Run migrations and migration/recovery verifier
5. Configure Prometheus/Grafana/Alertmanager
6. Run PR1–PR5 verifiers
7. Execute incident response, rollback, and DR drills
8. Complete security review
9. Obtain external reproduction report
10. Complete deployment audit
11. Review SLO evidence
12. Run PR6–PR12 verifiers
13. Run PR13 production readiness aggregator
14. Run PR14 governance sign-off

---

## 12. Final Boundary

This document defines a target environment for live evidence collection.

It does not itself satisfy the v2.0 production-readiness gate.

Production readiness remains not claimed until all mandatory evidence gates are complete, verified, and accepted for this defined target environment.
