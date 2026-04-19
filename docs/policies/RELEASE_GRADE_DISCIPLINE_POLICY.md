# Release Grade Discipline Policy

EthicBit / CEMU

## 1. Purpose

This policy ensures that every release, freeze, operational closure, and audit-grade claim is:

- reproducible,
- traceable,
- verifiable,
- blockable when a critical condition fails,
- and separated from experimentation.

## 2. Governing Principle

No official closure, readiness, freeze, or production claim can rely on critical pieces outside commit/tag, or on experimental branches mixed with the official perimeter.

## 3. Sovereign Branch Model

### 3.1 Protected principal branch

The sovereign release branch is `main`.

It must keep:

- branch protection enabled,
- required status checks,
- pull-request review before merge,
- restrictions on unsafe direct pushes according to repository policy.

### 3.2 Freeze curation branch

Examples:

- `codex/freeze-clean-YYYYMMDD`
- `strict-freeze-curation`

Used to:

- curate the final perimeter,
- clean the working tree,
- prepare strict freeze,
- validate claims before merge into `main`.

### 3.3 Agentic experimentation branch

Examples:

- `agentic-testing-lab`
- `codex/agentic-testing-YYYYMMDD`

Used for:

- test generation,
- fuzzing,
- adversarial testing,
- mutation testing,
- controlled exploration.

These branches cannot sustain official claims by themselves.

## 4. Critical Claims Rule

Official claims for:

- `READY`
- `READY_FOR_FREEZE`
- `READY_FOR_CONTROLLED_PRODUCTION`
- `ACTIVE_CANONICAL`
- `SIGNED_HYBRID`
- constitutional closure or audit-grade closure

must be backed by artifacts that are:

- versioned,
- committed,
- included in the corresponding tag,
- reproducible through official scripts.

## 5. Official Closure Perimeter

Any artifact sustaining closure claims must be inside the versioned perimeter.

Typical examples:

- final audit scripts,
- constitutional reporting scripts,
- constitutional amendment snapshot,
- final audit conclusions,
- taxonomy documents,
- manifests and public outputs used by the claim.

## 6. Required Controls Before Merge to `main`

### 6.1 Required status checks

The following checks are required before merge:

- `production-distributed-ready-final`
- `release-grade-discipline-gate`

### 6.2 Hermetic testing baseline

Tests must minimize external dependencies to reduce flakiness and improve reproducibility.

### 6.3 Mechanical ethics audit

The audit path must validate:

- `PASS`,
- `FAIL_CLOSED`,
- fallback,
- reject,
- and critical multisector rules.

### 6.4 Cryptographic and official-state verification

The verification path must validate:

- official state,
- artifact consistency,
- hybrid signature,
- canonical integrity.

### 6.5 Constitutional verification

The constitutional path must validate:

- document layer,
- policy layer,
- runtime layer,
- reporting layer.

## 7. Freeze Rule

### 7.1 Functional freeze

Accepted when:

- functional checks pass,
- claims are internally consistent,
- working tree may still contain local drift.

This state is valid for internal operational closure, not for strict final freeze.

### 7.2 Strict freeze

Accepted only when:

- working tree is clean,
- no relevant untracked files exist,
- no uncommitted local drift exists,
- commit/tag contains the full claim perimeter.

## 8. Progressive Exposure

Sensitive changes should use progressive exposure (for example canary patterns) before broad opening.

## 9. Chaos and Adversarial Testing

Chaos and adversarial experimentation should run in a separated stage or pipeline and not be mixed indiscriminately into the sovereign release path.

## 10. Role of Agentic Coding

Agentic coding is allowed as a testing accelerator, not as sovereign truth.

Allowed uses:

- test generation,
- edge-case discovery,
- coverage expansion,
- semantic fuzzing,
- controlled mutation proposals.

It does not replace:

- required status checks,
- human review,
- final audit,
- canonical verification.

## 11. Waiver and Exception Rule

Any exception to required controls must include:

- a waiver ID,
- approving authority,
- scope and expiration,
- compensating controls,
- link to evidence.

No waiver may redefine sovereign truth or bypass critical cryptographic verification permanently.

## 12. Final Approval Criteria

A release or official freeze is approved only if:

- required status checks pass,
- key testing remains reproducible and as hermetic as possible,
- final audit closes in `PASS`,
- critical claims are included in commit/tag,
- there is no contamination between official and experimental perimeters.

## 13. Golden Rule

Separate experimentation. Version official claims. Merge only with required controls. Strict freeze only with a clean tree.
