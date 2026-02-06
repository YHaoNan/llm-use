# Book Extract

Book Extract 将书籍转换成 LLM 友好的 Markdown 文档集，并提供 MCP Server（stdio）对外暴露 `convert` 工具（当前内置仅支持 epub）。

## 输出结构
```
chapter-index.json
images/
|-- image01.png
chapters/
|-- chapter1.md
|-- chapter1.1.md
|-- chapter1.2.md
|-- chapter2.md
|-- ...
```

说明：
- `chapters/`：每个章节一个 Markdown 文件
- `images/`：章节引用的图片资源
- `chapter-index.json`：章节索引（`chapters[]` 的列表顺序即章节顺序）

## 安装依赖
项目内依赖清单在 [requirements.txt](file:///d:/WorkSpace/personal/llm-use/book_extract/requirements.txt)。

```bash
python -m pip install -r book_extract/requirements.txt
```

## 使用（Python API）
```python
from book_extract.core import ConvertOptions, Converter, EpubSource, SourceRegistry

registry = SourceRegistry()
registry.register(EpubSource())

result = Converter(registry=registry).convert(
    input_path=r"D:\path\book.epub",
    output_dir=r"D:\path\out",
    options=ConvertOptions(overwrite=True),
)
print(result.index_path)
```

## 使用（raw 模式）
raw 模式是命令行裸启动：读取输入文件，写入输出目录，并在 stdout 输出一个 JSON 结构体（成功/失败）。

```bash
python -m book_extract --mode raw --input "D:\path\book.epub" --output "D:\path\out" --overwrite
```

成功输出示例：
```json
{
  "ok": true,
  "result": {
    "output_dir": "D:\\path\\out",
    "index_path": "D:\\path\\out\\chapter-index.json",
    "source_type": "epub",
    "chapters_count": 69,
    "warnings": []
  }
}
```

失败输出示例：
```json
{
  "ok": false,
  "error": {
    "message": "不支持的文档类型：.pdf",
    "code": "unsupported_format",
    "details": {
      "input_path": "D:\\path\\book.pdf",
      "extension": ".pdf"
    }
  }
}
```

## 使用（MCP Server 模式）
MCP Server 通过 stdio 提供工具调用，仅暴露一个工具：`convert`。

启动：
```bash
python -m book_extract --mode mcp
```

### 工具：convert
输入参数：
- `input_path`：源文件路径（字符串）
- `output_dir`：目标输出目录（字符串）
- `overwrite`：是否覆盖输出目录（布尔，可选，默认 false）

返回（工具文本内容是一个 JSON 字符串）：
- 成功：`{"ok": true, "result": {...}}`
- 失败：`{"ok": false, "error": {"code": "...", "message": "...", "details": {...}}}`

其中 `result` 至少包含：
- `output_dir` / `index_path` / `source_type` / `chapters_count` / `chapters` / `warnings`

## 代码结构
- core：核心转换框架与内置 sources（当前内置 epub）
- mcp：MCP Server 包装层（stdio）

## 扩展：新增 DocumentSource
实现接口见 [base.py](file:///d:/WorkSpace/personal/llm-use/book_extract/core/sources/base.py)：
- `type`：source 类型名（写入索引 `source.detected_type`）
- `supported_extensions`：支持的后缀（用于 registry 路由）
- `convert(request, workspace)`：读取源文件并调用 `workspace.write_chapter/write_image` 写入输出
