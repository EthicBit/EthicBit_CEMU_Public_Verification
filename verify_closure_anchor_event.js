import fs from "fs";
import { ethers } from "ethers";

// Uso:
// RPC_URL="https://..." \
// CONTRACT_ADDRESS="0x..." \
// ROOT_HASH="0x..." \
// TX_HASH="0x..." \
// EXPECTED_CHAIN_ID="11155111" \
// node verify_closure_anchor_event.js

const RPC_URL = process.env.RPC_URL || "";
const CONTRACT_ADDRESS = process.env.CONTRACT_ADDRESS || "";
const ROOT_HASH = process.env.ROOT_HASH || "";
const TX_HASH = process.env.TX_HASH || "";
const EXPECTED_CHAIN_ID = Number(process.env.EXPECTED_CHAIN_ID || "0");

function fail(message) {
  console.error(`FAIL: ${message}`);
  process.exit(1);
}

function ok(message) {
  console.log(`OK: ${message}`);
}

function info(message) {
  console.log(`INFO: ${message}`);
}

function normalizeHex(value) {
  return String(value || "").toLowerCase();
}

async function main() {
  if (!RPC_URL) fail("Falta RPC_URL");
  if (!CONTRACT_ADDRESS) fail("Falta CONTRACT_ADDRESS");
  if (!ROOT_HASH) fail("Falta ROOT_HASH");
  if (!EXPECTED_CHAIN_ID) fail("Falta EXPECTED_CHAIN_ID");

  const abi = JSON.parse(fs.readFileSync("contracts/ClosureAnchor.abi.json", "utf8"));

  const hasClosureAnchored = abi.some(
    (item) => item.type === "event" && item.name === "ClosureAnchored"
  );
  const hasIsAnchored = abi.some(
    (item) => item.type === "function" && item.name === "isAnchored"
  );
  const hasGetAnchor = abi.some(
    (item) => item.type === "function" && item.name === "getAnchor"
  );

  if (!hasClosureAnchored) fail("El ABI no contiene ClosureAnchored");
  if (!hasIsAnchored) fail("El ABI no contiene isAnchored");
  if (!hasGetAnchor) fail("El ABI no contiene getAnchor");

  ok("ABI alineado con ClosureAnchored / isAnchored / getAnchor");

  const provider = new ethers.JsonRpcProvider(RPC_URL);
  const network = await provider.getNetwork();

  if (Number(network.chainId) !== EXPECTED_CHAIN_ID) {
    fail(`ChainId inesperado: ${network.chainId} != ${EXPECTED_CHAIN_ID}`);
  }

  ok(`ChainId confirmado: ${network.chainId}`);

  const contract = new ethers.Contract(CONTRACT_ADDRESS, abi, provider);

  const anchored = await contract.isAnchored(ROOT_HASH);
  if (!anchored) fail("isAnchored(rootHash) devolvio false");
  ok("isAnchored(rootHash) devolvio true");

  const record = await contract.getAnchor(ROOT_HASH);

  if (!record.exists) fail("getAnchor(rootHash).exists devolvio false");
  ok("getAnchor(rootHash).exists devolvio true");

  if (normalizeHex(record.rootHash) !== normalizeHex(ROOT_HASH)) {
    fail("getAnchor(rootHash).rootHash no coincide con ROOT_HASH");
  }
  ok(`rootHash confirmado en getAnchor: ${record.rootHash}`);

  if (Number(record.chainId) !== EXPECTED_CHAIN_ID) {
    fail("getAnchor(rootHash).chainId no coincide con EXPECTED_CHAIN_ID");
  }
  ok(`chainId confirmado en getAnchor: ${record.chainId}`);

  if (TX_HASH) {
    info(`Verificando por transaccion: ${TX_HASH}`);

    const txReceipt = await provider.getTransactionReceipt(TX_HASH);
    if (!txReceipt) fail("No existe receipt para TX_HASH");

    if (txReceipt.to && normalizeHex(txReceipt.to) !== normalizeHex(CONTRACT_ADDRESS)) {
      fail("La transaccion no apunta al CONTRACT_ADDRESS esperado");
    }

    const iface = new ethers.Interface(abi);
    const expectedTopic0 = iface.getEvent("ClosureAnchored").topicHash;

    const matchingLogs = txReceipt.logs.filter((log) => {
      return (
        normalizeHex(log.address) === normalizeHex(CONTRACT_ADDRESS) &&
        normalizeHex(log.topics[0]) === normalizeHex(expectedTopic0)
      );
    });

    if (!matchingLogs.length) {
      fail("No se encontro evento ClosureAnchored dentro de TX_HASH");
    }

    let parsed = null;
    for (const log of matchingLogs) {
      try {
        const candidate = iface.parseLog(log);
        if (normalizeHex(candidate.args.rootHash) === normalizeHex(ROOT_HASH)) {
          parsed = candidate;
          break;
        }
      } catch {}
    }

    if (!parsed) {
      fail("No se encontro evento ClosureAnchored con el rootHash esperado dentro de TX_HASH");
    }

    ok("Evento ClosureAnchored encontrado en la transaccion");
    ok(`rootHash confirmado en evento: ${parsed.args.rootHash}`);

    if (normalizeHex(parsed.args.anchorer) !== normalizeHex(record.anchorer)) {
      fail("anchorer del evento no coincide con getAnchor(rootHash).anchorer");
    }
    ok(`anchorer consistente: ${parsed.args.anchorer}`);

    if (String(parsed.args.nonce) !== String(record.nonce)) {
      fail("nonce del evento no coincide con getAnchor(rootHash).nonce");
    }
    ok(`nonce consistente: ${parsed.args.nonce}`);

    if (Number(parsed.args.chainId) !== Number(record.chainId)) {
      fail("chainId del evento no coincide con getAnchor(rootHash).chainId");
    }
    ok(`chainId del evento consistente: ${parsed.args.chainId}`);

    const previousBlockNumber = Number(txReceipt.blockNumber) - 1;
    if (previousBlockNumber < 0) {
      fail("No se puede calcular el bloque previo");
    }

    const previousBlock = await provider.getBlock(previousBlockNumber);
    if (!previousBlock) {
      fail("No se pudo recuperar el bloque previo al receipt");
    }

    if (normalizeHex(parsed.args.blockHash) !== normalizeHex(previousBlock.hash)) {
      fail("blockHash del evento no coincide con blockhash(block.number - 1)");
    }
    ok(`blockHash consistente con bloque previo: ${parsed.args.blockHash}`);
  }

  console.log("EVENT_NAME=ClosureAnchored");
  console.log("EVENT_FIELD=rootHash");
  console.log(`CONTRACT_ADDRESS=${CONTRACT_ADDRESS}`);
  console.log(`ROOT_HASH=${ROOT_HASH}`);
  console.log("VERIFY_ONCHAIN_EVENT=PASS");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
