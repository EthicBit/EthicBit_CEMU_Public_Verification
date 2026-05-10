"""Production OIDC provider configuration — v2.0 PR 1."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProductionOidcConfig:
    issuer: str
    jwks_uri: str
    audience: str
    jwks_ttl_seconds: int = 300


def load_oidc_config() -> ProductionOidcConfig | None:
    """Return config from env vars, or None if OIDC_ISSUER is not set."""
    issuer = os.getenv("OIDC_ISSUER", "").strip()
    if not issuer:
        return None
    jwks_uri = os.getenv("OIDC_JWKS_URI", "").strip()
    if not jwks_uri:
        jwks_uri = issuer.rstrip("/") + "/.well-known/jwks.json"
    audience = os.getenv("OIDC_AUDIENCE", "aem-evolve").strip()
    ttl = int(os.getenv("OIDC_JWKS_TTL_SECONDS", "300"))
    return ProductionOidcConfig(
        issuer=issuer,
        jwks_uri=jwks_uri,
        audience=audience,
        jwks_ttl_seconds=ttl,
    )
