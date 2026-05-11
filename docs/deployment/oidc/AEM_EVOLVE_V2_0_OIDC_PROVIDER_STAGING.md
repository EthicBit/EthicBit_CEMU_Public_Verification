# AEM-EVOLVE™ v2.0 — OIDC Provider for Staging Controlled Cloud

**Gate:** PR1 — Production OIDC Provider Enforcement
**Target environment:** `staging_controlled_cloud`
**Purpose:** Live OIDC evidence collection
**Production-ready claimed:** false
**Regulatory approval claimed:** false
**External certification claimed:** false

---

## 1. Purpose

This document defines the OIDC provider setup required to collect live evidence for AEM-EVOLVE™ v2.0 PR1.

This setup is intended for `staging_controlled_cloud`.

It does not claim production readiness.

---

## 2. Recommended Provider

Initial provider: Keycloak

Acceptable alternatives:

- Auth0
- Okta
- Azure AD
- Google Identity
- other standards-compliant OIDC provider

---

## 3. Required Environment Variables

- OIDC_ISSUER=https://<oidc-provider>/realms/aem-evolve
- OIDC_JWKS_URI=https://<oidc-provider>/realms/aem-evolve/protocol/openid-connect/certs
- OIDC_AUDIENCE=aem-evolve

---

## 4. Required Evidence

The PR1 verifier must validate:

- OIDC_ISSUER configured
- OIDC_JWKS_URI reachable
- OIDC_AUDIENCE configured
- issuer validation PASS
- JWKS validation PASS
- audience validation PASS
- token expiry enforcement PASS
- invalid token rejection PASS
- missing token rejection PASS
- HITL approver bound to verified OIDC identity

---

## 5. Claim Boundary

This OIDC setup supports live evidence collection for the v2.0 readiness gate.

It does not claim:

- production readiness
- enterprise IAM completeness
- regulatory approval
- external certification
- universal identity security

---

## 6. Gate Command

After the OIDC provider is configured, run:

```bash
python3 demos/aem-evolve-multi-agent-api/tools/production_readiness/verify_oidc_provider.py
```

Expected result only after real OIDC configuration:

- PRODUCTION_OIDC_PROVIDER_CHECK=PASS

Until live OIDC variables are configured, the expected result remains:

- PRODUCTION_OIDC_PROVIDER_CHECK=FAIL_EXPECTED
