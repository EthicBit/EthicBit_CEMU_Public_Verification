#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${1:-$(cd -- "${SCRIPT_DIR}/.." && pwd)}"
PUBLICATION_ROOT="${2:-${ROOT_DIR}/publication}"
VERIFY_SCRIPT="${ROOT_DIR}/scripts/verify_closure_integrity.sh"
LOG_DIR="${ROOT_DIR}/logs"

fail() {
  local code="$1"
  shift
  printf '%s: %s\n' "$code" "$*" >&2
  exit 1
}

sha256_file() {
  shasum -a 256 "$1" | awk '{print $1}'
}

log_line() {
  printf '%s\n' "$1" | tee -a "$log_file"
}

run_and_log() {
  "$@" 2>&1 | tee -a "$log_file"
}

ensure_no_dual_publication_effective() {
  local publication_root="$1"
  local extra_pointer

  [[ -d "$publication_root" ]] || return 0
  [[ -L "${publication_root}/active" ]] || return 0

  extra_pointer=""
  local path
  for path in "$publication_root"/*; do
    [[ -e "$path" ]] || continue
    if [[ -L "$path" && "$(basename "$path")" != "active" ]]; then
      extra_pointer="$path"
      break
    fi
  done
  [[ -z "$extra_pointer" ]] || fail "PUBLICATION_DRIFT_DETECTED" "additional publication pointer detected: ${extra_pointer#${ROOT_DIR}/}"

  for path in \
    "${publication_root}/current" \
    "${publication_root}/live" \
    "${publication_root}/active.json" \
    "${publication_root}/current.json" \
    "${publication_root}/live.json"; do
    [[ ! -e "$path" ]] || fail "PUBLICATION_DRIFT_DETECTED" "competing publication pointer detected: ${path#${ROOT_DIR}/}"
  done
}

ensure_no_stale_public_pointer_cache() {
  local publication_root="$1"
  local publication_state active_link active_target stated_target stated_state stated_published_at

  [[ -d "$publication_root" ]] || return 0
  publication_state="${publication_root}/publication_state.json"
  active_link="${publication_root}/active"

  [[ -L "$active_link" ]] || return 0
  [[ -f "$publication_state" ]] || fail "PUBLICATION_DRIFT_DETECTED" "publication_state.json is missing while publication/active exists"

  active_target="$(readlink "$active_link")"
  stated_target="$(jq -r '.activeTarget // empty' "$publication_state")"
  stated_state="$(jq -r '.state // empty' "$publication_state")"
  stated_published_at="$(jq -r '.publishedAt // empty' "$publication_state")"

  [[ "$active_target" == "$stated_target" ]] || fail "PUBLICATION_DRIFT_DETECTED" "publication_state.json activeTarget does not match publication/active"
  [[ "$stated_state" == "ACTIVE_CANONICAL" ]] || fail "PUBLICATION_DRIFT_DETECTED" "publication_state.json state must remain ACTIVE_CANONICAL"
  [[ -n "$stated_published_at" ]] || fail "PUBLICATION_DRIFT_DETECTED" "publication_state.json publishedAt is empty"
}

main() {
  local timestamp log_file source_manifest_hash source_bundle_hash source_certificate_hash
  timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
  mkdir -p "$LOG_DIR"
  log_file="${LOG_DIR}/production_readiness_${timestamp}.log"

  [[ -x "$VERIFY_SCRIPT" ]] || fail "NOT_READY (FAIL-CLOSED)" "verify_closure_integrity.sh must be executable"
  [[ -x "${ROOT_DIR}/scripts/resolve_publication_drift.sh" ]] || fail "NOT_READY (FAIL-CLOSED)" "resolve_publication_drift.sh must be executable"
  [[ -x "${ROOT_DIR}/scripts/publish-closure-atomic.sh" ]] || fail "NOT_READY (FAIL-CLOSED)" "publish-closure-atomic.sh must be executable"

  run_and_log "$VERIFY_SCRIPT" "$ROOT_DIR"

  source_manifest_hash="$(sha256_file "${ROOT_DIR}/artifacts/artifact_manifest.json")"
  source_bundle_hash="$(sha256_file "${ROOT_DIR}/artifacts/security_incident_bundle_v1_0.json")"
  source_certificate_hash="$(sha256_file "${ROOT_DIR}/artifacts/formal_closure_certificate_multicapa_v1_0.json")"

  ensure_no_dual_publication_effective "$PUBLICATION_ROOT"
  ensure_no_stale_public_pointer_cache "$PUBLICATION_ROOT"

  if [[ -L "${PUBLICATION_ROOT}/active" ]]; then
    local active_root active_manifest_hash active_bundle_hash active_certificate_hash
    active_root="$(cd -P -- "${PUBLICATION_ROOT}/active" && pwd)"
    run_and_log "${active_root}/scripts/verify_closure_integrity.sh" "$active_root"

    active_manifest_hash="$(sha256_file "${active_root}/artifacts/artifact_manifest.json")"
    active_bundle_hash="$(sha256_file "${active_root}/artifacts/security_incident_bundle_v1_0.json")"
    active_certificate_hash="$(sha256_file "${active_root}/artifacts/formal_closure_certificate_multicapa_v1_0.json")"

    [[ "$source_manifest_hash" == "$active_manifest_hash" ]] || fail "PUBLICATION_DRIFT_DETECTED" "active publication manifest differs from the repository SSOT"
    [[ "$source_bundle_hash" == "$active_bundle_hash" ]] || fail "PUBLICATION_DRIFT_DETECTED" "active publication bundle differs from the repository root material"
    [[ "$source_certificate_hash" == "$active_certificate_hash" ]] || fail "PUBLICATION_DRIFT_DETECTED" "active publication certificate differs from the repository formal act"
  else
    log_line 'INFO: no active publication symlink detected; readiness remains a controlled candidate only.'
  fi

  log_line 'READY_FOR_CONTROLLED_PRODUCTION_CANDIDATE'
}

main "$@"