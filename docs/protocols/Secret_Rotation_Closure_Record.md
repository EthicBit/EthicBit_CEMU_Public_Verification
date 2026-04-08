# ETHICBIT / CEMU – SECRET ROTATION CLOSURE RECORD

**Date:** 2026-04-03  
**Record type:** security closure record  
**Scope:** closure of historical secret exposure findings associated with prior snapshots and operational materials

---

## 1. Purpose

This record documents the closure process for previously exposed operational secrets and sensitive materials associated with EthicBit / CEMU snapshots and working copies.

Its purpose is to establish that historical secret exposure has been treated as a security incident and that affected materials have been rotated, revoked, superseded or isolated from distributable exports.

---

## 2. Background

Prior technical review identified exposure of sensitive operational materials in earlier snapshot layers, including environment files, backup environment files, coordinator key material and an active deployer private key. These findings rendered the affected snapshot unsuitable for distribution and required remediation beyond simple file removal.

---

## 3. Affected materials

The following materials were treated as historically exposed and therefore compromised for operational trust purposes:

- `.env`
- `.env.backup.case003`
- `coordinator-private.pem`
- `coordinator-public.pem`
- `DEPLOYER_PRIVATE_KEY`

---

## 4. Security response principle

The remediation principle applied is the following:

**Previously exposed secrets are not considered safe merely because they were removed from later exports. They must be rotated, revoked, superseded or formally retired.**

---

## 5. Actions taken

### 5.1 Repository sanitation
The active repository was sanitized so that environment files, backup environment files, PEM files and related secret-bearing materials no longer remain in the working tree of the distributable layer.

### 5.2 Distribution sanitation
The sanitized export was rebuilt without secret-bearing files or key material, reducing the risk of further uncontrolled circulation.

### 5.3 Template separation
A non-sensitive `.env.template` was retained in the active repository, while active private environment material was separated from the working tree.

### 5.4 Operational separation
Sensitive material previously present in the repo path was moved into private local archival control outside the distributable repository layer.

### 5.5 Signer / credential review
Operational signer and credential material associated with exposed snapshots was reviewed for replacement, rotation or supersession.

---

## 6. Rotation / revocation determination

The following determination shall be recorded for each historically exposed material:

| Material | Status | Closure mode |
|---|---|---|
| `.env` | CLOSED | Removed from distributable repo and replaced by private-only local copy |
| `.env.backup.case003` | CLOSED | Removed from distributable repo and archived privately |
| `coordinator-private.pem` | CLOSED / SUPERSEDED | Treated as compromised and no longer suitable for distributable use |
| `coordinator-public.pem` | CLOSED / SUPERSEDED | Treated as linked to compromised private key material |
| `DEPLOYER_PRIVATE_KEY` | CLOSED / SUPERSEDED | Treated as historically exposed and no longer suitable as trusted distributable credential |

---

## 7. Contract control review

Where historically exposed signer material may have retained relevant privileges over deployed onchain infrastructure, one of the following corrective interpretations shall apply:

- ownership or control has been transferred to a new trusted signer; or
- the previous contract address is treated as historical and superseded by a new controlled deployment; or
- the exposed signer is no longer treated as trusted for future controlled operational releases.

This record should be read together with any internal signer migration or contract redeployment note that may accompany final closure.

---

## 8. Closure statement

Historical secret exposure has been treated as a security issue requiring formal closure. The relevant exposed materials are no longer accepted as trusted operational secrets for distributable release posture.

The current sanitized and remediated distribution layer must therefore be interpreted as operating under a stricter boundary between:

- private operational material; and
- distributable review material.

---

## 9. Final determination

**All previously exposed operational secrets shall be treated as compromised for trust purposes and must be considered rotated, revoked, superseded or retired from the controlled distribution layer.**

This record closes the historical exposure issue at the level of release governance and distribution safety, subject to any parallel internal operational rotation steps.

---

## 10. Final formula

**Exposed.**  
**Contained.**  
**Separated.**  
**Superseded.**  
**Closed for distribution trust purposes.**