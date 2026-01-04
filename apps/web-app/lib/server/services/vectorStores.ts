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

function throwIfError<TData>(
  result: ApiFieldsResult<TData>,
  fallbackMessage: string,
): void {
  if ('error' in result && result.error) {
    throwVectorStoreError(result.error, fallbackMessage, result.response?.status);
  }
}

export async function listVectorStores(): Promise<VectorStoreListResponse> {
  const { client, auth } = await getServerApiClient();
  const result = (await listVectorStoresApiV1VectorStoresGet({
    client,
    auth,
    throwOnError: false,
    responseStyle: 'fields',
  })) as ApiFieldsResult<VectorStoreListResponse>;

  throwIfError(result, 'Failed to load vector stores');

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

  throwIfError(result, 'Failed to create vector store');
  if (!result.data) {
    const status = result.response?.status ?? 502;
    throw new VectorStoreServiceError('Vector store create missing data', status);
  }
  return result.data;
}

export async function getVectorStore(vectorStoreId: string): Promise<VectorStoreResponse> {
  if (!vectorStoreId) {
    throw new VectorStoreServiceError('vectorStoreId is required.', 400);
  }

  const { client, auth } = await getServerApiClient();
  const response = (await getVectorStoreApiV1VectorStoresVectorStoreIdGet({
    client,
    auth,
    throwOnError: false,
    responseStyle: 'fields',
    path: { vector_store_id: vectorStoreId },
  })) as ApiFieldsResult<VectorStoreResponse>;

  throwIfError(response, 'Failed to load vector store');

  if (!response.data) {
    const status = response.response?.status ?? 404;
    const resolvedStatus = status >= 400 ? status : 404;
    throw new VectorStoreServiceError('Vector store not found', resolvedStatus);
  }

  return response.data;
}

export async function deleteVectorStore(vectorStoreId: string): Promise<void> {
  if (!vectorStoreId) {
    throw new VectorStoreServiceError('vectorStoreId is required.', 400);
  }

  const { client, auth } = await getServerApiClient();
  const response = (await deleteVectorStoreApiV1VectorStoresVectorStoreIdDelete({
    client,
    auth,
    throwOnError: false,
    responseStyle: 'fields',
    path: { vector_store_id: vectorStoreId },
  })) as ApiFieldsResult<void>;

  if ('error' in response && response.error) {
    throwVectorStoreError(response.error, 'Failed to delete vector store', response.response?.status);
  }
  const status = response.response?.status ?? 204;
  if (status >= 400) {
    throw new VectorStoreServiceError('Failed to delete vector store', status);
  }
}

export async function listVectorStoreFiles(
  vectorStoreId: string,
): Promise<VectorStoreFileListResponse> {
  if (!vectorStoreId) {
    throw new VectorStoreServiceError('vectorStoreId is required.', 400);
  }

  const { client, auth } = await getServerApiClient();
  const response = (await listFilesApiV1VectorStoresVectorStoreIdFilesGet({
    client,
    auth,
    throwOnError: false,
    responseStyle: 'fields',
    path: { vector_store_id: vectorStoreId },
  })) as ApiFieldsResult<VectorStoreFileListResponse>;

  throwIfError(response, 'Failed to list vector store files');
  return response.data ?? { items: [], total: 0 };
}

export async function attachVectorStoreFile(
  vectorStoreId: string,
  payload: VectorStoreFileCreateRequest,
): Promise<VectorStoreFileResponse> {
  if (!vectorStoreId) {
    throw new VectorStoreServiceError('vectorStoreId is required.', 400);
  }

  const { client, auth } = await getServerApiClient();
  const response = (await attachFileApiV1VectorStoresVectorStoreIdFilesPost({
    client,
    auth,
    throwOnError: false,
    responseStyle: 'fields',
    path: { vector_store_id: vectorStoreId },
    body: payload,
  })) as ApiFieldsResult<VectorStoreFileResponse>;

  throwIfError(response, 'Failed to attach file');

  if (!response.data) {
    const status = response.response?.status ?? 502;
    throw new VectorStoreServiceError('Attach file missing data', status);
  }

  return response.data;
}

