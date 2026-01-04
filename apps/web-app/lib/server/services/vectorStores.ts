'use server';

import {
  attachFileApiV1VectorStoresVectorStoreIdFilesPost,
  bindAgentToVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyPost,
  createVectorStoreApiV1VectorStoresPost,
  deleteFileApiV1VectorStoresVectorStoreIdFilesFileIdDelete,
  deleteVectorStoreApiV1VectorStoresVectorStoreIdDelete,
  getFileApiV1VectorStoresVectorStoreIdFilesFileIdGet,
  getVectorStoreApiV1VectorStoresVectorStoreIdGet,
  listFilesApiV1VectorStoresVectorStoreIdFilesGet,
  listVectorStoresApiV1VectorStoresGet,
  searchVectorStoreApiV1VectorStoresVectorStoreIdSearchPost,
  unbindAgentFromVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyDelete,
  uploadAndAttachFileApiV1VectorStoresVectorStoreIdFilesUploadPost,
} from '@/lib/api/client/sdk.gen';
import type {
  VectorStoreCreateRequest,
  VectorStoreFileCreateRequest,
  VectorStoreFileUploadRequest,
  VectorStoreListResponse,
  VectorStoreSearchRequest,
  VectorStoreSearchResponse,
  VectorStoreResponse,
  VectorStoreFileListResponse,
  VectorStoreFileResponse,
} from '@/lib/api/client/types.gen';
import { getServerApiClient } from '../apiClient';

export class VectorStoreServiceError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly detail?: string,
  ) {
    super(message);
    this.name = 'VectorStoreServiceError';
  }
}

type ApiFieldsResult<TData> =
  | {
      data: TData;
      error: undefined;
      response: Response;
    }
  | {
      data: undefined;
      error: unknown;
      response: Response;
    };

function resolveErrorMessage(error: unknown, fallback: string) {
  if (!error) return fallback;
  if (typeof error === 'string') return error;
  if (
    typeof error === 'object'
    && error !== null
    && 'message' in error
    && typeof (error as { message?: unknown }).message === 'string'
  ) {
    return (error as { message: string }).message;
  }
  if (typeof error === 'object' && error !== null && 'detail' in error) {
    const detail = (error as { detail?: unknown }).detail;
    if (typeof detail === 'string') return detail;
  }
  return fallback;
}

function resolveDetail(error: unknown): string | undefined {
  if (!error || typeof error !== 'object') return undefined;
  const record = error as { detail?: unknown };
  return typeof record.detail === 'string' ? record.detail : undefined;
}

function mapStatusFromMessage(message: string, fallback = 500): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) return 401;
  if (normalized.includes('not found')) return 404;
  return fallback;
}

function throwVectorStoreError(
  error: unknown,
  fallback: string,
  statusOverride?: number,
): never {
  const message = resolveErrorMessage(error, fallback);
  const status = statusOverride ?? mapStatusFromMessage(message);
  throw new VectorStoreServiceError(message, status, resolveDetail(error));
}

export async function listVectorStores(): Promise<VectorStoreListResponse> {
  const { client, auth } = await getServerApiClient();
  const result = (await listVectorStoresApiV1VectorStoresGet({
    client,
    auth,
    throwOnError: false,
    responseStyle: 'fields',
  })) as ApiFieldsResult<VectorStoreListResponse>;

  if ('error' in result && result.error) {
    throwVectorStoreError(result.error, 'Failed to load vector stores', result.response?.status);
  }

  return result.data ?? { items: [], total: 0 };
}

export async function createVectorStore(
  payload: VectorStoreCreateRequest,
): Promise<VectorStoreResponse> {
  const { client, auth } = await getServerApiClient();
  const result = (await createVectorStoreApiV1VectorStoresPost({
    client,
    auth,
    throwOnError: false,
    responseStyle: 'fields',
    body: payload,
  })) as ApiFieldsResult<VectorStoreResponse>;

  if ('error' in result && result.error) {
    throwVectorStoreError(result.error, 'Failed to create vector store', result.response?.status);
  }
  if (!result.data) {
    throw new VectorStoreServiceError('Vector store create missing data', 500);
  }
  return result.data;
}

export async function getVectorStore(vectorStoreId: string): Promise<VectorStoreResponse> {
  if (!vectorStoreId) {
    throw new VectorStoreServiceError('vectorStoreId is required.', 400);
  }

  try {
    const { client, auth } = await getServerApiClient();
    const response = await getVectorStoreApiV1VectorStoresVectorStoreIdGet({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
      path: { vector_store_id: vectorStoreId },
    });

    if (!response.data) {
      throw new VectorStoreServiceError('Vector store not found', 404);
    }

    return response.data;
  } catch (error) {
    throwVectorStoreError(error, 'Failed to load vector store');
  }
}

export async function deleteVectorStore(vectorStoreId: string): Promise<void> {
  if (!vectorStoreId) {
    throw new VectorStoreServiceError('vectorStoreId is required.', 400);
  }

  try {
    const { client, auth } = await getServerApiClient();
    await deleteVectorStoreApiV1VectorStoresVectorStoreIdDelete({
      client,
      auth,
      throwOnError: true,
      path: { vector_store_id: vectorStoreId },
    });
  } catch (error) {
    throwVectorStoreError(error, 'Failed to delete vector store');
  }
}

export async function listVectorStoreFiles(
  vectorStoreId: string,
): Promise<VectorStoreFileListResponse> {
  if (!vectorStoreId) {
    throw new VectorStoreServiceError('vectorStoreId is required.', 400);
  }

  try {
    const { client, auth } = await getServerApiClient();
    const response = await listFilesApiV1VectorStoresVectorStoreIdFilesGet({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
      path: { vector_store_id: vectorStoreId },
    });
    return response.data ?? { items: [], total: 0 };
  } catch (error) {
    throwVectorStoreError(error, 'Failed to list vector store files');
  }
}

