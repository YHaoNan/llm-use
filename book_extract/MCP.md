# MCP Server（book-extract）

book-extract 的 MCP Server 采用 stdio 方式运行，仅提供一个工具：`convert`。

## 启动
```bash
python -m book_extract --mode mcp
```

如果你要在 MCP 客户端里配置（示例，按你的客户端格式调整）：
```json
{
  "command": "python",
  "args": ["-m", "book_extract", "--mode", "mcp"]
}
```

使用绝对路径启动脚本（更稳，避免工作目录/包导入差异）：
```json
{
  "command": "python",
  "args": ["D:\\WorkSpace\\personal\\llm-use\\book_extract\\main.py", "--mode", "mcp"]
}
```

如果你的 MCP 客户端支持设置工作目录/环境变量，也推荐显式指定（进一步避免导入问题）：
```json
{
  "command": "python",
  "args": ["D:\\WorkSpace\\personal\\llm-use\\book_extract\\main.py", "--mode", "mcp"],
  "cwd": "D:\\WorkSpace\\personal\\llm-use",
  "env": {
    "PYTHONPATH": "D:\\WorkSpace\\personal\\llm-use"
  }
}
```

## 工具：convert
### 入参
```json
{
  "input_path": "D:\\path\\book.epub",
  "output_dir": "D:\\path\\out",
  "overwrite": true
}
```

### 返回结构（统一结构体）
工具返回的 `content[0].text` 是一个 JSON 字符串，结构如下：

成功：
```json
{
  "ok": true,
  "result": {
    "output_dir": "D:\\path\\out",
    "index_path": "D:\\path\\out\\chapter-index.json",
    "source_type": "epub",
    "chapters_count": 69,
    "chapters": [
      {"id": "ch_0001", "path": "chapters/0001-xxx.md", "title": "...", "level": 1}
    ],
    "warnings": []
  }
}
```

失败：
```json
{
  "ok": false,
  "error": {
    "code": "unsupported_format",
    "message": "不支持的文档类型：.pdf",
    "details": {
      "input_path": "D:\\path\\book.pdf",
      "extension": ".pdf"
    }
  }
}
```

说明：
- `error.code` 为稳定字段，便于客户端分支处理
- `error.details` 仅用于辅助定位问题（可选）
