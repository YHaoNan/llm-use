# TypeScript SDK README 摘要（flowus-api-sdk）

更新时间：2026-02-05  
来源（raw）：https://raw.githubusercontent.com/next-space/flowus-api-sdk/master/sdk/typescript/README.md

## 一句话概括

这是一个基于 OpenAPI 生成/维护的 TypeScript/JavaScript 客户端 SDK，通过 `DefaultApi + Configuration` 以 Bearer Token 调用 FlowUs 的 Pages / Blocks / Databases / Search 等 HTTP API，并提供完整类型定义与基础错误处理示例。

## 快速上手（README 提到的关键步骤）

- 安装：`npm install flowus-api-sdk`
- 初始化：
  - `Configuration({ basePath: 'https://api.flowus.cn', headers: { Authorization: 'Bearer YOUR_API_TOKEN' } })`
  - `new DefaultApi(config)`
- 调用示例：`api.createPage({...})`

## 鉴权方式（README 约定）

- 使用“集成（Integration）”生成的 API Token
- 在请求头使用：`Authorization: Bearer <token>`
- 获取 Token 的路径：Settings → Integrations → Create integration → Copy token

## 可用方法（README 列举的分类）

### Pages

- `createPage()`：创建页面
- `updatePage()`：更新页面
- `queryDatabase()`：查询数据库（README 把它列在 Pages 下）

### Blocks

- `getBlockChildren()`：获取块/页面的子块
- `appendBlockChildren()`：追加子块
- `updateBlock()`：更新块
- `deleteBlock()`：删除块

### Databases

- `createDatabase()`：创建数据库
- `updateDatabase()`：更新数据库属性

### Search

- `search()`：搜索页面/数据库

## TypeScript 支持点

- SDK 用 TypeScript 编写，包含完整类型定义（README 举例提到 `Block` / `Page` / `Database` 类型）
- 适合在 MCP Server（Node.js + TS）里直接获得类型提示、减少手写请求体/响应体的出错率

## 错误处理（README 示例）

- 用 `try/catch` 捕获错误
- 通过 `error.status` 判断 401/404 等情况并输出对应信息

## 与你关注点的映射

- 渐进式读取文档树：`getBlockChildren()` + 分页（需要你在服务端控制“按层级披露”策略）
- 文档增删改查：
  - 新建：`createPage()` / `appendBlockChildren()`
  - 更新：`updatePage()` / `updateBlock()`
  - 删除：`deleteBlock()`（是否有删除页面/归档页面方法需进一步看 OpenAPI/SDK 源码）
  - 读：`getBlockChildren()` / `getPage(...)`（README 示例里出现了 `api.getPage('page-id')`，但方法名需以实际 SDK 导出为准）
- 搜索文档：`search()`
- 登录与重新授权：README 只描述“使用 API Token”；OAuth2 授权码换 token 不在 README 里体现（外部应用场景需你自行实现 OAuth2 流程）

