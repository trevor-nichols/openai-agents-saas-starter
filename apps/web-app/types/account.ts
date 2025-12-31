import type { TenantSubscription } from '@/lib/types/billing';
import type { TeamRole } from '@/types/team';
import type { SessionResponse } from './session';

export interface AccountProfileTokenPayload {
  email?: string;
  email_verified?: boolean;
  name?: string;
  avatar_url?: string;
  tenant_id?: string;
  tenant_name?: string;
  tenant_slug?: string;
  tenant_role?: TeamRole;
  role?: TeamRole;
  [key: string]: unknown;
}

export interface AccountProfileEnvelope {
  user_id?: string;
  token_payload?: AccountProfileTokenPayload | null;
}

export interface AccountSessionResponse extends SessionResponse {
  profile?: AccountProfileEnvelope | null;
  scopes?: string[];
}

export interface AccountUserSummary {
  id: string | null;
  email: string | null;
  displayName: string | null;
  role: TeamRole | null;
  avatarUrl: string | null;
  emailVerified: boolean;
}

export interface AccountTenantSummary {
  id: string | null;
  name: string | null;
  slug: string | null;
  planCode: string | null;
  seatCount: number | null;
  autoRenew: boolean | null;
  currentPeriodStart: string | null;
  currentPeriodEnd: string | null;
  billingEmail: string | null;
}

export interface AccountProfileData {
  user: AccountUserSummary;
  tenant: AccountTenantSummary | null;
  subscription: TenantSubscription | null;
  verification: {
    emailVerified: boolean;
  };
  session: {
    expiresAt: string | null;
    scopes: string[];
  };
  raw: {
    session: AccountSessionResponse | null;
  };
}
