## Agent Frontend

This package contains the Next.js 16 UI that talks to the FastAPI backend. It relies on generated API clients from [@hey-api/openapi-ts](https://github.com/hey-api/openapi-ts) to stay in sync with the backend contract.

## Prerequisites

- Node.js 22+
- No backend required for client generation: the HeyAPI config now points at the committed billing-on artifact (`../api-service/.artifacts/openapi-billing.json`).

## Install & Dev Server

```bash
npm install
npm run dev
# or use pnpm / yarn / bun if you prefer
```

The app runs at [http://localhost:3000](http://localhost:3000).

## Regenerating the API Client

Whenever backend endpoints or schemas change, regenerate the HeyAPI client before building or committing UI code:

```bash
npm run generate
```

This executes `openapi-ts` with the configuration in `openapi-ts.config.ts` and refreshes the contents of `lib/api/client/`. Because that directory is ignored by git, each clone (or CI environment) must run the command at least once.

- To include test-fixture endpoints (e.g., for Playwright/CI seeding), first export the fixture-enabled spec:

  ```bash
  python -m starter_cli.app api export-openapi \
    --output api-service/.artifacts/openapi-billing-fixtures.json \
    --enable-billing --enable-test-fixtures
  ```

  then regenerate the SDK against it:

  ```bash
  pnpm generate:fixtures
  ```

  You can also point `OPENAPI_INPUT` to any spec path when running `pnpm generate`.

If you intentionally switch the source spec (e.g., regenerating in a fork), ensure billing endpoints remain present; otherwise, set `NEXT_PUBLIC_ENABLE_BILLING=false` so the UI stays coherent.

## Feature Flags

- `NEXT_PUBLIC_ENABLE_BILLING` (default: `false`): Drives billing navigation/pages/API routes/hooks. Set by the Starter CLI alongside backend `ENABLE_BILLING`.

## Production Builds

```bash
npm run build
npm run start
```

Follow [the Next.js deployment guide](https://nextjs.org/docs/app/building-your-application/deploying) for platform-specific instructions.
