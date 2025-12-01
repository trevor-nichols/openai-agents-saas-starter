import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { submitContactRequest } from '@/lib/api/contact';
import { apiV1Path } from '@/lib/apiPaths';

const originalFetch = global.fetch;

describe('contact API helper', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    if (originalFetch) {
      global.fetch = originalFetch;
    } else {
      // @ts-expect-error - cleaning up mocked fetch reference
      delete global.fetch;
    }
  });

  it('returns silently on 202 success', async () => {
    const response = new Response(JSON.stringify({ success: true }), {
      status: 202,
      headers: { 'Content-Type': 'application/json' },
    });

    global.fetch = vi.fn().mockResolvedValue(response);

    await expect(
      submitContactRequest({ email: 'test@example.com', message: 'Hi there!' }),
    ).resolves.toBeUndefined();

    expect(global.fetch).toHaveBeenCalledWith(
      apiV1Path('/contact'),
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('throws when backend signals failure', async () => {
    const response = new Response(JSON.stringify({ success: false, error: 'oops' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });

    global.fetch = vi.fn().mockResolvedValue(response);

    await expect(
      submitContactRequest({ email: 'test@example.com', message: 'Hi there!' }),
    ).rejects.toThrow('oops');
  });
});
