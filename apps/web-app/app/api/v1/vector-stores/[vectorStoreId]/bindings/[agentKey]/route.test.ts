import { describe, expect, it, vi, beforeEach } from 'vitest';

const bindAgentToVectorStore = vi.hoisted(() => vi.fn());
const unbindAgentFromVectorStore = vi.hoisted(() => vi.fn());
class VectorStoreServiceError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = 'VectorStoreServiceError';
  }
}

vi.mock('@/lib/server/services/vectorStores', () => ({
  bindAgentToVectorStore,
  unbindAgentFromVectorStore,
  VectorStoreServiceError,
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
    bindAgentToVectorStore.mockResolvedValue(undefined);
    const { POST } = await loadHandlers();

    const res = await POST({} as Request, params);

    expect(bindAgentToVectorStore).toHaveBeenCalledWith('vs-1', 'agent-1');
    expect(res.status).toBe(200);
    await expect(res.json()).resolves.toEqual({ success: true });
  });

  it('POST maps missing token to 401', async () => {
    bindAgentToVectorStore.mockRejectedValue(new VectorStoreServiceError('Missing access token', 401));
    const { POST } = await loadHandlers();

    const res = await POST({} as Request, params);

    expect(res.status).toBe(401);
    await expect(res.json()).resolves.toEqual({ message: 'Missing access token' });
  });

  it('POST maps not found to 404', async () => {
    bindAgentToVectorStore.mockRejectedValue(new VectorStoreServiceError('Not found', 404));
    const { POST } = await loadHandlers();

    const res = await POST({} as Request, params);

    expect(res.status).toBe(404);
    await expect(res.json()).resolves.toEqual({ message: 'Not found' });
  });

  it('DELETE unbinds agent from vector store', async () => {
    unbindAgentFromVectorStore.mockResolvedValue(undefined);
    const { DELETE } = await loadHandlers();

    const res = await DELETE({} as Request, params);

    expect(unbindAgentFromVectorStore).toHaveBeenCalledWith('vs-1', 'agent-1');
    expect(res.status).toBe(200);
    await expect(res.json()).resolves.toEqual({ success: true });
  });

  it('DELETE maps missing token to 401', async () => {
    unbindAgentFromVectorStore.mockRejectedValue(new VectorStoreServiceError('Missing access token', 401));
    const { DELETE } = await loadHandlers();

    const res = await DELETE({} as Request, params);

    expect(res.status).toBe(401);
    await expect(res.json()).resolves.toEqual({ message: 'Missing access token' });
  });

  it('DELETE maps not found to 404', async () => {
    unbindAgentFromVectorStore.mockRejectedValue(new VectorStoreServiceError('Not found', 404));
    const { DELETE } = await loadHandlers();

    const res = await DELETE({} as Request, params);

    expect(res.status).toBe(404);
    await expect(res.json()).resolves.toEqual({ message: 'Not found' });
  });
});
