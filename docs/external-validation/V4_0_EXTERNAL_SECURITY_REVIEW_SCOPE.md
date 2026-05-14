# v4.0 External Security Review Scope

**Criterion:** 2 — external_security_review
**Status:** PENDING_EXTERNAL
**Controlled assessment:** CONTROLLED_ASSESSMENT_PASS_INTERNAL_CONTROLS (2026-05-14)
**Artifact:** `assurance/v4_0/evidence/V4_0_02_SECURITY_REVIEW_ARTIFACT.json`
**Constitutional dependency:** EthicBit / CEMU v3.7.0+

---

## What this criterion requires

An independent security reviewer — with no EthicBit affiliation — reviews the repository security posture, governance security controls, and claim boundaries. Internal assessment does NOT satisfy this criterion.

---

## What was already verified internally

| Check | Result |
|---|---|
| bandit HIGH findings (API source) | 0 |
| bandit MEDIUM findings (API source) | 11 (all reviewed — false positives) |
| pip-audit CVEs (API production deps) | 0 |
| pip-audit CVEs (global tooling env) | 15 (all in tooling, not API runtime) |
| Governance controls documented | 7/7 |
| OWASP API Top 10 coverage | documented |
| Internal gate checks passed | 8/10 (C09/C10 require external reviewer) |

### Tooling CVEs (non-API scope — require external triage)

| Package | CVEs | Fix |
|---|---|---|
| gitpython 3.1.46 | 4 CVEs | 3.1.50 |
| pip 24.0 | 4 CVEs | 26.1 |
| setuptools 65.5.0 | 3 CVEs | 78.1.1 |
| urllib3 2.6.3 | 2 CVEs | 2.7.0 |

### Governance controls present (7/7)

1. HITL Identity Enforcement (HMAC + OIDC)
2. KMS/HSM Signing (ProductionKmsProvider)
3. Audit Chain Integrity (SHA-256 hash-linked)
4. Replay Mitigation (hitl_used_tokens)
5. RBAC Access Control (X-API-Key fail-closed)
6. Input Validation (Pydantic field validators)
7. Monitoring and Alerting (7 Prometheus counters)

### OWASP API Top 10 gaps noted internally

- API4: rate limiting not present in demo — production must add
- API7: SQLite demo only — production requires PostgreSQL + KMS + OIDC

---

## Scope for external reviewer

The external reviewer should cover:

1. **AEM v1.1 artifact verification mechanisms** — review SHA-256 chain integrity and fail-closed behavior
2. **Fast Path enforcement logic** — review snapshot security and bypass resistance
3. **Signing key management** — review key lifecycle, rotation policy, and custody model
4. **AI-ME gate implementation security** — review gate inputs, outputs, and manipulation resistance
5. **Claim boundary enforcement** — review CBE log and overclaim detection
6. **API and endpoint security** — review authentication, authorization, input validation
7. **Threat model validation** — review `demos/aem-evolve-multi-agent-api/docs/THREAT_MODEL.md`
8. **Tooling CVE triage** — confirm gitpython/urllib3 are tooling-only, not API runtime
9. **Dependency upgrade path** — assess pip/setuptools hygiene recommendations
10. **Static analysis medium findings** — review B608/B306/B310 dispositions

---

## Key artifacts for reviewer

```
demos/aem-evolve-multi-agent-api/docs/SECURITY_REVIEW.md
demos/aem-evolve-multi-agent-api/docs/THREAT_MODEL.md
demos/aem-evolve-multi-agent-api/tools/security/dependency_scan_2026_05.json
demos/aem-evolve-multi-agent-api/tools/security/static_analysis_2026_05.json
assurance/v4_0/evidence/V4_0_02_SECURITY_REVIEW_ARTIFACT.json
```

---

## Required output

- Reviewer identity / organization (no EthicBit affiliation)
- Review date
- Scope covered
- Findings per scope area (PASS / FAIL / PARTIAL / N/A)
- CVE triage decisions
- Recommendations
- Signature or attestation

---

## Non-claim

Internal assessment found 0 HIGH bandit findings and 0 CVEs in API production dependencies. This does not constitute an external security review. External review by an independent party with no EthicBit affiliation and including penetration testing has not been conducted. `AEM_SECURITY_REVIEWER` is not set.
