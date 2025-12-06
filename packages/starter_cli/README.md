# Starter CLI

Operator CLI for the OpenAI Agents starter stack. For full project documentation, see the repository root README.

## OpenAPI export quick reference

Paths are resolved from the repository root even when you run the command inside `packages/starter_cli`. Avoid prefixing with `../` or the file will be written outside the repo.

```
cd packages/starter_cli
python -m starter_cli.app api export-openapi \
  --output apps/api-service/.artifacts/openapi-fixtures.json \
  --enable-billing --enable-test-fixtures

cd ../../apps/web-app
OPENAPI_INPUT=../api-service/.artifacts/openapi-fixtures.json pnpm generate:fixtures
```
