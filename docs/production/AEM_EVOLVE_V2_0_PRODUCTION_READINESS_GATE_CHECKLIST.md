# AEM-EVOLVE™ v2.0+ Production Readiness Gate Checklist

**Document type:** Gate definition — mandatory evidence checklist  
**Version:** v2.0  
**Date:** 2026-05-10  
**Status:** ACTIVE — defines required evidence for v2.0+ production-readiness evaluation

---

## Claim permitted by this document

> This checklist defines the official AEM-EVOLVE™ v2.0+ Production Readiness Gate and the mandatory evidence required before any production-readiness claim can be evaluated.

## Mandatory non-claim

> This checklist does not claim that AEM-EVOLVE™ is production-ready.

---

## Governing rule

```
evidence first → gate second → claim last
```

No individual PR declares production readiness. Each PR adds one layer of evidence. Only the PR 13 aggregator can emit `PRODUCTION_READINESS_GATE=PASS`, and only if all gates PR 1–12 produce their required output for a **defined target environment**. PR 14 documents the factual result.

---

## The formula

```
v1.x (v1.1–v1.9) = production-hardening evidence path    [COMPLETE]
v2.0 PR 0–14      = production-readiness gate             [THIS DOCUMENT OPENS THE GATE]

production-ready = PRODUCTION_READINESS_GATE=PASS
                  for a defined target environment
                  with all 12 mandatory gates satisfied
```

The hardening sequence (v1.1–v1.9) is a prerequisite, not sufficient. The gate sequence (v2.0) requires evidence from real external systems, real operations, and third parties for a **defined target environment**.

---

## Defined target environment requirement

Every evidence artifact in PR 1–12 must specify:

| Field | Example |
|---|---|
| `environment_name` | `"ethicbit-staging-gcp-us-central1"` |
| `cloud_provider` | `"GCP"` |
| `region` | `"us-central1"` |
| `deployment_date` | ISO 8601 |
| `version_tag` | `"v2.0.0"` |
| `container_image_digest` | `"sha256:..."` |

A claim scoped to one environment does NOT transfer to another. A new defined target environment requires a new gate run.

---

## Mandatory gates — PR 1–12

### PR 1 — Production OIDC provider enforcement

**Type:** feat  
**Required output:** `PRODUCTION_OIDC_PROVIDER_CHECK=PASS`

Mandatory evidence:
- [ ] External OIDC provider configured and reachable (Okta, Auth0, Azure AD, Keycloak)
- [ ] Issuer validation PASS
- [ ] JWKS validation PASS against external provider
- [ ] Audience validation PASS
- [ ] Role/claim mapping PASS
- [ ] Token expiry enforcement PASS
- [ ] Invalid token rejection PASS
- [ ] Missing token rejection PASS
- [ ] HITL approver identity bound to verified OIDC identity

Claim permitted (if gate passes):
> AEM-EVOLVE™ v2.0+ supports production OIDC-based identity enforcement for governed approval and audit workflows.

Non-claims:
- Not universal identity assurance
- Not regulatory-approved identity control
- Not external IAM certification
- Not production-ready by itself

---

### PR 2 — HSM / KMS-backed production signing

**Type:** feat  
**Required output:** `HSM_KMS_SIGNING_CHECK=PASS`

