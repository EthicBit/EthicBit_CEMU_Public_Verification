"""
KmsSigningProvider — SigningProvider backed by AWS KMS.

Requires: pip install boto3
IAM: the caller must have kms:Sign and kms:GetPublicKey on the key ARN.

Configuration (environment variables):
  ETHICBIT_KMS_KEY_ID   AWS KMS key ARN or alias (e.g. arn:aws:kms:us-east-1:…)
  AWS_REGION            AWS region (or set via AWS_DEFAULT_REGION / ~/.aws/config)

Non-claims:
  Not production-tested against a live AWS KMS key.
  Requires valid AWS credentials and an Ed25519 or ECC KMS key.
  This stub confirms ABC compliance; real use requires AWS account + permissions.
"""

from __future__ import annotations

import base64
import os

from .signing_provider import SigningProvider

_KEY_ENV = "ETHICBIT_KMS_KEY_ID"


class KmsSigningProvider(SigningProvider):
    """Ed25519 / ECC signing via AWS KMS.

    Falls back to a clear ImportError when `boto3` is not installed.
    """

    def __init__(
        self,
        key_id: str | None = None,
        region: str | None = None,
        signing_algorithm: str = "ECDSA_SHA_256",
    ) -> None:
        try:
            import boto3  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "boto3 is required for KmsSigningProvider. "
                "Install with: pip install boto3  "
                "Then set ETHICBIT_KMS_KEY_ID to your KMS key ARN."
            ) from exc

        key_id = key_id or os.environ.get(_KEY_ENV)
        if not key_id:
            raise EnvironmentError(
                f"KMS key ID not set. Set {_KEY_ENV} or pass key_id= to KmsSigningProvider."
            )

        self._key_id = key_id
        self._algorithm = signing_algorithm
        self._client = boto3.client("kms", region_name=region)
        self._pub_pem: bytes | None = None  # lazy-loaded

    def sign(self, message: bytes) -> bytes:
        import hashlib
        digest = hashlib.sha256(message).digest()
        response = self._client.sign(
            KeyId=self._key_id,
            Message=digest,
            MessageType="DIGEST",
            SigningAlgorithm=self._algorithm,
        )
        return response["Signature"]

    def verify(self, message: bytes, signature: bytes) -> bool:
        import hashlib
        digest = hashlib.sha256(message).digest()
        try:
            response = self._client.verify(
                KeyId=self._key_id,
                Message=digest,
                MessageType="DIGEST",
                Signature=signature,
                SigningAlgorithm=self._algorithm,
            )
            return response.get("SignatureValid", False)
        except Exception:
            return False

    def public_key_pem(self) -> bytes:
        if self._pub_pem is None:
            response = self._client.get_public_key(KeyId=self._key_id)
            der = response["PublicKey"]
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.serialization import load_der_public_key
            key = load_der_public_key(der)
            self._pub_pem = key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        return self._pub_pem

    def algorithm(self) -> str:
        return f"KMS/{self._algorithm}"
