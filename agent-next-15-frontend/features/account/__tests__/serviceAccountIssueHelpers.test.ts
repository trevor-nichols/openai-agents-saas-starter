import { describe, expect, it } from 'vitest';

import {
  buildIssuePayload,
  createDefaultIssueForm,
  parseScopesInput,
  type ServiceAccountIssueFormValues,
} from '../serviceAccountIssueHelpers';

describe('createDefaultIssueForm', () => {
  it('prefills tenant id when provided', () => {
    const form = createDefaultIssueForm('tenant-1');
    expect(form.tenantId).toBe('tenant-1');
    expect(form.account).toBe('');
  });
});

describe('parseScopesInput', () => {
  it('splits by comma and newline and trims whitespace', () => {
    expect(parseScopesInput('billing:use, conversations:read\nlogs:read')).toEqual([
      'billing:use',
      'conversations:read',
      'logs:read',
    ]);
  });
});

describe('buildIssuePayload', () => {
  const baseForm: ServiceAccountIssueFormValues = {
    account: 'ci',
    scopes: 'conversations:read',
    tenantId: null,
    lifetimeMinutes: 30,
    fingerprint: 'runner-1',
    force: true,
    reason: 'Rotate weekly CI credential',
  };

  it('returns normalized payload when valid', () => {
    const payload = buildIssuePayload(baseForm, 'tenant-default');
    expect(payload).toMatchObject({
      account: 'ci',
      scopes: ['conversations:read'],
      tenantId: 'tenant-default',
      lifetimeMinutes: 30,
      fingerprint: 'runner-1',
      force: true,
    });
  });

  it('throws when required fields are missing', () => {
    expect(() => buildIssuePayload({ ...baseForm, account: ' ' }, null)).toThrow();
    expect(() => buildIssuePayload({ ...baseForm, scopes: '' }, null)).toThrow('Add at least one scope');
    expect(() => buildIssuePayload({ ...baseForm, reason: 'short' }, null)).toThrow('Reason must be at least 10 characters.');
  });
});
