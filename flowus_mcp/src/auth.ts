import http from "node:http";
import { spawn } from "node:child_process";
import crypto from "node:crypto";
import { URL } from "node:url";
import { FLOWUS_ENV_KEY, getTokenStorageHints, loadTokenBlob, saveTokenBlob, type OAuthStoredBlob } from "./tokenStore.js";

export type FlowUsAuthState = {
  status: "ready" | "pending";
  accessToken?: string;
};

function nowMs(): number {
  return Date.now();
}

function shouldReauth(blob: OAuthStoredBlob): boolean {
  if (!blob.expiresAtMs) return false;
  return blob.expiresAtMs - nowMs() <= 60_000;
}

async function fetchJson<T>(url: string, init: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  const text = await res.text();
  if (!res.ok) {
    throw new Error(`HTTP ${res.status} ${res.statusText}: ${text}`);
  }
  return JSON.parse(text) as T;
}

async function exchangeCodeForToken(args: {
  code: string;
  clientId: string;
  clientSecret: string;
  redirectUri: string;
}): Promise<{ access_token: string; refresh_token?: string; expires_in?: number }> {
  return fetchJson("https://api.flowus.cn/oauth/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      grant_type: "authorization_code",
      code: args.code,
      client_id: args.clientId,
      client_secret: args.clientSecret,
      redirect_uri: args.redirectUri,
    }),
  });
}

async function refreshAccessToken(args: {
  refreshToken: string;
  clientId: string;
  clientSecret: string;
}): Promise<{ access_token: string; refresh_token?: string; expires_in?: number }> {
  return fetchJson("https://api.flowus.cn/oauth/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      grant_type: "refresh_token",
      refresh_token: args.refreshToken,
      client_id: args.clientId,
      client_secret: args.clientSecret,
    }),
  });
}

function tryOpenBrowser(url: string): void {
  if (process.platform === "win32") {
    spawn("cmd", ["/c", "start", "", url], { windowsHide: true, stdio: "ignore" }).unref();
    return;
  }
  if (process.platform === "darwin") {
    spawn("open", [url], { stdio: "ignore" }).unref();
    return;
  }
  spawn("xdg-open", [url], { stdio: "ignore" }).unref();
}

function htmlPage(body: string): string {
  return `<!doctype html><html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>FlowUs MCP Auth</title></head><body style="font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; line-height:1.4; padding:24px; max-width:820px; margin:0 auto;">${body}</body></html>`;
}

