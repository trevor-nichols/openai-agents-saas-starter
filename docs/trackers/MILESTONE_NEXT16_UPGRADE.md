# Next.js 16 Upgrade Milestone (Frontend)

See also: `docs/trackers/current_milestone/MILESTONE_NEXT16_UPGRADE.md` for live updates.

_Last updated: November 22, 2025_

## Snapshot
- Next.js upgraded to 16.0.3 with `cacheComponents` enabled.
- Node standard set to 22 LTS (`.nvmrc`, engines).
- Auth guard migrated to `proxy.ts`; lockfile refreshed.

## Open Items
- Cache audit for components using `cookies/headers/searchParams` (mark dynamic/private as needed).
- Resolve Storybook peer warning for Next 16 once upstream publishes compat.
- Run and log: `pnpm lint`, `pnpm type-check`, `pnpm build`, `pnpm test:e2e`, `pnpm storybook:build`.
