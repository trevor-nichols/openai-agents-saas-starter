'use server';

import { getFeatureSnapshotApiV1FeaturesGet } from '@/lib/api/client/sdk.gen';
import { DEFAULT_FEATURE_FLAGS } from '@/lib/features/constants';
import { getServerApiClient, type ServerApiClientContext } from '@/lib/server/apiClient';
import type { FeatureFlags } from '@/types/features';

type BackendFeatureFlags = {
  billing_enabled?: boolean;
  billing_stream_enabled?: boolean;
};

type SdkFieldsResult<T> =
  | {
      data: T;
      error: undefined;
      response: Response;
    }
  | {
      data: undefined;
      error: unknown;
      response: Response;
    };

export class FeatureFlagsApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'FeatureFlagsApiError';
  }
}

function toFeatureFlags(payload: BackendFeatureFlags | null): FeatureFlags {
  if (!payload) return DEFAULT_FEATURE_FLAGS;
  return {
    billingEnabled: Boolean(payload.billing_enabled),
    billingStreamEnabled: Boolean(payload.billing_stream_enabled),
  };
}

function mapErrorMessage(payload: unknown): string {
  if (payload instanceof Error) {
    return payload.message;
  }
  if (typeof payload === 'string') {
    return payload;
  }
  if (!payload || typeof payload !== 'object') {
    return 'Feature flags request failed.';
  }
  const record = payload as Record<string, unknown>;
  if (typeof record.detail === 'string') return record.detail;
  if (typeof record.message === 'string') return record.message;
  if (typeof record.error === 'string') return record.error;
  return 'Feature flags request failed.';
}

export async function getBackendFeatureFlags(): Promise<FeatureFlags> {
  let clientContext: ServerApiClientContext;
  try {
    clientContext = await getServerApiClient();
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Missing access token';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    throw new FeatureFlagsApiError(status, message);
  }

  const result = await getFeatureSnapshotApiV1FeaturesGet({
    client: clientContext.client,
    auth: clientContext.auth,
    responseStyle: 'fields',
    throwOnError: false,
  });
  const { data, error, response } = result as SdkFieldsResult<BackendFeatureFlags>;
  if (error) {
    throw new FeatureFlagsApiError(response.status || 502, mapErrorMessage(error));
  }
  if (!data) {
    throw new FeatureFlagsApiError(
      response.status || 502,
      'Feature flags endpoint returned an empty payload.',
    );
  }
  return toFeatureFlags(data);
}

export async function getFeatureFlags(): Promise<FeatureFlags> {
  try {
    return await getBackendFeatureFlags();
  } catch (error) {
    console.warn('[features] Failed to load backend feature flags.', error);
    return DEFAULT_FEATURE_FLAGS;
  }
}

export async function isBillingEnabled(): Promise<boolean> {
  const flags = await getFeatureFlags();
  return flags.billingEnabled;
}

export async function requireBillingFeature(): Promise<void> {
  const flags = await getBackendFeatureFlags();
  if (!flags.billingEnabled) {
    throw new FeatureFlagsApiError(403, 'Billing is disabled.');
  }
}

export async function requireBillingStreamFeature(): Promise<void> {
  const flags = await getBackendFeatureFlags();
  if (!flags.billingStreamEnabled) {
    throw new FeatureFlagsApiError(403, 'Billing stream is disabled.');
  }
}