async function validateTokenUsable(accessToken: string): Promise<{ ok: boolean; message?: string }> {
  try {
    const res = await fetch("https://api.flowus.cn/v1/search", {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}`, "Content-Type": "application/json" },
      body: JSON.stringify({ query: "", page_size: 1 }),
    });
    if (res.ok) return { ok: true };
    const text = await res.text();
    const normalized = text.replace(/\s+/g, " ").trim();
    if (/暂无空间|不支持免费版|免费版空间/i.test(normalized)) {
      return { ok: false, message: "当前账号/空间可能不支持 API（例如：免费版空间不支持）。请切换到支持 API 的空间后重试授权。" };
    }
    return { ok: false, message: normalized ? `API 访问验证失败：${normalized}` : "API 访问验证失败（无返回内容）" };
  } catch (e) {
    return { ok: false, message: `API 访问验证失败：${e instanceof Error ? e.message : String(e)}` };
  }
}

export async function ensureFlowUsAccessToken(opts: {
  port: number;
  stderr: NodeJS.WritableStream;
}): Promise<FlowUsAuthState> {
  const stored = await loadTokenBlob();
  if (stored && stored.accessToken && !shouldReauth(stored)) {
    return { status: "ready", accessToken: stored.accessToken };
  }

  if (stored?.refreshToken && stored.clientId && stored.clientSecret) {
    try {
      const refreshed = await refreshAccessToken({
        refreshToken: stored.refreshToken,
        clientId: stored.clientId,
        clientSecret: stored.clientSecret,
      });
      const expiresAtMs =
        typeof refreshed.expires_in === "number" ? nowMs() + refreshed.expires_in * 1000 : undefined;
      const blob: OAuthStoredBlob = {
        version: 1,
        clientId: stored.clientId,
        clientSecret: stored.clientSecret,
        redirectUri: stored.redirectUri,
        accessToken: refreshed.access_token,
        refreshToken: refreshed.refresh_token ?? stored.refreshToken,
        expiresAtMs,
      };
      await saveTokenBlob(blob);
      return { status: "ready", accessToken: blob.accessToken };
    } catch {
    }
  }

  const redirectUri = `http://127.0.0.1:${opts.port}/callback`;
  const state = crypto.randomBytes(16).toString("hex");
  let readyResolve: ((token: string) => void) | null = null;
  let readyReject: ((err: Error) => void) | null = null;
  const readyPromise = new Promise<string>((resolve, reject) => {
    readyResolve = resolve;
    readyReject = reject;
  });

  const server = http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url ?? "/", `http://127.0.0.1:${opts.port}`);
      if (req.method === "GET" && url.pathname === "/") {
        res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
        res.end(
          htmlPage(`
            <h1>FlowUs MCP 授权</h1>
            <p>首次运行需要 OAuth 授权。请在下方填写 FlowUs 外部应用的 Client ID / Client Secret，然后点击授权。</p>
            <p><b>Redirect URI</b> 固定为：<code>${redirectUri}</code></p>
            <form method="POST" action="/start" style="display:flex; flex-direction:column; gap:12px; margin-top:16px;">
              <label>Client ID<br/><input name="clientId" style="width:100%; padding:8px;" required /></label>
              <label>Client Secret<br/><input name="clientSecret" style="width:100%; padding:8px;" required /></label>
              <button type="submit" style="padding:10px 14px; width:160px;">开始授权</button>
            </form>
            <hr style="margin:24px 0;"/>
            <p>完成授权后，token 会持久化保存到用户级环境变量：<code>${FLOWUS_ENV_KEY}</code>（当前为 Windows setx）。</p>
          `),
        );
        return;
      }

      if (req.method === "POST" && url.pathname === "/start") {
        const chunks: Buffer[] = [];
        req.on("data", (d) => chunks.push(d));
        req.on("end", () => {
          const body = Buffer.concat(chunks).toString("utf8");
          const params = new URLSearchParams(body);
          const clientId = (params.get("clientId") ?? "").trim();
          const clientSecret = (params.get("clientSecret") ?? "").trim();
          if (!clientId || !clientSecret) {
            res.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
            res.end("Missing clientId/clientSecret");
            return;
          }
          const authorize = new URL("https://api.flowus.cn/oauth/authorize");
          authorize.searchParams.set("response_type", "code");
          authorize.searchParams.set("client_id", clientId);
          authorize.searchParams.set("redirect_uri", redirectUri);
          authorize.searchParams.set("state", state);
          (server as any).__flowusClientId = clientId;
          (server as any).__flowusClientSecret = clientSecret;
          res.writeHead(302, { Location: authorize.toString() });
          res.end();
        });
        return;
      }

      if (req.method === "GET" && url.pathname === "/callback") {
        const code = (url.searchParams.get("code") ?? "").trim();
        const gotState = (url.searchParams.get("state") ?? "").trim();
        if (!code || gotState !== state) {
          res.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
          res.end("Invalid callback parameters");
          return;
        }
        const clientId = (server as any).__flowusClientId as string | undefined;
        const clientSecret = (server as any).__flowusClientSecret as string | undefined;
        if (!clientId || !clientSecret) {
          res.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
          res.end("Missing client credentials in session");
          return;
        }

        const token = await exchangeCodeForToken({ code, clientId, clientSecret, redirectUri });
        const expiresAtMs =
          typeof token.expires_in === "number" ? nowMs() + token.expires_in * 1000 : undefined;
        const blob: OAuthStoredBlob = {
          version: 1,
          clientId,
          clientSecret,
          redirectUri,
          accessToken: token.access_token,
          refreshToken: token.refresh_token,
          expiresAtMs,
        };
        const { envKey, filePath } = getTokenStorageHints();
        await saveTokenBlob(blob);
        const validation = await validateTokenUsable(blob.accessToken);
        res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
        res.end(
          htmlPage(`
            <h1>授权成功</h1>
            <p>Token 已保存到：</p>
            <ul>
              <li>用户级环境变量：<code>${envKey}</code>（需要重启 MCP Client/Trae 才会在新进程中生效）</li>
              <li>用户配置文件：<code>${filePath}</code></li>
            </ul>
            ${validation.ok ? "<p>API 访问验证：通过。</p>" : `<p style="color:#b91c1c;">API 访问验证：未通过。${validation.message ?? ""}</p>`}
            <p>现在可以关闭本页。</p>
          `),
        );
        readyResolve?.(blob.accessToken);
        return;
      }

      res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("Not Found");
    } catch (e) {
      res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("Internal Server Error");
      readyReject?.(e instanceof Error ? e : new Error(String(e)));
    }
  });

  await new Promise<void>((resolve, reject) => {
    server.listen(opts.port, "127.0.0.1", () => resolve());
    server.on("error", reject);
  });

  const localUrl = `http://127.0.0.1:${opts.port}/`;
  opts.stderr.write(
    `FlowUs MCP: 未检测到可用 token，已启动 OAuth 本地授权页：${localUrl}\n`,
  );
  tryOpenBrowser(localUrl);

  readyPromise.finally(() => {
    server.close();
  });

  return {
    status: "pending",
    get accessToken() {
      return undefined;
    },
  };
}

