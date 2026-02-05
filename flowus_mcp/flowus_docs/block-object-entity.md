# 块对象实体（Block Object Entity）

更新时间：2026-02-05  
来源：https://flowus.cn/share/d3bab0b8-8533-4b7a-afce-ca78cdbf1d65

## 用途（自建 MCP Server）

当你把 FlowUs 页面内容通过 Blocks API 拉出来后，需要用“块类型 -> data 结构”的规则去解析/渲染/转 Markdown/做索引。本页主要就是这个“类型与字段”的规范。

## 要点摘录

- 块对象通用字段：`object`、`id`、`parent`、`created_time`、`last_edited_time`、`archived`、`has_children`、`type`、`data`
- 常见文本块：`paragraph`、`heading_1/2/3`、`bulleted_list_item`、`numbered_list_item`、`to_do`、`quote`、`toggle`
- 常见媒体块：`code`、`image`、`file`、`bookmark`、`embed`
- 特殊块：`callout`、`equation`、`link_to_page`、`template`、`synced_block`
- 布局块：`divider`、`column_list`、`column`、`table`、`table_row`
- 子对象：`child_page`、`child_database`
- RichText 支持 `text` / `mention` / `equation`，并带 `annotations`（bold/italic/underline/code/color 等）

## 建议落地方式

- MCP 侧把块树转换为 Markdown：按 `type` 映射成 Markdown 语法（标题/列表/代码块/引用/图片链接等），RichText 做行内样式
- 索引侧以“块”为基本粒度：每个块保存 `block_id`、`page_id`、`type`、`plain_text`，便于增量更新与定位引用

