/**
 * EthicBit v4.0 EV Posture — Arweave + AO triple public anchor
 *
 * Usage:
 *   ARWEAVE_WALLET=/path/to/wallet.json node scripts/core/anchor_v4_0_ev_posture_arweave_ao.mjs
 *
 * DRY_RUN=1   — builds and prints the payload without uploading
 * AO_PROCESS_ID=<id>  — override the AO process to message (default: existing EthicBit process)
 */

import fs from "fs";
import { Readable } from "stream";
import path from "path";
import crypto from "crypto";
import { fileURLToPath } from "url";
import { TurboFactory, ArweaveSigner } from "@ardrive/turbo-sdk/node";
import { connect, createDataItemSigner } from "@permaweb/aoconnect";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "../..");
const DRY_RUN = process.env.DRY_RUN === "1";
const WALLET_PATH = process.env.ARWEAVE_WALLET;
const AO_PROCESS_ID =
  process.env.AO_PROCESS_ID || "Ypj63UI-c3H6EthuVERwzxfPv4fkEwo9CGBdAnH63C4";

// ── Artifact paths (relative to ROOT) ─────────────────────────────────────────

const ARTIFACTS = {
  subject_index:       "assurance/slsa/subject-index.json",
  sbom_cyclonedx:      "assurance/sbom/aem_v1_1_sbom.cyclonedx.json",
  sbom_sig:            "assurance/sbom/aem_v1_1_sbom.cyclonedx.sig.json",
  intoto_index:        "assurance/in-toto/attestation-index.json",
  threat_model:        "assurance/threat-model/threat-model.json",
  anchor_policy:       "assurance/anchor/anchor-policy.json",
  initiation_record_v2: "assurance/v4_0/V4_0_EXTERNAL_VALIDATION_INITIATION_RECORD_V2.json",
  signing_migration_b1: "docs/assurance/SIGNING_KEY_MIGRATION_RECORD.md",
};

function sha256hex(buf) {
  return crypto.createHash("sha256").update(buf).digest("hex");
}

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

// ── Build canonical anchor document ───────────────────────────────────────────

function buildAnchorDoc() {
  const hashes = {};
  for (const [key, rel] of Object.entries(ARTIFACTS)) {
    const full = path.join(ROOT, rel);
    if (!fs.existsSync(full)) throw new Error(`Missing artifact: ${rel}`);
    hashes[key] = sha256hex(fs.readFileSync(full));
  }

  const doc = {
    schema_id: "ETHICBIT_AEM_V4_0_EV_POSTURE_TRIPLE_ANCHOR_V1",
    version: "1.0.0",
    generated_at: nowIso(),
    anchor_scope: "v4.0 External Validation posture — triple public anchor (Arweave + AO) — 2026-05-19",
    release_class: "EXTERNAL_VALIDATION",
    constitutional_dependency: "EthicBit/CEMU/v3.7.0+",
    signing_posture: "PRODUCTION_HSM_READY",
    remediation_blocks_completed: ["A", "B1", "B2", "B3", "B4", "B5", "C", "D", "E"],
    criteria_controlled_pass: 5,
    criteria_pending_external: 3,
    criteria_pending_external_list: [1, 2, 8],
    chain_anchors: {
      ethereum_mainnet: {
        status: "ONCHAIN_BLOB_ANCHOR_VERIFIED",
        block_number: 25119456,
        tx_hash: "0x6c9b5fbf032782868e1cc46ba11208a862f891b652d7630dfd3ebaecde5cb692",
        blob_versioned_hash: "0x01abb661f362d12ddd6da5aff5313f7e92a97e1807c518172e02aabf849301a1",
        timestamp_utc: "2026-05-18T03:39:59Z",
      },
      sepolia: {
        status: "ONCHAIN_BLOB_ANCHOR_VERIFIED",
        block_number: 10872023,
        tx_hash: "0x8dad6d08b9a581c50482d2224ef9fd2975b9e0986b98541904a2efbba47da2e1",
        blob_versioned_hash: "0x01f999b7d2f59a6832c972c60166d664db9e053cead83d6cd1f8f694737f9bc4",
        timestamp_utc: "2026-05-18T04:09:00Z",
      },
    },
    artifact_hashes: hashes,
    non_claim:
      "Arweave+AO tamper-evidence anchor for v4.0 External Validation posture. " +
      "Does not claim external validation pass, third-party reproduced, production-ready, " +
      "or human attestation complete. Criteria 1, 2, 8 remain PENDING_EXTERNAL.",
  };

  // Compute payload hash over the canonical JSON (sorted keys)
  const canonical = JSON.stringify(doc, Object.keys(doc).sort());
  doc.payload_sha256 = sha256hex(Buffer.from(canonical, "utf-8"));

  return doc;
}

