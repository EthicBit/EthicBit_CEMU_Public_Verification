#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

MATRIX_PATH="${ROOT_DIR}/config/constitutional_controls.v1.json"
OUTPUT_PATH="${ROOT_DIR}/results/constitutional_controls_report.json"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/audit/verify_constitutional_controls.sh
  ./scripts/audit/verify_constitutional_controls.sh --matrix ./config/constitutional_controls.v1.json
  ./scripts/audit/verify_constitutional_controls.sh --output ./results/constitutional_controls_report.json
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --matrix)
      MATRIX_PATH="${2:-}"
      [[ -n "$MATRIX_PATH" ]] || { echo "missing value for --matrix" >&2; exit 2; }
      shift 2
      ;;
    --output)
      OUTPUT_PATH="${2:-}"
      [[ -n "$OUTPUT_PATH" ]] || { echo "missing value for --output" >&2; exit 2; }
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

mkdir -p "$(dirname "$OUTPUT_PATH")"

python3 - "$ROOT_DIR" "$MATRIX_PATH" "$OUTPUT_PATH" <<'PY'
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


root = Path(sys.argv[1]).resolve()
matrix_path = Path(sys.argv[2])
if not matrix_path.is_absolute():
    matrix_path = (root / matrix_path).resolve()
output_path = Path(sys.argv[3])
if not output_path.is_absolute():
    output_path = (root / output_path).resolve()

if not matrix_path.exists():
    print(f"ERROR: matrix not found: {matrix_path}", file=sys.stderr)
    raise SystemExit(2)

with open(matrix_path, "r", encoding="utf-8") as handle:
    matrix = json.load(handle)

controls = matrix.get("controls", [])
if not isinstance(controls, list):
    print("ERROR: controls must be a list", file=sys.stderr)
    raise SystemExit(2)

results = []
must_failed = False
summary = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "mustFailed": 0,
    "shouldFailed": 0,
}

