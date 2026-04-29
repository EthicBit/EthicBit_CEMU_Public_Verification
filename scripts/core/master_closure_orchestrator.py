#!/usr/bin/env python3
"""
EthicBit / CEMU - Master Closure Orchestrator (canonical, schema-aligned)

Single artifact that orchestrates verification of the L5 constitutional
evidence ceiling. Produces results/master_closure_report.json with full
stage results, git provenance, summary fields for mixed audiences
(technical, regulatory, legal, institutional), and explicit scope flags.

Modes:
  public-verify (default): read-only verification of published artifacts.
    No private key, no signing, no anchoring, no artifact mutation.
    Reproducible by any external auditor in approximately 30 seconds.

  operator-full: re-anchors via reanchor_blob_sepolia.py (requires
    ETHICBIT_PRIVATE_KEY in env or .env), runs all verification stages.

Output schema: ETHICBIT_MASTER_CLOSURE_REPORT_V1
Version: 2.0
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
REPORT_FILE = RESULTS / "master_closure_report.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json_atomic(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def safe_read_json(path: Path) -> dict:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def safe_cmd(cmd: list, timeout: int = 15) -> str:
    try:
        return subprocess.check_output(cmd, cwd=ROOT, text=True, timeout=timeout, stderr=subprocess.STDOUT).strip()
    except Exception:
        return "UNKNOWN"


def load_dotenv_if_present() -> bool:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return False
    loaded = False
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)
        loaded = True
    return loaded


def git_info() -> dict:
    branch = safe_cmd(["git", "branch", "--show-current"]) or "UNKNOWN"
    return {
        "branch": branch,
        "head_sha": safe_cmd(["git", "rev-parse", "HEAD"]),
        "main_head": safe_cmd(["git", "rev-parse", "origin/main"]),
        "status_short": safe_cmd(["git", "status", "--short"]),
    }


def run_stage(stage: str, cmd: list, description: str, timeout: int = 300) -> dict:
    print()
    print("=" * 80)
    print("[STAGE " + stage + "] " + description)
    print("=" * 80)
    print("command: " + " ".join(cmd))
    started = time.time()
    try:
        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        duration = round(time.time() - started, 3)
        status = "PASS" if result.returncode == 0 else "FAIL_CLOSED"
        if result.stdout:
            print(result.stdout[-3000:])
        if result.stderr:
            print(result.stderr[-1500:], file=sys.stderr)
        marker = "PASS" if status == "PASS" else "FAIL"
        print("[" + marker + "] " + description + " (" + str(duration) + "s)")
        return {
            "stage": stage,
            "description": description,
            "command": cmd,
            "status": status,
            "return_code": result.returncode,
            "duration_seconds": duration,
            "stdout_tail": result.stdout[-3000:],
            "stderr_tail": result.stderr[-1500:],
        }
    except subprocess.TimeoutExpired:
        return {
            "stage": stage, "description": description, "command": cmd,
            "status": "FAIL_CLOSED", "return_code": None,
            "duration_seconds": round(time.time() - started, 3),
            "error": "TIMEOUT",
        }
    except Exception as exc:
        return {
            "stage": stage, "description": description, "command": cmd,
            "status": "FAIL_CLOSED", "return_code": None,
            "duration_seconds": round(time.time() - started, 3),
            "error": str(exc),
        }


def preflight(mode: str) -> None:
    print()
    print("PREFLIGHT CHECK")
    print("-" * 80)
    common_required = [
        "results/constitutional_evidence_ceiling.json",
        "results/constitutional_evidence_ceiling.sig",
        "results/kzg_blob_anchor_report.json",
        "results/runtime_evidence_strength_report.json",
        "scripts/core/verify_l5_full_chain.py",
        "scripts/core/verify_l5_canonical_state.py",
        "scripts/core/verify_ceiling_signature.py",
        "scripts/core/verify_l5_onchain.py",
        "scripts/security/anti_re_guard.py",
        "scripts/audit/verify_constitutional_controls.sh",
        "config/anti_re_policy.v1.json",
        "config/constitutional_controls.v1.json",
        "docs/AUDIT.md",
    ]
    if mode == "operator-full":
        required = common_required + ["scripts/core/reanchor_blob_sepolia.py"]
        if load_dotenv_if_present():
            print("INFO: .env loaded into environment for operator-full")
        if not os.environ.get("ETHICBIT_PRIVATE_KEY"):
            print("FAIL: ETHICBIT_PRIVATE_KEY not found.")
            print("operator-full requires signing authority.")
            raise SystemExit(1)
    else:
        required = common_required
        print("INFO: PUBLIC_VERIFY mode - read-only, no secrets required")
        if os.environ.get("ETHICBIT_PRIVATE_KEY"):
            print("INFO: ETHICBIT_PRIVATE_KEY detected but public-verify will not use it")

    missing = [item for item in required if not (ROOT / item).exists()]
    if missing:
        print("FAIL: required files missing:")
        for item in missing:
            print("   - " + item)
        raise SystemExit(1)
    print("Mode selected: " + mode)
    print("Preflight: PASS")


def stages_for_mode(mode: str, with_tampering_test: bool = False) -> list:
    if mode == "operator-full":
        stages = [
            ("01", ["python3", "scripts/core/reanchor_blob_sepolia.py"],
             "EIP-4844 re-anchor + canonical re-signing on Sepolia", 600),
            ("02", ["python3", "scripts/core/verify_l5_full_chain.py"],
             "L5 full chain verification (canonical + custody + on-chain)", 180),
            ("03", ["bash", "scripts/audit/verify_constitutional_controls.sh"],
             "Full constitutional gate (13 controls)", 300),
            ("04", ["python3", "scripts/security/anti_re_guard.py", "--root", ".", "--enforce"],
             "Anti-RE hardening guard", 120),
        ]
    else:
        stages = [
            ("01", ["python3", "scripts/core/verify_l5_full_chain.py"],
             "L5 full chain verification (canonical + custody + on-chain)", 180),
            ("02", ["bash", "scripts/audit/verify_constitutional_controls.sh"],
             "Constitutional gate (13 controls)", 300),
            ("03", ["python3", "scripts/security/anti_re_guard.py", "--root", ".", "--enforce"],
             "Anti-RE hardening guard", 120),
        ]
    if with_tampering_test:
        stages.append((
            str(len(stages) + 1).zfill(2),
            ["python3", "scripts/core/test_tampering_resistance.py"],
            "Tampering resistance proof (3 attack classes)", 300,
        ))
    return stages


def build_summary(final_status: str) -> dict:
    ceiling = safe_read_json(RESULTS / "constitutional_evidence_ceiling.json")
    sig = safe_read_json(RESULTS / "constitutional_evidence_ceiling.sig")
    anchor = safe_read_json(RESULTS / "kzg_blob_anchor_report.json")
    controls = safe_read_json(RESULTS / "constitutional_controls_report.json")
    anti_re = safe_read_json(RESULTS / "anti_re_guard_report.json")

    constitutional_status = controls.get("constitutional_status") or controls.get("CONSTITUTIONAL_STATUS")
    if constitutional_status is None:
        s = controls.get("summary", {})
        if isinstance(s, dict):
            total = s.get("total")
            passed = s.get("pass")
            failed = s.get("fail")
            must_fail = s.get("must_fail") or s.get("mustFail")
            if total is not None and passed == total and failed == 0 and (must_fail in (0, None)):
                constitutional_status = "PASS"
    if constitutional_status is None:
        constitutional_status = "PASS" if final_status == "PASS" else "UNVERIFIED"

    claim_level_ceiling = ceiling.get("claim_level_ceiling") or ceiling.get("current_ceiling") or "UNVERIFIED"
    presentation_scope = "READY_WITH_SCOPE_DELIMITATION" if final_status == "PASS" else "UNVERIFIED"
    material_closure = "READY" if final_status == "PASS" else "FAIL_CLOSED"

    return {
        "constitutional_status": constitutional_status,
        "claim_level_ceiling": claim_level_ceiling,
        "ceiling_status": ceiling.get("status", "UNVERIFIED"),
        "anti_re_status": anti_re.get("status", "UNVERIFIED"),
        "anchor_status": anchor.get("status", "UNVERIFIED"),
        "anchor_tx_hash": anchor.get("tx_hash"),
        "anchor_block_number": anchor.get("block_number"),
        "signer_address": sig.get("signer_address"),
        "signature_scheme": sig.get("scheme"),
        "material_closure": material_closure,
        "primary_material_artifact": "MECHANICAL_ETHICAL_AGENT_EXECUTABLE",
        "third_party_binding": False,
        "third_party_presentability": presentation_scope,
        "evidence_falsifiable_in_seconds": 30,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="EthicBit/CEMU L5 Master Closure Orchestrator")
    parser.add_argument(
        "--mode",
        choices=["operator-full", "public-verify"],
        default=os.environ.get("ETHICBIT_MASTER_CLOSURE_MODE", "public-verify"),
    )
    parser.add_argument(
        "--with-tampering-test",
        action="store_true",
        help="Also run test_tampering_resistance.py",
    )
    args = parser.parse_args()

    started = time.time()
    print("=" * 80)
    print("ETHICBIT / CEMU")
    print("MASTER CLOSURE ORCHESTRATOR - L5 CANONICAL CLOSURE")
    print("Mode: " + args.mode)
    print("Date: " + now_iso())
    print("=" * 80)

    stages = []
    final_status = "PASS"
    try:
        preflight(args.mode)
        for stage_id, cmd, description, timeout in stages_for_mode(args.mode, args.with_tampering_test):
            result = run_stage(stage_id, cmd, description, timeout)
            stages.append(result)
            if result["status"] != "PASS":
                final_status = "FAIL_CLOSED"
                break
    except SystemExit as exc:
        final_status = "FAIL_CLOSED"
        stages.append({
            "stage": "PREFLIGHT", "description": "Preflight validation",
            "status": "FAIL_CLOSED", "return_code": exc.code,
        })

    duration = round(time.time() - started, 3)
    summary = build_summary(final_status)

    report = {
        "schema_id": "ETHICBIT_MASTER_CLOSURE_REPORT_V1",
        "system": "EthicBit/CEMU",
        "version": "2.0",
        "status": final_status,
        "mode": args.mode,
        "with_tampering_test": args.with_tampering_test,
        "generated_at": now_iso(),
        "duration_seconds": duration,
        "git": git_info(),
        "summary": summary,
        "stages": stages,
        "verifier_scripts": [
            "scripts/core/verify_l5_full_chain.py",
            "scripts/core/verify_l5_canonical_state.py",
            "scripts/core/verify_ceiling_signature.py",
            "scripts/core/verify_l5_onchain.py",
            "scripts/core/test_tampering_resistance.py",
            "scripts/security/anti_re_guard.py",
            "scripts/audit/verify_constitutional_controls.sh",
        ],
        "evidence_artifacts": [
            "results/constitutional_evidence_ceiling.json",
            "results/constitutional_evidence_ceiling.sig",
            "results/kzg_blob_anchor_report.json",
            "results/runtime_evidence_strength_report.json",
            "results/anti_re_guard_report.json",
            "results/constitutional_controls_report.json",
        ],
        "audit_documents": ["docs/AUDIT.md"],
        "public_scope": {
            "secrets_required_for_public_verify": False,
            "signing_performed_in_public_verify": False,
            "anchoring_performed_in_public_verify": False,
            "artifact_mutation_in_public_verify": False,
            "third_party_binding": False,
            "external_rpcs_consulted": True,
        },
        "operator_scope": {
            "signing_performed": args.mode == "operator-full",
            "anchoring_performed": args.mode == "operator-full",
            "requires_signing_authority": args.mode == "operator-full",
            "private_key_used": args.mode == "operator-full",
        },
    }

    write_json_atomic(REPORT_FILE, report)

    print()
    print("=" * 80)
    print("MASTER_CLOSURE_STATUS=" + final_status)
    print("Mode=" + args.mode)
    print("Duration=" + str(duration) + "s")
    print("Report=" + str(REPORT_FILE))
    print("constitutional_status=" + str(summary.get("constitutional_status")))
    print("claim_level_ceiling=" + str(summary.get("claim_level_ceiling")))
    print("third_party_binding=" + str(summary.get("third_party_binding")))
    print("presentation_scope=" + str(summary.get("third_party_presentability")))
    print("=" * 80)
    return 0 if final_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
