#!/usr/bin/env python3
"""Build AEM-EVOLVE v4.0 automated reproduction support evidence.

This script packages committed controlled evidence into an automated support report.
It intentionally does not claim third-party reproduction or external validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT / "assurance/external-validation/v4_0/automated_reproduction"
REPORT_PATH = OUTPUT_DIR / "AUTOMATED_REPRODUCTION_REPORT.json"
LOG_PATH = OUTPUT_DIR / "AUTOMATED_REPRODUCTION_LOG.txt"
HASH_RECORD_PATH = OUTPUT_DIR / "AUTOMATED_REPRODUCTION_HASH_RECORD.txt"

INPUT_PATHS = {
    "ai_me_v3_1_aggregate": "assurance/ai-me/v3_1/AI_ME_V3_1_AGGREGATE_REPORT.json",
    "fast_path_v1_0": "assurance/fast-path/v1/FAST_PATH_VERIFICATION_REPORT.json",
    "v4_0_controlled_evidence": "assurance/v4_0/V4_0_CONTROLLED_EVIDENCE_REPORT.json",
    "claim_boundary_red_team": "assurance/external-validation/v4_0/claim_red_team/CLAIM_BOUNDARY_RED_TEAM_REPORT.json",
    "notary_dossier_manifest": "assurance/external-validation/v4_0/notary_dossier/DOSSIER_MANIFEST.json",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_sha256(obj: Any) -> str:
    data = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_bytes(data)


def read_committed_bytes(repo_path: str) -> Tuple[bytes, str]:
    """Read from HEAD to avoid uncommitted local evidence drift when possible."""
    result = subprocess.run(
        ["git", "show", f"HEAD:{repo_path}"],
        cwd=ROOT,
        text=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode == 0:
        return result.stdout, "git_HEAD"

    local_path = ROOT / repo_path
    if local_path.exists():
        return local_path.read_bytes(), "local_filesystem_fallback"

    stderr = result.stderr.decode("utf-8", errors="replace").strip()
    raise FileNotFoundError(f"Unable to read evidence input {repo_path}: {stderr}")


def load_input(name: str, repo_path: str) -> Dict[str, Any]:
    raw, source = read_committed_bytes(repo_path)
    obj = json.loads(raw.decode("utf-8"))
    return {
        "name": name,
        "path": repo_path,
        "source": source,
        "sha256": sha256_bytes(raw),
        "canonical_sha256": canonical_json_sha256(obj),
        "json": obj,
    }


def check(condition: bool, check_id: str, status_when_true: str, status_when_false: str, detail: str) -> Dict[str, Any]:
    return {
        "check_id": check_id,
        "status": status_when_true if condition else status_when_false,
        "passed": bool(condition),
        "detail": detail,
    }


def build_report() -> Dict[str, Any]:
    inputs = {name: load_input(name, path) for name, path in INPUT_PATHS.items()}

    ai_me = inputs["ai_me_v3_1_aggregate"]["json"]
    fast_path = inputs["fast_path_v1_0"]["json"]
    v4 = inputs["v4_0_controlled_evidence"]["json"]
    red_team = inputs["claim_boundary_red_team"]["json"]
    dossier = inputs["notary_dossier_manifest"]["json"]

    checks: List[Dict[str, Any]] = [
        check(
            ai_me.get("aggregate_outcome") == "PASS" and ai_me.get("gates_pass") == 12,
            "AI_ME_V3_1",
            "PASS",
            "FAIL_CLOSED",
            "AI-ME v3.1 aggregate must be PASS with 12 passing gates.",
        ),
        check(
            fast_path.get("status") == "EVIDENCE_PASS"
            and fast_path.get("scenarios_executed") == 9
            and fast_path.get("scenarios_matched_expected") is True,
            "FAST_PATH_V1_0",
            "PASS",
            "FAIL_CLOSED",
            "Fast Path v1.0 must be EVIDENCE_PASS with 9 matched scenarios.",
        ),
        check(
            v4.get("status") == "CONTROLLED_EVIDENCE_PARTIAL"
            and v4.get("criteria_controlled_pass") == 5
            and v4.get("criteria_pending_external") == 3
            and v4.get("v4_0_external_validation_release_claimed") is False,
            "V4_0_CONTROLLED_EVIDENCE",
            "CONTROLLED_EVIDENCE_PARTIAL_CONFIRMED",
            "FAIL_CLOSED",
            "v4.0 must remain 5/8 controlled evidence with 3 external criteria pending.",
        ),
        check(
            red_team.get("claim_boundary_red_team") == "PASS"
            and red_team.get("overclaims_failed_to_block") == 0
            and red_team.get("external_claim_review_completed") is False,
            "CLAIM_BOUNDARY_RED_TEAM",
            "PASS",
            "FAIL_CLOSED",
            "Claim red-team must block all attempted overclaims without claiming external review completion.",
        ),
        check(
            dossier.get("human_attestation_status") == "HUMAN_ATTESTATION_PENDING"
            and dossier.get("external_validation_pass_claimed") is False
            and dossier.get("third_party_reproduction_completed") is False,
            "NOTARY_DOSSIER_BOUNDARY",
            "HUMAN_ATTESTATION_PENDING_CONFIRMED",
            "FAIL_CLOSED",
            "Notary dossier must preserve human attestation pending and no external validation pass claim.",
        ),
    ]

    all_passed = all(item["passed"] for item in checks)
    status = "AUTOMATED_REPRODUCTION_SUPPORT_PASS" if all_passed else "AUTOMATED_REPRODUCTION_SUPPORT_FAIL_CLOSED"
    support = "PASS" if all_passed else "FAIL_CLOSED"

    evidence_inputs = []
    for name, loaded in inputs.items():
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
        "schema_id": "AEM_EVOLVE_V4_0_AUTOMATED_REPRODUCTION_SUPPORT_REPORT_V1",
        "report_type": "AUTOMATED_REPRODUCTION_SUPPORT_REPORT",
        "version": "4.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "automated_reproduction_support": support,
        "pre_report_full_stack_verification": "PASS" if all_passed else "FAIL_CLOSED",
        "ai_me_v3_1": "PASS" if checks[0]["passed"] else "FAIL_CLOSED",
        "fast_path_v1_0": "PASS" if checks[1]["passed"] else "FAIL_CLOSED",
        "v4_0_controlled_evidence": "CONTROLLED_EVIDENCE_PARTIAL" if checks[2]["passed"] else "FAIL_CLOSED",
        "claim_boundary_red_team": "PASS" if checks[3]["passed"] else "FAIL_CLOSED",
        "notary_dossier_human_attestation": "HUMAN_ATTESTATION_PENDING" if checks[4]["passed"] else "FAIL_CLOSED",
        "evidence_inputs": evidence_inputs,
        "checks": checks,
        "claim_boundary": {
            "automated_reproduction_support_only": True,
            "automated_pipeline_may_claim_third_party_reproduction": False,
            "automated_pipeline_may_claim_external_validation_pass": False,
            "human_attestation_required_for_external_validation_elevation": True,
            "human_attestation_status": "HUMAN_ATTESTATION_PENDING",
        },
        "non_claims": {
            "third_party_reproduction_completed": False,
            "completed_external_validation": False,
            "completed_external_security_review": False,
            "completed_external_claim_review": False,
            "external_certification": False,
            "cybersecurity_certification": False,
            "regulatory_approval": False,
            "financial_advice": False,
            "clinical_or_diagnostic_readiness": False,
            "universal_production_readiness": False,
            "full_system_sub_15ms_validation": False,
            "universal_public_anchoring": False,
        },
        "notes": (
            "Automated reproduction support is not third-party reproduction completion unless "
            "independently reviewed and attested by an external reviewer."
        ),
    }


def write_log(report: Dict[str, Any]) -> None:
    lines = [
        "AEM-EVOLVE v4.0 Automated Reproduction Support",
        f"generated_utc={report['generated_utc']}",
        f"AUTOMATED_REPRODUCTION_SUPPORT={report['automated_reproduction_support']}",
        f"PRE_REPORT_FULL_STACK_VERIFICATION={report['pre_report_full_stack_verification']}",
        f"AI_ME_V3_1={report['ai_me_v3_1']}",
        f"FAST_PATH_V1_0={report['fast_path_v1_0']}",
        f"V4_0_CONTROLLED_EVIDENCE={report['v4_0_controlled_evidence']}",
        f"CLAIM_BOUNDARY_RED_TEAM={report['claim_boundary_red_team']}",
        "third_party_reproduction_completed=false",
        "external_validation_pass_claimed=false",
        "HUMAN_ATTESTATION_PENDING=true",
        "Automated reproduction support is not third-party reproduction completion.",
    ]
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_hash_record(report: Dict[str, Any]) -> None:
    entries = [
        ("AUTOMATED_REPRODUCTION_REPORT.json", REPORT_PATH),
        ("AUTOMATED_REPRODUCTION_LOG.txt", LOG_PATH),
    ]
    lines = [
        "AEM-EVOLVE v4.0 Automated Reproduction Support Hash Record",
        f"generated_utc={report['generated_utc']}",
        "hash_algorithm=SHA-256",
        "claim_boundary=automated_support_only_not_third_party_reproduction",
        "",
    ]
    for label, path in entries:
        lines.append(f"{sha256_bytes(path.read_bytes())}  {label}")
    lines.append("")
    lines.append("Evidence input hashes:")
    for item in report["evidence_inputs"]:
        lines.append(f"{item['sha256']}  {item['path']}  source={item['source']}")
        lines.append(f"{item['canonical_sha256']}  {item['path']}  canonical=json_sort_keys_no_whitespace_utf8")
    lines.append("")
    lines.append("third_party_reproduction_completed=false")
    lines.append("external_validation_pass_claimed=false")
    HASH_RECORD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    global OUTPUT_DIR, REPORT_PATH, LOG_PATH, HASH_RECORD_PATH

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Output directory for report artifacts")
    args = parser.parse_args()

    OUTPUT_DIR = Path(args.output_dir).resolve()
    REPORT_PATH = OUTPUT_DIR / "AUTOMATED_REPRODUCTION_REPORT.json"
    LOG_PATH = OUTPUT_DIR / "AUTOMATED_REPRODUCTION_LOG.txt"
    HASH_RECORD_PATH = OUTPUT_DIR / "AUTOMATED_REPRODUCTION_HASH_RECORD.txt"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = build_report()
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_log(report)
    write_hash_record(report)

    print(f"AUTOMATED_REPRODUCTION_SUPPORT={report['automated_reproduction_support']}")
    print(f"PRE_REPORT_FULL_STACK_VERIFICATION={report['pre_report_full_stack_verification']}")
    print(f"AI_ME_V3_1={report['ai_me_v3_1']}")
    print(f"FAST_PATH_V1_0={report['fast_path_v1_0']}")
    print("third_party_reproduction_completed=false")
    print("external_validation_pass_claimed=false")
    print("HUMAN_ATTESTATION_PENDING=true")
    return 0 if report["automated_reproduction_support"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
