#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${1:-$(cd -- "${SCRIPT_DIR}/.." && pwd)}"
ARTIFACTS_DIR="${ROOT_DIR}/artifacts"
SCRIPTS_DIR="${ROOT_DIR}/scripts"
JSON_QUERY_SCRIPT="${SCRIPTS_DIR}/json_query.py"

BUNDLE="${ARTIFACTS_DIR}/security_incident_bundle_v1_0.json"
CERTIFICATE="${ARTIFACTS_DIR}/formal_closure_certificate_multicapa_v1_0.json"
MANIFEST="${ARTIFACTS_DIR}/artifact_manifest.json"
LEDGER="${ARTIFACTS_DIR}/ethicbit_closure_artifacts_hashes.json"
CASE003_MATERIAL_SCRIPT="${SCRIPTS_DIR}/verify_case003_material_integrity.sh"
IN_TOTO_LAYOUT="${ROOT_DIR}/assurance/in-toto/root.layout"
IN_TOTO_INDEX="${ROOT_DIR}/assurance/in-toto/attestation-index.json"
SLSA_L4_POLICY="${ROOT_DIR}/assurance/slsa/level4-policy.json"
SIGSTORE_POLICY="${ROOT_DIR}/assurance/sigstore/policy.json"
ATTESTATION_STATUS_CANONICAL="${ROOT_DIR}/artifacts/history/swarm/attestation_status.canonical.json"
NORMALIZE_ATTESTATION_STATUS_SCRIPT="${ROOT_DIR}/scripts/status/normalize_attestation_status_canonical.py"

