import { describe, expect, it } from 'vitest';

import { entriesToRecord, recordToEntries } from '../utils';

describe('tenant settings utils', () => {
  it('round-trips metadata entries', () => {
    const record = { plan: 'enterprise', seats: '100' };
    const entries = recordToEntries(record);
    const next = entriesToRecord(entries);
    expect(next).toEqual(record);
  });

  it('omits blank keys when serializing', () => {
    const entries = [
      { id: '1', key: 'plan', value: 'pro' },
      { id: '2', key: '   ', value: 'ignore' },
    ];
    expect(entriesToRecord(entries)).toEqual({ plan: 'pro' });
  });
});
