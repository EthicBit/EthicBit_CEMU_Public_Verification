import { network } from "hardhat";

function requireEnv(name) {
  const value = process.env[name];
  if (!value || value.includes("REEMPLAZA") || value.includes("PENDING")) {
    throw new Error(`${name} is required`);
  }
  return value;
}

function requireBytes32(name) {
  const value = requireEnv(name);
  if (!/^0x[0-9a-fA-F]{64}$/.test(value)) {
    throw new Error(`${name} must be bytes32 hex (0x + 64 hex chars)`);
  }
  return value;
}

async function main() {
  const contractAddress = requireEnv("ETHICBIT_ORACLE_CONTRACT_ADDRESS");
  const rootHash = requireBytes32("ETHICBIT_CEMU_ROOT_HASH");
  const versionTag = requireBytes32("ETHICBIT_CEMU_VERSION_TAG");

  const { ethers } = await network.connect();

  const signers = await ethers.getSigners();
  if (!signers.length) {
    throw new Error("No signer configured");
  }

  const operator = signers[0];
  const operatorAddress = await operator.getAddress();

  const contract = await ethers.getContractAt("CEMUEthicalOracle", contractAddress, operator);

  console.log("ORACLE_CONTRACT=" + contractAddress);
  console.log("OPERATOR=" + operatorAddress);
  console.log("NEW_ROOT_HASH=" + rootHash);
  console.log("VERSION_TAG=" + versionTag);

  const tx = await contract.updateCemuRootHash(rootHash, versionTag);
  console.log("ORACLE_UPDATE_TX_HASH=" + tx.hash);

  const receipt = await tx.wait();
  console.log("ORACLE_UPDATE_STATUS=" + String(receipt.status));
  console.log("ORACLE_UPDATE_BLOCK_NUMBER=" + String(receipt.blockNumber));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
