import { DEFAULT_FEATURE_FLAGS } from '@/lib/features/constants';
import type { FeatureFlags } from '@/types/features';

export async function fetchFeatureFlags(): Promise<FeatureFlags> {
  try {
    const response = await fetch('/api/v1/features', { cache: 'no-store' });
    if (!response.ok) {
      return DEFAULT_FEATURE_FLAGS;
    }
    const payload = (await response.json()) as FeatureFlags | null;
    if (!payload) {
      return DEFAULT_FEATURE_FLAGS;
    }
    return payload;
  } catch (error) {
    console.warn('[features] Feature flags request failed.', error);
    return DEFAULT_FEATURE_FLAGS;
  }
}
