import { network } from "hardhat";

async function main() {
  const { ethers } = await network.connect();
  const [s] = await ethers.getSigners();

  console.log("SIGNER=" + s.address);
  console.log("BAL=" + (await ethers.provider.getBalance(s.address)).toString());

  // Debe ser NO cero y distinto del root real para que luego builder pueda actualizar
  const initRoot = "0x1111111111111111111111111111111111111111111111111111111111111111";
  const initVersion = "0x0000000000000000000000000000000000000000000000000000000000000001";

  const F = await ethers.getContractFactory("CEMUEthicalOracle", s);
  const c = await F.deploy(initRoot, initVersion);
  await c.waitForDeployment();

  console.log("ADDR=" + await c.getAddress());
}
main().catch((e) => { console.error(e); process.exit(1); });
