#!/usr/bin/env bash
# Verifies EthicBit key posture and emits a machine-readable report.
#
# Status model:
#   - NON_COMPLIANT
#   - TRANSITIONAL_COMPLIANT
#   - SOVEREIGN_COMPLIANT
#   - PRODUCTION_HSM_READY
#
# Usage:
#   scripts/security/verify_key_posture.sh [--output <path>] [--repo <owner/repo>] [--probe-signing]

set -euo pipefail
umask 077

SCRIPT_NAME="$(basename "$0")"
REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
OUTPUT_PATH="${REPO_ROOT}/results/key_posture_report.json"
REPO_SLUG=""
PROBE_SIGNING="0"

usage() {
  cat >&2 <<EOF
Usage:
  ${SCRIPT_NAME} [--output <path>] [--repo <owner/repo>] [--probe-signing]

Options:
  --output <path>     Output JSON report path.
                      Default: ${OUTPUT_PATH}
  --repo <owner/repo> GitHub repository slug for runner/secrets checks.
                      Default: derived from git remote origin.
  --probe-signing     Execute signer probe via assurance/signers/sign_dispatch.sh.
EOF
  exit 2
}

as_bool() {
  local raw="${1:-}"
  raw="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]')"
  [[ "$raw" == "1" || "$raw" == "true" || "$raw" == "yes" || "$raw" == "y" || "$raw" == "on" ]]
}

derive_repo_slug() {
  local remote
  remote="$(git -C "$REPO_ROOT" config --get remote.origin.url 2>/dev/null || true)"
  if [[ -z "$remote" ]]; then
    return 1
  fi
  remote="${remote%.git}"
  if [[ "$remote" =~ github\.com[:/]([^/]+/[^/]+)$ ]]; then
    printf '%s\n' "${BASH_REMATCH[1]}"
    return 0
  fi
  return 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      [[ $# -ge 2 ]] || usage
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --repo)
      [[ $# -ge 2 ]] || usage
      REPO_SLUG="$2"
      shift 2
      ;;
    --probe-signing)
      PROBE_SIGNING="1"
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      usage
      ;;
  esac
done

BACKEND="${ETHICBIT_SIGNING_BACKEND:-github_secrets_pem}"
ENDPOINT="${ETHICBIT_SIGNING_ENDPOINT:-}"
ED25519_KEY_ID="${ETHICBIT_ED25519_KEY_ID:-}"
MLDSA_KEY_ID="${ETHICBIT_MLDSA_KEY_ID:-}"
TOKEN_PRESENT="false"
if [[ -n "${ETHICBIT_SIGNING_TOKEN:-}" ]]; then
  TOKEN_PRESENT="true"
fi

if [[ -z "$REPO_SLUG" ]]; then
  REPO_SLUG="$(derive_repo_slug || true)"
fi

mkdir -p "$(dirname "$OUTPUT_PATH")"

tracked_private_hits="$(
  cd "$REPO_ROOT" && git grep -n -P '^-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----$' -- . 2>/dev/null || true
)"
private_keys_in_repo="false"
if [[ -n "$tracked_private_hits" ]]; then
  private_keys_in_repo="true"
fi

tracked_keys_under_assurance="$(
  cd "$REPO_ROOT" && git ls-files assurance/keys 2>/dev/null || true
)"

runner_label_required="${ETHICBIT_REQUIRED_RUNNER_LABEL:-mldsa-native}"
runner_status="unknown"
runner_busy="unknown"
runner_check_ok="false"

secrets_present="unknown"
if command -v gh >/dev/null 2>&1 && [[ -n "$REPO_SLUG" ]]; then
  if gh api "repos/${REPO_SLUG}/actions/runners" --jq ".runners[] | select([.labels[].name] | index(\"${runner_label_required}\")) | .status" >/tmp/ethicbit_runner_status.txt 2>/dev/null; then
    if [[ -s /tmp/ethicbit_runner_status.txt ]]; then
      runner_status="$(head -n1 /tmp/ethicbit_runner_status.txt)"
      runner_check_ok="true"
    fi
  fi
  if gh api "repos/${REPO_SLUG}/actions/runners" --jq ".runners[] | select([.labels[].name] | index(\"${runner_label_required}\")) | .busy" >/tmp/ethicbit_runner_busy.txt 2>/dev/null; then
    if [[ -s /tmp/ethicbit_runner_busy.txt ]]; then
      runner_busy="$(head -n1 /tmp/ethicbit_runner_busy.txt)"
    fi
  fi

  if gh secret list -R "$REPO_SLUG" >/tmp/ethicbit_secret_list.txt 2>/dev/null; then
    if grep -q 'ETHICBIT_ED25519_PRIVATE_KEY_PEM' /tmp/ethicbit_secret_list.txt \
      && grep -q 'ETHICBIT_ED25519_PUBLIC_KEY_PEM' /tmp/ethicbit_secret_list.txt \
      && grep -q 'ETHICBIT_MLDSA_PRIVATE_KEY_PEM' /tmp/ethicbit_secret_list.txt \
      && grep -q 'ETHICBIT_MLDSA_PUBLIC_KEY_PEM' /tmp/ethicbit_secret_list.txt; then
      secrets_present="true"
    else
      secrets_present="false"
    fi
  fi
fi
rm -f /tmp/ethicbit_runner_status.txt /tmp/ethicbit_runner_busy.txt /tmp/ethicbit_secret_list.txt

sign_probe_ok="unknown"
sign_probe_error=""
if as_bool "$PROBE_SIGNING"; then
  if [[ -x "${REPO_ROOT}/assurance/signers/sign_dispatch.sh" ]]; then
    probe_file="$(mktemp)"
    printf '{"probe":"key_posture"}\n' > "$probe_file"
    if ETHICBIT_KEY_POSTURE_PROBE_CONTEXT=1 ETHICBIT_SIGNING_BACKEND="$BACKEND" "${REPO_ROOT}/assurance/signers/sign_dispatch.sh" ED25519 "$probe_file" >/tmp/ethicbit_probe_ed.log 2>/tmp/ethicbit_probe_ed.err \
      && ETHICBIT_KEY_POSTURE_PROBE_CONTEXT=1 ETHICBIT_SIGNING_BACKEND="$BACKEND" "${REPO_ROOT}/assurance/signers/sign_dispatch.sh" ML-DSA "$probe_file" >/tmp/ethicbit_probe_ml.log 2>/tmp/ethicbit_probe_ml.err; then
      sign_probe_ok="true"
    else
      sign_probe_ok="false"
      sign_probe_error="$(
        { cat /tmp/ethicbit_probe_ed.err /tmp/ethicbit_probe_ml.err 2>/dev/null || true; } | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g'
      )"
    fi
    rm -f "$probe_file" /tmp/ethicbit_probe_ed.log /tmp/ethicbit_probe_ml.log /tmp/ethicbit_probe_ed.err /tmp/ethicbit_probe_ml.err
  else
    sign_probe_ok="false"
    sign_probe_error="sign_dispatch.sh not found/executable"
  fi
