"""
ProductionKmsProvider — v2.0 PR 2 production signing via KMS/HSM.

Routes to the appropriate backend based on AEM_KMS_PROVIDER:
  aws_kms       → KmsSigningProvider (boto3)
  gcp_kms       → GcpKmsSigningProvider (google-cloud-kms)
  azure_key_vault → AzureKeyVaultSigningProvider (azure-keyvault-keys)
  pkcs11        → Pkcs11SigningProvider (pkcs11)

from_env() returns None when AEM_KMS_PROVIDER is not set.
gate_check() returns a structured dict for /health and assurance.

Non-claims:
  Not production-tested against live KMS without real credentials.
  Not FIPS-validated unless the underlying HSM is separately certified.
  Not HSM-certified unless the hardware is separately evidenced.
  Not production-ready by itself — one gate of 12.
"""
from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .signing_provider import SigningProvider

_PROVIDER_ENV = "AEM_KMS_PROVIDER"
_KEY_ID_ENV = "AEM_KMS_KEY_ID"
_REGION_ENV = "AEM_KMS_REGION"
_PROJECT_ENV = "AEM_KMS_PROJECT"
_VAULT_URL_ENV = "AEM_KMS_VAULT_URL"
_ALGORITHM_ENV = "AEM_KMS_ALGORITHM"

_SUPPORTED_PROVIDERS = ("aws_kms", "gcp_kms", "azure_key_vault", "pkcs11")


@dataclass(frozen=True)
class ProductionKmsConfig:
    provider: str
    key_id: str
    region: str | None = None
    project: str | None = None
    vault_url: str | None = None
    algorithm: str = "ECDSA_SHA_256"
    non_exportable: bool = True   # posture — always True for KMS/HSM keys


def load_kms_config() -> ProductionKmsConfig | None:
    """Return config from env vars, or None when AEM_KMS_PROVIDER not set."""
    provider = os.getenv(_PROVIDER_ENV, "").strip().lower()
    if not provider:
        return None
    key_id = os.getenv(_KEY_ID_ENV, "").strip()
    return ProductionKmsConfig(
        provider=provider,
        key_id=key_id,
        region=os.getenv(_REGION_ENV, "").strip() or None,
        project=os.getenv(_PROJECT_ENV, "").strip() or None,
        vault_url=os.getenv(_VAULT_URL_ENV, "").strip() or None,
        algorithm=os.getenv(_ALGORITHM_ENV, "ECDSA_SHA_256").strip(),
    )


