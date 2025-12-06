import type { ReactNode } from 'react';
import {
  QueryClient,
  QueryClientProvider,
  type UseMutationResult,
} from '@tanstack/react-query';
import { vi } from 'vitest';

import type {
  AgentChatRequest,
  AgentChatResponse,
} from '@/lib/api/client/types.gen';

export type ChatMutationResult = UseMutationResult<
  AgentChatResponse,
  Error,
  AgentChatRequest,
  unknown
>;

export const createMutationMock = (
  overrides: Partial<ChatMutationResult> = {},
): ChatMutationResult => {
  const base = {
    mutate: vi.fn(),
    mutateAsync: vi.fn(),
    reset: vi.fn(),
    context: undefined,
    data: undefined,
    error: null,
    failureCount: 0,
    failureReason: null,
    isError: false,
    isIdle: true,
    isLoading: false,
    isPaused: false,
    isPending: false,
    isSuccess: false,
    status: 'idle',
    submittedAt: 0,
    variables: undefined,
    ...overrides,
  };

  return base as unknown as ChatMutationResult;
};

export function createQueryWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  const Wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  return { Wrapper, queryClient };
}

