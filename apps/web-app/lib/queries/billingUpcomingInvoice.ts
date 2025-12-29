import { useQuery } from '@tanstack/react-query';

import { previewUpcomingInvoice } from '@/lib/api/billingUpcomingInvoice';
import type { UpcomingInvoicePreview } from '@/lib/types/billing';
import { billingEnabled } from '@/lib/config/features';
import { queryKeys } from './keys';

interface UpcomingInvoiceOptions {
  tenantId: string | null;
  seatCount?: number | null;
  tenantRole?: string | null;
  enabled?: boolean;
}

interface UpcomingInvoiceResult {
  preview: UpcomingInvoicePreview | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useUpcomingInvoicePreview(options: UpcomingInvoiceOptions): UpcomingInvoiceResult {
  const { tenantId, seatCount = null, tenantRole = null, enabled } = options;
  const isEnabled = (enabled ?? true) && billingEnabled && Boolean(tenantId);

  const query = useQuery({
    queryKey: queryKeys.billing.upcomingInvoice(tenantId, seatCount ?? null),
    queryFn: () =>
      previewUpcomingInvoice(
        tenantId as string,
        {
          seat_count: seatCount ?? undefined,
        },
        { tenantRole },
      ),
    enabled: isEnabled,
    staleTime: 30 * 1000,
  });

  return {
    preview: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error instanceof Error ? query.error.message : null,
    refetch: () => query.refetch().then(() => undefined),
  };
}
