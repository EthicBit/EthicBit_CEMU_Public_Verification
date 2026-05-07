#!/usr/bin/env python3
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVENT_PATH = ROOT / "examples/evolve/EVO_GEN_2026_0097_event.json"
RECEIPT_PATH = ROOT / "examples/evolve/EVO_GEN_2026_0097_receipt.json"
EVENT_SCHEMA_PATH = ROOT / "schemas/evolve/evolution_event.schema.json"
RECEIPT_SCHEMA_PATH = ROOT / "schemas/evolve/evolution_receipt.schema.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_bytes(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def require_keys(name: str, obj: dict, keys: list[str]) -> None:
    missing = [key for key in keys if key not in obj]
    if missing:
        raise ValueError(f"{name} missing required keys: {', '.join(missing)}")


def verify_with_openssl(payload: bytes, public_key: Path, signature: Path) -> bool:
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(payload)
        tmp.flush()
        result = subprocess.run(
            [
                "openssl",
                "dgst",
                "-sha256",
                "-verify",
                str(public_key),
                "-signature",
                str(signature),
                "-sigopt",
                "rsa_padding_mode:pss",
                "-sigopt",
                "rsa_pss_saltlen:-1",
                tmp.name,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    return result.returncode == 0 and "Verified OK" in result.stdout


def main() -> int:
    event_schema = load_json(EVENT_SCHEMA_PATH)
    receipt_schema = load_json(RECEIPT_SCHEMA_PATH)
    event = load_json(EVENT_PATH)
    receipt = load_json(RECEIPT_PATH)

    require_keys("event schema", event_schema, ["$schema", "title", "required", "properties"])
    require_keys("receipt schema", receipt_schema, ["$schema", "title", "required", "properties"])
    require_keys(
        "event",
        event,
        [
            "schema_id",
            "event_id",
            "system_id",
            "base_artifact",
            "change_type",
            "sector_profile",
            "materiality_score",
            "evidence_bundle",
            "requested_claim_scope",
            "scope_boundary",
        ],
    )
    require_keys("receipt", receipt, ["schema_id", "receipt_payload", "signature"])

    payload = receipt["receipt_payload"]
    signature = receipt["signature"]
    non_claims = payload["non_claims"]
    payload_bytes = canonical_bytes(payload)
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()

    checks = {
        "EVOLUTION_EVENT_SCHEMA": event["schema_id"] == "AEM_EVOLVE_EVOLUTION_EVENT_SCHEMA_V1",
        "EVOLUTION_RECEIPT_SCHEMA": receipt["schema_id"] == "AEM_EVOLVE_EVOLUTION_RECEIPT_SCHEMA_V1",
        "EVOLUTION_EVENT_MATCH": event["event_id"] == payload["event_id"],
        "EVOLUTION_RECEIPT_PAYLOAD_HASH": payload_sha256 == signature["receipt_payload_sha256"],
        "EVOLUTION_RECEIPT_OUTCOME": payload["outcome"] == "SCOPE_LIMITED",
        "EVOLUTION_RECEIPT_CLAIM_SCOPE": payload["claim_scope"] == "EVIDENCE_REVIEW_SUPPORT",
        "EVOLUTION_RECEIPT_CLAIM_BOUNDARY": (
            non_claims["clinical_claimed"] is False
            and non_claims["diagnostic_claimed"] is False
            and non_claims["regulatory_approval_claimed"] is False
            and non_claims["third_party_binding"] is False
        ),
    }

    public_key = ROOT / signature["public_key_file"]
    signature_file = ROOT / signature["signature_file"]
    checks["EVOLUTION_RECEIPT_SIGNATURE"] = verify_with_openssl(payload_bytes, public_key, signature_file)

    for key, ok in checks.items():
        print(f"{key}={'PASS' if ok else 'FAIL'}")

    print(f"outcome={payload['outcome']}")
    print(f"claim_scope={payload['claim_scope']}")
    print(f"clinical_claimed={str(non_claims['clinical_claimed']).lower()}")
    print(f"diagnostic_claimed={str(non_claims['diagnostic_claimed']).lower()}")
    print(f"regulatory_approval_claimed={str(non_claims['regulatory_approval_claimed']).lower()}")
    print(f"third_party_binding={str(non_claims['third_party_binding']).lower()}")

    if not all(checks.values()):
        print("AEM_EVOLVE_DEMO_STATUS=FAIL")
        return 1

    print("AEM_EVOLVE_DEMO_STATUS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
