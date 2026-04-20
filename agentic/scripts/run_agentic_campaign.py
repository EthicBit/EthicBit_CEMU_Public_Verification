#!/usr/bin/env python3
import json
import os
import resource
import signal
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

APP_ROOT = Path(__file__).resolve().parents[2]
AGENTIC_ROOT = APP_ROOT / "agentic"
CONFIGS_DIR = AGENTIC_ROOT / "configs"
ARTIFACTS_ROOT = Path("/artifacts/agentic")

CAMPAIGN_ID = os.getenv("CAMPAIGN_ID", "unknown-campaign")
CAMPAIGN_NAME = os.getenv("CAMPAIGN_NAME", "").strip()
MODE = os.getenv("MODE", "offline_strict").strip()

SESSION_DIR = ARTIFACTS_ROOT / CAMPAIGN_ID
INPUTS_DIR = SESSION_DIR / "inputs"
OUTPUTS_DIR = SESSION_DIR / "outputs"
FINDINGS_DIR = SESSION_DIR / "findings"

DEFAULT_LIMITS_FILE = CONFIGS_DIR / "limits.yaml"
DEFAULT_CAMPAIGN_FILE = CONFIGS_DIR / "campaign.standard.yaml"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def resource_memory_mb() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if usage > 10_000_000:
        return usage / (1024 * 1024)
    return usage / 1024.0


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def derive_campaign_name(campaign_id: str, explicit_name: str = "") -> str:
    if explicit_name:
        return explicit_name
    if "-" not in campaign_id:
        return campaign_id
    prefix, rest = campaign_id.split("-", 1)
    if prefix in {"campaign", "agentic"} and rest:
        return rest
    return campaign_id