fi

production_hsm_ready="false"
sovereign_compliant="false"
transitional_compliant="false"
status="NON_COMPLIANT"

if [[ "$private_keys_in_repo" == "false" ]]; then
  case "$BACKEND" in
    remote_signing_provider)
      if [[ -n "$ENDPOINT" && -n "$ED25519_KEY_ID" && -n "$MLDSA_KEY_ID" && "$TOKEN_PRESENT" == "true" ]]; then
        if [[ "$sign_probe_ok" == "true" || "$PROBE_SIGNING" == "0" ]]; then
          production_hsm_ready="true"
          status="PRODUCTION_HSM_READY"
        fi
      fi
      ;;

    github_secrets_pem)
      transitional_compliant="true"
      status="TRANSITIONAL_COMPLIANT"

      if [[ "$secrets_present" == "true" && "$runner_status" == "online" ]]; then
        sovereign_compliant="true"
        status="SOVEREIGN_COMPLIANT"
      fi
      ;;

    *)
      status="NON_COMPLIANT"
      ;;
  esac
fi

remote_endpoint_configured="false"
remote_token_configured="false"
remote_ed25519_key_id_configured="false"
remote_mldsa_key_id_configured="false"
probe_executed="false"

[[ -n "$ENDPOINT" ]] && remote_endpoint_configured="true"
[[ "$TOKEN_PRESENT" == "true" ]] && remote_token_configured="true"
[[ -n "$ED25519_KEY_ID" ]] && remote_ed25519_key_id_configured="true"
[[ -n "$MLDSA_KEY_ID" ]] && remote_mldsa_key_id_configured="true"
[[ "$PROBE_SIGNING" == "1" ]] && probe_executed="true"

tracked_keys_file="$(mktemp)"
private_hits_file="$(mktemp)"
printf '%s\n' "$tracked_keys_under_assurance" > "$tracked_keys_file"
printf '%s\n' "$tracked_private_hits" > "$private_hits_file"
trap 'rm -f "$tracked_keys_file" "$private_hits_file"' EXIT