print(f"Constitutional controls matrix: {matrix_path}")
for control in controls:
    summary["total"] += 1
    control_id = str(control.get("controlId", "UNKNOWN"))
    title = str(control.get("title", ""))
    normative = str(control.get("normative", "SHOULD")).upper()
    execution = control.get("execution", {}) or {}
    command = str(execution.get("command", "")).strip()
    timeout_seconds = int(execution.get("timeoutSeconds", 120))
    evidence = control.get("evidence", {}) or {}
    evidence_paths = evidence.get("paths", []) or []

    record = {
        "controlId": control_id,
        "articleId": control.get("articleId"),
        "title": title,
        "normative": normative,
        "failureBehavior": control.get("failureBehavior", "WARN"),
        "command": command,
        "timeoutSeconds": timeout_seconds,
        "status": "FAIL",
        "execution": {},
        "evidence": {"paths": evidence_paths, "missing": []},
        "audiences": control.get("audiences", []),
        "checkedAt": now_utc_iso(),
    }

    command_ok = False
    if command:
        try:
            proc = subprocess.run(
                command,
                cwd=str(root),
                shell=True,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
            command_ok = proc.returncode == 0
            record["execution"] = {
                "returnCode": proc.returncode,
                "stdoutTail": (proc.stdout or "")[-1200:],
                "stderrTail": (proc.stderr or "")[-1200:],
            }
        except subprocess.TimeoutExpired as exc:
            record["execution"] = {
                "returnCode": 124,
                "stdoutTail": (exc.stdout or "")[-1200:] if exc.stdout else "",
                "stderrTail": (exc.stderr or "")[-1200:] if exc.stderr else "",
                "error": f"timeout after {timeout_seconds}s",
            }
            command_ok = False
    else:
        record["execution"] = {
            "returnCode": 0,
            "stdoutTail": "",
            "stderrTail": "",
            "note": "no command configured"
        }
        command_ok = True

    missing_evidence = []
    for rel_path in evidence_paths:
        p = Path(str(rel_path))
        if not p.is_absolute():
            p = (root / p).resolve()
        if not p.exists():
            missing_evidence.append(str(rel_path))
    record["evidence"]["missing"] = missing_evidence

    passed = command_ok and not missing_evidence
    record["status"] = "PASS" if passed else "FAIL"

    if passed:
        summary["passed"] += 1
        print(f"[PASS] {control_id} ({normative}) - {title}")
    else:
        summary["failed"] += 1
        if normative == "MUST":
            summary["mustFailed"] += 1
            must_failed = True
        elif normative == "SHOULD":
            summary["shouldFailed"] += 1
        print(f"[FAIL] {control_id} ({normative}) - {title}")
        if record["execution"].get("returnCode", 0) != 0:
            print(f"       command rc={record['execution'].get('returnCode')}")
        if missing_evidence:
            print(f"       missing evidence: {', '.join(missing_evidence)}")

    results.append(record)

report = {
    "artifactType": "constitutional_controls_report",
    "generatedAt": now_utc_iso(),
    "constitutionVersion": matrix.get("constitutionVersion"),
    "matrixVersion": matrix.get("matrixVersion"),
    "matrixPath": str(matrix_path),
    "root": str(root),
    "summary": summary,
    "mustFailClosedTriggered": must_failed,
    "controls": results,
}

# Dynamic constitutional control: PQ runtime secret protection by claim level.
claim_level = str(os.getenv("ETHICBIT_CLAIM_LEVEL", "ci_grade") or "ci_grade").strip()
strict_claim_levels = {"freeze_grade", "sovereign_release"}
strict_required = claim_level in strict_claim_levels
pq_path_rel = "results/pq_runtime_secret_protection.json"
pq_path = (root / pq_path_rel).resolve()

summary["total"] += 1
pq_record = {
    "controlId": "CTL-PQ-001",
    "articleId": "ART-02",
    "title": "PQ Runtime Secret Protection Claim-Level Enforcement",
    "normative": "MUST",
    "failureBehavior": "FAIL_CLOSED",
    "command": "dynamic:claim-level-pq-runtime-protection",
    "timeoutSeconds": 0,
    "status": "FAIL",
    "execution": {},
    "evidence": {"paths": [pq_path_rel], "missing": []},
    "audiences": ["ai-agentic", "cybersecurity", "regulatory", "government"],
    "checkedAt": now_utc_iso(),
    "metadata": {
        "claimLevel": claim_level,
        "strictRequired": strict_required,
        "strictClaimLevels": sorted(strict_claim_levels),
    },
}

if not pq_path.exists():
    pq_record["evidence"]["missing"] = [pq_path_rel]
    if strict_required:
        pq_record["status"] = "FAIL"
        pq_record["execution"] = {
            "returnCode": 1,
            "note": f"missing {pq_path_rel} for strict claim level {claim_level}",
        }
    else:
        pq_record["status"] = "PASS"
        pq_record["execution"] = {
            "returnCode": 0,
            "note": f"{pq_path_rel} missing but allowed for non-strict claim level {claim_level}",
        }
else:
    try:
        pq_payload = json.loads(pq_path.read_text(encoding="utf-8"))
    except Exception as exc:
        pq_payload = None
        pq_record["execution"] = {
            "returnCode": 1,
            "error": f"invalid JSON in {pq_path_rel}: {exc}",
        }
        pq_record["status"] = "FAIL" if strict_required else "PASS"

    if pq_payload is not None:
        artifact_type = str(pq_payload.get("artifactType") or "")
        pq_status = str(pq_payload.get("status") or "UNKNOWN")
        protector = str(pq_payload.get("protector") or "UNKNOWN")
        evidence_ref = str(pq_payload.get("evidence_ref") or "UNKNOWN")
        pq_record["execution"] = {
            "returnCode": 0,
            "artifactType": artifact_type,
            "pqStatus": pq_status,
            "protector": protector,
            "evidenceRef": evidence_ref,
        }

        if strict_required:
            strict_ok = artifact_type == "pq_runtime_secret_protection" and pq_status == "PROTECTED"
            pq_record["status"] = "PASS" if strict_ok else "FAIL"
            if not strict_ok:
                pq_record["execution"]["returnCode"] = 1
                pq_record["execution"]["error"] = (
                    "strict claim requires artifactType=pq_runtime_secret_protection and status=PROTECTED"
                )
        else:
            pq_record["status"] = "PASS"

if pq_record["status"] == "PASS":
    summary["passed"] += 1
    print(f"[PASS] {pq_record['controlId']} (MUST) - {pq_record['title']}")
else:
    summary["failed"] += 1
    summary["mustFailed"] += 1
    must_failed = True
    print(f"[FAIL] {pq_record['controlId']} (MUST) - {pq_record['title']}")
    if pq_record["execution"].get("returnCode", 0) != 0:
        print(f"       command rc={pq_record['execution'].get('returnCode')}")
    missing = pq_record["evidence"].get("missing", [])
    if missing:
        print(f"       missing evidence: {', '.join(missing)}")

results.append(pq_record)

# Dynamic constitutional control: Anti-RE hardening by claim level.
anti_re_path_rel = "results/anti_re_guard_report.json"
anti_re_path = (root / anti_re_path_rel).resolve()

summary["total"] += 1
anti_re_record = {
    "controlId": "CTL-RE-001",
    "articleId": "ART-11",
    "title": "Anti-RE Runtime Hardening Claim-Level Enforcement",
    "normative": "MUST",
    "failureBehavior": "FAIL_CLOSED",
    "command": "dynamic:claim-level-anti-re-hardening",
    "timeoutSeconds": 0,
    "status": "FAIL",
    "execution": {},
    "evidence": {"paths": [anti_re_path_rel], "missing": []},
    "audiences": ["ai-agentic", "cybersecurity", "regulatory", "government"],
    "checkedAt": now_utc_iso(),
    "metadata": {
        "claimLevel": claim_level,
        "strictRequired": strict_required,
        "strictClaimLevels": sorted(strict_claim_levels),
    },
}

if not anti_re_path.exists():
    anti_re_record["evidence"]["missing"] = [anti_re_path_rel]
    if strict_required:
        anti_re_record["status"] = "FAIL"
        anti_re_record["execution"] = {
            "returnCode": 1,
            "note": f"missing {anti_re_path_rel} for strict claim level {claim_level}",
        }
    else:
        anti_re_record["status"] = "PASS"
        anti_re_record["execution"] = {
            "returnCode": 0,
            "note": f"{anti_re_path_rel} missing but allowed for non-strict claim level {claim_level}",
        }
else:
    try:
        anti_re_payload = json.loads(anti_re_path.read_text(encoding="utf-8"))
    except Exception as exc:
        anti_re_payload = None
        anti_re_record["execution"] = {
            "returnCode": 1,
            "error": f"invalid JSON in {anti_re_path_rel}: {exc}",
        }
        anti_re_record["status"] = "FAIL" if strict_required else "PASS"

    if anti_re_payload is not None:
        artifact_type = str(anti_re_payload.get("artifactType") or "")
        anti_re_status = str(anti_re_payload.get("status") or "UNKNOWN")
        policy_version = str(anti_re_payload.get("policy_version") or "UNKNOWN")
        anti_re_record["execution"] = {
            "returnCode": 0,
            "artifactType": artifact_type,
            "antiReStatus": anti_re_status,
            "policyVersion": policy_version,
        }

        if strict_required:
            strict_ok = artifact_type == "anti_re_guard_report" and anti_re_status == "PASS"
            anti_re_record["status"] = "PASS" if strict_ok else "FAIL"
            if not strict_ok:
                anti_re_record["execution"]["returnCode"] = 1
                anti_re_record["execution"]["error"] = (
                    "strict claim requires artifactType=anti_re_guard_report and status=PASS"
                )
        else:
            anti_re_record["status"] = "PASS"

if anti_re_record["status"] == "PASS":
    summary["passed"] += 1
    print(f"[PASS] {anti_re_record['controlId']} (MUST) - {anti_re_record['title']}")
else:
    summary["failed"] += 1
    summary["mustFailed"] += 1
    must_failed = True
    print(f"[FAIL] {anti_re_record['controlId']} (MUST) - {anti_re_record['title']}")
    if anti_re_record["execution"].get("returnCode", 0) != 0:
        print(f"       command rc={anti_re_record['execution'].get('returnCode')}")
    missing = anti_re_record["evidence"].get("missing", [])
    if missing:
        print(f"       missing evidence: {', '.join(missing)}")

results.append(anti_re_record)

output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=2, ensure_ascii=False)
    handle.write("\n")

print("")
print(f"Report: {output_path}")
print(f"Summary: total={summary['total']} pass={summary['passed']} fail={summary['failed']} must_fail={summary['mustFailed']}")

if must_failed:
    print("CONSTITUTIONAL_STATUS=FAIL_CLOSED")
    raise SystemExit(1)

print("CONSTITUTIONAL_STATUS=PASS")
raise SystemExit(0)
PY
