import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  listConsents,
  listNotificationPreferences,
  recordConsent,
  upsertNotificationPreference,
} from '../users';

const getServerApiClient = vi.hoisted(() => vi.fn());
const listConsentsApiV1UsersConsentsGet = vi.hoisted(() => vi.fn());
const recordConsentApiV1UsersConsentsPost = vi.hoisted(() => vi.fn());
const listNotificationPreferencesApiV1UsersNotificationPreferencesGet = vi.hoisted(() => vi.fn());
const upsertNotificationPreferenceApiV1UsersNotificationPreferencesPut = vi.hoisted(() => vi.fn());

vi.mock('../../apiClient', () => ({
  getServerApiClient,
}));

vi.mock('@/lib/api/client/sdk.gen', () => ({
  listConsentsApiV1UsersConsentsGet,
  recordConsentApiV1UsersConsentsPost,
  listNotificationPreferencesApiV1UsersNotificationPreferencesGet,
  upsertNotificationPreferenceApiV1UsersNotificationPreferencesPut,
}));

describe('users service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('lists consents using response metadata', async () => {
    const payload = [
      {
        policy_key: 'privacy',
        version: 'v1',
        accepted_at: '2025-01-01T00:00:00Z',
      },
    ];

    getServerApiClient.mockResolvedValue({ client: 'client', auth: 'auth' });
    listConsentsApiV1UsersConsentsGet.mockResolvedValue({ data: payload });

    const result = await listConsents();

    expect(listConsentsApiV1UsersConsentsGet).toHaveBeenCalledWith({
      client: 'client',
      auth: 'auth',
      throwOnError: true,
      responseStyle: 'fields',
    });
    expect(result).toEqual(payload);
  });

  it('records a consent and returns the response payload', async () => {
    const request = { policy_key: 'privacy', version: 'v2' };
    const response = { success: true, message: 'ok', data: null };

    getServerApiClient.mockResolvedValue({ client: 'client', auth: 'auth' });
    recordConsentApiV1UsersConsentsPost.mockResolvedValue({ data: response });

    const result = await recordConsent(request);

    expect(recordConsentApiV1UsersConsentsPost).toHaveBeenCalledWith({
      client: 'client',
      auth: 'auth',
      throwOnError: true,
      responseStyle: 'fields',
      body: request,
    });
    expect(result).toEqual(response);
  });

  it('lists notification preferences with tenant headers', async () => {
    const payload = [
      {
        id: 'pref-1',
        channel: 'email',
        category: 'status',
        enabled: true,
        tenant_id: 'tenant-1',
      },
    ];

    getServerApiClient.mockResolvedValue({ client: 'client', auth: 'auth' });
    listNotificationPreferencesApiV1UsersNotificationPreferencesGet.mockResolvedValue({ data: payload });

    const result = await listNotificationPreferences({
      tenantId: 'tenant-1',
      tenantRole: 'admin',
    });

    expect(listNotificationPreferencesApiV1UsersNotificationPreferencesGet).toHaveBeenCalledWith({
      client: 'client',
      auth: 'auth',
      throwOnError: true,
      responseStyle: 'fields',
      headers: { 'X-Tenant-Id': 'tenant-1', 'X-Tenant-Role': 'admin' },
    });
    expect(result).toEqual(payload);
  });

  it('upserts a notification preference and returns the payload', async () => {
    const request = { channel: 'email', category: 'status', enabled: true };
    const response = {
      id: 'pref-2',
      channel: 'email',
      category: 'status',
      enabled: true,
      tenant_id: 'tenant-1',
    };

    getServerApiClient.mockResolvedValue({ client: 'client', auth: 'auth' });
    upsertNotificationPreferenceApiV1UsersNotificationPreferencesPut.mockResolvedValue({ data: response });

    const result = await upsertNotificationPreference(request, {
      tenantId: 'tenant-1',
      tenantRole: 'member',
    });

    expect(upsertNotificationPreferenceApiV1UsersNotificationPreferencesPut).toHaveBeenCalledWith({
      client: 'client',
      auth: 'auth',
      throwOnError: true,
      responseStyle: 'fields',
      body: request,
      headers: { 'X-Tenant-Id': 'tenant-1', 'X-Tenant-Role': 'member' },
    });
    expect(result).toEqual(response);
  });
});
