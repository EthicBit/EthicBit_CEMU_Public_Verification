#!/usr/bin/env python3
"""Build AEM V1.1 supply-chain verification extension artifacts.

This script adds a reproducible verification support layer without mutating:
  - AEM V1.1 canonical artifact
  - Global Public Verification Registry final artifact
  - Final mainnet registry anchor receipt
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "crypto"))

from jcs_rfc8785 import canonicalize_bytes  # noqa: E402


SCHEMA_EXTENSION_MANIFEST = "ETHICBIT_AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_MANIFEST_V1"
SCHEMA_EXTENSION_RECEIPT = "ETHICBIT_AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_EXTENSION_RECEIPT_V1"
SCHEMA_TOOLCHAIN = "ETHICBIT_AEM_V1_1_TOOLCHAIN_FINGERPRINT_V1"
SCHEMA_SLSA_PROVENANCE = "ETHICBIT_AEM_V1_1_SLSA_PROVENANCE_V1"

CLAIM_LEVEL = "PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT"
NOT_CLAIMED = {
    "fully_reproducible_build": False,
    "end_to_end_deterministic_rebuild": False,
    "independent_reproducible_build_proven": False,
    "slsa_l4_fully_achieved": False,
}

REGISTRY_PATH = ROOT / "registry" / "ETHICBIT_CEMU_AEM_V1_1_GLOBAL_PUBLIC_VERIFICATION_REGISTRY.json"
REGISTRY_HASH_RECORD_PATH = (
    ROOT / "registry" / "ETHICBIT_CEMU_AEM_V1_1_GLOBAL_PUBLIC_VERIFICATION_REGISTRY_HASH_RECORD.txt"
)
REGISTRY_RECEIPT_PATH = (
    ROOT
    / "receipts"
    / "ETHICBIT_CEMU_AEM_V1_1_GLOBAL_PUBLIC_VERIFICATION_REGISTRY_MAINNET_ANCHOR_RECEIPT.json"
)

SBOM_CYCLONEDX_PATH = ROOT / "assurance" / "sbom" / "aem_v1_1_sbom.cyclonedx.json"
SBOM_SPDX_PATH = ROOT / "assurance" / "sbom" / "aem_v1_1_sbom.spdx.json"
TOOLCHAIN_PATH = ROOT / "assurance" / "toolchain" / "toolchain_fingerprint.json"
PROVENANCE_JSON_PATH = ROOT / "assurance" / "provenance" / "SLSA_PROVENANCE.json"
PROVENANCE_MD_PATH = ROOT / "assurance" / "provenance" / "AEM_V1_1_BUILD_PROVENANCE.md"

MANIFEST_JSON_PATH = (
    ROOT / "assurance" / "release" / "AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_MANIFEST.json"
)
MANIFEST_JCS_PATH = (
    ROOT / "assurance" / "release" / "AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_MANIFEST.jcs.json"
)
HASH_RECORD_PATH = (
    ROOT / "assurance" / "release" / "AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_HASH_RECORD.txt"
)

SIGNATURE_TRUTH_PATH = ROOT / "assurance" / "signatures" / "AEM_V1_1_SUPPLY_CHAIN_CRYPTO_TRUTH.json"
SIGNATURE_SET_PATH = ROOT / "assurance" / "signatures" / "AEM_V1_1_SUPPLY_CHAIN_SIGNATURE_SET.json"
SIGNATURE_VERIFY_REPORT_PATH = (
    ROOT / "assurance" / "signatures" / "AEM_V1_1_SUPPLY_CHAIN_SIGNATURE_VERIFICATION.json"
)

RECEIPT_PATH = ROOT / "receipts" / "AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_EXTENSION_RECEIPT.json"

LOCKFILE_CANDIDATES = [
    "package-lock.json",
    "requirements.txt",
    "requirements-dev.txt",
    "go.mod",
    "pyproject.toml",
]


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json_bytes(obj: dict) -> bytes:
    return canonicalize_bytes(obj)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_cmd(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(cmd, cwd=ROOT, text=True, stderr=subprocess.STDOUT, timeout=20)
        return out.strip().splitlines()[0] if out.strip() else "UNKNOWN"
    except Exception:
        return "UNAVAILABLE"


def git_output(*args: str) -> str:
    return run_cmd(["git", *args])


def parse_registry_hash_record() -> dict:
    text = REGISTRY_HASH_RECORD_PATH.read_text(encoding="utf-8")
    canonical_match = re.search(
        r"SHA-256 \(canonicalized JSON:[^)]+\):\s*([0-9a-fA-F]{64})",
        text,
        flags=re.S,
    )
    file_match = re.search(
        r"SHA-256 \(file bytes as stored in repository\):\s*([0-9a-fA-F]{64})",
        text,
        flags=re.S,
    )
    return {
        "canonical_sha256": canonical_match.group(1).lower() if canonical_match else "",
        "file_sha256": file_match.group(1).lower() if file_match else "",
    }


def registry_hashes() -> dict:
    registry_obj = read_json(REGISTRY_PATH)
    canonical = canonical_json_bytes(registry_obj)
    return {
        "canonical_sha256": sha256_bytes(canonical),
        "file_sha256": sha256_file(REGISTRY_PATH),
    }


def parse_requirements(path: Path) -> list[dict]:
    components: list[dict] = []
    if not path.exists():
        return components
    req_re = re.compile(r"^([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?\s*([<>=!~]{1,2}\s*[^; ]+)?")
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line = line.split("#", 1)[0].strip()
        m = req_re.match(line)
        if not m:
            continue
        name = m.group(1)
        spec = (m.group(2) or "").replace(" ", "")
        version = ""
        if spec.startswith("=="):
            version = spec[2:]
        components.append(
            {
                "ecosystem": "pypi",
                "name": name,
                "version": version,
                "specifier": spec,
                "source": str(path.relative_to(ROOT)),
                "purl": f"pkg:pypi/{quote(name, safe='')}" + (f"@{version}" if version else ""),
            }
        )
    return components


def parse_package_lock(path: Path) -> list[dict]:
    components: list[dict] = []
    if not path.exists():
        return components
    data = read_json(path)
    packages = data.get("packages", {})
    if isinstance(packages, dict):
        for pkg_path, meta in packages.items():
            if pkg_path == "" or not isinstance(meta, dict):
                continue
            version = str(meta.get("version") or "").strip()
            if not version:
                continue
            if "node_modules/" in pkg_path:
                name = pkg_path.split("node_modules/")[-1]
            else:
                name = pkg_path
            name = name.strip("/")
            if not name:
                continue
            license_value = str(meta.get("license") or "").strip()
            components.append(
                {
                    "ecosystem": "npm",
                    "name": name,
                    "version": version,
                    "license": license_value,
                    "source": str(path.relative_to(ROOT)),
                    "purl": f"pkg:npm/{quote(name, safe='')}@{version}",
                }
            )
    return components


def parse_go_mod(path: Path) -> list[dict]:
    components: list[dict] = []
    if not path.exists():
        return components
    in_require_block = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("require ("):
            in_require_block = True
            continue
        if in_require_block and line == ")":
            in_require_block = False
            continue
        if line.startswith("require ") and not in_require_block:
            line = line[len("require ") :].strip()
        elif in_require_block:
            line = line.split("//", 1)[0].strip()
        else:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        name, version = parts[0], parts[1]
        components.append(
            {
                "ecosystem": "golang",
                "name": name,
                "version": version,
                "source": str(path.relative_to(ROOT)),
                "purl": f"pkg:golang/{quote(name, safe='/')}@{version}",
            }
        )
    return components


def collect_components() -> list[dict]:
    all_components: list[dict] = []
    all_components.extend(parse_package_lock(ROOT / "package-lock.json"))
    all_components.extend(parse_requirements(ROOT / "requirements.txt"))
    all_components.extend(parse_requirements(ROOT / "requirements-dev.txt"))
    all_components.extend(parse_go_mod(ROOT / "go.mod"))

    dedup: dict[tuple[str, str, str, str], dict] = {}
    for comp in all_components:
        key = (
            comp.get("ecosystem", ""),
            comp.get("name", ""),
            comp.get("version", ""),
            comp.get("source", ""),
        )
        dedup[key] = comp

    ordered = sorted(
        dedup.values(),
        key=lambda x: (
            x.get("ecosystem", ""),
            x.get("name", ""),
            x.get("version", ""),
            x.get("source", ""),
        ),
    )
    return ordered


def build_cyclonedx(components: list[dict]) -> dict:
    cyclonedx_components = []
    for comp in components:
        item = {
            "type": "library",
            "name": comp["name"],
            "version": comp["version"] or "UNSPECIFIED",
            "purl": comp["purl"],
            "properties": [
                {"name": "ethicbit:ecosystem", "value": comp["ecosystem"]},
                {"name": "ethicbit:source", "value": comp["source"]},
            ],
        }
        license_value = comp.get("license", "")
        if license_value:
            item["licenses"] = [{"license": {"name": license_value}}]
        if comp.get("specifier"):
            item["properties"].append({"name": "ethicbit:specifier", "value": comp["specifier"]})
        cyclonedx_components.append(item)

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": now_utc_iso(),
            "tools": [{"vendor": "EthicBit", "name": "aem-supply-chain-extension", "version": "1.0.0"}],
            "component": {
                "type": "application",
                "name": "EthicBit_CEMU",
                "version": "AEM V1.1",
            },
        },
        "components": cyclonedx_components,
    }


def build_spdx(components: list[dict]) -> dict:
    packages = []
    relationships = []
    for i, comp in enumerate(components, start=1):
        spdx_id = f"SPDXRef-Package-{i:05d}"
        package = {
            "name": comp["name"],
            "SPDXID": spdx_id,
            "versionInfo": comp["version"] or "UNSPECIFIED",
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
            "licenseConcluded": comp.get("license") or "NOASSERTION",
            "licenseDeclared": comp.get("license") or "NOASSERTION",
            "externalRefs": [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceType": "purl",
                    "referenceLocator": comp["purl"],
                }
            ],
        }
        packages.append(package)
        relationships.append(
            {
                "spdxElementId": "SPDXRef-DOCUMENT",
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": spdx_id,
            }
        )

    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "AEM V1.1 Supply-Chain SBOM",
        "documentNamespace": f"https://ethicbit.example/spdx/aem-v1-1-supply-chain/{now_utc_iso()}",
        "creationInfo": {
            "created": now_utc_iso(),
            "creators": ["Tool: aem-supply-chain-extension-generator-1.0.0"],
        },
        "packages": packages,
        "relationships": relationships,
    }


def build_toolchain_fingerprint() -> dict:
    lockfiles = []
    for rel in LOCKFILE_CANDIDATES:
        path = ROOT / rel
        lockfiles.append(
            {
                "path": rel,
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
            }
        )

    return {
        "schema_id": SCHEMA_TOOLCHAIN,
        "status": "CAPTURED",
        "generated_at": now_utc_iso(),
        "environment": {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
        },
        "tool_versions": {
            "git": run_cmd(["git", "--version"]),
            "python3": run_cmd(["python3", "--version"]),
            "node": run_cmd(["node", "--version"]),
            "npm": run_cmd(["npm", "--version"]),
            "go": run_cmd(["go", "version"]),
            "openssl": run_cmd(["openssl", "version"]),
            "jq": run_cmd(["jq", "--version"]),
            "docker": run_cmd(["docker", "--version"]),
        },
        "lockfiles": lockfiles,
        "build_inputs": {
            "dockerfile": {
                "path": "Dockerfile.build",
                "exists": (ROOT / "Dockerfile.build").exists(),
                "sha256": sha256_file(ROOT / "Dockerfile.build")
                if (ROOT / "Dockerfile.build").exists()
                else None,
            }
        },
        "scripts_used": [
            "scripts/supply_chain/build_aem_v1_1_supply_chain_extension.py",
            "scripts/verify_release.sh",
            "scripts/verify_closure_integrity.sh",
            ".github/workflows/slsa_hybrid_attest.yml",
        ],
    }


def make_manifest(subjects: list[dict], registry_ref: dict, anchor_ref: dict) -> dict:
    return {
        "schema_id": SCHEMA_EXTENSION_MANIFEST,
        "status": CLAIM_LEVEL,
        "generated_at": now_utc_iso(),
        "extension_version": "1.0.0",
        "relationship_to_canonical": {
            "mutates_aem_v1_1_canonical": False,
            "mutates_global_registry_final": False,
            "mutates_registry_mainnet_anchor_receipt": False,
        },
        "claim_level": CLAIM_LEVEL,
        "not_claimed": NOT_CLAIMED,
        "registry_reference": registry_ref,
        "anchor_reference": anchor_ref,
        "verification_workflow": {
            "single_command_script": "scripts/verify_release.sh",
            "support_level": "public_reproducible_verification_support",
        },
        "subjects": subjects,
    }


def write_hash_record(manifest: dict, manifest_file_sha: str) -> None:
    manifest_canonical_sha = sha256_bytes(canonical_json_bytes(manifest))
    record = "\n".join(
        [
            "ETHICBIT/CEMU - AEM V1.1 Supply-Chain Verification Extension Hash Record",
            "Artifact:",
            "assurance/release/AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_MANIFEST.json",
            "Schema:",
            SCHEMA_EXTENSION_MANIFEST,
            "Purpose:",
            "Public reproducible verification support layer for AEM V1.1 supply-chain evidence.",
            "SHA-256 (canonicalized JSON: RFC8785 canonical form):",
            manifest_canonical_sha,
            "SHA-256 (file bytes as stored in repository):",
            manifest_file_sha,
            "Timestamp UTC:",
            now_utc_iso(),
            "Claim level:",
            CLAIM_LEVEL,
            "Not claimed:",
            "FULLY_REPRODUCIBLE_BUILD=false",
            "END_TO_END_DETERMINISTIC_REBUILD=false",
            "INDEPENDENT_REPRODUCIBLE_BUILD_PROVEN=false",
            "SLSA_L4_FULLY_ACHIEVED=false",
            "",
        ]
    )
    HASH_RECORD_PATH.parent.mkdir(parents=True, exist_ok=True)
    HASH_RECORD_PATH.write_text(record, encoding="utf-8")


def run_signature_pipeline(manifest_path: Path, manifest_jcs_path: Path) -> dict:
    SIGNATURE_TRUTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    truth = {
        "ed25519_key_source": "trusted_secrets",
        "mldsa_key_source": "trusted_secrets",
        "mldsa_effective_mode": "compatibility_fallback",
        "hybrid_claim_mode": "compatibility_hybrid",
        "ephemeral_keys_used": False,
        "runner_supports_mldsa": False,
        "eligible_for_sovereign_release": False,
        "signing_backend": "github_secrets_pem",
        "key_posture_status": "TRANSITIONAL_COMPLIANT",
        "break_glass_signing": False,
    }
    write_json(SIGNATURE_TRUTH_PATH, truth)

    ed_sign = "assurance/signers/ed25519_sign.sh {payload}"
    ml_sign = "assurance/signers/mldsa_sign.sh {payload}"
    ed_verify = "assurance/signers/ed25519_verify.sh {payload} {signature}"
    ml_verify = "assurance/signers/mldsa_verify.sh {payload} {signature}"

    sign_cmd = [
        "python3",
        "scripts/crypto/hybrid_sign.py",
        str(manifest_path),
        "--output",
        str(SIGNATURE_SET_PATH),
        "--ed25519-sign-cmd",
        ed_sign,
        "--mldsa-sign-cmd",
        ml_sign,
        "--crypto-truth-json",
        str(SIGNATURE_TRUTH_PATH),
        "--claim-level",
        "ci_grade",
    ]

    verify_cmd = [
        "python3",
        "scripts/crypto/hybrid_verify.py",
        "--payload",
        str(manifest_jcs_path),
        "--signature-set",
        str(SIGNATURE_SET_PATH),
        "--ed25519-verify-cmd",
        ed_verify,
        "--mldsa-verify-cmd",
        ml_verify,
    ]

    env = dict(**os.environ)
    openssl3_bin = "/opt/homebrew/opt/openssl@3/bin"
    if Path(openssl3_bin).exists():
        env["PATH"] = f"{openssl3_bin}:{env.get('PATH', '')}"

    sign_proc = subprocess.run(
        sign_cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    verify_proc = subprocess.run(
        verify_cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    report = {
        "schema_id": "ETHICBIT_AEM_V1_1_SUPPLY_CHAIN_SIGNATURE_VERIFICATION_V1",
        "generated_at": now_utc_iso(),
        "sign_command": sign_cmd,
        "verify_command": verify_cmd,
        "sign_return_code": sign_proc.returncode,
        "verify_return_code": verify_proc.returncode,
        "status": "PASS" if sign_proc.returncode == 0 and verify_proc.returncode == 0 else "FAIL",
        "sign_stdout_tail": (sign_proc.stdout or "")[-4000:],
        "sign_stderr_tail": (sign_proc.stderr or "")[-4000:],
        "verify_stdout_tail": (verify_proc.stdout or "")[-4000:],
        "verify_stderr_tail": (verify_proc.stderr or "")[-4000:],
        "signature_set_path": str(SIGNATURE_SET_PATH.relative_to(ROOT)),
    }
    write_json(SIGNATURE_VERIFY_REPORT_PATH, report)
    return report


def write_slsa_provenance(subjects: list[dict], registry_ref: dict, anchor_ref: dict) -> None:
    provenance = {
        "schema_id": SCHEMA_SLSA_PROVENANCE,
        "status": CLAIM_LEVEL,
        "generated_at": now_utc_iso(),
        "buildType": "https://slsa.dev/provenance/v1",
        "builder": {
            "id": "https://github.com/EthicBit/EthicBit_CEMU",
            "tool": "scripts/supply_chain/build_aem_v1_1_supply_chain_extension.py",
        },
        "invocation": {
            "source_uri": git_output("config", "--get", "remote.origin.url"),
            "source_ref": git_output("rev-parse", "HEAD"),
            "branch": git_output("branch", "--show-current"),
        },
        "subjects": subjects,
        "upstream_references": {
            "registry_canonical_sha256": registry_ref["canonical_sha256"],
            "registry_mainnet_anchor_tx": anchor_ref["tx_hash"],
            "registry_mainnet_anchor_block": anchor_ref["block_number"],
        },
        "claim_boundaries": {
            "claim_level": CLAIM_LEVEL,
            "not_claimed": NOT_CLAIMED,
            "third_party_binding": False,
        },
    }
    write_json(PROVENANCE_JSON_PATH, provenance)

    lines = [
        "# AEM V1.1 Build Provenance (Supply-Chain Verification Extension)",
        "",
        f"Generated at: {provenance['generated_at']}",
        f"Schema: {SCHEMA_SLSA_PROVENANCE}",
        f"Status: {CLAIM_LEVEL}",
        "",
        "## Scope",
        "This provenance file supports public reproducible verification support.",
        "It does not claim fully reproducible build or deterministic end-to-end rebuild.",
        "",
        "## Source",
        f"- Remote: `{provenance['invocation']['source_uri']}`",
        f"- Commit: `{provenance['invocation']['source_ref']}`",
        f"- Branch: `{provenance['invocation']['branch']}`",
        "",
        "## Registry and Anchor References",
        f"- Registry canonical SHA-256: `{registry_ref['canonical_sha256']}`",
        f"- Registry mainnet anchor TX: `{anchor_ref['tx_hash']}`",
        f"- Registry mainnet anchor block: `{anchor_ref['block_number']}`",
        "",
        "## Subjects",
    ]
    for subject in subjects:
        lines.append(f"- `{subject['path']}`: `{subject['sha256']}`")
    lines.extend(
        [
            "",
            "## Boundaries",
            "- third_party_binding=false",
            "- patent_grant_claimed=false",
            "- uspto_approval_claimed=false",
            "- regulatory_approval_claimed=false",
            "",
        ]
    )
    PROVENANCE_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def build_receipt(
    manifest: dict,
    registry_ref: dict,
    anchor_ref: dict,
    signature_report: dict,
) -> dict:
    master_closure = read_json(ROOT / "results" / "master_closure_report.json")
    closure_summary = master_closure.get("summary", {})
    constitutional = read_json(ROOT / "results" / "constitutional_controls_report.json")
    constitutional_summary = constitutional.get("summary", {})

    receipt_status = "PASS" if signature_report.get("status") == "PASS" else "PARTIAL_PASS_UNSIGNED"
    return {
        "schema_id": SCHEMA_EXTENSION_RECEIPT,
        "generated_at": now_utc_iso(),
        "status": receipt_status,
        "extension_name": "AEM V1.1 Supply-Chain Verification Extension",
        "claim_level": CLAIM_LEVEL,
        "not_claimed": NOT_CLAIMED,
        "preserves_canonical_boundaries": True,
        "registry_reference": registry_ref,
        "anchor_reference": anchor_ref,
        "manifest": {
            "path": str(MANIFEST_JSON_PATH.relative_to(ROOT)),
            "sha256": sha256_file(MANIFEST_JSON_PATH),
            "canonical_sha256": sha256_bytes(canonical_json_bytes(manifest)),
            "jcs_path": str(MANIFEST_JCS_PATH.relative_to(ROOT)),
            "jcs_sha256": sha256_file(MANIFEST_JCS_PATH),
        },
        "signature_verification": {
            "status": signature_report.get("status"),
            "report_path": str(SIGNATURE_VERIFY_REPORT_PATH.relative_to(ROOT)),
            "signature_set_path": str(SIGNATURE_SET_PATH.relative_to(ROOT)),
        },
        "closure_snapshot": {
            "master_closure_status": master_closure.get("status"),
            "claim_level_ceiling": closure_summary.get("claim_level_ceiling"),
            "constitutional_status": closure_summary.get("constitutional_status"),
            "anti_re_status": closure_summary.get("anti_re_status"),
            "presentation_scope": closure_summary.get("third_party_presentability"),
            "third_party_binding": closure_summary.get("third_party_binding"),
            "constitutional_total": constitutional_summary.get("total"),
            "constitutional_passed": constitutional_summary.get("passed"),
            "constitutional_failed": constitutional_summary.get("failed"),
            "constitutional_must_failed": constitutional_summary.get("mustFailed"),
        },
    }


def main() -> int:
    if not REGISTRY_PATH.exists() or not REGISTRY_RECEIPT_PATH.exists() or not REGISTRY_HASH_RECORD_PATH.exists():
        raise SystemExit("missing registry inputs required for supply-chain extension")

    components = collect_components()
    cyclonedx = build_cyclonedx(components)
    spdx = build_spdx(components)
    write_json(SBOM_CYCLONEDX_PATH, cyclonedx)
    write_json(SBOM_SPDX_PATH, spdx)

    toolchain = build_toolchain_fingerprint()
    write_json(TOOLCHAIN_PATH, toolchain)

    registry_receipt = read_json(REGISTRY_RECEIPT_PATH)
    registry_record = parse_registry_hash_record()
    registry_runtime = registry_hashes()
    registry_ref = {
        "registry_path": str(REGISTRY_PATH.relative_to(ROOT)),
        "canonical_sha256": registry_runtime["canonical_sha256"],
        "file_sha256": registry_runtime["file_sha256"],
        "expected_canonical_sha256": registry_record["canonical_sha256"],
        "canonicalization": "json_sort_keys_no_whitespace_utf8",
    }
    anchor_ref = {
        "tx_hash": registry_receipt.get("tx_hash"),
        "block_number": registry_receipt.get("block_number"),
        "network": registry_receipt.get("network"),
        "chain_id": registry_receipt.get("chain_id"),
        "status": registry_receipt.get("status"),
    }

    subjects = []
    tracked_subject_paths = [
        SBOM_CYCLONEDX_PATH,
        SBOM_SPDX_PATH,
        TOOLCHAIN_PATH,
        PROVENANCE_JSON_PATH,
        PROVENANCE_MD_PATH,
    ]

    write_slsa_provenance([], registry_ref, anchor_ref)
    for path in tracked_subject_paths:
        if path.exists():
            subjects.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "sha256": sha256_file(path),
                    "kind": "supply_chain_extension_artifact",
                }
            )

    manifest = make_manifest(subjects, registry_ref, anchor_ref)
    write_json(MANIFEST_JSON_PATH, manifest)
    MANIFEST_JCS_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_JCS_PATH.write_bytes(canonical_json_bytes(manifest))

    write_hash_record(manifest, sha256_file(MANIFEST_JSON_PATH))

    signature_report = run_signature_pipeline(MANIFEST_JSON_PATH, MANIFEST_JCS_PATH)

    receipt = build_receipt(manifest, registry_ref, anchor_ref, signature_report)
    write_json(RECEIPT_PATH, receipt)

    print("AEM V1.1 supply-chain extension artifacts generated:")
    for p in [
        SBOM_CYCLONEDX_PATH,
        SBOM_SPDX_PATH,
        TOOLCHAIN_PATH,
        PROVENANCE_JSON_PATH,
        PROVENANCE_MD_PATH,
        MANIFEST_JSON_PATH,
        MANIFEST_JCS_PATH,
        HASH_RECORD_PATH,
        SIGNATURE_TRUTH_PATH,
        SIGNATURE_SET_PATH,
        SIGNATURE_VERIFY_REPORT_PATH,
        RECEIPT_PATH,
    ]:
        if p.exists():
            print(f"- {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
