# Hermetic Build + SLSA L4 Evolution Roadmap (2026-04-22)

## Purpose

Define the execution path from the current canonical equivalence model to stronger hermetic and corroborated assurance posture without breaking active fail-closed governance.

## Baseline (current)

- Canonical assurance is enforced through `scripts/verify_closure_integrity.sh`.
- `in-toto`, `SLSA`, and `sigstore` policy artifacts are required and validated in fail-closed mode.
- Canonical attestation normalization runs in strict mode before closure acceptance.

## Phase 1 kickoff update (2026-04-23)

- Strict tag lane (`v*`) now enforces hermetic posture materialization before signing and attestation.
- `ETHICBIT_HERMETIC_BASE_IMAGE_REF` is pinned with `@sha256` and validated in strict mode.
- Docker binary discovery hardening was added to avoid silent runner-path drift.
- JavaScript actions are forced to run on Node 24 (`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true`).
- Validation evidence: successful strict runs `24810631736` and `24813129514`.

## Stream A: Real hermetic builds

### A1. Runner hardening

- Run release-grade workflows inside pinned container images (`image@sha256:*`).
- Pin toolchain versions (`python`, `node`, `forge`, `openssl`) in workflow and image layer.
- Record immutable toolchain manifest per run.

### A2. Dependency closure

- Enforce lockfile-only installs (`npm ci`, pinned Python lock strategy).
- Block dependency resolution without lock updates.
- Archive dependency bill + hash digest as CI artifact.

### A3. Network control

- Add no-network build stage for reproducibility checks.
- Keep separate attest-only stage for required external services.
- Fail if hermetic stage reaches external network unexpectedly.

## Stream B: Corroborated provenance

### B1. Dual provenance corroboration

- Keep primary GitHub provenance attestation.
- Add corroboration source (second verifier or transparency corroboration).
- Emit a `corroborated_provenance.json` summary artifact.

### B2. Gate integration

- Extend closure gate to require corroboration on release/freeze tags.
- Keep branch-level compatibility mode for non-release development runs.

## Stream C: SLSA Build Track L4 migration readiness

### C1. Readiness mapping

- Map current controls to official Build Track L4 criteria.
- Track gaps in a machine-readable matrix (`status`, `evidence`, `owner`, `deadline`).

### C2. Incremental rollout

- Pilot Build Track L4 requirements on `audit-freeze-*` tags.
- Promote to `v*` release tags after two consecutive green cycles.
- Update public claims only after canonical evidence and addendum update.

## Stream D: Native hermetic toolchains (Nix/Bazel)

### D1. Feasibility track

- Evaluate Nix and Bazel against current build graph (`node`, `python`, `solidity`).
- Publish a compatibility matrix with adoption risk and operational cost.
- Select one pilot path for deterministic lock + no-network execution.

### D2. Controlled pilot

- Run pilot in parallel CI lane (non-blocking) for two cycles.
- Compare artifact hashes and runtime against current canonical lane.
- Promote to blocking only after parity and governance review.

## Governance rules for all streams

- Do not weaken fail-closed checks already active in closure scripts.
- Keep claims scope-bounded (US/EU/UK/CO and declared real targets).
- Treat historical artifacts as archival unless revalidated under active chain.

## Exit criteria

The roadmap is considered complete when:

1. release-grade runs are hermetic and reproducible with pinned dependencies,
2. provenance has corroborated verification in the closure path,
3. Build Track L4 native requirements are met for release/freeze tags,
4. addendum and mixed-audience docs are updated with evidence-linked claims.
