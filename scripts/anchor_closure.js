import { network } from "hardhat";
import fs from "fs";

function requireEnv(name) {
  const value = process.env[name];
  if (!value || value.includes("REEMPLAZA") || value.includes("PENDING")) {
    throw new Error(`${name} no esta configurada con un valor real`);
  }
  return value;
}

function toMetadataHash(ethers, value, label) {
  const normalized = String(value || "").trim();
  if (!normalized) {
    throw new Error(`${label} no puede estar vacio`);
  }
  return ethers.keccak256(ethers.toUtf8Bytes(normalized));
}

async function main() {
  const contractAddress = requireEnv("ETHICBIT_CONTRACT_ADDRESS");
  const rootHash = requireEnv("ETHICBIT_ROOT_HASH");
  const expectedChainId = Number(requireEnv("ETH_CHAIN_ID"));
  const expectedAccount = requireEnv("ETHICBIT_ACCOUNT_ADDRESS").toLowerCase();

  const anchorType = process.env.ETHICBIT_ANCHOR_TYPE || "DUAL_PUBLIC_ANCHOR";
  const artifactType = process.env.ETHICBIT_ARTIFACT_TYPE || "SOVEREIGN_CLOSURE";
  const version = process.env.ETHICBIT_VERSION || "3.7.0+";
  const manifestURI =
    process.env.ETHICBIT_MANIFEST_URI ||
    "artifacts/swarm/collective-pack.swarm_mvp_v1.canonical.json";
  const receiptURI =
    process.env.ETHICBIT_RECEIPT_URI ||
    "artifacts/swarm/anchor-receipt.swarm_mvp_v1.canonical.json";

  const { ethers } = await network.connect();
  const anchorTypeHash = toMetadataHash(ethers, anchorType, "ETHICBIT_ANCHOR_TYPE");
  const artifactTypeHash = toMetadataHash(ethers, artifactType, "ETHICBIT_ARTIFACT_TYPE");
  const versionHash = toMetadataHash(ethers, version, "ETHICBIT_VERSION");
  const manifestURIHash = toMetadataHash(ethers, manifestURI, "ETHICBIT_MANIFEST_URI");
  const receiptURIHash = toMetadataHash(ethers, receiptURI, "ETHICBIT_RECEIPT_URI");

  const signers = await ethers.getSigners();
  if (!signers.length) {
    throw new Error("No hay signers configurados para la red");
  }

  const deployer = signers[0];
  const deployerAddress = (await deployer.getAddress()).toLowerCase();

  if (deployerAddress !== expectedAccount) {
    throw new Error(
      `La cuenta del signer (${deployerAddress}) no coincide con ETHICBIT_ACCOUNT_ADDRESS (${expectedAccount})`
    );
  }

  const contract = await ethers.getContractAt("ClosureAnchor", contractAddress, deployer);

  const nextNonce = await contract.nextNonce();

  console.log("CONTRACT_ADDRESS=" + contractAddress);
  console.log("ROOT_HASH=" + rootHash);
  console.log("ANCHOR_TYPE_HASH=" + anchorTypeHash);
  console.log("ARTIFACT_TYPE_HASH=" + artifactTypeHash);
  console.log("VERSION_HASH=" + versionHash);
  console.log("MANIFEST_URI_HASH=" + manifestURIHash);
  console.log("RECEIPT_URI_HASH=" + receiptURIHash);
  console.log("NEXT_NONCE=" + nextNonce.toString());

  const tx = await contract.anchorClosure(
    rootHash,
    anchorTypeHash,
    artifactTypeHash,
    versionHash,
    manifestURIHash,
    receiptURIHash,
    expectedChainId,
    nextNonce
  );

  console.log("ANCHOR_TX_HASH=" + tx.hash);

  const receipt = await tx.wait();
  console.log("ANCHOR_BLOCK_NUMBER=" + receipt.blockNumber);
  console.log("ANCHOR_STATUS=" + receipt.status);

  const event = receipt.logs
    .map((log) => {
      try {
        return contract.interface.parseLog(log);
      } catch {
        return null;
      }
    })
    .find((parsed) => parsed && parsed.name === "ClosureAnchored");

  if (!event) {
    throw new Error("No se encontro el evento ClosureAnchored en el receipt");
  }

  console.log("EVENT_NAME=" + event.name);
  console.log("EVENT_ROOT_HASH=" + event.args.rootHash);
  console.log("EVENT_ANCHORER=" + event.args.anchorer);
  console.log("EVENT_ANCHOR_TYPE_HASH=" + event.args.anchorTypeHash);
  console.log("EVENT_ARTIFACT_TYPE_HASH=" + event.args.artifactTypeHash);
  console.log("EVENT_VERSION_HASH=" + event.args.versionHash);
  console.log("EVENT_MANIFEST_URI_HASH=" + event.args.manifestURIHash);
  console.log("EVENT_RECEIPT_URI_HASH=" + event.args.receiptURIHash);
  console.log("EVENT_NONCE=" + event.args.nonce.toString());
  console.log("EVENT_CHAIN_ID=" + event.args.chainId.toString());
  console.log("EVENT_BLOCK_HASH=" + event.args.blockHash);

  const output = {
    contractAddress,
    rootHash,
    anchorType,
    artifactType,
    version,
    manifestURI,
    receiptURI,
    anchorTypeHash,
    artifactTypeHash,
    versionHash,
    manifestURIHash,
    receiptURIHash,
    txHash: tx.hash,
    blockNumber: receipt.blockNumber,
    status: receipt.status,
    eventName: event.name,
    eventRootHash: event.args.rootHash,
    anchorer: event.args.anchorer,
    eventAnchorTypeHash: event.args.anchorTypeHash,
    eventArtifactTypeHash: event.args.artifactTypeHash,
    eventVersionHash: event.args.versionHash,
    eventManifestURIHash: event.args.manifestURIHash,
    eventReceiptURIHash: event.args.receiptURIHash,
    nonce: event.args.nonce.toString(),
    chainId: event.args.chainId.toString(),
    blockHash: event.args.blockHash
  };

  fs.writeFileSync(
    "artifacts/swarm/last_anchor_execution.json",
    JSON.stringify(output, null, 2)
  );

  console.log("ANCHOR_EXECUTION_RECORD=artifacts/swarm/last_anchor_execution.json");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
