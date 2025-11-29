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
    include: [
      'app/**/__tests__/**/*.{test,spec}.{ts,tsx}',
      'components/**/__tests__/**/*.{test,spec}.{ts,tsx}',
      'lib/**/__tests__/**/*.{test,spec}.{ts,tsx}',
      '**/*.{test,spec}.{ts,tsx}',
    ],
    exclude: ['node_modules/**', 'tests/**', 'dist/**', '.next/**'],
  },
});