fail() {
  local code="$1"
  shift
  printf '%s: %s\n' "$code" "$*" >&2
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

json_get_array_joined() {
  local file="$1"
  local path="$2"
  env -i PATH=/usr/bin:/bin HOME="${HOME:-$ROOT_DIR}" TMPDIR=/tmp /usr/bin/python3 -S "$JSON_QUERY_SCRIPT" "$file" "$path" --joined
}

require_file() {
  local path="$1"
  [[ -f "$path" ]] || fail "NOT_READY (FAIL-CLOSED)" "missing required component: ${path#${ROOT_DIR}/}"
}

ensure_required_components() {
  require_file "$BUNDLE"
  require_file "$CERTIFICATE"
  require_file "$MANIFEST"
  require_file "$LEDGER"
  require_file "$CASE003_MATERIAL_SCRIPT"
  require_file "${SCRIPTS_DIR}/verify_closure_integrity.sh"
  require_file "${SCRIPTS_DIR}/resolve_publication_drift.sh"
  require_file "${SCRIPTS_DIR}/publish-closure-atomic.sh"
  require_file "${SCRIPTS_DIR}/run_production_readiness.sh"
}

ensure_case003_material_integrity() {
  if ! "$CASE003_MATERIAL_SCRIPT" >/tmp/case003_material_integrity.out 2>/tmp/case003_material_integrity.err; then
    fail "NOT_READY (FAIL-CLOSED)" "case_003 material integrity gate failed"
  fi
}

ensure_assurance_layer_enforced() {
  require_file "$IN_TOTO_LAYOUT"
  require_file "$IN_TOTO_INDEX"
  require_file "$SLSA_L4_POLICY"
  require_file "$SIGSTORE_POLICY"
  require_file "$NORMALIZE_ATTESTATION_STATUS_SCRIPT"

  local layout_status index_status slsa_status sigstore_status
  local in_toto_all_steps in_toto_no_pending in_toto_required_status
  local sigstore_production_signing sigstore_allow_unsigned sigstore_hybrid_mode
  local slsa_attestation_required
  layout_status="$(json_get "$IN_TOTO_LAYOUT" "status")"
  index_status="$(json_get "$IN_TOTO_INDEX" "status")"
  slsa_status="$(json_get "$SLSA_L4_POLICY" "status")"
  sigstore_status="$(json_get "$SIGSTORE_POLICY" "status")"
  in_toto_all_steps="$(json_get "$IN_TOTO_INDEX" "verification.allStepsMustBeAttested")"
  in_toto_no_pending="$(json_get "$IN_TOTO_INDEX" "verification.noPendingAllowed")"
  in_toto_required_status="$(json_get "$IN_TOTO_INDEX" "verification.requiredStatementStatus")"
  sigstore_production_signing="$(json_get "$SIGSTORE_POLICY" "enforcement.production_signing_required")"
  sigstore_allow_unsigned="$(json_get "$SIGSTORE_POLICY" "enforcement.allow_unsigned_artifacts")"
  sigstore_hybrid_mode="$(json_get "$SIGSTORE_POLICY" "enforcement.hybrid_signature_required")"
  slsa_attestation_required="$(json_get "$SLSA_L4_POLICY" "enforcement.attestations_mandatory")"

  [[ "$layout_status" == "ENFORCED" ]] || fail "CRYPTO_POLICY_FAIL" "in-toto layout status must be ENFORCED"
  [[ "$index_status" == "ENFORCED" ]] || fail "CRYPTO_POLICY_FAIL" "in-toto attestation index status must be ENFORCED"
  [[ "$slsa_status" == "ENFORCED" ]] || fail "CRYPTO_POLICY_FAIL" "SLSA L4 policy status must be ENFORCED"
  [[ "$sigstore_status" == "ENFORCED" ]] || fail "CRYPTO_POLICY_FAIL" "sigstore policy status must be ENFORCED"
  [[ "$in_toto_all_steps" == "true" || "$in_toto_all_steps" == "True" ]] || fail "CRYPTO_POLICY_FAIL" "in-toto allStepsMustBeAttested must be true"
  [[ "$in_toto_no_pending" == "true" || "$in_toto_no_pending" == "True" ]] || fail "CRYPTO_POLICY_FAIL" "in-toto noPendingAllowed must be true"
  [[ "$in_toto_required_status" == "VERIFIED" ]] || fail "CRYPTO_POLICY_FAIL" "in-toto requiredStatementStatus must be VERIFIED"
  [[ "$sigstore_production_signing" == "true" || "$sigstore_production_signing" == "True" ]] || fail "CRYPTO_POLICY_FAIL" "sigstore production_signing_required must be true"
  [[ "$sigstore_allow_unsigned" == "false" || "$sigstore_allow_unsigned" == "False" ]] || fail "CRYPTO_POLICY_FAIL" "sigstore allow_unsigned_artifacts must be false"
  [[ "$sigstore_hybrid_mode" == "MODE_DRIVEN" ]] || fail "CRYPTO_POLICY_FAIL" "sigstore hybrid_signature_required must be MODE_DRIVEN"
  [[ "$slsa_attestation_required" == "true" || "$slsa_attestation_required" == "True" ]] || fail "CRYPTO_POLICY_FAIL" "slsa attestations_mandatory must be true"

  if grep -Eq 'PENDING_ATTESTATION|PLACEHOLDER|TODO' "$IN_TOTO_INDEX"; then
    fail "CRYPTO_POLICY_FAIL" "in-toto attestation index contains forbidden pending markers"
  fi

  if ! /usr/bin/python3 "$NORMALIZE_ATTESTATION_STATUS_SCRIPT" --root "$ROOT_DIR" --strict >/tmp/attestation_normalize.out 2>/tmp/attestation_normalize.err; then
    fail "CRYPTO_POLICY_FAIL" "canonical attestation normalization failed in strict mode"
  fi

  require_file "$ATTESTATION_STATUS_CANONICAL"

  local canonical_schema canonical_status canonical_gate_status canonical_slsa_status
  canonical_schema="$(json_get "$ATTESTATION_STATUS_CANONICAL" "schema_id")"
  canonical_status="$(json_get "$ATTESTATION_STATUS_CANONICAL" "status")"
  canonical_gate_status="$(json_get "$ATTESTATION_STATUS_CANONICAL" "gate.status")"
  canonical_slsa_status="$(json_get "$ATTESTATION_STATUS_CANONICAL" "slsaAssessment.status")"

  [[ "$canonical_schema" == "ETHICBIT_ATTESTATION_STATUS_CANONICAL_V1" ]] || fail "CRYPTO_POLICY_FAIL" "invalid canonical attestation schema_id"
  [[ "$canonical_status" == "VERIFIED" ]] || fail "CRYPTO_POLICY_FAIL" "canonical attestation status must be VERIFIED"
  [[ "$canonical_gate_status" == "PASS" ]] || fail "CRYPTO_POLICY_FAIL" "canonical attestation gate must be PASS"

  case "$canonical_slsa_status" in
    PASS_SLSA_FINAL|VERIFIED_REPRODUCIBLE|VERIFIED) ;;
    *) fail "CRYPTO_POLICY_FAIL" "canonical slsaAssessment.status is not an accepted final-equivalent status" ;;
  esac
}

ensure_no_known_competing_files() {
  local path
  for path in \
    "${ARTIFACTS_DIR}/security_incident_bundle_v1_0.superseded.json" \
    "${ARTIFACTS_DIR}/security_incident_bundle_v1_0.drifted.json" \
    "${ARTIFACTS_DIR}/formal_closure_certificate_multicapa_v1_0.superseded.json" \
    "${ARTIFACTS_DIR}/formal_closure_certificate_multicapa_v1_0.drifted.json" \
    "${ARTIFACTS_DIR}/artifact_manifest.superseded.json" \
    "${ARTIFACTS_DIR}/artifact_manifest.drifted.json" \
    "${ARTIFACTS_DIR}/ethicbit_closure_artifacts_hashes.superseded.json" \
    "${ARTIFACTS_DIR}/ethicbit_closure_artifacts_hashes.drifted.json"; do
    [[ ! -e "$path" ]] || fail "PUBLICATION_DRIFT_DETECTED" "competing active-path artifact detected: ${path#${ROOT_DIR}/}"
  done
}

