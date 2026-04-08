import "dotenv/config";
import hardhatEthers from "@nomicfoundation/hardhat-ethers";

export default {
  plugins: [hardhatEthers],
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
      url: process.env.ETH_RPC_URL || "",
      chainId: Number(process.env.ETH_CHAIN_ID || "11155111"),
      accounts:
        process.env.DEPLOYER_PRIVATE_KEY &&
        !process.env.DEPLOYER_PRIVATE_KEY.includes("REEMPLAZA")
          ? [process.env.DEPLOYER_PRIVATE_KEY]
          : []
    }
  }
};
