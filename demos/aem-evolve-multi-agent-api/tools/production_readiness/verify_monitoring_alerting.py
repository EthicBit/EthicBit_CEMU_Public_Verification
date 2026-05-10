#!/usr/bin/env python3
"""
AEM-EVOLVE™ v2.0 PR 5 — Monitoring and Alerting Evidence Gate Verifier.

Usage:
    python tools/production_readiness/verify_monitoring_alerting.py

Set AEM_PROMETHEUS_URL to enable C-08/C-09/C-10 live Prometheus checks.

Exit code:
    0 = PASS
    1 = FAIL (expected in local/demo — AEM_PROMETHEUS_URL not configured)
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[2]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from monitoring.monitoring_gate import MonitoringGate

_CHECKS = [
    ("C-01", "alert_rules_yaml",         "Alert rules YAML with all 7 mandatory rules"),
    ("C-02", "alertmanager_config",       "Alertmanager routing and receiver config"),
    ("C-03", "grafana_dashboard",         "Grafana dashboard with all 7 metric panels"),
    ("C-04", "counter_registration",      "Governance failure counters registered in metrics module"),
    ("C-05", "counter_name_consistency",  "Counter names consistent between code and alert rules"),
    ("C-06", "metrics_endpoint",          "Metrics endpoint present and counters wired in code"),
    ("C-07", "receiver_configured",       "Alertmanager receiver has notification channel"),
    ("C-08", "prometheus_reachable",      "Prometheus scrape endpoint reachable (live)"),
    ("C-09", "alert_rules_loaded",        "Alert rules loaded in live Prometheus"),
    ("C-10", "alert_can_fire",            "Governance counter queryable in Prometheus"),
]


def _fmt(ok: bool, skipped: bool = False) -> str:
    if skipped:
        return "SKIP"
    return "PASS" if ok else "FAIL"


def main() -> int:
    gate = MonitoringGate.from_env()
    result = gate.gate_check()
    checks = result["checks"]

    print("=" * 70)
    print("AEM-EVOLVE™ v2.0 PR 5 — Monitoring & Alerting Evidence Gate")
    print("=" * 70)
    print(f"Prometheus URL : {gate._prometheus_url or '(not configured)'}")
    print()

    for code, key, description in _CHECKS:
        full_key = f"{code}_{key}"
        c = checks.get(full_key, {})
        ok = c.get("ok", False)
        skipped = c.get("skipped", False)
        status = _fmt(ok, skipped)
        print(f"  [{status:4s}] {code}: {description}")
        if not ok and not skipped:
            detail = (
                c.get("detail")
                or c.get("fail_reason")
                or c.get("missing_alerts")
                or c.get("missing_prom_metrics")
                or c.get("counters_not_yet_wired")
                or c.get("mismatches")
            )
            if detail:
                print(f"         → {detail}")
        elif skipped:
            print(f"         → {c.get('reason', 'skipped')}")

    print()
    print(f"Checks passed : {result['checks_passed']}/{len(_CHECKS)}")
    print(f"Gate status   : {result['status']}")
    if result.get("fail_reason"):
        print(f"Fail reason   : {result['fail_reason']}")

    print()

    # ── Assurance report ────────────────────────────────────────────────────
    report = {
        "report_type": "AEM_EVOLVE_GATE_EVIDENCE",
        "gate": "MONITORING_ALERTING_CHECK",
        "pr": "PR5",
        "version": "0.12.0-demo",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "environment_name": os.getenv("AEM_ENV_NAME", "local-demo"),
            "cloud_provider": os.getenv("AEM_CLOUD_PROVIDER", "N/A"),
            "region": os.getenv("AEM_REGION", "N/A"),
            "deployment_date": os.getenv("AEM_DEPLOYMENT_DATE", "N/A"),
            "version_tag": "v2.0.0-pr5",
            "container_image_digest": os.getenv("AEM_CONTAINER_IMAGE_DIGEST", "N/A"),
        },
        "result": result,
        "non_claims": [
            "alert_delivery_not_verified_without_live_alertmanager",
            "prometheus_scrape_not_verified_without_AEM_PROMETHEUS_URL",
            "grafana_dashboard_not_imported_into_live_grafana",
            "counter_values_are_in_memory_not_persistent",
        ],
    }

    report_dir = DEMO_ROOT / "assurance" / "evolve-multi-agent" / "v2_0"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "monitoring_alerting_check_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Assurance report → {report_path}")

    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