export ETHICBIT_KEY_POSTURE_OUTPUT_PATH="$OUTPUT_PATH"
export ETHICBIT_KEY_POSTURE_STATUS="$status"
export ETHICBIT_KEY_POSTURE_BACKEND="$BACKEND"
export ETHICBIT_KEY_POSTURE_PRIVATE_IN_REPO="$private_keys_in_repo"
export ETHICBIT_KEY_POSTURE_RUNNER_REQUIRED_LABEL="$runner_label_required"
export ETHICBIT_KEY_POSTURE_RUNNER_STATUS="$runner_status"
export ETHICBIT_KEY_POSTURE_RUNNER_BUSY="$runner_busy"
export ETHICBIT_KEY_POSTURE_RUNNER_CHECK_OK="$runner_check_ok"
export ETHICBIT_KEY_POSTURE_GITHUB_REPO="$REPO_SLUG"
export ETHICBIT_KEY_POSTURE_GITHUB_SECRETS_PRESENT="$secrets_present"
export ETHICBIT_KEY_POSTURE_HSM_READY="$production_hsm_ready"
export ETHICBIT_KEY_POSTURE_SOVEREIGN="$sovereign_compliant"
export ETHICBIT_KEY_POSTURE_TRANSITIONAL="$transitional_compliant"
export ETHICBIT_KEY_POSTURE_REMOTE_ENDPOINT="$remote_endpoint_configured"
export ETHICBIT_KEY_POSTURE_REMOTE_TOKEN="$remote_token_configured"
export ETHICBIT_KEY_POSTURE_REMOTE_ED25519="$remote_ed25519_key_id_configured"
export ETHICBIT_KEY_POSTURE_REMOTE_MLDSA="$remote_mldsa_key_id_configured"
export ETHICBIT_KEY_POSTURE_PROBE_EXECUTED="$probe_executed"
export ETHICBIT_KEY_POSTURE_PROBE_OK="$sign_probe_ok"
export ETHICBIT_KEY_POSTURE_PROBE_ERROR="$sign_probe_error"
export ETHICBIT_KEY_POSTURE_TRACKED_KEYS_FILE="$tracked_keys_file"
export ETHICBIT_KEY_POSTURE_PRIVATE_HITS_FILE="$private_hits_file"

python3 - <<'PY'
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def as_bool(raw: str) -> bool:
    return str(raw or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def read_lines(path: str) -> list[str]:
    p = Path(path)
    if not p.exists():
        return []
    return [line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


report = {
    "artifactType": "key_posture_report",
    "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "status": os.environ.get("ETHICBIT_KEY_POSTURE_STATUS", "NON_COMPLIANT"),
    "signing_backend": os.environ.get("ETHICBIT_KEY_POSTURE_BACKEND", ""),
    "private_keys_in_repo": as_bool(os.environ.get("ETHICBIT_KEY_POSTURE_PRIVATE_IN_REPO", "false")),
    "tracked_keys_under_assurance": read_lines(os.environ.get("ETHICBIT_KEY_POSTURE_TRACKED_KEYS_FILE", "")),
    "runner_required_label": os.environ.get("ETHICBIT_KEY_POSTURE_RUNNER_REQUIRED_LABEL", ""),
    "runner_mode": os.environ.get("ETHICBIT_KEY_POSTURE_RUNNER_REQUIRED_LABEL", ""),
    "runner_status": os.environ.get("ETHICBIT_KEY_POSTURE_RUNNER_STATUS", "unknown"),
    "runner_busy": os.environ.get("ETHICBIT_KEY_POSTURE_RUNNER_BUSY", "unknown"),
    "runner_check_ok": as_bool(os.environ.get("ETHICBIT_KEY_POSTURE_RUNNER_CHECK_OK", "false")),
    "github_repo": os.environ.get("ETHICBIT_KEY_POSTURE_GITHUB_REPO", ""),
    "github_secrets_present": os.environ.get("ETHICBIT_KEY_POSTURE_GITHUB_SECRETS_PRESENT", "unknown"),
    "production_hsm_ready": as_bool(os.environ.get("ETHICBIT_KEY_POSTURE_HSM_READY", "false")),
    "sovereign_compliant": as_bool(os.environ.get("ETHICBIT_KEY_POSTURE_SOVEREIGN", "false")),
    "transitional_compliant": as_bool(os.environ.get("ETHICBIT_KEY_POSTURE_TRANSITIONAL", "false")),
    "remote": {
        "endpoint_configured": as_bool(os.environ.get("ETHICBIT_KEY_POSTURE_REMOTE_ENDPOINT", "false")),
        "token_present": as_bool(os.environ.get("ETHICBIT_KEY_POSTURE_REMOTE_TOKEN", "false")),
        "ed25519_key_id_configured": as_bool(os.environ.get("ETHICBIT_KEY_POSTURE_REMOTE_ED25519", "false")),
        "mldsa_key_id_configured": as_bool(os.environ.get("ETHICBIT_KEY_POSTURE_REMOTE_MLDSA", "false")),
    },
    "probe": {
        "executed": as_bool(os.environ.get("ETHICBIT_KEY_POSTURE_PROBE_EXECUTED", "false")),
        "sign_dispatch_ok": os.environ.get("ETHICBIT_KEY_POSTURE_PROBE_OK", "unknown"),
        "error": os.environ.get("ETHICBIT_KEY_POSTURE_PROBE_ERROR", ""),
    },
}

private_hits = read_lines(os.environ.get("ETHICBIT_KEY_POSTURE_PRIVATE_HITS_FILE", ""))
if private_hits:
    report["private_key_hits"] = private_hits

out = Path(os.environ["ETHICBIT_KEY_POSTURE_OUTPUT_PATH"])
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2, ensure_ascii=False))
PY

case "$status" in
  NON_COMPLIANT)
    exit 2
    ;;
  *)
    exit 0
    ;;
esac
