import json
import time
import re
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parents[2]
TIMEOUT = 8
MIN_REAL_PROVIDERS = 2

def get_github_owner_repo():
    remote = subprocess.check_output(
        ["git", "remote", "get-url", "origin"],
        text=True
    ).strip()
    m = re.search(r'github\.com[:/](.+?)/(.+?)(?:\.git)?$', remote)
    if not m:
        raise RuntimeError(f"Cannot parse GitHub owner/repo from origin: {remote}")
    return m.group(1), m.group(2)

OWNER, REPO = get_github_owner_repo()
BRANCH = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip() or "main"

TARGETS = {
    "constitutional_controls": "config/constitutional_controls.v1.json",
    "attestation_status": "artifacts/history/swarm/attestation_status.canonical.json",
    "readiness_cert": "artifacts/production_distributed_readiness_certificate_final.json",
}

PROVIDERS = {}
for key, rel in TARGETS.items():
    PROVIDERS[f"raw_{key}"] = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/{rel}"
    PROVIDERS[f"github_blob_{key}"] = f"https://github.com/{OWNER}/{REPO}/blob/{BRANCH}/{rel}"
    PROVIDERS[f"jsdelivr_{key}"] = f"https://cdn.jsdelivr.net/gh/{OWNER}/{REPO}@{BRANCH}/{rel}"

def fetch(url):
    started = time.time()
    req = Request(url, headers={"User-Agent": "EthicBit-L4-Candidate-Gate/1.0"})
    with urlopen(req, timeout=TIMEOUT) as resp:
        body = resp.read()
        elapsed = round(time.time() - started, 3)
        return {
            "ok": True,
            "status_code": getattr(resp, "status", 200),
            "bytes": len(body),
            "elapsed_seconds": elapsed,
            "sha256": __import__("hashlib").sha256(body).hexdigest(),
        }

def try_provider(name, url):
    try:
        meta = fetch(url)
        meta["provider"] = name
        meta["url"] = url
        meta["source_type"] = "REAL_EXTERNAL"
        return meta
    except HTTPError as e:
        return {"ok": False, "provider": name, "url": url, "source_type": "REAL_EXTERNAL", "error_type": "HTTPError", "error": str(e)}
    except URLError as e:
        return {"ok": False, "provider": name, "url": url, "source_type": "REAL_EXTERNAL", "error_type": "URLError", "error": str(e)}
    except Exception as e:
        return {"ok": False, "provider": name, "url": url, "source_type": "REAL_EXTERNAL", "error_type": type(e).__name__, "error": str(e)}

provider_results = []
real_success = []

for name, url in PROVIDERS.items():
    result = try_provider(name, url)
    provider_results.append(result)
    if result.get("ok"):
        real_success.append(result["provider"])

status = "PASS" if len(real_success) >= MIN_REAL_PROVIDERS else "FAIL_CLOSED"
claim_level_ceiling = "L4_CANDIDATE" if status == "PASS" else "L3_CANDIDATE"

reasons = []
if status != "PASS":
    reasons.append("REAL_EXTERNAL_QUORUM_NOT_REACHED")
if len(real_success) == 0:
    reasons.append("NO_REAL_EXTERNAL_PROVIDER_RESPONDED")
elif len(real_success) == 1:
    reasons.append("ONLY_ONE_REAL_EXTERNAL_PROVIDER_RESPONDED")
else:
    reasons.append("REAL_EXTERNAL_QUORUM_REACHED")

out = {
    "schema_id": "ETHICBIT_REAL_EXTERNAL_L4_CANDIDATE_GATE_V1",
    "status": status,
    "mode": "REAL_EXTERNAL_STRICT",
    "owner": OWNER,
    "repo": REPO,
    "branch": BRANCH,
    "minimum_real_providers_required": MIN_REAL_PROVIDERS,
    "real_providers_responded": len(real_success),
    "real_provider_ids": real_success,
    "provider_results": provider_results,
    "claim_level_ceiling": claim_level_ceiling,
    "eligible_for_l4": status == "PASS",
    "eligible_for_l5": False,
    "reasons": reasons,
}

out_path = ROOT / "results" / "real_external_l4_candidate_gate.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"wrote {out_path}")
print(f"status={status}")
print(f"real_providers_responded={len(real_success)}")
print(f"claim_level_ceiling={claim_level_ceiling}")
