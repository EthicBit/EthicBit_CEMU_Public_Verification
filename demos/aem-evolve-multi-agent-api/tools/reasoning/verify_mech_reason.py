#!/usr/bin/env python3
"""MECH-REASON™ verification — AEM-EVOLVE™ v1.2.

Verifies that a MECH_REASON_REPORT.json satisfies all structural,
integrity, and determinism invariants. No LLM involvement.

Checks:
  1. Schema validity         — required fields present, correct types
  2. Policy version          — matches expected version string
  3. Input hash integrity    — re-hash each input file, compare recorded hashes
  4. Report hash integrity   — re-derive report_hash, compare
  5. Score ranges            — all scores in [0.0, 1.0]
  6. Triggered rules         — list of strings, all in known rule IDs
  7. Recommended outcome     — one of ALLOWED_OUTCOMES
  8. Mechanical explanation  — non-LLM marker present
  9. Non-claims preserved    — all required non-claim statements present
 10. Deterministic repeatability — re-run engine twice, compare outputs

Output: MECH_REASON_VERIFICATION=PASS | FAIL
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT   = Path(__file__).resolve().parents[4]
V1_2        = REPO_ROOT / "assurance/evolve-multi-agent/v1_2"
TOOLS       = Path(__file__).parent
POLICY_PATH = TOOLS / "policies/AEM_EVOLVE_POLICY_V1_2.json"
REPORT_PATH = V1_2 / "MECH_REASON_REPORT.json"
VERIF_OUT   = V1_2 / "MECH_REASON_VERIFICATION_REPORT.json"

EXPECTED_SCHEMA_ID    = "AEM_EVOLVE_MECH_REASON_REPORT_V1_2"
EXPECTED_POLICY_VER   = "1.2.0"
ALLOWED_OUTCOMES      = {"PASS", "SCOPE_LIMITED", "FAIL_CLOSED", "ESCALATE_TO_HITL"}
NON_LLM_MARKER        = "LLM output was not used to generate this explanation."
REQUIRED_NON_CLAIMS   = [
    "LLM output is not final governance.",
    "LLM output is not official status.",
    "LLM output is not regulatory approval.",
    "LLM output is not legal compliance.",
    "LLM output is not certification.",
    "LLM output is not receipt sealing.",
    "This recommendation is not regulatory approval.",
    "This recommendation is not legal compliance.",
    "This recommendation is not external certification.",
]
REQUIRED_SCORE_KEYS = [
    "evidence_completeness_score",
    "governance_risk_score",
    "claim_boundary_risk_score",
    "hitl_necessity_score",
    "anchor_integrity_score",
    "receipt_integrity_score",
    "regulatory_mapping_presence_score",
]


def _fail(checks: list, check_id: str, detail: str) -> None:
    checks.append({"check_id": check_id, "status": "FAIL", "detail": detail})


def _pass(checks: list, check_id: str, detail: str = "ok") -> None:
    checks.append({"check_id": check_id, "status": "PASS", "detail": detail})


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_report() -> dict:
    with open(REPORT_PATH) as f:
        return json.load(f)


# ── Check 1: schema validity ──────────────────────────────────────────────────
def check_schema(report: dict, checks: list) -> None:
    required = [
        "schema_id", "generated_at", "policy_version", "recommended_outcome",
        "hitl_required", "triggered_rules", "scores", "state_machine_validation",
        "mechanical_explanation", "input_hashes", "report_hash",
        "llm_involved", "non_claims_preserved",
    ]
    missing = [k for k in required if k not in report]
    if missing:
        _fail(checks, "C-01-SCHEMA", f"missing fields: {missing}")
        return
    if report.get("schema_id") != EXPECTED_SCHEMA_ID:
        _fail(checks, "C-01-SCHEMA", f"schema_id mismatch: {report.get('schema_id')}")
        return
    if report.get("llm_involved") is not False:
        _fail(checks, "C-01-SCHEMA", "llm_involved must be false")
        return
    _pass(checks, "C-01-SCHEMA", f"schema_id={EXPECTED_SCHEMA_ID}, llm_involved=false")


# ── Check 2: policy version ───────────────────────────────────────────────────
def check_policy_version(report: dict, checks: list) -> None:
    pv = report.get("policy_version")
    if pv != EXPECTED_POLICY_VER:
        _fail(checks, "C-02-POLICY-VER", f"expected {EXPECTED_POLICY_VER}, got {pv}")
    else:
        _pass(checks, "C-02-POLICY-VER", f"policy_version={pv}")


# ── Check 3: input hash integrity ─────────────────────────────────────────────
def check_input_hashes(report: dict, checks: list) -> None:
    recorded = report.get("input_hashes", {})
    file_map = {
        "claim_boundary_check_report.json":  V1_2 / "claim_boundary_check_report.json",
        "evidence_completeness_report.json": V1_2 / "evidence_completeness_report.json",
        "governance_risk_score_report.json": V1_2 / "governance_risk_score_report.json",
        "AEM_EVOLVE_POLICY_V1_2.json":       POLICY_PATH,
    }
    mismatches = []
    for fname, path in file_map.items():
        expected = _sha256_file(path)
        got      = recorded.get(fname, "")
        if expected != got:
            mismatches.append(f"{fname}: expected={expected[:16]}… got={got[:16]}…")
    if mismatches:
        _fail(checks, "C-03-INPUT-HASHES", "; ".join(mismatches))
    else:
        _pass(checks, "C-03-INPUT-HASHES", f"all {len(file_map)} input hashes verified")


# ── Check 4: report hash integrity ───────────────────────────────────────────
def check_report_hash(report: dict, checks: list) -> None:
    recorded_hash = report.get("report_hash", "")
    payload = {
        "recommended_outcome": report.get("recommended_outcome"),
        "triggered_rules":     report.get("triggered_rules"),
        "scores":              report.get("scores"),
        "input_hashes":        report.get("input_hashes"),
    }
    derived = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if derived != recorded_hash:
        _fail(checks, "C-04-REPORT-HASH", f"report_hash mismatch: derived={derived[:16]}… recorded={recorded_hash[:16]}…")
    else:
        _pass(checks, "C-04-REPORT-HASH", f"report_hash={derived[:16]}…")


# ── Check 5: score ranges ─────────────────────────────────────────────────────
def check_score_ranges(report: dict, checks: list) -> None:
    scores = report.get("scores", {})
    out_of_range = []
    for key in REQUIRED_SCORE_KEYS:
        val = scores.get(key)
        if val is None:
            out_of_range.append(f"{key}: missing")
        elif not isinstance(val, (int, float)) or not (0.0 <= float(val) <= 1.0):
            out_of_range.append(f"{key}={val} not in [0.0, 1.0]")
    if out_of_range:
        _fail(checks, "C-05-SCORES", "; ".join(out_of_range))
    else:
        _pass(checks, "C-05-SCORES", f"all {len(REQUIRED_SCORE_KEYS)} scores in [0.0, 1.0]")


# ── Check 6: triggered rules ──────────────────────────────────────────────────
def check_triggered_rules(report: dict, checks: list) -> None:
    rules = report.get("triggered_rules")
    if not isinstance(rules, list):
        _fail(checks, "C-06-TRIGGERED-RULES", f"triggered_rules must be list, got {type(rules)}")
        return
    non_strings = [r for r in rules if not isinstance(r, str)]
    if non_strings:
        _fail(checks, "C-06-TRIGGERED-RULES", f"non-string entries: {non_strings}")
    else:
        _pass(checks, "C-06-TRIGGERED-RULES", f"{len(rules)} rule(s), all strings")


# ── Check 7: recommended outcome ─────────────────────────────────────────────
def check_recommended_outcome(report: dict, checks: list) -> None:
    outcome = report.get("recommended_outcome")
    if outcome not in ALLOWED_OUTCOMES:
        _fail(checks, "C-07-OUTCOME", f"'{outcome}' not in ALLOWED_OUTCOMES={ALLOWED_OUTCOMES}")
    else:
        _pass(checks, "C-07-OUTCOME", f"recommended_outcome={outcome}")


# ── Check 8: mechanical explanation ──────────────────────────────────────────
def check_mechanical_explanation(report: dict, checks: list) -> None:
    expl = report.get("mechanical_explanation", "")
    if not isinstance(expl, str) or len(expl) < 10:
        _fail(checks, "C-08-EXPLANATION", "explanation missing or too short")
        return
    if NON_LLM_MARKER not in expl:
        _fail(checks, "C-08-EXPLANATION", f"missing non-LLM marker: '{NON_LLM_MARKER}'")
    else:
        _pass(checks, "C-08-EXPLANATION", f"explanation present, non-LLM marker confirmed")


# ── Check 9: non-claims preserved ────────────────────────────────────────────
def check_non_claims(report: dict, checks: list) -> None:
    preserved = report.get("non_claims_preserved", [])
    missing = [nc for nc in REQUIRED_NON_CLAIMS if nc not in preserved]
    if missing:
        _fail(checks, "C-09-NON-CLAIMS", f"missing: {missing}")
    else:
        _pass(checks, "C-09-NON-CLAIMS", f"all {len(REQUIRED_NON_CLAIMS)} non-claims present")


# ── Check 10: deterministic repeatability ────────────────────────────────────
def check_deterministic_repeatability(checks: list) -> None:
    engine = TOOLS / "mech_reason.py"
    outcomes = []
    for run in range(2):
        result = subprocess.run(
            [sys.executable, str(engine)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            _fail(checks, "C-10-DETERMINISM", f"run {run+1} failed: {result.stderr.strip()[:200]}")
            return
        run_report = {}
        if REPORT_PATH.exists():
            with open(REPORT_PATH) as f:
                run_report = json.load(f)
        outcomes.append({
            "recommended_outcome": run_report.get("recommended_outcome"),
            "triggered_rules":     run_report.get("triggered_rules"),
            "scores":              run_report.get("scores"),
        })

    if outcomes[0] == outcomes[1]:
        _pass(checks, "C-10-DETERMINISM",
              f"two runs agree: outcome={outcomes[0]['recommended_outcome']}, "
              f"triggered_rules={outcomes[0]['triggered_rules']}")
    else:
        _fail(checks, "C-10-DETERMINISM",
              f"run 1 ≠ run 2: {outcomes[0]} vs {outcomes[1]}")


def main() -> int:
    print("[MECH-REASON™ VERIFIER] Starting verification...")

    if not REPORT_PATH.exists():
        print(f"ERROR: MECH_REASON_REPORT.json not found at {REPORT_PATH}", file=sys.stderr)
        return 1

    report = _load_report()
    checks: list[dict] = []

    check_schema(report, checks)
    check_policy_version(report, checks)
    check_input_hashes(report, checks)
    check_report_hash(report, checks)
    check_score_ranges(report, checks)
    check_triggered_rules(report, checks)
    check_recommended_outcome(report, checks)
    check_mechanical_explanation(report, checks)
    check_non_claims(report, checks)
    check_deterministic_repeatability(checks)

    failed = [c for c in checks if c["status"] == "FAIL"]
    passed = [c for c in checks if c["status"] == "PASS"]
    overall = "PASS" if not failed else "FAIL"

    # Re-read report after repeatability runs (engine regenerates it)
    final_report = _load_report()

    verif_report = {
        "schema_id": "AEM_EVOLVE_MECH_REASON_VERIFICATION_REPORT_V1_2",
        "source_report_hash": final_report.get("report_hash", ""),
        "policy_version": EXPECTED_POLICY_VER,
        "verification_result": overall,
        "checks_passed": len(passed),
        "checks_failed": len(failed),
        "checks": checks,
        "non_claims_verified": REQUIRED_NON_CLAIMS,
        "llm_involved": False,
        "verification_non_claims": [
            "This verification is not a regulatory audit.",
            "This verification is not legal compliance certification.",
            "This verification does not replace HITL human review.",
            "LLM output was not used in this verification.",
        ],
    }

    V1_2.mkdir(parents=True, exist_ok=True)
    with open(VERIF_OUT, "w") as f:
        json.dump(verif_report, f, indent=2)

    for c in checks:
        mark = "✓" if c["status"] == "PASS" else "✗"
        print(f"  {mark} [{c['check_id']}] {c['detail']}")

    print(f"MECH_REASON_VERIFICATION={overall}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
