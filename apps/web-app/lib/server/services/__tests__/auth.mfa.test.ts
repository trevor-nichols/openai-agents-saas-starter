import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { listMfaMethods } from '../auth/mfa';

const getServerApiClient = vi.hoisted(() => vi.fn());
const listMfaMethodsApiV1AuthMfaGet = vi.hoisted(() => vi.fn());

vi.mock('../../apiClient', () => ({
  getServerApiClient,
}));

vi.mock('@/lib/api/client/sdk.gen', () => ({
  listMfaMethodsApiV1AuthMfaGet,
}));

describe('listMfaMethods', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns MFA methods from the SDK payload', async () => {
    const methods = [
      {
        id: 'mfa-1',
        method_type: 'totp',
        label: null,
        verified_at: '2025-01-01T00:00:00Z',
        last_used_at: null,
        revoked_at: null,
      },
    ];

    getServerApiClient.mockResolvedValue({ client: 'client', auth: 'auth' });
    listMfaMethodsApiV1AuthMfaGet.mockResolvedValue({ data: methods });

    const result = await listMfaMethods();

    expect(listMfaMethodsApiV1AuthMfaGet).toHaveBeenCalledWith({
      client: 'client',
      auth: 'auth',
      throwOnError: true,
      responseStyle: 'fields',
    });
    expect(result).toEqual(methods);
  });

  it('returns an empty array when the payload is missing', async () => {
    getServerApiClient.mockResolvedValue({ client: 'client', auth: 'auth' });
    listMfaMethodsApiV1AuthMfaGet.mockResolvedValue({ data: null });

    const result = await listMfaMethods();

    expect(result).toEqual([]);
  });
});
