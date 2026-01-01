import { act, renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { getTenantPaginationMeta, useTenantOpsPagination } from '../useTenantOpsPagination';

describe('useTenantOpsPagination', () => {
  it('calculates pagination metadata', () => {
    const meta = getTenantPaginationMeta(60, 0, 25);
    expect(meta.pageCount).toBe(3);
    expect(meta.page).toBe(1);
    expect(meta.canPrev).toBe(false);
    expect(meta.canNext).toBe(true);

    const nextMeta = getTenantPaginationMeta(60, 50, 25);
    expect(nextMeta.page).toBe(3);
    expect(nextMeta.canNext).toBe(false);
  });

  it('advances and resets offset', () => {
    const { result } = renderHook(() => useTenantOpsPagination(25));

    expect(result.current.offset).toBe(0);

    act(() => {
      result.current.nextPage();
    });

    expect(result.current.offset).toBe(25);

    act(() => {
      result.current.prevPage();
    });

    expect(result.current.offset).toBe(0);

    act(() => {
      result.current.nextPage();
      result.current.nextPage();
    });

    expect(result.current.offset).toBe(50);

    act(() => {
      result.current.resetPage();
    });

    expect(result.current.offset).toBe(0);
  });
});
