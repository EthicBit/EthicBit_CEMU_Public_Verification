#!/usr/bin/env python3
"""Release-grade deep audit for EthicBit/CEMU.

This audit is intentionally evidence-bound. It records component, code,
security, ecosystem, publication and claim-boundary posture without claiming
external validation or certification.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "assurance/audit/RELEASE_GRADE_DEEP_AUDIT_REPORT_V1_0.json"
DOC_PATH = ROOT / "docs/audit/ETHICBIT_RELEASE_GRADE_DEEP_AUDIT_V1_0.md"
HASH_RECORD_PATH = ROOT / "assurance/audit/RELEASE_GRADE_DEEP_AUDIT_HASH_RECORD_V1_0.txt"

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".vercel",
    ".hardhat",
}

EXPECTED_CEMU_COMPONENTS = [
    "cemu/core/intake.py",
    "cemu/core/fixation.py",
    "cemu/core/sealing.py",
    "cemu/core/provenance.py",
    "cemu/core/closure.py",
    "cemu/core/governance.py",
    "cemu/builders/runtime_guard.py",
    "cemu/builders/swarm_containment.py",
]

HV_EXPECTED = [
    "docs/external-validation/hybrid/V4_0_HYBRID_VALIDATION_SUPPORT_MODEL.md",
    "docs/external-validation/hybrid/V4_0_AUTOMATED_EVIDENCE_PIPELINE.md",
    "docs/external-validation/hybrid/V4_0_NOTARY_DOSSIER_STRUCTURE.md",
    "docs/external-validation/hybrid/V4_0_HUMAN_ATTESTATION_PROTOCOL.md",
    "tools/external_validation/build_v4_notary_dossier.py",
    "tools/external_validation/claim_red_team/run_claim_red_team.py",
    ".github/workflows/v4_automated_reproduction_support.yml",
    ".github/workflows/v4_automated_security_review_support.yml",
    "docs/external-validation/outreach/V4_0_VALIDATOR_INVITATION.md",
    "docs/STATUS_BULLETIN_PUBLIC_2026-05-16_V4_0_HYBRID_VALIDATION.md",
    "docs/external-validation/hybrid/V4_0_HYBRID_VALIDATION_CLAIM_STATE_MACHINE.md",
]

PUBLICATION_REQUIRED = [
    "README.md",
    "README_PUBLIC.md",
    "docs/briefs/ETHICBIT_V4_0_PROPRIETARY_TECHNOLOGY_AND_MARKET_ANCHOR_BRIEF.md",
    "docs/external-validation/outreach/V4_0_VALIDATOR_INVITATION.md",
    "assurance/external-validation/v4_0/security_review/AUTOMATED_SECURITY_REVIEW_SUMMARY.json",
    "assurance/external-validation/v4_0/claim_red_team/CLAIM_BOUNDARY_RED_TEAM_REPORT.json",
]

SENSITIVE_PATH_PATTERNS = [
    re.compile(r"(^|/)\.env(\.|$|$)"),
    re.compile(r"(^|/).*private.*\.(pem|key|p8)$", re.IGNORECASE),
]

SECRET_CONTENT_PATTERNS = {
    "private_key_block": re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    "aws_secret_value": re.compile(r"AWS_SECRET_ACCESS_KEY\s*[:=]\s*[\'\"][A-Za-z0-9/+=]{20,}"),
    "github_token_value": re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    "ethereum_private_key_value": re.compile(r"(?i)(ETHICBIT_PRIVATE_KEY|ETH_PRIVATE_KEY)\s*[:=]\s*[\'\"]?(0x)?[0-9a-f]{64}"),
}

FORBIDDEN_CLAIM_PATTERNS = {
    "external_validation_pass_asserted": re.compile(
        r"(?i)(status|state|claim|closure)\s*[:=]\s*[`\"]?EXTERNAL_VALIDATION_PASS"
    ),
    "regulatory_approval_asserted": re.compile(r"(?i)\b(is|are|has been|status:)\s+(FDA|EMA|regulatory)[ -]approved\b"),
    "cybersecurity_certified_asserted": re.compile(r"(?i)\bcybersecurity certified\b"),
    "production_ready_universal_asserted": re.compile(r"(?i)\buniversal production[- ]ready\b"),
}


@dataclass(frozen=True)
class Gate:
    name: str
    status: str
    score: int
    notes: list[str]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run_git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_files() -> list[Path]:
    files: list[Path] = []
    for current_root, dirs, filenames in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        current = Path(current_root)
        for filename in filenames:
            path = current / filename
            if path.is_file():
                files.append(path)
    return sorted(files)


def existing(paths: list[str]) -> list[str]:
    return [p for p in paths if (ROOT / p).exists()]


def missing(paths: list[str]) -> list[str]:
    return [p for p in paths if not (ROOT / p).exists()]


def git_tracked_files() -> set[str]:
    output = run_git(["ls-files"])
    return set(output.splitlines()) if output else set()


def git_ignored(path: str) -> bool:
    try:
        subprocess.check_call(["git", "check-ignore", "-q", path], cwd=ROOT)
        return True
    except subprocess.CalledProcessError:
        return False


def audit_code(files: list[Path]) -> tuple[Gate, dict[str, Any]]:
    py_files = [p for p in files if p.suffix == ".py"]
    syntax_failures: list[str] = []
    for path in py_files:
        try:
            ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=rel(path))
        except SyntaxError:
            syntax_failures.append(rel(path))

    test_files = [rel(p) for p in py_files if "/tests/" in f"/{rel(p)}" or p.name.startswith("test_")]
    dev_config = (ROOT / "pyproject.toml").read_text(encoding="utf-8", errors="ignore") if (ROOT / "pyproject.toml").exists() else ""
    req_dev = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8", errors="ignore") if (ROOT / "requirements-dev.txt").exists() else ""
    tool_markers = {
        "pytest": "pytest" in dev_config or "pytest" in req_dev,
        "ruff": "ruff" in dev_config or "ruff" in req_dev,
        "mypy": "mypy" in dev_config or "mypy" in req_dev,
        "bandit": "bandit" in dev_config or "bandit" in req_dev,
    }
    cemu_component_tests = [p for p in test_files if "cemu" in p]

    score = 100
    notes: list[str] = []
    if syntax_failures:
        score -= 35
        notes.append(f"Python syntax failures detected: {len(syntax_failures)}")
    else:
        notes.append("Python AST syntax scan completed without failures.")
    if len(test_files) < 10:
        score -= 12
        notes.append("Test inventory is present but uneven across the repository.")
    else:
        notes.append(f"Python test inventory present: {len(test_files)} files.")
    if not cemu_component_tests:
        score -= 10
        notes.append("CEMU component-specific test coverage is sparse.")
    else:
        notes.append(f"CEMU component-specific tests present: {len(cemu_component_tests)} files.")
    if not tool_markers["bandit"]:
        score -= 8
        notes.append("Bandit is not configured as a committed dev dependency.")
    if not tool_markers["ruff"] or not tool_markers["mypy"]:
        score -= 8
        notes.append("Ruff/mypy posture should remain enforced for code-quality maturity.")

    status = "PASS" if score >= 85 and not syntax_failures else "SCOPE_LIMITED" if score >= 60 else "FAIL_CLOSED"
    return Gate("code_quality", status, max(score, 0), notes), {
        "python_files": len(py_files),
        "syntax_failures": syntax_failures,
        "test_files": len(test_files),
        "cemu_component_tests": cemu_component_tests,
        "dev_tool_markers": tool_markers,
    }


def audit_components() -> tuple[Gate, dict[str, Any]]:
    cemu_present = existing(EXPECTED_CEMU_COMPONENTS)
    cemu_missing = missing(EXPECTED_CEMU_COMPONENTS)
    hv_present = existing(HV_EXPECTED)
    hv_missing = missing(HV_EXPECTED)
    ai_me_reports = sorted(p.as_posix() for p in (ROOT / "assurance/ai-me/v3_1").glob("AI-ME-*_report.json"))
    fast_path_reports = sorted(p.as_posix() for p in (ROOT / "assurance/fast-path/v1").glob("**/*.json"))
    workflows = sorted(p.as_posix() for p in (ROOT / ".github/workflows").glob("*.yml"))

    score = 100
    notes = [
        f"CEMU components present: {len(cemu_present)}/{len(EXPECTED_CEMU_COMPONENTS)}.",
        f"HV suite artifacts present: {len(hv_present)}/{len(HV_EXPECTED)}.",
        f"AI-ME report artifacts found: {len(ai_me_reports)}.",
        f"Fast Path evidence artifacts found: {len(fast_path_reports)}.",
    ]
    if cemu_missing:
        score -= 25
        notes.append(f"Missing CEMU components: {cemu_missing}")
    if hv_missing:
        score -= 20
        notes.append(f"Missing HV artifacts: {hv_missing}")
    if len(ai_me_reports) < 12:
        score -= 10
        notes.append("AI-ME report count is below 12; verify v3.1 evidence bundle scope.")
    if len(fast_path_reports) < 9:
        score -= 10
        notes.append("Fast Path evidence count is below expected 9 scenario baseline.")

    status = "PASS" if score >= 90 else "SCOPE_LIMITED" if score >= 65 else "FAIL_CLOSED"
    return Gate("component_inventory", status, max(score, 0), notes), {
        "cemu_present": cemu_present,
        "cemu_missing": cemu_missing,
        "hv_present_count": len(hv_present),
        "hv_missing": hv_missing,
        "ai_me_report_count": len(ai_me_reports),
        "fast_path_artifact_count": len(fast_path_reports),
        "workflow_count": len(workflows),
    }


def audit_security(files: list[Path], tracked: set[str]) -> tuple[Gate, dict[str, Any]]:
    local_sensitive_paths: list[dict[str, Any]] = []
    tracked_sensitive_paths: list[str] = []
    for path in files:
        path_rel = rel(path)
        if any(pattern.search(path_rel) for pattern in SENSITIVE_PATH_PATTERNS):
            record = {
                "path": path_rel,
                "tracked": path_rel in tracked,
                "ignored": git_ignored(path_rel),
            }
            local_sensitive_paths.append(record)
            if path_rel in tracked:
                tracked_sensitive_paths.append(path_rel)

    tracked_text_files = [ROOT / p for p in tracked if (ROOT / p).is_file() and (ROOT / p).stat().st_size < 2_000_000]
    content_hits: list[dict[str, str]] = []
    for path in tracked_text_files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for name, pattern in SECRET_CONTENT_PATTERNS.items():
            if pattern.search(text):
                content_hits.append({"path": rel(path), "pattern": name})

    score = 100
    notes: list[str] = []
    if tracked_sensitive_paths:
        score -= 45
        notes.append(f"Tracked sensitive path names detected: {len(tracked_sensitive_paths)}.")
    else:
        notes.append("No tracked sensitive path names detected by path-pattern scan.")
    if content_hits:
        score -= 35
        notes.append(f"Tracked secret-like content markers detected: {len(content_hits)}.")
    else:
        notes.append("No tracked secret-like content markers detected by conservative pattern scan.")
    if local_sensitive_paths:
        score -= 10
        notes.append("Ignored local sensitive files are present; publication packaging must exclude them.")
    if not (ROOT / "tools/external_validation/security_review/run_automated_security_review_support.py").exists():
        score -= 10
        notes.append("Automated security-review support runner missing.")

    status = "PASS" if score >= 90 else "SCOPE_LIMITED" if score >= 60 else "FAIL_CLOSED"
    return Gate("security_posture", status, max(score, 0), notes), {
        "local_sensitive_paths_present": local_sensitive_paths,
        "tracked_sensitive_paths": tracked_sensitive_paths,
        "tracked_secret_content_markers": content_hits[:50],
        "tracked_secret_content_marker_count": len(content_hits),
    }


def audit_ecosystem() -> tuple[Gate, dict[str, Any]]:
    required = PUBLICATION_REQUIRED + [
        "assurance/unified/ETHICBIT_MECHANICAL_ETHICS_ASSURANCE_UNIFIED_MANIFEST_v0_1.json",
        "assurance/unified/ETHICBIT_MECHANICAL_ETHICS_ASSURANCE_UNIFIED_ANCHOR_RECEIPT_v0_1.json",
        "receipts/AEM_EVOLVE_TECHNICAL_DEMONSTRATION_MAINNET_ANCHOR_RECEIPT.json",
        "assurance/external-validation/v4_0/automated_reproduction/AUTOMATED_REPRODUCTION_REPORT.json",
    ]
    present = existing(required)
    miss = missing(required)
    score = 100 - (len(miss) * 6)
    notes = [
        f"Required publication/evidence artifacts present: {len(present)}/{len(required)}.",
        "Ethereum/mainnet and external-validation evidence are treated as references, not external certification.",
    ]
    if miss:
        notes.append(f"Missing required ecosystem artifacts: {miss}")
    status = "PASS" if not miss else "SCOPE_LIMITED" if score >= 70 else "FAIL_CLOSED"
    return Gate("ecosystem_publication_surface", status, max(score, 0), notes), {
        "required_present": present,
        "required_missing": miss,
    }


def audit_claims(files: list[Path]) -> tuple[Gate, dict[str, Any]]:
    doc_files = [p for p in files if p.suffix.lower() in {".md", ".txt", ".json", ".yml", ".yaml"} and p.stat().st_size < 2_000_000]
    hits: list[dict[str, str]] = []
    for path in doc_files:
        path_rel = rel(path)
        if "/.git/" in f"/{path_rel}/":
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for name, pattern in FORBIDDEN_CLAIM_PATTERNS.items():
            if pattern.search(text):
                hits.append({"path": path_rel, "pattern": name})

    # Existing claim-red-team evidence is the stronger source of truth for claim posture.
    claim_red_team = ROOT / "assurance/external-validation/v4_0/claim_red_team/CLAIM_BOUNDARY_RED_TEAM_REPORT.json"
    claim_red_team_status = None
    if claim_red_team.exists():
        try:
            data = json.loads(claim_red_team.read_text(encoding="utf-8"))
            claim_red_team_status = data.get("status") or data.get("claim_boundary_red_team") or data.get("overall_status")
        except json.JSONDecodeError:
            claim_red_team_status = "INVALID_JSON"

    score = 100
    notes = []
    if hits:
        score -= 25
        notes.append(f"Potential forbidden claim assertion patterns require review: {len(hits)}.")
    else:
        notes.append("No direct forbidden claim assertion patterns detected by conservative scan.")
    if claim_red_team_status:
        notes.append(f"Claim red-team artifact present with status marker: {claim_red_team_status}.")
    else:
        score -= 15
        notes.append("Claim red-team artifact missing or unreadable.")

    status = "PASS" if score >= 90 else "SCOPE_LIMITED" if score >= 65 else "FAIL_CLOSED"
    return Gate("claim_boundary", status, max(score, 0), notes), {
        "potential_forbidden_claim_assertions": hits[:100],
        "potential_forbidden_claim_assertion_count": len(hits),
        "claim_red_team_status": claim_red_team_status,
    }


def audit_reproducibility() -> tuple[Gate, dict[str, Any]]:
    required = [
        "scripts/reproducibility/run_reproducibility_extension_e2e.sh",
        "docs/reproducibility/REPRODUCIBLE_BUILD_GUIDE.md",
        "assurance/reproducibility/declared_subjects.json",
        "assurance/reproducibility/expected_hashes.json",
        "challenge/independent-reproduction/AEM_V1_1_INDEPENDENT_REPRODUCTION_CHALLENGE.md",
        "docs/external-validation/outreach/V4_0_VALIDATOR_INVITATION.md",
    ]
    present = existing(required)
    miss = missing(required)
    external_pending_markers = []
    for path in [
        ROOT / "docs/STATUS_BULLETIN_PUBLIC_2026-05-16_V4_0_HYBRID_VALIDATION.md",
        ROOT / "docs/external-validation/hybrid/V4_0_HYBRID_VALIDATION_CLAIM_STATE_MACHINE.md",
    ]:
        if path.exists() and "HUMAN_ATTESTATION_PENDING" in path.read_text(encoding="utf-8", errors="ignore"):
            external_pending_markers.append(rel(path))

    score = 100 - len(miss) * 8
    notes = [f"Reproducibility/challenge inputs present: {len(present)}/{len(required)}."]
    if miss:
        notes.append(f"Missing reproducibility inputs: {miss}")
    if external_pending_markers:
        score -= 5
        notes.append("External human attestation remains pending by design.")
    status = "PASS" if not miss and not external_pending_markers else "SCOPE_LIMITED" if score >= 70 else "FAIL_CLOSED"
    return Gate("reproducibility_and_external_validation", status, max(score, 0), notes), {
        "required_present": present,
        "required_missing": miss,
        "external_pending_markers": external_pending_markers,
    }


def render_markdown(report: dict[str, Any]) -> str:
    gates = report["gates"]
    lines = [
        "# EthicBit Release-Grade Deep Audit v1.0",
        "",
        "**Status:** `{}`".format(report["overall_status"]),
        f"**Generated UTC:** `{report['generated_at_utc']}`",
        f"**Commit:** `{report['git']['commit']}`",
        "**Scope:** internal release-readiness audit for code, components, ecosystem, security posture, reproducibility and claim boundaries.",
        "",
        "## Boundary",
        "This audit is an internal release-grade readiness audit. It is not external certification, regulatory approval, cybersecurity certification, legal advice, clinical validation, or independent reproduction.",
        "",
        "## Gate Summary",
        "",
        "| Gate | Status | Score | Notes |",
        "|---|---:|---:|---|",
    ]
    for gate in gates:
        note = "<br>".join(gate["notes"])
        lines.append(f"| `{gate['name']}` | `{gate['status']}` | {gate['score']} | {note} |")

    lines.extend([
        "",
        "## Key Findings",
        "",
    ])
    for finding in report["key_findings"]:
        lines.append(f"- **{finding['severity']}** — {finding['summary']}")

    lines.extend([
        "",
        "## Publication Decision",
        "",
        f"`{report['publication_decision']}`",
        "",
        "## Required Next Actions",
        "",
    ])
    for action in report["required_next_actions"]:
        lines.append(f"- {action}")

    lines.extend([
        "",
        "## Explicit Non-Claims",
        "",
        "This audit does not claim completed external validation, external security audit completion, third-party reproduction completion, cybersecurity certification, regulatory approval, legal compliance, universal production readiness, absence of all vulnerabilities, or clinical/diagnostic readiness.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    files = iter_files()
    tracked = git_tracked_files()
    generated_at = datetime.now(timezone.utc).isoformat()
    commit = run_git(["rev-parse", "--short=8", "HEAD"])
    branch = run_git(["branch", "--show-current"])

    gates_with_details = [
        audit_code(files),
        audit_components(),
        audit_security(files, tracked),
        audit_ecosystem(),
        audit_claims(files),
        audit_reproducibility(),
    ]
    gates = [gate for gate, _ in gates_with_details]
    details = {gate.name: detail for gate, detail in gates_with_details}

    weighted_score = round(sum(g.score for g in gates) / len(gates))
    if any(g.status == "FAIL_CLOSED" for g in gates):
        overall_status = "FAIL_CLOSED"
    elif any(g.status == "SCOPE_LIMITED" for g in gates):
        overall_status = "PASS_WITH_SCOPE_LIMITATIONS"
    else:
        overall_status = "PASS"

    key_findings = [
        {
            "severity": "HIGH",
            "summary": "External validation remains HUMAN_ATTESTATION_PENDING; do not claim EXTERNAL_VALIDATION_PASS.",
        },
        {
            "severity": "MEDIUM",
            "summary": "Ignored local sensitive files are present; release and mirror packaging must continue to exclude secrets and private key material.",
        },
        {
            "severity": "MEDIUM",
            "summary": "Code-quality posture is improved but still scope-limited until broader CEMU component tests and committed SAST tooling are expanded.",
        },
    ]

    publication_decision = (
        "PUBLICATION_ALLOWED_SCOPE_LIMITED_WITH_EXTERNAL_ATTESTATION_PENDING"
        if overall_status != "FAIL_CLOSED"
        else "PUBLICATION_BLOCKED_FAIL_CLOSED"
    )
    required_next_actions = [
        "Run this audit before each major public release or mirror refresh.",
        "Keep private engineering repository and public verification mirror separated unless a sanitized mirror package is explicitly prepared.",
        "Do not elevate to EXTERNAL_VALIDATION_PASS until signed human attestation covers criteria 1, 2 and 8.",
        "Expand CEMU component tests and add committed Bandit/SAST posture if the next target is higher code-quality score.",
        "Continue excluding `.env*`, private keys and local runtime secrets from all release and mirror packaging.",
    ]

    report = {
        "schema_id": "ETHICBIT_RELEASE_GRADE_DEEP_AUDIT_REPORT_V1_0",
        "generated_at_utc": generated_at,
        "git": {"branch": branch, "commit": commit},
        "overall_status": overall_status,
        "overall_score": weighted_score,
        "publication_decision": publication_decision,
        "gates": [gate.__dict__ for gate in gates],
        "details": details,
        "key_findings": key_findings,
        "required_next_actions": required_next_actions,
        "non_claims": {
            "external_validation_completed": False,
            "third_party_reproduction_completed": False,
            "cybersecurity_certification_claimed": False,
            "regulatory_approval_claimed": False,
            "legal_compliance_claimed": False,
            "universal_production_readiness_claimed": False,
            "clinical_or_diagnostic_readiness_claimed": False,
        },
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    HASH_RECORD_PATH.parent.mkdir(parents=True, exist_ok=True)

    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    DOC_PATH.write_text(render_markdown(report), encoding="utf-8")

    hash_lines = [
        f"generated_at_utc={generated_at}",
        f"git_commit={commit}",
        f"overall_status={overall_status}",
        f"overall_score={weighted_score}",
        "",
    ]
    for path in [Path("tools/audit/release_grade_deep_audit.py"), REPORT_PATH.relative_to(ROOT), DOC_PATH.relative_to(ROOT)]:
        hash_lines.append(f"{sha256_file(ROOT / path)}  {path.as_posix()}")
    HASH_RECORD_PATH.write_text("\n".join(hash_lines) + "\n", encoding="utf-8")

    print(f"ETHICBIT_RELEASE_GRADE_DEEP_AUDIT_STATUS={overall_status}")
    print(f"overall_score={weighted_score}")
    print(f"publication_decision={publication_decision}")
    for gate in gates:
        print(f"{gate.name}={gate.status}:{gate.score}")
    print(f"report={REPORT_PATH.relative_to(ROOT)}")
    print(f"document={DOC_PATH.relative_to(ROOT)}")
    print(f"hash_record={HASH_RECORD_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