export async function getVectorStoreFile(
  vectorStoreId: string,
  fileId: string,
): Promise<VectorStoreFileResponse> {
  if (!vectorStoreId || !fileId) {
    throw new VectorStoreServiceError('vectorStoreId and fileId are required.', 400);
  }

  const { client, auth } = await getServerApiClient();
  const response = (await getFileApiV1VectorStoresVectorStoreIdFilesFileIdGet({
    client,
    auth,
    throwOnError: false,
    responseStyle: 'fields',
    path: { vector_store_id: vectorStoreId, file_id: fileId },
  })) as ApiFieldsResult<VectorStoreFileResponse>;

  throwIfError(response, 'Failed to load vector store file');

  if (!response.data) {
    const status = response.response?.status ?? 404;
    const resolvedStatus = status >= 400 ? status : 404;
    throw new VectorStoreServiceError('Vector store file not found', resolvedStatus);
  }

  return response.data;
}

export async function deleteVectorStoreFile(
  vectorStoreId: string,
  fileId: string,
): Promise<void> {
  if (!vectorStoreId || !fileId) {
    throw new VectorStoreServiceError('vectorStoreId and fileId are required.', 400);
  }

  const { client, auth } = await getServerApiClient();
  const response = (await deleteFileApiV1VectorStoresVectorStoreIdFilesFileIdDelete({
    client,
    auth,
    throwOnError: false,
    responseStyle: 'fields',
    path: { vector_store_id: vectorStoreId, file_id: fileId },
  })) as ApiFieldsResult<void>;

  if ('error' in response && response.error) {
    throwVectorStoreError(response.error, 'Failed to delete vector store file', response.response?.status);
  }

  const status = response.response?.status ?? 204;
  if (status >= 400) {
    throw new VectorStoreServiceError('Failed to delete vector store file', status);
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

  const status = result.response?.status ?? (result.error ? 502 : 201);
  if ('error' in result && result.error) {
    throwVectorStoreError(result.error, 'Failed to upload vector store file', status);
  }

  if (!result.data) {
    const resolvedStatus = status >= 400 ? status : 502;
    throw new VectorStoreServiceError('Vector store upload missing data', resolvedStatus);
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

  const { client, auth } = await getServerApiClient();
  const response = (await searchVectorStoreApiV1VectorStoresVectorStoreIdSearchPost({
    client,
    auth,
    throwOnError: false,
    responseStyle: 'fields',
    path: { vector_store_id: vectorStoreId },
    body: payload,
  })) as ApiFieldsResult<VectorStoreSearchResponse>;

  throwIfError(response, 'Failed to search vector store');

  if (!response.data || typeof response.data !== 'object') {
    const status = response.response?.status ?? 502;
    throw new VectorStoreServiceError('Vector store search returned an invalid payload.', status);
  }

  const record = response.data as Record<string, unknown>;
  if (typeof record.object !== 'string' || typeof record.search_query !== 'string') {
    const status = response.response?.status ?? 502;
    throw new VectorStoreServiceError('Vector store search returned an invalid payload.', status);
  }

  return response.data as VectorStoreSearchResponse;
}

export async function bindAgentToVectorStore(
  vectorStoreId: string,
  agentKey: string,
): Promise<void> {
  if (!vectorStoreId || !agentKey) {
    throw new VectorStoreServiceError('vectorStoreId and agentKey are required.', 400);
  }

  const { client, auth } = await getServerApiClient();
  const response = (await bindAgentToVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyPost({
    client,
    auth,
    throwOnError: false,
    responseStyle: 'fields',
    path: { vector_store_id: vectorStoreId, agent_key: agentKey },
  })) as ApiFieldsResult<void>;

  if ('error' in response && response.error) {
    throwVectorStoreError(response.error, 'Failed to bind agent to vector store', response.response?.status);
  }

  const status = response.response?.status ?? 204;
  if (status >= 400) {
    throw new VectorStoreServiceError('Failed to bind agent to vector store', status);
  }
}

export async function unbindAgentFromVectorStore(
  vectorStoreId: string,
  agentKey: string,
): Promise<void> {
  if (!vectorStoreId || !agentKey) {
    throw new VectorStoreServiceError('vectorStoreId and agentKey are required.', 400);
  }

  const { client, auth } = await getServerApiClient();
  const response = (await unbindAgentFromVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyDelete({
    client,
    auth,
    throwOnError: false,
    responseStyle: 'fields',
    path: { vector_store_id: vectorStoreId, agent_key: agentKey },
  })) as ApiFieldsResult<void>;

  if ('error' in response && response.error) {
    throwVectorStoreError(response.error, 'Failed to unbind agent from vector store', response.response?.status);
  }

  const status = response.response?.status ?? 204;
  if (status >= 400) {
    throw new VectorStoreServiceError('Failed to unbind agent from vector store', status);
  }
}