Mandatory evidence:
- [ ] KMS/HSM provider configured (AWS KMS, GCP Cloud HSM, Azure Key Vault, PKCS#11)
- [ ] Non-exportable key posture documented
- [ ] Local/private-key fallback disabled in production mode
- [ ] All production signing operations use KMS/HSM
- [ ] Public-key verification PASS
- [ ] Key rotation policy documented
- [ ] Key usage audit logs present
- [ ] Least-privilege IAM policy for signing role present

Claim permitted:
> AEM-EVOLVE™ v2.0+ supports hardware-backed or managed-key custody for production signing workflows with non-exportable key posture and audit-backed operations.

Non-claims:
- Not tamper-proof
- Not FIPS-validated unless separately evidenced
- Not HSM-certified unless separately evidenced
- Not production-ready by itself

---

### PR 3 — PostgreSQL production persistence validation

**Type:** feat  
**Required output:** `POSTGRES_PRODUCTION_PERSISTENCE_CHECK=PASS`

Mandatory evidence:
- [ ] PostgreSQLAdapter active in production config
- [ ] SQLite disabled in production mode
- [ ] Migrations executed successfully
- [ ] Schema validation PASS
- [ ] Connection pooling configured (pgbouncer or equivalent)
- [ ] Load test under concurrent approvals/writes
- [ ] Audit-chain integrity verified under load
- [ ] Backup and restore validation PASS

Claim permitted:
> AEM-EVOLVE™ v2.0+ supports PostgreSQL-backed audit persistence validated under load-tested production-like conditions.

Non-claims:
- Not universal production database readiness
- Not enterprise production-ready by itself
- Not tamper-proof storage

---

### PR 4 — Migration and recovery evidence

**Type:** assurance  
**Required output:** `MIGRATION_RECOVERY_CHECK=PASS`

Mandatory evidence:
- [ ] Forward migration hash before/after
- [ ] Rollback migration hash before/after
- [ ] Receipt/event count reconciliation
- [ ] Audit-chain continuity verification
- [ ] Backup restore test
- [ ] Full restore + audit-chain verification

Claim permitted:
> AEM-EVOLVE™ v2.0+ includes migration and recovery evidence preserving audit-chain continuity across storage transitions.

Non-claims:
- Not disaster recovery complete by itself
- Not production-ready by itself
- Not zero data loss unless RPO evidence separately supports it

---

### PR 5 — Monitoring and alerting evidence

**Type:** ops  
**Required output:** `MONITORING_ALERTING_CHECK=PASS`

Mandatory alerts (must be configured and tested):
- [ ] Failed HITL approval
- [ ] Signature verification failure
- [ ] Replay attempt detected
- [ ] Audit-chain mismatch
- [ ] Database unavailable
- [ ] KMS/HSM signing failure
- [ ] OIDC provider outage

Mandatory evidence:
- [ ] Prometheus metrics exported
- [ ] Grafana dashboard present
- [ ] Structured logs aggregated
- [ ] Alerts configured
- [ ] Alerts tested (fire + receive evidence)
- [ ] Alert delivery evidence present

Claim permitted:
> AEM-EVOLVE™ v2.0+ includes monitoring and alerting evidence for governance-critical failure modes.

Non-claims:
- Not SOC-ready by itself
- Not 24/7 managed monitoring unless separately evidenced
- Not contractual SLA

---

### PR 6 — Incident response runbook and drill evidence

**Type:** ops  
**Required output:** `INCIDENT_RESPONSE_CHECK=PASS`

Mandatory scenarios (runbook + drill):
- [ ] Signature verification failure
- [ ] HITL replay attempt
- [ ] Unauthorized approval attempt
- [ ] OIDC provider outage
- [ ] KMS/HSM outage
- [ ] PostgreSQL outage
- [ ] Audit-chain mismatch
- [ ] Suspected credential exposure
- [ ] Rollback trigger
- [ ] Public-status correction
- [ ] Evidence preservation

Mandatory evidence:
- [ ] Documented runbook covering all scenarios
- [ ] Tabletop or live drill executed
- [ ] Drill report with outcomes and improvements

Claim permitted:
> AEM-EVOLVE™ v2.0+ includes incident-response procedures for governance, identity, custody, audit, and rollback failure modes.

Non-claims:
- Not incident-response certified
- Not SOC2/ISO certified
- Not production-ready by itself

---

### PR 7 — Production-readiness security review evidence

**Type:** security  
**Required output:** `SECURITY_REVIEW_CHECK=PASS`

Mandatory evidence:
- [ ] Secret scan (no secrets in repo)
- [ ] Dependency scan (CVE audit)
- [ ] Container scan (image vulnerabilities)
- [ ] SAST (static analysis)
- [ ] AuthN/AuthZ review
- [ ] KMS/HSM policy review
- [ ] OIDC configuration review
- [ ] Database permissions review
- [ ] Threat model documented
- [ ] Residual risks register
- [ ] Remediation record

Claim permitted:
> AEM-EVOLVE™ v2.0+ has undergone documented security review for production-readiness controls.

Non-claims:
- Do not claim "secure"
- Do not claim "production-secure"
- Do not claim externally certified
- Do not claim vulnerability-free

---

### PR 8 — External reproduction report evidence

**Type:** assurance  
**Required output:** `EXTERNAL_REPRODUCTION_CHECK=PASS`  
**Minimum:** 1 external reproduction report (target: 3+)

Mandatory fields per report:
- [ ] Independent environment (not EthicBit infrastructure)
- [ ] Fresh clone from public repo
- [ ] Commands used (verbatim transcript)
- [ ] Full test outputs
- [ ] Health endpoint outputs
- [ ] Hash records
- [ ] Verifier identity/org (or pseudonym with env fingerprint)
- [ ] Date/time
- [ ] Environment description (OS, Python, hardware)
- [ ] Deviation notes (if any)
- [ ] PASS/FAIL conclusion

Claim permitted:
> AEM-EVOLVE™ v2.0+ has at least one external reproduction report confirming public or independent verification of selected governance evidence.

Non-claims:
- Not universal independent reproduction
- Not full external certification
- Not production-ready by itself
- Not regulatory approval

---

### PR 9 — Production deployment audit evidence

**Type:** assurance  
**Required output:** `PRODUCTION_DEPLOYMENT_AUDIT_CHECK=PASS`

Mandatory evidence for the defined target environment:
- [ ] Cloud provider / region / network topology
- [ ] Exact version/tag deployed
- [ ] Container image digest
- [ ] Redacted config snapshot (no secrets)
- [ ] OIDC enabled and pointed to external provider
- [ ] KMS/HSM enabled (local signing disabled)
- [ ] PostgreSQL enabled (SQLite disabled)
- [ ] Secrets excluded from repo and config snapshots
- [ ] Rollback verified
- [ ] Monitoring active
- [ ] Audit trail active

Claim permitted:
> AEM-EVOLVE™ v2.0+ includes production deployment audit evidence for a configured production or production-like environment.

Non-claims:
- Not universal production readiness
- Not external certification
- Not regulatory approval

---

### PR 10 — SLO evidence for governance workflows

**Type:** ops  
**Required output:** `SLO_EVIDENCE_CHECK=PASS`

Mandatory SLO definitions and measurements:
- [ ] Availability target (e.g., 99.5% over 30-day window)
- [ ] Latency targets (p50, p95, p99 for /approve, /start, /receipt)
- [ ] Error-rate target
- [ ] Observed metrics window (minimum 7 days)
- [ ] SLO dashboard or export
- [ ] Known exclusions documented
- [ ] Error budget policy documented

Claim permitted:
> AEM-EVOLVE™ v2.0+ defines and measures SLOs for governance-critical workflows.

Non-claims:
- No contractual SLA unless a real contract exists separately
- Not production-ready by itself
- Not a guarantee of future availability

---

### PR 11 — Tested rollback procedure evidence

**Type:** ops  
**Required output:** `ROLLBACK_PROCEDURE_CHECK=PASS`

Mandatory evidence:
- [ ] Rollback trigger criteria documented
- [ ] Previous image digest/version identified
- [ ] Database rollback strategy (migration down or snapshot restore)
- [ ] Config rollback method
- [ ] KMS/OIDC caveats documented (key rotation implications)
- [ ] Post-rollback verification steps
- [ ] Audit-chain preservation across rollback
- [ ] Rollback drill executed and reported

Claim permitted:
> AEM-EVOLVE™ v2.0+ includes a tested rollback procedure for production or production-like deployments.

Non-claims:
- Not zero-downtime rollback unless separately evidenced
- Not universal rollback guarantee
- Not disaster recovery by itself

---

### PR 12 — Disaster recovery evidence

**Type:** ops  
**Required output:** `DISASTER_RECOVERY_CHECK=PASS`

Mandatory evidence:
- [ ] Backup schedule documented
- [ ] Retention policy documented
- [ ] Restore procedure documented
- [ ] Restore test executed
- [ ] RTO and RPO measured (not just defined)
- [ ] Backup checksum validation
- [ ] Key custody continuity plan (KMS/HSM outage)
- [ ] OIDC outage handling
- [ ] Audit-chain recovery verification post-restore
- [ ] DR test report

Claim permitted:
> AEM-EVOLVE™ v2.0+ includes disaster-recovery evidence for restoring governed audit operations after infrastructure failure.

Non-claims:
- Not guaranteed continuity
- Not universal disaster recovery
- Not production-ready by itself

---

## Aggregator — PR 13

**Type:** assurance  
**Required output:**
- `PRODUCTION_READINESS_GATE=PASS` (if all PR 1–12 gates pass)
- `PRODUCTION_READINESS_GATE=FAIL_CLOSED` (if any gate is missing or failed)

The aggregator reads the output of each gate's assurance report in `assurance/evolve-multi-agent/v2_0/` and emits a single result. It must also report `defined_target_environment=<name>`.

**Claim permitted only if all gates pass:**
> AEM-EVOLVE™ v2.0 has passed the documented production-readiness evidence gate for the defined target environment.

**If any gate fails:**
> PRODUCTION_READINESS_GATE=FAIL_CLOSED. Missing or failed gates: [list].

Non-claims:
- Not universal production-ready
- Not production-ready outside defined target environment
- Not regulatory-approved
- Not externally certified

---

## Readiness report — PR 14

**Type:** docs  
**Artifact:** `docs/production/AEM_EVOLVE_V2_0_PRODUCTION_READINESS_REPORT.md`

If all gates pass:
> AEM-EVOLVE™ v2.0 has production-readiness evidence for the defined target environment covered by this report.

If not all gates pass:
> AEM-EVOLVE™ v2.0 remains in production-hardening mode with incomplete production-readiness gates.

Must include:
- [ ] Defined target environment
- [ ] Gate results PR 1–12 (PASS / FAIL / MISSING)
- [ ] Aggregator result (PR 13 output)
- [ ] Evidence links
- [ ] Residual risks
- [ ] Non-claims
- [ ] Date, version, tag
- [ ] Reviewer/owner

Non-claims (always present, regardless of gate result):
- Not universal production-ready
- Not regulatory-approved
- Not externally certified
- Not clinical or diagnostic
- Not financial advice
- Not cybersecurity certification

---

## Recommended execution sequence

```
PR 0  — This checklist (DONE)
PR 1  — OIDC provider enforcement
PR 2  — HSM/KMS signing
PR 3  — PostgreSQL persistence
PR 4  — Migration / recovery
PR 5  — Monitoring / alerting
PR 6  — Incident response
PR 7  — Security review
PR 8  — External reproduction
PR 9  — Deployment audit
PR 10 — SLO evidence
PR 11 — Rollback procedure
PR 12 — Disaster recovery
PR 13 — Gate aggregator
PR 14 — Readiness report
```

PRs 1–3 may proceed in parallel once the defined target environment is specified.  
PRs 4–12 require PRs 1–3 to have active infrastructure evidence.  
PR 13 is blocked until all PR 1–12 outputs exist.  
PR 14 is blocked until PR 13 runs.

---

## What this checklist does NOT do

```
This checklist does not claim that AEM-EVOLVE™ is production-ready.
This checklist does not grant regulatory approval.
This checklist does not replace external certification.
This checklist does not create a contractual SLA.
This checklist does not guarantee security.
This checklist does not transfer across environments without a new gate run.
```

---

## Relationship to v1.x hardening sequence

| Sequence | Purpose | Status |
|---|---|---|
| v1.1–v1.9 | Technical gap closures — what the code can do | COMPLETE |
| v2.0 PR 0 | Gate definition — what evidence is required | THIS DOCUMENT |
| v2.0 PR 1–12 | Evidence layers — what a real deployment must demonstrate | PENDING |
| v2.0 PR 13 | Gate aggregator — PASS only if all 12 layers present | PENDING |
| v2.0 PR 14 | Factual report — documents the gate result | PENDING |

The v1.x hardening sequence is a prerequisite for PR 1–12, not sufficient. Evidence from external systems, real operations, and third parties for a defined target environment is required before any production-readiness claim can be evaluated.
