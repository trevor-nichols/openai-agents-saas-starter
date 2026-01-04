import { createClient, createConfig, type Client } from '@/lib/api/client/client';
import { API_BASE_URL } from '@/lib/config/server';
import { getAccessTokenFromCookies } from '@/lib/auth/cookies';

/**
 * Minimal context returned by {@link getServerApiClient}. It bundles the
 * generated HeyAPI client with an auth callback so downstream service
 * functions can pass it straight into SDK calls.
 */
export interface ServerApiClientContext {
  client: Client;
  /**
   * Callback consumed by the generated SDK to attach bearer auth headers.
   * It is intentionally stable per-request so multiple SDK calls share the
 *   same token without repeatedly hitting the cookie store.
   */
  auth: () => string;
}

const normalizedBaseUrl = API_BASE_URL.endsWith('/')
  ? API_BASE_URL.slice(0, -1)
  : API_BASE_URL;

export function getApiBaseUrl(): string {
  return normalizedBaseUrl;
}

const baseConfig = createConfig({
  baseUrl: normalizedBaseUrl,
  responseStyle: 'data',
  throwOnError: true,
});

/**
 * Create a bare client without any attached auth.
 * Useful for public endpoints (login/refresh) that do not require bearer tokens.
 */
export function createApiClient(): Client {
  return createClient(baseConfig);
}

/**
 * Return a per-request API client that automatically injects the caller's
 * bearer token. Callers should catch and handle the thrown error to surface
 * auth failures in a user-friendly way.
 */
export async function getServerApiClient(): Promise<ServerApiClientContext> {
  const token = await getAccessTokenFromCookies();

  if (!token) {
    throw new Error('Missing access token');
  }

  return {
    client: createApiClient(),
    auth: () => token,
  };
}

/**
 * Helper to run a block with an authenticated API client. Useful when the
 * calling code prefers functional composition instead of manual context wiring.
 */
export async function withServerApiClient<T>(
  handler: (context: ServerApiClientContext) => Promise<T>,
): Promise<T> {
  const context = await getServerApiClient();
  return handler(context);
}
