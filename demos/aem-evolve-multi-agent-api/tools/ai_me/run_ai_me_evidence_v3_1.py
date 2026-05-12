"""
AI-ME v3.1 — Evidence Execution Runner
AEM-EVOLVE v3.1 — Controlled Environment
Constitutional dependency: EthicBit / CEMU v3.7.0+

Executes all 12 AI-ME gate verifiers and runs the aggregator.
Evidence scope: AEM-EVOLVE multi-agent governance API — controlled environment — 2026-05-12.
"""
import hashlib
import json
import os
import sys

EVIDENCE_DIR = "assurance/ai-me/v3_1/evidence"
REPORT_DIR = "assurance/ai-me/v3_1"
RECEIPTS_DIR = "assurance/ai-me/v3_1"
SCOPE = "AEM-EVOLVE multi-agent governance API — controlled environment — EthicBit / CEMU v3.7.0+"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from ai_me.verify_ai_me_01_model_evaluation import verify as v01
    from ai_me.verify_ai_me_02_bias_fairness import verify as v02
    from ai_me.verify_ai_me_03_explainability import verify as v03
    from ai_me.verify_ai_me_04_data_lineage import verify as v04
    from ai_me.verify_ai_me_05_agent_trace import verify as v05
    from ai_me.verify_ai_me_06_tool_call_governance import verify as v06
    from ai_me.verify_ai_me_07_memory_mutation import verify as v07
    from ai_me.verify_ai_me_08_hitl_review import verify as v08
    from ai_me.verify_ai_me_09_multi_agent import verify as v09
    from ai_me.verify_ai_me_10_red_team import verify as v10
    from ai_me.verify_ai_me_11_decision_logging import verify as v11
    from ai_me.verify_ai_me_12_claim_boundary import verify as v12
    from ai_me.aggregate_ai_me_v3_1 import aggregate

    def artifact(name: str) -> tuple:
        path = os.path.join(EVIDENCE_DIR, name)
        return path, sha256_file(path)

    print("=== AI-ME v3.1 Evidence Execution ===")
    print(f"Scope: {SCOPE}")
    print()

    a01_path, a01_hash = artifact("AI_ME_01_model_evaluation_artifact.json")
    r01 = v01(a01_path, a01_hash, "aem-evolve-multi-agent-governance-api-v3.1", SCOPE, output_dir=REPORT_DIR)
    print(f"AI-ME-01 {r01['gate_outcome']}")

    a02_path, a02_hash = artifact("AI_ME_02_fairness_evaluation_artifact.json")
    r02 = v02(
        a02_path, a02_hash,
        protected_attributes=["operator_identity", "artifact_type", "request_timestamp"],
        methodology="Structural parity evaluation of governance gate outcomes across equivalent input classes",
        evaluation_scope=SCOPE,
        output_dir=REPORT_DIR,
    )
    print(f"AI-ME-02 {r02['gate_outcome']}")

    a03_path, a03_hash = artifact("AI_ME_03_explainability_artifact.json")
    r03 = v03(
        a03_path, a03_hash,
        methodology="rule_based_deterministic",
        application_scope=SCOPE,
        output_dir=REPORT_DIR,
    )
    print(f"AI-ME-03 {r03['gate_outcome']}")

    a04_path, a04_hash = artifact("AI_ME_04_data_provenance_artifact.json")
    r04 = v04(
        a04_path, a04_hash,
        data_sources=["aem_evolve_audit_sqlite", "aem_evolve_artifact_manifests", "aem_evolve_anchor_receipts"],
        lineage_scope=SCOPE,
        fast_path_enabled=False,
        output_dir=REPORT_DIR,
    )
    print(f"AI-ME-04 {r04['gate_outcome']}")

    a05_path, a05_hash = artifact("AI_ME_05_agent_trace_artifact.json")
    r05 = v05(a05_path, a05_hash, SCOPE, raw_cot_captured=False, output_dir=REPORT_DIR)
    print(f"AI-ME-05 {r05['gate_outcome']}")

    a06_path, a06_hash = artifact("AI_ME_06_tool_call_governance_artifact.json")
    r06 = v06(a06_path, a06_hash, SCOPE,
              authorization_policy_reference="docs/architecture/ETHICBIT_CONSTITUTIONAL_TECHNOLOGY_BRIDGE.md",
              output_dir=REPORT_DIR)
    print(f"AI-ME-06 {r06['gate_outcome']}")

    a07_path, a07_hash = artifact("AI_ME_07_memory_mutation_artifact.json")
    r07 = v07(a07_path, a07_hash, SCOPE,
              authorization_policy_reference="docs/architecture/AEM_V1_1_ARTIFACT_ASSURANCE_CONTINUITY.md",
              output_dir=REPORT_DIR)
    print(f"AI-ME-07 {r07['gate_outcome']}")

    a08_path, a08_hash = artifact("AI_ME_08_hitl_decision_artifact.json")
    r08 = v08(a08_path, a08_hash, "governance_decision", SCOPE,
              reviewer_identity_recorded=True, output_dir=REPORT_DIR)
    print(f"AI-ME-08 {r08['gate_outcome']}")

    a09_path, a09_hash = artifact("AI_ME_09_multi_agent_coordination_artifact.json")
    r09 = v09(a09_path, a09_hash, SCOPE, agent_roles_declared=True, output_dir=REPORT_DIR)
    print(f"AI-ME-09 {r09['gate_outcome']}")

    a10_path, a10_hash = artifact("AI_ME_10_red_team_artifact.json")
    r10 = v10(a10_path, a10_hash, SCOPE, methodology_documented=True, output_dir=REPORT_DIR)
    print(f"AI-ME-10 {r10['gate_outcome']}")

    a11_path, a11_hash = artifact("AI_ME_11_decision_log_artifact.json")
    r11 = v11(a11_path, a11_hash, SCOPE, appeal_procedure_documented=True, output_dir=REPORT_DIR)
    print(f"AI-ME-11 {r11['gate_outcome']}")

    a12_path, a12_hash = artifact("AI_ME_12_claim_boundary_enforcement_artifact.json")
    r12 = v12(a12_path, a12_hash, SCOPE, claim_level_ceilings_recorded=True, output_dir=REPORT_DIR)
    print(f"AI-ME-12 {r12['gate_outcome']}")

    print()
    print("=== Aggregating ===")
    agg = aggregate(report_dir=REPORT_DIR)
    print(f"AGGREGATE OUTCOME: {agg['aggregate_outcome']}")
    print(f"Gates evaluated:   {agg['gates_evaluated']}")
    print(f"PASS:              {agg['gates_pass']}")
    print(f"SCOPE_LIMITED:     {agg['gates_scope_limited']}")
    print(f"FAIL_CLOSED:       {agg['gates_fail_closed']}")
    print(f"MISSING:           {agg['gates_missing']}")
    print(f"PENDING:           {agg['gates_pending']}")
    violations = agg.get("fast_path_illegal_upgrade_violations", [])
    print(f"Fast Path violations: {len(violations)}")
    print()
    print(f"Aggregate report: {REPORT_DIR}/AI_ME_V3_1_AGGREGATE_REPORT.json")
    return agg


if __name__ == "__main__":
    main()