class _AuditLog:
    """Thread-safe in-process signing audit log — satisfies key usage audit requirement."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: list[dict[str, Any]] = []
        self._sign_count = 0
        self._verify_count = 0

    def record_sign(self, key_id: str, algorithm: str) -> None:
        with self._lock:
            self._sign_count += 1
            self._entries.append({
                "op": "sign",
                "key_id": key_id,
                "algorithm": algorithm,
                "ts": datetime.now(timezone.utc).isoformat(),
            })

    def record_verify(self, key_id: str, algorithm: str, ok: bool) -> None:
        with self._lock:
            self._verify_count += 1
            self._entries.append({
                "op": "verify",
                "key_id": key_id,
                "algorithm": algorithm,
                "result": "ok" if ok else "fail",
                "ts": datetime.now(timezone.utc).isoformat(),
            })

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "sign_count": self._sign_count,
                "verify_count": self._verify_count,
                "entry_count": len(self._entries),
                "last_entries": self._entries[-5:],
            }


class ProductionKmsProvider(SigningProvider):
    """
    Production signing provider backed by a KMS/HSM.

    Wraps the appropriate backend for the configured AEM_KMS_PROVIDER.
    Delegates sign/verify/public_key_pem to the backend; adds gate_check()
    and a key-usage audit log.
    """

    def __init__(self, config: ProductionKmsConfig, backend: SigningProvider) -> None:
        self._config = config
        self._backend = backend
        self._audit = _AuditLog()

    # ------------------------------------------------------------------
    @classmethod
    def from_env(cls) -> "ProductionKmsProvider | None":
        """Return a provider from env vars, or None when AEM_KMS_PROVIDER not set."""
        config = load_kms_config()
        if config is None:
            return None
        try:
            backend = _load_backend(config)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load KMS backend for provider={config.provider!r}: {exc}"
            ) from exc
        return cls(config, backend)

    # ------------------------------------------------------------------
    @property
    def config(self) -> ProductionKmsConfig:
        return self._config

    @property
    def audit_log(self) -> _AuditLog:
        return self._audit

    # ------------------------------------------------------------------
    def sign(self, message: bytes) -> bytes:
        sig = self._backend.sign(message)
        self._audit.record_sign(self._config.key_id, self._config.algorithm)
        return sig

    def verify(self, message: bytes, signature: bytes) -> bool:
        ok = self._backend.verify(message, signature)
        self._audit.record_verify(self._config.key_id, self._config.algorithm, ok)
        return ok

    def public_key_pem(self) -> bytes:
        return self._backend.public_key_pem()

    def algorithm(self) -> str:
        return f"KMS/{self._config.provider}/{self._config.algorithm}"

    # ------------------------------------------------------------------
    def gate_check(self) -> dict[str, Any]:
        """Structured gate status for /health and assurance reports."""
        result: dict[str, Any] = {
            "gate": "HSM_KMS_SIGNING_CHECK",
            "provider": self._config.provider,
            "key_id": self._config.key_id or "(not set)",
            "algorithm": self._config.algorithm,
            "non_exportable_posture": self._config.non_exportable,
            "audit_log_active": True,
        }
        # Check: key_id present
        if not self._config.key_id:
            result["status"] = "FAIL"
            result["reason"] = f"{_KEY_ID_ENV} not configured"
            return result

        # Check: public key reachable (proves key accessible)
        try:
            pub_pem = self._backend.public_key_pem()
            result["public_key_reachable"] = True
            result["public_key_algorithm"] = self._config.algorithm
        except Exception as exc:
            result["public_key_reachable"] = False
            result["status"] = "FAIL"
            result["reason"] = f"public_key_pem failed: {exc}"
            return result

        # Check: round-trip sign/verify
        try:
            test_msg = b"aem-evolve-kms-gate-check"
            sig = self._backend.sign(test_msg)
            ok = self._backend.verify(test_msg, sig)
            result["sign_verify_roundtrip"] = ok
            if not ok:
                result["status"] = "FAIL"
                result["reason"] = "sign/verify round-trip failed"
                return result
        except Exception as exc:
            result["sign_verify_roundtrip"] = False
            result["status"] = "FAIL"
            result["reason"] = f"sign/verify error: {exc}"
            return result

        result["status"] = "PASS"
        result["reason"] = "ok"
        return result


# ------------------------------------------------------------------
def _load_backend(config: ProductionKmsConfig) -> SigningProvider:
    """Instantiate the appropriate backend for the given provider config."""
    import sys
    from pathlib import Path
    _tools_dir = str(Path(__file__).resolve().parent.parent)
    if _tools_dir not in sys.path:
        sys.path.insert(0, _tools_dir)

    p = config.provider
    if p == "aws_kms":
        from signing.kms_signing_provider import KmsSigningProvider
        return KmsSigningProvider(
            key_id=config.key_id or None,
            region=config.region or None,
            signing_algorithm=config.algorithm,
        )
    elif p == "pkcs11":
        from signing.pkcs11_signing_provider import Pkcs11SigningProvider
        return Pkcs11SigningProvider(key_label=config.key_id or None)
    elif p == "gcp_kms":
        return _GcpKmsSigningProvider(config)
    elif p == "azure_key_vault":
        return _AzureKeyVaultSigningProvider(config)
    else:
        raise ValueError(
            f"Unsupported AEM_KMS_PROVIDER={config.provider!r}. "
            f"Supported: {', '.join(_SUPPORTED_PROVIDERS)}"
        )


# ------------------------------------------------------------------
class _GcpKmsSigningProvider(SigningProvider):
    """GCP Cloud KMS signing via google-cloud-kms."""

    def __init__(self, config: ProductionKmsConfig) -> None:
        try:
            from google.cloud import kms as _kms  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "google-cloud-kms is required for gcp_kms provider. "
                "Install with: pip install google-cloud-kms  "
                "Then set AEM_KMS_KEY_ID to a full KMS resource name."
            ) from exc
        self._config = config
        self._client = _kms.KeyManagementServiceClient()

    def sign(self, message: bytes) -> bytes:
        import hashlib
        from google.cloud import kms as _kms  # type: ignore[import]
        digest_bytes = hashlib.sha256(message).digest()
        digest = _kms.Digest(sha256=digest_bytes)
        response = self._client.asymmetric_sign(
            request={"name": self._config.key_id, "digest": digest}
        )
        return response.signature

    def verify(self, message: bytes, signature: bytes) -> bool:
        try:
            pub = self.public_key_pem()
            from cryptography.hazmat.primitives.serialization import load_pem_public_key
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import ec
            key = load_pem_public_key(pub)
            key.verify(signature, message, ec.ECDSA(hashes.SHA256()))  # type: ignore[union-attr]
            return True
        except Exception:
            return False

    def public_key_pem(self) -> bytes:
        response = self._client.get_public_key(request={"name": self._config.key_id})
        return response.pem.encode()

    def algorithm(self) -> str:
        return f"GCP_KMS/{self._config.algorithm}"


class _AzureKeyVaultSigningProvider(SigningProvider):
    """Azure Key Vault signing via azure-keyvault-keys."""

    def __init__(self, config: ProductionKmsConfig) -> None:
        try:
            from azure.keyvault.keys.crypto import CryptographyClient, SignatureAlgorithm  # type: ignore[import]
            from azure.identity import DefaultAzureCredential  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "azure-keyvault-keys and azure-identity are required for azure_key_vault provider. "
                "Install with: pip install azure-keyvault-keys azure-identity  "
                "Then set AEM_KMS_KEY_ID to the Key Vault key identifier URL and "
                "AEM_KMS_VAULT_URL to the vault URL."
            ) from exc
        self._config = config
        credential = DefaultAzureCredential()
        self._crypto_client = CryptographyClient(config.key_id, credential=credential)

    def sign(self, message: bytes) -> bytes:
        import hashlib
        from azure.keyvault.keys.crypto import SignatureAlgorithm  # type: ignore[import]
        digest = hashlib.sha256(message).digest()
        result = self._crypto_client.sign(SignatureAlgorithm.es256, digest)
        return result.signature

    def verify(self, message: bytes, signature: bytes) -> bool:
        import hashlib
        from azure.keyvault.keys.crypto import SignatureAlgorithm  # type: ignore[import]
        digest = hashlib.sha256(message).digest()
        result = self._crypto_client.verify(SignatureAlgorithm.es256, digest, signature)
        return result.is_valid

    def public_key_pem(self) -> bytes:
        from azure.keyvault.keys import KeyClient  # type: ignore[import]
        from azure.identity import DefaultAzureCredential  # type: ignore[import]
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicNumbers, SECP256R1
        from cryptography.hazmat.backends import default_backend
        credential = DefaultAzureCredential()
        client = KeyClient(vault_url=self._config.vault_url or "", credential=credential)
        key = client.get_key(self._config.key_id)
        kv = key.key
        import base64

        def _b64url_int(s: str) -> int:
            padded = s + "=" * (-len(s) % 4)
            return int.from_bytes(base64.urlsafe_b64decode(padded), "big")

        numbers = EllipticCurvePublicNumbers(
            x=_b64url_int(kv.x),
            y=_b64url_int(kv.y),
            curve=SECP256R1(),
        )
        pub = numbers.public_key(default_backend())
        from cryptography.hazmat.primitives import serialization
        return pub.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

    def algorithm(self) -> str:
        return f"Azure_KeyVault/{self._config.algorithm}"
