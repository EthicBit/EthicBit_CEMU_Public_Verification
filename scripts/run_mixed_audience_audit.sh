#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${ROOT_DIR:-$(cd -- "${SCRIPT_DIR}/.." && pwd)}"
RESULTS_DIR="${ROOT_DIR}/results"
PROFILE="all"
JSON_QUERY_SCRIPT="${ROOT_DIR}/scripts/json_query.py"
READINESS_CANDIDATE="READY_FOR_CONTROLLED_PRODUCTION"
READINESS_READY="READY_FOR_CONTROLLED_PRODUCTION"
READINESS_ACTIVE="CONTROLLED_PRODUCTION_ACTIVE"
STATE_TAXONOMY_VERSION="ethicbit-state-taxonomy.v2.0.0"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/run_mixed_audience_audit.sh --all
  ./scripts/run_mixed_audience_audit.sh --profile public
  ./scripts/run_mixed_audience_audit.sh --profile technical
  ./scripts/run_mixed_audience_audit.sh --profile legal
  ./scripts/run_mixed_audience_audit.sh --profile regulatory
  ./scripts/run_mixed_audience_audit.sh --profile finance
  ./scripts/run_mixed_audience_audit.sh --profile executive
  ./scripts/run_mixed_audience_audit.sh --results-dir ./results
EOF
}

fail() {
  printf '%s\n' "$*" >&2
  exit 1
}

sha256_file() {
  shasum -a 256 "$1" | awk '{print $1}'
}

json_get() {
  local file="$1"
  local path="$2"
  env -i PATH=/usr/bin:/bin HOME="${HOME:-$ROOT_DIR}" TMPDIR=/tmp /usr/bin/python3 -S "$JSON_QUERY_SCRIPT" "$file" "$path"
}

json_get_or_default() {
  local file="$1"
  local path="$2"
  local default_value="$3"
  if env -i PATH=/usr/bin:/bin HOME="${HOME:-$ROOT_DIR}" TMPDIR=/tmp /usr/bin/python3 -S "$JSON_QUERY_SCRIPT" "$file" "$path" >/tmp/json_query_out.$$ 2>/dev/null; then
    cat /tmp/json_query_out.$$
  else
    printf '%s\n' "$default_value"
  fi
  rm -f /tmp/json_query_out.$$
}

json_get_joined() {
  local file="$1"
  local path="$2"
  env -i PATH=/usr/bin:/bin HOME="${HOME:-$ROOT_DIR}" TMPDIR=/tmp /usr/bin/python3 -S "$JSON_QUERY_SCRIPT" "$file" "$path" --joined
}

json_quote() {
  env -i PATH=/usr/bin:/bin HOME="${HOME:-$ROOT_DIR}" TMPDIR=/tmp /usr/bin/python3 -S -c 'import json, sys; print(json.dumps(sys.argv[1]))' "$1"
}

matches_profile() {
  local target="$1"
  [[ "$PROFILE" == "all" || "$PROFILE" == "$target" ]]
}

resolve_root_relative() {
  local value="$1"
  if [[ -z "$value" || "$value" == "null" ]]; then
    printf '\n'
  else
    printf '%s/%s\n' "$ROOT_DIR" "$value"
  fi
}

gate_if() {
  if "$@"; then
    printf 'PASS\n'
  else
    printf 'FAIL\n'
  fi
}

contains_line() {
  local haystack="$1"
  local needle="$2"
  printf '%s\n' "$haystack" | grep -Fxq "$needle"
}

is_verified_readiness_status() {
  local value="$1"
  [[ "$value" == "$READINESS_CANDIDATE" || "$value" == "$READINESS_READY" || "$value" == "$READINESS_ACTIVE" ]]
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)
      PROFILE="all"
      shift
      ;;
    --profile)
      PROFILE="${2:-}"
      [[ -n "$PROFILE" ]] || fail "missing value for --profile"
      shift 2
      ;;
    --results-dir)
      RESULTS_DIR="${2:-}"
      [[ -n "$RESULTS_DIR" ]] || fail "missing value for --results-dir"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

case "$PROFILE" in
  all|public|technical|legal|regulatory|finance|executive)
    ;;
  *)
    fail "unsupported profile: $PROFILE"
    ;;
esac

VERIFY_SCRIPT="${ROOT_DIR}/scripts/verify_closure_integrity.sh"
READINESS_SCRIPT="${ROOT_DIR}/scripts/run_production_readiness.sh"
PACKAGE_MANIFEST="${ROOT_DIR}/PACKAGE_MANIFEST.json"
ARTIFACT_MANIFEST="${ROOT_DIR}/artifacts/artifact_manifest.json"
BUNDLE="${ROOT_DIR}/artifacts/security_incident_bundle_v1_0.json"
CERTIFICATE="${ROOT_DIR}/artifacts/formal_closure_certificate_multicapa_v1_0.json"
LEDGER="${ROOT_DIR}/artifacts/ethicbit_closure_artifacts_hashes.json"
PUBLICATION_STATE="${ROOT_DIR}/publication/publication_state.json"

[[ -x "$VERIFY_SCRIPT" ]] || fail "missing executable: $VERIFY_SCRIPT"
[[ -x "$READINESS_SCRIPT" ]] || fail "missing executable: $READINESS_SCRIPT"
[[ -f "$PACKAGE_MANIFEST" ]] || fail "missing package manifest: $PACKAGE_MANIFEST"
[[ -f "$ARTIFACT_MANIFEST" ]] || fail "missing artifact manifest: $ARTIFACT_MANIFEST"
[[ -f "$BUNDLE" ]] || fail "missing bundle: $BUNDLE"
[[ -f "$CERTIFICATE" ]] || fail "missing certificate: $CERTIFICATE"
[[ -f "$LEDGER" ]] || fail "missing ledger: $LEDGER"
[[ -f "$PUBLICATION_STATE" ]] || fail "missing publication state: $PUBLICATION_STATE"

VERIFY_OUTPUT=""
VERIFY_EXIT_CODE=0
if VERIFY_OUTPUT="$("$VERIFY_SCRIPT" "$ROOT_DIR" 2>&1)"; then
  VERIFY_EXIT_CODE=0
else
  VERIFY_EXIT_CODE=$?
fi

READINESS_OUTPUT=""
READINESS_EXIT_CODE=0
if READINESS_OUTPUT="$("$READINESS_SCRIPT" "$ROOT_DIR" "${ROOT_DIR}/publication" 2>&1)"; then
  READINESS_EXIT_CODE=0
else
  READINESS_EXIT_CODE=$?
fi

VERIFY_STATUS="$(printf '%s\n' "$VERIFY_OUTPUT" | tail -n 1)"
READINESS_STATUS="$(printf '%s\n' "$READINESS_OUTPUT" | tail -n 1)"

CASE003_MATERIAL_STATUS="$("${ROOT_DIR}/scripts/verify_case003_material_integrity.sh" 2>/tmp/case003_material_check.err || true)"
if [[ "$CASE003_MATERIAL_STATUS" != "CASE003_MATERIAL_OK" ]]; then
  READINESS_STATUS="NOT_VERIFIED"
  READINESS_EXIT_CODE=1
