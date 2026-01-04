import { vi } from 'vitest';
import type { NextRequest } from 'next/server';

import { DELETE } from './route';

const deleteWorkflowRun = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/workflows', () => ({
  deleteWorkflowRun,
}));

describe('DELETE /api/v1/workflows/runs/[runId]', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('forwards delete to backend and returns 204 on success', async () => {
    deleteWorkflowRun.mockResolvedValue({ status: 204, data: null });

    const request = {
      url: 'http://localhost/api/v1/workflows/runs/run-1?hard=true&reason=cleanup',
    } as unknown as NextRequest;

    const response = await DELETE(request, { params: Promise.resolve({ runId: 'run-1' }) });

    expect(deleteWorkflowRun).toHaveBeenCalledWith({ runId: 'run-1', hard: true, reason: 'cleanup' });
    expect(response.status).toBe(204);
  });

  it('returns 404 when backend reports not found', async () => {
    deleteWorkflowRun.mockResolvedValue({
      status: 404,
      error: { message: 'Workflow run not found', detail: 'Workflow run not found' },
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
    deleteWorkflowRun.mockResolvedValue({
      status: 409,
      error: {
        message: 'Hard delete blocked by retention window',
        detail: 'Hard delete blocked by retention window',
      },
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
    deleteWorkflowRun.mockRejectedValue(new Error('Missing access token'));

    const request = { url: 'http://localhost/api/v1/workflows/runs/run-1' } as unknown as NextRequest;

    const response = await DELETE(request, { params: Promise.resolve({ runId: 'run-1' }) });

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toMatchObject({ message: 'Missing access token', detail: 'Missing access token' });
  });
});
