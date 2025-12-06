import { describe, expect, it } from 'vitest';

import type { IncidentRecord } from '@/types/status';

import { getActiveIncidentId } from '../hooks/useIncidentReplayState';

const incidents: IncidentRecord[] = [
  { id: 'inc-1', service: 'api', occurredAt: '2025-01-01T00:00:00Z', impact: 'major', state: 'open' },
  { id: 'inc-2', service: 'web', occurredAt: '2025-01-02T00:00:00Z', impact: 'maintenance', state: 'resolved' },
];

describe('getActiveIncidentId', () => {
  it('falls back to the first incident when none is selected', () => {
    expect(getActiveIncidentId(null, incidents)).toBe('inc-1');
    expect(getActiveIncidentId('', incidents)).toBe('inc-1');
  });

  it('returns the selected incident when it exists', () => {
    expect(getActiveIncidentId('inc-2', incidents)).toBe('inc-2');
  });

  it('returns empty string when no incidents are available', () => {
    expect(getActiveIncidentId(null, [])).toBe('');
  });
});
