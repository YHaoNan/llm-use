# FlowUs MCP Server（Node.js + TypeScript）

当前能力：

- tool：`search`（基于 FlowUs HTTP API /v1/search，通过 TypeScript SDK 调用）

认证策略：

- 默认采用 OAuth（外部应用授权码流程）
- 未检测到有效 token 时，会在本机启动一个授权页（默认 `http://127.0.0.1:32111/`），引导用户完成 OAuth 授权
- 授权成功后会把凭据持久化到用户级环境变量 `FLOWUS_MCP_OAUTH`（Windows 下通过 `setx`）

## 运行

```bash
cd mcp-servers/flowus_mcp
npm install
npm run build
npm run start
```

首次运行如果没有 token，会自动打开浏览器到授权页。

## Trae MCP 配置示例（mcp.json）

```json
{
  "mcpServers": {
    "flowus": {
      "transport": "stdio",
      "command": "node",
      "args": ["D:/WorkSpace/personal/llm-use/mcp-servers/flowus_mcp/dist/index.js"],
      "cwd": "D:\\WorkSpace\\personal\\llm-use\\mcp-servers\\flowus_mcp",
      "env": {}
    }
  }
}
```

## 说明

- 你需要在 FlowUs 创建“外部应用（External Application）”，并在其 Redirect URI 中添加：
  - `http://127.0.0.1:32111/callback`
- 授权成功后，需要重启 MCP Client 才能让新写入的用户环境变量在新进程里生效。

