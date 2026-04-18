# State Model: Sovereign Closure vs External Projection

## Purpose

This model separates three different truths so the repository does not collapse internal integrity into external live availability.

## Canonical State Layers

1. `internalClosureStatus`
- Scope: sovereign internal closure.
- Source: internal canonical integrity, production readiness, cryptography policy.
- Typical values:
  - `INTERNAL_CLOSED`
  - `INTERNAL_CLOSED_FROZEN`
  - `INTERNAL_GATE_BLOCKED`
  - `INTERNAL_CANONICAL_BLOCKED`
  - `INTERNAL_CRYPTO_BLOCKED`

2. `externalProjectionStatus`
- Scope: public live convergence against external anchors.
- Source: live verification outcome (Sepolia/Arweave/AO).
- Typical values:
  - `EXTERNAL_LIVE_CONVERGED`
  - `EXTERNAL_LIVE_FAIL`
  - `EXTERNAL_LIVE_UNKNOWN`

3. `officialOperationalStatus`
- Scope: single operational truth for production decisions.
- Source: policy resolver over internal + external + freeze + cryptography.
- Typical values:
  - `READY`
  - `FROZEN`
  - `DEGRADED`
  - `BLOCKED`

## Operational Rule

- Internal closure is necessary but not sufficient for external readiness.
- Live external convergence is mandatory for `officialOperationalStatus=READY`.
- Oracle updates stay fail-closed:
  - only when `officialOperationalStatus=READY`
  - and cryptography is `PASS`.

## Cryptography Separation

- `internalCryptographyStatus` represents sovereign internal cryptographic closure.
- `externalCryptographyStatus` represents market interoperability (hybrid signer/KMS path).
- Internal closure is computed from canonical + gate + internal cryptography.
- External signer failures no longer redefine internal closure by default.

## Operating Modes

From `assurance/sigstore/policy.json`, EthicBit supports:

1. `SOVEREIGN_INTERNAL` (default)
- Internal cryptography is required.
- External hybrid signatures are optional for projection.
- External signer failures do not block internal closure semantics.
- If `--require-signature` is passed, hybrid signatures become mandatory for that run.

2. `MARKET_INTEROP`
- Internal cryptography is required.
- External hybrid signatures are required.
- External signer failures can block official operational status.

## Where It Is Exposed

- `artifacts/history/swarm/official_operational_status.json`
  - `internalClosureStatus`
  - `externalProjectionStatus`
  - `officialOperationalStatus`
  - `internalCryptographyStatus`
  - `externalCryptographyStatus`
  - `policyBinding.operatingMode`

- `results/GATE_REPORT.json`
  - `verifiedState.internalClosureStatus`
  - `verifiedState.externalProjectionStatus`
  - `stateModel.*` (gate-derived + observed official state)

- `results/technical_verification.md`
  - human-readable view of the three layers.
