## Agent Frontend

This package contains the Next.js 15 UI that talks to the FastAPI backend. It relies on generated API clients from [@hey-api/openapi-ts](https://github.com/hey-api/openapi-ts) to stay in sync with the backend contract.

## Prerequisites

- Node.js 20+
- A running backend on `http://localhost:8000` (the OpenAPI document is fetched from `/openapi.json`).

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

If the backend is hosted at a different URL, update `input` in `openapi-ts.config.ts` accordingly.

## Production Builds

```bash
npm run build
npm run start
```

Follow [the Next.js deployment guide](https://nextjs.org/docs/app/building-your-application/deploying) for platform-specific instructions.
