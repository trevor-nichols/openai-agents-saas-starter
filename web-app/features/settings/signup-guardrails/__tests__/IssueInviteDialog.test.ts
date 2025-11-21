import { describe, expect, it } from 'vitest';

import { issueInviteSchema } from '../components/IssueInviteDialog';

describe('issueInviteSchema', () => {
  it('allows invite email and expiry inputs to be omitted', () => {
    const result = issueInviteSchema.safeParse({
      invitedEmail: '',
      maxRedemptions: 1,
      expiresInHours: '',
      note: '',
    });

    expect(result.success).toBe(true);
    if (!result.success) {
      throw new Error(result.error.message);
    }

    expect(result.data.invitedEmail).toBeUndefined();
    expect(result.data.expiresInHours).toBeUndefined();
  });

  it('trims whitespace before validation', () => {
    const result = issueInviteSchema.parse({
      invitedEmail: '  operator@example.com  ',
      maxRedemptions: 1,
      expiresInHours: ' 24 ',
      note: '',
    });

    expect(result.invitedEmail).toBe('operator@example.com');
    expect(result.expiresInHours).toBe(24);
  });
});
