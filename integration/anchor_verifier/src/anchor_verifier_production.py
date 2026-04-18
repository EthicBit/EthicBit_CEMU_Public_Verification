#!/usr/bin/env python3
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
CONFIG_PATH = os.path.join(SCRIPT_DIR, '..', 'anchor_txids_real.json')
RECEIPT_PATH = os.path.join(BASE_DIR, 'artifacts', 'swarm', 'anchor-receipt.swarm_mvp_v1.canonical.json')
SNAPSHOT_PATH = os.path.join(SCRIPT_DIR, 'arweave_anchor_receipt.json')
REPORT_PATH = os.path.join(BASE_DIR, 'artifacts', 'history', 'swarm', 'triple_public_anchor_live_verification.json')
PACKAGE_MANIFEST_PATH = os.path.join(BASE_DIR, 'PACKAGE_MANIFEST.json')
PUBLICATION_STATE_PATH = os.path.join(BASE_DIR, 'publication', 'publication_state.json')

POLICY_VERSION = 'triple-public-anchor-live-policy.v1.0.0'

PLACEHOLDER_RE = re.compile(r'PENDING_|PON_AQUI|TODO|REPLACE_ME', re.IGNORECASE)
ERROR_TEXT_RE = re.compile(r'not found|unable to locate process|process scheduler not found|upstream timeout|\\berror\\b', re.IGNORECASE)
HEX64_RE = re.compile(r'^0x[0-9a-fA-F]{64}$')


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_optional_json(path):
    if not os.path.exists(path):
        return {}
    try:
        return load_json(path)
    except Exception:
        return {}


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def fetch_url(url, timeout=30, method='GET', body=None, headers=None):
    req = urllib.request.Request(url=url, method=method)
    req.add_header('User-Agent', 'EthicBit-CEMU-AnchorVerifier/1.0')
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)
    raw_body = None
    status = None
    content_type = ''
    error = ''

    try:
        with urllib.request.urlopen(req, data=body, timeout=timeout) as resp:
            status = getattr(resp, 'status', None) or resp.getcode()
            content_type = resp.headers.get('Content-Type', '')
            raw = resp.read()
            raw_body = raw.decode('utf-8', errors='replace')
    except urllib.error.HTTPError as exc:
        status = exc.code
        content_type = exc.headers.get('Content-Type', '') if exc.headers else ''
        try:
            raw_body = exc.read().decode('utf-8', errors='replace')
        except Exception:
            raw_body = ''
        error = f'HTTPError:{exc.code}'
    except Exception as exc:
        raw_body = ''
        error = str(exc)

    return {
        'status': status if status is not None else 0,
        'contentType': content_type,
        'body': raw_body or '',
        'error': error,
    }


def classify_body(text):
    if not text:
        return 'EMPTY'
    lowered = text.lower()
    if '<html' in lowered:
        return 'HTML'
    if ERROR_TEXT_RE.search(text):
        return 'ERROR_TEXT'
    return 'TEXT'


def json_parse_ok(text):
    try:
        json.loads(text)
        return True
    except Exception:
        return False


def first_locator(locators, locator_type):
    for item in locators:
        if item.get('type') == locator_type:
            return item
    return {}


def build_run_context(package_manifest, publication_state):
    generated_at = now_utc_iso()
    generated_token = re.sub(r'[^0-9A-Za-z]', '', generated_at)

    run_id = os.environ.get('ETHICBIT_RUN_ID') or f'run-{generated_token}-{os.getpid()}'
    release_id = (
        os.environ.get('ETHICBIT_RELEASE_ID')
        or package_manifest.get('packageId')
        or publication_state.get('activeTarget')
        or 'UNKNOWN_RELEASE'
    )
    verification_epoch = (
        os.environ.get('ETHICBIT_VERIFICATION_EPOCH')
        or f"{generated_at[:13]}:00:00Z"
    )

    return {
        'runId': run_id,
        'releaseId': release_id,
        'verificationEpoch': verification_epoch,
        'generatedAt': generated_at,
    }


