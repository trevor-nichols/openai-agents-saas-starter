import { describe, expect, it } from 'vitest';

import { isMfaChallengeResponse, resolveSafeRedirect, resolveTenantSelector } from '@/lib/auth/sso';

describe('resolveTenantSelector', () => {
  it('returns null for empty values', () => {
    expect(resolveTenantSelector('')).toBeNull();
    expect(resolveTenantSelector('   ')).toBeNull();
    expect(resolveTenantSelector(undefined)).toBeNull();
  });

  it('returns tenant_id for UUID-like values', () => {
    const selector = resolveTenantSelector('11111111-2222-3333-4444-555555555555');
    expect(selector).toEqual({ tenant_id: '11111111-2222-3333-4444-555555555555' });
  });

  it('returns tenant_slug for non-UUID values', () => {
    const selector = resolveTenantSelector('acme');
    expect(selector).toEqual({ tenant_slug: 'acme' });
  });
});

describe('resolveSafeRedirect', () => {
  it('rejects unsafe redirect targets', () => {
    expect(resolveSafeRedirect('https://example.com')).toBeNull();
    expect(resolveSafeRedirect('//example.com')).toBeNull();
    expect(resolveSafeRedirect('')).toBeNull();
  });

  it('accepts safe relative paths', () => {
    expect(resolveSafeRedirect('/dashboard')).toBe('/dashboard');
  });
});

describe('isMfaChallengeResponse', () => {
  it('detects MFA challenge payloads', () => {
    expect(isMfaChallengeResponse({ challenge_token: 'token', methods: [] })).toBe(true);
    expect(isMfaChallengeResponse({ access_token: 'token' })).toBe(false);
  });
});
