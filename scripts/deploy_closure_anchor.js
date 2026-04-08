import { network } from "hardhat";

function requireEnv(name) {
  const value = process.env[name];
  if (!value || value.includes("REEMPLAZA") || value.includes("PENDING")) {
    throw new Error(`${name} no esta configurada con un valor real`);
  }
  return value;
}

async function main() {
  const expectedAccount = requireEnv("ETHICBIT_ACCOUNT_ADDRESS").toLowerCase();

  const { ethers } = await network.connect();

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

  const factory = await ethers.getContractFactory("ClosureAnchor", deployer);
  const contract = await factory.deploy(await deployer.getAddress());
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  const owner = await contract.owner();

  console.log(`DEPLOYED_CLOSURE_ANCHOR=${address}`);
  console.log(`OWNER=${owner}`);
}
main().catch((error) => {
  console.error(error);
  process.exit(1);
});
