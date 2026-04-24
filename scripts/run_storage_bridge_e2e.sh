#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

BUNDLE_PATH="${1:-}"
ARWEAVE_TX_ID="${2:-${ETHICBIT_ARWEAVE_TX_ID:-}}"

if [[ -z "${BUNDLE_PATH}" ]]; then
  echo "Uso: $0 <bundle_path> [arweave_tx_id]" >&2
  echo "Tip: también puedes pasar ARWEAVE_TX_ID por ETHICBIT_ARWEAVE_TX_ID" >&2
  exit 1
fi

if [[ ! -f "${BUNDLE_PATH}" ]]; then
  echo "Bundle no encontrado: ${BUNDLE_PATH}" >&2
  exit 1
fi

if [[ -z "${ARWEAVE_TX_ID}" ]]; then
  echo "Falta arweave_tx_id (argumento #2 o ETHICBIT_ARWEAVE_TX_ID)." >&2
  exit 1
fi

python3 - "${BUNDLE_PATH}" "${ARWEAVE_TX_ID}" <<'PY'
import json
import pathlib
import sys

from agentic.ipfs_nftstorage_arweave_bridge import IPFSNFTStorageArweaveBridge

bundle_path = pathlib.Path(sys.argv[1]).resolve()
arweave_tx_id = sys.argv[2].strip()

bridge = IPFSNFTStorageArweaveBridge()

upload = bridge.upload_to_storage(str(bundle_path))
if not upload.get("cid"):
    failed = {
        "artifactType": "storage_bridge_e2e",
        "status": "failed",
        "phase": "upload_to_storage",
        "bundle_path": str(bundle_path),
        "upload_result": upload,
    }
    print(json.dumps(failed, indent=2, ensure_ascii=False))
    raise SystemExit(1)

cid = upload["cid"]
local_hash = bridge._compute_local_hash(str(bundle_path))
ipfs_ok = bridge.verify_ipfs(cid, local_hash)

bridge_report = bridge.bridge_and_verify(str(bundle_path), arweave_tx_id)

result = {
    "artifactType": "storage_bridge_e2e",
    "status": "success" if ipfs_ok else "partial",
    "bundle_path": str(bundle_path),
    "storage_backend": upload.get("backend"),
    "cid": cid,
    "ipfs_verified": ipfs_ok,
    "bridge_report_path": str(bridge.report_file),
    "bridge_report": bridge_report,
}

print(json.dumps(result, indent=2, ensure_ascii=False))
PY
