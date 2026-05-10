"""Production OIDC provider — JWKS-backed RS256 token verification — v2.0 PR 1."""
from __future__ import annotations

import threading
import time
from typing import Any

from security.oidc_config import ProductionOidcConfig, load_oidc_config


class ProductionOidcProvider:
    def __init__(self, config: ProductionOidcConfig) -> None:
        self._config = config
        self._jwks_cache: dict[str, Any] = {}
        self._jwks_fetched_at: float = 0.0
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    @classmethod
    def from_env(cls) -> "ProductionOidcProvider | None":
        config = load_oidc_config()
        if config is None:
            return None
        return cls(config)

    # ------------------------------------------------------------------
    @property
    def config(self) -> ProductionOidcConfig:
        return self._config

    # ------------------------------------------------------------------
    def fetch_jwks(self) -> dict[str, Any]:
        """Return JWKS dict, using a TTL cache to limit external calls."""
        with self._lock:
            age = time.monotonic() - self._jwks_fetched_at
            if self._jwks_cache and age < self._config.jwks_ttl_seconds:
                return self._jwks_cache
        # Fetch outside the lock — worst case two threads both fetch once.
        import httpx  # optional dep; already used elsewhere in the project
        resp = httpx.get(self._config.jwks_uri, timeout=10.0)
        resp.raise_for_status()
        jwks = resp.json()
        with self._lock:
            self._jwks_cache = jwks
            self._jwks_fetched_at = time.monotonic()
        return jwks

    # ------------------------------------------------------------------
    def _get_public_key(self, kid: str | None) -> Any:
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
        import base64, struct
        from cryptography.hazmat.primitives.asymmetric.rsa import (
            RSAPublicNumbers,
        )
        from cryptography.hazmat.backends import default_backend

        jwks = self.fetch_jwks()
        keys = jwks.get("keys", [])
        if not keys:
            raise ValueError("JWKS contains no keys")

        # If a kid is provided, match it; otherwise fall back to first RS256 key.
        candidates = [k for k in keys if k.get("kty") == "RSA"]
        if kid:
            candidates = [k for k in candidates if k.get("kid") == kid] or candidates
        if not candidates:
            raise ValueError(f"No RSA key found for kid={kid!r}")

        jwk = candidates[0]

        def _b64url_int(s: str) -> int:
            padded = s + "=" * (-len(s) % 4)
            data = base64.urlsafe_b64decode(padded)
            return int.from_bytes(data, "big")

        n = _b64url_int(jwk["n"])
        e = _b64url_int(jwk["e"])
        return RSAPublicNumbers(e, n).public_key(default_backend())

    # ------------------------------------------------------------------
    def verify_token(self, token: str) -> tuple[bool, str, dict]:
        """
        Verify a JWT against the external OIDC provider's JWKS.
        Returns (ok, reason, claims).
        """
        try:
            from jose import jwt as jose_jwt, exceptions as jose_exc
        except ImportError:
            return False, "python-jose not installed", {}

        try:
            # Decode header to get kid without verifying signature yet.
            unverified_header = jose_jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            alg = unverified_header.get("alg", "RS256")

            if alg not in ("RS256", "RS384", "RS512"):
                return False, f"unsupported_algorithm:{alg}", {}

            public_key = self._get_public_key(kid)

            claims = jose_jwt.decode(
                token,
                public_key,
                algorithms=[alg],
                audience=self._config.audience,
                issuer=self._config.issuer,
                options={"verify_exp": True, "verify_iat": True},
            )
            return True, "ok", claims

        except jose_exc.ExpiredSignatureError:
            return False, "token_expired", {}
        except jose_exc.JWTClaimsError as exc:
            return False, f"claims_error:{exc}", {}
        except jose_exc.JWTError as exc:
            return False, f"jwt_error:{exc}", {}
        except Exception as exc:
            return False, f"verification_error:{exc}", {}

    # ------------------------------------------------------------------
    def gate_check(self) -> dict[str, Any]:
        """Return a structured dict summarising the gate status for /health and assurance."""
        result: dict[str, Any] = {
            "gate": "PRODUCTION_OIDC_PROVIDER_CHECK",
            "issuer": self._config.issuer,
            "jwks_uri": self._config.jwks_uri,
            "audience": self._config.audience,
        }
        try:
            jwks = self.fetch_jwks()
            key_count = len(jwks.get("keys", []))
            result["jwks_reachable"] = True
            result["jwks_key_count"] = key_count
            result["status"] = "PASS" if key_count > 0 else "FAIL"
            result["reason"] = "ok" if key_count > 0 else "JWKS returned no keys"
        except Exception as exc:
            result["jwks_reachable"] = False
            result["jwks_key_count"] = 0
            result["status"] = "FAIL"
            result["reason"] = str(exc)
        return result
