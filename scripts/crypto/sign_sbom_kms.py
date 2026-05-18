#!/usr/bin/env python3
"""Sign EthicBit SBOM files using AWS KMS.

Uses alias/ethicbit-intoto-signing (ECC_NIST_P256, ECDSA_SHA_256).
Adds a 'signature' block at the root of each CycloneDX BOM following
the CycloneDX JSF-style envelope, and writes a detached .sig.json
sidecar alongside each signed file.
"""
from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import boto3

REPO_ROOT = Path(__file__).resolve().parents[2]
SBOM_DIR = REPO_ROOT / "assurance" / "sbom"
KEY_ID = "alias/ethicbit-intoto-signing"
REGION = "us-east-2"
SIGNING_ALGORITHM = "ECDSA_SHA_256"

SBOM_FILES = [
    "aem_v1_1_sbom.cyclonedx.json",
]


def canonical_payload(bom: dict) -> bytes:
    """Deterministic JSON of the BOM, excluding any existing signature block."""
    unsigned = {k: v for k, v in bom.items() if k != "signature"}
    return json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()


def sign_sbom(kms: boto3.client, path: Path, signer_arn: str, now: str) -> tuple[dict, dict]:
    bom = json.loads(path.read_text(encoding="utf-8"))
    payload = canonical_payload(bom)
    payload_hash = hashlib.sha256(payload).digest()
    payload_sha256 = hashlib.sha256(payload).hexdigest()

    resp = kms.sign(
        KeyId=KEY_ID,
        Message=payload_hash,
        MessageType="DIGEST",
        SigningAlgorithm=SIGNING_ALGORITHM,
    )
    sig_b64 = base64.b64encode(resp["Signature"]).decode()

    signature_block = {
        "algorithm": SIGNING_ALGORITHM,
        "keyId": KEY_ID,
        "signerArn": signer_arn,
        "value": sig_b64,
        "payloadSHA256": payload_sha256,
        "signedAt": now,
    }

    signed_bom = {**bom, "signature": signature_block}

    sidecar = {
        "schema_id": "ETHICBIT_SBOM_KMS_SIGNATURE_V1",
        "sbom_file": path.name,
        "bomFormat": bom.get("bomFormat"),
        "specVersion": bom.get("specVersion"),
        "component_count": len(bom.get("components", [])),
        "payloadSHA256": payload_sha256,
        "signature": signature_block,
    }

    return signed_bom, sidecar


def main() -> None:
    kms = boto3.client("kms", region_name=REGION)

    key_meta = kms.describe_key(KeyId=KEY_ID)["KeyMetadata"]
    signer_arn = key_meta["Arn"]
    now = datetime.now(timezone.utc).isoformat()

    print(f"Signer ARN : {signer_arn}")
    print(f"Timestamp  : {now}")
    print()

    for filename in SBOM_FILES:
        path = SBOM_DIR / filename
        if not path.exists():
            print(f"  SKIP {filename} (not found)")
            continue

        signed_bom, sidecar = sign_sbom(kms, path, signer_arn, now)

        path.write_text(json.dumps(signed_bom, indent=2) + "\n", encoding="utf-8")
        sidecar_path = SBOM_DIR / (path.stem + ".sig.json")
        sidecar_path.write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")

        sig_preview = sidecar["signature"]["value"][:32]
        print(f"  SIGNED {filename}")
        print(f"    sha256={sidecar['payloadSHA256'][:32]}...")
        print(f"    sig={sig_preview}...")
        print(f"    sidecar → {sidecar_path.name}")

    print("\nSBOM signing complete.")


if __name__ == "__main__":
    main()