export class FlowUsAuthManager {
  private readonly port: number;
  private readonly stderr: NodeJS.WritableStream;
  private token: string | null = null;
  private pending: Promise<string> | null = null;

  constructor(opts: { port?: number; stderr?: NodeJS.WritableStream } = {}) {
    this.port = opts.port ?? 32111;
    this.stderr = opts.stderr ?? process.stderr;
  }

  async init(): Promise<void> {
    const stored = await loadTokenBlob();
    if (stored?.accessToken && !shouldReauth(stored)) {
      this.token = stored.accessToken;
      return;
    }
    if (this.pending) return;
    this.pending = this.startOAuthAndWaitForToken();
    this.pending
      .then((t) => {
        this.token = t;
      })
      .catch(() => {
        this.pending = null;
      });
  }

  async getAccessToken(): Promise<string> {
    if (this.token) return this.token;
    await this.init();
    if (this.token) return this.token;
    if (!this.pending) {
      this.pending = this.startOAuthAndWaitForToken();
    }
    return this.pending;
  }

  private async startOAuthAndWaitForToken(): Promise<string> {
    const stored = await loadTokenBlob();
    if (stored?.refreshToken && stored.clientId && stored.clientSecret) {
      try {
        const refreshed = await refreshAccessToken({
          refreshToken: stored.refreshToken,
          clientId: stored.clientId,
          clientSecret: stored.clientSecret,
        });
        const expiresAtMs =
          typeof refreshed.expires_in === "number" ? nowMs() + refreshed.expires_in * 1000 : undefined;
        const blob: OAuthStoredBlob = {
          version: 1,
          clientId: stored.clientId,
          clientSecret: stored.clientSecret,
          redirectUri: stored.redirectUri,
          accessToken: refreshed.access_token,
          refreshToken: refreshed.refresh_token ?? stored.refreshToken,
          expiresAtMs,
        };
        await saveTokenBlob(blob);
        return blob.accessToken;
      } catch {
      }
    }

    const redirectUri = `http://127.0.0.1:${this.port}/callback`;
    const state = crypto.randomBytes(16).toString("hex");
    let resolveToken: ((token: string) => void) | null = null;
    let rejectToken: ((err: Error) => void) | null = null;
    const tokenPromise = new Promise<string>((resolve, reject) => {
      resolveToken = resolve;
      rejectToken = reject;
    });

    const server = http.createServer(async (req, res) => {
      try {
        const url = new URL(req.url ?? "/", `http://127.0.0.1:${this.port}`);
        if (req.method === "GET" && url.pathname === "/") {
          res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
          res.end(
            htmlPage(`
              <h1>FlowUs MCP 授权</h1>
              <p>首次运行需要 OAuth 授权。请在下方填写 FlowUs 外部应用的 Client ID / Client Secret，然后点击授权。</p>
              <p><b>Redirect URI</b> 固定为：<code>${redirectUri}</code></p>
              <form method="POST" action="/start" style="display:flex; flex-direction:column; gap:12px; margin-top:16px;">
                <label>Client ID<br/><input name="clientId" style="width:100%; padding:8px;" required /></label>
                <label>Client Secret<br/><input name="clientSecret" style="width:100%; padding:8px;" required /></label>
                <button type="submit" style="padding:10px 14px; width:160px;">开始授权</button>
              </form>
              <hr style="margin:24px 0;"/>
              <p>完成授权后，token 会持久化保存到用户级环境变量：<code>${FLOWUS_ENV_KEY}</code>（当前为 Windows setx）。</p>
            `),
          );
          return;
        }

        if (req.method === "POST" && url.pathname === "/start") {
          const chunks: Buffer[] = [];
          req.on("data", (d) => chunks.push(d));
          req.on("end", () => {
            const body = Buffer.concat(chunks).toString("utf8");
            const params = new URLSearchParams(body);
            const clientId = (params.get("clientId") ?? "").trim();
            const clientSecret = (params.get("clientSecret") ?? "").trim();
            if (!clientId || !clientSecret) {
              res.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
              res.end("Missing clientId/clientSecret");
              return;
            }
            const authorize = new URL("https://api.flowus.cn/oauth/authorize");
            authorize.searchParams.set("response_type", "code");
            authorize.searchParams.set("client_id", clientId);
            authorize.searchParams.set("redirect_uri", redirectUri);
            authorize.searchParams.set("state", state);
            (server as any).__flowusClientId = clientId;
            (server as any).__flowusClientSecret = clientSecret;
            res.writeHead(302, { Location: authorize.toString() });
            res.end();
          });
          return;
        }

        if (req.method === "GET" && url.pathname === "/callback") {
          const code = (url.searchParams.get("code") ?? "").trim();
          const gotState = (url.searchParams.get("state") ?? "").trim();
          if (!code || gotState !== state) {
            res.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
            res.end("Invalid callback parameters");
            return;
          }
          const clientId = (server as any).__flowusClientId as string | undefined;
          const clientSecret = (server as any).__flowusClientSecret as string | undefined;
          if (!clientId || !clientSecret) {
            res.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
            res.end("Missing client credentials in session");
            return;
          }

          const token = await exchangeCodeForToken({ code, clientId, clientSecret, redirectUri });
          const expiresAtMs =
            typeof token.expires_in === "number" ? nowMs() + token.expires_in * 1000 : undefined;
          const blob: OAuthStoredBlob = {
            version: 1,
            clientId,
            clientSecret,
            redirectUri,
            accessToken: token.access_token,
            refreshToken: token.refresh_token,
            expiresAtMs,
          };
          const { envKey, filePath } = getTokenStorageHints();
          await saveTokenBlob(blob);
          const validation = await validateTokenUsable(blob.accessToken);
          res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
          res.end(
            htmlPage(`
              <h1>授权成功</h1>
              <p>Token 已保存到：</p>
              <ul>
                <li>用户级环境变量：<code>${envKey}</code>（需要重启 MCP Client/Trae 才会在新进程中生效）</li>
                <li>用户配置文件：<code>${filePath}</code></li>
              </ul>
              ${validation.ok ? "<p>API 访问验证：通过。</p>" : `<p style="color:#b91c1c;">API 访问验证：未通过。${validation.message ?? ""}</p>`}
              <p>现在可以关闭本页。</p>
            `),
          );
          resolveToken?.(blob.accessToken);
          return;
        }

        res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
        res.end("Not Found");
      } catch (e) {
        res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
        res.end("Internal Server Error");
        rejectToken?.(e instanceof Error ? e : new Error(String(e)));
      }
    });

    await new Promise<void>((resolve, reject) => {
      server.listen(this.port, "127.0.0.1", () => resolve());
      server.on("error", reject);
    });

    const localUrl = `http://127.0.0.1:${this.port}/`;
    this.stderr.write(`FlowUs MCP: 请完成 OAuth 授权：${localUrl}\n`);
    tryOpenBrowser(localUrl);

    tokenPromise.finally(() => {
      server.close();
    });

    return tokenPromise;
  }
}
