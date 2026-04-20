if ! scripts/verify_case003_material_integrity.sh; then
  echo "FAIL_CLOSED: case_003 material integrity gate failed"
  exit 1
fi

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
  require_file "${SCRIPTS_DIR}/verify_closure_integrity.sh"
  require_file "${SCRIPTS_DIR}/resolve_publication_drift.sh"
  require_file "${SCRIPTS_DIR}/publish-closure-atomic.sh"
  require_file "${SCRIPTS_DIR}/run_production_readiness.sh"
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
  ensure_no_known_competing_files
  ensure_manifest_shape
  ensure_hash_alignment
  ensure_zero_active_superseded_references
  ensure_freeze_is_not_active
  ensure_publication_pointer_if_present
  printf 'ACTIVE_CANONICAL\n'
}

main "$@"