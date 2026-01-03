## apps/web-app/lib

| Name | Purpose | Location | Required | Default | Format | Sensitivity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `AGENT_ALLOW_INSECURE_COOKIES` | If set to `true`, disables the `secure` flag on cookies even when `NODE_ENV` is production. | `auth/cookieConfig.ts` | Optional | `false` (implicit) | boolean string (`true`) | Config |
| `AGENT_FORCE_SECURE_COOKIES` | If set to `true`, forces the `secure` flag on cookies even in non-production environments. | `auth/cookieConfig.ts` | Optional | `false` (implicit) | boolean string (`true`) | Config |
| `API_BASE_URL` | Server-side fallback URL for the backend API. | `config/server.ts` | Optional | `http://localhost:8000` | URL string | Config |
| `APP_PUBLIC_URL` | Public base URL used for SEO/absolute links. | `seo/siteUrl.ts` | Optional | `http://localhost:3000` | URL string | Config |
| `NEXT_PUBLIC_AGENT_API_MOCK` | Client-side flag to enable mock API mode. | `config.ts` | Optional | `false` (implicit) | boolean string (`true`) | Config |
| `NEXT_PUBLIC_LOG_LEVEL` | Minimum log severity level to emit. | `logging/index.ts` | Optional | `info` | string (`debug`, `info`, `warn`, `error`) | Config |
| `NEXT_PUBLIC_LOG_SINK` | Destination for log events. | `logging/index.ts` | Optional | `console` | string (`console`, `beacon`, `none`) | Config |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Public key for Stripe Elements integration. | `config/stripe.ts` | Optional | `''` | string | Public Key |
| `NODE_ENV` | Determines environment mode (production vs development vs test). Affects secure cookies and logging fallbacks. | `auth/cookieConfig.ts`, `logging/index.ts` | Optional | `development` (implicit) | string | Config |
| `PLAYWRIGHT_TENANT_ADMIN_EMAIL` | Email used for the mock user profile when `USE_API_MOCK` is active. | `server/services/users.ts` | Optional | `mock-admin@example.com` | email string | Config |
| `VERCEL_GIT_COMMIT_TIMESTAMP` | Git commit timestamp provided by Vercel, used for "Last Modified" dates. | `seo/deployInfo.ts` | Optional | `new Date()` | ISO Date string | Config |
