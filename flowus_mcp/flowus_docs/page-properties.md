# Page Properties（页面/记录属性规范）

更新时间：2026-02-05  
来源：https://flowus.cn/share/7643e0f0-5e47-4db8-ba72-41f430533edf

## 原文抓取

概述Page Properties 定义了页面和数据库记录的属性格式。本文档详细说明了不同类型属性的数据结构、使用方法和格式要求。页面属性广泛应用于：页面标题：普通页面的标题属性数据库记录：多维表中记录的各种属性页面元数据：图标、封面、创建时间等基础概念属性对象结构每个属性对象都包含以下基本字段：{
  "属性名称": {
    "id": "属性UUID",
    "type": "属性类型",
    "属性类型": "属性值"
  }
}字段说明：属性名称：用户可读的属性名称，作为对象的keyid：属性的唯一标识符（UUID）type：属性类型，定义了数据的格式和行为属性类型：与type字段相同的key，包含实际的属性值支持的属性类型FlowUs 支持 15 种不同的属性类型，涵盖了从基础数据到复杂关联的所有需求：基础属性类型title - 标题属性rich_text - 富文本属性number - 数字属性checkbox - 复选框属性url - 链接属性email - 邮箱属性phone_number - 电话属性选择属性类型select - 单选下拉框multi_select - 多选下拉框时间和人员属性date - 日期时间属性people - 人员属性文件和关联属性files - 文件附件属性relation - 数据库关联属性计算属性类型（只读）formula - 公式计算属性1. 标题属性 (title)页面和数据库记录的主标题。API格式：{
  "标题": {
    "id": "title",
    "type": "title",
    "title": [
      {
        "type": "text",
        "text": {
          "content": "页面标题内容",
          "link": null
        },
        "annotations": {
          "bold": false,
          "italic": false,
          "strikethrough": false,
          "underline": false,
          "code": false,
          "color": "default"
        },
        "plain_text": "页面标题内容",
        "href": null
      }
    ]
  }
}创建/更新时的简化格式：{
  "标题": {
    "type": "title",
    "title": [
      {
        "text": {
          "content": "页面标题内容"
        }
      }
    ]
  }
}2. 富文本属性 (rich_text)支持格式化的文本内容。API格式：{
  "描述": {
    "id": "property-uuid",
    "type": "rich_text",
    "rich_text": [
      {
        "type": "text",
        "text": {
          "content": "这是一段富文本",
          "link": null
        },
        "annotations": {
          "bold": true,
          "italic": false,
          "strikethrough": false,
          "underline": false,
          "code": false,
          "color": "blue"
        },
        "plain_text": "这是一段富文本",
        "href": null
      }
    ]
  }
}创建/更新时的格式：{
  "描述": {
    "type": "rich_text",
    "rich_text": [
      {
        "text": {
          "content": "这是一段富文本"
        }
      }
    ]
  }
}3. 数字属性 (number)数值类型的属性。API格式：{
  "价格": {
    "id": "price-uuid",
    "type": "number",
    "number": 99.99
  }
}创建/更新时的格式：{
  "价格": {
    "type": "number",
    "number": 99.99
  }
}4. 选择属性 (select)单选下拉框属性。API格式：{
  "状态": {
    "id": "status-uuid",
    "type": "select",
    "select": {
      "id": "option-uuid",
      "name": "进行中",
      "color": "yellow"
    }
  }
}创建/更新时的格式：{
  "状态": {
    "type": "select",
    "select": {
      "name": "进行中"
    }
  }
}5. 多选属性 (multi_select)多选下拉框属性。API格式：{
  "标签": {
    "id": "tags-uuid",
    "type": "multi_select",
    "multi_select": [
      {
        "id": "tag1-uuid",
        "name": "重要",
        "color": "red"
      },
      {
        "id": "tag2-uuid",
        "name": "紧急",
        "color": "orange"
      }
    ]
  }
}创建/更新时的格式：{
  "标签": {
    "type": "multi_select",
    "multi_select": [
      {
        "name": "重要"
      },
      {
        "name": "紧急"
      }
    ]
  }
}6. 复选框属性 (checkbox)布尔值属性。API格式：{
  "完成": {
    "id": "completed-uuid",
    "type": "checkbox",
    "checkbox": true
  }
}创建/更新时的格式：{
  "完成": {
    "type": "checkbox",
    "checkbox": true
  }
}7. 日期属性 (date)日期和时间属性。API格式：{
  "截止日期": {
    "id": "due-date-uuid",
    "type": "date",
    "date": {
      "start": "2024-01-15T10:30:00",
      "end": "2024-01-16T18:00:00",
      "time_zone": null
    }
  }
}创建/更新时的格式：{
  "截止日期": {
    "type": "date",
    "date": {
      "start": "2024-01-15T10:30:00",
      "end": "2024-01-16T18:00:00"
    }
  }
}8. 人员属性 (people)用户引用属性。API格式：{
  "负责人": {
    "id": "assignee-uuid",
    "type": "people",
    "people": [
      {
        "object": "user",
        "id": "user-uuid"
      }
    ]
  }
}9. 文件属性 (files)文件附件属性。API格式：{
  "附件": {
    "id": "files-uuid",
    "type": "files",
    "files": [
      {
        "name": "文档.pdf",
        "type": "external",
        "external": {
          "url": "https://example.com/document.pdf"
        }
      }
    ]
  }
}10. 链接属性 (url)URL链接属性。11. 邮箱属性 (email)。12. 电话属性 (phone_number)。13. 关联属性 (relation)。14. 公式属性 (formula)（只读）。系统属性（只读）：created_time/created_by/last_edited_time/last_edited_by。更多示例、验证规则与错误示例见原文全文。