ensure_manifest_shape() {
  local bundle_path certificate_path ledger_path active_state active_list

  bundle_path="$(json_get "$MANIFEST" "securityIncidentBundle.path")"
  certificate_path="$(json_get "$MANIFEST" "formalClosureCertificate.path")"
  ledger_path="$(json_get "$MANIFEST" "derivedLedger.path")"
  active_state="$(json_get "$MANIFEST" "activePublication.state")"
  active_list="$(json_get_array_joined "$MANIFEST" "activePublication.activeSet")"

  [[ "$bundle_path" == "artifacts/security_incident_bundle_v1_0.json" ]] || fail "INVALID_ACTIVE_SOURCE" "manifest bundle path does not match the canonical active bundle path"
  [[ "$certificate_path" == "artifacts/formal_closure_certificate_multicapa_v1_0.json" ]] || fail "INVALID_ACTIVE_SOURCE" "manifest certificate path does not match the canonical active certificate path"
  [[ "$ledger_path" == "artifacts/ethicbit_closure_artifacts_hashes.json" ]] || fail "INVALID_ACTIVE_SOURCE" "manifest ledger path does not match the canonical active ledger path"
  [[ "$active_state" == "ACTIVE_CANONICAL" ]] || fail "INVALID_ACTIVE_SOURCE" "manifest activePublication.state must be ACTIVE_CANONICAL"

  local expected_active_set
  expected_active_set=$'artifacts/security_incident_bundle_v1_0.json\nartifacts/formal_closure_certificate_multicapa_v1_0.json\nartifacts/artifact_manifest.json\nartifacts/ethicbit_closure_artifacts_hashes.json'
  [[ "$active_list" == "$expected_active_set" ]] || fail "INVALID_ACTIVE_SOURCE" "manifest active set differs from the canonical active chain"
}

ensure_hash_alignment() {
  local actual_bundle_hash actual_certificate_hash manifest_bundle_hash manifest_certificate_hash ledger_bundle_hash ledger_certificate_hash ledger_manifest_path

  actual_bundle_hash="$(sha256_file "$BUNDLE")"
  actual_certificate_hash="$(sha256_file "$CERTIFICATE")"
  manifest_bundle_hash="$(json_get "$MANIFEST" "securityIncidentBundle.hash")"
  manifest_certificate_hash="$(json_get "$MANIFEST" "formalClosureCertificate.hash")"
  ledger_bundle_hash="$(json_get "$LEDGER" "bundleHash")"
  ledger_certificate_hash="$(json_get "$LEDGER" "certificateHash")"
  ledger_manifest_path="$(json_get "$LEDGER" "derivedFrom.manifestPath")"

  [[ "$actual_bundle_hash" == "$manifest_bundle_hash" ]] || fail "PUBLICATION_DRIFT_DETECTED" "bundle hash mismatch between material root and manifest"
  [[ "$actual_certificate_hash" == "$manifest_certificate_hash" ]] || fail "PUBLICATION_DRIFT_DETECTED" "certificate hash mismatch between formal act and manifest"
  [[ "$actual_bundle_hash" == "$ledger_bundle_hash" ]] || fail "INVALID_ACTIVE_SOURCE" "bundle hash mismatch between manifest-driven chain and derived ledger"
  [[ "$actual_certificate_hash" == "$ledger_certificate_hash" ]] || fail "INVALID_ACTIVE_SOURCE" "certificate hash mismatch between manifest-driven chain and derived ledger"
  [[ "$ledger_manifest_path" == "artifacts/artifact_manifest.json" ]] || fail "INVALID_ACTIVE_SOURCE" "derived ledger is not subordinated to artifacts/artifact_manifest.json"
}

