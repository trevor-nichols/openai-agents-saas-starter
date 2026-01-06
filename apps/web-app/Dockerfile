# syntax=docker/dockerfile:1

FROM node:22-slim AS deps

ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /repo

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web-app/package.json apps/web-app/package.json

RUN pnpm install --filter web-app... --frozen-lockfile

FROM node:22-slim AS builder

ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /repo

RUN corepack enable

COPY --from=deps /repo/node_modules /repo/node_modules
COPY --from=deps /repo/apps/web-app/node_modules /repo/apps/web-app/node_modules
COPY --from=deps /repo/package.json /repo/package.json
COPY --from=deps /repo/pnpm-lock.yaml /repo/pnpm-lock.yaml
COPY --from=deps /repo/pnpm-workspace.yaml /repo/pnpm-workspace.yaml
COPY --from=deps /repo/apps/web-app/package.json /repo/apps/web-app/package.json

COPY apps/web-app apps/web-app

RUN pnpm --filter web-app build

FROM node:22-slim AS runtime

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

RUN npm install -g npm@11.7.0

RUN useradd --create-home --uid 10001 appuser

COPY --from=builder /repo/apps/web-app/public /app/public
COPY --from=builder /repo/apps/web-app/.next/standalone /app/
COPY --from=builder /repo/apps/web-app/.next/static /app/.next/static

RUN mkdir -p /app/.next/cache \
  && chown -R appuser:appuser /app

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:3000/api/health/ready').then(r => { if (!r.ok) process.exit(1); }).catch(() => process.exit(1))"

USER appuser

CMD ["node", "server.js"]
