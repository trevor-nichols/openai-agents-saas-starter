# Next.js 16 Upgrade Milestone

_Last updated: November 22, 2025_

## Objective
Move the web frontend to Next.js 16 with Cache Components enabled and Node 22 (latest stable LTS recommended by Next 16) while preserving authenticated flows and streaming APIs.

## Scope & Deliverables
- Bump Next.js + lint config to 16.0.x, align lockfile, and pin Node 22 via `engines` + `.nvmrc`.
- Replace `middleware.ts` with `proxy.ts` for auth redirects; keep matcher semantics.
- Enable `cacheComponents` globally; annotate/opt-out components that depend on request-specific data.
- Refresh developer docs (milestone tracker + top-level tracker entry).
- Validate with lint, type-check, build, Playwright smoke, and Storybook build.

## Non-Goals
- Edge runtime tuning (we run on Node for now).
- Refactors to adopt new React 19 features beyond what is required for compatibility.

## Work Plan
| # | Task | Status | Owner | Target |
| - | ---- | ------ | ----- | ------ |
| 1 | Pin Node 22 via `.nvmrc` and `engines` fields (repo + web-app); remove Turbopack flag from scripts. | ✅ Done | FE | Nov 2025 |
| 2 | Upgrade `next`/`eslint-config-next` to 16.0.3; refresh `pnpm-lock.yaml`. | ✅ Done | FE | Nov 2025 |
| 3 | Migrate auth guard from `middleware.ts` → `proxy.ts`, keep matcher coverage. | ✅ Done | FE | Nov 2025 |
| 4 | Enable `cacheComponents` in `next.config.ts`; map where to apply `'use cache'` vs. dynamic rendering (marketing vs. app shell/chat). | ✅ Done | FE | Nov 2025 |
| 5 | Audit server components for `cookies/headers/searchParams` usage; add explicit `dynamic = 'force-dynamic'` or `'use cache: private'` where needed. | ✅ Done | FE | Nov 2025 |
| 6 | Resolve Storybook peer warning for Next 16 (upgrade addon bundle once available). | ✅ Done | FE | Dec 2025 |
| 7 | Validation: `pnpm lint`, `pnpm type-check`, `pnpm build`, `pnpm storybook:build`; log outcomes here. | ⚠️ Partial | FE | Nov 2025 |

## Validation Plan
- Automated: `pnpm lint`, `pnpm type-check`, `pnpm build`. **Status:** ✅ (Nov 22, 2025) — build surfaced non-blocking prerender warnings for `/register` signup policy fetch (handled in logs, build completed).
- UI: `pnpm storybook:build` to catch Next 16/Storybook integration issues. **Status:** ✅ (warnings only: Tailwind ambiguous `ease-[...]` classes; asset size hints; media-chrome package.json lookup warning).
- Record results in this file after each run.

## Risks & Mitigations
| Risk | Impact | Mitigation |
| --- | --- | --- |
| Cache Components caching request-bound content (auth/session) | High | Mark affected components as dynamic or private cache; keep proxy-based auth redirects. |
| Storybook peer mismatch with Next 16 | Medium | Track upstream release; temporarily tolerate warning; validate build. |
| Node 22 requirement in CI images | Medium | Update CI/base images and devcontainer to Node 22; engines gate local installs. |
| SSE/stream routes under new runtime defaults | Low | Keep `runtime = 'nodejs'` where needed; smoke-test chat/billing streams. |

## Notes
- Latest Next.js stable: 16.0.3; requires Node ≥20.9, we standardize on Node 22 LTS.
- Turbopack is default in 16; scripts no longer pass `--turbopack`.
