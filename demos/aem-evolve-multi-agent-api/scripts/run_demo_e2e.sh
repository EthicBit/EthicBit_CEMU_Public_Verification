#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${AEM_EVOLVE_MULTI_AGENT_API_URL:-http://127.0.0.1:8000}"
THREAD_ID="${AEM_EVOLVE_THREAD_ID:-demo-thread-001}"

python3 - "$BASE_URL" "$THREAD_ID" <<'PY'
import json
import sys
import urllib.error
import urllib.request

base_url = sys.argv[1].rstrip('/')
thread_id = sys.argv[2]


def request(method, path, payload=None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(base_url + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8')
        raise SystemExit(f'HTTP_ERROR {exc.code} {path}: {body}')
    except Exception as exc:
        raise SystemExit(f'REQUEST_FAIL {method} {path}: {exc}')

health = request('GET', '/health')
assert health.get('status') == 'healthy', health
assert health.get('demo_type') == 'technical_demonstration', health
assert health.get('local_only') is True, health
assert health.get('signature_status') == 'NOT_SIGNED_DEMO', health

start = request('POST', '/start', {'thread_id': thread_id, 'initial_prompt': 'Eres un asistente general.'})
assert start.get('thread_id') == thread_id, start

status = request('GET', f'/status/{thread_id}')
assert status.get('status') == 'awaiting_human_approval', status
assert status.get('human_approval_needed') is True, status

receipt = request('GET', f'/receipt/{thread_id}')
payload = receipt.get('receipt_payload', {})
assert payload.get('outcome') == 'SCOPE_LIMITED', receipt
assert payload.get('requested_claim_scope') == 'RESEARCH_SUPPORT', receipt
assert receipt.get('signature_status') == 'NOT_SIGNED_DEMO', receipt
boundary = payload.get('claim_boundary', {})
assert boundary.get('research_support_only') is True, boundary
assert boundary.get('clinical_claimed') is False, boundary
assert boundary.get('diagnostic_claimed') is False, boundary
assert boundary.get('regulatory_approval_claimed') is False, boundary
assert boundary.get('third_party_binding') is False, boundary

_events = request('GET', f'/event/{thread_id}')
assert len(_events.get('events', [])) >= 1, _events

audit_before = request('GET', f'/audit/{thread_id}')
assert len(audit_before.get('events', [])) >= 1, audit_before
assert len(audit_before.get('receipts', [])) >= 1, audit_before

approved = request('POST', '/approve', {
    'thread_id': thread_id,
    'decision': 'approve',
    'approver_id': 'human-reviewer',
    'override_reason': 'Approved for research-support scope only.'
})
assert approved.get('status') == 'completed', approved

status_after = request('GET', f'/status/{thread_id}')
assert status_after.get('human_approval_needed') is False, status_after
assert status_after.get('approved_changes_count') >= 1, status_after

audit_after = request('GET', f'/audit/{thread_id}')
assert len(audit_after.get('human_decisions', [])) >= 1, audit_after

print('AEM_EVOLVE_MULTI_AGENT_API_DEMO_STATUS=PASS')
print('EVOLUTION_EVENT_CREATED=PASS')
print('EVOLUTION_RECEIPT_CREATED=PASS')
print('CLAIM_BOUNDARY=PASS')
print('HITL_APPROVAL_GATE=PASS')
print('AUDIT_TABLES=PASS')
print('SIGNATURE_STATUS=NOT_SIGNED_DEMO')
print('ANCHOR_STATUS=NOT_ANCHORED_FOR_THIS_DEMO')
PY
