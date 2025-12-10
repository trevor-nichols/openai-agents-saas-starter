import type { AccountProfileData } from '@/types/account';
import type { SessionRow } from '@/lib/queries/accountSessions';
import type {
  ServiceAccountIssueResult,
  ServiceAccountTokenRow,
} from '@/types/serviceAccounts';

export const mockAccountProfile: AccountProfileData = {
  user: {
    id: 'user-123',
    email: 'ash@example.com',
    displayName: 'Ash Example',
    role: 'admin',
    avatarUrl: 'https://avatars.githubusercontent.com/u/123?v=4',
    emailVerified: false,
  },
  tenant: {
    id: 'tenant-123',
    name: 'Acme Labs',
    slug: 'acme-labs',
    planCode: 'pro',
    seatCount: 12,
    autoRenew: true,
    currentPeriodStart: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    currentPeriodEnd: new Date(Date.now() + 21 * 24 * 60 * 60 * 1000).toISOString(),
    billingEmail: 'billing@acme.example',
  },
  subscription: null,
  verification: {
    emailVerified: false,
  },
  session: {
    expiresAt: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
    scopes: ['support:read', 'service_accounts:write'],
  },
  raw: {
    session: {
      profile: {
        token_payload: {
          email: 'ash@example.com',
          email_verified: false,
          name: 'Ash Example',
          tenant_id: 'tenant-123',
          tenant_name: 'Acme Labs',
          tenant_slug: 'acme-labs',
          tenant_role: 'admin',
          role: 'admin',
          last_login_at: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
          password_changed_at: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
        },
      },
      expiresAt: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
      scopes: ['support:read', 'service_accounts:write'],
    },
  },
};

export const mockSessions: SessionRow[] = [
  {
    id: 'sess-current',
    current: true,
    created_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
    last_seen_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
    revoked_at: null,
    ip_address_masked: '203.0.113.24',
    location: { city: 'San Francisco', region: 'CA', country: 'US' },
    client: { device: 'MacBook Pro', platform: 'macOS 15.2', browser: 'Arc' },
    tenant_id: 'tenant-123',
  },
  {
    id: 'sess-secondary',
    current: false,
    created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    last_seen_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    revoked_at: null,
    ip_address_masked: '198.51.100.9',
    location: { city: 'New York', region: 'NY', country: 'US' },
    client: { device: 'iPhone 15', platform: 'iOS 18', browser: 'Safari' },
    tenant_id: 'tenant-123',
  },
  {
    id: 'sess-revoked',
    current: false,
    created_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
    last_seen_at: new Date(Date.now() - 9 * 24 * 60 * 60 * 1000).toISOString(),
    revoked_at: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString(),
    ip_address_masked: '203.0.113.77',
    location: { city: 'Chicago', region: 'IL', country: 'US' },
    client: { device: 'Windows Laptop', platform: 'Windows 11', browser: 'Chrome' },
    tenant_id: 'tenant-123',
  },
];

export const mockServiceAccountTokens: ServiceAccountTokenRow[] = [
  {
    id: 'sat-001',
    account: 'automation-bot',
    tenantId: 'tenant-123',
    scopes: ['conversations:read', 'conversations:write'],
    issuedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    revokedAt: null,
    revokedReason: null,
    fingerprint: 'fp:abcd1234',
    signingKeyId: 'kid-01',
  },
  {
    id: 'sat-002',
    account: 'data-sync',
    tenantId: 'tenant-123',
    scopes: ['billing:read'],
    issuedAt: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
    expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    revokedAt: null,
    revokedReason: null,
    fingerprint: 'fp:efgh5678',
    signingKeyId: 'kid-02',
  },
  {
    id: 'sat-003',
    account: 'retired-bot',
    tenantId: 'tenant-123',
    scopes: ['workflows:read'],
    issuedAt: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
    expiresAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    revokedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    revokedReason: 'Rotated',
    fingerprint: 'fp:ijkl9012',
    signingKeyId: 'kid-03',
  },
];

export const mockIssueResult: ServiceAccountIssueResult = {
  refreshToken: 'sat_refresh_token_mock',
  account: 'automation-bot',
  tenantId: 'tenant-123',
  scopes: ['conversations:read', 'conversations:write'],
  expiresAt: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString(),
  issuedAt: new Date().toISOString(),
  kid: 'kid-issue',
  tokenUse: 'service_account',
};

export const mockNotificationPreferences = [
  { id: 'np-1', channel: 'email', category: 'security', enabled: true },
  { id: 'np-2', channel: 'email', category: 'billing', enabled: true },
  { id: 'np-3', channel: 'sms', category: 'security', enabled: false },
  { id: 'np-4', channel: 'in_app', category: 'product_updates', enabled: true },
];

export const mockConsents = [
  {
    policy_key: 'terms_of_service',
    version: 2,
    accepted_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    policy_key: 'privacy_policy',
    version: 3,
    accepted_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
  },
];

export const mockIssuedTokenText =
  'eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCIsInBrZyI6ImVkMjU1MTkifQ.eyJzdWIiOiJzYXRfMDAxIiwic2MiOlsic2VydmljZV9hY2NvdW50Il0sImF1ZCI6InNlcnZpY2UtYWNjb3VudCIsImV4cCI6MTcwMDAwMDAwMH0.mock-signature';
