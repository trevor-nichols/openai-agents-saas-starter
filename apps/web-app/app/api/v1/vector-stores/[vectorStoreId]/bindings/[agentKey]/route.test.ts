import { describe, expect, it, vi, beforeEach } from 'vitest';

const getServerApiClient = vi.hoisted(() => vi.fn());
const bindAgentToVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyPost = vi.hoisted(() => vi.fn());
const unbindAgentFromVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyDelete = vi.hoisted(
  () => vi.fn(),
);

vi.mock('@/lib/server/apiClient', () => ({
  getServerApiClient,
}));

vi.mock('@/lib/api/client/sdk.gen', () => ({
  bindAgentToVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyPost,
  unbindAgentFromVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyDelete,
}));

async function loadHandlers() {
  vi.resetModules();
  return import('./route');
}

const params = { params: Promise.resolve({ vectorStoreId: 'vs-1', agentKey: 'agent-1' }) };

describe('/api/v1/vector-stores/[vectorStoreId]/bindings/[agentKey]', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('POST binds agent to vector store', async () => {
    getServerApiClient.mockResolvedValue({ client: 'client', auth: vi.fn() });
    bindAgentToVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyPost.mockResolvedValue({ data: undefined });
    const { POST } = await loadHandlers();

    const res = await POST({} as Request, params);

    expect(bindAgentToVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyPost).toHaveBeenCalledWith(
      expect.objectContaining({
        path: { vector_store_id: 'vs-1', agent_key: 'agent-1' },
      }),
    );
    expect(res.status).toBe(200);
    await expect(res.json()).resolves.toEqual({ success: true });
  });

  it('POST maps missing token to 401', async () => {
    getServerApiClient.mockRejectedValue(new Error('Missing access token'));
    const { POST } = await loadHandlers();

    const res = await POST({} as Request, params);

    expect(res.status).toBe(401);
    await expect(res.json()).resolves.toEqual({ message: 'Missing access token' });
  });

  it('POST maps not found to 404', async () => {
    getServerApiClient.mockResolvedValue({ client: 'client', auth: vi.fn() });
    bindAgentToVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyPost.mockRejectedValue(new Error('Not found'));
    const { POST } = await loadHandlers();

    const res = await POST({} as Request, params);

    expect(res.status).toBe(404);
    await expect(res.json()).resolves.toEqual({ message: 'Not found' });
  });

  it('DELETE unbinds agent from vector store', async () => {
    getServerApiClient.mockResolvedValue({ client: 'client', auth: vi.fn() });
    unbindAgentFromVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyDelete.mockResolvedValue({ data: undefined });
    const { DELETE } = await loadHandlers();

    const res = await DELETE({} as Request, params);

    expect(unbindAgentFromVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyDelete).toHaveBeenCalledWith(
      expect.objectContaining({
        path: { vector_store_id: 'vs-1', agent_key: 'agent-1' },
      }),
    );
    expect(res.status).toBe(200);
    await expect(res.json()).resolves.toEqual({ success: true });
  });

  it('DELETE maps missing token to 401', async () => {
    getServerApiClient.mockRejectedValue(new Error('Missing access token'));
    const { DELETE } = await loadHandlers();

    const res = await DELETE({} as Request, params);

    expect(res.status).toBe(401);
    await expect(res.json()).resolves.toEqual({ message: 'Missing access token' });
  });

  it('DELETE maps not found to 404', async () => {
    getServerApiClient.mockResolvedValue({ client: 'client', auth: vi.fn() });
    unbindAgentFromVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyDelete.mockRejectedValue(
      new Error('Not found'),
    );
    const { DELETE } = await loadHandlers();

    const res = await DELETE({} as Request, params);

    expect(res.status).toBe(404);
    await expect(res.json()).resolves.toEqual({ message: 'Not found' });
  });
});
