import {
  attachFileApiV1VectorStoresVectorStoreIdFilesPost,
  createVectorStoreApiV1VectorStoresPost,
  deleteFileApiV1VectorStoresVectorStoreIdFilesFileIdDelete,
  deleteVectorStoreApiV1VectorStoresVectorStoreIdDelete,
  listFilesApiV1VectorStoresVectorStoreIdFilesGet,
  listVectorStoresApiV1VectorStoresGet,
  searchVectorStoreApiV1VectorStoresVectorStoreIdSearchPost,
} from '@/lib/api/client/sdk.gen';
import type {
  VectorStoreListResponse,
  VectorStoreFileListResponse,
  VectorStoreSearchResponse,
  VectorStoreCreateRequest,
  VectorStoreFileCreateRequest,
  VectorStoreSearchRequest,
} from '@/lib/api/client/types.gen';
import { USE_API_MOCK } from '@/lib/config';
import { mockVectorStores, mockVectorStoreFiles, mockVectorStoreSearch } from '@/lib/vector-stores/mock';
import { client } from './config';

export async function listVectorStores(): Promise<VectorStoreListResponse> {
  if (USE_API_MOCK) return mockVectorStores;
  const res = await listVectorStoresApiV1VectorStoresGet({ client, throwOnError: true, responseStyle: 'fields' });
  return res.data ?? { items: [], total: 0 };
}

export async function createVectorStore(body: VectorStoreCreateRequest) {
  if (USE_API_MOCK) return mockVectorStores.items[0];
  const res = await createVectorStoreApiV1VectorStoresPost({ client, throwOnError: true, responseStyle: 'fields', body });
  if (!res.data) throw new Error('Vector store create missing data');
  return res.data;
}

export async function deleteVectorStore(vectorStoreId: string) {
  if (USE_API_MOCK) return;
  await deleteVectorStoreApiV1VectorStoresVectorStoreIdDelete({ client, throwOnError: true, path: { vector_store_id: vectorStoreId } });
}

export async function listVectorStoreFiles(vectorStoreId: string): Promise<VectorStoreFileListResponse> {
  if (USE_API_MOCK) return mockVectorStoreFiles;
  const res = await listFilesApiV1VectorStoresVectorStoreIdFilesGet({ client, throwOnError: true, responseStyle: 'fields', path: { vector_store_id: vectorStoreId } });
  return res.data ?? { items: [], total: 0 };
}

export async function attachVectorStoreFile(vectorStoreId: string, body: VectorStoreFileCreateRequest) {
  if (USE_API_MOCK) return mockVectorStoreFiles.items[0];
  const res = await attachFileApiV1VectorStoresVectorStoreIdFilesPost({ client, throwOnError: true, responseStyle: 'fields', path: { vector_store_id: vectorStoreId }, body });
  if (!res.data) throw new Error('Attach file missing data');
  return res.data;
}

export async function deleteVectorStoreFile(vectorStoreId: string, fileId: string) {
  if (USE_API_MOCK) return;
  await deleteFileApiV1VectorStoresVectorStoreIdFilesFileIdDelete({ client, throwOnError: true, path: { vector_store_id: vectorStoreId, file_id: fileId } });
}

export async function searchVectorStore(vectorStoreId: string, body: VectorStoreSearchRequest): Promise<VectorStoreSearchResponse> {
  if (USE_API_MOCK) return mockVectorStoreSearch;
  const res = await searchVectorStoreApiV1VectorStoresVectorStoreIdSearchPost({ client, throwOnError: true, responseStyle: 'fields', path: { vector_store_id: vectorStoreId }, body });
  if (!res.data) throw new Error('Vector store search missing data');
  return res.data;
}
