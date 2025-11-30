import type { ContactSubmission } from '@/types/marketing';

interface ContactApiResponse {
  success: boolean;
  error?: string;
}

export async function submitContactRequest(payload: ContactSubmission): Promise<void> {
  const response = await fetch('/api/contact', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });

  const data = (await response.json().catch(() => ({}))) as ContactApiResponse;

  if (!response.ok || data.success === false) {
    throw new Error(data.error || 'Failed to send your message.');
  }
}

