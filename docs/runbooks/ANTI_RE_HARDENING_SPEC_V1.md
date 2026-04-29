# Anti-RE Hardening Spec v1

Version: 1.0  
Date: 2026-04-29  
Status: Ready for phased implementation

## 1) Purpose

Define a concrete, fail-closed hardening plan to raise the cost of reverse engineering and tampering against EthicBit/CEMU.

This spec is not "absolute prevention". It is an enforceable architecture that:

- blocks high-risk execution paths when anti-tamper conditions fail,
- avoids over-claiming trust levels when key custody is weak,
- produces auditable evidence for legal, technical, and constitutional review.

## 2) Scope

In scope:

- runtime tamper detection and fail-closed behavior,
- signing custody policy enforcement by claim level,
- immutable policy checks for strict claims,
- anti-reverse-engineering controls integrated into canonical closure reports.

Out of scope:

- DRM-style "impossible to reverse" guarantees,
- obfuscation-only security without policy enforcement,
- legal advice or jurisdiction-level patent determinations.

## 3) Threat model (practical)

Targeted adversarial actions:

- patching local JSON artifacts to forge closure status,
- forcing fallback signing modes to bypass sovereign policy,
- replaying stale snapshots or editing fingerprints,
- injecting runtime hooks/debuggers to modify process behavior,
- exfiltrating exportable keys and re-signing outside policy,
- copying architecture while bypassing fail-closed gates.

## 4) Control matrix (where / what / check / fail condition)

| ID | Where | What | Check | Fail condition |
|---|---|---|---|---|
| RE-001 | `scripts/realtime/realtime_snapshot_guard.py` | Keep snapshot integrity/freshness as strict runtime gate | Snapshot exists, age <= threshold, fingerprint matches, L5 conditions true | `guard=BLOCKED`, `constitutional_equivalence=false`, non-zero exit |
| RE-002 | `scripts/realtime/realtime_snapshot_guard.py` (new section) | Add anti-hook/anti-debug env/process checks | Detect `LD_PRELOAD`, `DYLD_INSERT_LIBRARIES`, known debugger/tracer indicators | `reason=RUNTIME_HOOK_OR_DEBUGGER_DETECTED`, block execution |
| RE-003 | `scripts/core/test_tampering_resistance.py` | Preserve 3-class tamper proof as mandatory regression | Invalid tx hash, wrong from address, wrong block all produce non-zero verifier exit | Any attack class not detected => `TAMPERING_RESISTANCE=UNPROVEN` |
| RE-004 | `scripts/core/master_closure_orchestrator.py` | Include Anti-RE stage and surface output in master report | Anti-RE stage runs and emits canonical report artifact | Stage status != PASS => `MASTER_CLOSURE_STATUS=FAIL_CLOSED` |
| RE-005 | `scripts/crypto/hybrid_sign.py` | Strict claim key-custody enforcement | For `freeze_grade`/`sovereign_release`: no ephemeral keys, trusted sources, native ML-DSA | `SystemExit` with explicit reason, signature set FAIL |
| RE-006 | `scripts/crypto/hybrid_verify.py` | Verify semantic consistency of crypto truth | Enforce claim-level constraints and required ML-DSA semantics | Verification status FAIL with semantic errors |
| RE-007 | `assurance/signers/sign_dispatch.sh` | Backend gate by claim level and policy | In strict claims, reject `github_secrets_pem` unless explicit break-glass policy | Exit non-zero with policy violation |
| RE-008 | `scripts/security/verify_key_posture.sh` | Canonical key posture artifact for release decisions | Status computed as NON_COMPLIANT / TRANSITIONAL / SOVEREIGN / PRODUCTION_HSM_READY | Strict claim + posture below threshold => fail-closed in closure path |
| RE-009 | `scripts/audit/verify_constitutional_controls.sh` | Add/upgrade constitutional Anti-RE control (CTL-RE-001) | Anti-RE artifact exists and passes required fields | MUST control fail => constitutional fail-closed |
| RE-010 | `scripts/verify_closure_integrity.sh` | Enforce Anti-RE for strict claim levels | Anti-RE artifact present and status PASS for strict claims | Missing/invalid Anti-RE artifact => fail-closed |
| RE-011 | `scripts/core/EvidenceBroker.py` + `scripts/core/RegistryManager.py` | Keep conflict/error/quorum fail-closed semantics | Quorum met, no conflicts, no provider errors in critical rules | Critical rule with broker fail => `FAIL_CLOSED` |
| RE-012 | `scripts/status/official_operational_status_calculator.py` | Publish anti-re posture in official status metadata | Include anti-re status and policy mode in output JSON | Missing anti-re status under strict claim => fail-closed |

## 5) New artifacts (canonical)

### 5.1 `results/anti_re_guard_report.json` (new)

Required minimum schema:

