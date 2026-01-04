import { defineConfig } from '@hey-api/openapi-ts';

// Allow developers to override the production spec source by setting OPENAPI_INPUT.
// Fixture endpoints are generated via openapi-ts.fixtures.config.ts.
const input = process.env.OPENAPI_INPUT || '../api-service/.artifacts/openapi.json';

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
