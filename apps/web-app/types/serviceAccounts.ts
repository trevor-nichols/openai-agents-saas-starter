import type { ServiceAccountTokenStatus } from '@/lib/api/client/types.gen';

export type ServiceAccountStatusFilter = ServiceAccountTokenStatus;

export interface ServiceAccountTokenSummary {
  id: string;
  account: string;
  tenantId: string | null;
  scopes: string[];
  issuedAt: string;
  expiresAt: string;
  revokedAt: string | null;
  revokedReason?: string | null;
  fingerprint?: string | null;
  signingKeyId: string;
}

export interface ServiceAccountTokenListResult {
  tokens: ServiceAccountTokenSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface ServiceAccountTokenQueryParams {
  account?: string | null;
  fingerprint?: string | null;
  status?: ServiceAccountStatusFilter;
  tenantId?: string | null;
  includeGlobal?: boolean;
  limit?: number;
  offset?: number;
}

export type ServiceAccountTokenRow = ServiceAccountTokenSummary;

export type ServiceAccountIssueMode = 'browser' | 'vault';

interface ServiceAccountIssueBasePayload {
  account: string;
  scopes: string[];
  tenantId: string | null;
  lifetimeMinutes?: number | null;
  fingerprint?: string | null;
  force?: boolean;
  reason: string;
}

export interface BrowserServiceAccountIssuePayload extends ServiceAccountIssueBasePayload {
  mode: 'browser';
}

export interface VaultServiceAccountIssuePayload extends ServiceAccountIssueBasePayload {
  mode: 'vault';
  vaultAuthorization: string;
  vaultPayload?: string | null;
}

export type ServiceAccountIssuePayload =
  | BrowserServiceAccountIssuePayload
  | VaultServiceAccountIssuePayload;

export interface ServiceAccountIssueResult {
  refreshToken: string;
  account: string;
  tenantId: string | null;
  scopes: string[];
  expiresAt: string;
  issuedAt: string;
  kid: string;
  tokenUse: string;
}
