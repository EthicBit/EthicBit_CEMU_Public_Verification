#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

snapshot_path = ROOT / "results/constitutional_amendment_snapshot.json"
controls_path = ROOT / "results/constitutional_controls_report.json"
tech_md_path = ROOT / "results/technical_verification.md"

snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

controls = json.loads(controls_path.read_text(encoding="utf-8"))
controls["constitutionalAmendment"] = snapshot
controls["constitutionalSnapshotPath"] = "results/constitutional_amendment_snapshot.json"
controls_path.write_text(json.dumps(controls, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

section = f"""

## Constitutional Amendment Snapshot

- Amendment snapshot artifact: `results/constitutional_amendment_snapshot.json`
- Amendment ID: `{snapshot.get("amendment_id")}`
- Constitutional scope: `{snapshot.get("constitutional_scope")}`
- Rule count: `{snapshot.get("rule_count")}`

### Rules
"""

for rule in snapshot.get("rules", []):
    section += (
        f"- `{rule.get('rule_id')}` | "
        f"visibility={rule.get('entity_visibility')} | "
        f"detectability={rule.get('entity_detectability')} | "
        f"detection_mode={rule.get('detection_mode')} | "
        f"cross_sector_activation={rule.get('cross_sector_activation')}\n"
    )

tech_text = tech_md_path.read_text(encoding="utf-8") if tech_md_path.exists() else "# Technical Verification\n"
marker = "\n## Constitutional Amendment Snapshot\n"
if marker in tech_text:
    tech_text = tech_text.split(marker)[0].rstrip() + "\n"
tech_text += section
tech_md_path.write_text(tech_text, encoding="utf-8")

print("OK: constitutional_controls_report.json actualizado")
print("OK: technical_verification.md actualizado")
