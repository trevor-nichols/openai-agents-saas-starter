import { act, renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { useTenantOpsFilters } from '../useTenantOpsFilters';

describe('useTenantOpsFilters', () => {
  it('applies and resets filters', () => {
    const { result } = renderHook(() => useTenantOpsFilters());

    expect(result.current.appliedStatus).toBe('active');
    expect(result.current.appliedQuery).toBe('');
    expect(result.current.appliedFilters.status).toBe('active');

    act(() => {
      result.current.setStatusFilter('all');
      result.current.setQuery('  acme  ');
    });

    act(() => {
      result.current.applyFilters();
    });

    expect(result.current.appliedStatus).toBe('all');
    expect(result.current.appliedQuery).toBe('acme');
    expect(result.current.appliedFilters.status).toBeUndefined();
    expect(result.current.appliedFilters.q).toBe('acme');

    act(() => {
      result.current.resetFilters();
    });

    expect(result.current.statusFilter).toBe('active');
    expect(result.current.query).toBe('');
    expect(result.current.appliedStatus).toBe('active');
    expect(result.current.appliedQuery).toBe('');
  });
});
