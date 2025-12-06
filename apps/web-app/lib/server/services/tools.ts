'use server';

import { listAvailableToolsApiV1ToolsGet } from '@/lib/api/client/sdk.gen';
import type { ToolRegistry } from '@/types/tools';

import { getServerApiClient } from '../apiClient';

/**
 * Fetch metadata about all registered tools for the authenticated tenant.
 */
export async function listAvailableTools(): Promise<ToolRegistry> {
  const { client, auth } = await getServerApiClient();
  const response = await listAvailableToolsApiV1ToolsGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
  });

  return (response.data ?? {}) as ToolRegistry;
}
