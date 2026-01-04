import { defineConfig } from '@hey-api/openapi-ts';

// Fixture-only SDK generation. Keep this isolated from the production SDK so
// fixture endpoints do not leak into the main client surface.
const input =
  process.env.OPENAPI_FIXTURES_INPUT ||
  '../api-service/.artifacts/openapi-fixtures.json';

export default defineConfig({
  input,
  output: {
    path: 'lib/api/fixtures-client',
    format: 'prettier',
    lint: 'eslint',
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
