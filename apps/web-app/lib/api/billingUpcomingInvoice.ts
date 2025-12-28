import type {
  UpcomingInvoicePreviewRequest,
  UpcomingInvoicePreviewResponse,
} from '@/lib/api/client/types.gen';
import { apiV1Path } from '@/lib/apiPaths';
import {
  buildBillingHeaders,
  isBillingDisabled,
  parseBillingResponse,
  resolveBillingErrorMessage,
} from './billingUtils';

interface RequestOptions {
  tenantRole?: string | null;
}

export async function previewUpcomingInvoice(
  tenantId: string,
  payload: UpcomingInvoicePreviewRequest,
  options?: RequestOptions,
): Promise<UpcomingInvoicePreviewResponse> {
  if (!tenantId || tenantId.trim().length === 0) {
    throw new Error('Tenant id is required.');
  }

  const response = await fetch(apiV1Path(`/billing/tenants/${encodeURIComponent(tenantId)}/upcoming-invoice`), {
    method: 'POST',
    headers: buildBillingHeaders(options, true),
    cache: 'no-store',
    body: JSON.stringify(payload),
  });

  const data = await parseBillingResponse<UpcomingInvoicePreviewResponse>(response);
  if (isBillingDisabled(response.status, data)) {
    throw new Error('Billing is disabled.');
  }

  if (!response.ok) {
    throw new Error(resolveBillingErrorMessage(data, 'Failed to preview upcoming invoice.'));
  }
  if (!data) {
    throw new Error('Upcoming invoice preview returned empty response.');
  }

  return data as UpcomingInvoicePreviewResponse;
}
