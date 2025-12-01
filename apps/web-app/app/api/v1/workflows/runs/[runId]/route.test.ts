import { vi } from 'vitest';
import type { NextRequest } from 'next/server';

import { DELETE } from './route';

const getServerApiClient = vi.hoisted(() => vi.fn());
const deleteWorkflowRunApiV1WorkflowsRunsRunIdDelete = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/apiClient', () => ({
  getServerApiClient,
}));

vi.mock('@/lib/api/client/sdk.gen', () => ({
  deleteWorkflowRunApiV1WorkflowsRunsRunIdDelete,
}));

describe('DELETE /api/v1/workflows/runs/[runId]', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('forwards delete to backend and returns 204 on success', async () => {
    getServerApiClient.mockResolvedValue({ client: {}, auth: vi.fn() });
    deleteWorkflowRunApiV1WorkflowsRunsRunIdDelete.mockResolvedValue({
      data: null,
      error: undefined,
      response: new Response(null, { status: 204 }),
    });

    const request = {
      url: 'http://localhost/api/v1/workflows/runs/run-1?hard=true&reason=cleanup',
    } as unknown as NextRequest;

    const response = await DELETE(request, { params: Promise.resolve({ runId: 'run-1' }) });

    expect(deleteWorkflowRunApiV1WorkflowsRunsRunIdDelete).toHaveBeenCalledWith(
      expect.objectContaining({
        path: { run_id: 'run-1' },
        query: { hard: true, reason: 'cleanup' },
        throwOnError: false,
      }),
    );
    expect(response.status).toBe(204);
  });

  it('returns 404 when backend reports not found', async () => {
    getServerApiClient.mockResolvedValue({ client: {}, auth: vi.fn() });
    deleteWorkflowRunApiV1WorkflowsRunsRunIdDelete.mockResolvedValue({
      data: undefined,
      error: 'Workflow run not found',
      response: new Response(JSON.stringify({ detail: 'Workflow run not found' }), { status: 404 }),
    });

    const request = { url: 'http://localhost/api/v1/workflows/runs/missing' } as unknown as NextRequest;

    const response = await DELETE(request, { params: Promise.resolve({ runId: 'missing' }) });

    expect(response.status).toBe(404);
    await expect(response.json()).resolves.toMatchObject({
      message: 'Workflow run not found',
      detail: 'Workflow run not found',
    });
  });

  it('returns 409 when retention guard blocks hard delete', async () => {
    getServerApiClient.mockResolvedValue({ client: {}, auth: vi.fn() });
    deleteWorkflowRunApiV1WorkflowsRunsRunIdDelete.mockResolvedValue({
      data: undefined,
      error: 'Hard delete blocked by retention window',
      response: new Response(JSON.stringify({ detail: 'Hard delete blocked by retention window' }), {
        status: 409,
      }),
    });

    const request = { url: 'http://localhost/api/v1/workflows/runs/run-1?hard=true' } as unknown as NextRequest;

    const response = await DELETE(request, { params: Promise.resolve({ runId: 'run-1' }) });

    expect(response.status).toBe(409);
    await expect(response.json()).resolves.toMatchObject({
      message: 'Hard delete blocked by retention window',
      detail: 'Hard delete blocked by retention window',
    });
  });

  it('returns 401 when missing access token', async () => {
    getServerApiClient.mockRejectedValue(new Error('Missing access token'));

    const request = { url: 'http://localhost/api/v1/workflows/runs/run-1' } as unknown as NextRequest;

    const response = await DELETE(request, { params: Promise.resolve({ runId: 'run-1' }) });

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toMatchObject({ message: 'Missing access token', detail: 'Missing access token' });
  });
});