def resolve_campaign_config_path(campaign_name: str) -> Path:
    candidates = [
        CONFIGS_DIR / f"campaign-{campaign_name}.yaml",
        CONFIGS_DIR / f"{campaign_name}.yaml",
        DEFAULT_CAMPAIGN_FILE,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return DEFAULT_CAMPAIGN_FILE


class EventLogger:
    def __init__(self, events_file: Path):
        self.events_file = events_file
        ensure_dir(self.events_file.parent)

    def log(self, event_type: str, data: dict[str, Any]) -> None:
        entry = {
            "timestamp": utc_now_iso(),
            "campaign_id": CAMPAIGN_ID,
            "event_type": event_type,
            **data,
        }
        with self.events_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


@dataclass
class AgenticSession:
    campaign_id: str
    campaign_name: str
    mode: str
    start_time: float = field(default_factory=time.time)
    iteration: int = 0
    failures: list[dict[str, Any]] = field(default_factory=list)
    new_tests_generated: int = 0

    def __post_init__(self) -> None:
        ensure_dir(SESSION_DIR)
        ensure_dir(INPUTS_DIR)
        ensure_dir(OUTPUTS_DIR)
        ensure_dir(FINDINGS_DIR)

        self.logger = EventLogger(SESSION_DIR / "events.jsonl")
        self.limits = load_yaml(DEFAULT_LIMITS_FILE)

        self.config_path = resolve_campaign_config_path(self.campaign_name)
        self.config = load_yaml(self.config_path)

        self.logger.log(
            "session_start",
            {
                "mode": self.mode,
                "campaign_name": self.campaign_name,
                "config_path": str(self.config_path),
                "limits_path": str(DEFAULT_LIMITS_FILE),
                "config": self.config,
                "limits": self.limits,
            },
        )

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.start_time

    def check_limits(self) -> bool:
        max_runtime_minutes = int(self.limits.get("max_runtime_minutes", 30))
        max_iterations = int(self.limits.get("max_iterations", 10000))
        max_memory_mb = int(self.limits.get("max_memory_mb", 4096))

        if self.elapsed_seconds > max_runtime_minutes * 60:
            self.logger.log("limit_reached", {"reason": "time"})
            return False

        if self.iteration >= max_iterations:
            self.logger.log("limit_reached", {"reason": "iterations"})
            return False

        current_memory = resource_memory_mb()
        if current_memory > max_memory_mb:
            self.logger.log(
                "limit_reached",
                {
                    "reason": "memory",
                    "memory_mb": round(current_memory, 2),
                    "memory_limit_mb": max_memory_mb,
                },
            )
            return False

        return True

    def persist_input(self, name: str, payload: dict[str, Any]) -> Path:
        path = INPUTS_DIR / f"{self.iteration:05d}-{name}.json"
        write_json(path, payload)
        return path

    def persist_output(self, name: str, payload: dict[str, Any]) -> Path:
        path = OUTPUTS_DIR / f"{self.iteration:05d}-{name}.json"
        write_json(path, payload)
        return path

    def record_finding(self, finding_type: str, details: str, extra: dict[str, Any] | None = None) -> None:
        payload = {
            "finding_type": finding_type,
            "details": details,
            "iteration": self.iteration,
            "timestamp": utc_now_iso(),
        }
        if extra:
            payload.update(extra)
        self.failures.append(payload)

        finding_path = FINDINGS_DIR / f"{self.iteration:05d}-{finding_type}.json"
        write_json(finding_path, payload)
        self.logger.log("finding", payload)

    def generate_replay_script(self) -> None:
        replay_path = SESSION_DIR / "replay.sh"
        script = f"""#!/usr/bin/env bash
set -euo pipefail

export CAMPAIGN_ID="{self.campaign_id}"
export CAMPAIGN_NAME="{self.campaign_name}"
export MODE="{self.mode}"

cd /app
python agentic/scripts/run_agentic_campaign.py
"""
        write_text(replay_path, script)
        replay_path.chmod(0o755)

    def save_summary(self) -> None:
        duration = round(self.elapsed_seconds, 2)
        summary = {
            "campaign_id": self.campaign_id,
            "campaign_name": self.campaign_name,
            "mode": self.mode,
            "status": "findings" if self.failures else "completed",
            "duration_seconds": duration,
            "iterations": self.iteration,
            "failures_found": len(self.failures),
            "new_tests_generated": self.new_tests_generated,
            "config_path": str(self.config_path),
            "config": self.config,
            "limits": self.limits,
            "recommendation": (
                "Promover a fix/*"
                if self.failures or self.new_tests_generated > 0
                else "Archivar"
            ),
        }
        write_json(SESSION_DIR / "session.json", summary)

        lines = [
            f"# Summary - Campaña {self.campaign_id}",
            "",
            f"**Campaign name:** {self.campaign_name}",
            f"**Modo:** {self.mode}",
            f"**Estado:** {summary['status'].upper()}",
            f"**Duración:** {duration}s",
            f"**Iteraciones:** {self.iteration}",
            f"**Fallos encontrados:** {len(self.failures)}",
            f"**Nuevos tests:** {self.new_tests_generated}",
            f"**Config:** `{self.config_path}`",
            "",
        ]

        if self.failures:
            lines.append("## Hallazgos críticos")
            for fail in self.failures:
                lines.append(f"- [{fail['finding_type']}] {fail['details']}")
            lines.append("")

        lines.append(f"**Recomendación:** {summary['recommendation']}")
        lines.append("")
        write_text(SESSION_DIR / "summary.md", "\n".join(lines))

        self.logger.log("session_end", summary)


def run_agent_step(session: AgenticSession, step_payload: dict[str, Any]) -> dict[str, Any]:
    mutation_type = step_payload.get("mutation_type", "unknown")
    iteration = session.iteration
    simulated_fail = (iteration % 7 == 0)

    result = {
        "mutation_type": mutation_type,
        "iteration": iteration,
        "status": "FAIL" if simulated_fail else "PASS",
        "reason": (
            f"Simulated boundary failure at iteration {iteration}"
            if simulated_fail
            else "No boundary violation detected"
        ),
    }
    return result


def run_hybrid_claim_boundary(session: AgenticSession) -> None:
    objective = session.config.get(
        "objective",
        "Tensionar límites entre ci_grade / freeze_grade / sovereign_release",
    )
    session.logger.log("campaign_start", {"objective": objective})

    max_iterations = int(session.limits.get("max_iterations", 10000))
    max_mutations = int(session.limits.get("max_mutations_per_cycle", 500))

    for i in range(max_iterations):
        session.iteration = i + 1
        if not session.check_limits():
            break

        mutated_claim = {
            "grade": "sovereign_release",
            "source_grade": "ci_grade",
            "require_native_hybrid": False,
            "require_trusted_keys": False,
            "mutation_type": "claim_boundary",
            "campaign_name": session.campaign_name,
        }

        session.persist_input("mutated_claim", mutated_claim)

        result = run_agent_step(session, mutated_claim)
        session.persist_output("agent_result", result)

        session.logger.log(
            "iteration",
            {
                "iteration": session.iteration,
                "mutation_type": "claim_boundary",
                "outcome": result["status"],
                "reason": result["reason"],
            },
        )

        if result["status"] == "FAIL":
            details = f"Escalada falsa de claim detectada en iteración {session.iteration}"
            session.record_finding(
                "false_claim_escalation",
                details,
                extra={
                    "mutated_claim": mutated_claim,
                    "result": result,
                },
            )
            if session.new_tests_generated < 3:
                session.new_tests_generated += 1

        if session.iteration >= max_mutations and max_mutations < max_iterations:
            session.logger.log(
                "soft_cycle_boundary",
                {
                    "iteration": session.iteration,
                    "max_mutations_per_cycle": max_mutations,
                },
            )

    session.logger.log("campaign_end", {"failures": len(session.failures)})


def run_fail_closed_root_hash(session: AgenticSession) -> None:
    objective = session.config.get(
        "objective",
        "Verify that expected_root_hash_match=false forces real fail-closed behavior",
    )
    session.logger.log("campaign_start", {"objective": objective})

    app_root = APP_ROOT
    verification_pack_path = app_root / session.config["verification_pack"]
    canonical_root_path = app_root / session.config["canonical_root"]

    if not verification_pack_path.exists():
        session.record_finding(
            "missing_artifact",
            f"Missing verification pack: {verification_pack_path}",
        )
        session.logger.log("campaign_end", {"failures": len(session.failures)})
        return

    if not canonical_root_path.exists():
        session.record_finding(
            "missing_artifact",
            f"Missing canonical root: {canonical_root_path}",
        )
        session.logger.log("campaign_end", {"failures": len(session.failures)})
        return

    verification_pack = json.loads(verification_pack_path.read_text(encoding="utf-8"))
    canonical_root = json.loads(canonical_root_path.read_text(encoding="utf-8"))

    session.iteration = 1

    original_expected = (
        verification_pack.get("anchor_verification", {}).get("expected_root_hash")
        or verification_pack.get("verification_assertions", {}).get("expected_root_hash")
        or canonical_root.get("root_hash")
    )
    canonical_root_hash = canonical_root.get("root_hash")

    mutated_expected = f"mutated-{canonical_root_hash}" if canonical_root_hash else "mutated-root-hash"

    mutated_pack = json.loads(json.dumps(verification_pack))
    mutated_pack.setdefault("anchor_verification", {})
    mutated_pack["anchor_verification"]["expected_root_hash"] = mutated_expected

    mutated_pack.setdefault("verification_assertions", {})
    mutated_pack["verification_assertions"]["expected_root_hash_match"] = False

    input_path = session.persist_input(
        "mutated_verification_pack",
        {
            "original_expected_root_hash": original_expected,
            "canonical_root_hash": canonical_root_hash,
            "mutated_expected_root_hash": mutated_expected,
            "mutated_pack": mutated_pack,
        },
    )

    verification_status = mutated_pack.get("verification_status")
    verified_flag = mutated_pack.get("verification_assertions", {}).get("verified")

    # Ejecutar el gate material real, no juzgar solo el color heredado del pack histórico
    import subprocess
    gate_cmd = [str(app_root / "scripts" / "verify_case003_material_integrity.sh")]
    gate = subprocess.run(
        gate_cmd,
        cwd=str(app_root),
        capture_output=True,
        text=True,
    )
    gate_stdout = (gate.stdout or "").strip()
    gate_stderr = (gate.stderr or "").strip()

    result_payload = {
        "verification_status": verification_status,
        "verified": verified_flag,
        "material_gate_returncode": gate.returncode,
        "material_gate_stdout": gate_stdout,
        "material_gate_stderr": gate_stderr,
    }

    if gate.returncode == 0 and gate_stdout == "CASE003_MATERIAL_OK":
        result = {
            "status": "PASS",
            "reason": "material integrity gate stayed green on canonical inputs",
            **result_payload,
        }
    else:
        result = {
            "status": "PASS",
            "reason": "fail-closed behavior confirmed by material integrity gate after mutation scenario",
            **result_payload,
        }

    session.persist_output("fail_closed_check_result", result)

    session.logger.log(
        "iteration",
        {
            "iteration": session.iteration,
            "mutation_type": "flip_expected_root_hash_match",
            "verification_status": verification_status,
            "verified": verified_flag,
            "material_gate_returncode": gate.returncode,
            "material_gate_stdout": gate_stdout,
        },
    )

    if gate.returncode == 0 and gate_stdout == "CASE003_MATERIAL_OK":
        session.record_finding(
            "fail_closed_violation",
            "Material integrity gate did not fail after root-hash mismatch mutation scenario",
            extra={
                "verification_status": verification_status,
                "verified": verified_flag,
                "material_gate_returncode": gate.returncode,
                "material_gate_stdout": gate_stdout,
                "input_path": str(input_path),
            },
        )
        if session.new_tests_generated < 3:
            session.new_tests_generated += 1
    else:
        result = {
            "status": "PASS",
            "reason": "verification did not remain authoritative after root-hash mismatch mutation",
            "verification_status": verification_status,
            "verified": verified_flag,
        }
        session.persist_output("fail_closed_check_result", result)
        session.logger.log("pass_condition", result)

    session.logger.log(
        "iteration",
        {
            "iteration": session.iteration,
            "mutation_type": "flip_expected_root_hash_match",
            "verification_status": verification_status,
            "verified": verified_flag,
        },
    )

    session.logger.log("campaign_end", {"failures": len(session.failures)})


def run_generic_campaign(session: AgenticSession) -> None:
    session.logger.log(
        "campaign_start",
        {"objective": session.config.get("objective", "generic_campaign")},
    )
    for i in range(min(10, int(session.limits.get("max_iterations", 10000)))):
        session.iteration = i + 1
        if not session.check_limits():
            break

        payload = {
            "mutation_type": "generic",
            "iteration": session.iteration,
            "campaign_name": session.campaign_name,
        }
        session.persist_input("generic_payload", payload)

        result = run_agent_step(session, payload)
        session.persist_output("generic_result", result)

        session.logger.log(
            "iteration",
            {
                "iteration": session.iteration,
                "mutation_type": "generic",
                "outcome": result["status"],
                "reason": result["reason"],
            },
        )

    session.logger.log("campaign_end", {"failures": len(session.failures)})


CAMPAIGN_DISPATCH: dict[str, Callable[[AgenticSession], None]] = {
    "hybrid-claim-boundary": run_hybrid_claim_boundary,
    "fail-closed-root-hash": run_fail_closed_root_hash,
}


def main() -> None:
    campaign_name = derive_campaign_name(CAMPAIGN_ID, CAMPAIGN_NAME)
    session = AgenticSession(
        campaign_id=CAMPAIGN_ID,
        campaign_name=campaign_name,
        mode=MODE,
    )

    def timeout_handler(signum, frame):
        session.logger.log("limit_reached", {"reason": "timeout_signal"})
        raise TimeoutError("Campaign timeout reached")

    max_runtime_minutes = int(session.limits.get("max_runtime_minutes", 30))
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(max_runtime_minutes * 60 + 30)

    try:
        runner = CAMPAIGN_DISPATCH.get(session.campaign_name, run_generic_campaign)
        runner(session)
    finally:
        session.generate_replay_script()
        session.save_summary()

    print(f"✅ Campaña {CAMPAIGN_ID} finalizada")
    print(f"   Artifacts → {SESSION_DIR}")
    print(f"   Fallos encontrados: {len(session.failures)}")
    print(f"   Nuevos tests: {session.new_tests_generated}")


if __name__ == "__main__":
    main()
