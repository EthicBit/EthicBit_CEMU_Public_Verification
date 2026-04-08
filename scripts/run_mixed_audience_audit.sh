#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${ROOT_DIR:-$(cd -- "${SCRIPT_DIR}/.." && pwd)}"
RESULTS_DIR="${ROOT_DIR}/results"
PROFILE="all"
JSON_QUERY_SCRIPT="${ROOT_DIR}/scripts/json_query.py"

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

VERIFY_OUTPUT="$("$VERIFY_SCRIPT" "$ROOT_DIR")"
READINESS_OUTPUT="$("$READINESS_SCRIPT" "$ROOT_DIR" "${ROOT_DIR}/publication")"

VERIFY_STATUS="$(printf '%s\n' "$VERIFY_OUTPUT" | tail -n 1)"
READINESS_STATUS="$(printf '%s\n' "$READINESS_OUTPUT" | tail -n 1)"
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
DECLARED_CERTIFICATE_STATES="$(json_get_or_default "$CERTIFICATE" "declaredStates" "READY_FOR_CONTROLLED_PRODUCTION_CANDIDATE")"
ANCHOR_HARDENING_STATUS_REL="$(json_get_or_default "$BUNDLE" "externalAnchorEvidence.swarmMvpV1.anchorHardeningStatusPath" "artifacts/history/swarm/anchor_hardening_status.swarm_mvp_v1.json")"
INDEPENDENT_REVERIFICATION_REL="$(json_get_or_default "$BUNDLE" "externalAnchorEvidence.swarmMvpV1.independentExternalReverificationArtifactPath" "artifacts/history/swarm/independent_external_anchor_reverification.swarm_mvp_v1.json")"
ANCHOR_HARDENING_STATUS_PATH="$(resolve_root_relative "$ANCHOR_HARDENING_STATUS_REL")"
INDEPENDENT_REVERIFICATION_PATH="$(resolve_root_relative "$INDEPENDENT_REVERIFICATION_REL")"
GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
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
GATE_RUN_PRODUCTION_READINESS="$(if [[ "$READINESS_STATUS" == "READY_FOR_CONTROLLED_PRODUCTION_CANDIDATE" ]]; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"

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

DECLARED_OPERATIONAL_READINESS_PRESENT="$(if contains_line "$DECLARED_CERTIFICATE_STATES" "READY_FOR_CONTROLLED_PRODUCTION_CANDIDATE"; then printf 'PASS\n'; else printf 'FAIL\n'; fi)"

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

if [[ "$GATE_RUN_PRODUCTION_READINESS" == "PASS" && "$GATE_NO_DUAL_PUBLICATION_EFFECTIVE" == "PASS" && "$GATE_NO_STALE_PUBLIC_POINTER_CACHE" == "PASS" ]]; then
  VERIFIED_OPERATIONAL_READINESS="READY_FOR_CONTROLLED_PRODUCTION_CANDIDATE"
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

mkdir -p "$RESULTS_DIR"

write_gate_report() {
  cat > "${RESULTS_DIR}/GATE_REPORT.json" <<EOF
{
  "artifactType": "mixed_audience_gate_report",
  "generatedAt": "${GENERATED_AT}",
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
    "publicationState": "${VERIFIED_PUBLICATION_STATE}"
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
    "publicationState": "${VERIFIED_PUBLICATION_STATE}"
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