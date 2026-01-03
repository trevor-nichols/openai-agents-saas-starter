## apps/web-app/tests

| Name | Purpose | Location | Required | Default Value | Format / Constraints | Sensitivity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ALLOW_PUBLIC_SIGNUP` | Secondary fallback for enabling public signup tests. | `harness/env.ts` (buildRawEnv) | Optional | `undefined` | Boolean-like string ('true', '1', 'yes', 'on') | Non-secret Config |
| `CI` | Indicates if the tests are running in a Continuous Integration environment. Used to force storage state refresh and seeding. | `harness/env.ts` (buildRawEnv) | Optional | `undefined` | Boolean-like string | Non-secret Config |
| `NEXT_PUBLIC_ALLOW_PUBLIC_SIGNUP` | Tertiary fallback for enabling public signup tests. | `harness/env.ts` (buildRawEnv) | Optional | `undefined` | Boolean-like string | Non-secret Config |
| `NEXT_PUBLIC_API_URL` | Fallback URL for the API if `PLAYWRIGHT_API_URL` is not set. | `harness/env.ts` (buildRawEnv) | Optional | `undefined` | Valid URL string | Non-secret Config |
| `PLAYWRIGHT_ALLOW_PUBLIC_SIGNUP` | Primary flag to enable tests involving public signup flows. | `harness/env.ts` (buildRawEnv) | Optional | `undefined` (resolves to false) | Boolean-like string | Non-secret Config |
| `PLAYWRIGHT_API_URL` | The base URL for the backend API used during tests. | `harness/env.ts` (buildRawEnv) | Optional | `'http://localhost:8000'` | Valid URL string | Non-secret Config |
| `PLAYWRIGHT_BASE_URL` | The base URL for the frontend application (Real mode). | `harness/env.ts` (buildRawEnv) | Optional | `'http://localhost:3000'` | Valid URL string | Non-secret Config |
| `PLAYWRIGHT_BILLING_EMAIL` | Email address used for billing plan change inputs in tests. | `harness/env.ts` (buildRawEnv) | Optional | `'billing+playwright@example.com'` | Valid email string | Non-secret Config |
| `PLAYWRIGHT_MOCK_BASE_URL` | The base URL for the frontend application (Mock mode). | `harness/env.ts` (buildRawEnv) | Optional | `'http://localhost:3001'` | Valid URL string | Non-secret Config |
| `PLAYWRIGHT_OPERATOR_EMAIL` | Email address for the platform operator account. | `harness/env.ts` (buildRawEnv) | Optional | `'platform-ops@example.com'` | Valid email string | Non-secret Config |
| `PLAYWRIGHT_OPERATOR_PASSWORD` | Password for the platform operator account. | `harness/env.ts` (buildRawEnv) | Optional | `'OpsAccount123!'` | String (min length 1) | **Secret** |
| `PLAYWRIGHT_OPERATOR_TENANT` | The tenant slug identifier for the operator organization. | `harness/env.ts` (buildRawEnv) | Optional | `'platform-ops'` | String (min length 1) | Non-secret Config |
| `PLAYWRIGHT_REFRESH_STORAGE_STATE` | Forces authentication (login) to refresh stored cookies/tokens even if valid ones exist. | `harness/env.ts` (buildRawEnv) | Optional | `undefined` (resolves to false) | Boolean-like string | Non-secret Config |
| `PLAYWRIGHT_SEED_ON_START` | Triggers the database seed script (`pnpm test:seed`) before running tests. | `harness/env.ts` (buildRawEnv) | Optional | `undefined` (resolves to false) | Boolean-like string | Non-secret Config |
| `PLAYWRIGHT_SKIP_SEED` | Prevents the seed script from running, even if logic otherwise suggests it should. | `harness/env.ts` (buildRawEnv) | Optional | `undefined` (resolves to false) | Boolean-like string | Non-secret Config |
| `PLAYWRIGHT_SKIP_STORAGE_STATE` | Skips the authentication/storage state generation step in global setup. | `harness/env.ts` (buildRawEnv) | Optional | `undefined` (resolves to false) | Boolean-like string | Non-secret Config |
| `PLAYWRIGHT_SKIP_WEB_SERVER` | Flag intended to skip starting the local web server (referenced in env object). | `harness/env.ts` (buildRawEnv) | Optional | `undefined` (resolves to false) | Boolean-like string | Non-secret Config |
| `PLAYWRIGHT_TENANT_ADMIN_EMAIL` | Email address for the primary tenant admin account. | `harness/env.ts` (buildRawEnv) | Optional | `'user@example.com'` | Valid email string | Non-secret Config |
| `PLAYWRIGHT_TENANT_ADMIN_PASSWORD` | Password for the primary tenant admin account. | `harness/env.ts` (buildRawEnv) | Optional | `'SuperSecret123!'` | String (min length 1) | **Secret** |
| `PLAYWRIGHT_TENANT_SLUG` | The tenant slug identifier for the primary test organization. | `harness/env.ts` (buildRawEnv) | Optional | `'playwright-starter'` | String (min length 1) | Non-secret Config |