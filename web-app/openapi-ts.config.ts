import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  // Pin to the billing-enabled OpenAPI artifact to keep the generated SDK stable
  // even when a local dev backend runs with ENABLE_BILLING=false.
  input: '../api-service/.artifacts/openapi-billing.json',
  output: {
    path: 'lib/api/client',
    format: 'prettier',
    lint: 'eslint',
  },
  client: {
    name: '@hey-api/client-fetch',
  },
  types: {
    dates: 'types+transform',
    enums: 'javascript',
  },
});
