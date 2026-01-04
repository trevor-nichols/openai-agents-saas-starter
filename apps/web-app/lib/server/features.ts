'use server';

import { featureFlagsHealthFeaturesGet } from '@/lib/api/client/sdk.gen';
import { DEFAULT_FEATURE_FLAGS } from '@/lib/features/constants';
import { createApiClient } from '@/lib/server/apiClient';
import { getRequestOrigin } from '@/lib/server/requestOrigin';
import type { FeatureFlags } from '@/types/features';

type BackendFeatureFlags = {
  billing_enabled?: boolean;
  billing_stream_enabled?: boolean;
};

function toFeatureFlags(payload: BackendFeatureFlags | null): FeatureFlags {
  if (!payload) return DEFAULT_FEATURE_FLAGS;
  return {
    billingEnabled: Boolean(payload.billing_enabled),
    billingStreamEnabled: Boolean(payload.billing_stream_enabled),
  };
}

async function fetchJson<T>(url: string): Promise<{ data: T | null; status: number }> {
  const response = await fetch(url, { cache: 'no-store' });
  if (!response.ok) return { data: null, status: response.status };
  const data = (await response.json()) as T | null;
  return { data, status: response.status };
}

export async function getBackendFeatureFlags(): Promise<FeatureFlags> {
  const client = createApiClient();
  const payload = await featureFlagsHealthFeaturesGet({ client });
  if (!payload) {
    throw new Error('Feature flags endpoint returned an empty payload.');
  }
  return toFeatureFlags(payload as BackendFeatureFlags);
}

export async function getFeatureFlags(): Promise<FeatureFlags> {
  try {
    const origin = await getRequestOrigin();
    const { data, status } = await fetchJson<FeatureFlags>(`${origin}/api/health/features`);
    if (!data) {
      console.warn(`[features] Feature flags BFF returned ${status}.`);
      return DEFAULT_FEATURE_FLAGS;
    }
    return data;
  } catch (error) {
    console.warn('[features] Failed to load feature flags via BFF.', error);
    return DEFAULT_FEATURE_FLAGS;
  }
}

export async function isBillingEnabled(): Promise<boolean> {
  const flags = await getFeatureFlags();
  return flags.billingEnabled;
}