// ── Arweave upload ─────────────────────────────────────────────────────────────

async function uploadArweave(docBuf, jwk) {
  const signer = new ArweaveSigner(jwk);
  const turbo = TurboFactory.authenticated({ signer });

  const result = await turbo.uploadFile({
    fileStreamFactory: () => {
      const r = new Readable();
      r.push(docBuf);
      r.push(null);
      return r;
    },
    fileSizeFactory: () => docBuf.length,
    dataItemOpts: {
      tags: [
        { name: "Content-Type",          value: "application/json" },
        { name: "App-Name",              value: "EthicBit_CEMU" },
        { name: "Release-Class",         value: "EXTERNAL_VALIDATION" },
        { name: "Artifact-Type",         value: "ev-posture-triple-anchor" },
        { name: "Constitutional-Dep",    value: "EthicBit/CEMU/v3.7.0+" },
        { name: "Anchor-Date",           value: "2026-05-19" },
      ],
    },
  });

  return result;
}

// ── AO message ─────────────────────────────────────────────────────────────────

async function sendAoMessage(doc, jwk) {
  const ao = connect();
  const signer = createDataItemSigner(jwk);

  const msgId = await ao.message({
    process: AO_PROCESS_ID,
    signer,
    tags: [
      { name: "Action",            value: "EV_POSTURE_ANCHOR" },
      { name: "App-Name",          value: "EthicBit_CEMU" },
      { name: "Release-Class",     value: "EXTERNAL_VALIDATION" },
      { name: "Anchor-Date",       value: "2026-05-19" },
      { name: "Payload-SHA256",    value: doc.payload_sha256 },
      { name: "Mainnet-TX",        value: doc.chain_anchors.ethereum_mainnet.tx_hash },
      { name: "Sepolia-TX",        value: doc.chain_anchors.sepolia.tx_hash },
    ],
    data: JSON.stringify({ schema_id: doc.schema_id, payload_sha256: doc.payload_sha256 }),
  });

  return msgId;
}

// ── Write receipts ─────────────────────────────────────────────────────────────

function writeReceipts(doc, arweaveTxId, aoMessageId) {
  const arweaveReceipt = {
    schema_id: "ETHICBIT_AEM_V4_0_EV_POSTURE_ARWEAVE_RECEIPT_V1",
    status: "ARWEAVE_ANCHOR_UPLOADED",
    tx_id: arweaveTxId,
    locator: `https://arweave.net/${arweaveTxId}`,
    gateway_url: `https://arweave.net/${arweaveTxId}`,
    anchor_scope: doc.anchor_scope,
    payload_sha256: doc.payload_sha256,
    generated_at: nowIso(),
    constitutional_dependency: doc.constitutional_dependency,
    non_claim: doc.non_claim,
  };

  const aoReceipt = {
    schema_id: "ETHICBIT_AEM_V4_0_EV_POSTURE_AO_RECEIPT_V1",
    status: "AO_MESSAGE_SENT",
    process_id: AO_PROCESS_ID,
    message_id: aoMessageId,
    locator: `https://www.ao.link/#/message/${aoMessageId}`,
    anchor_scope: doc.anchor_scope,
    payload_sha256: doc.payload_sha256,
    generated_at: nowIso(),
    constitutional_dependency: doc.constitutional_dependency,
    non_claim: doc.non_claim,
  };

  const assuranceDir = path.join(ROOT, "assurance/v4_0");
  fs.mkdirSync(assuranceDir, { recursive: true });
  fs.writeFileSync(
    path.join(assuranceDir, "V4_0_EV_POSTURE_ARWEAVE_ANCHOR_RECEIPT.json"),
    JSON.stringify(arweaveReceipt, null, 2),
  );
  fs.writeFileSync(
    path.join(assuranceDir, "V4_0_EV_POSTURE_AO_ANCHOR_RECEIPT.json"),
    JSON.stringify(aoReceipt, null, 2),
  );

  return { arweaveReceipt, aoReceipt };
}

