# AEM-EVOLVE™ Incident Response Runbook

**Version:** 2.0 | **Gate:** INCIDENT_RESPONSE_CHECK | **PR:** 6  
**Owner:** EthicBit Security & Governance Team  
**Review cycle:** Quarterly | **Last reviewed:** 2026-05-10

---

## Non-claims

- This runbook is a template. Contact details must be populated before production deployment.
- Drill evidence requires execution against a live environment — local/demo drill artifacts are configuration evidence only.
- This document does not constitute regulatory approval.

---

## 1. Severity Classification

| Severity | Label | Definition | Response SLA |
|----------|-------|------------|--------------|
| **P1** | Critical | Governance gate down or bypassed; data integrity at risk | 15 min |
| **P2** | High | Degraded governance path; redundant path active | 1 hour |
| **P3** | Medium | Non-critical component degraded; full governance enforced | 4 hours |

---

## 2. Escalation Matrix

| Role | Responsibility | Notification |
|------|---------------|--------------|
| **On-Call Engineer** | First responder; triage and initial containment | PagerDuty / #aem-alerts Slack |
| **Governance Lead** | HITL and audit-chain incidents | governance@your-domain.example.com |
| **Security Lead** | Signing, KMS, OIDC incidents | security@your-domain.example.com |
| **Database Admin** | PostgreSQL and audit storage incidents | ops@your-domain.example.com |
| **Engineering Manager** | P1 escalation; external communication | Direct page |

---

## 3. Incident Response Checklist

1. **Acknowledge** the alert in Alertmanager / PagerDuty.
2. **Assess** severity using the classification table above.
3. **Contain** — see incident-specific runbooks below.
4. **Notify** escalation contacts per severity level.
5. **Resolve** — apply recovery procedure; verify gate returns PASS.
6. **Document** — write post-mortem within 24 hours of resolution.
7. **Sign off** — Governance Lead approves post-mortem.

---

## 4. Incident-Specific Recovery Procedures

### INC-01: HITL Approval Failure (`AEM_HITLApprovalFailed`)

**Alert rule:** `AEM_HITLApprovalFailed`  
**Counter:** `aem_hitl_approval_failed_total`  
**Severity:** P1 (Critical)  
**Gate:** PR1_OIDC / PR2_KMS

**Symptoms:** `POST /approve` returns 403; counter `hitl_approval_failed` increments.

**Recovery steps:**
1. Check OIDC provider connectivity: `curl $OIDC_ISSUER/.well-known/openid-configuration`
2. Verify HITL token expiry — tokens expire per `HITL_TOKEN_TTL_SECONDS`.
3. If OIDC provider is down, escalate to **Security Lead** (see INC-07).
4. Re-issue token: `python tools/hitl/hitl_token_generator.py`
5. Verify gate: `python tools/production_readiness/verify_oidc_provider.py`

**Reference:** `docs/OIDC_PROVIDER_ENFORCEMENT.md`

---

### INC-02: Signature Verification Failure (`AEM_SignatureVerificationFailed`)

**Alert rule:** `AEM_SignatureVerificationFailed`  
**Counter:** `aem_signature_verification_failed_total`  
**Severity:** P1 (Critical)  
**Gate:** PR2_KMS

**Symptoms:** `/receipt/{id}` or `/event/{id}` returns `signature_verified: false`.

**Recovery steps:**
1. Check if signing key was rotated without re-signing stored artifacts.
2. Verify KMS key accessibility: `python tools/production_readiness/verify_kms_signing.py`
3. If key was rotated: re-sign artifacts with new key; update `signing_key.pem`.
4. If artifact tampering suspected: preserve logs; escalate to **Security Lead**; invoke INC-04.

**Reference:** `docs/HITL_SIGNATURE_VERIFICATION.md`

---

### INC-03: Replay Attempt Detected (`AEM_ReplayAttemptDetected`)

**Alert rule:** `AEM_ReplayAttemptDetected`  
**Counter:** `aem_replay_attempt_detected_total`  
**Severity:** P2 (High)  
**Gate:** HITL

**Symptoms:** `POST /approve` returns 409; counter `replay_attempt_detected` increments.

**Recovery steps:**
1. Identify the approver and token from logs (`hitl_identity_verified` log event).
2. Determine if replay is accidental (approver double-submitted) or adversarial.
3. If adversarial: rotate HITL secret (`HITL_SECRET` env var); issue new tokens to legitimate approvers.
4. Document in post-mortem; assess if `hitl_used_tokens` table was tampered.

**Reference:** `docs/HITL_SIGNATURE_VERIFICATION.md`

---

### INC-04: Audit Chain Mismatch (`AEM_AuditChainMismatch`)

**Alert rule:** `AEM_AuditChainMismatch`  
**Counter:** `aem_audit_chain_mismatch_total`  
**Severity:** P1 (Critical)  
**Gate:** PR3_POSTGRES

**Symptoms:** `GET /chain/verify` returns `"status": "TAMPER_DETECTED"`.

**Recovery steps:**
1. **Do not delete or modify** any audit chain entries — preserve evidence.
2. Run `GET /chain/verify` and capture the full error list (seq, entry_id).
3. Cross-reference with PostgreSQL WAL logs for the affected time window.
4. Determine root cause: storage corruption vs. adversarial write.
5. Escalate to **Database Admin** and **Security Lead**.
6. If corruption: restore from last verified backup; re-run missing events from application logs.
7. If adversarial: treat as security incident; involve legal/compliance.

