import "dotenv/config";
import hardhatEthers from "@nomicfoundation/hardhat-ethers";

const sepoliaUrl = process.env.ETH_RPC_URL || "http://127.0.0.1:8545";
const soliditySettings = {
  optimizer: {
    enabled: true,
    runs: 200
  },
  viaIR: true
};

export default {
  plugins: [hardhatEthers],
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./.hardhat/cache",
    artifacts: "./.hardhat/artifacts"
  },
  solidity: {
    compilers: [
      { version: "0.8.24", settings: soliditySettings },
      { version: "0.8.28", settings: soliditySettings }
    ]
  },
  networks: {
    sepolia: {
      type: "http",
      url: sepoliaUrl,
      chainId: Number(process.env.ETH_CHAIN_ID || "11155111"),
      accounts:
        process.env.DEPLOYER_PRIVATE_KEY &&
        !process.env.DEPLOYER_PRIVATE_KEY.includes("REEMPLAZA")
          ? [process.env.DEPLOYER_PRIVATE_KEY]
          : []
    }
  }
};
