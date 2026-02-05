# Blocks API（块）

更新时间：2026-02-05  
来源：https://flowus.cn/share/f1a96121-14f4-46ed-8500-132498017720

## 原文抓取

概述Blocks API 提供了类似 Notion 的块管理能力，包括获取、创建、更新和删除各种类型的内容块。支持段落、标题、列表、多媒体、布局等多种块类型，以及完整的颜色和格式化功能。基础信息API 版本复制基础 URL正式环境https://api.flowus.cn/v1测试环境https://api-test.allflow.cn/v1认证所有 API 请求都需要在 Authorization 头中包含有效的机器人令牌：Authorization: Bearer <bot_token>获取机器人令牌： 请参考 插件开发指南 了解如何创建集成应用和获取机器人访问令牌。1. 获取单个块获取指定块的详细信息。请求GET /v1/blocks/{block_id}路径参数block_id (string, 必填): 要获取的块ID响应示例{
  \"object\": \"block\",
  \"id\": \"550e8400-e29b-41d4-a716-446655440000\",
  \"parent\": {
    \"type\": \"block_id\",
    \"block_id\": \"550e8400-e29b-41d4-a716-446655440001\"
  },
  \"created_time\": \"2023-12-01T10:00:00.000Z\",
  \"created_by\": {
    \"object\": \"user\",
    \"id\": \"user-550e8400-e29b-41d4-a716-446655440000\"
  },
  \"last_edited_time\": \"2023-12-01T10:30:00.000Z\",
  \"last_edited_by\": {
    \"object\": \"user\",
    \"id\": \"user-550e8400-e29b-41d4-a716-446655440001\"
  },
  \"archived\": false,
  \"has_children\": true,
  \"type\": \"paragraph\",
  \"data\": {
    \"rich_text\": [
      {
        \"type\": \"text\",
        \"text\": {
          \"content\": \"这是一个段落块\",
          \"link\": null
        },
        \"annotations\": {
          \"bold\": false,
          \"italic\": false,
          \"strikethrough\": false,
          \"underline\": false,
          \"code\": false,
          \"color\": \"default\"
        },
        \"plain_text\": \"这是一个段落块\",
        \"href\": null
      }
    ],
    \"text_color\": \"default\",
    \"background_color\": \"default\"
  }
}2. 获取块的子块获取指定块的直接子块列表，支持分页。请求GET /v1/blocks/{block_id}/children路径参数block_id (string, 必填): 父块ID查询参数page_size (integer, 可选): 每页返回的块数量，取值范围 1-100，默认 50start_cursor (string, 可选): 分页游标，使用子块的ID作为游标值响应示例{
  \"object\": \"list\",
  \"results\": [
    {
      \"object\": \"block\",
      \"id\": \"550e8400-e29b-41d4-a716-446655440002\",
      \"type\": \"paragraph\",
      \"data\": {
        \"rich_text\": [
          {
            \"type\": \"text\",
            \"text\": {
              \"content\": \"子块内容\",
              \"link\": null
            }
          }
        ],
        \"text_color\": \"default\",
        \"background_color\": \"default\"
      }
    }
  ],
  \"next_cursor\": \"550e8400-e29b-41d4-a716-446655440002\",
  \"has_more\": true,
  \"type\": \"block\",
  \"block\": {}
}3. 追加子块向指定块追加一个或多个子块。请求PATCH /v1/blocks/{block_id}/children路径参数block_id (string, 必填): 父块ID请求体{
  \"children\": [
    {
      \"type\": \"paragraph\",
      \"data\": {
        \"rich_text\": [
          {
            \"type\": \"text\",
            \"text\": {
              \"content\": \"新段落内容\",
              \"link\": null
            },
            \"annotations\": {
              \"bold\": false,
              \"italic\": false,
              \"strikethrough\": false,
              \"underline\": false,
              \"code\": false,
              \"color\": \"default\"
            }
          }
        ],
        \"text_color\": \"blue\",
        \"background_color\": \"yellow\"
      }
    }
  ]
}限制单次最多创建 100 个子块每个子块必须指定有效的类型响应示例{
  \"object\": \"list\",
  \"results\": [
    {
      \"object\": \"block\",
      \"id\": \"550e8400-e29b-41d4-a716-446655440003\",
      \"type\": \"paragraph\",
      \"data\": {
        \"rich_text\": [
          {
            \"type\": \"text\",
            \"text\": {
              \"content\": \"新段落内容\",
              \"link\": null
            }
          }
        ],
        \"text_color\": \"blue\",
        \"background_color\": \"yellow\"
      }
    }
  ],
  \"next_cursor\": null,
  \"has_more\": false,
  \"type\": \"block\",
  \"block\": {}
}4. 更新块更新现有块的内容、类型或属性。请求PATCH /v1/blocks/{block_id}路径参数block_id (string, 必填): 要更新的块ID4.1 更新块内容请求体示例{
  \"data\": {
    \"rich_text\": [
      {
        \"type\": \"text\",
        \"text\": {
          \"content\": \"更新后的段落内容\",
          \"link\": null
        },
        \"annotations\": {
          \"bold\": true,
          \"italic\": false,
          \"strikethrough\": false,
          \"underline\": false,
          \"code\": false,
          \"color\": \"red\"
        }
      }
    ],
    \"text_color\": \"red\",
    \"background_color\": \"yellow\"
  }
}4.2 更改块类型请求体示例{
  \"type\": \"heading_1\",
  \"data\": {
    \"rich_text\": [
      {
        \"type\": \"text\",
        \"text\": {
          \"content\": \"现在是一级标题\",
          \"link\": null
        },
        \"annotations\": {
          \"bold\": true,
          \"color\": \"default\"
        }
      }
    ],
    \"text_color\": \"blue\",
    \"background_color\": \"default\"
  }
}4.3 归档块请求体示例{
  \"archived\": true
}响应示例{
  \"object\": \"block\",
  \"id\": \"550e8400-e29b-41d4-a716-446655440000\",
  \"type\": \"heading_1\",
  \"data\": {
    \"rich_text\": [
      {
        \"type\": \"text\",
        \"text\": {
          \"content\": \"现在是一级标题\",
          \"link\": null
        }
      }
    ],
    \"text_color\": \"blue\",
    \"background_color\": \"default\"
  }
}5. 删除块删除指定块及其所有子块。此操作不可逆。请求DELETE /v1/blocks/{block_id}路径参数block_id (string, 必填): 要删除的块ID响应示例{
  \"object\": \"block\",
  \"id\": \"550e8400-e29b-41d4-a716-446655440000\",
  \"deleted\": true
}支持的块类型FlowUs Blocks API 支持丰富的块类型，涵盖文本、媒体、布局等各种内容形式：块类型概览颜色支持所有文本类块类型都支持双层颜色系统：块级别颜色：text_color 和 background_color富文本级别颜色：annotations.color支持的颜色值：default, gray, brown, orange, yellow, green, blue, purple, pink, red富文本对象富文本对象用于表示格式化的文本内容，支持以下类型：支持的富文本类型格式化支持所有富文本类型都支持 annotations 格式化：样式：bold, italic, strikethrough, underline, code颜色：color (支持所有标准颜色值)链接：href 和 text.link使用示例创建复杂内容结构PATCH /v1/blocks/parent-block-id/children
Authorization: Bearer your_bot_token
Content-Type: application/json

