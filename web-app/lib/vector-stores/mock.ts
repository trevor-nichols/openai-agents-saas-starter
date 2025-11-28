import type { VectorStoreFileListResponse, VectorStoreListResponse, VectorStoreSearchResponse } from '@/lib/api/client/types.gen';

export const mockVectorStores: VectorStoreListResponse = {
  items: [
    {
      id: 'vs-1',
      openai_id: 'vs-1',
      tenant_id: 'tenant',
      owner_user_id: 'user',
      name: 'Demo Store',
      description: 'Example vector store',
      status: 'ready',
      usage_bytes: 0,
      expires_after: null,
      expires_at: null,
      last_active_at: new Date().toISOString(),
      metadata: {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ],
  total: 1,
};

export const mockVectorStoreFiles: VectorStoreFileListResponse = {
  items: [
    {
      id: 'file-1',
      openai_file_id: 'file-1',
      vector_store_id: 'vs-1',
      filename: 'notes.txt',
      mime_type: 'text/plain',
      size_bytes: 1024,
      usage_bytes: 1024,
      status: 'processed',
      attributes: {},
      chunking_strategy: null,
      last_error: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ],
  total: 1,
};

export const mockVectorStoreSearch: VectorStoreSearchResponse = {
  data: [{ id: 'hit-1', score: 0.9 }],
};
