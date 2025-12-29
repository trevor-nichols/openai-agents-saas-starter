import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

// Prevent Next.js server-only guard from throwing in JSDOM tests.
vi.mock('server-only', () => ({}));

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
