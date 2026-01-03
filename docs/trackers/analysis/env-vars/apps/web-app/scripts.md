## apps/web-app/scripts

| Name | Purpose | Where it’s used | Required? | Default | Format | Sensitivity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`LOG_ROOT`** | Defines the root directory where dated log files are written. Passed to child processes as well. | `with-log-root.js` (Line 25) | Optional | `var/log` (relative to repo root) | Directory path | Non-secret config |
| **`API_BASE_URL`** | Fallback API URL used for fixture seeding if `PLAYWRIGHT_API_URL` is not set. | `test-seed.js` (Line 99) | Optional | `http://localhost:8000` | URL string | Non-secret config |
| **`PLAYWRIGHT_API_URL`** | Primary override for the backend API URL when running seed fixtures. | `test-seed.js` (Line 98) | Optional | `API_BASE_URL` or `http://localhost:8000` | URL string | Non-secret config |
| **`PLAYWRIGHT_SEED_FILE`** | Path to the YAML specification file used for seeding data. | `test-seed.js` (Line 23) | Optional | `seeds/playwright.yaml` (relative to project root) | File path | Non-secret config |
