import { renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useStatusSubscriptionActions } from '../useStatusSubscriptionActions';

const replaceMock = vi.fn();
let searchParamsValue = '';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: replaceMock }),
  useSearchParams: () => new URLSearchParams(searchParamsValue),
}));

vi.mock('@/lib/api/statusSubscriptions', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api/statusSubscriptions')>();
  return {
    ...actual,
    verifyStatusSubscriptionToken: vi.fn(),
    unsubscribeStatusSubscription: vi.fn(),
  };
});

const { verifyStatusSubscriptionToken, unsubscribeStatusSubscription } = vi.mocked(
  await import('@/lib/api/statusSubscriptions'),
);

function setSearchParams(query: string) {
  searchParamsValue = query;
  const prefix = query ? `/status?${query}` : '/status';
  window.history.replaceState({}, '', prefix);
}

beforeEach(() => {
  replaceMock.mockReset();
  verifyStatusSubscriptionToken.mockReset();
  unsubscribeStatusSubscription.mockReset();
  setSearchParams('');
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('useStatusSubscriptionActions', () => {
  it('confirms subscription tokens and redirects with success', async () => {
    verifyStatusSubscriptionToken.mockResolvedValueOnce();
    setSearchParams('token=abc&subscription_id=sub-1');

    renderHook(() => useStatusSubscriptionActions());

    await waitFor(() => expect(verifyStatusSubscriptionToken).toHaveBeenCalledWith('abc'));
    await waitFor(() =>
      expect(replaceMock).toHaveBeenCalledWith('/status?verification=success', { scroll: false }),
    );
  });

  it('surfaces verification errors and redirects with error state', async () => {
    verifyStatusSubscriptionToken.mockRejectedValueOnce(new Error('boom'));
    setSearchParams('token=bad-token&subscription_id=sub-err');

    renderHook(() => useStatusSubscriptionActions());

    await waitFor(() => expect(verifyStatusSubscriptionToken).toHaveBeenCalledWith('bad-token'));
    await waitFor(() =>
      expect(replaceMock).toHaveBeenCalledWith('/status?verification=error', { scroll: false }),
    );
  });

  it('processes unsubscribe tokens and clears subscription id on success', async () => {
    unsubscribeStatusSubscription.mockResolvedValueOnce();
    setSearchParams('unsubscribe_token=tok-1&subscription_id=sub-9');

    renderHook(() => useStatusSubscriptionActions());

    await waitFor(() =>
      expect(unsubscribeStatusSubscription).toHaveBeenCalledWith('tok-1', 'sub-9'),
    );
    await waitFor(() =>
      expect(replaceMock).toHaveBeenCalledWith('/status?unsubscribe=success', { scroll: false }),
    );
  });

  it('handles missing subscription id when unsubscribing and redirects with error', async () => {
    setSearchParams('unsubscribe_token=tok-2');

    renderHook(() => useStatusSubscriptionActions());

    await waitFor(() =>
      expect(replaceMock).toHaveBeenCalledWith('/status?unsubscribe=error', { scroll: false }),
    );
    expect(unsubscribeStatusSubscription).not.toHaveBeenCalled();
  });
});
