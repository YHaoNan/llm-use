import { spawn } from "node:child_process";
import { Buffer } from "node:buffer";

const blob = {
  version: 1,
  clientId: "dummy",
  clientSecret: "dummy",
  redirectUri: "http://127.0.0.1:32111/callback",
  accessToken: "dummy",
};
const encoded = Buffer.from(JSON.stringify(blob), "utf8").toString("base64url");

const child = spawn("node", ["dist/index.js"], {
  cwd: new URL("..", import.meta.url),
  stdio: ["pipe", "pipe", "pipe"],
  env: { ...process.env, FLOWUS_MCP_OAUTH: encoded },
});

child.stderr.on("data", (d) => process.stderr.write(String(d)));

let buf = Buffer.alloc(0);
function tryRead() {
  while (true) {
    const idx = buf.indexOf("\n");
    if (idx === -1) return;
    const line = buf.slice(0, idx).toString("utf8").replace(/\r$/, "");
    buf = buf.slice(idx + 1);
    if (!line.trim()) continue;
    process.stdout.write(`RECV ${line}\n`);
  }
}

child.stdout.on("data", (d) => {
  buf = Buffer.concat([buf, d]);
  tryRead();
});

function send(obj) {
  child.stdin.write(JSON.stringify(obj) + "\n");
}

send({
  jsonrpc: "2.0",
  id: 1,
  method: "initialize",
  params: { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "smoke", version: "0.0.0" } },
});
setTimeout(() => {
  send({
    jsonrpc: "2.0",
    id: 2,
    method: "tools/call",
    params: { name: "search", arguments: { query: "test", page_size: 1 } },
  });
}, 200);

setTimeout(() => child.kill(), 2000);

