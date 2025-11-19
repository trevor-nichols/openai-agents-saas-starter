import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: 'http://localhost:8000/openapi.json',
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
