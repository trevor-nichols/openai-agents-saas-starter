import 'server-only';

import { createClient, createConfig, type Client } from '@/lib/api/fixtures-client/client';
import { getApiBaseUrl } from './apiBaseUrl';

const baseConfig = createConfig({
  baseUrl: getApiBaseUrl(),
  responseStyle: 'fields',
  throwOnError: true,
});

export function createFixturesApiClient(): Client {
  return createClient(baseConfig);
}
