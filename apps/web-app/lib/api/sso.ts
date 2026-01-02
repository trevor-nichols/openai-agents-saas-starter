import type {
  MfaChallengeResponse,
  SsoProviderView,
  SsoStartRequest,
  SsoStartResponse,
} from '@/lib/api/client/types.gen';
import type { TenantSelector } from '@/lib/auth/sso';
import { apiV1Path } from '@/lib/apiPaths';

export type SsoStartInput = {
  provider: string;
  tenantSelector: TenantSelector;
  loginHint?: string | null;
  redirectTo?: string | null;
};

export type SsoCallbackInput = {
  provider: string;
  code: string;
  state: string;
};

export type SsoCallbackResult =
  | { status: 'authenticated'; redirect_to: string }
  | { status: 'mfa_required'; redirect_to: string; mfa: MfaChallengeResponse };

async function parseJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch (_error) {
    throw new Error('Failed to parse response from server.');
  }
}

export async function fetchSsoProviders(selector: TenantSelector): Promise<SsoProviderView[]> {
  const search = new URLSearchParams();
  if ('tenant_id' in selector && selector.tenant_id) {
    search.set('tenant_id', selector.tenant_id);
  }
  if ('tenant_slug' in selector && selector.tenant_slug) {
    search.set('tenant_slug', selector.tenant_slug);
  }

  const response = await fetch(`${apiV1Path('/auth/sso/providers')}?${search.toString()}`, {
    cache: 'no-store',
  });
  const data = await parseJson<{ providers: SsoProviderView[] } | { message?: string }>(response);

  if (!response.ok) {
    throw new Error((data as { message?: string }).message ?? 'Failed to load SSO providers.');
  }

  return (data as { providers: SsoProviderView[] }).providers ?? [];
}

export async function startSsoLogin(input: SsoStartInput): Promise<SsoStartResponse> {
  const payload: SsoStartRequest & { redirect_to?: string | null } = {
    ...input.tenantSelector,
    login_hint: input.loginHint ?? null,
    redirect_to: input.redirectTo ?? null,
  };

  const response = await fetch(apiV1Path(`/auth/sso/${encodeURIComponent(input.provider)}/start`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });

  const data = await parseJson<SsoStartResponse | { message?: string }>(response);

  if (!response.ok) {
    throw new Error((data as { message?: string }).message ?? 'Failed to start SSO.');
  }

  return data as SsoStartResponse;
}

export async function completeSsoCallback(input: SsoCallbackInput): Promise<SsoCallbackResult> {
  const response = await fetch(apiV1Path(`/auth/sso/${encodeURIComponent(input.provider)}/callback`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code: input.code, state: input.state }),
    cache: 'no-store',
  });

  const data = await parseJson<SsoCallbackResult | { message?: string }>(response);

  if (!response.ok) {
    throw new Error((data as { message?: string }).message ?? 'Failed to complete SSO login.');
  }

  return data as SsoCallbackResult;
}
