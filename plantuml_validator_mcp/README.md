# PlantUML Validator MCP Server

提供一个最小 MCP Server（stdio），暴露一个 tool：`plantuml_validate`，用于校验 PlantUML 语法。


todo 修复jar路径

## 配置参数

- PlantUML jar 包路径
  - 通过启动参数：`--plantuml-jar <path>`
  - 或环境变量：`PLANTUML_JAR_PATH=<path>`
  - 若两者都不提供，会尝试自动使用仓库内 `jars/plantuml-*.jar`

## Tool

- 名称：`plantuml_validate`
- 参数：
  - `code`：string（PlantUML 源码）
- 返回：
  - `errors`：string 数组（错误列表；无错误则为空）

## Trae MCP 配置示例（mcp.json）

```json
{
  "mcpServers": {
    "plantuml-validator": {
      "transport": "stdio",
      "command": "python",
      "args": [
        "D:/WorkSpace/personal/mcp-server/plantuml_validator_mcp/main.py",
        "--plantuml-jar",
        "D:/WorkSpace/personal/mcp-server/jars/plantuml-1.2026.1.jar"
      ],
      "cwd": "D:\\WorkSpace\\personal\\mcp-server",
      "env": {}
    }
  }
}
```

也可以不写 `--plantuml-jar`，改为配置环境变量：

```json
{
  "mcpServers": {
    "plantuml-validator": {
      "transport": "stdio",
      "command": "python",
      "args": ["D:/WorkSpace/personal/mcp-server/plantuml_validator_mcp/main.py"],
      "cwd": "D:\\WorkSpace\\personal\\mcp-server",
      "env": {
        "PLANTUML_JAR_PATH": "D:/WorkSpace/personal/mcp-server/jars/plantuml-1.2026.1.jar"
      }
    }
  }
}
```

如果 Trae 一直显示“准备中”，优先把 `command` 改成绝对路径的 python.exe（避免 PATH 差异），并在 `env` 里临时加上 `"MCP_DEBUG": "1"` 便于从 stderr 排查启动与握手问题。

