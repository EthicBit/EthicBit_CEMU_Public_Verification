#!/usr/bin/env python3
"""Build AEM-EVOLVE v4.0 automated security-review support evidence.

This runner performs lightweight, deterministic scans over committed HEAD content.
It supports external reviewer assessment; it does not certify cybersecurity or prove
absence of all vulnerabilities.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = ROOT / "assurance/external-validation/v4_0/security_review"

SUMMARY_NAME = "AUTOMATED_SECURITY_REVIEW_SUMMARY.json"
LOG_NAME = "AUTOMATED_SECURITY_REVIEW_LOG.txt"
HASH_RECORD_NAME = "SECURITY_SCAN_HASH_RECORD.txt"

SUPPORT_INPUTS = {
    "v4_0_controlled_evidence": "assurance/v4_0/V4_0_CONTROLLED_EVIDENCE_REPORT.json",
    "claim_boundary_red_team": "assurance/external-validation/v4_0/claim_red_team/CLAIM_BOUNDARY_RED_TEAM_REPORT.json",
    "notary_dossier_manifest": "assurance/external-validation/v4_0/notary_dossier/DOSSIER_MANIFEST.json",
    "automated_reproduction_support": "assurance/external-validation/v4_0/automated_reproduction/AUTOMATED_REPRODUCTION_REPORT.json",
}

DEPENDENCY_MANIFEST_RE = re.compile(
    r"(^|/)(requirements.*\.txt|package-lock\.json|package\.json|go\.mod|go\.sum|pyproject\.toml|Pipfile|Pipfile\.lock)$"
)

SECRET_PATTERNS = [
    {
        "id": "private_key_block",
        "severity": "critical",
        "regex": re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"),
    },
    {
        "id": "aws_access_key_id",
        "severity": "critical",
        "regex": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    },
    {
        "id": "github_token",
        "severity": "critical",
        "regex": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),
    },
    {
        "id": "openai_api_key",
        "severity": "critical",
        "regex": re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    },
    {
        "id": "google_api_key",
        "severity": "critical",
        "regex": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    },
    {
        "id": "slack_token",
        "severity": "critical",
        "regex": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    },
]

OPTIONAL_TOOLS = ["gitleaks", "trufflehog", "pip-audit", "safety", "bandit", "trivy", "semgrep"]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_sha256(obj: Any) -> str:
    data = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_bytes(data)


def run_git(args: List[str]) -> bytes:
    result = subprocess.run(["git", *args], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {stderr}")
    return result.stdout


def head_file_list() -> List[str]:
    raw = run_git(["ls-tree", "-r", "--name-only", "HEAD"])
    return [line for line in raw.decode("utf-8").splitlines() if line]


def read_head_file(path: str) -> bytes:
    return run_git(["show", f"HEAD:{path}"])


def is_probably_binary(data: bytes) -> bool:
    if b"\0" in data:
        return True
    sample = data[:4096]
    if not sample:
        return False
    non_text = sum(1 for byte in sample if byte < 9 or (13 < byte < 32))
    return non_text / len(sample) > 0.20


def load_support_input(name: str, repo_path: str) -> Dict[str, Any]:
    raw = read_head_file(repo_path)
    obj = json.loads(raw.decode("utf-8"))
    return {
        "name": name,
        "path": repo_path,
        "source": "git_HEAD",
        "sha256": sha256_bytes(raw),
        "canonical_sha256": canonical_json_sha256(obj),
        "json": obj,
    }


def scan_high_confidence_secrets(paths: Iterable[str]) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    scanned_files = 0
    skipped_binary_files = 0
    skipped_large_files = 0

    for repo_path in paths:
        try:
            raw = read_head_file(repo_path)
        except Exception:
            continue
        if len(raw) > 2_000_000:
            skipped_large_files += 1
            continue
        if is_probably_binary(raw):
            skipped_binary_files += 1
            continue
        text = raw.decode("utf-8", errors="replace")
        scanned_files += 1
        for pattern in SECRET_PATTERNS:
            for match in pattern["regex"].finditer(text):
                line_number = text.count("\n", 0, match.start()) + 1
                findings.append(
                    {
                        "finding_id": pattern["id"],
                        "severity": pattern["severity"],
                        "path": repo_path,
                        "line": line_number,
                        "match_sha256": sha256_bytes(match.group(0).encode("utf-8")),
                    }
                )

    critical_findings = sum(1 for finding in findings if finding["severity"] == "critical")
    return {
        "scanner": "high_confidence_secret_pattern_scan",
        "scope": "committed_git_HEAD_tracked_text_files",
        "scanned_files": scanned_files,
        "skipped_binary_files": skipped_binary_files,
        "skipped_large_files": skipped_large_files,
        "secret_findings": len(findings),
        "critical_findings": critical_findings,
        "findings": findings,
    }


def dependency_inventory(paths: Iterable[str]) -> List[Dict[str, Any]]:
    inventory = []
    for repo_path in paths:
        if not DEPENDENCY_MANIFEST_RE.search(repo_path):
            continue
        raw = read_head_file(repo_path)
        inventory.append(
            {
                "path": repo_path,
                "source": "git_HEAD",
                "sha256": sha256_bytes(raw),
                "size_bytes": len(raw),
            }
        )
    return sorted(inventory, key=lambda item: item["path"])


def optional_tool_inventory() -> List[Dict[str, Any]]:
    inventory = []
    for tool in OPTIONAL_TOOLS:
        path = shutil.which(tool)
        inventory.append(
            {
                "tool": tool,
                "available_in_runner": path is not None,
                "path": path,
                "required_for_pass": False,
            }
        )
    return inventory


def check(condition: bool, check_id: str, pass_status: str, fail_status: str, detail: str) -> Dict[str, Any]:
    return {
        "check_id": check_id,
        "status": pass_status if condition else fail_status,
        "passed": bool(condition),
        "detail": detail,
    }


def build_summary() -> Dict[str, Any]:
    paths = head_file_list()
    support_inputs = {name: load_support_input(name, path) for name, path in SUPPORT_INPUTS.items()}
    secret_scan = scan_high_confidence_secrets(paths)
    dependencies = dependency_inventory(paths)
    tools = optional_tool_inventory()

    v4 = support_inputs["v4_0_controlled_evidence"]["json"]
    red_team = support_inputs["claim_boundary_red_team"]["json"]
    dossier = support_inputs["notary_dossier_manifest"]["json"]
    reproduction = support_inputs["automated_reproduction_support"]["json"]

    checks = [
        check(
            secret_scan["secret_findings"] == 0 and secret_scan["critical_findings"] == 0,
            "HIGH_CONFIDENCE_SECRET_SCAN",
            "PASS",
            "FAIL_CLOSED",
            "No high-confidence committed secret patterns may be present in scanned HEAD text files.",
        ),
        check(
            v4.get("status") == "CONTROLLED_EVIDENCE_PARTIAL"
            and "external_security_review" in v4.get("pending_external_criteria", [])
            and v4.get("v4_0_external_validation_release_claimed") is False,
            "V4_0_SECURITY_REVIEW_BOUNDARY",
            "PENDING_EXTERNAL_CONFIRMED",
            "FAIL_CLOSED",
            "External security review must remain pending until external reviewer attestation exists.",
        ),
        check(
            red_team.get("claim_boundary_red_team") == "PASS"
            and red_team.get("external_claim_review_completed") is False,
            "CLAIM_BOUNDARY_RED_TEAM_SUPPORT",
            "PASS",
            "FAIL_CLOSED",
            "Claim red-team support must pass without claiming external claim review completion.",
        ),
        check(
            dossier.get("external_security_review_completed") is False
            and dossier.get("human_attestation_status") == "HUMAN_ATTESTATION_PENDING"
            and dossier.get("external_validation_pass_claimed") is False,
            "NOTARY_DOSSIER_SECURITY_BOUNDARY",
            "HUMAN_ATTESTATION_PENDING_CONFIRMED",
            "FAIL_CLOSED",
            "Dossier must not claim completed external security review or external validation pass.",
        ),
        check(
            reproduction.get("automated_reproduction_support") == "PASS"
            and reproduction.get("non_claims", {}).get("completed_external_validation") is False,
            "AUTOMATED_REPRODUCTION_SUPPORT_REFERENCE",
            "PASS",
            "FAIL_CLOSED",
            "HV-5 automated reproduction support should be present while preserving non-claims.",
        ),
    ]

    all_passed = all(item["passed"] for item in checks)
    status = "AUTOMATED_SECURITY_REVIEW_SUPPORT_PASS" if all_passed else "AUTOMATED_SECURITY_REVIEW_SUPPORT_FAIL_CLOSED"
    support = "PASS" if all_passed else "FAIL_CLOSED"

    evidence_inputs = []
    for name, loaded in support_inputs.items():
        evidence_inputs.append(
            {
                "name": name,
                "path": loaded["path"],
                "source": loaded["source"],
                "sha256": loaded["sha256"],
                "canonical_sha256": loaded["canonical_sha256"],
            }
        )

    return {
        "schema_id": "AEM_EVOLVE_V4_0_AUTOMATED_SECURITY_REVIEW_SUPPORT_SUMMARY_V1",
        "report_type": "AUTOMATED_SECURITY_REVIEW_SUPPORT_SUMMARY",
        "version": "4.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "automated_security_review_support": support,
        "critical_findings": secret_scan["critical_findings"],
        "secret_findings": secret_scan["secret_findings"],
        "scan_scope": secret_scan["scope"],
        "scanned_files": secret_scan["scanned_files"],
        "skipped_binary_files": secret_scan["skipped_binary_files"],
        "skipped_large_files": secret_scan["skipped_large_files"],
        "dependency_inventory_status": "GENERATED",
        "dependency_manifest_count": len(dependencies),
        "dependency_manifests": dependencies,
        "optional_security_tools": tools,
        "evidence_inputs": evidence_inputs,
        "checks": checks,
        "claim_boundary": {
            "automated_security_review_support_only": True,
            "automated_pipeline_may_claim_external_security_review_completed": False,
            "automated_pipeline_may_claim_cybersecurity_certification": False,
            "automated_pipeline_may_claim_absence_of_all_vulnerabilities": False,
            "human_attestation_required_for_external_security_review_completion": True,
            "human_attestation_status": "HUMAN_ATTESTATION_PENDING",
        },
        "non_claims": {
            "completed_external_security_review": False,
            "cybersecurity_certification": False,
            "absence_of_all_vulnerabilities": False,
            "completed_external_validation": False,
            "external_certification": False,
            "regulatory_approval": False,
            "financial_advice": False,
            "clinical_or_diagnostic_readiness": False,
            "universal_production_readiness": False,
            "legal_compliance": False,
        },
        "notes": (
            "Automated security review support does not constitute cybersecurity certification, "
            "external security audit completion, legal compliance, or absence of all vulnerabilities."
        ),
    }


def write_log(summary: Dict[str, Any], log_path: Path) -> None:
    lines = [
        "AEM-EVOLVE v4.0 Automated Security Review Support",
        f"generated_utc={summary['generated_utc']}",
        f"AUTOMATED_SECURITY_REVIEW_SUPPORT={summary['automated_security_review_support']}",
        f"critical_findings={summary['critical_findings']}",
        f"secret_findings={summary['secret_findings']}",
        f"dependency_manifest_count={summary['dependency_manifest_count']}",
        "external_security_review_completed=false",
        "cybersecurity_certification=false",
        "absence_of_all_vulnerabilities=false",
        "HUMAN_ATTESTATION_PENDING=true",
        "Automated security review support is not cybersecurity certification or completed external security review.",
    ]
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_hash_record(summary: Dict[str, Any], summary_path: Path, log_path: Path, hash_path: Path) -> None:
    lines = [
        "AEM-EVOLVE v4.0 Automated Security Review Support Hash Record",
        f"generated_utc={summary['generated_utc']}",
        "hash_algorithm=SHA-256",
        "claim_boundary=automated_security_support_only_not_external_security_review",
        "",
        f"{sha256_bytes(summary_path.read_bytes())}  {SUMMARY_NAME}",
        f"{sha256_bytes(log_path.read_bytes())}  {LOG_NAME}",
        "",
        "Evidence input hashes:",
    ]
    for item in summary["evidence_inputs"]:
        lines.append(f"{item['sha256']}  {item['path']}  source={item['source']}")
        lines.append(f"{item['canonical_sha256']}  {item['path']}  canonical=json_sort_keys_no_whitespace_utf8")
    lines.append("")
    lines.append("Dependency manifest hashes:")
    for item in summary["dependency_manifests"]:
        lines.append(f"{item['sha256']}  {item['path']}  source={item['source']}")
    lines.append("")
    lines.append("external_security_review_completed=false")
    lines.append("cybersecurity_certification=false")
    lines.append("absence_of_all_vulnerabilities=false")
    hash_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory for security review support artifacts")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / SUMMARY_NAME
    log_path = output_dir / LOG_NAME
    hash_path = output_dir / HASH_RECORD_NAME

    summary = build_summary()
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_log(summary, log_path)
    write_hash_record(summary, summary_path, log_path, hash_path)

    print(f"AUTOMATED_SECURITY_REVIEW_SUPPORT={summary['automated_security_review_support']}")
    print(f"critical_findings={summary['critical_findings']}")
    print(f"secret_findings={summary['secret_findings']}")
    print("external_security_review_completed=false")
    print("cybersecurity_certification=false")
    print("HUMAN_ATTESTATION_PENDING=true")
    return 0 if summary["automated_security_review_support"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
