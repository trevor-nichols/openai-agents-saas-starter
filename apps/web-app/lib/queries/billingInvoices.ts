import { useInfiniteQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import { fetchBillingInvoices } from '@/lib/api/billingInvoices';
import { readClientSessionMeta } from '@/lib/auth/clientMeta';
import { billingEnabled } from '@/lib/config/features';
import type { BillingInvoice, BillingInvoiceListResponse } from '@/types/billing';

import { queryKeys } from './keys';

interface UseBillingInvoicesOptions {
  pageSize?: number;
  tenantRole?: string | null;
}

interface UseBillingInvoicesResult {
  invoices: BillingInvoice[];
  isLoading: boolean;
  isFetchingMore: boolean;
  hasNextPage: boolean;
  loadMore: () => Promise<void>;
  error: Error | null;
  refetch: () => Promise<void>;
}

export function useBillingInvoices(options?: UseBillingInvoicesOptions): UseBillingInvoicesResult {
  const meta = readClientSessionMeta();
  const tenantId = meta?.tenantId ?? null;
  const pageSize = options?.pageSize ?? 25;

  const queryResult = useInfiniteQuery<
    BillingInvoiceListResponse,
    Error,
    BillingInvoiceListResponse,
    ReturnType<typeof queryKeys.billing.invoices>,
    number
  >({
    queryKey: queryKeys.billing.invoices(tenantId, { pageSize }),
    queryFn: ({ pageParam }) => {
      if (!tenantId) {
        return Promise.resolve({ items: [], next_offset: null });
      }
      return fetchBillingInvoices({
        tenantId,
        limit: pageSize,
        offset: pageParam,
        tenantRole: options?.tenantRole ?? null,
      });
    },
    enabled: billingEnabled && Boolean(tenantId),
    initialPageParam: 0,
    getNextPageParam: (lastPage) => lastPage?.next_offset ?? undefined,
    staleTime: 30 * 1000,
  });

  const invoices = useMemo(() => {
    const pages = (queryResult.data as unknown as { pages?: BillingInvoiceListResponse[] })?.pages;
    if (!pages) return [];
    return pages.flatMap((page) => page.items ?? []);
  }, [queryResult.data]);

  return {
    invoices,
    isLoading: queryResult.isLoading,
    isFetchingMore: queryResult.isFetchingNextPage,
    hasNextPage: Boolean(queryResult.hasNextPage),
    loadMore: () => queryResult.fetchNextPage().then(() => undefined),
    error: queryResult.error instanceof Error ? queryResult.error : null,
    refetch: () => queryResult.refetch().then(() => undefined),
  };
}
