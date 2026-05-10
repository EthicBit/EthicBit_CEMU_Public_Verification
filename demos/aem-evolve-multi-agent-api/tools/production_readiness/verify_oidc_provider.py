#!/usr/bin/env python3
"""
v2.0 PR 1 — Production OIDC Provider Enforcement Verifier

Gate output: PRODUCTION_OIDC_PROVIDER_CHECK=PASS | FAIL

IMPORTANT: This gate FAILS when OIDC_ISSUER is not configured.
That is the correct and expected outcome for a local/demo environment.
Set OIDC_ISSUER, OIDC_JWKS_URI, and OIDC_AUDIENCE to a real external
OIDC provider to satisfy this gate.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEMO_ROOT = Path(__file__).resolve().parents[2]
ASSURANCE_OUT = DEMO_ROOT.parents[1] / "assurance" / "evolve-multi-agent" / "v2_0"

if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

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
    entry = {"id": check_id, "label": label, "status": status}
    if detail:
        entry["detail"] = detail
    _CHECKS.append(entry)
    marker = "✓" if passed else "✗"
    print(f"  [{marker}] {check_id}: {label} — {status}" + (f" ({detail})" if detail else ""))


def run() -> str:
    print("=" * 70)
    print("v2.0 PR 1 — Production OIDC Provider Enforcement Verifier")
    print("=" * 70)

    oidc_issuer = os.getenv("OIDC_ISSUER", "").strip()
    oidc_jwks_uri = os.getenv("OIDC_JWKS_URI", "").strip()
    oidc_audience = os.getenv("OIDC_AUDIENCE", "").strip()

    print(f"\nEnvironment:")
    print(f"  OIDC_ISSUER    = {oidc_issuer or '(not set)'}")
    print(f"  OIDC_JWKS_URI  = {oidc_jwks_uri or '(not set — will be inferred)'}")
    print(f"  OIDC_AUDIENCE  = {oidc_audience or '(not set — defaults to aem-evolve)'}")
    print()

    # C-01: OIDC_ISSUER env var set
    _check("C-01", "OIDC_ISSUER env var configured", bool(oidc_issuer),
           oidc_issuer or "OIDC_ISSUER not set")

    # C-02: security package importable
    try:
        from security.oidc_config import load_oidc_config, ProductionOidcConfig
        _check("C-02", "security.oidc_config importable", True)
    except ImportError as exc:
        _check("C-02", "security.oidc_config importable", False, str(exc))
        _emit_fail_closed(oidc_issuer)
        return "PRODUCTION_OIDC_PROVIDER_CHECK=FAIL"

    # C-03: security.oidc_provider importable
    try:
        from security.oidc_provider import ProductionOidcProvider
        _check("C-03", "security.oidc_provider importable", True)
    except ImportError as exc:
        _check("C-03", "security.oidc_provider importable", False, str(exc))
        _emit_fail_closed(oidc_issuer)
        return "PRODUCTION_OIDC_PROVIDER_CHECK=FAIL"

    # C-04: load_oidc_config returns None when OIDC_ISSUER not set
    if not oidc_issuer:
        cfg = load_oidc_config()
        _check("C-04", "load_oidc_config returns None (OIDC_ISSUER unset)", cfg is None,
               "Correct: gate not satisfied without external provider")
    else:
        cfg = load_oidc_config()
        _check("C-04", "load_oidc_config returns config (OIDC_ISSUER set)", cfg is not None,
               f"issuer={cfg.issuer if cfg else 'None'}")

    # C-05: from_env() mirrors config result
    provider = ProductionOidcProvider.from_env()
    expected_provider = cfg is not None
    _check("C-05", "from_env() returns provider iff config present",
           (provider is not None) == expected_provider,
           f"provider={'present' if provider else 'None'}")

    # C-06: When OIDC_ISSUER not set — gate is NOT_CONFIGURED (honest FAIL)
    if not oidc_issuer:
        _check("C-06", "gate status NOT_CONFIGURED when issuer unset",
               provider is None,
               "Correct gate behavior — FAIL_CLOSED: external IdP required")
        _check("C-07", "JWKS reachability check N/A (no issuer)", True,
               "Skipped — OIDC_ISSUER not configured")
        _check("C-08", "Issuer validation N/A", True, "Skipped")
        _check("C-09", "Audience validation N/A", True, "Skipped")
        _check("C-10", "gate_check() output structure valid", True,
               "Skipped — no provider to check")
        _emit_honest_fail(oidc_issuer)
        return "PRODUCTION_OIDC_PROVIDER_CHECK=FAIL"

    # C-06: Provider has correct issuer
    _check("C-06", "Provider issuer matches OIDC_ISSUER", provider.config.issuer == oidc_issuer,
           provider.config.issuer)

    # C-07: JWKS URI reachable
    try:
        result = provider.fetch_jwks()
        key_count = len(result.get("keys", []))
        _check("C-07", "JWKS URI reachable", True, f"{key_count} key(s) returned")
    except Exception as exc:
        _check("C-07", "JWKS URI reachable", False, str(exc))

    # C-08: JWKS contains at least one RS256 key
    try:
        jwks = provider.fetch_jwks()
        rs256_keys = [k for k in jwks.get("keys", []) if k.get("kty") == "RSA"]
        _check("C-08", "JWKS contains at least one RSA key", len(rs256_keys) > 0,
               f"{len(rs256_keys)} RSA key(s)")
    except Exception as exc:
        _check("C-08", "JWKS contains at least one RSA key", False, str(exc))

    # C-09: Audience configured correctly
    _check("C-09", "Audience configured",
           bool(provider.config.audience),
           provider.config.audience)

    # C-10: gate_check() returns structured result
    gate_result = provider.gate_check()
    valid_structure = (
        "gate" in gate_result
        and "status" in gate_result
        and gate_result["gate"] == "PRODUCTION_OIDC_PROVIDER_CHECK"
    )
    _check("C-10", "gate_check() returns valid structure", valid_structure,
           f"status={gate_result.get('status')}")

    # Determine overall result
    gate_status = "PASS" if _FAIL == 0 else "FAIL"
    _emit_report(gate_status, oidc_issuer, cfg, provider)
    result_line = f"PRODUCTION_OIDC_PROVIDER_CHECK={gate_status}"
    print()
    print(f"  Gate result: {result_line} ({_PASS}/{_PASS + _FAIL} checks passed)")
    return result_line


def _emit_honest_fail(oidc_issuer: str) -> None:
    """Emit assurance report when gate is FAIL (honest — no issuer configured)."""
    _emit_report("FAIL", oidc_issuer, None, None)
    print()
    print("  Gate result: PRODUCTION_OIDC_PROVIDER_CHECK=FAIL")
    print()
    print("  NOTE: This is the correct and expected result for a local/demo")
    print("  environment. To satisfy this gate, set OIDC_ISSUER to an external")
    print("  OIDC provider (Okta, Auth0, Azure AD, Keycloak) and re-run.")


def _emit_fail_closed(oidc_issuer: str) -> None:
    _emit_report("FAIL", oidc_issuer, None, None)
    print()
    print("  Gate result: PRODUCTION_OIDC_PROVIDER_CHECK=FAIL")


def _emit_report(gate_status: str, oidc_issuer: str, cfg: Any, provider: Any) -> None:
    ASSURANCE_OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "gate": "PRODUCTION_OIDC_PROVIDER_CHECK",
        "gate_version": "v2.0-PR1",
        "result": gate_status,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "oidc_issuer_configured": bool(oidc_issuer),
            "oidc_issuer": oidc_issuer or None,
            "oidc_jwks_uri": (cfg.jwks_uri if cfg else None),
            "oidc_audience": (cfg.audience if cfg else None),
        },
        "checks": _CHECKS,
        "summary": {"total": len(_CHECKS), "passed": _PASS, "failed": _FAIL},
        "non_claims": [
            "This gate result does not certify the external OIDC provider",
            "This gate does not grant regulatory approval",
            "This gate does not replace external IAM certification",
            "PASS requires a real external OIDC provider — not a demo key pair",
        ],
    }
    if gate_status == "FAIL":
        report["fail_reason"] = (
            "OIDC_ISSUER not configured — external OIDC provider required"
            if not oidc_issuer
            else "One or more checks failed"
        )
    out_path = ASSURANCE_OUT / "oidc_provider_check_report.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(f"\n  Assurance report: {out_path}")


if __name__ == "__main__":
    result = run()
    sys.exit(0 if "=PASS" in result else 1)
