import { useCallback, useState } from 'react';

interface TenantPaginationMeta {
  canPrev: boolean;
  canNext: boolean;
  page: number;
  pageCount: number;
}

export function getTenantPaginationMeta(total: number, offset: number, limit: number): TenantPaginationMeta {
  const safeTotal = Math.max(0, total);
  const pageCount = Math.max(1, Math.ceil(safeTotal / limit));
  const page = Math.min(pageCount, Math.floor(offset / limit) + 1);
  const canPrev = offset > 0;
  const canNext = offset + limit < safeTotal;

  return {
    canPrev,
    canNext,
    page,
    pageCount,
  };
}

interface UseTenantOpsPaginationResult {
  offset: number;
  limit: number;
  nextPage: () => void;
  prevPage: () => void;
  resetPage: () => void;
}

export function useTenantOpsPagination(limit: number): UseTenantOpsPaginationResult {
  const [offset, setOffset] = useState(0);

  const resetPage = useCallback(() => {
    setOffset(0);
  }, []);

  const prevPage = useCallback(() => {
    setOffset((current) => Math.max(0, current - limit));
  }, [limit]);

  const nextPage = useCallback(() => {
    setOffset((current) => current + limit);
  }, [limit]);

  return {
    offset,
    limit,
    nextPage,
    prevPage,
    resetPage,
  };
}
