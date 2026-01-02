import { describe, expect, it } from 'vitest';

import {
  isMfaChallengeResponse,
  resolveSafeRedirect,
  resolveTenantSelection,
} from '@/lib/auth/sso';

describe('resolveTenantSelection', () => {
  it('returns null for empty values', () => {
    expect(resolveTenantSelection({ tenantId: '', tenantSlug: '' })).toEqual({
      selector: null,
      conflict: false,
    });
    expect(resolveTenantSelection({ tenantId: '   ', tenantSlug: undefined })).toEqual({
      selector: null,
      conflict: false,
    });
    expect(resolveTenantSelection({ tenantId: undefined, tenantSlug: undefined })).toEqual({
      selector: null,
      conflict: false,
    });
  });

  it('returns tenant_id when tenantId is provided', () => {
    const selection = resolveTenantSelection({
      tenantId: '11111111-2222-3333-4444-555555555555',
      tenantSlug: '',
    });
    expect(selection).toEqual({
      selector: { tenant_id: '11111111-2222-3333-4444-555555555555' },
      conflict: false,
    });
  });

  it('returns tenant_slug when tenantSlug is provided', () => {
    const selection = resolveTenantSelection({ tenantId: null, tenantSlug: 'acme' });
    expect(selection).toEqual({ selector: { tenant_slug: 'acme' }, conflict: false });
  });

  it('flags conflicts when both tenantId and tenantSlug are provided', () => {
    const selection = resolveTenantSelection({
      tenantId: 'tenant-1',
      tenantSlug: 'acme',
    });
    expect(selection).toEqual({ selector: null, conflict: true });
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
