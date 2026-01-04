import 'server-only';

import {
  bindAgentContainerApiV1ContainersAgentsAgentKeyContainerPost,
  createContainerApiV1ContainersPost,
  deleteContainerApiV1ContainersContainerIdDelete,
  getContainerByIdApiV1ContainersContainerIdGet,
  listContainersApiV1ContainersGet,
  unbindAgentContainerApiV1ContainersAgentsAgentKeyContainerDelete,
} from '@/lib/api/client/sdk.gen';
import type {
  ContainerBindRequest,
  ContainerCreateRequest,
  ContainerListResponse,
  ContainerResponse,
} from '@/lib/api/client/types.gen';
import { getServerApiClient } from '../apiClient';

export async function listContainers(): Promise<ContainerListResponse> {
  const { client, auth } = await getServerApiClient();
  const response = await listContainersApiV1ContainersGet({
    client,
    auth,
    throwOnError: true,
    responseStyle: 'fields',
  });

  return response.data ?? { items: [], total: 0 };
}

export async function createContainer(
  payload: ContainerCreateRequest,
): Promise<ContainerResponse> {
  const { client, auth } = await getServerApiClient();
  const response = await createContainerApiV1ContainersPost({
    client,
    auth,
    throwOnError: true,
    responseStyle: 'fields',
    body: payload,
  });

  if (!response.data) {
    throw new Error('Create container missing data.');
  }

  return response.data;
}

export async function getContainerById(
  containerId: string,
): Promise<ContainerResponse> {
  if (!containerId) {
    throw new Error('containerId is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await getContainerByIdApiV1ContainersContainerIdGet({
    client,
    auth,
    throwOnError: true,
    responseStyle: 'fields',
    path: { container_id: containerId },
  });

  if (!response.data) {
    throw new Error('Container not found.');
  }

  return response.data;
}

export async function deleteContainer(containerId: string): Promise<void> {
  if (!containerId) {
    throw new Error('containerId is required.');
  }

  const { client, auth } = await getServerApiClient();
  await deleteContainerApiV1ContainersContainerIdDelete({
    client,
    auth,
    throwOnError: true,
    responseStyle: 'fields',
    path: { container_id: containerId },
  });
}

export async function bindAgentContainer(
  agentKey: string,
  payload: ContainerBindRequest,
): Promise<void> {
  if (!agentKey) {
    throw new Error('agentKey is required.');
  }

  const { client, auth } = await getServerApiClient();
  await bindAgentContainerApiV1ContainersAgentsAgentKeyContainerPost({
    client,
    auth,
    throwOnError: true,
    responseStyle: 'fields',
    path: { agent_key: agentKey },
    body: payload,
  });
}

export async function unbindAgentContainer(agentKey: string): Promise<void> {
  if (!agentKey) {
    throw new Error('agentKey is required.');
  }

  const { client, auth } = await getServerApiClient();
  await unbindAgentContainerApiV1ContainersAgentsAgentKeyContainerDelete({
    client,
    auth,
    throwOnError: true,
    responseStyle: 'fields',
    path: { agent_key: agentKey },
  });
}
