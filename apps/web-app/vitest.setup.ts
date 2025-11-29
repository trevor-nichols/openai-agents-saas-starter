import '@testing-library/jest-dom/vitest';

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
