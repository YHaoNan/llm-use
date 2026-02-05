import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

export const FLOWUS_ENV_KEY = "FLOWUS_MCP_OAUTH";

export type OAuthStoredBlob = {
  version: 1;
  clientId: string;
  clientSecret: string;
  redirectUri: string;
  accessToken: string;
  refreshToken?: string;
  expiresAtMs?: number;
};

function encodeBlob(blob: OAuthStoredBlob): string {
  return Buffer.from(JSON.stringify(blob), "utf8").toString("base64url");
}

function decodeBlob(encoded: string): OAuthStoredBlob | null {
  try {
    const raw = Buffer.from(encoded, "base64url").toString("utf8");
    const parsed = JSON.parse(raw) as OAuthStoredBlob;
    if (parsed?.version !== 1) return null;
    if (!parsed.clientId || !parsed.clientSecret || !parsed.redirectUri || !parsed.accessToken) return null;
    return parsed;
  } catch {
    return null;
  }
}

function getDefaultTokenFilePath(): string {
  const home = os.homedir();
  if (process.platform === "win32") {
    const appData = process.env.APPDATA || path.join(home, "AppData", "Roaming");
    return path.join(appData, "flowus-mcp", "token.json");
  }
  if (process.platform === "darwin") {
    return path.join(home, "Library", "Application Support", "flowus-mcp", "token.json");
  }
  const xdg = process.env.XDG_CONFIG_HOME || path.join(home, ".config");
  return path.join(xdg, "flowus-mcp", "token.json");
}

export function getTokenStorageHints(): { envKey: string; filePath: string } {
  return { envKey: FLOWUS_ENV_KEY, filePath: getDefaultTokenFilePath() };
}

export async function loadTokenBlob(): Promise<OAuthStoredBlob | null> {
  const v = (process.env[FLOWUS_ENV_KEY] ?? "").trim();
  if (v) {
    const blob = decodeBlob(v);
    if (blob) return blob;
  }
  const filePath = getDefaultTokenFilePath();
  try {
    const raw = await fs.readFile(filePath, "utf8");
    const parsed = JSON.parse(raw) as { encoded?: string };
    if (!parsed?.encoded) return null;
    const blob = decodeBlob(parsed.encoded);
    if (!blob) return null;
    process.env[FLOWUS_ENV_KEY] = parsed.encoded;
    return blob;
  } catch {
    return null;
  }
}

async function persistToUserEnvWindows(encoded: string): Promise<void> {
  const { spawn } = await import("node:child_process");
  await new Promise<void>((resolve, reject) => {
    const child = spawn("setx", [FLOWUS_ENV_KEY, encoded], {
      windowsHide: true,
      stdio: ["ignore", "ignore", "pipe"],
    });
    let stderr = "";
    child.stderr.on("data", (d) => {
      stderr += d.toString("utf8");
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error(stderr.trim() || `setx failed with code ${code}`));
    });
  });
}

export async function saveTokenBlob(blob: OAuthStoredBlob): Promise<string> {
  const encoded = encodeBlob(blob);
  process.env[FLOWUS_ENV_KEY] = encoded;

  const filePath = getDefaultTokenFilePath();
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, JSON.stringify({ encoded }, null, 2), "utf8");
  if (process.platform !== "win32") {
    try {
      await fs.chmod(filePath, 0o600);
    } catch {
    }
  }

  if (process.platform === "win32") {
    try {
      await persistToUserEnvWindows(encoded);
    } catch {
    }
  }

  return encoded;
}

