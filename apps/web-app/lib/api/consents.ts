import type { ConsentRequest, ConsentView } from '@/lib/api/client/types.gen';
import { apiV1Path } from '@/lib/apiPaths';

async function parseJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch (_error) {
    throw new Error('Failed to parse response from server.');
  }
}

export async function listConsentsRequest(): Promise<ConsentView[]> {
  const response = await fetch(apiV1Path('/users/consents'), { cache: 'no-store' });
  const data = await parseJson<ConsentView[] | { message?: string }>(response);
  if (!response.ok) {
    throw new Error((data as { message?: string }).message ?? 'Failed to load consents.');
  }
  return data as ConsentView[];
}

export async function recordConsentRequest(payload: ConsentRequest): Promise<void> {
  const response = await fetch(apiV1Path('/users/consents'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!response.ok) {
    const data = await parseJson<{ message?: string }>(response).catch(() => ({}));
    throw new Error((data as { message?: string }).message ?? 'Failed to record consent.');
  }
}