{
  \"children\": [
    {
      \"type\": \"heading_1\",
      \"data\": {
        \"rich_text\": [
          {
            \"type\": \"text\",
            \"text\": {
              \"content\": \"项目文档\",
              \"link\": null
            },
            \"annotations\": {
              \"bold\": true,
              \"color\": \"blue\"
            }
          }
        ],
        \"text_color\": \"blue\",
        \"background_color\": \"default\"
      }
    },
    {
      \"type\": \"callout\",
      \"data\": {
        \"rich_text\": [
          {
            \"type\": \"text\",
            \"text\": {
              \"content\": \"这是一个重要提示，请仔细阅读！\",
              \"link\": null
            }
          }
        ],
        \"icon\": {
          \"emoji\": \"⚠️\"
        },
        \"text_color\": \"default\",
        \"background_color\": \"yellow\"
      }
    }
  ]
}更新块内容和颜色PATCH /v1/blocks/block-id
Authorization: Bearer your_bot_token
Content-Type: application/json

{
  \"data\": {
    \"rich_text\": [
      {
        \"type\": \"text\",
        \"text\": {
          \"content\": \"这是更新后的内容，\",
          \"link\": null
        },
        \"annotations\": {
          \"bold\": true,
          \"color\": \"red\"
        }
      }
    ],
    \"text_color\": \"default\",
    \"background_color\": \"yellow\"
  }
}错误处理HTTP 状态码错误响应格式{
  \"object\": \"error\",
  \"status\": 400,
  \"code\": \"validation_error\",
  \"message\": \"请求参数验证失败\",
  \"details\": {
    \"field\": \"children\",
    \"reason\": \"必须提供至少一个子块\"
  }
}API 限制请求限制单次创建块数量：最多100个子块富文本长度：单个富文本段落最大2000字符嵌套深度：块嵌套深度不超过50层分页大小：分页查询最大页面大小为100频率限制读取操作：每分钟1000次请求写入操作：每分钟100次请求批量操作：每分钟10次请求存储限制文件大小：单个文件最大100MB图片尺寸：最大20MB，推荐尺寸不超过4K总存储：根据空间套餐限制

