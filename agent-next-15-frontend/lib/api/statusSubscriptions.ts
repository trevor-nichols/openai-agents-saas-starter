const VERIFY_ENDPOINT = '/api/status-subscriptions/verify';
const UNSUBSCRIBE_ENDPOINT = '/api/status-subscriptions/unsubscribe';

interface ApiResponse {
  success?: boolean;
  error?: string;
  detail?: string;
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
    if (body?.detail) {
      message = body.detail;
    } else if (body?.error) {
      message = body.error;
    }
  } catch (_error) {
    // ignore
  }

  throw new Error(message);
}
