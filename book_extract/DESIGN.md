# Book Extract 设计文档（Core + MCP）

## 目标与边界
- 目标：将 epub、mobi、pdf 等常见文档转换为“LLM 友好的 Markdown 文档集”，并生成章节索引，输出结构与 [README.md](file:///d:/WorkSpace/personal/llm-use/book_extract/README.md) 一致。
- 边界：核心与 MCP 包装只约定输入/输出与错误语义；具体格式解析由各个 DocumentSource 实现（当前内置 epub）。
- 可包装为 MCP：核心逻辑以纯函数/类方法形式提供，输入输出使用可 JSON 序列化的数据结构，异常语义清晰，便于 MCP 工具层映射为结构化错误。

## 输出产物规范
输出目录（用户指定 output_dir）下生成：
```
chapter-index.json
images/
chapters/
```

### chapters/*.md
- 每个章节一个 Markdown 文件（文件名由 DocumentSource 决定或由框架辅助生成）。
- 框架不对 Markdown 内容做强约束，但提供可选的标准化能力（例如统一 frontmatter 或标题层级），后续可扩展。

### images/*
- 章节引用的图片等资源统一放到 images/ 下。
- 资源命名建议可复现且去重（如基于内容 hash），由框架提供工具方法，具体策略可选。

### chapter-index.json
建议的 JSON schema（便于 LLM 或上层消费）：
```json
{
  "version": 1,
  "source": {
    "input_path": "D:/.../book.epub",
    "detected_type": "epub"
  },
  "generated_at": "2026-02-06T12:34:56Z",
  "chapters": [
    {
      "id": "ch_0001",
      "title": "Chapter 1",
      "path": "chapters/chapter1.md",
      "level": 1,
      "parent_id": null,
      "source_ref": null
    }
  ]
}
```

说明：
- `version`：索引版本，便于未来升级兼容。
- `chapters[]` 的列表顺序即章节顺序，不额外提供 `order` 字段。
- `chapters[].path`：相对 output_dir 的路径，便于搬运目录。
- `source_ref`：可选，用于保留“源文档定位信息”（例如 epub spine id、pdf 页码范围等），框架不解释其内容。

## 核心抽象

### DocumentSource：格式适配器接口
每种文档格式实现一个 DocumentSource。框架只依赖接口，不关心实现细节（可解压、可解析二进制、可调用 AI/OCR 等）。

建议接口形态（用 typing.Protocol 或 abc.ABC 表达）：
- `type: str`：该 source 的类型名（如 `"epub"`）。
- `supported_extensions: tuple[str, ...]`：支持的文件后缀（如 `(".epub",)`，统一小写带点）。
- `can_handle(input_path: Path) -> bool`（可选）：更复杂的探测（例如 mobi/azw 混杂、或者根据魔数判断）。
- `convert(request: ConvertRequest, workspace: OutputWorkspace) -> SourceConvertResult`

#### ConvertRequest（通用参数）
以 dataclass 表达，确保可序列化与可测试：
- `input_path: Path`
- `output_dir: Path`
- `options: ConvertOptions`

#### ConvertOptions（通用选项）
只放“跨格式通用”的选项，避免污染接口；格式特有参数后续通过 `options.extra: dict[str, Any]` 承载（同时保持框架不理解它）。
建议字段：
- `overwrite: bool = False`：output_dir 已存在时是否覆盖。
- `language: str | None = None`：提示语言/分词/标题生成等（可选）。
- `max_image_width: int | None = None`：可选的图片处理上限（框架提供工具，source 可用可不用）。
- `extra: dict[str, object] = {}`：格式特有参数透传。

### OutputWorkspace：输出写入的统一门面
为了解耦“写文件/建目录/资源命名/索引生成”，框架提供一个 workspace，DocumentSource 只调用 workspace 的方法，不直接操作 output_dir（但不强制禁止）。

建议能力：
- `init_layout()`：创建 `chapters/`、`images/`，准备写入。
- `write_chapter(slug: str, title: str | None, markdown: str) -> ChapterRef`
- `write_image(filename: str, content: bytes, media_type: str | None) -> str`（返回相对路径，如 `images/image01.png`）
- `finalize_index(chapters: list[ChapterRef]) -> Path`

好处：
- 框架能统一生成 chapter-index.json。
- 便于未来切换到内存输出、对象存储、或 MCP 以 base64 形式回传等。

### ConvertResult：统一返回值
建议最小集（可 JSON 化）：
- `output_dir: Path`
- `index_path: Path`（即 chapter-index.json）
- `chapters: list[ChapterRef]`
- `warnings: list[str]`（非致命问题）
- `source_type: str`

## 调度与注册机制

### SourceRegistry：后缀到 DocumentSource 的映射
核心功能：根据 `input_path.suffix.lower()` 决定使用哪个 source。

设计要点：
- 默认使用后缀映射：`.epub`、`.mobi`、`.pdf` 等。
- 支持一个后缀映射多个 source（按优先级或按 `can_handle` 进一步判断），为未来兼容魔数识别、同后缀多格式留出空间。
- registry 既支持“代码内注册”（后续在包初始化时注册），也支持未来的“插件发现”（例如 Python entry points），但本阶段只实现前者，保留扩展点。

### Converter（门面/入口）
提供一个稳定入口，未来 MCP 直接调用它：
- `convert(input_path: str|Path, output_dir: str|Path, options: ConvertOptions|None = None) -> ConvertResult`

Converter 的职责：
- 规范化与校验输入路径、输出路径（Path 解析、存在性、权限、覆盖策略）。
- 选择 DocumentSource（registry）。
- 创建 workspace、调用 `source.convert()`。
- 做后置校验：确保索引存在、章节列表与文件存在（可作为框架“契约”）。

## 统一异常语义
为 MCP 包装友好，异常需要分层且稳定：
- `BookExtractError`：所有框架异常基类（便于捕获与映射）。
- `InvalidInputError`：输入文件不存在/不可读/路径非法。
- `UnsupportedFormatError`：无法根据后缀（或探测）找到 source。
- `OutputConflictError`：输出目录冲突且 `overwrite=False`。
- `ConversionError`：source 转换失败（可包含 `cause` 与可序列化的 `details`）。

建议每个异常包含：
- `message: str`
- `code: str`（例如 `"unsupported_format"`，利于上层做分支处理）
- `details: dict[str, object] | None`（可选）

## 模块化与 import 策略（避免“任意目录访问”问题）
建议将核心逻辑实现为可安装的 Python 包，采用绝对导入，避免相对路径运行失败：
```
book_extract/
  pyproject.toml（后续补）
  book_extract/
    __init__.py
    converter.py
    registry.py
    sources/
      __init__.py
      base.py
    workspace.py
    models.py
    errors.py
```

关键原则：
- 入口只依赖包内绝对导入：`from book_extract.converter import convert`
- 所有路径处理使用 `pathlib.Path`，不依赖当前工作目录。
- 不在 import 时做 IO（避免 MCP 环境加载时副作用）。

## 未来扩展点（本阶段只预留）
- 插件化：通过 entry points 自动发现第三方 DocumentSource。
- AI/OCR：对图片 PDF/扫描版文档，source 内部可调用外部服务；框架只承诺异常与输出契约。
- 并行化：章节级并发写入与资源去重（workspace 提供线程安全策略）。
- 质量控制：可选的 Markdown 规范化、章节拆分策略、锚点提取、去噪等。

## 最小可交付（MVP）清单（本阶段）
- 定义数据模型（request/options/result、chapter 引用）。
- 定义异常体系。
- 定义 DocumentSource 接口（抽象类/协议）。
- 实现 SourceRegistry（按后缀选择）。
- 实现 Converter + OutputWorkspace（只提供写入/索引生成能力）。
- 内置至少一个可用 source（目前为 epub）。

## 代码结构（当前实现）
```
book_extract/
  __init__.py
  __main__.py
  main.py              # 统一入口：--mode raw|mcp
  requirements.txt
  core/
    __init__.py
    converter.py
    registry.py
    workspace.py
    models.py
    errors.py
    sources/
      __init__.py
      base.py
      epub.py
  mcp/
    __init__.py
    server.py          # MCP Server，仅提供 convert 工具
```

## 入口与运行模式
- raw 模式：命令行指定输入/输出，输出 JSON（成功/失败结构体）。
- mcp 模式：stdio MCP Server，仅提供 convert 工具，失败原因通过结构化 error 返回。

