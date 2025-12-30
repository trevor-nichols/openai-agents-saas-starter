import path from 'node:path';

import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '.'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
    environmentMatchGlobs: [
      ['app/api/**/route.test.ts', 'node'],
      ['app/api/**/route.test.tsx', 'node'],
      ['app/api/**/route.spec.ts', 'node'],
      ['app/api/**/route.spec.tsx', 'node'],
      ['lib/server/**/__tests__/**/*.test.ts', 'node'],
      ['lib/server/**/__tests__/**/*.test.tsx', 'node'],
      ['lib/server/**/__tests__/**/*.spec.ts', 'node'],
      ['lib/server/**/__tests__/**/*.spec.tsx', 'node'],
    ],
    testTimeout: 10000,
    hookTimeout: 10000,
    include: [
      'app/**/__tests__/**/*.{test,spec}.{ts,tsx}',
      'components/**/__tests__/**/*.{test,spec}.{ts,tsx}',
      'lib/**/__tests__/**/*.{test,spec}.{ts,tsx}',
      '**/*.{test,spec}.{ts,tsx}',
    ],
    exclude: ['node_modules/**', 'tests/**', 'dist/**', '.next/**'],
  },
});
