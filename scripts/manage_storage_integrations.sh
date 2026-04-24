#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

COMMAND="${1:-help}"

status() {
  echo "=== STORAGE INTEGRATIONS STATUS ==="
  echo "root=${ROOT_DIR}"
  echo "Arweave verifier file: $( [ -f agentic/arweave_verifier.py ] && echo PASS || echo FAIL )"
  echo "Storage bridge file:   $( [ -f agentic/ipfs_nftstorage_arweave_bridge.py ] && echo PASS || echo FAIL )"
  python3 -c "from agentic.arweave_verifier import ArweaveVerifier" >/dev/null 2>&1 \
    && echo "ArweaveVerifier import: PASS" || echo "ArweaveVerifier import: FAIL"
  python3 -c "from agentic.ipfs_nftstorage_arweave_bridge import IPFSNFTStorageArweaveBridge" >/dev/null 2>&1 \
    && echo "Bridge import:          PASS" || echo "Bridge import:          FAIL"
}

install() {
  echo "No-op installer. Required dependencies are managed in project environment."
}

rollback() {
  echo "No-op rollback. Use git to revert storage integration changes."
}

case "${COMMAND}" in
  install)  install ;;
  rollback) rollback ;;
  status)   status ;;
  test)     status ;;
  help|*)
    echo "Usage: $0 <install|rollback|status|test|help>"
    ;;
esac
