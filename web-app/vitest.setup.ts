import '@testing-library/jest-dom/vitest';

// JSDOM lacks ResizeObserver; mock minimal API for components using Radix size hooks.
if (typeof global.ResizeObserver === 'undefined') {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
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