**Reference:** `docs/ARCHITECTURE.md`

---

### INC-05: Database Unavailable (`AEM_DatabaseUnavailable`)

**Alert rule:** `AEM_DatabaseUnavailable`  
**Counter:** `aem_database_unavailable_total`  
**Severity:** P1 (Critical)  
**Gate:** PR3_POSTGRES

**Symptoms:** API endpoints return 500; `_append_audit_chain` raises; counter increments.

**Recovery steps:**
1. Check PostgreSQL connectivity: `pg_isready -h $DB_HOST -p $DB_PORT`
2. Verify `AEM_DB_URL` env var is set and correct.
3. Check PostgreSQL logs for OOM, disk full, or connection exhaustion.
4. Restart PostgreSQL if safe: `systemctl restart postgresql`
5. Verify schema post-restart: `python tools/production_readiness/verify_postgres_persistence.py`
6. If disk full: expand volume; run `VACUUM FULL` if needed.

**Reference:** `db/postgres_production_gate.py`

---

### INC-06: KMS Signing Failure (`AEM_KMSSigningFailed`)

**Alert rule:** `AEM_KMSSigningFailed`  
**Counter:** `aem_kms_signing_failed_total`  
**Severity:** P1 (Critical)  
**Gate:** PR2_KMS

**Symptoms:** `POST /start` returns 500; `kms_signing_failed` counter increments.

**Recovery steps:**
1. Check KMS provider connectivity and key permissions:
   - AWS KMS: verify IAM role has `kms:Sign` permission on `AEM_KMS_KEY_ID`
   - GCP KMS: verify service account has `cloudkms.cryptoKeyVersions.useToSign`
   - Azure Key Vault: verify managed identity has `Sign` permission
   - PKCS#11: verify HSM connection and slot availability
2. Run `python tools/production_readiness/verify_kms_signing.py`
3. If key rotation caused failure: update `AEM_KMS_KEY_ID` and re-verify.
4. Fallback (temporary only): set `AEM_KMS_PROVIDER=""` to revert to file-based signing; document as P1 deviation.

**Reference:** `tools/signing/production_kms_provider.py`

---

### INC-07: OIDC Provider Outage (`AEM_OIDCProviderOutage`)

**Alert rule:** `AEM_OIDCProviderOutage`  
**Counter:** `aem_oidc_provider_outage_total`  
**Severity:** P1 (Critical)  
**Gate:** PR1_OIDC

**Symptoms:** `oidc_provider_outage` counter increments; HITL approvals requiring OIDC are blocked.

**Recovery steps:**
1. Verify OIDC provider status: `curl $OIDC_ISSUER/.well-known/openid-configuration`
2. Check JWKS TTL cache — provider may have returned stale JWKS.
3. If provider is down: contact IdP team; estimate RTO.
4. If extended outage (> 30 min P1 SLA): invoke fallback — use HMAC HITL path (demo path); document deviation.
5. When provider recovers: verify `python tools/production_readiness/verify_oidc_provider.py` returns PASS.
6. Clear JWKS cache: restart AEM-EVOLVE API process.

**Reference:** `docs/OIDC_PROVIDER_ENFORCEMENT.md`

---

## 5. Post-Incident Documentation Template

```
## Post-Mortem: [Incident Title]

**Date:** YYYY-MM-DD  
**Severity:** P1 / P2 / P3  
**Duration:** HH:MM  
**Alert(s) fired:** [alert names]  
**Affected gate(s):** [gate names]

### Timeline
| Time (UTC) | Event |
|------------|-------|

### Root Cause
[One paragraph]

### Recovery Actions Taken
[Numbered list]

### Lessons Learned
[Numbered list]

### Gate Verification Post-Recovery
[Paste verifier output]

### Sign-off
- Governance Lead: [name] — [date]
- Security Lead (if applicable): [name] — [date]
```

---

## 6. Drill Schedule

| Drill Type | Frequency | Scenario |
|------------|-----------|----------|
| Tabletop exercise | Quarterly | Rotate through INC-01 through INC-07 |
| Live failover drill | Semi-annually | INC-05 (DB) + INC-07 (OIDC) combined |
| Red team exercise | Annually | Adversarial replay + chain mismatch |

Drill scenarios: `tools/incident_response/drill_scenario.py`  
Drill evidence format: `tools/incident_response/drill_evidence_*.json`

---

## 7. Alert → Runbook Cross-Reference

| Prometheus Alert | Counter | Section |
|-----------------|---------|---------|
| `AEM_HITLApprovalFailed` | `aem_hitl_approval_failed_total` | INC-01 |
| `AEM_SignatureVerificationFailed` | `aem_signature_verification_failed_total` | INC-02 |
| `AEM_ReplayAttemptDetected` | `aem_replay_attempt_detected_total` | INC-03 |
| `AEM_AuditChainMismatch` | `aem_audit_chain_mismatch_total` | INC-04 |
| `AEM_DatabaseUnavailable` | `aem_database_unavailable_total` | INC-05 |
| `AEM_KMSSigningFailed` | `aem_kms_signing_failed_total` | INC-06 |
| `AEM_OIDCProviderOutage` | `aem_oidc_provider_outage_total` | INC-07 |
