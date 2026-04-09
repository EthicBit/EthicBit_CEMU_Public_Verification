import "dotenv/config";
import hardhatEthers from "@nomicfoundation/hardhat-ethers";

const sepoliaUrl = process.env.ETH_RPC_URL || "http://127.0.0.1:8545";

export default {
  plugins: [hardhatEthers],
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./.hardhat/cache",
    artifacts: "./.hardhat/artifacts"
  },
  solidity: {
    version: "0.8.24",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      },
      viaIR: true
    }
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