fi

material_case003_root_hash_verified() {
  python3 - <<'PY2'
import json
from pathlib import Path
import sys

root = Path("artifacts/cases/case_003/canonical_root.case_003.json")
anchor = Path("artifacts/cases/case_003/anchor_verification.case_003.canonical.json")

def norm(v: str) -> str:
    v = (v or "").strip().lower()
    if v.startswith("0x"):
        v = v[2:]
    return v

if not root.exists() or not anchor.exists():
    raise SystemExit(1)

root_data = json.loads(root.read_text(encoding="utf-8"))
anchor_data = json.loads(anchor.read_text(encoding="utf-8"))

root_hash = norm(root_data.get("root_hash", ""))
expected_root_hash = norm(anchor_data.get("expected_root_hash", ""))

if not root_hash or not expected_root_hash:
    raise SystemExit(1)

if root_hash != expected_root_hash:
    raise SystemExit(1)

print("case003_root_hash_match")
PY2
}

if ! material_case003_root_hash_verified >/tmp/case003_material_check.out 2>/tmp/case003_material_check.err; then
  READINESS_STATUS="NOT_VERIFIED"
  READINESS_EXIT_CODE=1
fi

if [[ "$VERIFY_EXIT_CODE" -ne 0 && "$VERIFY_STATUS" != "ACTIVE_CANONICAL" ]]; then
  VERIFY_STATUS="NOT_VERIFIED"
fi
if [[ "$READINESS_EXIT_CODE" -ne 0 ]] || ! is_verified_readiness_status "$READINESS_STATUS"; then
  READINESS_STATUS="NOT_VERIFIED"
fi
DECLARED_PACK_STATE="$(json_get "$PACKAGE_MANIFEST" "declaredState.packState")"
DECLARED_EXTERNAL_ANCHOR_STATE="$(json_get "$PACKAGE_MANIFEST" "declaredState.externalAnchorState")"
DECLARED_OPERATIONAL_READINESS="$(json_get "$PACKAGE_MANIFEST" "declaredState.operationalReadinessClaim")"
DECLARED_PUBLICATION_STATE="$(json_get "$PACKAGE_MANIFEST" "declaredState.publicationState")"
PACKAGE_ID="$(json_get "$PACKAGE_MANIFEST" "packageId")"
PUBLISHED_AT="$(json_get "$PACKAGE_MANIFEST" "publishedAt")"
ACTIVE_TARGET="$(json_get "$PUBLICATION_STATE" "activeTarget")"
PUBLICATION_STATE_VALUE="$(json_get "$PUBLICATION_STATE" "state")"
PUBLICATION_PUBLISHED_AT="$(json_get "$PUBLICATION_STATE" "publishedAt")"
CANONICAL_LINEAGE="$(json_get_or_default "$BUNDLE" "identity.selectedCanonicalLineage" "case_003_promoted_active_chain")"
CASE003_TX_HASH="$(json_get_or_default "$BUNDLE" "externalAnchorEvidence.case003.txHash" "NOT_DECLARED")"
MANIFEST_BUNDLE_HASH="$(json_get "$ARTIFACT_MANIFEST" "securityIncidentBundle.hash")"
MANIFEST_CERTIFICATE_HASH="$(json_get "$ARTIFACT_MANIFEST" "formalClosureCertificate.hash")"
LEDGER_BUNDLE_HASH="$(json_get "$LEDGER" "bundleHash")"
LEDGER_CERTIFICATE_HASH="$(json_get "$LEDGER" "certificateHash")"
LEDGER_MANIFEST_PATH="$(json_get "$LEDGER" "derivedFrom.manifestPath")"
MANIFEST_ACTIVE_STATE="$(json_get "$ARTIFACT_MANIFEST" "activePublication.state")"
ALLOWED_CLAIMS="$(json_get_or_default "$BUNDLE" "governance.allowedClaims" "NOT_DECLARED")"
FORBIDDEN_CLAIMS="$(json_get_or_default "$BUNDLE" "governance.forbiddenClaims" "NOT_DECLARED")"
OFFICIAL_STATES="$(json_get_or_default "$BUNDLE" "officialStates" "ACTIVE_CANONICAL")"
DECLARED_CERTIFICATE_STATES="$(json_get_or_default "$CERTIFICATE" "declaredStates" "READY_FOR_CONTROLLED_PRODUCTION")"
ANCHOR_HARDENING_STATUS_REL="$(json_get_or_default "$BUNDLE" "externalAnchorEvidence.swarmMvpV1.anchorHardeningStatusPath" "artifacts/history/swarm/anchor_hardening_status.swarm_mvp_v1.json")"
INDEPENDENT_REVERIFICATION_REL="$(json_get_or_default "$BUNDLE" "externalAnchorEvidence.swarmMvpV1.independentExternalReverificationArtifactPath" "artifacts/history/swarm/independent_external_anchor_reverification.swarm_mvp_v1.json")"
ANCHOR_HARDENING_STATUS_PATH="$(resolve_root_relative "$ANCHOR_HARDENING_STATUS_REL")"
INDEPENDENT_REVERIFICATION_PATH="$(resolve_root_relative "$INDEPENDENT_REVERIFICATION_REL")"
GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
RUN_ID="${ETHICBIT_RUN_ID:-run-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
RELEASE_ID="${ETHICBIT_RELEASE_ID:-${PACKAGE_ID}}"
VERIFICATION_EPOCH="${ETHICBIT_VERIFICATION_EPOCH:-$(date -u +%Y-%m-%dT%H:00:00Z)}"
GATE_POLICY_VERSION="mixed-audience-gate-policy.v1.1.0"
OFFICIAL_AUDIT_WORKFLOW="${ROOT_DIR}/.github/workflows/official-periodic-audit.yml"
OFFICIAL_OPERATIONAL_STATUS_PATH="${ROOT_DIR}/artifacts/history/swarm/official_operational_status.json"
PQ_RUNTIME_SECRET_PROTECTION_PATH="${ROOT_DIR}/results/pq_runtime_secret_protection.json"
LEGACY_RELEASE_PATH="publication/releases/release-20260407T204627Z"
LEGACY_RELEASE_CERTIFICATE="${ROOT_DIR}/${LEGACY_RELEASE_PATH}/artifacts/formal_closure_certificate_multicapa_v1_0.json"
LEGACY_HUMAN_APPROVAL_ARTIFACT_PATH="${ROOT_DIR}/${LEGACY_RELEASE_PATH}/artifacts/cases/case_003/human_approval.case_003.canonical.json"
ACTIVE_HUMAN_APPROVAL_ARTIFACT_PATH="${ROOT_DIR}/artifacts/cases/case_003/human_approval.case_003.canonical.json"
VERIFY_OUTPUT_JSON="$(json_quote "$VERIFY_OUTPUT")"
READINESS_OUTPUT_JSON="$(json_quote "$READINESS_OUTPUT")"

