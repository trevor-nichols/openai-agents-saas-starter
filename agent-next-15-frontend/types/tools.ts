import type { ListAvailableToolsApiV1ToolsGetResponses } from '@/lib/api/client/types.gen';

export type ToolRegistry = ListAvailableToolsApiV1ToolsGetResponses[200];

export interface ToolsResponse {
  success: boolean;
  tools?: ToolRegistry;
  error?: string;
}

export type ToolDefinition = {
  name: string;
  description?: string | null;
  supported_agents?: string[];
};