```json
{
  "artifactType": "anti_re_guard_report",
  "schemaVersion": "1.0.0",
  "generatedAt": "2026-04-29T00:00:00Z",
  "status": "PASS",
  "claim_level": "ci_grade",
  "policy_version": "ANTI_RE_POLICY_V1",
  "checks": {
    "snapshot_integrity": "PASS",
    "snapshot_freshness": "PASS",
    "runtime_hook_debugger": "PASS",
    "key_posture": "PASS"
  },
  "failures": []
}
```

Allowed `status` values:

- `PASS`
- `FAIL_CLOSED`
- `NOT_REQUIRED_FOR_CURRENT_CLAIM`

### 5.2 `config/anti_re_policy.v1.json` (new)

Include:

- strict claim levels,
- runtime forbidden env vars/process flags,
- key-custody thresholds per claim level,
- break-glass policy and audit marker requirements.

## 6) PR phases

## PR1 - Baseline instrumentation (safe, non-breaking)

Goal: produce Anti-RE artifact without strict blocking in `ci_grade`.

Changes:

- add `config/anti_re_policy.v1.json`,
- add `scripts/security/anti_re_guard.py` (new),
- add Anti-RE stage to `scripts/core/master_closure_orchestrator.py`,
- reference `results/anti_re_guard_report.json` in report artifact list.

Checks:

- anti-re script returns PASS locally in canonical state,
- master report includes Anti-RE stage output,
- no regression in `public-verify`.

Fail condition:

- Anti-RE stage hard-fails in `ci_grade` by default (not allowed in PR1).

## PR2 - Strict claim enforcement

Goal: enforce Anti-RE in strict claims only.

Changes:

- integrate Anti-RE checks in `scripts/verify_closure_integrity.sh`,
- add CTL-RE-001 dynamic control in `scripts/audit/verify_constitutional_controls.sh`,
- consume `results/key_posture_report.json` in strict claim path.

Checks:

- `freeze_grade` and `sovereign_release` fail when anti-re artifact missing/invalid,
- `ci_grade` remains informational unless explicitly configured stricter.

Fail condition:

- strict claim passes despite missing anti-re artifact.

## PR3 - Runtime anti-hook hardening

Goal: block execution on debugger/hook indicators.

Changes:

- extend `scripts/realtime/realtime_snapshot_guard.py` with anti-hook checks,
- emit explicit reason codes.

Checks:

- injecting forbidden env flag triggers `guard=BLOCKED`,
- no false positive in clean runtime.

Fail condition:

- hook indicator detected but guard remains OK.

## PR4 - Signing custody hardening

Goal: prevent weak custody in high claims.

Changes:

- enforce strict backend/key posture in `assurance/signers/sign_dispatch.sh`,
- tighten `scripts/crypto/hybrid_sign.py` and `scripts/crypto/hybrid_verify.py` policy assertions.

Checks:

- strict claim with ephemeral/unsupported posture fails before signature acceptance,
- remote non-exportable path passes when configured correctly.

Fail condition:

- strict claim accepted with transitional/exportable posture without break-glass evidence.

## PR5 - Official status and audit packaging

Goal: make anti-re status first-class in official outputs.

Changes:

- include anti-re fields in `scripts/status/official_operational_status_calculator.py`,
- add anti-re section in `results/GATE_REPORT.json` generation path,
- document in `docs/AUDIT.md` and mixed audience outputs.

Checks:

- official status shows anti-re posture consistently,
- reproducible verification includes anti-re checks and expected failure modes.

Fail condition:

- anti-re status absent or contradictory across official artifacts.

## 7) Hard fail rules (v1)

- For `freeze_grade` and `sovereign_release`, any Anti-RE status other than `PASS` is fail-closed.
- For strict claims, transitional key posture cannot satisfy sovereign cryptographic assertion unless explicit break-glass path is activated and auditable.
- Break-glass usage must emit mandatory artifact fields:
  - reason,
  - operator identity,
  - timestamp,
  - scope,
  - automatic expiry.

## 8) Acceptance criteria (release gate)

Minimum acceptance for v1:

- all existing L5 closure stages remain PASS in clean state,
- Anti-RE report generated and consistent,
- strict claims fail when anti-re policy is violated,
- tampering regression still proves 3/3 detections + healthy restoration,
- no private key material introduced into repository.

## 9) Implementation notes

- Prefer policy-driven checks over hardcoded condition trees.
- Keep fail reasons machine-readable and stable (`REASON_CODE` style).
- Do not leak sensitive values in logs or artifacts.
- Treat this as constitutional control surface, not only developer diagnostics.

## 10) Non-goals and realism

This hardening reduces operational and legal risk, but does not claim impossible reverse engineering prevention.
Security value comes from fail-closed policy, custody thresholds, immutable evidence, and auditable enforcement.

