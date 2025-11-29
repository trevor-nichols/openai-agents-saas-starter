import {
  bindAgentContainerApiV1ContainersAgentsAgentKeyContainerPost,
  createContainerApiV1ContainersPost,
  deleteContainerApiV1ContainersContainerIdDelete,
  getContainerByIdApiV1ContainersContainerIdGet,
  listContainersApiV1ContainersGet,
  unbindAgentContainerApiV1ContainersAgentsAgentKeyContainerDelete,
} from '@/lib/api/client/sdk.gen';
import type {
  ContainerCreateRequest,
  ContainerListResponse,
  ContainerResponse,
  ContainerBindRequest,
} from '@/lib/api/client/types.gen';
import { USE_API_MOCK } from '@/lib/config';
import { mockContainers } from '@/lib/containers/mock';
import { client } from './config';

export async function listContainers(): Promise<ContainerListResponse> {
  if (USE_API_MOCK) return { items: mockContainers, total: mockContainers.length };
  const res = await listContainersApiV1ContainersGet({ client, throwOnError: true, responseStyle: 'fields' });
  return res.data ?? { items: [], total: 0 };
}

export async function createContainer(body: ContainerCreateRequest): Promise<ContainerResponse> {
  if (USE_API_MOCK) {
    const id = `ctr-${Date.now()}`;
    const base =
      mockContainers[0] ??
      ({
        id: 'ctr-base',
        openai_id: 'ctr-base',
        tenant_id: 'tenant',
        owner_user_id: 'user',
        name: 'base',
        memory_limit: '4g',
        status: 'ready',
        expires_after: null,
        last_active_at: new Date().toISOString(),
        metadata: {},
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as ContainerResponse);
    const now = new Date().toISOString();
    return {
      ...base,
      id,
      openai_id: id,
      tenant_id: base.tenant_id ?? 'tenant',
      owner_user_id: base.owner_user_id ?? 'user',
      name: body.name,
      memory_limit: body.memory_limit ?? base.memory_limit,
      status: base.status ?? 'ready',
      expires_after: base.expires_after ?? null,
      last_active_at: base.last_active_at ?? now,
      metadata: base.metadata ?? {},
      created_at: base.created_at ?? now,
      updated_at: now,
    };
  }
  const res = await createContainerApiV1ContainersPost({ client, throwOnError: true, responseStyle: 'fields', body });
  if (!res.data) throw new Error('Create container missing data');
  return res.data;
}

export async function deleteContainer(containerId: string) {
  if (USE_API_MOCK) return;
  await deleteContainerApiV1ContainersContainerIdDelete({ client, throwOnError: true, path: { container_id: containerId } });
}

export async function getContainer(containerId: string) {
  if (USE_API_MOCK) return mockContainers.find((c) => c.id === containerId) ?? mockContainers[0];
  const res = await getContainerByIdApiV1ContainersContainerIdGet({ client, throwOnError: true, responseStyle: 'fields', path: { container_id: containerId } });
  if (!res.data) throw new Error('Container not found');
  return res.data;
}

export async function bindAgentToContainer(agentKey: string, body: ContainerBindRequest) {
  if (USE_API_MOCK) return;
  await bindAgentContainerApiV1ContainersAgentsAgentKeyContainerPost({
    client,
    throwOnError: true,
    responseStyle: 'fields',
    path: { agent_key: agentKey },
    body,
  });
}

export async function unbindAgentFromContainer(agentKey: string) {
  if (USE_API_MOCK) return;
  await unbindAgentContainerApiV1ContainersAgentsAgentKeyContainerDelete({
    client,
    throwOnError: true,
    path: { agent_key: agentKey },
  });
}
