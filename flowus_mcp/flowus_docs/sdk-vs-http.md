# SDK vs 纯 HTTP（Node.js + TypeScript 自建 MCP Server 视角）

更新时间：2026-02-05

## 结论先行

- 如果你要快速做出可用的 MCP Server，并且主要覆盖“渐进式读取块树 / CRUD / 搜索 / token 管理”，优先用 TypeScript SDK：省掉大量请求/类型样板代码，迭代更快。
- 如果你非常在意“可控性、可观测性（日志/重试/限流/缓存）、以及对 OAuth2/刷新策略/边角端点的完全掌控”，纯 HTTP 更直接；也可以采用“HTTP 封装 + 代码生成类型”的折中方案。

## 能力差异对比（重点围绕你的 4 项需求）

| 维度 | TypeScript SDK（flowus-api-sdk） | 纯 HTTP（fetch/undici/axios 等） |
|---|---|---|
| 渐进式读取文档树（按层级披露） | 直接调用 `getBlockChildren()`，你只需在 MCP 工具侧决定每次展开的层级/分页大小；类型定义能减少解析出错 | 同样能做，但要手写请求/响应类型与解析；更容易把“块类型/富文本结构”写错 |
| 文档 CRUD（页面/块/多维表） | README 列出 pages/blocks/databases 的常用方法（create/update/query/search 等）；调用接口更像“函数” | 端点完全自由；遇到 SDK 未覆盖/未同步的端点时更灵活 |
| 搜索 | README 提供 `search()`；适合直接做 MCP `search` 工具 | 同样能做；你需要自己处理分页 cursor 与响应结构 |
| 登录与重新授权 | README 只描述“Integration API Token + Bearer”；OAuth2 外部应用流程通常仍需你自己实现 | 最适合实现 OAuth2 授权码流程（`/oauth/authorize` + `/oauth/token`）与 token 存储/撤销/重试 |
| 类型安全 | 自带 TS 类型（README 明确），更适合 MCP 的工具入参/出参稳定 | 需要你自己写类型或生成类型；否则容易在演进时出错 |
| 维护成本 | 依赖 SDK 与其 OpenAPI 同步频率；更新 SDK 即可获得新端点/新字段（前提：仓库更新及时） | 由你维护请求封装与类型；一旦 FlowUs API 改动，你需要自行跟进修复 |
| 可观测性（日志/指标/重试/限流） | 需要看 SDK 底层实现是否提供 hooks；通常要在外层包一层“请求拦截器/包装器” | 你可完全自定义：统一重试退避、429/5xx 处理、并发与速率限制、请求追踪等 |
| 依赖风险 | 多一个第三方依赖；版本升级可能带来破坏性变更 | 依赖更少；但你自己实现的 HTTP 封装也要测试 |

## 两种方式的“能力本质”是否不同？

大多数情况下不不同：SDK 本质是对同一组 HTTP 端点的封装（并带类型）。因此：

- “能否读取块树/搜索/写入页面”取决于 FlowUs HTTP API 能力，不取决于 SDK
- 差异主要在“工程效率”和“可控性/可观测性”

## 推荐落地策略（适配 MCP Server）

### 策略 A：SDK 优先（推荐默认）

- MCP Server 内部直接用 SDK 发请求
- 外层统一封装：
  - token 获取与注入（Bot Token / OAuth2 access_token）
  - 速率限制（读/写/批量）
  - 重试退避（网络抖动/5xx/429）
  - 统一错误映射（转换为 MCP 可读错误）

### 策略 B：纯 HTTP + 类型生成（折中）

- 纯 HTTP 自己控制所有细节
- 同时从 OpenAPI 生成 TS 类型（只生成类型/模型，不生成客户端），兼顾可控性与类型安全

### 策略 C：纯 HTTP（极简）

- 只用 fetch/undici
- 快速原型阶段可用，但随着工具增多，维护成本会快速上升

## 选型建议（结合你的 4 项专注点）

- 你要做“渐进式读取块树”：SDK 的 `getBlockChildren()` + 类型定义非常省时间
- 你要做“登录与重新授权”：无论 SDK 还是 HTTP，都建议你自己实现 OAuth2（外部应用）与 token 持久化；SDK 负责“拿到 token 后的业务调用”

