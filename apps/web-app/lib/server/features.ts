'use server';

import { featureFlagsHealthFeaturesGet } from '@/lib/api/client/sdk.gen';
import { createApiClient } from '@/lib/server/apiClient';
import { getSiteUrl } from '@/lib/seo/siteUrl';
import type { FeatureFlags } from '@/types/features';

const FALLBACK_FLAGS: FeatureFlags = {
  billingEnabled: false,
  billingStreamEnabled: false,
};

type BackendFeatureFlags = {
  billing_enabled?: boolean;
  billing_stream_enabled?: boolean;
};

function toFeatureFlags(payload: BackendFeatureFlags | null): FeatureFlags {
  if (!payload) return FALLBACK_FLAGS;
  return {
    billingEnabled: Boolean(payload.billing_enabled),
    billingStreamEnabled: Boolean(payload.billing_stream_enabled),
  };
}

async function fetchJson<T>(url: string): Promise<T | null> {
  const response = await fetch(url, { cache: 'no-store' });
  if (!response.ok) return null;
  return (await response.json()) as T | null;
}

export async function getBackendFeatureFlags(): Promise<FeatureFlags> {
  try {
    const client = createApiClient();
    const payload = await featureFlagsHealthFeaturesGet({ client });
    return toFeatureFlags(payload as BackendFeatureFlags);
  } catch (error) {
    console.warn('[features] Failed to load backend feature flags.', error);
    return FALLBACK_FLAGS;
  }
}

export async function getFeatureFlags(): Promise<FeatureFlags> {
  try {
    const baseUrl = getSiteUrl();
    const payload = await fetchJson<FeatureFlags>(`${baseUrl}/api/health/features`);
    return payload ?? FALLBACK_FLAGS;
  } catch (error) {
    console.warn('[features] Failed to load feature flags via BFF.', error);
    return FALLBACK_FLAGS;
  }
}

export async function isBillingEnabled(): Promise<boolean> {
  const flags = await getFeatureFlags();
  return flags.billingEnabled;
}
