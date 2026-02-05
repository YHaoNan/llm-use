# 鉴权与集成（Internal Plugin / External Application）

更新时间：2026-02-05  
来源：https://flowus.cn/share/07168d83-cb08-4ab8-ab73-74fe915054b1

## 两种集成模式怎么选

- 内部插件（Internal Plugin）
  - 更像“你给自己空间写的内置工具”
  - 授权链路更短：应用内创建机器人并授权页面
  - 适合：自用 MCP Server、企业内网自动化、无需给外部用户分发
- 外部应用（External Application）
  - 标准 OAuth2 授权码流程
  - 适合：要让“其他 FlowUs 用户”在你的系统里授权后使用（多租户）

## 外部应用 OAuth2（授权码换 token）

文档给出的端点：

- `GET https://api.flowus.cn/oauth/authorize`
- `GET https://api.flowus.cn/oauth/authorize/info`
- `POST https://api.flowus.cn/oauth/token`

换到 token 后，后续调用统一使用：

`Authorization: Bearer <access_token>`

## 机器人 token（Bot Token）

文档描述为“机器人访问令牌/机器人 Token”。后续调用统一使用：

`Authorization: Bearer <bot_token>`

Base URL（v1）：

- 正式：`https://api.flowus.cn/v1`
- 测试：`https://api-test.allflow.cn/v1`

## 权限（Capabilities）

从 API 文档的错误示例可以看到常见能力名称（典型用于拒绝原因）：

- `readContent`
- `insertContent`
- `updateContent`

建议在自建 MCP Server 侧做“工具级最小权限”设计：只申请你 MCP 工具会用到的能力，并且只授权必要页面/数据库。

## 原文抓取（便于离线检索）

概述FlowUs 插件开发系统提供了完整的API接口，允许开发者创建功能丰富的插件来扩展FlowUs的功能。本指南将带您了解从零开始开发插件的完整流程。插件类型FlowUs 支持两种不同类型的集成应用，分别适用于不同的开发场景和用户体验需求：1. 内部插件 (Internal Plugin)嵌入式UI：插件界面直接嵌入在 FlowUs 应用内部无缝集成：用户在 FlowUs 内完成所有操作，无需跳转简化授权：用户在应用内直接选择要授权的页面适用场景：FlowUs 官方插件、企业内部工具技术特性：无需配置 redirectUris直接API调用操作内容简化授权流程，一步完成机器人创建和授权2. 外部应用 (External Application)独立应用：第三方开发的独立应用程序标准OAuth2：遵循OAuth2.0授权码流程跨平台集成：可以在任何平台上开发和部署适用场景：第三方开发者工具、SaaS服务集成类型对比表特性内部插件 (internal)外部应用 (external)spaceId必填不需要redirectUris可选（通常为空）必填如何选择类型？选择内部插件的情况：开发 FlowUs 官方功能扩展企业内部工具，不需要对外发布希望提供无缝的用户体验不需要复杂的OAuth流程选择外部应用的情况：第三方开发者工具需要在多个平台集成的SaaS服务独立的应用程序需要遵循标准OAuth2流程的场景核心概念集成应用 (Integration)插件的基础配置和身份标识定义插件的基本信息（名称、描述、图标等）配置OAuth回调地址（公共插件需要）设置机器人能力权限开发流程第一步：创建集成应用开发者中心主要是提供了一些flowus的api给有开发能力的用户使用，入口在空间设置里。集成应用主要分2种：插件内应用：开发者用于自己空间页面，比如想用api对对某个页面进行编辑，就可以创建应用插件。外部应用：开发者给其他flowus用户使用，比如开发者有一个新闻类网站，希望支持用户把某条新闻同步到flowus，就可以创建外部应用，用户授权后就有相应的权限进行读写。外部应用需要填写自己的网站地址以及callback地址，跟常规网站授权流程差不多。授权后会访问callback地址并且带上可访问用户数据的code。第二步：应用授权（根据应用类型选择）内部插件开发流程内部插件的UI嵌入在FlowUs应用内，创建时直接创建机器人，无需额外的授权步骤。外部应用开发流程外部应用是独立的第三方应用，用户在外部应用中操作，通过标准的 OAuth2.0 授权码流程获取权限访问授权URL通过访问授权url进入授权页面,选择授权页面后自动跳转调用外部插件配置的重定向URI重定向URI的接口中用户要添加交换访问令牌逻辑typescript demo 代码如下// 在回调页面处理授权码
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

const { access_token } = await tokenResponse.json();完整示例代码创建页面// 使用访问令牌调用API
const page = await fetch('https://api.flowus.cn/v1/pages', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    parent: { database_id: 'database-uuid' },
    properties: {
      '标题': {
        type: 'title',
        title: [{ text: { content: '外部应用创建的任务' } }]
      }
    }
  })
});API 接口总览OAuth2 授权 API（外部应用）GET /oauth/authorize - 启动OAuth2授权流程GET /oauth/authorize/info - 获取授权页面信息POST /oauth/token - 交换访问令牌API (v1)POST /v1/pages - 创建页面/记录GET /v1/blocks/{blockId} - 获取单个块GET /v1/blocks/{blockId}/children - 获取块的子块（基于 subNodes 分页）PATCH /v1/blocks/{blockId}/children - 追加子块到指定块PATCH /v1/blocks/{blockId} - 更新块DELETE /v1/blocks/{blockId} - 删除块分页特性： 子块获取API使用基于父块 subNodes 字段的分页机制，保持用户设置的块顺序，游标格式为简单的块ID。机器人API详细说明认证所有 API 请求都需要在 HTTP 头中包含 Bearer Token：Authorization: Bearer your_bot_token_here基础 URL正式环境https://api.flowus.cn/v1创建页面创建一个新的页面或多维表记录。POST /v1/pages请求体：{  "parent": {    "database_id": "d9824bdc-8445-4327-be8b-5b47500af6ce"  },  "icon": {    "emoji": "📝"  },  "cover": {    "external": {      "url": "https://example.com/cover.jpg"    }  },  "properties": {    "标题": {      "type": "title",      "title": [        {          "text": {            "content": "新页面标题"          }        }      ]    },    "描述": {      "type": "text",      "text": [        {          "text": {            "content": "页面描述"          }        }      ]    },    "状态": {      "type": "select",      "select": {        "name": "进行中"      }    },    "价格": {      "type": "number",      "number": 99.99    }  }}支持的属性类型：标题属性：{  "标题": {    "type": "title",    "title": [      {        "type": "text",        "text": {          "content": "页面标题"        }      }    ]  }}文本属性：{  "描述": {    "type": "text",     "text": [      {        "type": "text",        "text": {          "content": "这是一段描述文本"        }      }    ]  }}选择属性：{  "状态": {    "type": "select",    "select": {      "name": "进行中"    }  }}数字属性：{  "价格": {    "type": "number",    "number": 99.99  }}权限系统页面权限管理机器人只能访问被明确授权的页面支持动态添加/移除页面权限权限检查在每次API调用时进行错误处理常见错误码错误响应格式{  "object": "error",  "status": 400,  "code": "validation_error",  "message": "请求参数验证失败"}说明:object: 固定为 "error"status: HTTP状态码code: 错误类型代码message: 详细错误信息

