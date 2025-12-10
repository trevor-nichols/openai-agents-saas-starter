import type { StorybookConfig } from '@storybook/nextjs';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const config: StorybookConfig = {
  stories: ['../features/**/*.stories.@(ts|tsx)', '../components/**/*.stories.@(ts|tsx)'],
  addons: [],
  framework: {
    name: '@storybook/nextjs',
    options: {},
  },
  webpackFinal: async (config) => {
    config.resolve = config.resolve || {};
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      'next/config': path.resolve(__dirname, './next-config-shim.js'),
      'next/navigation': path.resolve(__dirname, './mocks/next-navigation.ts'),
      '@': path.resolve(__dirname, '../'),
      // Storybook-only shims so stories can run without Vitest mocks
      '@/app/actions/auth': path.resolve(__dirname, './mocks/auth-actions.ts'),
      '@/app/actions/auth/signup': path.resolve(__dirname, './mocks/auth-signup.ts'),
      '@/app/actions/auth/passwords': path.resolve(__dirname, './mocks/auth-passwords.ts'),
      '@/lib/queries/mfa': path.resolve(__dirname, './mocks/mfa-queries.ts'),
      '@/lib/queries/conversations': path.resolve(
        __dirname,
        './mocks/conversations-queries.ts'
      ),
      '@/lib/api/conversations': path.resolve(__dirname, './mocks/conversations-api.ts'),
      '@/lib/api/activity': path.resolve(__dirname, './mocks/activity-api.ts'),
      '@/lib/streams/activity': path.resolve(__dirname, './mocks/activity-stream.ts'),
      '@/lib/api/signup': path.resolve(__dirname, './mocks/signup-api.ts'),
      '@/lib/queries/signup': path.resolve(__dirname, './mocks/signup-queries.ts'),
      '@/lib/api/tenantSettings': path.resolve(__dirname, './mocks/tenantSettings-api.ts'),
      '@/lib/queries/tenantSettings': path.resolve(__dirname, './mocks/tenantSettings-queries.ts'),
      '@/lib/queries/account': path.resolve(__dirname, './mocks/account-queries.ts'),
      '@/lib/queries/accountSecurity': path.resolve(__dirname, './mocks/accountSecurity-queries.ts'),
      '@/lib/queries/accountSessions': path.resolve(__dirname, './mocks/accountSessions-queries.ts'),
      '@/lib/queries/accountServiceAccounts': path.resolve(
        __dirname,
        './mocks/accountServiceAccounts-queries.ts'
      ),
      '@/lib/queries/notificationPreferences': path.resolve(
        __dirname,
        './mocks/notificationPreferences-queries.ts'
      ),
      '@/lib/queries/consents': path.resolve(__dirname, './mocks/consents-queries.ts'),
    };
    return config;
  },
};

export default config;
