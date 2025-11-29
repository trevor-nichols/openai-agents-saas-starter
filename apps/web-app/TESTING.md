# Testing Conventions

We keep test placement predictable so feature code and its checks travel together.

- **Route handlers:** Keep `route.test.ts` (or `route.test.tsx`) beside the matching `route.ts`.
- **Everything else:** Place tests in a sibling `__tests__/` directory next to the code under test.

Checks

- Run `pnpm lint:test-placement` (also included in `pnpm validate`) to fail on mis‑placed tests.
