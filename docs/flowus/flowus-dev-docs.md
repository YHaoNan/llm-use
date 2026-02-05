# FlowUs 开发者文档（本地备份）

更新时间：2026-02-05  
来源入口：https://flowus.cn/share/df7cd54f-1c21-4fc1-9fd8-ce81be1918a5

> 说明：此文件为对公开开发者文档页面的抓取备份，便于后续离线检索与二次探索。文档处于 Beta 阶段，部分链接可能会失效或内容变动。

## 目录

- MCP 接入
- 插件/外部应用与鉴权（OAuth2 / Bot Token）
- API 参考
  - Database（多维表）
  - Pages（页面）
  - Page Properties（页面/记录属性）
  - Blocks（块）
  - Block Object Entity（块对象实体）
  - User
  - Search
- 更新日志

## MCP 接入

文档中给出的 MCP 访问地址（token 为“授权码”）：

- Streamable HTTP：`https://mcp.allflow.cn/message?token=授权码`
- SSE：`https://mcp.allflow.cn/sse?token=授权码`

## 插件/外部应用与鉴权（OAuth2 / Bot Token）

来源：https://flowus.cn/share/07168d83-cb08-4ab8-ab73-74fe915054b1

### 插件类型

- 内部插件（Internal Plugin）
  - UI 嵌入在 FlowUs 内
  - 授权简化：应用内直接选择要授权的页面
  - 技术特性：无需配置 redirectUris；直接 API 调用；一步完成机器人创建与授权
- 外部应用（External Application）
  - 独立第三方应用
  - 标准 OAuth2.0 授权码流程
  - 适合对外提供能力（SaaS / 多用户）

### OAuth2 授权 API（外部应用）

- `GET /oauth/authorize`：启动 OAuth2 授权流程
- `GET /oauth/authorize/info`：获取授权页面信息
- `POST /oauth/token`：交换访问令牌

示例（文档原文片段）：

```ts
// 在回调页面处理授权码
const urlParams = new URLSearchParams(window.location.search);
const code = urlParams.get('code');
const state = urlParams.get('state');

// 第三方应用交换访问令牌
const tokenResponse = await fetch('https://api.flowus.cn/oauth/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    grant_type: 'authorization_code',
    code: code,
    client_id: integration.id,
    client_secret: integration.secret,
    redirect_uri: 'https://my-plugin.com/callback'
  })
});

const { access_token } = await tokenResponse.json();
```

### 机器人 API（v1）

认证方式（文档原文）：所有 API 请求都需要在 HTTP 头中包含 Bearer Token：

`Authorization: Bearer <your_bot_token_here>`

基础 URL：

- 正式环境：`https://api.flowus.cn/v1`
- 测试环境：`https://api-test.allflow.cn/v1`

## API 参考

### Database API（多维表）

来源：https://flowus.cn/share/fb8da20c-be08-4e1c-b136-f2706e43ca0c

能力概述：

- 创建数据库：`POST /v1/databases`
- 获取数据库：`GET /v1/databases/{database_id}`
- 查询数据库：`POST /v1/databases/{database_id}/query`
- 更新数据库：`PATCH /v1/databases/{database_id}`

重要限制（文档原文）：

- 每个数据库最多 100 个属性
- 查询每页最多 100 条记录
- 单选/多选选项数量限制 100 个
- Formula 属性主要支持读取（创建/更新有一定限制）

### Pages API（页面）

来源：https://flowus.cn/share/2ae7e334-147f-4eae-b318-10aa1d19804a

能力概述：

- 创建页面：`POST /v1/pages`（支持在页面或数据库下创建）
- 获取页面：`GET /v1/pages/{page_id}`
- 更新页面：`PATCH /v1/pages/{page_id}`
- 获取页面子块：通过 Blocks 子块接口（页面也是一种块）

文档提到的创建容错机制：

- parent 不指定：创建到默认位置
- parent 指定但不存在：也会创建到默认位置（保证创建成功）

### Page Properties（页面/记录属性）

来源：https://flowus.cn/share/7643e0f0-5e47-4db8-ba72-41f430533edf

关键格式特性：

- API 使用“用户可读的属性名称”作为 properties 的 key（而非 UUID）
- title / rich_text 使用富文本数组结构
- date 遵循 ISO 8601

### Blocks API（块）

来源：https://flowus.cn/share/f1a96121-14f4-46ed-8500-132498017720

能力概述：

- 获取单个块：`GET /v1/blocks/{block_id}`
- 获取子块：`GET /v1/blocks/{block_id}/children`
- 追加子块：`PATCH /v1/blocks/{block_id}/children`（单次最多 100 个子块）
- 更新块：`PATCH /v1/blocks/{block_id}`
- 删除块：`DELETE /v1/blocks/{block_id}`

频率限制（文档原文）：

- 读取：每分钟 1000 次
- 写入：每分钟 100 次
- 批量：每分钟 10 次

### Block Object Entity（块对象实体）

来源：https://flowus.cn/share/d3bab0b8-8533-4b7a-afce-ca78cdbf1d65

### User API

来源：https://flowus.cn/share/7947314f-fac8-441e-9753-6b417452bbeb

- 获取机器人创建者信息：`GET /v1/users/me`
- 权限要求：需要 `readContent`

### Search API

来源：https://flowus.cn/share/114cd617-8202-492b-b3f9-6fdb717cb4f7

- 搜索：`POST /v1/search`
- 搜索范围：仅限机器人已授权访问的页面
- 分页：Base64 编码 JSON 游标（包含 offset），page_size 1-100

## 更新日志

来源：https://flowus.cn/share/b30dd458-7fb9-4e29-b5ed-e09274465c34

节选：

- 2025-09-29：新增「支持 API 访问/修改数据（开发者中心）」等
- 2026-01-29：修复若干问题，增加英文/日文支持

## 失效链接记录

- Cursor 配置：https://flowus.cn/share/c98e5d0c-17fd-4d9d-a436-f8f67155ecb3 （抓取时显示“页面不存在/回收站或删除”）

