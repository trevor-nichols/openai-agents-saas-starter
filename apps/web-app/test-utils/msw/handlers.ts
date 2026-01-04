import { http, HttpResponse } from 'msw';

import type { FeatureFlags } from '@/types/features';

const defaultFeatureFlags: FeatureFlags = {
  billingEnabled: true,
  billingStreamEnabled: true,
};

export const defaultHandlers = [
  http.get('/api/health/features', () => HttpResponse.json(defaultFeatureFlags)),
];
