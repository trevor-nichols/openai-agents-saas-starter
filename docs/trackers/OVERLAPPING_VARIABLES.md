### 1. Environment vs debug — resolved

* `ENVIRONMENT` is the single source of truth.
* `DEBUG` now auto-derives from `ENVIRONMENT` (true only for `development|dev|local|test`). No operator input required; explicit overrides are discouraged.
* Secret/Vault hardening still keys off the derived `DEBUG` + `ENVIRONMENT` pair.

---

### 2. Frontend/API URLs & CORS — resolved

**Group A – frontend / origins**

* `APP_PUBLIC_URL`
* `ALLOWED_ORIGINS`

Resolution:
* `APP_PUBLIC_URL` is canonical for the frontend.
* CORS now always includes `APP_PUBLIC_URL`; `ALLOWED_ORIGINS` remains only as an additive list for extras.
* Defaults remain localhost-friendly but dedupe automatically.

**Group B – backend / API URLs**

* `API_BASE_URL`
* `NEXT_PUBLIC_API_URL`

Resolution:
* `API_BASE_URL` is canonical for the backend.
* `NEXT_PUBLIC_API_URL` is always derived by the frontend from `API_BASE_URL` (build-time fallback), so operators set it once.

**Cross-group overlap**

* `APP_PUBLIC_URL`
* `ALLOWED_ORIGINS`
* `API_BASE_URL`
* `NEXT_PUBLIC_API_URL`

Resolution:
* “Frontend origin”: `APP_PUBLIC_URL`.
* “Backend/API base”: `API_BASE_URL` (mirrored to `NEXT_PUBLIC_API_URL`).
* `ALLOWED_ORIGINS` is only an additive list when you truly need extra origins.

---

### 3. Redis base vs specialized Redis URLs — resolved

* `REDIS_URL`
* `RATE_LIMIT_REDIS_URL`
* `AUTH_CACHE_REDIS_URL`
* `SECURITY_TOKEN_REDIS_URL`
* `BILLING_EVENTS_REDIS_URL`

Resolution:
* `REDIS_URL` is required baseline.
* Specialized URLs are optional overrides and explicitly fall back to `REDIS_URL`.
* Hardened envs enforce TLS/auth and emit warnings if sensitive workloads ride on the baseline URL.

---

### 4. Billing Redis specifically — resolved

* `BILLING_EVENTS_REDIS_URL` remains the dedicated knob; it falls back to `REDIS_URL` only when left unset.
* Factory validation + startup checks keep billing streams isolated when a dedicated URL is provided.