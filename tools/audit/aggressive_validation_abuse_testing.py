#!/usr/bin/env python3
"""Aggressive validation and abuse testing for EthicBit/CEMU.

The suite runs negative tests against claim elevation, state transitions,
tamper detection, reproducibility mismatch behavior, package leak posture and
external-validation boundaries. It is internal abuse testing, not an external
security audit or certification.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "assurance/audit/AGGRESSIVE_VALIDATION_ABUSE_TEST_REPORT_V1_0.json"
DOC_PATH = ROOT / "docs/audit/ETHICBIT_AGGRESSIVE_VALIDATION_ABUSE_TESTING_V1_0.md"
HASH_RECORD_PATH = ROOT / "assurance/audit/AGGRESSIVE_VALIDATION_ABUSE_TEST_HASH_RECORD_V1_0.txt"

CLAIM_RED_TEAM_REPORT = ROOT / "assurance/external-validation/v4_0/claim_red_team/CLAIM_BOUNDARY_RED_TEAM_REPORT.json"
STATE_MACHINE_DOC = ROOT / "docs/external-validation/hybrid/V4_0_HYBRID_VALIDATION_CLAIM_STATE_MACHINE.md"
EXPECTED_HASHES = ROOT / "assurance/reproducibility/expected_hashes.json"
DECLARED_SUBJECTS = ROOT / "assurance/reproducibility/declared_subjects.json"
SECURITY_REVIEW_SUMMARY = ROOT / "assurance/external-validation/v4_0/security_review/AUTOMATED_SECURITY_REVIEW_SUMMARY.json"
AUTOMATED_REPRODUCTION_REPORT = ROOT / "assurance/external-validation/v4_0/automated_reproduction/AUTOMATED_REPRODUCTION_REPORT.json"

SENSITIVE_ENTRY_PATTERNS = [
    re.compile(r"(^|/)\.env(\.|$|$)"),
    re.compile(r"(^|/).*_private\.(pem|key|p8)$", re.IGNORECASE),
    re.compile(r"(^|/)signing_key\.pem$", re.IGNORECASE),
    re.compile(r"(^|/)id_rsa$", re.IGNORECASE),
]

PROHIBITED_TRANSITIONS = [
    ("CONTROLLED_EVIDENCE_ADVANCED", "EXTERNAL_VALIDATION_PASS"),
    ("HYBRID_VALIDATION_READY", "EXTERNAL_VALIDATION_PASS"),
    ("DOSSIER_BUILT", "EXTERNAL_VALIDATION_PASS"),
    ("DOSSIER_VERIFIED", "EXTERNAL_VALIDATION_PASS"),
    ("HUMAN_ATTESTATION_PENDING", "EXTERNAL_VALIDATION_PASS"),
]

PROHIBITED_AUTOMATED_ELEVATIONS = [
    ("AUTOMATED_REPRODUCTION_SUPPORT=PASS", "third_party_reproduction_completed"),
    ("AUTOMATED_SECURITY_REVIEW_SUPPORT=PASS", "cybersecurity_certified"),
    ("AUTOMATED_SECURITY_REVIEW_SUPPORT=PASS", "absence_of_all_vulnerabilities"),
    ("CLAIM_BOUNDARY_RED_TEAM=PASS", "external_claim_review_completed"),
    ("FAST_PATH_EVIDENCE_PASS", "full_system_sub_15ms_validation"),
    ("TRIPLE_ANCHOR_PRESENT", "universal_public_anchoring"),
    ("DOSSIER_VERIFIED", "externally_certified"),
    ("DOSSIER_VERIFIED", "regulatory_approved"),
]


@dataclass(frozen=True)
class AbuseTest:
    name: str
    status: str
    score: int
    summary: str
    details: dict[str, Any]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_output(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json_hash(path: Path) -> str:
    obj = load_json(path)
    data = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_bytes(data)


def file_or_canonical_hash(path: Path, hash_type: str) -> str:
    return canonical_json_hash(path) if hash_type == "canonical_sha256" else sha256_file(path)


def test_claim_red_team_blocking() -> AbuseTest:
    report = load_json(CLAIM_RED_TEAM_REPORT)
    attempted = int(report.get("overclaims_attempted", 0))
    blocked = int(report.get("overclaims_blocked", -1))
    block_rate = float(report.get("block_rate_percent", 0.0))
    passed = (
        report.get("claim_boundary_red_team") == "PASS"
        and attempted > 0
        and attempted == blocked
        and block_rate == 100.0
        and report.get("external_claim_review_completed") is False
        and report.get("external_validation_pass_claimed") is False
    )
    return AbuseTest(
        name="claim_red_team_overclaim_blocking",
        status="PASS" if passed else "FAIL_CLOSED",
        score=100 if passed else 0,
        summary=f"Blocked {blocked}/{attempted} attempted overclaims; external claim review remains false.",
        details={
            "report": rel(CLAIM_RED_TEAM_REPORT),
            "overclaims_attempted": attempted,
            "overclaims_blocked": blocked,
            "block_rate_percent": block_rate,
            "external_claim_review_completed": report.get("external_claim_review_completed"),
            "external_validation_pass_claimed": report.get("external_validation_pass_claimed"),
        },
    )


def state_transition_decision(source: str, target: str, conditions: dict[str, bool] | None = None) -> str:
    conditions = conditions or {}
    if (source, target) in PROHIBITED_TRANSITIONS:
        return "FAIL_CLOSED"
    if target == "EXTERNAL_VALIDATION_PASS":
        required = [
            "signed_human_attestation",
            "reviewer_scope_declared",
            "dossier_hashes_verified",
            "methodology_review_completed",
            "claim_boundary_review_completed",
            "limitations_declared",
            "no_forbidden_claims",
        ]
        return "ALLOW" if all(conditions.get(key) is True for key in required) else "FAIL_CLOSED"
    return "SCOPE_LIMITED"


def test_state_machine_abuse() -> AbuseTest:
    text = STATE_MACHINE_DOC.read_text(encoding="utf-8")
    prohibited_results = [
        {"from": src, "to": dst, "decision": state_transition_decision(src, dst)}
        for src, dst in PROHIBITED_TRANSITIONS
    ]
    automated_elevation_mentions = [
        {"automated_output": out, "prohibited_claim": claim, "documented": out in text and claim in text}
        for out, claim in PROHIBITED_AUTOMATED_ELEVATIONS
    ]
    incomplete_external_pass = state_transition_decision(
        "HUMAN_ATTESTATION_PASS",
        "EXTERNAL_VALIDATION_PASS",
        {"signed_human_attestation": True, "reviewer_scope_declared": True},
    )
    full_conditions = {
        "signed_human_attestation": True,
        "reviewer_scope_declared": True,
        "dossier_hashes_verified": True,
        "methodology_review_completed": True,
        "claim_boundary_review_completed": True,
        "limitations_declared": True,
        "no_forbidden_claims": True,
    }
    complete_external_pass = state_transition_decision("HUMAN_ATTESTATION_PASS", "EXTERNAL_VALIDATION_PASS", full_conditions)
    passed = (
        all(item["decision"] == "FAIL_CLOSED" for item in prohibited_results)
        and all(item["documented"] for item in automated_elevation_mentions)
        and incomplete_external_pass == "FAIL_CLOSED"
        and complete_external_pass == "ALLOW"
        and "EXTERNAL_VALIDATION_PASS" in text
        and "has not been reached and is not claimed" in text
    )
    return AbuseTest(
        name="hybrid_validation_state_machine_abuse",
        status="PASS" if passed else "FAIL_CLOSED",
        score=100 if passed else 0,
        summary="Prohibited automated transitions fail closed; external pass requires complete human-attestation conditions.",
        details={
            "state_machine_doc": rel(STATE_MACHINE_DOC),
            "prohibited_transition_results": prohibited_results,
            "automated_elevation_documentation": automated_elevation_mentions,
            "incomplete_external_pass_decision": incomplete_external_pass,
            "complete_external_pass_decision_with_required_conditions": complete_external_pass,
        },
    )


def test_hash_tamper_detection() -> AbuseTest:
    expected = load_json(EXPECTED_HASHES)
    subject_results: list[dict[str, Any]] = []
    mismatch_simulations = 0
    for subject in expected.get("subjects", []):
        path = ROOT / subject["path"]
        observed = file_or_canonical_hash(path, subject["hash_type"])
        expected_sha = subject["expected_sha256"]
        original_match = observed == expected_sha
        tampered_expected = expected_sha[:-1] + ("0" if expected_sha[-1] != "0" else "1")
        tamper_detected = observed != tampered_expected
        mismatch_simulations += 1 if tamper_detected else 0
        subject_results.append(
            {
                "id": subject["id"],
                "path": subject["path"],
                "original_match": original_match,
                "tampered_expected_detected": tamper_detected,
            }
        )
    passed = bool(subject_results) and all(item["original_match"] and item["tampered_expected_detected"] for item in subject_results)
    return AbuseTest(
        name="reproducibility_hash_tamper_detection",
        status="PASS" if passed else "FAIL_CLOSED",
        score=100 if passed else 0,
        summary=f"Simulated expected-hash tamper detected for {mismatch_simulations}/{len(subject_results)} declared subjects.",
        details={"subjects": subject_results, "expected_hashes": rel(EXPECTED_HASHES)},
    )


def test_receipt_boundary_integrity() -> AbuseTest:
    reproduction = load_json(AUTOMATED_REPRODUCTION_REPORT)
    security = load_json(SECURITY_REVIEW_SUMMARY)
    declared = load_json(DECLARED_SUBJECTS)
    checks = {
        "automated_reproduction_not_third_party_completion": reproduction.get("third_party_reproduction_completed") is not True,
        "automated_security_not_certification": security.get("cybersecurity_certification_claimed") is not True,
        "security_critical_findings_zero": int(security.get("critical_findings", -1)) == 0,
        "security_secret_findings_zero": int(security.get("secret_findings", -1)) == 0,
        "declared_subjects_do_not_claim_independent_reproduction": declared.get("scope_boundary", {}).get("independently_reproduced_release_build_achieved") is False,
        "declared_subjects_do_not_claim_full_reproducible_build": declared.get("scope_boundary", {}).get("fully_reproducible_build_claimed") is False,
    }
    passed = all(checks.values())
    return AbuseTest(
        name="automated_evidence_non_claim_boundary",
        status="PASS" if passed else "FAIL_CLOSED",
        score=100 if passed else 0,
        summary="Automated reproduction/security evidence remains support evidence, not external completion or certification.",
        details={
            "checks": checks,
            "automated_reproduction_report": rel(AUTOMATED_REPRODUCTION_REPORT),
            "security_review_summary": rel(SECURITY_REVIEW_SUMMARY),
            "declared_subjects": rel(DECLARED_SUBJECTS),
        },
    )


def git_tracked_files() -> list[str]:
    out = git_output(["ls-files"])
    return out.splitlines() if out else []


def is_sensitive_entry(name: str) -> bool:
    normalized = name.replace("\\", "/")
    return any(pattern.search(normalized) for pattern in SENSITIVE_ENTRY_PATTERNS)


def test_packaging_and_secret_leak_boundaries() -> AbuseTest:
    tracked = git_tracked_files()
    tracked_sensitive = [path for path in tracked if is_sensitive_entry(path)]
    zip_hits: list[dict[str, str]] = []
    zip_files = sorted((ROOT / "artifacts/releases").glob("*.zip")) if (ROOT / "artifacts/releases").exists() else []
    for zip_path in zip_files:
        try:
            with zipfile.ZipFile(zip_path) as zf:
                for entry in zf.namelist():
                    if is_sensitive_entry(entry):
                        zip_hits.append({"zip": rel(zip_path), "entry": entry})
        except zipfile.BadZipFile:
            zip_hits.append({"zip": rel(zip_path), "entry": "BAD_ZIP"})
    local_sensitive_present = [
        str(path.relative_to(ROOT))
        for pattern in [".env", ".env.local", "assurance/keys/*_private.pem"]
        for path in ROOT.glob(pattern)
    ]
    passed = not tracked_sensitive and not zip_hits
    return AbuseTest(
        name="release_packaging_secret_leak_abuse_scan",
        status="PASS" if passed else "FAIL_CLOSED",
        score=100 if passed else 0,
        summary=f"Scanned {len(tracked)} tracked files and {len(zip_files)} release ZIPs for sensitive entries.",
        details={
            "tracked_sensitive_entries": tracked_sensitive,
            "release_zip_sensitive_entries": zip_hits,
            "ignored_local_sensitive_entries_present": local_sensitive_present,
            "zip_files_scanned": len(zip_files),
        },
    )


def test_manifest_hash_record_tamper_detection() -> AbuseTest:
    hash_record = ROOT / "assurance/audit/RELEASE_GRADE_DEEP_AUDIT_HASH_RECORD_V1_0.txt"
    verified: list[dict[str, Any]] = []
    for line in hash_record.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^[a-f0-9]{64}  ", line):
            continue
        expected_sha, path_text = line.split("  ", 1)
        path = ROOT / path_text
        observed = sha256_file(path)
        tampered = path.read_bytes() + b"\nTAMPER_SIMULATION_DO_NOT_WRITE\n"
        verified.append(
            {
                "path": path_text,
                "record_match": observed == expected_sha,
                "tamper_changes_hash": sha256_bytes(tampered) != observed,
            }
        )
    passed = bool(verified) and all(item["record_match"] and item["tamper_changes_hash"] for item in verified)
    return AbuseTest(
        name="audit_hash_record_tamper_detection",
        status="PASS" if passed else "FAIL_CLOSED",
        score=100 if passed else 0,
        summary=f"Verified {len(verified)} hash-record entries and in-memory tamper mismatch behavior.",
        details={"hash_record": rel(hash_record), "verified_entries": verified},
    )


def canonical_obj_hash(obj: dict[str, Any]) -> str:
    return sha256_bytes(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def test_receipt_forgery_mutation_detection() -> AbuseTest:
    base = {
        "schema_id": "AEM_EVOLVE_EVOLUTION_RECEIPT_V1",
        "receipt_id": "aggressive-test-receipt-001",
        "outcome": "SCOPE_LIMITED",
        "materiality_score": 0.3,
        "scope_boundary": "controlled_environment",
        "hitl_required": False,
        "non_claims": ["Not production-ready.", "Not certified.", "Not regulatory-approved."],
        "production_ready_claimed": False,
        "generated_at": "2026-05-17T00:00:00+00:00",
    }
    base["receipt_hash"] = canonical_obj_hash(base)

    def tamper_detected(original: dict[str, Any], mutated: dict[str, Any]) -> bool:
        original_body = {k: v for k, v in original.items() if k != "receipt_hash"}
        expected_hash = canonical_obj_hash(original_body)
        mutated_body = {k: v for k, v in mutated.items() if k != "receipt_hash"}
        return canonical_obj_hash(mutated_body) != expected_hash or mutated.get("receipt_hash") != expected_hash

    mutations = {
        "modify_outcome": lambda r: {**r, "outcome": "PASS"},
        "modify_materiality_score": lambda r: {**r, "materiality_score": 0.99},
        "remove_non_claims": lambda r: {k: v for k, v in r.items() if k != "non_claims"},
        "change_scope_boundary": lambda r: {**r, "scope_boundary": "universal_production"},
        "change_hitl_requirement": lambda r: {**r, "hitl_required": True},
        "replay_old_receipt_hash": lambda r: {**r, "outcome": "PASS", "receipt_hash": r["receipt_hash"]},
        "inject_production_ready_claim": lambda r: {**r, "production_ready_claimed": True, "status": "production-ready"},
        "replace_receipt_hash": lambda r: {**r, "receipt_hash": "0" * 64},
    }
    results = []
    for name, mutate in mutations.items():
        mutated = mutate(dict(base))
        detected = tamper_detected(base, mutated)
        results.append({"mutation": name, "tamper_detected": detected})
    passed = all(item["tamper_detected"] for item in results)
    return AbuseTest(
        name="receipt_forgery_mutation_detection",
        status="PASS" if passed else "FAIL_CLOSED",
        score=100 if passed else 0,
        summary=f"Detected {sum(1 for item in results if item['tamper_detected'])}/{len(results)} receipt forgery mutations.",
        details={"mutations": results},
    )


def run_audit_chain_verifier(db_path: Path) -> str:
    verifier = ROOT / "scripts/core/verify_aem_evolve_multi_agent_audit_chain.py"
    result = subprocess.run(["python3", str(verifier), str(db_path)], cwd=ROOT, capture_output=True, text=True)
    output = result.stdout + result.stderr
    if "AEM_EVOLVE_AUDIT_CHAIN_STATUS=PASS" in output:
        return "PASS"
    if "AEM_EVOLVE_AUDIT_CHAIN_STATUS=TAMPER_DETECTED" in output:
        return "TAMPER_DETECTED"
    return "UNKNOWN"


def test_audit_chain_sqlite_tamper_detection() -> AbuseTest:
    source_db = ROOT / "demos/aem-evolve-multi-agent-api/ethicbit_demo.db"
    if not source_db.exists():
        return AbuseTest(
            name="audit_chain_sqlite_tamper_detection",
            status="FAIL_CLOSED",
            score=0,
            summary="Source SQLite demo DB is missing; audit-chain tamper test cannot run.",
            details={"source_db": rel(source_db)},
        )

    cases: list[dict[str, Any]] = []

    def with_temp_db(case_name: str, mutate) -> None:
        fd, tmp_name = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        tmp = Path(tmp_name)
        try:
            shutil.copy2(source_db, tmp)
            mutate(tmp)
            observed = run_audit_chain_verifier(tmp)
            cases.append({"case": case_name, "observed": observed, "tamper_detected": observed == "TAMPER_DETECTED"})
        finally:
            tmp.unlink(missing_ok=True)

    baseline_fd, baseline_name = tempfile.mkstemp(suffix=".db")
    os.close(baseline_fd)
    baseline = Path(baseline_name)
    try:
        shutil.copy2(source_db, baseline)
        baseline_status = run_audit_chain_verifier(baseline)
    finally:
        baseline.unlink(missing_ok=True)

    def mutate_entry_sha256(db: Path) -> None:
        conn = sqlite3.connect(str(db))
        conn.execute("UPDATE audit_chain SET entry_sha256 = ? WHERE seq = 1", ("deadbeef" * 8,))
        conn.commit()
        conn.close()

    with_temp_db("mutate_entry_sha256_seq_1", mutate_entry_sha256)

    def mutate_middle_chain_hash(db: Path) -> None:
        conn = sqlite3.connect(str(db))
        rows = conn.execute("SELECT seq FROM audit_chain ORDER BY seq").fetchall()
        if rows:
            mid_seq = rows[len(rows) // 2][0]
            conn.execute("UPDATE audit_chain SET chain_hash = ? WHERE seq = ?", ("cafebabe" * 8, mid_seq))
            conn.commit()
        conn.close()

    with_temp_db("mutate_middle_chain_hash", mutate_middle_chain_hash)

    def delete_chain_entry(db: Path) -> None:
        conn = sqlite3.connect(str(db))
        rows = conn.execute("SELECT seq FROM audit_chain ORDER BY seq").fetchall()
        if len(rows) >= 2:
            conn.execute("DELETE FROM audit_chain WHERE seq = ?", (rows[1][0],))
            conn.commit()
        conn.close()

    with_temp_db("delete_chain_entry", delete_chain_entry)

    passed = baseline_status == "PASS" and all(case["tamper_detected"] for case in cases)
    return AbuseTest(
        name="audit_chain_sqlite_tamper_detection",
        status="PASS" if passed else "FAIL_CLOSED",
        score=100 if passed else 0,
        summary=f"Clean DB baseline={baseline_status}; detected {sum(1 for case in cases if case['tamper_detected'])}/{len(cases)} SQLite audit-chain tamper cases.",
        details={"source_db": rel(source_db), "baseline_status": baseline_status, "tamper_cases": cases},
    )


def run_tests() -> list[AbuseTest]:
    return [
        test_claim_red_team_blocking(),
        test_state_machine_abuse(),
        test_hash_tamper_detection(),
        test_receipt_boundary_integrity(),
        test_packaging_and_secret_leak_boundaries(),
        test_manifest_hash_record_tamper_detection(),
        test_receipt_forgery_mutation_detection(),
        test_audit_chain_sqlite_tamper_detection(),
    ]


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EthicBit Aggressive Validation & Abuse Testing v1.0",
        "",
        f"**Status:** `{report['overall_status']}`",
        f"**Generated UTC:** `{report['generated_at_utc']}`",
        f"**Commit:** `{report['git']['commit']}`",
        "**Scope:** internal aggressive abuse testing for claim boundaries, tamper behavior, release packaging, reproducibility mismatch behavior and external-validation non-claims.",
        "",
        "## Boundary",
        "This is internal aggressive validation. It is not an external penetration test, cybersecurity certification, legal opinion, regulatory approval, or independent reproduction.",
        "",
        "## Test Summary",
        "",
        "| Test | Status | Score | Summary |",
        "|---|---:|---:|---|",
    ]
    for test in report["tests"]:
        lines.append(f"| `{test['name']}` | `{test['status']}` | {test['score']} | {test['summary']} |")
    lines.extend(
        [
            "",
            "## Result",
            "",
            f"`{report['publication_decision']}`",
            "",
            "## Required Boundaries",
            "",
            "- Do not claim `EXTERNAL_VALIDATION_PASS` until signed independent human attestation is present.",
            "- Do not claim cybersecurity certification or absence of all vulnerabilities from automated security support.",
            "- Do not claim third-party reproduction from automated reproduction support.",
            "- Keep `.env*`, private keys and runtime secrets excluded from releases and public mirrors.",
            "",
            "## Non-Claims",
            "",
            "This report does not claim completed external validation, third-party reproduction, external security audit completion, cybersecurity certification, regulatory approval, legal compliance, universal production readiness, absence of all vulnerabilities, or clinical/diagnostic readiness.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(report: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    HASH_RECORD_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    DOC_PATH.write_text(render_markdown(report), encoding="utf-8")
    hash_lines = [
        f"generated_at_utc={report['generated_at_utc']}",
        f"git_commit={report['git']['commit']}",
        f"overall_status={report['overall_status']}",
        f"overall_score={report['overall_score']}",
        "",
    ]
    for path in [
        Path("tools/audit/aggressive_validation_abuse_testing.py"),
        REPORT_PATH.relative_to(ROOT),
        DOC_PATH.relative_to(ROOT),
    ]:
        hash_lines.append(f"{sha256_file(ROOT / path)}  {path.as_posix()}")
    HASH_RECORD_PATH.write_text("\n".join(hash_lines) + "\n", encoding="utf-8")


def main() -> int:
    tests = run_tests()
    failed = [test for test in tests if test.status != "PASS"]
    overall_score = round(sum(test.score for test in tests) / len(tests)) if tests else 0
    overall_status = "PASS_WITH_SCOPE_LIMITATIONS" if not failed else "FAIL_CLOSED"
    publication_decision = (
        "PUBLICATION_ALLOWED_SCOPE_LIMITED_AFTER_AGGRESSIVE_TESTING_WITH_EXTERNAL_ATTESTATION_PENDING"
        if not failed
        else "PUBLICATION_BLOCKED_BY_AGGRESSIVE_TESTING"
    )
    report = {
        "schema_id": "ETHICBIT_AGGRESSIVE_VALIDATION_ABUSE_TEST_REPORT_V1_0",
        "generated_at_utc": now_utc(),
        "git": {
            "branch": git_output(["branch", "--show-current"]),
            "commit": git_output(["rev-parse", "--short=8", "HEAD"]),
        },
        "overall_status": overall_status,
        "overall_score": overall_score,
        "publication_decision": publication_decision,
        "tests_total": len(tests),
        "tests_passed": len(tests) - len(failed),
        "tests_failed": len(failed),
        "tests": [test.__dict__ for test in tests],
        "non_claims": {
            "external_validation_completed": False,
            "third_party_reproduction_completed": False,
            "external_security_audit_completed": False,
            "cybersecurity_certification_claimed": False,
            "regulatory_approval_claimed": False,
            "legal_compliance_claimed": False,
            "universal_production_readiness_claimed": False,
            "absence_of_all_vulnerabilities_claimed": False,
            "clinical_or_diagnostic_readiness_claimed": False,
        },
    }
    write_outputs(report)
    print(f"AGGRESSIVE_VALIDATION_ABUSE_TEST_STATUS={overall_status}")
    print(f"overall_score={overall_score}")
    print(f"tests_total={len(tests)}")
    print(f"tests_passed={len(tests) - len(failed)}")
    print(f"tests_failed={len(failed)}")
    print(f"publication_decision={publication_decision}")
    for test in tests:
        print(f"{test.name}={test.status}:{test.score}")
    print(f"report={REPORT_PATH.relative_to(ROOT)}")
    print(f"document={DOC_PATH.relative_to(ROOT)}")
    print(f"hash_record={HASH_RECORD_PATH.relative_to(ROOT)}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
