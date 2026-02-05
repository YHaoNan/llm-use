# User API（机器人用户）

更新时间：2026-02-05  
来源：https://flowus.cn/share/7947314f-fac8-441e-9753-6b417452bbeb

## 原文抓取

概述机器人用户 API 提供了获取机器人创建者信息的功能。这些API允许机器人了解创建它的用户信息。认证所有 API 请求都需要在 HTTP 头中包含机器人的 Bearer Token：复制获取机器人创建者信息获取当前机器人的创建者用户信息。请求GET /v1/users/me权限要求机器人需要具备 readContent 能力响应成功响应 (200 OK):{  "object": "user",  "id": "875bb809-eab6-467f-80d9-a7de6899d885",  "type": "person",  "person": {    "email": "user@example.com"  },  "name": "张三",  "avatar_url": "https://cdn2.flowus.cn/avatar123.jpg"}错误响应401 Unauthorized - 认证失败:{  "error": {    "code": "unauthorized",    "message": "缺少Authorization header"  }}403 Forbidden - 权限不足:{  "error": {    "code": "forbidden",     "message": "机器人没有readContent权限"  }}404 Not Found - 创建者不存在:{  "error": {    "code": "not_found",    "message": "机器人创建者不存在"  }}

