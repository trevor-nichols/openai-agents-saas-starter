import type { BillingInvoice, BillingInvoiceListResponse } from '@/types/billing';
import { apiV1Path } from '@/lib/apiPaths';
import {
  buildBillingHeaders,
  isBillingDisabled,
  parseBillingResponse,
  resolveBillingErrorMessage,
} from './billingUtils';

export interface FetchBillingInvoicesParams {
  tenantId: string;
  limit?: number;
  offset?: number;
  tenantRole?: string | null;
  signal?: AbortSignal;
}

export interface FetchBillingInvoiceParams {
  tenantId: string;
  invoiceId: string;
  tenantRole?: string | null;
  signal?: AbortSignal;
}

export async function fetchBillingInvoices(
  params: FetchBillingInvoicesParams,
): Promise<BillingInvoiceListResponse> {
  const { tenantId, limit, offset, tenantRole = null, signal } = params;

  if (!tenantId) {
    throw new Error('Tenant id is required to load invoices.');
  }

  const search = new URLSearchParams();
  if (limit) {
    search.set('limit', String(limit));
  }
  if (offset !== undefined) {
    search.set('offset', String(offset));
  }

  const baseUrl = apiV1Path(`/billing/tenants/${encodeURIComponent(tenantId)}/invoices`);
  const url = search.toString() ? `${baseUrl}?${search.toString()}` : baseUrl;

  const response = await fetch(url, {
    headers: buildBillingHeaders({ tenantRole }, false),
    cache: 'no-store',
    signal,
  });

  const payload = await parseBillingResponse<BillingInvoiceListResponse>(response);
  if (isBillingDisabled(response.status, payload)) {
    return { items: [], next_offset: null };
  }

  if (!response.ok) {
    throw new Error(resolveBillingErrorMessage(payload, 'Failed to load invoices.'));
  }

  const data =
    payload && typeof payload === 'object' && 'items' in payload
      ? (payload as BillingInvoiceListResponse)
      : { items: [], next_offset: null };

  return {
    items: data.items ?? [],
    next_offset: data.next_offset ?? null,
  };
}

export async function fetchBillingInvoice(
  params: FetchBillingInvoiceParams,
): Promise<BillingInvoice> {
  const { tenantId, invoiceId, tenantRole = null, signal } = params;

  if (!tenantId) {
    throw new Error('Tenant id is required to load invoices.');
  }
  if (!invoiceId) {
    throw new Error('Invoice id is required to load an invoice.');
  }

  const url = apiV1Path(
    `/billing/tenants/${encodeURIComponent(tenantId)}/invoices/${encodeURIComponent(invoiceId)}`,
  );

  const response = await fetch(url, {
    headers: buildBillingHeaders({ tenantRole }, false),
    cache: 'no-store',
    signal,
  });

  const payload = await parseBillingResponse<BillingInvoice>(response);
  if (isBillingDisabled(response.status, payload)) {
    throw new Error('Billing is disabled.');
  }

  if (!response.ok) {
    throw new Error(resolveBillingErrorMessage(payload, 'Failed to load invoice.'));
  }

  if (!payload) {
    throw new Error('Invoice not found.');
  }

  return payload as BillingInvoice;
}
