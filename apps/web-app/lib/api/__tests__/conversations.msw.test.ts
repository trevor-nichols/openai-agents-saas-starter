import { describe, expect, it } from 'vitest';

import { fetchConversationMessages } from '@/lib/api/conversations';
import { http, HttpResponse, server } from '@/test-utils/msw/server';

describe('fetchConversationMessages (msw)', () => {
  it('returns normalized pagination payload', async () => {
    let requestedPathname = '';
    let requestedLimit: string | null = null;

    server.use(
      http.get('/api/v1/conversations/:conversationId/messages', ({ request }) => {
        const url = new URL(request.url);
        requestedPathname = url.pathname;
        requestedLimit = url.searchParams.get('limit');
        return HttpResponse.json({
          items: [
            { role: 'assistant', content: 'hi', timestamp: '2024-01-01T00:00:00Z' },
            { role: 'user', content: 'hello', timestamp: '2023-12-31T23:59:59Z' },
          ],
          next_cursor: 'cursor-2',
          prev_cursor: null,
        });
      }),
    );

    const result = await fetchConversationMessages({ conversationId: 'conv-123', limit: 2 });

    expect(result.items).toHaveLength(2);
    expect(result.next_cursor).toBe('cursor-2');
    expect(result.prev_cursor).toBeNull();
    expect(requestedPathname).toContain('/api/v1/conversations/conv-123/messages');
    expect(requestedLimit).toBe('2');
  });
});
