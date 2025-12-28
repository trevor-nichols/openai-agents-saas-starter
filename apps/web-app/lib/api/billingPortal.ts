import type { PortalSessionRequest, PortalSessionResponse } from '@/lib/api/client/types.gen';
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

export async function createBillingPortalSession(
  tenantId: string,
  payload: PortalSessionRequest,
  options?: RequestOptions,
): Promise<PortalSessionResponse> {
  if (!tenantId || tenantId.trim().length === 0) {
    throw new Error('Tenant id is required.');
  }

  const response = await fetch(apiV1Path(`/billing/tenants/${encodeURIComponent(tenantId)}/portal`), {
    method: 'POST',
    headers: buildBillingHeaders(options, true),
    cache: 'no-store',
    body: JSON.stringify(payload),
  });

  const data = await parseBillingResponse<PortalSessionResponse>(response);
  if (isBillingDisabled(response.status, data)) {
    throw new Error('Billing is disabled.');
  }
  if (!response.ok) {
    throw new Error(resolveBillingErrorMessage(data, 'Failed to create a billing portal session.'));
  }
  if (!data) {
    throw new Error('Portal session returned empty response.');
  }

  return data as PortalSessionResponse;
}
