#!/usr/bin/env bash
set -euo pipefail
"$(dirname "$0")/kms_sign.sh" "$1" "$2" "$3" "ED25519"