ACTIVE_RELEASE_DIR="${ROOT_DIR}/publication/${ACTIVE_TARGET}"
ACTIVE_RELEASE_BUNDLE="${ACTIVE_RELEASE_DIR}/artifacts/security_incident_bundle_v1_0.json"
ACTIVE_RELEASE_CERTIFICATE="${ACTIVE_RELEASE_DIR}/artifacts/formal_closure_certificate_multicapa_v1_0.json"
ACTIVE_RELEASE_MANIFEST="${ACTIVE_RELEASE_DIR}/artifacts/artifact_manifest.json"
ACTIVE_LINK_TARGET="$(readlink "${ROOT_DIR}/publication/active")"

ACTUAL_BUNDLE_HASH="$(sha256_file "$BUNDLE")"
ACTUAL_CERTIFICATE_HASH="$(sha256_file "$CERTIFICATE")"

GATE_REQUIRED_COMPONENTS="$(gate_if test -f "$BUNDLE" -a -f "$CERTIFICATE" -a -f "$ARTIFACT_MANIFEST" -a -f "$LEDGER")"
GATE_MANIFEST_ACTIVE_STATE="$(if [[ "$MANIFEST_ACTIVE_STATE" == "ACTIVE_CANONICAL" ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"
GATE_BUNDLE_HASH_MATCHES_MANIFEST="$(if [[ "$ACTUAL_BUNDLE_HASH" == "$MANIFEST_BUNDLE_HASH" ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"
GATE_CERTIFICATE_HASH_MATCHES_MANIFEST="$(if [[ "$ACTUAL_CERTIFICATE_HASH" == "$MANIFEST_CERTIFICATE_HASH" ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"
GATE_LEDGER_BUNDLE_MATCHES_MANIFEST="$(if [[ "$LEDGER_BUNDLE_HASH" == "$MANIFEST_BUNDLE_HASH" ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"
GATE_LEDGER_CERTIFICATE_MATCHES_MANIFEST="$(if [[ "$LEDGER_CERTIFICATE_HASH" == "$MANIFEST_CERTIFICATE_HASH" ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"
GATE_LEDGER_SUBORDINATED_TO_MANIFEST="$(if [[ "$LEDGER_MANIFEST_PATH" == "artifacts/artifact_manifest.json" ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"
GATE_ACTIVE_LINK_PRESENT="$(gate_if test -L "${ROOT_DIR}/publication/active")"
GATE_ACTIVE_LINK_MATCHES_TARGET="$(if [[ "$ACTIVE_LINK_TARGET" == "$ACTIVE_TARGET" ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"
GATE_ACTIVE_RELEASE_EXISTS="$(gate_if test -d "$ACTIVE_RELEASE_DIR")"
GATE_ACTIVE_PUBLICATION_STATE="$(if [[ "$PUBLICATION_STATE_VALUE" == "ACTIVE_CANONICAL" ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"
GATE_ACTIVE_BUNDLE_MATCHES_SOURCE="$(if [[ -f "$ACTIVE_RELEASE_BUNDLE" && "$(sha256_file "$ACTIVE_RELEASE_BUNDLE")" == "$ACTUAL_BUNDLE_HASH" ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"
GATE_ACTIVE_CERTIFICATE_MATCHES_SOURCE="$(if [[ -f "$ACTIVE_RELEASE_CERTIFICATE" && "$(sha256_file "$ACTIVE_RELEASE_CERTIFICATE")" == "$ACTUAL_CERTIFICATE_HASH" ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"
GATE_ACTIVE_MANIFEST_MATCHES_SOURCE="$(if [[ -f "$ACTIVE_RELEASE_MANIFEST" && "$(sha256_file "$ACTIVE_RELEASE_MANIFEST")" == "$(sha256_file "$ARTIFACT_MANIFEST")" ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"
GATE_VERIFY_CLOSURE_INTEGRITY="$(if [[ "$VERIFY_STATUS" == "ACTIVE_CANONICAL" ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"
GATE_CASE003_MATERIAL_INTEGRITY="$(if [[ "$CASE003_MATERIAL_STATUS" == "CASE003_MATERIAL_OK" ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"
GATE_RUN_PRODUCTION_READINESS="$(if is_verified_readiness_status "$READINESS_STATUS"; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"

ZERO_ACTIVE_SUPERSEDED_FAIL=0
if printf '%s\n%s\n%s\n%s\n' \
  "$(json_get "$ARTIFACT_MANIFEST" "securityIncidentBundle.path")" \
  "$(json_get "$ARTIFACT_MANIFEST" "formalClosureCertificate.path")" \
  "$(json_get "$ARTIFACT_MANIFEST" "derivedLedger.path")" \
  "$(json_get "$LEDGER" "derivedFrom.manifestPath")" | grep -Eq '\.(superseded|drifted)\.'; then
  ZERO_ACTIVE_SUPERSEDED_FAIL=1
