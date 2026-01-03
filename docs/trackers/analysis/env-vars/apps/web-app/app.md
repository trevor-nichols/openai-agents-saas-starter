## apps/web-app/app

| Name | Purpose | Location | Required? | Default | Format | Sensitivity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `API_BASE_URL` | Backend API URL used in test fixture routes to proxy requests. | `api/v1/test-fixtures/apply/route.ts`<br>`api/v1/test-fixtures/email-verification-token/route.ts` | Optional | `http://localhost:8000` | URL | Non-secret |
| `NODE_ENV` | Used to disable test fixture routes in production environments. | `api/v1/test-fixtures/apply/route.ts`<br>`api/v1/test-fixtures/email-verification-token/route.ts` | Optional | N/A | String (`production` / `development`) | Non-secret |
| `APP_PUBLIC_URL` | Base URL of the site, used for generating absolute URLs in manifest, robots, and sitemap. | `__tests__/manifest.test.ts` (test)<br>`__tests__/robots.test.ts` (test)<br>`__tests__/sitemap.test.ts` (test) | Required (for SEO) | N/A | URL | Non-secret |
| `VERCEL_GIT_COMMIT_TIMESTAMP` | Used to determine the `lastModified` date for sitemap entries. | `__tests__/sitemap.test.ts` (test) | Optional | N/A | ISO Date String | Non-secret |
