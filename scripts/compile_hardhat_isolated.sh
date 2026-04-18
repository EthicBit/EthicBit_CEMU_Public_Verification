#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

# Use isolated HOME to avoid global hardhat lock collisions.
ISOLATED_HOME="${HARDHAT_ISOLATED_HOME:-/tmp/hh-home}"
# Provide a safe default URL to satisfy Hardhat config validation.
DEFAULT_RPC_URL="http://127.0.0.1:8545"

mkdir -p "${ISOLATED_HOME}"

# If the isolated cache doesn't exist yet, seed it from the current user's cache.
if [[ ! -d "${ISOLATED_HOME}/Library/Caches/hardhat-nodejs" ]] && [[ -d "${HOME}/Library/Caches/hardhat-nodejs" ]]; then
  mkdir -p "${ISOLATED_HOME}/Library/Caches"
  cp -R "${HOME}/Library/Caches/hardhat-nodejs" "${ISOLATED_HOME}/Library/Caches/"
fi

cd "${REPO_ROOT}"

HOME="${ISOLATED_HOME}" \
ETH_RPC_URL="${ETH_RPC_URL:-${DEFAULT_RPC_URL}}" \
npx hardhat compile --force "$@"