ensure_zero_active_superseded_references() {
  local actual_bundle_hash actual_certificate_hash competing_path competing_hash

  actual_bundle_hash="$(sha256_file "$BUNDLE")"
  actual_certificate_hash="$(sha256_file "$CERTIFICATE")"

  local active_paths
  active_paths=$(
    printf '%s\n' \
      "$(json_get "$MANIFEST" "securityIncidentBundle.path")" \
      "$(json_get "$MANIFEST" "formalClosureCertificate.path")" \
      "$(json_get "$MANIFEST" "derivedLedger.path")" \
      "$(json_get "$LEDGER" "derivedFrom.manifestPath")"
  )

  if printf '%s\n' "$active_paths" | grep -Eq '\.(superseded|drifted)\.'; then
    fail "INVALID_ACTIVE_SOURCE" "active chain references a superseded or drifted path"
  fi

  local glob
  for glob in "$ARTIFACTS_DIR"/*.superseded.json "$ARTIFACTS_DIR"/*.drifted.json; do
    [[ -e "$glob" ]] || continue
    competing_path="$glob"
    competing_hash="$(sha256_file "$competing_path")"
    [[ "$competing_hash" != "$actual_bundle_hash" ]] || fail "INVALID_ACTIVE_SOURCE" "active bundle hash matches a superseded or drifted artifact"
    [[ "$competing_hash" != "$actual_certificate_hash" ]] || fail "INVALID_ACTIVE_SOURCE" "active certificate hash matches a superseded or drifted artifact"
  done
}

ensure_freeze_is_not_active() {
  local freeze_marker="${ARTIFACTS_DIR}/runtime/publication_freeze_state.json"
  [[ ! -f "$freeze_marker" ]] || fail "PUBLICATION_FREEZE_ACTIVE" "freeze marker is active; publication is intentionally blocked until remediation completes"
}

ensure_publication_pointer_if_present() {
  local publication_root="${ROOT_DIR}/publication"
  local active_link="${publication_root}/active"
  local publication_state="${publication_root}/publication_state.json"

  [[ -d "$publication_root" ]] || return 0
  [[ -e "$active_link" ]] || return 0
  [[ -L "$active_link" ]] || fail "PUBLICATION_DRIFT_DETECTED" "publication/active exists but is not a symlink, so atomic publication cannot be trusted"
  [[ -f "$publication_state" ]] || fail "PUBLICATION_DRIFT_DETECTED" "publication_state.json is missing while an active publication pointer exists"

  local active_dir active_target stated_target stated_state stated_published_at
  active_dir="$(cd -P -- "$active_link" && pwd)"
  [[ -d "$active_dir" ]] || fail "PUBLICATION_DRIFT_DETECTED" "publication/active points to a missing release directory"

  active_target="$(readlink "$active_link")"
  stated_target="$(json_get "$publication_state" "activeTarget")"
  stated_state="$(json_get "$publication_state" "state")"
  stated_published_at="$(json_get "$publication_state" "publishedAt")"

  [[ "$active_target" == "$stated_target" ]] || fail "PUBLICATION_DRIFT_DETECTED" "publication_state.json activeTarget does not match publication/active"
  [[ "$stated_state" == "ACTIVE_CANONICAL" ]] || fail "PUBLICATION_DRIFT_DETECTED" "publication_state.json state must be ACTIVE_CANONICAL when publication/active exists"
  [[ "$stated_published_at" != "null" && -n "$stated_published_at" ]] || fail "PUBLICATION_DRIFT_DETECTED" "publication_state.json publishedAt is empty or null"

  local source_manifest_hash source_bundle_hash source_certificate_hash active_manifest_hash active_bundle_hash active_certificate_hash
  source_manifest_hash="$(sha256_file "$MANIFEST")"
  source_bundle_hash="$(sha256_file "$BUNDLE")"
  source_certificate_hash="$(sha256_file "$CERTIFICATE")"
  active_manifest_hash="$(sha256_file "${active_dir}/artifacts/artifact_manifest.json")"
  active_bundle_hash="$(sha256_file "${active_dir}/artifacts/security_incident_bundle_v1_0.json")"
  active_certificate_hash="$(sha256_file "${active_dir}/artifacts/formal_closure_certificate_multicapa_v1_0.json")"

  [[ "$source_manifest_hash" == "$active_manifest_hash" ]] || fail "PUBLICATION_DRIFT_DETECTED" "publication/active manifest differs from the repository SSOT"
  [[ "$source_bundle_hash" == "$active_bundle_hash" ]] || fail "PUBLICATION_DRIFT_DETECTED" "publication/active bundle differs from the repository root material"
  [[ "$source_certificate_hash" == "$active_certificate_hash" ]] || fail "PUBLICATION_DRIFT_DETECTED" "publication/active certificate differs from the repository formal act"
}

main() {
  ensure_required_components
  ensure_case003_material_integrity
  ensure_assurance_layer_enforced
  ensure_no_known_competing_files
  ensure_manifest_shape
  ensure_hash_alignment
  ensure_zero_active_superseded_references
  ensure_freeze_is_not_active
  ensure_publication_pointer_if_present
  printf 'ACTIVE_CANONICAL\n'
}

main "$@"
