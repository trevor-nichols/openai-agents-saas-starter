import type { FeatureFlags } from '@/types/features';

export async function fetchFeatureFlags(): Promise<FeatureFlags> {
  const response = await fetch('/api/health/features', { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Feature flags request failed (${response.status}).`);
  }
  const payload = (await response.json()) as FeatureFlags | null;
  if (!payload) {
    throw new Error('Feature flags endpoint returned an empty payload.');
  }
  return payload;
}