def verify_sepolia_live(blockchain_locator, rpc_candidates):
    tx_hash = blockchain_locator.get('transactionHash', '')
    contract = str(blockchain_locator.get('contractAddress', '')).lower()
    block_hash = str(blockchain_locator.get('blockHash', '')).lower()

    tx_hash_format_ok = bool(HEX64_RE.match(tx_hash))
    live_ok = False
    selected_rpc = ''
    live_note = 'No RPC responded with matching transaction data.'

    payload = json.dumps({
        'jsonrpc': '2.0',
        'method': 'eth_getTransactionByHash',
        'params': [tx_hash],
        'id': 1,
    }).encode('utf-8')

    for rpc in rpc_candidates:
        resp = fetch_url(
            rpc,
            method='POST',
            body=payload,
            headers={'Content-Type': 'application/json'},
        )
        if resp['status'] < 200 or resp['status'] >= 300:
            continue
        try:
            parsed = json.loads(resp['body'])
        except Exception:
            continue

        result = parsed.get('result') or {}
        if not isinstance(result, dict) or not result:
            continue

        rpc_hash = str(result.get('hash', '')).lower()
        rpc_to = str(result.get('to', '')).lower()
        rpc_block_hash = str(result.get('blockHash', '')).lower()

        hash_match = rpc_hash == tx_hash.lower()
        contract_match = (not contract) or (rpc_to == contract)
        block_match = (not block_hash) or (rpc_block_hash == block_hash)

        if hash_match and contract_match and block_match:
            live_ok = True
            selected_rpc = rpc
            live_note = 'Sepolia transaction resolved and matched locator fields.'
            break

    if not tx_hash_format_ok:
        substatus = 'INVALID_INPUT'
        reason_code = 'SEPOLIA_TX_HASH_INVALID'
    elif live_ok:
        substatus = 'CONVERGED'
        reason_code = 'SEPOLIA_TX_RESOLVED'
    else:
        substatus = 'RESOLUTION_FAILED'
        reason_code = 'SEPOLIA_TX_NOT_RESOLVED'

    return {
        'txHashFormat': 'PASS' if tx_hash_format_ok else 'FAIL',
        'liveResolved': 'PASS' if live_ok else 'FAIL',
        'selectedRpc': selected_rpc,
        'note': live_note,
        'substatus': substatus,
        'reasonCode': reason_code,
    }


def verify_arweave_live(ar_locator):
    tx_id = ar_locator.get('txId', '')
    locator = ar_locator.get('locator', '')

    meta_resp = fetch_url(f'https://arweave.net/tx/{tx_id}')
    body_resp = fetch_url(locator)

    meta_tx_match = False
    meta_data_nonzero = False
    meta_data_size = '0'
    try:
        meta_json = json.loads(meta_resp['body'])
        meta_tx_match = meta_json.get('id') == tx_id
        meta_data_size = str(meta_json.get('data_size', '0'))
        meta_data_nonzero = meta_data_size != '0'
    except Exception:
        pass

    body = body_resp['body']
    body_nonempty = bool(body)
    body_is_html = '<html' in body.lower()
    body_json_ok = json_parse_ok(body)
    body_has_placeholders = bool(PLACEHOLDER_RE.search(body)) if body_nonempty else True

    resolved = all([
        meta_tx_match,
        meta_data_nonzero,
        body_nonempty,
        not body_is_html,
        body_json_ok,
        not body_has_placeholders,
    ])

    if meta_resp['status'] == 0:
        substatus = 'RESOLUTION_FAILED'
        reason_code = 'ARWEAVE_META_UNREACHABLE'
    elif not meta_tx_match:
        substatus = 'HASH_MISMATCH'
        reason_code = 'ARWEAVE_META_TX_MISMATCH'
    elif not meta_data_nonzero:
        substatus = 'CONTENT_UNAVAILABLE'
        reason_code = 'ARWEAVE_DATA_SIZE_ZERO'
    elif not body_nonempty:
        substatus = 'CONTENT_UNAVAILABLE'
        reason_code = 'ARWEAVE_BODY_EMPTY'
    elif body_is_html:
        substatus = 'REACHABLE_BUT_MISMATCH'
        reason_code = 'ARWEAVE_BODY_HTML'
    elif not body_json_ok:
        substatus = 'CONTENT_INVALID'
        reason_code = 'ARWEAVE_BODY_NOT_JSON'
    elif body_has_placeholders:
        substatus = 'CONTENT_INVALID'
        reason_code = 'ARWEAVE_BODY_HAS_PLACEHOLDERS'
    else:
        substatus = 'CONVERGED'
        reason_code = 'ARWEAVE_OBJECT_CONVERGED'

    return {
        'metaTxMatch': 'PASS' if meta_tx_match else 'FAIL',
        'metaDataSizeNonZero': 'PASS' if meta_data_nonzero else 'FAIL',
        'bodyNonEmpty': 'PASS' if body_nonempty else 'FAIL',
        'bodyIsJson': 'PASS' if body_json_ok else 'FAIL',
        'bodyIsNotHtml': 'PASS' if not body_is_html else 'FAIL',
        'bodyNoPlaceholders': 'PASS' if not body_has_placeholders else 'FAIL',
        'resolved': 'PASS' if resolved else 'FAIL',
        'note': 'Arweave content must be JSON and placeholder-free to pass live verification.',
        'selectedLocator': locator,
        'metaHttp': meta_resp['status'],
        'bodyHttp': body_resp['status'],
        'metaDataSize': meta_data_size,
        'substatus': substatus,
        'reasonCode': reason_code,
    }


