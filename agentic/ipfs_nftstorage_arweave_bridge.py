#!/usr/bin/env python3
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict, Any
import requests
from agentic.arweave_verifier import ArweaveVerifier

class IPFSNFTStorageArweaveBridge:
    NFT_STORAGE_API_URL = "https://api.nft.storage/upload"
    IPFS_GATEWAYS = ["https://ipfs.io", "https://cloudflare-ipfs.com"]

    def __init__(self):
        self.arweave_verifier = ArweaveVerifier()
        self.nft_storage_key = os.getenv("ETHICBIT_NFT_STORAGE_KEY", "")
        self.cache_file = Path("proof_run/storage_cache.json")
        self.report_file = Path("proof_run/storage_bridge_report.json")

    def _compute_local_hash(self, bundle_path: str) -> str:
        p = Path(bundle_path)
        if not p.exists():
            raise FileNotFoundError(f"bundle not found: {bundle_path}")
        return hashlib.sha256(p.read_bytes()).hexdigest()

    def _load_cache(self) -> dict:
        if not self.cache_file.exists():
            return {}
        try:
            return json.loads(self.cache_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_cache(self, cache: dict) -> None:
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")

    def upload_to_nft_storage(self, bundle_path: str) -> Dict[str, Any]:
        local_hash = self._compute_local_hash(bundle_path)
        cache = self._load_cache()
        if local_hash in cache.get("nft_storage", {}):
            return {"cid": cache["nft_storage"][local_hash], "status": "cached"}
        if not self.nft_storage_key:
            return {"cid": None, "status": "failed", "error": "ETHICBIT_NFT_STORAGE_KEY no configurada"}
        try:
            with open(bundle_path, "rb") as f:
                headers = {"Authorization": f"Bearer {self.nft_storage_key}"}
                r = requests.post(self.NFT_STORAGE_API_URL, files={"file": f}, headers=headers, timeout=45)
                r.raise_for_status()
                cid = r.json()["value"]["cid"]
                cache.setdefault("nft_storage", {})[local_hash] = cid
                self._save_cache(cache)
                return {"cid": cid, "status": "uploaded"}
        except Exception as e:
            return {"cid": None, "status": "failed", "error": str(e)}

    def verify_ipfs(self, cid: str, local_hash: str) -> bool:
        for gateway in self.IPFS_GATEWAYS:
            try:
                r = requests.get(f"{gateway}/ipfs/{cid}", timeout=8)
                if r.status_code == 200 and hashlib.sha256(r.content).hexdigest() == local_hash:
                    return True
            except Exception:
                continue
        return False

    def bridge_and_verify(self, bundle_path: str, arweave_tx_id: str) -> Dict[str, Any]:
        start = time.time()
        local_hash = self._compute_local_hash(bundle_path)
        nft_result = self.upload_to_nft_storage(bundle_path)
        if not nft_result.get("cid"):
            result = {"artifactType": "storage_bridge_report", "status": "failed", "error": nft_result.get("error"), "bundle_path": bundle_path}
            self.report_file.parent.mkdir(parents=True, exist_ok=True)
            self.report_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
            return result
        ipfs_verified = self.verify_ipfs(nft_result["cid"], local_hash)
        arweave_result = self.arweave_verifier.verify_bundle(bundle_path, arweave_tx_id)
        result = {
            "artifactType": "storage_bridge_report",
            "status": "success",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "bundle_path": bundle_path,
            "local_hash": local_hash,
            "nft_storage_cid": nft_result["cid"],
            "ipfs_verified": ipfs_verified,
            "arweave_verification": arweave_result,
            "verification_status": "VERIFIED" if ipfs_verified and arweave_result.get("arweave_verified") else "PARTIAL",
            "duration_seconds": round(time.time() - start, 2),
        }
        self.report_file.parent.mkdir(parents=True, exist_ok=True)
        self.report_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return result