// ── Main ───────────────────────────────────────────────────────────────────────

async function main() {
  console.log("=".repeat(60));
  console.log("EthicBit v4.0 EV Posture — Arweave + AO anchor");
  console.log(`Mode: ${DRY_RUN ? "DRY_RUN" : "BROADCAST"}`);
  console.log("=".repeat(60));

  const doc = buildAnchorDoc();
  const docBuf = Buffer.from(JSON.stringify(doc, null, 2), "utf-8");

  console.log(`\nAnchor document (${docBuf.length} bytes)`);
  console.log(`  payload_sha256:  ${doc.payload_sha256}`);
  console.log(`  artifact hashes: ${Object.keys(doc.artifact_hashes).length}`);
  console.log(`  chain_anchors:   mainnet(${doc.chain_anchors.ethereum_mainnet.block_number}) + sepolia(${doc.chain_anchors.sepolia.block_number})`);

  if (DRY_RUN) {
    console.log("\nDRY_RUN — payload built, no upload performed.");
    console.log(JSON.stringify(doc, null, 2).slice(0, 600) + "\n  ...");
    return;
  }

  if (!WALLET_PATH) {
    console.error("\nERR: ARWEAVE_WALLET not set.");
    console.error("  Set it to the path of your Arweave JWK wallet JSON file.");
    console.error("  Example: ARWEAVE_WALLET=~/arweave-wallet.json node scripts/core/anchor_v4_0_ev_posture_arweave_ao.mjs");
    process.exit(1);
  }

  if (!fs.existsSync(WALLET_PATH)) {
    console.error(`\nERR: Wallet file not found: ${WALLET_PATH}`);
    process.exit(1);
  }

  const jwk = JSON.parse(fs.readFileSync(WALLET_PATH, "utf-8"));
  console.log("\n→ Uploading to Arweave via Turbo...");
  const arResult = await uploadArweave(docBuf, jwk);
  const arTxId = arResult.id || arResult.dataCaches?.[0] || String(arResult);
  console.log(`  TX ID: ${arTxId}`);
  console.log(`  URL:   https://arweave.net/${arTxId}`);

  console.log("\n→ Sending AO message...");
  const aoMsgId = await sendAoMessage(doc, jwk);
  console.log(`  Message ID: ${aoMsgId}`);
  console.log(`  URL: https://www.ao.link/#/message/${aoMsgId}`);

  const { arweaveReceipt, aoReceipt } = writeReceipts(doc, arTxId, aoMsgId);

  console.log("\n→ Receipts written:");
  console.log("  assurance/v4_0/V4_0_EV_POSTURE_ARWEAVE_ANCHOR_RECEIPT.json");
  console.log("  assurance/v4_0/V4_0_EV_POSTURE_AO_ANCHOR_RECEIPT.json");

  console.log("\n" + "=".repeat(60));
  console.log("RESULT: TRIPLE ANCHOR COMPLETE");
  console.log(`  Mainnet:  block 25119456 (confirmed)`);
  console.log(`  Sepolia:  block 10872023 (confirmed)`);
  console.log(`  Arweave:  ${arTxId}`);
  console.log(`  AO:       ${aoMsgId}`);
  console.log("=".repeat(60));
}

main().catch((e) => {
  console.error("\nFATAL:", e.message || e);
  process.exit(1);
});
