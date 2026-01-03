## apps/web-app/app

| Name | Purpose | Location | Required? | Default | Format | Sensitivity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `API_URL` | Fallback backend API URL used in test fixture routes if `NEXT_PUBLIC_API_URL` is missing. | `api/v1/test-fixtures/apply/route.ts`<br>`api/v1/test-fixtures/email-verification-token/route.ts` | Optional | `http://localhost:8000` (via fallback chain) | URL | Non-secret |
| `BACKEND_API_URL` | Fallback backend API URL used in test fixture routes if `API_URL` is missing. | `api/v1/test-fixtures/apply/route.ts`<br>`api/v1/test-fixtures/email-verification-token/route.ts` | Optional | `http://localhost:8000` (via fallback chain) | URL | Non-secret |
| `ENABLE_BILLING` | Backend feature flag to enable/disable billing logic. | `api/health/features/route.ts` | Optional | `null` | Boolean-like string (`true`, `1`, `yes`) | Non-secret |
| `NEXT_PUBLIC_API_URL` | Primary backend API URL used in test fixture routes to proxy requests. | `api/v1/test-fixtures/apply/route.ts`<br>`api/v1/test-fixtures/email-verification-token/route.ts` | Optional | `http://localhost:8000` (via fallback chain) | URL | Non-secret |
| `NEXT_PUBLIC_ENABLE_BILLING` | Frontend feature flag to enable/disable billing UI. | `api/health/features/route.ts`<br>`(app)/__tests__/layout.test.ts` (test) | Optional | `null` | Boolean-like string (`true`, `false`) | Non-secret |
| `NODE_ENV` | Used to disable test fixture routes in production environments. | `api/v1/test-fixtures/apply/route.ts`<br>`api/v1/test-fixtures/email-verification-token/route.ts` | Optional | N/A | String (`production` / `development`) | Non-secret |
| `SITE_URL` | Base URL of the site, used for generating absolute URLs in manifest, robots, and sitemap. | `__tests__/manifest.test.ts` (test)<br>`__tests__/robots.test.ts` (test)<br>`__tests__/sitemap.test.ts` (test) | Required (for SEO) | N/A | URL | Non-secret |
| `VERCEL_GIT_COMMIT_TIMESTAMP` | Used to determine the `lastModified` date for sitemap entries. | `__tests__/sitemap.test.ts` (test) | Optional | N/A | ISO Date String | Non-secret |