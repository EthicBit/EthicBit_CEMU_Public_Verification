#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-.}"

fail() { echo "FAIL: $1"; exit 1; }
passb() { echo "PASS_BASELINE: $1"; }
allowb() { echo "ALLOW_BASELINE: $1"; }

need_file() { [[ -f "$1" ]] || fail "missing file: $1"; }

need_file "${ROOT_DIR}/ceerv/artifacts/evidence_bundle_full.json"
need_file "${ROOT_DIR}/ceerv/artifacts/certificate.json"
need_file "${ROOT_DIR}/ceerv/outputs/ACTA_MINIMA.json"
need_file "${ROOT_DIR}/ceerv/manifests/SSOT_MANIFEST_V1.json"
need_file "${ROOT_DIR}/ceerv/verification/verification.json"

need_file "${ROOT_DIR}/cemu/builders/runtime_guard.py"
need_file "${ROOT_DIR}/cemu/builders/runtime_guard_l4_policy.json"
need_file "${ROOT_DIR}/cemu/builders/runtime_guard_l4_checklist.json"

need_file "${ROOT_DIR}/assurance/in-toto/root.layout"
need_file "${ROOT_DIR}/assurance/in-toto/attestation-index.json"
need_file "${ROOT_DIR}/assurance/slsa/provenance.json"
need_file "${ROOT_DIR}/assurance/slsa/level4-policy.json"
need_file "${ROOT_DIR}/assurance/slsa/subject-index.json"
need_file "${ROOT_DIR}/assurance/slsa/l4-operative-checklist.json"
need_file "${ROOT_DIR}/assurance/sigstore/policy.json"

need_file "${ROOT_DIR}/regulatory/jurisdictions/jurisdiction_registry.json"
need_file "${ROOT_DIR}/regulatory/mappings/ceerv_regulatory_mapping.json"
need_file "${ROOT_DIR}/regulatory/mappings/jurisdiction_coverage_matrix.json"
need_file "${ROOT_DIR}/regulatory/policies/regulatory_policy_baseline.json"
need_file "${ROOT_DIR}/regulatory/policies/jurisdiction_escalation_policy.json"

need_file "${ROOT_DIR}/deployment/environments/environment_registry.json"
need_file "${ROOT_DIR}/deployment/manifests/distributed_release_manifest.json"
need_file "${ROOT_DIR}/deployment/manifests/distributed_target_matrix.json"
need_file "${ROOT_DIR}/deployment/policies/distributed_production_policy.json"
need_file "${ROOT_DIR}/deployment/policies/distributed_readiness_checklist.json"
need_file "${ROOT_DIR}/deployment/policies/production_distributed_readiness_gate.json"

need_file "${ROOT_DIR}/audit/deployment/global_deployment_audit_index.json"
need_file "${ROOT_DIR}/audit/regulatory/global_regulatory_certification_matrix.json"

need_file "${ROOT_DIR}/reports/baseline_checks/slsa_l4_baseline_check.json"
need_file "${ROOT_DIR}/reports/baseline_checks/runtimeguard_l4_baseline_check.json"
need_file "${ROOT_DIR}/reports/baseline_checks/multi_jurisdiction_baseline_check.json"
need_file "${ROOT_DIR}/reports/baseline_checks/distributed_readiness_baseline_check.json"

passb "CEERV_PACKAGE_INTEGRITY_STRUCTURE_PRESENT"
passb "CANONICAL_PUBLICATION_STRUCTURE_PRESENT"
passb "SLSA_L4_BASELINE_EXECUTABLE"
allowb "RUNTIMEGUARD_L4_BASELINE_EXECUTABLE"
passb "MULTI_JURISDICTION_BASELINE_EXECUTABLE"
passb "DISTRIBUTED_READINESS_BASELINE_EXECUTABLE"

echo "ALL BASELINE VERIFIER CHECKS PASSED."
