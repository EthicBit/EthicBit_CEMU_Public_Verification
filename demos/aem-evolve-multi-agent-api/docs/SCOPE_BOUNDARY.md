# AEM-EVOLVE Multi-Agent Governance API v0.3.1-demo Scope Boundary

## Status

`TECHNICAL_DEMONSTRATION_PACKAGE`

This package is a local endpoint-level technical demonstration of AEM-EVOLVE-style governance for multi-agent workflow changes.

## Permitted Claim

AEM-EVOLVE Multi-Agent Governance API v0.3.1-demo provides an endpoint-level technical demonstration of Evolution Events, scope-limited Evolution Receipts, SQLite audit persistence, and Human-in-the-Loop approval for multi-agent workflow changes.

## Scope

The package demonstrates:

- local FastAPI endpoints;
- LangGraph workflow state transitions;
- canonical-hashed Evolution Events;
- scope-limited Evolution Receipts;
- SQLite checkpoint and audit persistence;
- Human-in-the-Loop approval for `SCOPE_LIMITED` changes;
- fail-closed routing for high-materiality changes;
- endpoint smoke verification;
- simulated tamper checklist.

## Non-Claims

This package does not claim:

- production readiness;
- independent reproduction;
- cryptographically signed receipts;
- Ethereum-mainnet anchoring for this demo package;
- regulatory approval;
- clinical or diagnostic use;
- external certification;
- production authentication or authorization;
- tamper-proof audit trail;
- production-grade database storage.

SQLite is demonstration storage only.

## Local-Only Boundary

The demo binds to `127.0.0.1` by default and is intended for local technical inspection only. It must not be exposed as a public service without separate authentication, authorization, threat modeling, operational hardening, and security review.

## Relationship to AEM-EVOLVE

This package does not replace the AEM-EVOLVE v0.3 technical demonstration release. It is an additional local API demonstration showing how AEM-EVOLVE-style governance can apply to multi-agent workflow changes.
