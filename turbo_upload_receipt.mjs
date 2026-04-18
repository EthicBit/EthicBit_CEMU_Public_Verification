import fs from "fs";
import { TurboFactory, ArweaveSigner } from "@ardrive/turbo-sdk";

const filePath = "/tmp/anchor-receipt.arweave_republish.complete.json";
const walletPath = process.env.ARWEAVE_WALLET;

if (!walletPath) {
  console.error("ERR_NO_WALLET_ENV");
  process.exit(1);
}
if (!fs.existsSync(walletPath)) {
  console.error("ERR_WALLET_NOT_FOUND");
  process.exit(2);
}
if (!fs.existsSync(filePath)) {
  console.error("ERR_FILE_NOT_FOUND");
  process.exit(3);
}

const jwk = JSON.parse(fs.readFileSync(walletPath, "utf-8"));
const signer = new ArweaveSigner(jwk);
const turbo = TurboFactory.authenticated({ signer });

const result = await turbo.uploadFile({
  fileStreamFactory: () => fs.createReadStream(filePath),
  fileSizeFactory: () => fs.statSync(filePath).size,
  dataItemOpts: {
    tags: [
      { name: "Content-Type", value: "application/json" },
      { name: "App-Name", value: "EthicBit_CEMU" },
      { name: "Artifact-Type", value: "anchor-receipt.swarm_mvp_v1.complete-republish" }
    ]
  }
});

console.log(JSON.stringify(result, null, 2));
