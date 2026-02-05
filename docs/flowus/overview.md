# FlowUs 开发者能力综述（自建 MCP Server 视角）

更新时间：2026-02-05  
官方入口：https://flowus.cn/share/df7cd54f-1c21-4fc1-9fd8-ce81be1918a5

## 你要的能力是否齐全

如果你的目标是“把 FlowUs 当作知识库，并通过 MCP Server 为 LLM 提供检索/写入能力”，FlowUs 的 HTTP API 已覆盖必要的 CRUD 与搜索能力：

- 页面（Page）与块（Block）模型：可以把一篇笔记当作“页面 + 其子块树”
- 多维表（Database）：可以把知识条目结构化成记录，并提供查询接口
- 搜索（Search）：在机器人已授权的范围内做检索（适合 MCP 的 `search` 工具）

## 核心入口

- 正式环境 API Base URL：`https://api.flowus.cn/v1`
- 测试环境 API Base URL：`https://api-test.allflow.cn/v1`
- 鉴权头：`Authorization: Bearer <token>`

## 文档里提到的 MCP 接入（官方托管）

文档页面给出了 FlowUs 自己的 MCP 访问地址（token 为“授权码”）：

- Streamable HTTP：`https://mcp.allflow.cn/message?token=授权码`
- SSE：`https://mcp.allflow.cn/sse?token=授权码`

这两条更像是“直接使用 FlowUs 官方 MCP 服务”的方式；如果你要自建 MCP Server，可以先把它当作对照实现。

## 自建 MCP Server 的推荐数据流

常见的工具组合（与 API 端点的对应关系）：

- `flowus.search(query)` -> `POST /v1/search`
- `flowus.getPage(pageId)` -> `GET /v1/pages/{page_id}`
- `flowus.getBlockChildren(blockId, cursor)` -> `GET /v1/blocks/{block_id}/children`
- `flowus.createPage(parent, properties)` -> `POST /v1/pages`
- `flowus.appendBlocks(parentBlockId, children[])` -> `PATCH /v1/blocks/{block_id}/children`
- `flowus.queryDatabase(databaseId, filter/sort/cursor)` -> `POST /v1/databases/{database_id}/query`

## 边界与限制（对 MCP 影响最大）

- 权限：搜索与读写都被限制在机器人明确授权的页面/数据库范围内
- 速率：Blocks API 文档给出了读/写/批量的分钟级限制，适合做批处理与退避重试
- 内容分块：富文本单段长度与块嵌套深度有限制，长内容写入需要分段/分块

