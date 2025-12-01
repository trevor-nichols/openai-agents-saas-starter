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

export async function listVectorStores(): Promise<VectorStoreListResponse> {
  if (USE_API_MOCK) return mockVectorStores;
  const res = await fetch('/api/vector-stores', { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to load vector stores (${res.status})`);
  return (await res.json()) as VectorStoreListResponse;
}

export async function createVectorStore(body: VectorStoreCreateRequest) {
  if (USE_API_MOCK) return mockVectorStores.items[0];
  const res = await fetch('/api/vector-stores/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Failed to create vector store (${res.status})`);
  return (await res.json()) as VectorStoreListResponse['items'][number];
}

export async function deleteVectorStore(vectorStoreId: string) {
  if (USE_API_MOCK) return;
  const res = await fetch(`/api/vector-stores/${encodeURIComponent(vectorStoreId)}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`Failed to delete vector store (${res.status})`);
}

export async function listVectorStoreFiles(vectorStoreId: string): Promise<VectorStoreFileListResponse> {
  if (USE_API_MOCK) return mockVectorStoreFiles;
  const res = await fetch(`/api/vector-stores/${encodeURIComponent(vectorStoreId)}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to load vector store files (${res.status})`);
  return (await res.json()) as VectorStoreFileListResponse;
}

export async function attachVectorStoreFile(vectorStoreId: string, body: VectorStoreFileCreateRequest) {
  if (USE_API_MOCK) return mockVectorStoreFiles.items[0];
  const res = await fetch(`/api/vector-stores/${encodeURIComponent(vectorStoreId)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Failed to attach file (${res.status})`);
  return (await res.json()) as VectorStoreFileListResponse['items'][number];
}

export async function deleteVectorStoreFile(vectorStoreId: string, fileId: string) {
  if (USE_API_MOCK) return;
  const res = await fetch(`/api/vector-stores/${encodeURIComponent(vectorStoreId)}/files/${encodeURIComponent(fileId)}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error(`Failed to delete vector store file (${res.status})`);
}

export async function searchVectorStore(vectorStoreId: string, body: VectorStoreSearchRequest): Promise<VectorStoreSearchResponse> {
  if (USE_API_MOCK) return mockVectorStoreSearch;
  const res = await fetch(`/api/vector-stores/${encodeURIComponent(vectorStoreId)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Failed to search vector store (${res.status})`);
  return (await res.json()) as VectorStoreSearchResponse;
}
