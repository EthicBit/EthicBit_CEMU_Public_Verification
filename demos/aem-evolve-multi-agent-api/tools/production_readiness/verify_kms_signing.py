#!/usr/bin/env python3
"""
v2.0 PR 2 — HSM/KMS-Backed Production Signing Verifier

Gate output: HSM_KMS_SIGNING_CHECK=PASS | FAIL

IMPORTANT: This gate FAILS when AEM_KMS_PROVIDER is not configured.
That is the correct and expected outcome for a local/demo environment.
Set AEM_KMS_PROVIDER (aws_kms | gcp_kms | azure_key_vault | pkcs11),
AEM_KMS_KEY_ID, and provider-specific env vars to satisfy this gate.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEMO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_ROOT = DEMO_ROOT / "tools"
ASSURANCE_OUT = DEMO_ROOT.parents[1] / "assurance" / "evolve-multi-agent" / "v2_0"

if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

_CHECKS: list[dict[str, Any]] = []
_PASS = 0
_FAIL = 0


def _check(check_id: str, label: str, passed: bool, detail: str = "") -> None:
    global _PASS, _FAIL
    status = "PASS" if passed else "FAIL"
    if passed:
        _PASS += 1
    else:
        _FAIL += 1
    entry: dict[str, Any] = {"id": check_id, "label": label, "status": status}
    if detail:
        entry["detail"] = detail
    _CHECKS.append(entry)
    marker = "✓" if passed else "✗"
    print(f"  [{marker}] {check_id}: {label} — {status}" + (f" ({detail})" if detail else ""))


def run() -> str:
    print("=" * 70)
    print("v2.0 PR 2 — HSM/KMS-Backed Production Signing Verifier")
    print("=" * 70)

    kms_provider = os.getenv("AEM_KMS_PROVIDER", "").strip()
    kms_key_id = os.getenv("AEM_KMS_KEY_ID", "").strip()
    kms_region = os.getenv("AEM_KMS_REGION", "").strip()
    kms_project = os.getenv("AEM_KMS_PROJECT", "").strip()
    kms_algorithm = os.getenv("AEM_KMS_ALGORITHM", "ECDSA_SHA_256").strip()

    print(f"\nEnvironment:")
    print(f"  AEM_KMS_PROVIDER  = {kms_provider or '(not set)'}")
    print(f"  AEM_KMS_KEY_ID    = {kms_key_id or '(not set)'}")
    print(f"  AEM_KMS_REGION    = {kms_region or '(not set)'}")
    print(f"  AEM_KMS_ALGORITHM = {kms_algorithm}")
    print()

    # C-01: AEM_KMS_PROVIDER env var set
    _check("C-01", "AEM_KMS_PROVIDER env var configured", bool(kms_provider),
           kms_provider or "AEM_KMS_PROVIDER not set")

    # C-02: production_kms_provider module importable
    try:
        from signing.production_kms_provider import (
            ProductionKmsProvider, load_kms_config, ProductionKmsConfig,
            _SUPPORTED_PROVIDERS,
        )
        _check("C-02", "signing.production_kms_provider importable", True)
    except ImportError as exc:
        _check("C-02", "signing.production_kms_provider importable", False, str(exc))
        _emit_report("FAIL", kms_provider, None, None)
        return "HSM_KMS_SIGNING_CHECK=FAIL"

    # C-03: supported provider list complete
    supported = set(_SUPPORTED_PROVIDERS)
    expected = {"aws_kms", "gcp_kms", "azure_key_vault", "pkcs11"}
    _check("C-03", "all four provider types supported",
           expected.issubset(supported),
           f"supported={sorted(supported)}")

    # C-04: load_kms_config returns None when AEM_KMS_PROVIDER unset
    if not kms_provider:
        cfg = load_kms_config()
        _check("C-04", "load_kms_config returns None (AEM_KMS_PROVIDER unset)",
               cfg is None,
               "Correct: gate not satisfied without KMS/HSM provider")
    else:
        cfg = load_kms_config()
        _check("C-04", "load_kms_config returns config (AEM_KMS_PROVIDER set)",
               cfg is not None,
               f"provider={cfg.provider if cfg else 'None'}")

    # C-05: from_env() mirrors config
    provider_obj = ProductionKmsProvider.from_env() if kms_provider else None
    _check("C-05", "from_env() returns provider iff config present",
           (provider_obj is not None) == bool(kms_provider),
           f"provider={'present' if provider_obj else 'None'}")

    # C-06: When no provider — gate NOT_CONFIGURED (honest FAIL)
    if not kms_provider:
        _check("C-06", "gate NOT_CONFIGURED when AEM_KMS_PROVIDER unset",
               provider_obj is None,
               "Correct gate behavior — FAIL_CLOSED: KMS/HSM required")
        _check("C-07", "key accessible N/A (no provider)", True, "Skipped")
        _check("C-08", "sign/verify round-trip N/A", True, "Skipped")
        _check("C-09", "non-exportable key posture N/A", True, "Skipped")
        _check("C-10", "audit log active N/A", True, "Skipped")
        _emit_honest_fail(kms_provider)
        return "HSM_KMS_SIGNING_CHECK=FAIL"

    # --- Provider configured path ---

    # C-06: AEM_KMS_KEY_ID set
    _check("C-06", "AEM_KMS_KEY_ID configured", bool(kms_key_id),
           kms_key_id or "AEM_KMS_KEY_ID not set")

    # C-07: key accessible (public key reachable)
    gate_result = provider_obj.gate_check() if provider_obj else {}
    pub_reachable = gate_result.get("public_key_reachable", False)
    _check("C-07", "KMS key accessible (public key reachable)", pub_reachable,
           gate_result.get("reason", ""))

    # C-08: sign/verify round-trip
    roundtrip = gate_result.get("sign_verify_roundtrip", False)
    _check("C-08", "sign/verify round-trip via KMS", roundtrip,
           gate_result.get("reason", ""))

    # C-09: non-exportable key posture
    non_exp = gate_result.get("non_exportable_posture", False)
    _check("C-09", "non-exportable key posture configured",
           non_exp,
           "KMS/HSM keys are non-exportable by design" if non_exp else "not set")

    # C-10: audit log active
    audit_log = gate_result.get("audit_log_active", False)
    _check("C-10", "key-usage audit log active", audit_log,
           "signing operations logged in-process" if audit_log else "audit_log_active=False")

    gate_status = "PASS" if _FAIL == 0 else "FAIL"
    _emit_report(gate_status, kms_provider, load_kms_config(), provider_obj)
    result_line = f"HSM_KMS_SIGNING_CHECK={gate_status}"
    print()
    print(f"  Gate result: {result_line} ({_PASS}/{_PASS + _FAIL} checks passed)")
    return result_line


def _emit_honest_fail(kms_provider: str) -> None:
    _emit_report("FAIL", kms_provider, None, None)
    print()
    print("  Gate result: HSM_KMS_SIGNING_CHECK=FAIL")
    print()
    print("  NOTE: This is the correct and expected result for a local/demo")
    print("  environment. To satisfy this gate, set AEM_KMS_PROVIDER to one of:")
    print("    aws_kms | gcp_kms | azure_key_vault | pkcs11")
    print("  and set AEM_KMS_KEY_ID to the key ARN/resource name, then re-run.")


def _emit_report(gate_status: str, kms_provider: str, cfg: Any, provider_obj: Any) -> None:
    ASSURANCE_OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "gate": "HSM_KMS_SIGNING_CHECK",
        "gate_version": "v2.0-PR2",
        "result": gate_status,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "kms_provider_configured": bool(kms_provider),
            "kms_provider": kms_provider or None,
            "kms_key_id": (cfg.key_id if cfg else None),
            "kms_algorithm": (cfg.algorithm if cfg else None),
        },
        "checks": _CHECKS,
        "summary": {"total": len(_CHECKS), "passed": _PASS, "failed": _FAIL},
        "non_claims": [
            "This gate does not certify FIPS compliance unless the underlying HSM is separately certified",
            "This gate does not certify HSM tamper-proof status",
            "This gate does not grant regulatory approval",
            "PASS requires a real KMS/HSM — not a local software key",
            "This gate is not production-ready by itself — one of 12 required gates",
        ],
    }
    if gate_status == "FAIL":
        report["fail_reason"] = (
            "AEM_KMS_PROVIDER not configured — KMS/HSM provider required"
            if not kms_provider
            else "One or more checks failed"
        )
    out_path = ASSURANCE_OUT / "kms_signing_check_report.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(f"\n  Assurance report: {out_path}")


if __name__ == "__main__":
    result = run()
    sys.exit(0 if "=PASS" in result else 1)
