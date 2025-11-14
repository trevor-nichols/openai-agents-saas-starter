import type { StatusSubscriptionResponse } from '@/lib/api/client/types.gen';

const CREATE_ENDPOINT = '/api/status-subscriptions';
const VERIFY_ENDPOINT = '/api/status-subscriptions/verify';
const UNSUBSCRIBE_ENDPOINT = '/api/status-subscriptions/unsubscribe';

interface ApiResponse {
  success?: boolean;
  error?: string;
  detail?: string;
}

export interface CreateStatusSubscriptionInput {
  channel: 'email' | 'webhook';
  target: string;
  severity_filter?: 'all' | 'major' | 'maintenance';
  metadata?: Record<string, unknown>;
}

function resolveErrorMessage(body: ApiResponse | undefined, fallbackMessage: string): string {
  if (!body) {
    return fallbackMessage;
  }
  if (body.detail) {
    return body.detail;
  }
  if (body.error) {
    return body.error;
  }
  return fallbackMessage;
}

export async function createStatusSubscription(
  payload: CreateStatusSubscriptionInput,
): Promise<StatusSubscriptionResponse> {
  const response = await fetch(CREATE_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    cache: 'no-store',
    body: JSON.stringify(payload),
  });

  const body = (await response.json().catch(() => undefined)) as
    | StatusSubscriptionResponse
    | ApiResponse
    | undefined;

  if (!response.ok) {
    throw new Error(resolveErrorMessage(body as ApiResponse | undefined, 'Unable to subscribe to alerts.'));
  }

  return body as StatusSubscriptionResponse;
}

export async function verifyStatusSubscriptionToken(token: string): Promise<void> {
  await submitToken(VERIFY_ENDPOINT, { token }, 'Unable to confirm subscription.');
}

export async function unsubscribeStatusSubscription(
  token: string,
  subscriptionId: string | null,
): Promise<void> {
  if (!subscriptionId) {
    throw new Error('Missing subscription identifier.');
  }
  await submitToken(
    UNSUBSCRIBE_ENDPOINT,
    { token, subscriptionId },
    'Unable to unsubscribe from alerts.',
  );
}

async function submitToken(
  endpoint: string,
  payload: Record<string, string>,
  fallbackMessage: string,
): Promise<void> {
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });

  if (response.ok) {
    return;
  }

  let message = fallbackMessage;
  try {
    const body = (await response.json()) as ApiResponse;
    message = resolveErrorMessage(body, fallbackMessage);
  } catch (_error) {
    // ignore JSON parse issues
  }

  throw new Error(message);
}