def verify_ao_live(ao_locator):
    process_id = ao_locator.get('processId', '')
    message_id = ao_locator.get('messageId', '')
    primary = ao_locator.get('locator', '')

    candidates = [
        primary,
        f'https://su-router.ao-testnet.xyz/{message_id}?process-id={process_id}',
        f'https://cu.ao-testnet.xyz/result/{message_id}?process-id={process_id}',
    ]

    selected = ''
    selected_http = 0
    selected_class = 'EMPTY'
    resolved = False
    selected_error = ''
    probed = []

    for candidate in candidates:
        if not candidate:
            continue
        resp = fetch_url(candidate)
        body_class = classify_body(resp['body'])

        selected = candidate
        selected_http = resp['status']
        selected_class = body_class
        selected_error = resp['error']

        probed.append({
            'locator': candidate,
            'http': resp['status'],
            'bodyClass': body_class,
            'error': resp['error'],
        })

        if 200 <= resp['status'] < 300 and body_class == 'TEXT':
            resolved = True
            break

    note = 'AO endpoint did not return a valid non-HTML payload.'
    if resolved:
        note = 'AO endpoint resolved with non-HTML payload.'

    if resolved:
        substatus = 'CONVERGED'
        reason_code = 'AO_PAYLOAD_RESOLVED'
    elif selected_http == 404:
        substatus = 'RESOLUTION_FAILED'
        reason_code = 'AO_HTTP_404'
    elif selected_http == 0:
        substatus = 'RESOLUTION_FAILED'
        reason_code = 'AO_TRANSPORT_ERROR'
    elif selected_class == 'EMPTY':
        substatus = 'CONTENT_UNAVAILABLE'
        reason_code = 'AO_EMPTY_PAYLOAD'
    elif selected_class == 'HTML':
        substatus = 'REACHABLE_BUT_MISMATCH'
        reason_code = 'AO_HTML_PAYLOAD'
    elif selected_class == 'ERROR_TEXT':
        substatus = 'REACHABLE_BUT_MISMATCH'
        reason_code = 'AO_ERROR_PAYLOAD'
    else:
        substatus = 'REACHABLE_BUT_MISMATCH'
        reason_code = 'AO_UNRESOLVED'

    return {
        'resolved': 'PASS' if resolved else 'FAIL',
        'selectedLocator': selected,
        'selectedHttp': selected_http,
        'selectedBodyClass': selected_class,
        'selectedError': selected_error,
        'probedCandidates': probed,
        'note': note,
        'substatus': substatus,
        'reasonCode': reason_code,
    }


