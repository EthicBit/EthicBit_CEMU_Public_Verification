# Lingo and Claim Dictionary — AEM-EVOLVE™ v1.1

**Document type:** Canonical claim-language controls
**Version:** v1.1.0
**Policy:** v1.1-claim-boundary-policy

This dictionary governs all claim language used in AEM-EVOLVE™ v1.1 documentation, receipts, reports, and communications.

---

## Allowed Terms

These terms may be used freely as they accurately describe what is implemented and evidenced:

| Term | Definition |
|---|---|
| `public controlled-environment release` | Released for use in explicitly declared controlled environments |
| `regulatory mapping evidence` | Technical mapping of capabilities to framework requirements — not approval |
| `timestamped integrity reference` | On-chain or anchor-verified hash reference proving a timestamp |
| `demo HITL signature verification` | Human-in-the-loop decision verification at demo assurance level |
| `open independent reproduction pathway` | A publicly available guide enabling third parties to attempt reproduction |
| `governance-effectiveness metrics` | Metrics measuring governance boundary preservation in controlled demonstrations |
| `declared-scope assurance` | Assurance claims bounded to explicitly declared jurisdictions and targets |
| `fail-closed policy` | Policy that forces a denied outcome on boundary violations |
| `multi-anchor verification` | Verification across more than one public anchor point |
| `canonical claim-language controls` | Dictionary of allowed / restricted / forbidden claim terms |
| `controlled demonstration` | A demonstration conducted within explicitly declared scope and constraints |

---

## Restricted Terms

These terms require explicit qualification and evidence before use. They must not appear as bare claims:

| Term | Required qualification |
|---|---|
| `production-ready` | Must specify "for which environment" and "under which conditions"; forbidden as universal claim |
| `certified` | Must name the certifying body and certification standard |
| `compliance` | Must specify "compliance with what, under what jurisdiction, as assessed by whom" |
| `regulatory approved` | Must name the regulator and the approval decision |
| `independently reproduced` | Must cite the external reproduction report |
| `enterprise-grade` | Must specify the enterprise standard being met |
| `audited` | Must name the auditor and the scope of the audit |

---

## Forbidden Terms (unless separately evidenced)

These terms must not appear as claims without the named separate evidence artifact:

| Term | Why forbidden | What evidence would be required |
|---|---|---|
| `regulator-approved` | No regulator has approved AEM-EVOLVE™ | Named regulator decision letter |
| `legal compliance` | Not a legal compliance product | Legal opinion from admitted counsel |
| `conformity assessed` | No conformity assessment conducted | Notified body assessment report |
| `externally certified` | No external certification body engaged | Named certification body certificate |
| `HSM-backed` | No HSM key custody implemented | HSM vendor attestation |
| `tamper-proof` | No tamper-proof claim is supportable | Independent security audit |
| `cybersecurity certified` | No cybersecurity certification conducted | Named cybersecurity certification |
| `banking approved` | No banking regulatory engagement | Named banking regulator approval |
| `financial advice` | Not a financial services product | Regulated financial advisor sign-off |
| `clinical or diagnostic` | Not a medical device or diagnostic | Medical device regulatory clearance |

---

## Non-Claims (transversal v1.1)

The following non-claims apply to all AEM-EVOLVE™ v1.1 artifacts, receipts, and reports:

```
Not regulatory-approved.
Not externally certified.
Not legal compliance.
Not conformity assessed.
Not production-ready universal.
Not independently reproduced unless external reports exist.
Not cybersecurity certified.
Not financial advice.
Not clinical or diagnostic.
Not tamper-proof.
Not HSM-backed unless separately implemented.
```

---

## Usage rules

1. Before writing a new claim, check this dictionary.
2. If the term is in **Allowed** — use it freely with the defined meaning.
3. If the term is in **Restricted** — add the required qualification or do not use it.
4. If the term is in **Forbidden** — do not use it without the named separate evidence artifact.
5. When in doubt, default to the non-claim form: "Not X."
6. All v1.1 receipts, reports, and official status artifacts must include the transversal non-claims block.
