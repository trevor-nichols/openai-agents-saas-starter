import { useMutation, useQuery } from '@tanstack/react-query';

import {
  fetchAccountSession,
  fetchTenantSubscriptionSummary,
  resendVerificationEmailRequest,
} from '@/lib/api/account';
import type { AccountProfileData, AccountSessionResponse } from '@/types/account';
import type { TenantSubscription } from '@/lib/types/billing';
import { queryKeys } from './keys';

interface AccountProfileQueryResult {
  profile: AccountProfileData;
  tenantError: Error | null;
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' ? (value as Record<string, unknown>) : null;
}

function asString(value: unknown): string | null {
  return typeof value === 'string' && value.length > 0 ? value : null;
}

function asBoolean(value: unknown): boolean | null {
  if (typeof value === 'boolean') {
    return value;
  }
  return null;
}

function resolveTenantId(
  session: AccountSessionResponse,
  payload: Record<string, unknown> | null,
): string | null {
  return (
    session.tenantId ??
    (payload
      ? asString(payload['tenant_id']) ??
        asString(payload['tenantId']) ??
        asString(payload['tenant'])
      : null)
  );
}

function mapAccountProfile(
  session: AccountSessionResponse,
  subscription: TenantSubscription | null,
): AccountProfileData {
  const payload = asRecord(session.profile?.token_payload ?? session.profile);

  const email = asString(payload?.['email']);
  const displayName = asString(payload?.['name']);
  const avatarUrl = asString(payload?.['avatar_url']);
  const role = asString(payload?.['tenant_role'] ?? payload?.['role']);
  const emailVerified = asBoolean(payload?.['email_verified']) ?? false;
  const tenantId = resolveTenantId(session, payload);
  const tenantName = asString(payload?.['tenant_name']);
  const tenantSlug = asString(payload?.['tenant_slug']);

  return {
    user: {
      id: asString(session.userId) ?? asString(session.profile?.user_id) ?? null,
      email,
      displayName,
      role,
      avatarUrl,
      emailVerified,
    },
    tenant: tenantId
      ? {
          id: tenantId,
          name: tenantName,
          slug: tenantSlug,
          planCode: subscription?.plan_code ?? null,
          seatCount: subscription?.seat_count ?? null,
          autoRenew: subscription?.auto_renew ?? null,
          currentPeriodStart: subscription?.current_period_start ?? null,
          currentPeriodEnd: subscription?.current_period_end ?? null,
          billingEmail: subscription?.billing_email ?? null,
        }
      : null,
    subscription,
    verification: {
      emailVerified,
    },
    session: {
      expiresAt: session.expiresAt ?? null,
      scopes: session.scopes ?? [],
    },
    raw: {
      session,
    },
  };
}

async function loadAccountProfile(): Promise<AccountProfileQueryResult> {
  const session = await fetchAccountSession();
  const payload = asRecord(session.profile?.token_payload ?? session.profile);
  const tenantId = resolveTenantId(session, payload);

  let subscription: TenantSubscription | null = null;
  let tenantError: Error | null = null;

  if (tenantId) {
    try {
      subscription = await fetchTenantSubscriptionSummary(tenantId);
    } catch (error) {
      tenantError = error instanceof Error ? error : new Error('Unable to load tenant subscription.');
    }
  }

  return {
    profile: mapAccountProfile(session, subscription),
    tenantError,
  };
}

export function useAccountProfileQuery(options?: { enabled?: boolean }) {
  const query = useQuery({
    queryKey: queryKeys.account.profile(),
    queryFn: loadAccountProfile,
    enabled: options?.enabled ?? true,
    staleTime: 30 * 1000,
  });

  return {
    profile: query.data?.profile ?? null,
    tenantError: query.data?.tenantError ?? null,
    isLoadingProfile: query.isLoading,
    profileError: query.error instanceof Error ? query.error : null,
    refetchProfile: query.refetch,
  };
}

export function useResendVerificationMutation() {
  return useMutation({
    mutationFn: resendVerificationEmailRequest,
  });
}