def main():
    print('=== EthicBit_CEMU Triple Public Anchor Verifier - LIVE ===')
    print(f'BASE_DIR={BASE_DIR}')
    print(f'RECEIPT_PATH={RECEIPT_PATH}')

    if not os.path.exists(RECEIPT_PATH):
        print('RECEIPT_PATH_MISSING=FAIL')
        return 1

    receipt = load_json(RECEIPT_PATH)
    config = load_json(CONFIG_PATH) if os.path.exists(CONFIG_PATH) else {}
    package_manifest = load_optional_json(PACKAGE_MANIFEST_PATH)
    publication_state = load_optional_json(PUBLICATION_STATE_PATH)

    run_context = build_run_context(package_manifest, publication_state)

    save_json(SNAPSHOT_PATH, receipt)

    freeze_date = config.get('freezeDate', 'UNKNOWN')
    root_hash = config.get('rootHash', 'UNKNOWN')
    support_type = receipt.get('supportType', '')
    verification_status = receipt.get('verificationStatus', '')
    canonical_model = config.get('canonicalAnchorModel') or config.get('canonicalModel', 'TRIPLE_PUBLIC_ANCHOR')

    print(f'Freeze Date: {freeze_date}')
    if root_hash != 'UNKNOWN' and len(root_hash) > 24:
        print(f'Root hash: {root_hash[:16]}...{root_hash[-8:]}')
    else:
        print(f'Root hash: {root_hash}')

    print(f'SUPPORT_TYPE={support_type}')
    print(f'VERIFICATION_STATUS={verification_status}')
    print(f'CANONICAL_ANCHOR_MODEL={canonical_model}')
    print(f'RUN_ID={run_context["runId"]}')
    print(f'RELEASE_ID={run_context["releaseId"]}')
    print(f'VERIFICATION_EPOCH={run_context["verificationEpoch"]}')

    locators = receipt.get('locators', [])
    blockchain = first_locator(locators, 'BLOCKCHAIN_ANCHOR')
    arweave = first_locator(locators, 'ARWEAVE_OBJECT')
    ao = first_locator(locators, 'AO_PROCESS')

    rpc_candidates = [
        config.get('endpoints', {}).get('sepoliaRpc', ''),
        'https://ethereum-sepolia-rpc.publicnode.com',
        'https://rpc.sepolia.org',
    ]
    rpc_candidates = [x for x in rpc_candidates if x]

    sepolia = verify_sepolia_live(blockchain, rpc_candidates)
    arweave_result = verify_arweave_live(arweave)
    ao_result = verify_ao_live(ao)

    support_ok = support_type == 'TRIPLE_PUBLIC_ANCHOR'
    canonical_ok = canonical_model == 'TRIPLE_PUBLIC_ANCHOR'

    print(f'SUPPORT_TYPE_CANONICAL={"PASS" if support_ok else "FAIL"}')
    print(f'CANONICAL_MODEL_DECLARED={"PASS" if canonical_ok else "FAIL"}')

    print(f'SEPOLIA_ANCHOR_FORMAT={sepolia["txHashFormat"]}')
    print(f'SEPOLIA_ANCHOR_RESOLVED={sepolia["liveResolved"]}')
    print(f'SEPOLIA_REASON_CODE={sepolia["reasonCode"]}')

    print(f'ARWEAVE_META_TX_MATCH={arweave_result["metaTxMatch"]}')
    print(f'ARWEAVE_META_DATA_SIZE_NONZERO={arweave_result["metaDataSizeNonZero"]}')
    print(f'ARWEAVE_BODY_JSON={arweave_result["bodyIsJson"]}')
    print(f'ARWEAVE_BODY_NO_PLACEHOLDERS={arweave_result["bodyNoPlaceholders"]}')
    print(f'ARWEAVE_OBJECT_RESOLVED={arweave_result["resolved"]}')
    print(f'ARWEAVE_REASON_CODE={arweave_result["reasonCode"]}')

    print(f'AO_PROCESS_RESOLVED={ao_result["resolved"]}')
    print(f'AO_SELECTED_LOCATOR={ao_result["selectedLocator"] or "NONE"}')
    print(f'AO_SELECTED_HTTP={ao_result["selectedHttp"]}')
    print(f'AO_SELECTED_BODY_CLASS={ao_result["selectedBodyClass"]}')
    print(f'AO_REASON_CODE={ao_result["reasonCode"]}')

    all_live_ok = all([
        support_ok,
        canonical_ok,
        sepolia['txHashFormat'] == 'PASS',
        sepolia['liveResolved'] == 'PASS',
        arweave_result['resolved'] == 'PASS',
        ao_result['resolved'] == 'PASS',
    ])

    print()
    print('===== STATUS SUMMARY =====')
    print('ACTIVE_CANONICAL')
    print('EXTERNAL_ANCHOR_EVIDENCE_READY_FOR_INDEPENDENT_REVERIFICATION')
    print(f'NO_UNRESOLVED_ANCHOR_CONFLICTS={"PASS" if all_live_ok else "FAIL_VISIBLE"}')
    print(f'ANCHOR_HARDENING_ENABLED={"PASS_LIVE" if all_live_ok else "FAIL_LIVE"}')

    report = {
        'artifact': 'triple_public_anchor_live_verification',
        'generatedAt': run_context['generatedAt'],
        'policyVersion': POLICY_VERSION,
        'runContext': {
            'runId': run_context['runId'],
            'releaseId': run_context['releaseId'],
            'verificationEpoch': run_context['verificationEpoch'],
        },
        'supportType': support_type,
        'verificationStatus': verification_status,
        'canonicalAnchorModel': canonical_model,
        'checks': {
            'supportTypeCanonical': 'PASS' if support_ok else 'FAIL',
            'canonicalModelDeclared': 'PASS' if canonical_ok else 'FAIL',
            'sepolia': sepolia,
            'arweave': arweave_result,
            'ao': ao_result,
            'noUnresolvedAnchorConflicts': 'PASS' if all_live_ok else 'FAIL_VISIBLE',
        },
        'anchors': {
            'sepolia': {
                'status': sepolia['liveResolved'],
                'substatus': sepolia['substatus'],
                'reasonCode': sepolia['reasonCode'],
            },
            'arweave': {
                'status': arweave_result['resolved'],
                'substatus': arweave_result['substatus'],
                'reasonCode': arweave_result['reasonCode'],
            },
            'ao': {
                'status': ao_result['resolved'],
                'substatus': ao_result['substatus'],
                'reasonCode': ao_result['reasonCode'],
            },
        },
        'result': 'PASS' if all_live_ok else 'FAIL',
    }
    save_json(REPORT_PATH, report)
    print(f'LIVE_REPORT_PATH={REPORT_PATH}')

    return 0 if all_live_ok else 1


if __name__ == '__main__':
    sys.exit(main())
