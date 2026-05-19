#!/usr/bin/env bash
# EthicBit / CEMU — Independent Reproduction Runner
#
# Usage (from repo root):
#   bash scripts/reproduce_e2e.sh
#
# Flags:
#   SKIP_INSTALL=1   — skip pip install (use existing venv)
#
# What a PASS means:
#   - 15 unit/integration tests pass
#   - 8 Hypothesis property invariants pass (claim boundary)
#   - Claim red-team: 14/14 overclaims blocked (block_rate=100%)
#   - 4/4 SLSA subject digests bound to subject-index
#   - LangGraph governance E2E: 6/6 checks PASS (no LLM API key needed)
#
# Non-claim: PASS here does NOT constitute third-party reproduction completion.
# That requires an independent external reviewer to attest the result.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SEP="================================================================"
PASS_COUNT=0
FAIL_COUNT=0
RESULTS=()

pass() { PASS_COUNT=$((PASS_COUNT+1)); RESULTS+=("PASS  $1"); echo "  [PASS] $1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT+1)); RESULTS+=("FAIL  $1"); echo "  [FAIL] $1"; }

echo "$SEP"
echo "EthicBit / CEMU — Reproduction Runner"
echo "Commit: $(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN)"
echo "Date:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "$SEP"

# ── 1. Install ────────────────────────────────────────────────────────────────
if [[ "${SKIP_INSTALL:-0}" != "1" ]]; then
  echo ""
  echo "→ Installing dependencies..."
  pip install -e ".[dev]" -q
  pip install -r integrations/langgraph/requirements.txt -q
fi

# ── 2. Unit + integration tests ───────────────────────────────────────────────
echo ""
echo "→ Unit / integration tests (pytest)..."
if python3 -m pytest tests/ -q --tb=short 2>&1 | tee /tmp/repro_pytest.txt | tail -3; then
  TESTS=$(grep -E '^[0-9]+ passed' /tmp/repro_pytest.txt | grep -oE '^[0-9]+' || echo 0)
  if [[ "${TESTS}" -ge 15 ]]; then
    pass "pytest: ${TESTS} passed"
  else
    fail "pytest: only ${TESTS}/15 passed"
  fi
else
  fail "pytest: suite failed"
fi

# ── 3. Hypothesis property invariants ─────────────────────────────────────────
echo ""
echo "→ Claim boundary Hypothesis invariants..."
if python3 -m pytest tests/test_claim_boundary_properties.py -q --tb=short 2>&1 | tee /tmp/repro_hypothesis.txt | tail -3; then
  HYPO=$(grep -E '^[0-9]+ passed' /tmp/repro_hypothesis.txt | grep -oE '^[0-9]+' || echo 0)
  if [[ "${HYPO}" -ge 8 ]]; then
    pass "Hypothesis invariants: ${HYPO}/8 passed"
  else
    fail "Hypothesis invariants: only ${HYPO}/8 passed"
  fi
else
  fail "Hypothesis invariants: suite failed"
fi

# ── 4. Claim boundary red-team ────────────────────────────────────────────────
echo ""
echo "→ Claim red-team (14 overclaim attempts)..."
REDTEAM_OUT="$(python3 tools/external_validation/claim_red_team/run_claim_red_team.py 2>&1)"
if echo "$REDTEAM_OUT" | grep -q "CLAIM_BOUNDARY_RED_TEAM=PASS"; then
  BLOCK_RATE="$(echo "$REDTEAM_OUT" | grep block_rate | grep -oE '[0-9]+%' || echo '?')"
  pass "Claim red-team: PASS (block_rate=${BLOCK_RATE})"
else
  fail "Claim red-team: FAIL"
fi

# ── 5. SLSA subject digest binding ────────────────────────────────────────────
echo ""
echo "→ SLSA subject digest binding..."
SLSA_OUT="$(python3 scripts/slsa/compute_subject_digests.py 2>&1)"
BOUND_COUNT="$(echo "$SLSA_OUT" | grep -c '  BOUND' || echo 0)"
if [[ "${BOUND_COUNT}" -ge 4 ]]; then
  pass "SLSA subject digests: ${BOUND_COUNT}/4 BOUND"
else
  fail "SLSA subject digests: only ${BOUND_COUNT}/4 BOUND"
fi

# ── 6. LangGraph governance E2E ───────────────────────────────────────────────
echo ""
echo "→ LangGraph governance E2E (no LLM API key required)..."
if SKIP_INSTALL=1 bash integrations/langgraph/scripts/run_langgraph_demo_e2e.sh 2>&1 | tee /tmp/repro_langgraph.txt | grep -E "PASS|FAIL" | tail -5; then
  if grep -q "RESULT: PASS" /tmp/repro_langgraph.txt; then
    pass "LangGraph E2E: PASS (6/6 governance checks)"
  else
    fail "LangGraph E2E: FAIL"
  fi
else
  fail "LangGraph E2E: runner failed"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "$SEP"
echo "REPRODUCTION RUNNER SUMMARY"
echo "$SEP"
for r in "${RESULTS[@]}"; do echo "  $r"; done
echo ""
echo "  Checks passed: ${PASS_COUNT}"
echo "  Checks failed: ${FAIL_COUNT}"
echo ""

if [[ "${FAIL_COUNT}" -eq 0 ]]; then
  echo "RESULT: REPRODUCTION_SUPPORT_PASS"
  echo ""
  echo "NON-CLAIM: This result does not constitute third-party reproduction"
  echo "completion. An independent reviewer must attest this output from an"
  echo "environment with no EthicBit affiliation."
  echo "$SEP"
  exit 0
else
  echo "RESULT: REPRODUCTION_SUPPORT_FAIL (${FAIL_COUNT} check(s) failed)"
  echo "$SEP"
  exit 1
fi
