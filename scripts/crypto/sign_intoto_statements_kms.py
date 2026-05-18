#!/usr/bin/env python3
"""Sign EthicBit in-toto statements using AWS KMS.

Uses alias/ethicbit-intoto-signing (ECC_NIST_P256, ECDSA_SHA_256).
Writes signature, signedBy, signedAt, and verificationStatus into each
statement file in assurance/in-toto/attestations/.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import boto3

REPO_ROOT = Path(__file__).resolve().parents[2]
ATTESTATIONS_DIR = REPO_ROOT / "assurance" / "in-toto" / "attestations"
KEY_ID = "alias/ethicbit-intoto-signing"
REGION = "us-east-2"
SIGNING_ALGORITHM = "ECDSA_SHA_256"

STATEMENT_FILES = [
    "intake.statement.json",
    "provenance.statement.json",
    "governance.statement.json",
    "fixation.statement.json",
    "sealing.statement.json",
    "closure.statement.json",
]


def canonical_payload(statement: dict) -> bytes:
    """Produce deterministic JSON payload for signing (excludes signature fields)."""
    fields_to_sign = {
        k: v for k, v in statement.items()
        if k not in ("signedBy", "signedAt", "signature", "verificationStatus", "status")
    }
    return json.dumps(fields_to_sign, sort_keys=True, separators=(",", ":")).encode()


def sign_statement(kms: boto3.client, statement_path: Path, signer_arn: str, now: str) -> dict:
    payload = canonical_payload(json.loads(statement_path.read_text()))
    payload_hash = hashlib.sha256(payload).digest()

    resp = kms.sign(
        KeyId=KEY_ID,
        Message=payload_hash,
        MessageType="DIGEST",
        SigningAlgorithm=SIGNING_ALGORITHM,
    )
    sig_b64 = base64.b64encode(resp["Signature"]).decode()

    statement = json.loads(statement_path.read_text())
    statement["signedBy"] = [signer_arn]
    statement["signedAt"] = now
    statement["signature"] = sig_b64
    statement["signingAlgorithm"] = SIGNING_ALGORITHM
    statement["payloadSHA256"] = hashlib.sha256(payload).hexdigest()
    statement["verificationStatus"] = "KMS_SIGNED"
    statement["status"] = "KMS_SIGNED_PENDING_EXTERNAL_WITNESS"
    return statement


def main() -> None:
    kms = boto3.client("kms", region_name=REGION)

    key_meta = kms.describe_key(KeyId=KEY_ID)["KeyMetadata"]
    signer_arn = key_meta["Arn"]
    now = datetime.now(timezone.utc).isoformat()

    print(f"Signer ARN : {signer_arn}")
    print(f"Timestamp  : {now}")
    print()

    for filename in STATEMENT_FILES:
        path = ATTESTATIONS_DIR / filename
        if not path.exists():
            print(f"  SKIP {filename} (not found)")
            continue
        signed = sign_statement(kms, path, signer_arn, now)
        path.write_text(json.dumps(signed, indent=2) + "\n")
        print(f"  SIGNED {filename} — sig={signed['signature'][:32]}...")

    print("\nAll statements signed.")
    print("Next: update attestation-index.json status.")


if __name__ == "__main__":
    main()
