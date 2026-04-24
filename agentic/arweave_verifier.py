#!/usr/bin/env python3
import hashlib
import os
import time
from pathlib import Path
from typing import Dict, Any
import requests

class ArweaveVerifier:
    DEFAULT_GATEWAYS = ["https://arweave.net", "https://arweave.dev", "https://permagate.io"]

    def __init__(self):
        self.gateways = os.getenv("ETHICBIT_ARWEAVE_GATEWAYS", ",".join(self.DEFAULT_GATEWAYS)).split(",")
        self.timeout = int(os.getenv("ETHICBIT_ARWEAVE_TIMEOUT", "12"))
        self.retries = int(os.getenv("ETHICBIT_ARWEAVE_RETRIES", "2"))

    def _compute_local_hash(self, bundle_path: str) -> str:
        p = Path(bundle_path)
        if not p.exists():
            raise FileNotFoundError(f"bundle not found: {bundle_path}")
        return hashlib.sha256(p.read_bytes()).hexdigest()

    def verify_bundle(self, bundle_path: str, arweave_tx_id: str) -> Dict[str, Any]:
        result = {
            "source": "arweave_verifier",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "bundle_path": bundle_path,
            "arweave_tx_id": arweave_tx_id,
            "arweave_verified": False,
            "gateways_tried": 0,
            "verification_status": "UNVERIFIED",
        }
        local_hash = self._compute_local_hash(bundle_path)
        result["local_hash"] = local_hash

        if not arweave_tx_id:
            result["error"] = "ETHICBIT_ARWEAVE_TX_ID missing"
            return result

        for gateway in self.gateways:
            for attempt in range(self.retries + 1):
                try:
                    url = f"{gateway.rstrip('/')}/{arweave_tx_id}"
                    resp = requests.get(url, timeout=self.timeout)
                    resp.raise_for_status()
                    remote_hash = hashlib.sha256(resp.content).hexdigest()
                    result["gateways_tried"] += 1
                    result["used_gateway"] = gateway
                    result["remote_hash"] = remote_hash
                    if local_hash == remote_hash:
                        result.update({
                            "arweave_verified": True,
                            "verification_status": "VERIFIED",
                            "error": None,
                        })
                        return result
                    break
                except Exception:
                    if attempt < self.retries:
                        time.sleep(0.5)
                    continue

        result["error"] = "All gateways failed or hash mismatch"
        return result
