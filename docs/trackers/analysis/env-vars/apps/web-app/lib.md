## apps/web-app/lib

| Name | Purpose | Location | Required | Default | Format | Sensitivity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `AGENT_ALLOW_INSECURE_COOKIES` | If set to `true`, disables the `secure` flag on cookies even when `NODE_ENV` is production. | `auth/cookieConfig.ts` | Optional | `false` (implicit) | boolean string (`true`) | Config |
| `AGENT_API_MOCK` | Server-side flag to enable mock API mode. | `config.ts` | Optional | `false` (implicit) | boolean string (`true`) | Config |
| `AGENT_FORCE_SECURE_COOKIES` | If set to `true`, forces the `secure` flag on cookies even in non-production environments. | `auth/cookieConfig.ts` | Optional | `false` (implicit) | boolean string (`true`) | Config |
| `API_BASE_URL` | Server-side fallback URL for the backend API. | `config.ts` | Optional | `http://localhost:8000` | URL string | Config |
| `NEXT_PUBLIC_AGENT_API_MOCK` | Client-side flag to enable mock API mode. | `config.ts` | Optional | `false` (implicit) | boolean string (`true`) | Config |
| `NEXT_PUBLIC_API_URL` | Primary URL for the backend API (accessible to client). | `config.ts` | Optional | `http://localhost:8000` | URL string | Config |
| `NEXT_PUBLIC_ENABLE_BILLING` | Feature flag to enable/disable billing-related UI and queries. | `config/features.ts` | Optional | `false` (except `true` in test) | boolean string (`true`, `1`, `yes`) | Config |
| `NEXT_PUBLIC_LOG_LEVEL` | Minimum log severity level to emit. | `logging/index.ts` | Optional | `info` | string (`debug`, `info`, `warn`, `error`) | Config |
| `NEXT_PUBLIC_LOG_SINK` | Destination for log events. | `logging/index.ts` | Optional | `console` | string (`console`, `beacon`, `none`) | Config |
| `NEXT_PUBLIC_SITE_URL` | Base URL of the deployed application (used for SEO/absolute links), preferred over Vercel URL. | `seo/siteUrl.ts` | Optional | `http://localhost:3000` | URL string | Config |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Public key for Stripe Elements integration. | `config/stripe.ts` | Optional | `''` | string | Public Key |
| `NEXT_PUBLIC_VERCEL_URL` | Automatically set by Vercel; used as a fallback for site URL. | `seo/siteUrl.ts` | Optional | `http://localhost:3000` | URL string (host) | Config |
| `NODE_ENV` | Determines environment mode (production vs development vs test). Affects secure cookies, billing defaults, and logging fallbacks. | `auth/cookieConfig.ts`, `config/features.ts`, `logging/index.ts` | Optional | `development` (implicit) | string | Config |
| `PLAYWRIGHT_TENANT_ADMIN_EMAIL` | Email used for the mock user profile when `USE_API_MOCK` is active. | `server/services/users.ts` | Optional | `mock-admin@example.com` | email string | Config |
| `SITE_URL` | Server-side override for the application's base URL. | `seo/siteUrl.ts` | Optional | `http://localhost:3000` | URL string | Config |
| `VERCEL_GIT_COMMIT_TIMESTAMP` | Git commit timestamp provided by Vercel, used for "Last Modified" dates. | `seo/deployInfo.ts` | Optional | `new Date()` | ISO Date string | Config |