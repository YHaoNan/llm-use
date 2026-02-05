import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { FlowUsAuthManager } from "./auth.js";
import { createFlowUsApi, searchFlowUs } from "./flowus.js";

const SearchArgsSchema = z.object({
  query: z.string().default(""),
  page_size: z.number().int().min(1).max(100).optional(),
  start_cursor: z.string().optional(),
});

type SearchArgs = z.infer<typeof SearchArgsSchema>;

const auth = new FlowUsAuthManager({ stderr: process.stderr });
auth.init().catch(() => {
});

const server = new Server(
  { name: "flowus-mcp", version: "0.1.0" },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "search",
        description: "Search FlowUs pages within the authorized scope",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string", description: "Search query (can be empty)" },
            page_size: { type: "number", description: "Page size (1-100)" },
            start_cursor: { type: "string", description: "Pagination cursor" },
          },
          required: ["query"],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const name = request.params.name;
  if (name !== "search") {
    return {
      content: [{ type: "text", text: `Unknown tool: ${name}` }],
      isError: true,
    };
  }

  let args: SearchArgs;
  try {
    args = SearchArgsSchema.parse(request.params.arguments ?? {});
  } catch (e) {
    return {
      content: [{ type: "text", text: `Invalid arguments: ${String(e)}` }],
      isError: true,
    };
  }

  try {
    const accessToken = await auth.getAccessToken();
    const api = createFlowUsApi(accessToken);
    const result = await searchFlowUs(api, {
      query: args.query,
      page_size: args.page_size,
      start_cursor: args.start_cursor,
    });
    return {
      content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
      isError: false,
    };
  } catch (e) {
    return {
      content: [{ type: "text", text: `Search failed: ${e instanceof Error ? e.message : String(e)}` }],
      isError: true,
    };
  }
});

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((e) => {
  process.stderr.write(`FlowUs MCP fatal: ${e instanceof Error ? e.stack ?? e.message : String(e)}\n`);
  process.exitCode = 1;
});

