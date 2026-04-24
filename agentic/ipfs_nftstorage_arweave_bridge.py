#!/usr/bin/env python3
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from agentic.arweave_verifier import ArweaveVerifier

class IPFSNFTStorageArweaveBridge:
    STORAGE_BACKEND_AUTO = "auto"
    STORAGE_BACKEND_NFT_STORAGE = "nft_storage"
    STORAGE_BACKEND_PINATA = "pinata"
    NFT_STORAGE_API_URL = "https://api.nft.storage/upload"
    PINATA_API_URL = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    IPFS_GATEWAYS = ["https://ipfs.io", "https://cloudflare-ipfs.com"]

    def __init__(self):
        self.arweave_verifier = ArweaveVerifier()
        self.storage_backend = os.getenv("ETHICBIT_STORAGE_BACKEND", self.STORAGE_BACKEND_AUTO).strip().lower()
        self.nft_storage_key = os.getenv("ETHICBIT_NFT_STORAGE_KEY", "")
        self.nft_storage_api_url = os.getenv("ETHICBIT_NFT_STORAGE_API_URL", self.NFT_STORAGE_API_URL)
        self.pinata_jwt = os.getenv("ETHICBIT_PINATA_JWT", "").strip()
        self.pinata_api_key = os.getenv("ETHICBIT_PINATA_API_KEY", "").strip()
        self.pinata_api_secret = os.getenv("ETHICBIT_PINATA_API_SECRET", "").strip()
        self.pinata_api_url = os.getenv("ETHICBIT_PINATA_API_URL", self.PINATA_API_URL).strip() or self.PINATA_API_URL
        self.cache_file = Path("proof_run/storage_cache.json")
        self.report_file = Path("proof_run/storage_bridge_report.json")

    def _build_retry_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["POST"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _extract_cid(self, payload: Any) -> str:
        if not isinstance(payload, dict):
            return ""
        value = payload.get("value")
        if isinstance(value, dict) and isinstance(value.get("cid"), str) and value.get("cid"):
            return value["cid"]
        if isinstance(payload.get("cid"), str) and payload.get("cid"):
            return payload["cid"]
        return ""

    def _format_http_error(self, response: requests.Response, mode: str) -> str:
        body = (response.text or "").strip().replace("\n", " ")
        body = body[:280]
        return f"{mode}: HTTP {response.status_code} {response.reason} - {body}" if body else f"{mode}: HTTP {response.status_code} {response.reason}"

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
            return {"cid": cache["nft_storage"][local_hash], "status": "cached", "backend": self.STORAGE_BACKEND_NFT_STORAGE}
        if not self.nft_storage_key:
            return {"cid": None, "status": "failed", "error": "ETHICBIT_NFT_STORAGE_KEY no configurada", "backend": self.STORAGE_BACKEND_NFT_STORAGE}

        session = self._build_retry_session()
        errors = []
        auth_header = {"Authorization": f"Bearer {self.nft_storage_key}", "Accept": "application/json"}
        bundle_name = Path(bundle_path).name

        try:
            # Preferred path for NFT.Storage Upload API: raw body, not multipart.
            with open(bundle_path, "rb") as f:
                headers = dict(auth_header)
                headers["Content-Type"] = "application/octet-stream"
                r = session.post(self.nft_storage_api_url, data=f, headers=headers, timeout=(10, 120))
            if r.ok:
                payload = r.json()
                cid = self._extract_cid(payload)
                if cid:
                    cache.setdefault("nft_storage", {})[local_hash] = cid
                    self._save_cache(cache)
                    return {"cid": cid, "status": "uploaded", "backend": self.STORAGE_BACKEND_NFT_STORAGE}
                errors.append("octet-stream: response missing CID")
            else:
                errors.append(self._format_http_error(r, "octet-stream"))

            # Compatibility fallback for endpoints that still expect multipart form-data.
            with open(bundle_path, "rb") as f:
                r2 = session.post(
                    self.nft_storage_api_url,
                    files={"file": (bundle_name, f, "application/octet-stream")},
                    headers=auth_header,
                    timeout=(10, 120),
                )
            if r2.ok:
                payload = r2.json()
                cid = self._extract_cid(payload)
                if cid:
                    cache.setdefault("nft_storage", {})[local_hash] = cid
                    self._save_cache(cache)
                    return {"cid": cid, "status": "uploaded", "backend": self.STORAGE_BACKEND_NFT_STORAGE}
                errors.append("multipart: response missing CID")
            else:
                errors.append(self._format_http_error(r2, "multipart"))

            combined = " | ".join(errors) if errors else "unknown NFT.Storage upload error"
            if "decommission" in combined.lower():
                combined += " | NFT.Storage classic uploads appear decommissioned; configure an alternate hot storage backend."
            return {"cid": None, "status": "failed", "error": combined, "backend": self.STORAGE_BACKEND_NFT_STORAGE}
        except Exception as e:
            combined = " | ".join(errors) if errors else ""
            suffix = f" | prior_attempts={combined}" if combined else ""
            return {"cid": None, "status": "failed", "error": f"{str(e)}{suffix}", "backend": self.STORAGE_BACKEND_NFT_STORAGE}
        finally:
            session.close()

    def upload_to_pinata(self, bundle_path: str) -> Dict[str, Any]:
        local_hash = self._compute_local_hash(bundle_path)
        cache = self._load_cache()
        if local_hash in cache.get("pinata", {}):
            return {"cid": cache["pinata"][local_hash], "status": "cached", "backend": self.STORAGE_BACKEND_PINATA}

        headers = {"Accept": "application/json"}
        if self.pinata_jwt:
            headers["Authorization"] = f"Bearer {self.pinata_jwt}"
        elif self.pinata_api_key and self.pinata_api_secret:
            headers["pinata_api_key"] = self.pinata_api_key
            headers["pinata_secret_api_key"] = self.pinata_api_secret
        else:
            return {
                "cid": None,
                "status": "failed",
                "error": "Pinata credentials missing: set ETHICBIT_PINATA_JWT or ETHICBIT_PINATA_API_KEY + ETHICBIT_PINATA_API_SECRET",
                "backend": self.STORAGE_BACKEND_PINATA,
            }

        session = self._build_retry_session()
        bundle_name = Path(bundle_path).name
        try:
            with open(bundle_path, "rb") as f:
                response = session.post(
                    self.pinata_api_url,
                    headers=headers,
                    files={"file": (bundle_name, f, "application/octet-stream")},
                    timeout=(10, 120),
                )
            if not response.ok:
                return {
                    "cid": None,
                    "status": "failed",
                    "error": self._format_http_error(response, "pinata"),
                    "backend": self.STORAGE_BACKEND_PINATA,
                }

            payload = response.json()
            cid = payload.get("IpfsHash")
            if not isinstance(cid, str) or not cid:
                return {
                    "cid": None,
                    "status": "failed",
                    "error": "pinata: response missing IpfsHash",
                    "backend": self.STORAGE_BACKEND_PINATA,
                }

            cache.setdefault("pinata", {})[local_hash] = cid
            self._save_cache(cache)
            return {"cid": cid, "status": "uploaded", "backend": self.STORAGE_BACKEND_PINATA}
        except Exception as e:
            return {"cid": None, "status": "failed", "error": str(e), "backend": self.STORAGE_BACKEND_PINATA}
        finally:
            session.close()

    def upload_to_storage(self, bundle_path: str) -> Dict[str, Any]:
        backend = self.storage_backend
        if backend == self.STORAGE_BACKEND_NFT_STORAGE:
            return self.upload_to_nft_storage(bundle_path)
        if backend == self.STORAGE_BACKEND_PINATA:
            return self.upload_to_pinata(bundle_path)
        if backend != self.STORAGE_BACKEND_AUTO:
            return {
                "cid": None,
                "status": "failed",
                "error": f"Unsupported ETHICBIT_STORAGE_BACKEND={backend}. Use auto|nft_storage|pinata",
                "backend": backend,
            }

        nft_result = self.upload_to_nft_storage(bundle_path)
        if nft_result.get("cid"):
            return nft_result

        pinata_result = self.upload_to_pinata(bundle_path)
        if pinata_result.get("cid"):
            pinata_result["fallback_from"] = self.STORAGE_BACKEND_NFT_STORAGE
            return pinata_result

        nft_err = nft_result.get("error", "unknown nft_storage error")
        pinata_err = pinata_result.get("error", "unknown pinata error")
        return {
            "cid": None,
            "status": "failed",
            "backend": self.STORAGE_BACKEND_AUTO,
            "error": f"auto backend failed: nft_storage=({nft_err}) | pinata=({pinata_err})",
        }

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
        storage_result = self.upload_to_storage(bundle_path)
        if not storage_result.get("cid"):
            result = {
                "artifactType": "storage_bridge_report",
                "status": "failed",
                "error": storage_result.get("error"),
                "storage_backend": storage_result.get("backend", self.storage_backend),
                "bundle_path": bundle_path,
            }
            self.report_file.parent.mkdir(parents=True, exist_ok=True)
            self.report_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
            return result

        cid = storage_result["cid"]
        backend_used = storage_result.get("backend", self.storage_backend)
        ipfs_verified = self.verify_ipfs(cid, local_hash)
        arweave_result = self.arweave_verifier.verify_bundle(bundle_path, arweave_tx_id)
        result = {
            "artifactType": "storage_bridge_report",
            "status": "success",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "bundle_path": bundle_path,
            "local_hash": local_hash,
            "storage_backend": backend_used,
            "storage_cid": cid,
            "nft_storage_cid": cid if backend_used == self.STORAGE_BACKEND_NFT_STORAGE else None,
            "pinata_cid": cid if backend_used == self.STORAGE_BACKEND_PINATA else None,
            "ipfs_verified": ipfs_verified,
            "arweave_verification": arweave_result,
            "verification_status": "VERIFIED" if ipfs_verified and arweave_result.get("arweave_verified") else "PARTIAL",
            "duration_seconds": round(time.time() - start, 2),
        }
        if storage_result.get("fallback_from"):
            result["storage_fallback_from"] = storage_result["fallback_from"]
        self.report_file.parent.mkdir(parents=True, exist_ok=True)
        self.report_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return result
