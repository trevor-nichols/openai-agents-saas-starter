import type { ToolRegistry, ToolsResponse } from '@/types/tools';
import { apiV1Path } from '@/lib/apiPaths';

export async function fetchTools(): Promise<ToolRegistry> {
  const response = await fetch(apiV1Path('/tools'), { cache: 'no-store' });
  const payload = (await response.json()) as ToolsResponse;

  if (!response.ok) {
    throw new Error(payload.error || 'Failed to load tools');
  }

  if (!payload.success || !payload.tools) {
    throw new Error(payload.error || 'No tools returned from API');
  }

  return payload.tools;
}