export async function attachVectorStoreFile(
  vectorStoreId: string,
  payload: VectorStoreFileCreateRequest,
): Promise<VectorStoreFileResponse> {
  if (!vectorStoreId) {
    throw new VectorStoreServiceError('vectorStoreId is required.', 400);
  }

  try {
    const { client, auth } = await getServerApiClient();
    const response = await attachFileApiV1VectorStoresVectorStoreIdFilesPost({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
      path: { vector_store_id: vectorStoreId },
      body: payload,
    });

    if (!response.data) {
      throw new VectorStoreServiceError('Attach file missing data', 500);
    }

    return response.data;
  } catch (error) {
    throwVectorStoreError(error, 'Failed to attach file');
  }
}

export async function getVectorStoreFile(
  vectorStoreId: string,
  fileId: string,
): Promise<VectorStoreFileResponse> {
  if (!vectorStoreId || !fileId) {
    throw new VectorStoreServiceError('vectorStoreId and fileId are required.', 400);
  }

  try {
    const { client, auth } = await getServerApiClient();
    const response = await getFileApiV1VectorStoresVectorStoreIdFilesFileIdGet({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
      path: { vector_store_id: vectorStoreId, file_id: fileId },
    });

    if (!response.data) {
      throw new VectorStoreServiceError('Vector store file not found', 404);
    }

    return response.data;
  } catch (error) {
    throwVectorStoreError(error, 'Failed to load vector store file');
  }
}

export async function deleteVectorStoreFile(
  vectorStoreId: string,
  fileId: string,
): Promise<void> {
  if (!vectorStoreId || !fileId) {
    throw new VectorStoreServiceError('vectorStoreId and fileId are required.', 400);
  }

  try {
    const { client, auth } = await getServerApiClient();
    await deleteFileApiV1VectorStoresVectorStoreIdFilesFileIdDelete({
      client,
      auth,
      throwOnError: true,
      path: { vector_store_id: vectorStoreId, file_id: fileId },
    });
  } catch (error) {
    throwVectorStoreError(error, 'Failed to delete vector store file');
  }
}

export async function uploadVectorStoreFile(
  vectorStoreId: string,
  payload: VectorStoreFileUploadRequest,
): Promise<{ data: VectorStoreFileResponse; status: number }> {
  if (!vectorStoreId) {
    throw new VectorStoreServiceError('vectorStoreId is required.', 400);
  }

  const { client, auth } = await getServerApiClient();
  const result = (await uploadAndAttachFileApiV1VectorStoresVectorStoreIdFilesUploadPost({
    client,
    auth,
    throwOnError: false,
    responseStyle: 'fields',
    path: { vector_store_id: vectorStoreId },
    body: payload,
  })) as ApiFieldsResult<VectorStoreFileResponse>;

  const status = result.response?.status ?? (result.error ? 500 : 201);
  if ('error' in result && result.error) {
    const detail = resolveDetail(result.error);
    const message = resolveErrorMessage(
      result.error,
      detail ?? 'Failed to upload vector store file',
    );
    throw new VectorStoreServiceError(message, status, detail);
  }

  if (!result.data) {
    throw new VectorStoreServiceError('Vector store upload missing data', 500);
  }

  return { data: result.data, status };
}

export async function searchVectorStore(
  vectorStoreId: string,
  payload: VectorStoreSearchRequest,
): Promise<VectorStoreSearchResponse> {
  if (!vectorStoreId) {
    throw new VectorStoreServiceError('vectorStoreId is required.', 400);
  }

  try {
    const { client, auth } = await getServerApiClient();
    const response = await searchVectorStoreApiV1VectorStoresVectorStoreIdSearchPost({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
      path: { vector_store_id: vectorStoreId },
      body: payload,
    });

    if (!response.data || typeof response.data !== 'object') {
      throw new VectorStoreServiceError('Vector store search returned an invalid payload.', 502);
    }

    const record = response.data as Record<string, unknown>;
    if (typeof record.object !== 'string' || typeof record.search_query !== 'string') {
      throw new VectorStoreServiceError('Vector store search returned an invalid payload.', 502);
    }

    return response.data as VectorStoreSearchResponse;
  } catch (error) {
    throwVectorStoreError(error, 'Failed to search vector store');
  }
}

export async function bindAgentToVectorStore(
  vectorStoreId: string,
  agentKey: string,
): Promise<void> {
  if (!vectorStoreId || !agentKey) {
    throw new VectorStoreServiceError('vectorStoreId and agentKey are required.', 400);
  }

  try {
    const { client, auth } = await getServerApiClient();
    await bindAgentToVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyPost({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
      path: { vector_store_id: vectorStoreId, agent_key: agentKey },
    });
  } catch (error) {
    throwVectorStoreError(error, 'Failed to bind agent to vector store');
  }
}

export async function unbindAgentFromVectorStore(
  vectorStoreId: string,
  agentKey: string,
): Promise<void> {
  if (!vectorStoreId || !agentKey) {
    throw new VectorStoreServiceError('vectorStoreId and agentKey are required.', 400);
  }

  try {
    const { client, auth } = await getServerApiClient();
    await unbindAgentFromVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyDelete({
      client,
      auth,
      throwOnError: true,
      path: { vector_store_id: vectorStoreId, agent_key: agentKey },
    });
  } catch (error) {
    throwVectorStoreError(error, 'Failed to unbind agent from vector store');
  }
}
