#!/bin/bash
set -euo pipefail

die() {
  echo "ERROR: $*" >&2
  exit 1
}

load_dotenv_safe() {
  local env_file="$1"
  [ -f "$env_file" ] || return 0
  while IFS='=' read -r key raw_value; do
    [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    local value="$raw_value"
    value="${value%\"}"
    value="${value#\"}"
    value="${value%\'}"
    value="${value#\'}"
    export "${key}=${value}"
  done < <(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$env_file")
}

echo "=== RECONCILE AND SHOW STATUS ==="

# 1. Reconciliación canónica (parte original)
echo "[1/4] Reconciliando estado soberano..."
# Aquí iría tu lógica original de reconciliación (si la tienes)
# Por ahora mantenemos la parte de mostrar estado

echo "[2/4] Generando artefactos derivados..."
# (Aquí irían tus scripts de generación de GATE_REPORT, etc.)

echo "[3/4] Exportando snapshot final..."
# (Aquí iría tu exportación de final_status_snapshot.json)

echo "[4/4] Anclando estado en blockchain (Anchor Hardening)..."

load_dotenv_safe ".env"

CONTRACT_ADDRESS="${ETHICBIT_ANCHOR_CONTRACT_ADDRESS:-}"
[ -n "${CONTRACT_ADDRESS}" ] || die "Define ETHICBIT_ANCHOR_CONTRACT_ADDRESS"
[ -n "${BASE_SEPOLIA_RPC:-}" ] || die "Define BASE_SEPOLIA_RPC"

STATE_FILE="audit_package/current_state/official_operational_status.json"
[ -f "$STATE_FILE" ] || die "No existe ${STATE_FILE}"

# Calcular hash del estado soberano
STATE_HASH=$(python3 -c '
import hashlib, json, sys
with open(sys.argv[1], "r") as f:
    data = json.load(f)
print("0x" + hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest())
' "$STATE_FILE")

echo "State Hash: $STATE_HASH"

# Anclar en blockchain
echo "Anclando estado en contrato $CONTRACT_ADDRESS ..."
wallet_args=()
if [ -n "${ETH_KEYSTORE_ACCOUNT:-}" ]; then
  wallet_args+=(--account "$ETH_KEYSTORE_ACCOUNT")
elif [ -n "${ETH_KEYSTORE:-}" ]; then
  wallet_args+=(--keystore "$ETH_KEYSTORE")
  if [ -n "${ETH_PASSWORD:-}" ]; then
    wallet_args+=(--password-file "$ETH_PASSWORD")
  fi
elif [ "${ALLOW_INSECURE_PRIVATE_KEY_CLI:-false}" = "true" ] && [ -n "${PRIVATE_KEY:-}" ]; then
  echo "WARNING: usando --private-key por compatibilidad (modo inseguro habilitado)"
  wallet_args+=(--private-key "$PRIVATE_KEY")
else
  die "Configura ETH_KEYSTORE_ACCOUNT o ETH_KEYSTORE (recomendado). Si necesitas fallback inseguro, exporta ALLOW_INSECURE_PRIVATE_KEY_CLI=true y PRIVATE_KEY."
fi

CAST_OUTPUT=$(cast send "$CONTRACT_ADDRESS" "anchorState(bytes32,uint256)" \
  "$STATE_HASH" 0 \
  --rpc-url "$BASE_SEPOLIA_RPC" \
  "${wallet_args[@]}" \
  --json)

TX_HASH=$(printf '%s' "$CAST_OUTPUT" | jq -r '.transactionHash // empty')
[ -n "$TX_HASH" ] || die "No se pudo obtener transactionHash de cast send"

echo "✅ Anclaje realizado exitosamente"
echo "Transaction Hash: $TX_HASH"
echo "Verificar en: https://sepolia.basescan.org/tx/$TX_HASH"

# Mostrar estado final (parte original del script)
echo
echo "=== OFFICIAL ==="
grep -nE '"internalClosureStatus"|"liveStatus"|"externalProjectionStatus"|"officialOperationalStatus"|"reason"' artifacts/history/swarm/official_operational_status.json || true

echo
echo "=== GATE_REPORT ==="
grep -nE 'internalClosureStatus|externalProjectionStatus|officialReasonObserved|officialExternalProjectionStatusObserved|officialOperationalStatusObserved' results/GATE_REPORT.json || true

echo
echo "=== TECHNICAL_VERIFICATION ==="
grep -nE 'Internal Closure Status|External Projection Status|Official Operational Status|Official Reason|Official Internal Closure Status|Official External Projection Status' results/technical_verification.md || true

echo
echo "=== FINAL SNAPSHOT ==="
cat results/active/final_status_snapshot.json

echo
echo "Done. Estado anclado en blockchain."
