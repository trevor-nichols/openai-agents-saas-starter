import '@testing-library/jest-dom/vitest';
import { afterAll, afterEach, beforeAll, vi } from 'vitest';

import { server } from '@/test-utils/msw/server';

// Prevent Next.js server-only guard from throwing in JSDOM tests.
vi.mock('server-only', () => ({}));

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
});

afterEach(() => {
  server.resetHandlers();
  vi.clearAllMocks();
});

afterAll(() => {
  server.close();
});

// JSDOM lacks ResizeObserver; mock minimal API for components using Radix size hooks.
if (typeof global.ResizeObserver === 'undefined') {
  (global as any).ResizeObserver = class ResizeObserver {
    observe() {
      // no-op
    }
    unobserve() {
      // no-op
    }
    disconnect() {
      // no-op
    }
  };
}
