import { Configuration, DefaultApi } from "flowus-api-sdk";

export type FlowUsSearchArgs = {
  query: string;
  start_cursor?: string;
  page_size?: number;
};

export type FlowUsSearchResult = unknown;

export function createFlowUsApi(accessToken: string): DefaultApi {
  const config = new Configuration({
    basePath: "https://api.flowus.cn",
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return new DefaultApi(config);
}

export async function searchFlowUs(api: DefaultApi, args: FlowUsSearchArgs): Promise<FlowUsSearchResult> {
  const anyApi = api as any;
  if (typeof anyApi.v1Search === "function") {
    return anyApi.v1Search({
      v1SearchRequest: {
        query: args.query,
        start_cursor: args.start_cursor,
        page_size: args.page_size,
      },
    });
  }
  if (typeof anyApi.search === "function") {
    return anyApi.search(args);
  }
  throw new Error("FlowUs SDK: v1Search/search method not found on DefaultApi");
}
