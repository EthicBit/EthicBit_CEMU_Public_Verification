# scripts/swarm/case_003/cemu_case_003_status_reporter.py
# ETHICBIT / CEMU – CASE 003
# Status Reporter
# Outputs:
#   - case_003_status.md
#   - case_003_integrity_manifest.sha256

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path


CASE_ID = "case_003"
BASE_DIR = Path(__file__).resolve().parents[3]
ARTIFACTS_DIR = BASE_DIR / "artifacts" / "cases" / CASE_ID
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

STATUS_FILE = ARTIFACTS_DIR / "case_003_status.md"
INTEGRITY_FILE = ARTIFACTS_DIR / "case_003_integrity_manifest.sha256"

TRACKED_FILES = [
    "runtime_constitutional_assessment.case_003.canonical.json",
    "ensemble_evaluation.case_003.canonical.json",
    "freeze_decision.case_003.canonical.json",
    "runtime_audit_trail.case_003.canonical.json",
    "swarm_containment_state.case_003.canonical.json",
    "post_event_isolation_bundle.case_003.canonical.json",
    "derived_outputs.case_003.canonical.json",
    "residual_gap_state.case_003.canonical.json",
    "artifact_manifest.case_003.canonical.json",
    "collective_pack.case_003.canonical.json",
    "case_bundle.case_003.canonical.json",
    "canonical_root.case_003.json",
    "anchor_prepare.case_003.canonical.json",
    "anchor_receipt.case_003.canonical.json",
    "anchor_verification.case_003.canonical.json",
    "verification_environment.case_003.canonical.json",
    "verification_pack.case_003.canonical.json",
    "pre_sealing_record.case_003.canonical.json",
    "closure_state.case_003.canonical.json",
    "formal_closure_certificate.case_003.canonical.json",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def build_status() -> str:
    lines = []
    lines.append(f"# ETHICBIT / CEMU – {CASE_ID.upper()} STATUS")
    lines.append("")
    lines.append(f"Generated at: {now_iso()}")
    lines.append("")
    lines.append("| Artifact | Present | SHA-256 |")
    lines.append("|---|---|---|")

    present_count = 0
    for name in TRACKED_FILES:
        path = ARTIFACTS_DIR / name
        if path.exists():
            digest = sha256_file(path)
            present = "YES"
            present_count += 1
        else:
            digest = "-"
            present = "NO"
        lines.append(f"| {name} | {present} | {digest} |")

    lines.append("")
    lines.append(f"Artifacts present: {present_count}/{len(TRACKED_FILES)}")
    lines.append("")
    if present_count == len(TRACKED_FILES):
        lines.append("Overall status: COMPLETE_ARTIFACT_SET_PRESENT")
    else:
        lines.append("Overall status: PARTIAL_ARTIFACT_SET_PRESENT")

    return "\n".join(lines) + "\n"


def build_integrity_manifest() -> str:
    lines = []
    for name in TRACKED_FILES:
        path = ARTIFACTS_DIR / name
        if path.exists():
            lines.append(f"{sha256_file(path)}  {name}")
    return "\n".join(lines) + "\n"


def main() -> None:
    status_text = build_status()
    integrity_text = build_integrity_manifest()

    STATUS_FILE.write_text(status_text, encoding="utf-8")
    INTEGRITY_FILE.write_text(integrity_text, encoding="utf-8")

    print("=" * 88)
    print("ETHICBIT / CEMU – CASE 003 STATUS REPORTER")
    print("=" * 88)
    print(f"Status file:            {STATUS_FILE}")
    print(f"Integrity manifest:     {INTEGRITY_FILE}")
    print("=" * 88)


if __name__ == "__main__":
    main()
