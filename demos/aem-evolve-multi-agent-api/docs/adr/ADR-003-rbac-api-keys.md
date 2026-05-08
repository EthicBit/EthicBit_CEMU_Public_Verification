# ADR-003: RBAC via Static API Key Header

**Status:** Accepted  
**Date:** May 2026  
**Context:** AEM-EVOLVE Multi-Agent Governance API v0.3.1-demo

## Decision

Implement role-based access control (RBAC) using a static `X-API-Key` header mapped to three roles (`INITIATOR`, `APPROVER`, `OBSERVER`). Keys are loaded from `configs/auth_demo_keys.json` or the `AEM_DEMO_AUTH_KEYS_JSON` environment variable.

## Rationale

- **Reproducibility without external dependencies**: A reproducer running the 30-minute quickstart needs no OAuth server, no OIDC provider, no JWT library. Static keys from a JSON file are trivially inspectable and testable.
- **Role separation is the core governance property to demonstrate**: The critical claim is that INITIATOR cannot approve, APPROVER cannot initiate, and every approval is attributed to an authenticated key. Static keys demonstrate this property clearly.
- **Fail-closed**: `_require_role` raises `401` (missing/unknown key) or `403` (wrong role) — there is no default-allow path.
- **Approver identity is derived from the authenticated key**: `approver_id` in `human_decisions` is set from the key store, not from the request body, preventing impersonation via crafted payloads.
- **Env-var fallback**: `AEM_DEMO_AUTH_KEYS_JSON` allows CI environments to inject keys without committing a `configs/` file, supporting the GitHub Actions workflow.

## Trade-offs

- Static keys are not rotatable without restarting the server.
- No token expiry; a leaked key remains valid indefinitely.
- No multi-tenant isolation — all INITIATOR keys share the same role and the same audit namespace.
- `configs/auth_demo_keys.json` must not be committed with production keys; the file contains only demo values (`demo-initiator-key-001`, etc.).

## Migration Path

Replace `_load_key_store()` with a call to an external identity provider (e.g., OAuth2 Bearer token validation, API key management service). The `_require_role` interface remains stable — only the key-to-role lookup changes. The role constants (`INITIATOR`, `APPROVER`, `OBSERVER`) are retained.
