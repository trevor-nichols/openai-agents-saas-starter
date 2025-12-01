import type {
  ContainerBindRequest,
  ContainerCreateRequest,
  ContainerListResponse,
  ContainerResponse,
} from '@/lib/api/client/types.gen';
import { USE_API_MOCK } from '@/lib/config';
import { mockContainers } from '@/lib/containers/mock';
import { apiV1Path } from '@/lib/apiPaths';

async function parseJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch {
    throw new Error('Failed to parse containers response');
  }
}

function buildError(response: Response, fallback: string): Error {
  return new Error(fallback || `Request failed with ${response.status}`);
}

export async function listContainers(): Promise<ContainerListResponse> {
  if (USE_API_MOCK) return { items: mockContainers, total: mockContainers.length };

  const res = await fetch(apiV1Path('/containers'), { cache: 'no-store' });
  if (!res.ok) throw buildError(res, 'Failed to load containers');
  return parseJson<ContainerListResponse>(res);
}

export async function createContainer(body: ContainerCreateRequest): Promise<ContainerResponse> {
  if (USE_API_MOCK) {
    const now = new Date().toISOString();
    const id = `ctr-${Date.now()}`;
    const base = mockContainers[0];
    return {
      ...(base ?? {
        id,
        openai_id: id,
        tenant_id: 'tenant',
        owner_user_id: 'user',
        status: 'ready',
        expires_after: null,
        last_active_at: now,
        metadata: {},
        created_at: now,
        updated_at: now,
      }),
      id,
      openai_id: id,
      name: body.name,
      memory_limit: body.memory_limit ?? base?.memory_limit ?? '4g',
      updated_at: now,
    };
  }

  const res = await fetch(apiV1Path('/containers'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) throw buildError(res, 'Failed to create container');
  return parseJson<ContainerResponse>(res);
}

export async function deleteContainer(containerId: string) {
  if (USE_API_MOCK) return;

  const res = await fetch(apiV1Path(`/containers/${encodeURIComponent(containerId)}`), { method: 'DELETE' });
  if (!res.ok) throw buildError(res, 'Failed to delete container');
}

export async function getContainer(containerId: string) {
  if (USE_API_MOCK) return mockContainers.find((c) => c.id === containerId) ?? mockContainers[0];

  const res = await fetch(apiV1Path(`/containers/${encodeURIComponent(containerId)}`), { cache: 'no-store' });
  if (res.status === 404) throw new Error('Container not found');
  if (!res.ok) throw buildError(res, 'Failed to load container');
  return parseJson<ContainerResponse>(res);
}

export async function bindAgentToContainer(agentKey: string, body: ContainerBindRequest) {
  if (USE_API_MOCK) return;

  const res = await fetch(apiV1Path(`/containers/agents/${encodeURIComponent(agentKey)}/container`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) throw buildError(res, 'Failed to bind agent to container');
}

export async function unbindAgentFromContainer(agentKey: string) {
  if (USE_API_MOCK) return;

  const res = await fetch(apiV1Path(`/containers/agents/${encodeURIComponent(agentKey)}/container`), {
    method: 'DELETE',
  });

  if (!res.ok) throw buildError(res, 'Failed to unbind agent from container');
}