fi
for competing_path in "${ROOT_DIR}/artifacts"/*.superseded.json "${ROOT_DIR}/artifacts"/*.drifted.json; do
  [[ -e "$competing_path" ]] || continue
  competing_hash="$(sha256_file "$competing_path")"
  if [[ "$competing_hash" == "$ACTUAL_BUNDLE_HASH" || "$competing_hash" == "$ACTUAL_CERTIFICATE_HASH" ]]; then
    ZERO_ACTIVE_SUPERSEDED_FAIL=1
    break
  fi
done
GATE_ZERO_ACTIVE_SUPERSEDED_REFERENCES="$(if [[ "$ZERO_ACTIVE_SUPERSEDED_FAIL" -eq 0 ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"

EXTRA_PUBLICATION_POINTER=""
for pointer in "${ROOT_DIR}/publication"/*; do
  [[ -e "$pointer" ]] || continue
  if [[ -L "$pointer" && "$(basename "$pointer")" != "active" ]]; then
    EXTRA_PUBLICATION_POINTER="$pointer"
    break
  fi
done
SHADOW_PUBLICATION_POINTER=""
for pointer in \
  "${ROOT_DIR}/publication/current" \
  "${ROOT_DIR}/publication/live" \
  "${ROOT_DIR}/publication/active.json" \
  "${ROOT_DIR}/publication/current.json" \
  "${ROOT_DIR}/publication/live.json"; do
  if [[ -e "$pointer" ]]; then
    SHADOW_PUBLICATION_POINTER="$pointer"
    break
  fi
done
GATE_NO_DUAL_PUBLICATION_EFFECTIVE="$(if [[ -z "$EXTRA_PUBLICATION_POINTER" && -z "$SHADOW_PUBLICATION_POINTER" ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"
GATE_NO_STALE_PUBLIC_POINTER_CACHE="$(if [[ "$GATE_ACTIVE_LINK_PRESENT" == "PASS" && "$GATE_ACTIVE_LINK_MATCHES_TARGET" == "PASS" && "$GATE_ACTIVE_MANIFEST_MATCHES_SOURCE" == "PASS" && "$GATE_ACTIVE_BUNDLE_MATCHES_SOURCE" == "PASS" && "$GATE_ACTIVE_CERTIFICATE_MATCHES_SOURCE" == "PASS" && -n "$PUBLICATION_PUBLISHED_AT" && "$PUBLICATION_STATE_VALUE" == "ACTIVE_CANONICAL" ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"
GATE_PERIODIC_AUDIT_WORKFLOW_SCHEDULED="$(if [[ -f "$OFFICIAL_AUDIT_WORKFLOW" ]] && grep -Eq '^[[:space:]]*schedule:' "$OFFICIAL_AUDIT_WORKFLOW"; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"

GATE_ANCHOR_STATUS_ARTIFACT_PRESENT="$(gate_if test -f "$ANCHOR_HARDENING_STATUS_PATH")"
GATE_INDEPENDENT_REVERIFICATION_ARTIFACT_PRESENT="$(gate_if test -f "$INDEPENDENT_REVERIFICATION_PATH")"

if [[ "$GATE_ANCHOR_STATUS_ARTIFACT_PRESENT" == "PASS" ]]; then
  ANCHOR_HARDENING_ENABLED_VALUE="$(json_get "$ANCHOR_HARDENING_STATUS_PATH" "anchorHardeningEnabled")"
  ANCHOR_HARDENING_EVIDENCE_STATE="$(json_get "$ANCHOR_HARDENING_STATUS_PATH" "externalAnchorEvidenceState")"
  ANCHOR_HARDENING_INDEPENDENT_REVERIFICATION="$(json_get "$ANCHOR_HARDENING_STATUS_PATH" "independentExternalAnchorReverification")"
  GATE_EXTERNAL_TRIPLE_ANCHOR_RECONCILED="$(json_get "$ANCHOR_HARDENING_STATUS_PATH" "gates.TRIPLE_PUBLIC_ANCHOR_RECONCILED")"
  GATE_EXTERNAL_NO_UNRESOLVED_CONFLICTS="$(json_get "$ANCHOR_HARDENING_STATUS_PATH" "gates.no_unresolved_anchor_conflicts")"
else
  ANCHOR_HARDENING_ENABLED_VALUE="FAIL"
  ANCHOR_HARDENING_EVIDENCE_STATE="MISSING"
  ANCHOR_HARDENING_INDEPENDENT_REVERIFICATION="FAIL"
  GATE_EXTERNAL_TRIPLE_ANCHOR_RECONCILED="FAIL"
  GATE_EXTERNAL_NO_UNRESOLVED_CONFLICTS="FAIL"
fi

if [[ "$GATE_INDEPENDENT_REVERIFICATION_ARTIFACT_PRESENT" == "PASS" ]]; then
  INDEPENDENT_REVERIFICATION_STATUS="$(json_get "$INDEPENDENT_REVERIFICATION_PATH" "status")"
  GATE_EXTERNAL_ZERO_PUBLICATION_DRIFT="$(json_get "$INDEPENDENT_REVERIFICATION_PATH" "checks.zeroPublicationDrift")"
  GATE_EXTERNAL_INDEPENDENT_REVERIFICATION="$(json_get "$INDEPENDENT_REVERIFICATION_PATH" "result")"
else
  INDEPENDENT_REVERIFICATION_STATUS="FAIL"
  GATE_EXTERNAL_ZERO_PUBLICATION_DRIFT="FAIL"
  GATE_EXTERNAL_INDEPENDENT_REVERIFICATION="FAIL"
fi

GATE_ANCHOR_HARDENING_DECLARED="$(if [[ "$ANCHOR_HARDENING_ENABLED_VALUE" == "PASS" && "$ANCHOR_HARDENING_INDEPENDENT_REVERIFICATION" == "PASS" ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"
GATE_EXTERNAL_ANCHOR_HARDENING_VERIFIED="$(if [[ "$GATE_ANCHOR_HARDENING_DECLARED" == "PASS" && "$INDEPENDENT_REVERIFICATION_STATUS" == "PASS" && "$GATE_EXTERNAL_TRIPLE_ANCHOR_RECONCILED" == "PASS" && "$GATE_EXTERNAL_NO_UNRESOLVED_CONFLICTS" == "PASS" && "$GATE_EXTERNAL_ZERO_PUBLICATION_DRIFT" == "PASS" && "$GATE_EXTERNAL_INDEPENDENT_REVERIFICATION" == "PASS" ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"

DECLARED_OPERATIONAL_READINESS_PRESENT="$(if contains_line "$DECLARED_CERTIFICATE_STATES" "$READINESS_CANDIDATE" || contains_line "$DECLARED_CERTIFICATE_STATES" "$READINESS_READY" || contains_line "$DECLARED_CERTIFICATE_STATES" "$READINESS_ACTIVE"; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"

if [[ \
  "$GATE_REQUIRED_COMPONENTS" == "PASS" && \
  "$GATE_MANIFEST_ACTIVE_STATE" == "PASS" && \
  "$GATE_BUNDLE_HASH_MATCHES_MANIFEST" == "PASS" && \
  "$GATE_CERTIFICATE_HASH_MATCHES_MANIFEST" == "PASS" && \
  "$GATE_LEDGER_BUNDLE_MATCHES_MANIFEST" == "PASS" && \
  "$GATE_LEDGER_CERTIFICATE_MATCHES_MANIFEST" == "PASS" && \
  "$GATE_LEDGER_SUBORDINATED_TO_MANIFEST" == "PASS" && \
  "$GATE_ACTIVE_LINK_PRESENT" == "PASS" && \
  "$GATE_ACTIVE_LINK_MATCHES_TARGET" == "PASS" && \
  "$GATE_ACTIVE_RELEASE_EXISTS" == "PASS" && \
  "$GATE_ACTIVE_PUBLICATION_STATE" == "PASS" && \
  "$GATE_ACTIVE_BUNDLE_MATCHES_SOURCE" == "PASS" && \
  "$GATE_ACTIVE_CERTIFICATE_MATCHES_SOURCE" == "PASS" && \
  "$GATE_ACTIVE_MANIFEST_MATCHES_SOURCE" == "PASS" && \
  "$GATE_ZERO_ACTIVE_SUPERSEDED_REFERENCES" == "PASS" && \
  "$GATE_NO_STALE_PUBLIC_POINTER_CACHE" == "PASS" && \
  "$GATE_VERIFY_CLOSURE_INTEGRITY" == "PASS" ]]; then
  VERIFIED_PACK_STATE="ACTIVE_CANONICAL"
else
  VERIFIED_PACK_STATE="NOT_VERIFIED"
fi

if [[ "$GATE_RUN_PRODUCTION_READINESS" == "PASS" && "$GATE_NO_DUAL_PUBLICATION_EFFECTIVE" == "PASS" && "$GATE_NO_STALE_PUBLIC_POINTER_CACHE" == "PASS" && "$GATE_PERIODIC_AUDIT_WORKFLOW_SCHEDULED" == "PASS" ]]; then
  VERIFIED_OPERATIONAL_READINESS="$READINESS_STATUS"
else
  VERIFIED_OPERATIONAL_READINESS="NOT_VERIFIED"
fi

if [[ "$GATE_EXTERNAL_ANCHOR_HARDENING_VERIFIED" == "PASS" ]]; then
  VERIFIED_EXTERNAL_ANCHOR_STATE="ANCHOR_HARDENING_ENABLED"
else
  VERIFIED_EXTERNAL_ANCHOR_STATE="NOT_VERIFIED"
fi

if [[ "$GATE_ACTIVE_PUBLICATION_STATE" == "PASS" && "$GATE_NO_DUAL_PUBLICATION_EFFECTIVE" == "PASS" && "$GATE_NO_STALE_PUBLIC_POINTER_CACHE" == "PASS" ]]; then
  VERIFIED_PUBLICATION_STATE="ACTIVE_CANONICAL"
else
  VERIFIED_PUBLICATION_STATE="NOT_VERIFIED"
fi

if [[ "$VERIFIED_PACK_STATE" == "ACTIVE_CANONICAL" && "$VERIFIED_OPERATIONAL_READINESS" != "NOT_VERIFIED" ]]; then
  INTERNAL_CLOSURE_STATUS="INTERNAL_CLOSED"
elif [[ "$VERIFIED_PACK_STATE" == "ACTIVE_CANONICAL" ]]; then
  INTERNAL_CLOSURE_STATUS="INTERNAL_PARTIAL"
else
  INTERNAL_CLOSURE_STATUS="INTERNAL_BLOCKED"
fi

if [[ "$VERIFIED_EXTERNAL_ANCHOR_STATE" == "ANCHOR_HARDENING_ENABLED" ]]; then
  EXTERNAL_PROJECTION_STATUS="EXTERNAL_READY_FOR_LIVE_CONVERGENCE"
else
  EXTERNAL_PROJECTION_STATUS="EXTERNAL_NOT_READY"
fi

OBSERVED_OFFICIAL_OPERATIONAL_STATUS="$(json_get_or_default "$OFFICIAL_OPERATIONAL_STATUS_PATH" "officialOperationalStatus" "NOT_COMPUTED")"
if [[ -z "$OBSERVED_OFFICIAL_OPERATIONAL_STATUS" || "$OBSERVED_OFFICIAL_OPERATIONAL_STATUS" == "NOT_COMPUTED" || "$OBSERVED_OFFICIAL_OPERATIONAL_STATUS" == "null" ]]; then
  OBSERVED_OFFICIAL_OPERATIONAL_STATUS="$(json_get_or_default "$OFFICIAL_OPERATIONAL_STATUS_PATH" "officialStatus" "NOT_COMPUTED")"
fi
OBSERVED_OFFICIAL_REASON="$(json_get_or_default "$OFFICIAL_OPERATIONAL_STATUS_PATH" "reason" "NOT_COMPUTED")"
OBSERVED_INTERNAL_CLOSURE_STATUS="$(json_get_or_default "$OFFICIAL_OPERATIONAL_STATUS_PATH" "internalClosureStatus" "NOT_COMPUTED")"
OBSERVED_EXTERNAL_PROJECTION_STATUS="$(json_get_or_default "$OFFICIAL_OPERATIONAL_STATUS_PATH" "externalProjectionStatus" "NOT_COMPUTED")"
LEGACY_CERTIFICATE_STATUS="$(json_get_or_default "$LEGACY_RELEASE_CERTIFICATE" "certificate_status" "NOT_PRESENT")"
LEGACY_DECISION_MODE="$(json_get_or_default "$LEGACY_RELEASE_CERTIFICATE" "decision_mode" "NOT_PRESENT")"
LEGACY_HUMAN_APPROVAL_EVIDENCE_PRESENT="$(gate_if test -f "$LEGACY_HUMAN_APPROVAL_ARTIFACT_PATH")"
ACTIVE_HUMAN_APPROVAL_EVIDENCE_PRESENT="$(gate_if test -f "$ACTIVE_HUMAN_APPROVAL_ARTIFACT_PATH")"
GATE_PQ_RUNTIME_SECRET_PROTECTION_PRESENT="$(gate_if test -f "$PQ_RUNTIME_SECRET_PROTECTION_PATH")"

if [[ "$GATE_PQ_RUNTIME_SECRET_PROTECTION_PRESENT" == "PASS" ]]; then
  PQ_RUNTIME_SECRET_PROTECTION_STATUS="$(json_get_or_default "$PQ_RUNTIME_SECRET_PROTECTION_PATH" "status" "UNKNOWN")"
  PQ_RUNTIME_SECRET_PROTECTION_PROTECTOR="$(json_get_or_default "$PQ_RUNTIME_SECRET_PROTECTION_PATH" "protector" "UNKNOWN")"
  PQ_RUNTIME_SECRET_PROTECTION_EVIDENCE_REF="$(json_get_or_default "$PQ_RUNTIME_SECRET_PROTECTION_PATH" "evidence_ref" "UNKNOWN")"
else
  PQ_RUNTIME_SECRET_PROTECTION_STATUS="UNAVAILABLE_IN_CURRENT_RUNTIME"
  PQ_RUNTIME_SECRET_PROTECTION_PROTECTOR="UNKNOWN"
  PQ_RUNTIME_SECRET_PROTECTION_EVIDENCE_REF="UNKNOWN"
fi

CONSTITUTIONAL_EVIDENCE_CEILING_PATH="${RESULTS_DIR}/constitutional_evidence_ceiling.json"
GATE_EVIDENCE_CEILING_PRESENT="$(gate_if test -f "$CONSTITUTIONAL_EVIDENCE_CEILING_PATH")"

if [[ "$GATE_EVIDENCE_CEILING_PRESENT" == "PASS" ]]; then
  EVIDENCE_CLAIM_LEVEL="$(json_get_or_default "$CONSTITUTIONAL_EVIDENCE_CEILING_PATH" "claim_level_ceiling" "UNKNOWN")"
  EVIDENCE_CONFIDENCE="$(json_get_or_default "$CONSTITUTIONAL_EVIDENCE_CEILING_PATH" "confidence" "0.0")"
  EVIDENCE_MODE="$(json_get_or_default "$CONSTITUTIONAL_EVIDENCE_CEILING_PATH" "evidence_mode" "UNKNOWN")"
  EVIDENCE_MECHANICAL_ETHICS_STATUS="$(json_get_or_default "$CONSTITUTIONAL_EVIDENCE_CEILING_PATH" "mechanical_ethics_status" "UNKNOWN")"
  EVIDENCE_ELIGIBLE_L4="$(json_get_or_default "$CONSTITUTIONAL_EVIDENCE_CEILING_PATH" "eligible_for_l4" "false")"
  EVIDENCE_ELIGIBLE_L5="$(json_get_or_default "$CONSTITUTIONAL_EVIDENCE_CEILING_PATH" "eligible_for_l5" "false")"
else
  EVIDENCE_CLAIM_LEVEL="NOT_COMPUTED"
  EVIDENCE_CONFIDENCE="0.0"
  EVIDENCE_MODE="UNKNOWN"
  EVIDENCE_MECHANICAL_ETHICS_STATUS="UNKNOWN"
  EVIDENCE_ELIGIBLE_L4="false"
  EVIDENCE_ELIGIBLE_L5="false"
fi

mkdir -p "$RESULTS_DIR"

write_gate_report() {
  cat > "${RESULTS_DIR}/GATE_REPORT.json" <<EOF
{
  "artifactType": "mixed_audience_gate_report",
  "generatedAt": "${GENERATED_AT}",
  "policyVersion": "${GATE_POLICY_VERSION}",
  "stateTaxonomyVersion": "${STATE_TAXONOMY_VERSION}",
  "runContext": {
    "runId": "${RUN_ID}",
    "releaseId": "${RELEASE_ID}",
    "verificationEpoch": "${VERIFICATION_EPOCH}"
  },
  "packageId": "${PACKAGE_ID}",
  "declaredState": {
    "packState": "${DECLARED_PACK_STATE}",
    "externalAnchorState": "${DECLARED_EXTERNAL_ANCHOR_STATE}",
    "operationalReadinessClaim": "${DECLARED_OPERATIONAL_READINESS}",
    "publicationState": "${DECLARED_PUBLICATION_STATE}"
  },
  "verifiedState": {
    "packState": "${VERIFIED_PACK_STATE}",
    "externalAnchorState": "${VERIFIED_EXTERNAL_ANCHOR_STATE}",
    "operationalReadiness": "${VERIFIED_OPERATIONAL_READINESS}",
    "publicationState": "${VERIFIED_PUBLICATION_STATE}",
    "internalClosureStatus": "${INTERNAL_CLOSURE_STATUS}",
    "externalProjectionStatus": "${EXTERNAL_PROJECTION_STATUS}"
  },
  "stateModel": {
    "model": "SOVEREIGN_INTERNAL_CLOSURE_PLUS_EXTERNAL_PROJECTION_V1",
    "internalClosureStatus": "${INTERNAL_CLOSURE_STATUS}",
    "externalProjectionStatus": "${EXTERNAL_PROJECTION_STATUS}",
    "operationalTruthStatus": "${OBSERVED_OFFICIAL_OPERATIONAL_STATUS}",
    "canonicalIntegrityStatus": "${VERIFIED_PACK_STATE}",
    "externalAssuranceStatus": "${VERIFIED_EXTERNAL_ANCHOR_STATE}",
    "deploymentAuthorizationStatus": "${VERIFIED_OPERATIONAL_READINESS}",
    "officialOperationalStatusObserved": "${OBSERVED_OFFICIAL_OPERATIONAL_STATUS}",
    "officialReasonObserved": "${OBSERVED_OFFICIAL_REASON}",
    "officialStatePath": "artifacts/history/swarm/official_operational_status.json",
    "officialInternalClosureStatusObserved": "${OBSERVED_INTERNAL_CLOSURE_STATUS}",
    "officialExternalProjectionStatusObserved": "${OBSERVED_EXTERNAL_PROJECTION_STATUS}"
  },
  "runtimeSecretProtection": {
    "path": "results/pq_runtime_secret_protection.json",
    "present": "${GATE_PQ_RUNTIME_SECRET_PROTECTION_PRESENT}",
    "status": "${PQ_RUNTIME_SECRET_PROTECTION_STATUS}",
    "protector": "${PQ_RUNTIME_SECRET_PROTECTION_PROTECTOR}",
    "evidenceRef": "${PQ_RUNTIME_SECRET_PROTECTION_EVIDENCE_REF}"
  },
  "evidenceLevel": {
    "path": "results/constitutional_evidence_ceiling.json",
    "present": "${GATE_EVIDENCE_CEILING_PRESENT}",
    "claimLevelCeiling": "${EVIDENCE_CLAIM_LEVEL}",
    "confidence": ${EVIDENCE_CONFIDENCE},
    "evidenceMode": "${EVIDENCE_MODE}",
    "mechanicalEthicsStatus": "${EVIDENCE_MECHANICAL_ETHICS_STATUS}",
    "eligibleForL4": ${EVIDENCE_ELIGIBLE_L4},
    "eligibleForL5": ${EVIDENCE_ELIGIBLE_L5}
  },
  "gates": {
    "requiredComponentsPresent": "${GATE_REQUIRED_COMPONENTS}",
    "manifestActiveState": "${GATE_MANIFEST_ACTIVE_STATE}",
    "bundleHashMatchesManifest": "${GATE_BUNDLE_HASH_MATCHES_MANIFEST}",
    "certificateHashMatchesManifest": "${GATE_CERTIFICATE_HASH_MATCHES_MANIFEST}",
    "ledgerBundleMatchesManifest": "${GATE_LEDGER_BUNDLE_MATCHES_MANIFEST}",
    "ledgerCertificateMatchesManifest": "${GATE_LEDGER_CERTIFICATE_MATCHES_MANIFEST}",
    "ledgerSubordinatedToManifest": "${GATE_LEDGER_SUBORDINATED_TO_MANIFEST}",
    "publicationActiveLinkPresent": "${GATE_ACTIVE_LINK_PRESENT}",
    "publicationActiveLinkMatchesTarget": "${GATE_ACTIVE_LINK_MATCHES_TARGET}",
    "activeReleaseExists": "${GATE_ACTIVE_RELEASE_EXISTS}",
    "publicationStateActiveCanonical": "${GATE_ACTIVE_PUBLICATION_STATE}",
    "activeBundleMatchesSource": "${GATE_ACTIVE_BUNDLE_MATCHES_SOURCE}",
    "activeCertificateMatchesSource": "${GATE_ACTIVE_CERTIFICATE_MATCHES_SOURCE}",
    "activeManifestMatchesSource": "${GATE_ACTIVE_MANIFEST_MATCHES_SOURCE}",
    "zeroActiveSupersededReferences": "${GATE_ZERO_ACTIVE_SUPERSEDED_REFERENCES}",
    "noDualPublicationEffective": "${GATE_NO_DUAL_PUBLICATION_EFFECTIVE}",
    "noStalePublicPointerCache": "${GATE_NO_STALE_PUBLIC_POINTER_CACHE}",
    "periodicAuditWorkflowScheduled": "${GATE_PERIODIC_AUDIT_WORKFLOW_SCHEDULED}",
    "verifyClosureIntegrity": "${GATE_VERIFY_CLOSURE_INTEGRITY}",
    "runProductionReadiness": "${GATE_RUN_PRODUCTION_READINESS}",
    "declaredOperationalReadinessPresent": "${DECLARED_OPERATIONAL_READINESS_PRESENT}",
    "anchorHardeningStatusArtifactPresent": "${GATE_ANCHOR_STATUS_ARTIFACT_PRESENT}",
    "independentExternalReverificationArtifactPresent": "${GATE_INDEPENDENT_REVERIFICATION_ARTIFACT_PRESENT}",
    "anchorHardeningDeclared": "${GATE_ANCHOR_HARDENING_DECLARED}",
    "externalTriplePublicAnchorReconciled": "${GATE_EXTERNAL_TRIPLE_ANCHOR_RECONCILED}",
    "externalNoUnresolvedAnchorConflicts": "${GATE_EXTERNAL_NO_UNRESOLVED_CONFLICTS}",
    "externalZeroPublicationDrift": "${GATE_EXTERNAL_ZERO_PUBLICATION_DRIFT}",
    "externalIndependentReverification": "${GATE_EXTERNAL_INDEPENDENT_REVERIFICATION}",
    "externalAnchorHardeningVerified": "${GATE_EXTERNAL_ANCHOR_HARDENING_VERIFIED}"
  },
  "rawOutputs": {
    "verifyClosureIntegrity": ${VERIFY_OUTPUT_JSON},
    "runProductionReadiness": ${READINESS_OUTPUT_JSON}
  },
  "rawExitCodes": {
    "verifyClosureIntegrity": ${VERIFY_EXIT_CODE},
    "runProductionReadiness": ${READINESS_EXIT_CODE}
  }
}
EOF
}

write_public() {
  cat > "${RESULTS_DIR}/public_summary.md" <<EOF
# Public Summary

Generated At: ${GENERATED_AT}
Package ID: ${PACKAGE_ID}
Declared Pack State: ${DECLARED_PACK_STATE}
Verified Pack State: ${VERIFIED_PACK_STATE}
Declared External Anchor State: ${DECLARED_EXTERNAL_ANCHOR_STATE}
Verified External Anchor State: ${VERIFIED_EXTERNAL_ANCHOR_STATE}
Verified Operational Readiness: ${VERIFIED_OPERATIONAL_READINESS}
Periodic Audit Workflow Scheduled: ${GATE_PERIODIC_AUDIT_WORKFLOW_SCHEDULED}
Verified Publication State: ${VERIFIED_PUBLICATION_STATE}
Active Target: ${ACTIVE_TARGET}
Canonical Lineage: ${CANONICAL_LINEAGE}
Gate Report: results/GATE_REPORT.json

This artifact exposes one active canonical truth chain and separates declared labels from verified gate outcomes.

What it proves visibly:

- the active bundle, certificate, manifest and ledger align by hash
- the frozen publication target matches the active release pointer
- the promoted lineage is ${CANONICAL_LINEAGE}
- the external anchor layer is only treated as verified when the hardening gates pass

Boundary statement (historical package and claims):

- ${LEGACY_RELEASE_PATH}/ is preserved as historical release evidence, not as a standalone final authority
- observed legacy certificate fields are certificate_status=${LEGACY_CERTIFICATE_STATUS} and decision_mode=${LEGACY_DECISION_MODE}
- a legacy certificate field alone is not sufficient to sustain "remediated release final" or "explicit human approval evidence" claims
- explicit human approval evidence is only treated as supportable when the active artifact is present and gates pass
- legacy human approval artifact present: ${LEGACY_HUMAN_APPROVAL_EVIDENCE_PRESENT}; active human approval artifact present: ${ACTIVE_HUMAN_APPROVAL_EVIDENCE_PRESENT}
EOF
}

write_technical() {
  cat > "${RESULTS_DIR}/technical_verification.md" <<EOF
# Technical Verification

Generated At: ${GENERATED_AT}
Package ID: ${PACKAGE_ID}
Declared Pack State: ${DECLARED_PACK_STATE}
Verified Pack State: ${VERIFIED_PACK_STATE}
Declared External Anchor State: ${DECLARED_EXTERNAL_ANCHOR_STATE}
Verified External Anchor State: ${VERIFIED_EXTERNAL_ANCHOR_STATE}
Verified Operational Readiness: ${VERIFIED_OPERATIONAL_READINESS}
Verified Publication State: ${VERIFIED_PUBLICATION_STATE}
Internal Closure Status (Gate-Derived): ${INTERNAL_CLOSURE_STATUS}
External Projection Status (Gate-Derived): ${EXTERNAL_PROJECTION_STATUS}
Official Operational Status (Observed): ${OBSERVED_OFFICIAL_OPERATIONAL_STATUS}
Official Reason (Observed): ${OBSERVED_OFFICIAL_REASON}
Official Internal Closure Status (Observed): ${OBSERVED_INTERNAL_CLOSURE_STATUS}
Official External Projection Status (Observed): ${OBSERVED_EXTERNAL_PROJECTION_STATUS}
Official Status Path: artifacts/history/swarm/official_operational_status.json
Active Target: ${ACTIVE_TARGET}
Canonical Lineage: ${CANONICAL_LINEAGE}
Bundle Hash: ${MANIFEST_BUNDLE_HASH}
Certificate Hash: ${MANIFEST_CERTIFICATE_HASH}
case_003 Anchor Tx: ${CASE003_TX_HASH}
Gate Report: results/GATE_REPORT.json

Observed command outputs:

\`\`\`text
${VERIFY_OUTPUT}
${READINESS_OUTPUT}
\`\`\`

Technical interpretation:

- fail-closed integrity is treated as verified only when the gate report passes the material chain checks
- operational readiness is reported as verified from script output, not from a packaging label
- external anchor hardening is separated into declared and verified layers
EOF
}

write_legal() {
  cat > "${RESULTS_DIR}/legal_claim_boundary.md" <<EOF
# Legal Claim Boundary

Generated At: ${GENERATED_AT}
Package ID: ${PACKAGE_ID}
Declared Pack State: ${DECLARED_PACK_STATE}
Verified Pack State: ${VERIFIED_PACK_STATE}
Declared External Anchor State: ${DECLARED_EXTERNAL_ANCHOR_STATE}
Verified External Anchor State: ${VERIFIED_EXTERNAL_ANCHOR_STATE}
Declared Operational Readiness Claim: ${DECLARED_OPERATIONAL_READINESS}
Verified Operational Readiness: ${VERIFIED_OPERATIONAL_READINESS}
Gate Report: results/GATE_REPORT.json

Allowed claims:

${ALLOWED_CLAIMS}

Forbidden claims:

${FORBIDDEN_CLAIMS}

Legal interpretation:

- the package distinguishes declared states from verified states
- no higher claim should rely on declaration alone when the corresponding verified state is not established
- the gate report is the operative support layer for material and external-anchor assertions

Historical-package legal boundary:

- historical release snapshot path: ${LEGACY_RELEASE_PATH}/
- standalone claim "remediated release final" from that historical snapshot is forbidden without current gate convergence
- standalone claim "explicit human approval evidence" from legacy certificate fields is forbidden when the legacy human approval artifact is missing
- operative support for human-required closure remains tied to the active artifact and current gate report
- legacy human approval artifact present: ${LEGACY_HUMAN_APPROVAL_EVIDENCE_PRESENT}; active human approval artifact present: ${ACTIVE_HUMAN_APPROVAL_EVIDENCE_PRESENT}
EOF
}

write_regulatory() {
  cat > "${RESULTS_DIR}/regulatory_control_report.md" <<EOF
# Regulatory Control Report

Generated At: ${GENERATED_AT}
Package ID: ${PACKAGE_ID}
Declared Pack State: ${DECLARED_PACK_STATE}
Verified Pack State: ${VERIFIED_PACK_STATE}
Declared External Anchor State: ${DECLARED_EXTERNAL_ANCHOR_STATE}
Verified External Anchor State: ${VERIFIED_EXTERNAL_ANCHOR_STATE}
Verified Operational Readiness: ${VERIFIED_OPERATIONAL_READINESS}
Verified Publication State: ${VERIFIED_PUBLICATION_STATE}
Active Target: ${ACTIVE_TARGET}
Canonical Lineage: ${CANONICAL_LINEAGE}
Anchor Hardening Status Artifact: ${ANCHOR_HARDENING_STATUS_REL}
Independent Reverification Artifact: ${INDEPENDENT_REVERIFICATION_REL}
Gate Report: results/GATE_REPORT.json

Control interpretation:

- the package exposes gate-by-gate outcomes instead of relying only on inherited labels
- the material chain and active publication target can be checked locally
- the external anchor layer is only elevated after the declared and verified controls converge
EOF
}

write_finance() {
  cat > "${RESULTS_DIR}/finance_anchor_report.md" <<EOF
# Finance And Anchor Report

Generated At: ${GENERATED_AT}
Package ID: ${PACKAGE_ID}
Canonical Lineage: ${CANONICAL_LINEAGE}
Declared External Anchor State: ${DECLARED_EXTERNAL_ANCHOR_STATE}
Verified External Anchor State: ${VERIFIED_EXTERNAL_ANCHOR_STATE}
Verified Pack State: ${VERIFIED_PACK_STATE}
case_003 Anchor Tx: ${CASE003_TX_HASH}
Bundle Hash: ${MANIFEST_BUNDLE_HASH}
Certificate Hash: ${MANIFEST_CERTIFICATE_HASH}
Gate Report: results/GATE_REPORT.json

Finance and crypto interpretation:

- deterministic hashes are exposed for the active chain
- the external anchor state is separated into declared and verified views
- the package is suitable for independent checking without relying on the mutable source repository
EOF
}

write_executive() {
  cat > "${RESULTS_DIR}/executive_onepager.md" <<EOF
# Executive One-Pager

Generated At: ${GENERATED_AT}
Package ID: ${PACKAGE_ID}

Declared states:

- Pack: ${DECLARED_PACK_STATE}
- External anchor: ${DECLARED_EXTERNAL_ANCHOR_STATE}
- Operational readiness claim: ${DECLARED_OPERATIONAL_READINESS}
- Publication: ${DECLARED_PUBLICATION_STATE}

Verified states:

- Pack: ${VERIFIED_PACK_STATE}
- External anchor: ${VERIFIED_EXTERNAL_ANCHOR_STATE}
- Operational readiness: ${VERIFIED_OPERATIONAL_READINESS}
- Publication: ${VERIFIED_PUBLICATION_STATE}
- Active target: ${ACTIVE_TARGET}
- Canonical lineage: ${CANONICAL_LINEAGE}

Executive takeaway:

This artifact now shows a clean distinction between what the pack declares and what the gate report verifies from the material chain, publication snapshot and external anchor evidence.
EOF
}

write_index() {
  cat > "${RESULTS_DIR}/index.json" <<EOF
{
  "artifactType": "mixed_audience_audit_results_index",
  "generatedAt": "${GENERATED_AT}",
  "policyVersion": "${GATE_POLICY_VERSION}",
  "stateTaxonomyVersion": "${STATE_TAXONOMY_VERSION}",
  "runContext": {
    "runId": "${RUN_ID}",
    "releaseId": "${RELEASE_ID}",
    "verificationEpoch": "${VERIFICATION_EPOCH}"
  },
  "packageId": "${PACKAGE_ID}",
  "declaredState": {
    "packState": "${DECLARED_PACK_STATE}",
    "externalAnchorState": "${DECLARED_EXTERNAL_ANCHOR_STATE}",
    "operationalReadinessClaim": "${DECLARED_OPERATIONAL_READINESS}",
    "publicationState": "${DECLARED_PUBLICATION_STATE}"
  },
  "verifiedState": {
    "packState": "${VERIFIED_PACK_STATE}",
    "externalAnchorState": "${VERIFIED_EXTERNAL_ANCHOR_STATE}",
    "operationalReadiness": "${VERIFIED_OPERATIONAL_READINESS}",
    "publicationState": "${VERIFIED_PUBLICATION_STATE}",
    "internalClosureStatus": "${INTERNAL_CLOSURE_STATUS}",
    "externalProjectionStatus": "${EXTERNAL_PROJECTION_STATUS}"
  },
  "stateModel": {
    "model": "SOVEREIGN_INTERNAL_CLOSURE_PLUS_EXTERNAL_PROJECTION_V1",
    "internalClosureStatus": "${INTERNAL_CLOSURE_STATUS}",
    "externalProjectionStatus": "${EXTERNAL_PROJECTION_STATUS}",
    "operationalTruthStatus": "${OBSERVED_OFFICIAL_OPERATIONAL_STATUS}",
    "canonicalIntegrityStatus": "${VERIFIED_PACK_STATE}",
    "externalAssuranceStatus": "${VERIFIED_EXTERNAL_ANCHOR_STATE}",
    "deploymentAuthorizationStatus": "${VERIFIED_OPERATIONAL_READINESS}",
    "officialOperationalStatusObserved": "${OBSERVED_OFFICIAL_OPERATIONAL_STATUS}",
    "officialReasonObserved": "${OBSERVED_OFFICIAL_REASON}",
    "officialStatePath": "artifacts/history/swarm/official_operational_status.json"
  },
  "gateReportPath": "results/GATE_REPORT.json",
  "activeTarget": "${ACTIVE_TARGET}",
  "canonicalLineage": "${CANONICAL_LINEAGE}",
  "officialStates": [
$(printf '%s\n' "$OFFICIAL_STATES" | awk 'NF {printf "    \"%s\",\n", $0}' | sed '$ s/,$//')
  ],
  "generatedResults": [
$(for path in GATE_REPORT.json public_summary.md technical_verification.md legal_claim_boundary.md regulatory_control_report.md finance_anchor_report.md executive_onepager.md; do
    if [[ -f "${RESULTS_DIR}/${path}" ]]; then
      printf '    "%s",\n' "$path"
    fi
  done | sed '$ s/,$//')
  ]
}
EOF
}

write_gate_report
matches_profile public && write_public
matches_profile technical && write_technical
matches_profile legal && write_legal
matches_profile regulatory && write_regulatory
matches_profile finance && write_finance
matches_profile executive && write_executive
write_index

printf 'RESULTS_DIR=%s\n' "$RESULTS_DIR"
find "$RESULTS_DIR" -maxdepth 1 -type f | sort

echo "=== EJECUTANDO AUDITORÍA DE ÉTICA MECÁNICA ==="

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ETHIC_AUDIT_SCRIPT="$ROOT_DIR/scripts/audit/audit_ethic_mechanics.sh"

if [ ! -f "$ETHIC_AUDIT_SCRIPT" ]; then
    echo "ERROR: No se encontró $ETHIC_AUDIT_SCRIPT"
    exit 2
fi

bash "$ETHIC_AUDIT_SCRIPT" || {
    echo "AUDITORÍA DE ÉTICA MECÁNICA FALLIDA"
    echo "Se detectó incumplimiento de regla CRITICAL (FAIL_CLOSED)"
    echo "El proceso se detiene por violación ética grave"
    exit 1
}

echo "AUDITORÍA DE ÉTICA MECÁNICA: PASS"
echo "==============================================================================="
