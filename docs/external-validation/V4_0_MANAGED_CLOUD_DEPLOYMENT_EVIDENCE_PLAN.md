# v4.0 Managed Cloud Deployment Evidence Plan

**Criterion:** 3 — managed_cloud_deployment
**Status:** PENDING_EXTERNAL
**Controlled assessment:** CONTROLLED_ASSESSMENT_PASS_DOCUMENTATION_AND_CODE_TIER (2026-05-14)
**Artifact:** `assurance/v4_0/evidence/V4_0_03_CLOUD_DEPLOYMENT_ARTIFACT.json`
**Constitutional dependency:** EthicBit / CEMU v3.7.0+

---

## What this criterion requires

AEM-EVOLVE must be deployed to a managed cloud environment — not a local machine — with managed compute, managed PostgreSQL, OIDC provider, and KMS/HSM. Deployment audit trail must be recorded with `AEM_DEPLOYMENT_TARGET` and `AEM_DEPLOYMENT_TIMESTAMP` set.

---

## What was already verified internally

Documentation and code tier pass. Infrastructure tier blocked on absent provisioning.

| Verifier | Result | Blocking |
|---|---|---|
| verify_deployment_audit | FAIL | AEM_DEPLOYMENT_TARGET, AEM_DEPLOYMENT_TIMESTAMP not set |
| verify_disaster_recovery | FAIL | AEM_DR_TESTER, AEM_DR_TEST_DATE not set |
| verify_governance_signoff | FAIL | AEM_GOVERNANCE_APPROVER, AEM_GOVERNANCE_SIGNOFF_DATE not set |
| verify_incident_response | FAIL | AEM_DRILL_COMPLETED_AT, AEM_DRILL_SIGNOFF_APPROVER not set |
| verify_kms_signing | FAIL | AEM_KMS_PROVIDER not set (criterion 4) |
| verify_migration_recovery | FAIL | AEM_DB_URL not set |
| verify_monitoring_alerting | FAIL | AEM_PROMETHEUS_URL not set |
| verify_oidc_provider | FAIL | OIDC_ISSUER not set |
| verify_postgres_persistence | FAIL | AEM_DB_URL not set |
| verify_rollback_procedure | FAIL | AEM_ROLLBACK_TESTER, AEM_ROLLBACK_TEST_DATE not set |
| verify_security_review | FAIL | AEM_SECURITY_REVIEWER not set (criterion 2) |
| verify_slo_evidence | FAIL | AEM_SLO_REVIEWER, AEM_SLO_REVIEW_DATE not set |

Documentation SHA256s verified for: deployment manifest, DR plan, rollback runbook, incident response, SLO, alert rules, alertmanager config, Grafana dashboard.

---

## What must be provisioned externally

### Infrastructure required

| Component | Options |
|---|---|
| Managed compute | AWS ECS / GCP Cloud Run / Azure Container Apps |
| Managed PostgreSQL | AWS RDS / GCP Cloud SQL / Azure Database |
| OIDC provider | Okta / Auth0 / Azure AD / Keycloak |
| Managed KMS / HSM | AWS KMS / GCP Cloud KMS / Azure Key Vault / PKCS11 (criterion 4) |
| Monitoring | Prometheus + Grafana or managed equivalent |

### Environment variables to set (14 required)

```bash
AEM_DEPLOYMENT_TARGET=<cloud provider and region>
AEM_DEPLOYMENT_TIMESTAMP=<ISO-8601 deployment datetime>
AEM_DB_URL=<managed PostgreSQL connection string>
AEM_KMS_PROVIDER=<aws_kms|gcp_kms|azure_key_vault|pkcs11>
AEM_KMS_KEY_ID=<key ARN or resource name>
AEM_KMS_REGION=<cloud region>
AEM_PROMETHEUS_URL=<Prometheus endpoint>
OIDC_ISSUER=<OIDC provider issuer URL>
AEM_DR_TESTER=<name of DR tester>
AEM_DR_TEST_DATE=<ISO-8601>
AEM_ROLLBACK_TESTER=<name>
AEM_ROLLBACK_TEST_DATE=<ISO-8601>
AEM_GOVERNANCE_APPROVER=<approver name>
AEM_GOVERNANCE_SIGNOFF_DATE=<ISO-8601>
AEM_DRILL_COMPLETED_AT=<ISO-8601>
AEM_DRILL_SIGNOFF_APPROVER=<name>
AEM_SLO_REVIEWER=<reviewer name>
AEM_SLO_REVIEW_DATE=<ISO-8601>
AEM_SECURITY_REVIEWER=<security reviewer identity — criterion 2>
```

Full variable reference: `demos/aem-evolve-multi-agent-api/docs/DEPLOYMENT_MANIFEST.md`

### Deployment steps

```bash
# 1. Build container image (Dockerfile is a deployment-time step — not in repo)
docker build -t aem-evolve-api:latest .

# 2. Push to managed container registry
docker push <registry>/aem-evolve-api:latest

# 3. Deploy to managed compute with all env vars set
# (see DEPLOYMENT_MANIFEST.md for provider-specific steps)

# 4. Run production readiness verifiers with env vars populated
python3 demos/aem-evolve-multi-agent-api/tools/verify_deployment_audit.py
python3 demos/aem-evolve-multi-agent-api/tools/verify_postgres_persistence.py
python3 demos/aem-evolve-multi-agent-api/tools/verify_oidc_provider.py
python3 demos/aem-evolve-multi-agent-api/tools/verify_kms_signing.py
# Expected: all 12 verifiers PASS
```

---

## Required output

- Cloud provider and region
- Commit / tag deployed
- Container image digest
- Managed PostgreSQL evidence (endpoint, version)
- OIDC configuration evidence
- KMS configuration evidence (provider, key ID, non-exportable posture)
- Monitoring evidence (Prometheus endpoint, alert rules active)
- Rollback test result
- DR dry-run result
- All 12 production readiness verifier outputs
- Deployment audit trail record

---

## Non-claim

Documentation tier verified. No actual cloud deployment has been executed. `AEM_DEPLOYMENT_TARGET` and `AEM_DEPLOYMENT_TIMESTAMP` are not set. Managed cloud deployment requires external cloud provider provisioning and completion of all 12 production readiness verifiers with infrastructure-tier checks passing.
