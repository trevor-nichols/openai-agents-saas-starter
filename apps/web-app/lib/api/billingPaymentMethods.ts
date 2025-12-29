import type {
  PaymentMethodResponse,
  SetupIntentRequest,
  SetupIntentResponse,
  SuccessNoDataResponse,
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

const paymentMethodsPath = (tenantId: string) => {
  if (!tenantId || tenantId.trim().length === 0) {
    throw new Error('Tenant id is required.');
  }
  return apiV1Path(`/billing/tenants/${encodeURIComponent(tenantId)}/payment-methods`);
};

export async function fetchPaymentMethods(
  tenantId: string,
  options?: RequestOptions,
): Promise<PaymentMethodResponse[]> {
  const response = await fetch(paymentMethodsPath(tenantId), {
    method: 'GET',
    headers: buildBillingHeaders(options, false),
    cache: 'no-store',
  });

  const data = await parseBillingResponse<PaymentMethodResponse[]>(response);
  if (isBillingDisabled(response.status, data)) {
    throw new Error('Billing is disabled.');
  }

  if (!response.ok) {
    throw new Error(resolveBillingErrorMessage(data, 'Failed to load payment methods.'));
  }

  if (!Array.isArray(data)) {
    throw new Error('Payment methods returned empty response.');
  }

  return data;
}

export async function createSetupIntentRequest(
  tenantId: string,
  payload: SetupIntentRequest,
  options?: RequestOptions,
): Promise<SetupIntentResponse> {
  const response = await fetch(`${paymentMethodsPath(tenantId)}/setup-intent`, {
    method: 'POST',
    headers: buildBillingHeaders(options, true),
    cache: 'no-store',
    body: JSON.stringify(payload),
  });

  const data = await parseBillingResponse<SetupIntentResponse>(response);
  if (isBillingDisabled(response.status, data)) {
    throw new Error('Billing is disabled.');
  }

  if (!response.ok) {
    throw new Error(resolveBillingErrorMessage(data, 'Failed to create setup intent.'));
  }
  if (!data) {
    throw new Error('Setup intent returned empty response.');
  }

  return data as SetupIntentResponse;
}

export async function setDefaultPaymentMethodRequest(
  tenantId: string,
  paymentMethodId: string,
  options?: RequestOptions,
): Promise<SuccessNoDataResponse> {
  if (!paymentMethodId || paymentMethodId.trim().length === 0) {
    throw new Error('Payment method id is required.');
  }

  const response = await fetch(
    `${paymentMethodsPath(tenantId)}/${encodeURIComponent(paymentMethodId)}/default`,
    {
      method: 'POST',
      headers: buildBillingHeaders(options, false),
      cache: 'no-store',
    },
  );

  const data = await parseBillingResponse<SuccessNoDataResponse>(response);
  if (isBillingDisabled(response.status, data)) {
    throw new Error('Billing is disabled.');
  }

  if (!response.ok) {
    throw new Error(resolveBillingErrorMessage(data, 'Failed to set default payment method.'));
  }

  return data as SuccessNoDataResponse;
}

export async function detachPaymentMethodRequest(
  tenantId: string,
  paymentMethodId: string,
  options?: RequestOptions,
): Promise<SuccessNoDataResponse> {
  if (!paymentMethodId || paymentMethodId.trim().length === 0) {
    throw new Error('Payment method id is required.');
  }

  const response = await fetch(
    `${paymentMethodsPath(tenantId)}/${encodeURIComponent(paymentMethodId)}`,
    {
      method: 'DELETE',
      headers: buildBillingHeaders(options, false),
      cache: 'no-store',
    },
  );

  const data = await parseBillingResponse<SuccessNoDataResponse>(response);
  if (isBillingDisabled(response.status, data)) {
    throw new Error('Billing is disabled.');
  }

  if (!response.ok) {
    throw new Error(resolveBillingErrorMessage(data, 'Failed to remove payment method.'));
  }

  return data as SuccessNoDataResponse;
}
