# Search API（搜索）

更新时间：2026-02-05  
来源：https://flowus.cn/share/114cd617-8202-492b-b3f9-6fdb717cb4f7

## 原文抓取

概述搜索 API 允许机器人在其授权的页面范围内进行智能搜索。该接口支持全文搜索和语义搜索，返回相关的页面结果。接口详情搜索页面在机器人授权的页面范围内搜索相关内容。请求方式： POST /v1/search请求头：复制请求参数：参数类型必填描述默认值querystring否搜索关键词""start_cursorstring否分页游标，用于获取下一页结果-page_sizenumber否每页返回的结果数量，范围 1-10010请求示例：{  "query": "项目计划",  "start_cursor": "eyJvZmZzZXQiOjEwfQ==",  "page_size": 20}响应格式：{  "object": "list",  "results": [    {      "object": "page",      "id": "a1b2c3d4-5678-9012-3456-789012345678",      "created_time": "2024-01-01T10:00:00.000Z",      "last_edited_time": "2024-01-15T14:30:00.000Z",      "parent": {        "type": "database_id",        "database_id": "d9824bdc-8445-4327-be8b-5b47500af6ce"      },      "archived": false,      "properties": {        "title": {          "type": "title",          "title": [            {              "type": "text",              "text": {                "content": "项目计划文档"              }            }          ]        }      }    }  ],  "next_cursor": "eyJvZmZzZXQiOjIwfQ==",  "has_more": true}搜索行为搜索范围搜索仅限于机器人已授权访问的页面包括页面标题和页面内容支持模糊匹配和语义搜索搜索结果排序默认按相关性排序相关性相同时按最后编辑时间降序排列分页机制使用 Base64 编码的 JSON 游标进行分页游标包含偏移量信息：{"offset": 20}最大页面大小为 100 项权限要求机器人必须具有 readContent 权限只能搜索机器人已授权访问的页面搜索结果会自动过滤掉无权限访问的页面

