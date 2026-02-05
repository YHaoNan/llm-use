# FlowUs 文档（本地归档）

更新时间：2026-02-05

本目录用于归档 FlowUs 与“基于 HTTP API 自建 MCP Server”相关的官方公开文档与关键要点，方便后续离线检索与持续迭代。

## 快速索引

- 综述与入口：[overview.md](./overview.md)
- 鉴权与集成（内部插件 / 外部应用 OAuth2）：[auth.md](./auth.md)
- API
  - Pages（页面）：[api-pages.md](./api-pages.md)
  - Blocks（块）：[api-blocks.md](./api-blocks.md)
  - Databases（多维表）：[api-databases.md](./api-databases.md)
  - Search（搜索）：[api-search.md](./api-search.md)
  - User（用户）：[api-user.md](./api-user.md)
  - Page Properties（属性规范）：[page-properties.md](./page-properties.md)
  - Block Object Entity（块对象实体/类型定义）：[block-object-entity.md](./block-object-entity.md)
- 更新日志：[changelog.md](./changelog.md)
- SDK 与 Demo（GitHub 摘录）：[sdk.md](./sdk.md)
- TypeScript SDK README 摘要：[typescript-sdk-summary.md](./typescript-sdk-summary.md)
- SDK vs 纯 HTTP 对比：[sdk-vs-http.md](./sdk-vs-http.md)
- 早期汇总备份：[flowus-dev-docs.md](./flowus-dev-docs.md)

## 给 MCP Server 的最小接口集合（建议）

- 鉴权
  - 外部应用：OAuth2 换取 access_token
  - 内部插件：Bot Token（机器人令牌）
- 读取
  - `POST /v1/search`：按关键词/语义在授权范围内找页面
  - `GET /v1/pages/{page_id}`：拿页面元信息与 properties
  - `GET /v1/blocks/{block_id}/children`：读取页面内容（页面也是块）
  - `POST /v1/databases/{database_id}/query`：查询结构化记录
- 写入
  - `POST /v1/pages`：创建页面/数据库记录
  - `PATCH /v1/pages/{page_id}`：更新页面属性
  - `PATCH /v1/blocks/{block_id}/children`：追加内容块（批量写入）
  - `PATCH /v1/blocks/{block_id}` / `DELETE /v1/blocks/{block_id}`：更新/删除块
