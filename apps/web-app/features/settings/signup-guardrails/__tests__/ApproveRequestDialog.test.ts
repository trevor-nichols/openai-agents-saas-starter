import { describe, expect, it } from 'vitest';

import { approveSchema } from '../components/ApproveRequestDialog';

describe('approveSchema', () => {
  it('allows invite expiry input to be cleared', () => {
    const result = approveSchema.safeParse({
      inviteExpiresInHours: '',
      note: '',
    });

    expect(result.success).toBe(true);
    if (!result.success) {
      throw new Error(result.error.message);
    }

    expect(result.data.inviteExpiresInHours).toBeUndefined();
  });

  it('normalizes whitespace before coercing to a number', () => {
    const result = approveSchema.parse({
      inviteExpiresInHours: '  48 ',
      note: '',
    });

    expect(result.inviteExpiresInHours).toBe(48);
  });
});
