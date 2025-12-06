import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { useAttachmentResolver } from '../useAttachmentResolver';

vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ error: vi.fn(), success: vi.fn() }),
}));

vi.mock('@/lib/api/storage', () => ({
  getAttachmentDownloadUrl: vi.fn(async () => ({ download_url: 'https://example.com/file' })),
}));

describe('useAttachmentResolver', () => {
  it('resolves and caches attachment download urls', async () => {
    const { result } = renderHook(() => useAttachmentResolver());

    expect(result.current.attachmentState).toEqual({});

    await act(async () => {
      await result.current.resolveAttachment('obj-1');
    });

    expect(result.current.attachmentState['obj-1']).toMatchObject({
      url: 'https://example.com/file',
      loading: false,
      error: undefined,
    });
  });
});
