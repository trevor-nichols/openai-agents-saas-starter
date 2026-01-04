import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { listUsage } from '../usage';

const getServerApiClient = vi.hoisted(() => vi.fn());
const listUsageApiV1UsageGet = vi.hoisted(() => vi.fn());

vi.mock('../../apiClient', () => ({
  getServerApiClient,
}));

vi.mock('@/lib/api/client/sdk.gen', () => ({
  listUsageApiV1UsageGet,
}));

describe('listUsage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns usage counters and forwards tenant headers', async () => {
    const payload = [
      {
        id: 'usage-1',
        tenant_id: 'tenant-1',
        user_id: null,
        period_start: '2025-01-01T00:00:00Z',
        granularity: 'day',
        input_tokens: 10,
        output_tokens: 5,
        requests: 2,
        storage_bytes: 0,
        updated_at: '2025-01-02T00:00:00Z',
      },
    ];

    getServerApiClient.mockResolvedValue({ client: 'client', auth: 'auth' });
    listUsageApiV1UsageGet.mockResolvedValue({ data: payload });

    const result = await listUsage({
      tenantId: 'tenant-1',
      tenantRole: 'viewer',
    });

    expect(listUsageApiV1UsageGet).toHaveBeenCalledWith({
      client: 'client',
      auth: 'auth',
      throwOnError: true,
      responseStyle: 'fields',
      headers: { 'X-Tenant-Id': 'tenant-1', 'X-Tenant-Role': 'viewer' },
    });
    expect(result).toEqual(payload);
  });

  it('returns an empty array when the payload is missing', async () => {
    getServerApiClient.mockResolvedValue({ client: 'client', auth: 'auth' });
    listUsageApiV1UsageGet.mockResolvedValue({ data: null });

    const result = await listUsage();

    expect(result).toEqual([]);
  });
});
