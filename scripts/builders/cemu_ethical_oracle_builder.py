#!/usr/bin/env python3
"""
CEMU Ethical Oracle Builder

Fail-closed rule:
- Only allows on-chain update when officialStatus == READY

Usage:
  ./scripts/builders/cemu_ethical_oracle_builder.py
  ./scripts/builders/cemu_ethical_oracle_builder.py --execute --contract-address 0x... --network sepolia
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_STATUS_FILE = "artifacts/history/swarm/official_operational_status.json"
DEFAULT_RECEIPT_FILE = "artifacts/swarm/anchor-receipt.swarm_mvp_v1.canonical.json"
DEFAULT_RUNNER = "scripts/builders/update_cemu_ethical_oracle.js"
DEFAULT_VERSION_TEXT = "EthicBit_CEMU_v3.7.0"

HEX_32_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


def fail(message: str, code: int = 1) -> int:
    print(f"ERROR: {message}")
    return code


def read_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(str(path))
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_bytes32(value: str) -> str:
    value = value.strip()
    if HEX_32_RE.fullmatch(value):
        return value.lower()
    raise ValueError("value is not valid bytes32 hex (0x + 64 hex chars)")


def bytes32_from_text(text: str) -> str:
    raw = text.encode("utf-8")
    if len(raw) > 32:
        raise ValueError("version tag text exceeds 32 bytes")
    padded = raw + (b"\x00" * (32 - len(raw)))
    return "0x" + padded.hex()


def root_hash_from_receipt(receipt_path: Path) -> str:
    receipt = read_json(receipt_path)
    if not isinstance(receipt, dict):
        raise ValueError("receipt file must be a JSON object")

    candidate = str(receipt.get("bundleRootHash") or "").strip()
    if candidate.startswith("sha256:"):
        digest = candidate.split(":", 1)[1].strip()
        if re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            return "0x" + digest.lower()
    if HEX_32_RE.fullmatch(candidate):
        return candidate.lower()

    raise ValueError("bundleRootHash missing or invalid in receipt")


def load_status(status_path: Path) -> tuple[str, str]:
    payload = read_json(status_path)
    if not isinstance(payload, dict):
        raise ValueError("official status file must be a JSON object")
    status = str(payload.get("officialStatus") or "UNKNOWN").strip().upper()
    reason = str(payload.get("reason") or "UNKNOWN").strip()
    return status, reason


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fail-closed builder for CEMUEthicalOracle updates")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--status-file", default=DEFAULT_STATUS_FILE, help="Path to official status JSON")
    parser.add_argument("--receipt-file", default=DEFAULT_RECEIPT_FILE, help="Path to anchor receipt JSON")
    parser.add_argument("--runner", default=DEFAULT_RUNNER, help="Hardhat runner script")
    parser.add_argument("--network", default=os.environ.get("ETH_NETWORK", "sepolia"), help="Hardhat network")
    parser.add_argument("--contract-address", default=os.environ.get("ETHICBIT_ORACLE_CONTRACT_ADDRESS", ""))
    parser.add_argument("--root-hash", default=os.environ.get("ETHICBIT_CEMU_ROOT_HASH", ""))
    parser.add_argument("--version-tag", default=os.environ.get("ETHICBIT_CEMU_VERSION_TAG", ""))
    parser.add_argument(
        "--version-tag-text",
        default=os.environ.get("ETHICBIT_CEMU_VERSION_TAG_TEXT", DEFAULT_VERSION_TEXT),
        help="Text fallback if --version-tag is not provided (encoded to bytes32)",
    )
    parser.add_argument("--execute", action="store_true", help="Execute on-chain update (default is dry-run)")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.root).resolve()

    status_path = (root / args.status_file).resolve() if not Path(args.status_file).is_absolute() else Path(args.status_file)
    receipt_path = (root / args.receipt_file).resolve() if not Path(args.receipt_file).is_absolute() else Path(args.receipt_file)
    runner_path = (root / args.runner).resolve() if not Path(args.runner).is_absolute() else Path(args.runner)

    try:
        official_status, reason = load_status(status_path)
    except Exception as exc:
        return fail(f"cannot read official status: {exc}")

    print(f"OFFICIAL_STATUS={official_status}")
    print(f"OFFICIAL_REASON={reason}")
    print(f"OFFICIAL_STATUS_PATH={status_path}")

    if official_status != "READY":
        print("ORACLE_UPDATE=BLOCKED_BY_OFFICIAL_STATUS")
        print("DETAIL=Only READY can update CEMUEthicalOracle")
        return 2

    contract_address = args.contract_address.strip()
    if not ADDR_RE.fullmatch(contract_address):
        return fail("--contract-address (or ETHICBIT_ORACLE_CONTRACT_ADDRESS) must be a valid 0x address")

    root_hash_input = args.root_hash.strip()
    if not root_hash_input:
        try:
            root_hash = root_hash_from_receipt(receipt_path)
            print(f"ROOT_HASH_SOURCE={receipt_path}")
        except Exception as exc:
            return fail(f"cannot derive root hash from receipt: {exc}")
    else:
        if root_hash_input.startswith("sha256:"):
            digest = root_hash_input.split(":", 1)[1].strip()
            if re.fullmatch(r"[0-9a-fA-F]{64}", digest):
                root_hash_input = "0x" + digest
        try:
            root_hash = normalize_bytes32(root_hash_input)
        except ValueError as exc:
            return fail(f"invalid --root-hash: {exc}")
        print("ROOT_HASH_SOURCE=CLI_OR_ENV")

    version_tag_input = args.version_tag.strip()
    if version_tag_input:
        try:
            version_tag = normalize_bytes32(version_tag_input)
            print("VERSION_TAG_SOURCE=CLI_OR_ENV_BYTES32")
        except ValueError as exc:
            return fail(f"invalid --version-tag: {exc}")
    else:
        try:
            version_tag = bytes32_from_text(args.version_tag_text)
            print("VERSION_TAG_SOURCE=TEXT_ENCODED")
        except ValueError as exc:
            return fail(f"invalid --version-tag-text: {exc}")

    if not runner_path.exists():
        return fail(f"runner not found: {runner_path}")

    print(f"NETWORK={args.network}")
    print(f"CONTRACT_ADDRESS={contract_address}")
    print(f"ROOT_HASH={root_hash}")
    print(f"VERSION_TAG={version_tag}")
    print(f"RUNNER={runner_path}")

    command = [
        "npx",
        "hardhat",
        "run",
        str(runner_path),
        "--network",
        args.network,
    ]

    if not args.execute:
        print("MODE=DRY_RUN")
        print("NEXT_COMMAND=" + " ".join(command))
        return 0

    env = os.environ.copy()
    env["ETHICBIT_ORACLE_CONTRACT_ADDRESS"] = contract_address
    env["ETHICBIT_CEMU_ROOT_HASH"] = root_hash
    env["ETHICBIT_CEMU_VERSION_TAG"] = version_tag

    print("MODE=EXECUTE")

    try:
        completed = subprocess.run(command, cwd=str(root), env=env, check=False)
    except OSError as exc:
        return fail(f"failed to launch hardhat: {exc}")

    if completed.returncode != 0:
        return fail(f"hardhat run failed with code {completed.returncode}", code=completed.returncode)

    print("ORACLE_UPDATE=SUCCESS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
