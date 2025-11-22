import { defineConfig } from '@hey-api/openapi-ts';

// Allow developers to override the spec source (e.g., to include test-fixture routes)
// by setting OPENAPI_INPUT. Default remains the billing-enabled artifact committed
// to the repo so CI stays stable.
const input = process.env.OPENAPI_INPUT || '../api-service/.artifacts/openapi-billing.json';

export default defineConfig({
  // Pin to the billing-enabled OpenAPI artifact to keep the generated SDK stable
  // even when a local dev backend runs with ENABLE_BILLING=false.
  input,
  output: {
    path: 'lib/api/client',
    format: 'prettier',
    lint: 'eslint',
    // Ensure imports point to .ts files during Next dev (pre-transpile)
    importFileExtension: '.ts',
  },
  client: {
    name: '@hey-api/client-fetch',
  },
  types: {
    dates: 'types+transform',
    enums: 'javascript',
  },
});
