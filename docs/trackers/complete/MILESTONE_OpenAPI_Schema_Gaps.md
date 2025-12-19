# OpenAPI Contract Gaps & Fix Plan

This doc lists **everything discovered (from the current OpenAPI + provided code)** that should be addressed to make the API contract accurate, stable for client generation, and developer-friendly. It focuses on **schema correctness**, **content types**, **streaming semantics**, and **error-model alignment**.

---

## Execution plan (contract hardening)

This milestone is intentionally **contract-first**: we will treat the OpenAPI artifact as a production interface and systematically align **runtime behavior ↔ documented schemas** so typed clients (HeyAPI/TanStack Query) and third-party integrators behave correctly.

### Decisions (recommended path — adopted)

#### Decision A — Error responses

- We will adopt **one** error envelope for *all* errors and ensure OpenAPI matches it everywhere.
- Runtime will return **only** `ErrorResponse` fields (`success=false`, `error`, `message`, `details`) for both `HTTPException` and validation failures.
  - We will **not** include an extra top-level `detail` field (current handler sometimes injects it).
  - HTTP headers stay as actual response headers, not duplicated into the JSON body.
- OpenAPI will advertise:
  - `422` as `ValidationErrorResponse` (same envelope; `details` is the Pydantic errors list)
  - common errors (`400/401/403/404/409/413/429/5xx`) as `ErrorResponse` where applicable

#### Decision B — Frontend log ingest contract

- We will refactor `POST /api/v1/logs` to a normal typed request:
  - body: `FrontendLogPayload` (FastAPI request body schema)
  - header: `x-log-signature` (required)
- Signature verification will remain correct by verifying against `await request.body()` (FastAPI caches request bodies, so we can still use typed parsing afterwards).
- Status code alignment:
  - `422` for invalid JSON / body validation
  - `401` for missing/invalid signature or missing secret
  - `403` when anonymous ingest is disabled
  - `413` when payload exceeds limits

#### Decision C — Vector store search response typing

- We will not expose an untyped OpenAI passthrough (`Any`) for `/api/v1/vector-stores/{vector_store_id}/search`.
- Instead we will define a stable DTO and map OpenAI’s response into our contract.
  - Planned contract shape mirrors the OpenAI “search vector store” response page:
    - top-level: `object`, `search_query`, `data`, `has_more`, `next_page`
    - each result: `file_id`, `filename`, `score`, `attributes`, `content[]` (text chunks)
  - Current OpenAI response shape (from official API reference at time of review):
    - `object`: `"vector_store.search_results.page"`
    - `search_query`: `string[]`
    - `data`: array of:
      - `file_id`: `string`
      - `filename`: `string`
      - `score`: `number`
      - `attributes`: `object`
      - `content`: array of `{ type: "text", text: string }`
    - `has_more`: `boolean`
    - `next_page`: `string` (treat as nullable/optional defensively)

### Documentation requirements (to avoid guessing)

- We **do not** need OpenAI API documentation for our error envelopes, SSE wrapper semantics, Stripe webhook request schema (free-form), RSS, or binary download responses.
- We **do** need official OpenAI documentation for **Vector Store Search** (`POST /v1/vector_stores/{vector_store_id}/search`) to lock the exact response shape (fields + optionality) before we finalize the DTO + mapping. (The local `openai_raw_api_reference.md` focuses on the Responses API/tooling and does not include the Vector Stores REST `/search` response schema.)

### Guiding principles

- **Truthfulness:** OpenAPI must describe what the server actually returns (content-type, status codes, shapes).
- **Stability:** Prefer explicit DTOs over `Any`/free-form objects; where passthrough is required, document it explicitly.
- **Minimal “OpenAPI hacks”:** Prefer `response_model=...`, typed headers/body params, and `responses=...` over large `openapi_extra` blobs.
- **No legacy constraints:** We may change runtime responses where doing so produces a cleaner, more consistent contract.
- **Verified, not guessed:** Anything that mirrors OpenAI payloads must be sourced from official docs (repo docs or web) before we lock it into public schemas.

### Definition of done

- `starter_cli api export-openapi --enable-billing --enable-test-fixtures` produces an OpenAPI spec where:
  - streaming routes are `text/event-stream`
  - binary/RSS routes declare correct media types and headers
  - all “raw-body” endpoints declare request bodies + signature headers
  - validation errors (`422`) and common errors use our unified error envelope
  - previously untyped responses (`{}` / `Any`) are tightened where feasible
- Backend passes `hatch run lint` + `hatch run typecheck`.
- Frontend SDK regeneration succeeds (`pnpm generate:fixtures`) without requiring hand-edits of generated files.
- A small **contract test suite** asserts the key OpenAPI guarantees so we don’t regress.

### Phased work plan (do in order)

#### Phase 1 — Lock in contract checks (prevents regressions)

- [x] Add backend contract tests that generate OpenAPI from `create_application()` and assert:
  - `GET /api/v1/activity/stream` and `GET /api/v1/billing/stream` advertise `text/event-stream`
  - download endpoints advertise `application/octet-stream` + `Content-Disposition`
  - `GET /api/v1/status/rss` advertises `application/rss+xml`
  - raw-body endpoints include `requestBody` and signature headers
  - `422` uses our validation error envelope (not `HTTPValidationError`)
- [x] Document the local workflow: regenerate OpenAPI → regenerate SDK → run typechecks.

Implementation notes (Phase 1):

- OpenAPI patch layer: `apps/api-service/src/app/api/openapi.py`
- OpenAPI wired into app factory: `apps/api-service/src/main.py`
- Contract tests: `apps/api-service/tests/contract/test_openapi_contract.py`
- Test harness hardening: `OPENAI_AGENTS_DISABLE_TRACING=true` is set for pytest to prevent shutdown-unsafe debug logs.

Local workflow (dev):

1) Export OpenAPI (with optional routes enabled)
   - `python -m starter_cli.app api export-openapi --output apps/api-service/.artifacts/openapi-fixtures.json --enable-billing --enable-test-fixtures`
2) Regenerate frontend SDK (offline)
   - `cd apps/web-app && OPENAPI_INPUT=../api-service/.artifacts/openapi-fixtures.json pnpm generate:fixtures`
3) Validate
   - `just backend-lint && just backend-typecheck`
   - `just web-lint && just web-typecheck`

#### Phase 2 — Standardize error envelope + OpenAPI alignment

Decision to make up-front (recommended):
- **Adopt a single error envelope** for both `HTTPException` and validation errors, without “sometimes extra fields”.

Work items:
- [x] Decide the final error response shape (recommended: `ErrorResponse` with `details` carrying either structured context or validation errors; avoid an extra `detail` field).
- [x] Update `app/api/errors.py` to emit exactly that shape for both handlers (and add a safe 500 handler for unhandled exceptions).
- [x] Ensure OpenAPI advertises that shape for:
  - `422` validation errors globally
  - common failure statuses (`400/401/403/404/409/413/429/5xx`) either per-route or via a documented default response strategy

Implementation notes (Phase 2):

- Runtime:
  - `apps/api-service/src/app/api/errors.py` now emits only the `ErrorResponse` envelope for `HTTPException`, validation errors, and unhandled exceptions (500). No extra top-level `detail` field.
- OpenAPI:
  - `apps/api-service/src/app/api/openapi.py` adds a baseline set of error responses (plus `default`) to every operation, all referencing `ErrorResponse`.
  - `HTTPValidationError` / `ValidationError` are removed from the generated component schemas to avoid client confusion; `422` references `ValidationErrorResponse`.
- Tests:
  - `apps/api-service/tests/unit/api/test_error_handlers.py` asserts runtime envelope correctness for `HTTPException` and unhandled exceptions.

#### Phase 3 — Fix content-types & schemas for non-JSON endpoints

- [x] SSE routes:
  - `GET /api/v1/activity/stream`: document `text/event-stream` and declare the `data:` payload as JSON matching `ActivityEventItem`
  - `GET /api/v1/billing/stream`: document `text/event-stream` and declare the `data:` payload as JSON matching `BillingEventResponse`
- [x] Binary downloads:
  - `GET /api/v1/openai/files/{file_id}/download`
  - `GET /api/v1/openai/containers/{container_id}/files/{file_id}/download`
  - Document `application/octet-stream` response schema (`format: binary`) + headers (`Content-Disposition`, `Cache-Control`)
- [x] RSS:
  - `GET /api/v1/status/rss`: declare `application/rss+xml` response content

Implementation notes (Phase 3):

- OpenAPI SSE docs now include explicit framing notes (heartbeats + `data: <json>`):
  - `apps/api-service/src/app/api/openapi.py`
- Contract tests assert the presence of `text/event-stream`, SSE framing wording, and download headers:
  - `apps/api-service/tests/contract/test_openapi_contract.py`

#### Phase 4 — Raw-body request schemas (webhooks + signed ingest)

- [x] Stripe webhook (`POST /webhooks/stripe`):
  - Document required `Stripe-Signature` header
  - Document request body as either `application/json` (free-form) and/or `application/octet-stream` (raw bytes)
  - Optional hardening: document stable 202 response body fields (`success`, `duplicate`)
- [x] Frontend log ingest (`POST /api/v1/logs`, conditional):
  - Document required `x-log-signature` header
  - Document request body schema to match `FrontendLogPayload`
  - Decide whether invalid payloads should be `422` (FastAPI validation) or `400` (current manual validation), then align OpenAPI + runtime accordingly

Implementation notes (Phase 4):

- Logs ingest is now a typed request body (`FrontendLogPayload`) so OpenAPI includes the request schema automatically:
  - `apps/api-service/src/app/api/v1/logs/router.py`
- Logs signature verification uses the raw request bytes for HMAC, but signature failures return `401` (envelope `ErrorResponse`), and oversized payloads return `413` with a stable error code and `details.max_bytes`.
- Stripe webhook continues to validate against raw request bytes (required for signature verification) while OpenAPI documents both JSON and octet-stream bodies:
  - `apps/api-service/src/app/presentation/webhooks/stripe.py`
- Tests were added/updated to reflect the unified error envelope and the signed-ingest semantics:
  - `apps/api-service/tests/unit/api/test_frontend_logs_route.py`
  - `apps/api-service/tests/unit/api/test_stripe_webhook_route.py`

#### Phase 5 — Tighten “loose” schemas without guessing external APIs

- [x] `/api/v1/tools`:
  - Replace `dict[str, object]` with a typed `ToolCatalogResponse` model (shape is already stable: `total_tools`, `tool_names`, `categories`, `per_agent`)
- [x] `/api/v1/vector-stores/{vector_store_id}/search`:
  - **Research-first:** confirm the OpenAI vector store search response shape from official docs (repo docs or web)
  - Choose a stable contract strategy:
    - **Option A (recommended):** define a minimal stable `VectorStoreSearchMatch[]` DTO and map OpenAI response → DTO (better DX + stability)
    - Option B: explicitly document as passthrough `object` with `additionalProperties: true` and label it “OpenAI passthrough (unstable)”

Implementation notes (Phase 5):

- Tools catalog is now typed end-to-end:
  - `apps/api-service/src/app/api/v1/tools/schemas.py`
  - `apps/api-service/src/app/api/v1/tools/router.py`
- Vector store search response is now typed using the local OpenAI reference:
  - Source of truth: `docs/integrations/openai-agents-sdk/tools/rag/vector-stores-&-retrieval-api.md` (Search vector store section).
  - Domain model + mapping: `apps/api-service/src/app/services/vector_stores/search.py` + `apps/api-service/src/app/domain/vector_stores.py`
  - API DTOs: `apps/api-service/src/app/api/v1/vector_stores/schemas.py`
- Tests:
  - OpenAPI contract asserts `/api/v1/tools` and `/api/v1/vector-stores/{vector_store_id}/search` schemas are `$ref`’d (no `Any` / free-form objects): `apps/api-service/tests/contract/test_openapi_contract.py`
  - Search mapping unit test: `apps/api-service/tests/unit/vector_stores/test_search_service_contract.py`

#### Phase 6 — Publish artifacts + frontend alignment

- [x] Export OpenAPI artifact to `apps/api-service/.artifacts/openapi-fixtures.json`.
- [x] Regenerate the frontend HeyAPI client (`apps/web-app/lib/api/client/**`) using the artifact.
- [ ] Validate end-to-end typing:
  - [x] Backend: `just backend-lint` and `just backend-typecheck`
  - [ ] Frontend: `just web-lint` and `just web-typecheck` (pending; to be handled by web team/agents)

## 0) Global error responses do **not** match the OpenAPI (highest priority)

### Problem

Your API **overrides FastAPI’s default error shapes** in `app/api/errors.py`, but the OpenAPI still advertises FastAPI’s defaults in many places (e.g., `HTTPValidationError` for `422`).

**Reality (implementation)**

* **Request validation errors (422)** return your `ErrorResponse` envelope:

  * `success=false`
  * `error="ValidationError"`
  * `message="Request validation failed."`
  * `details=[...]` (Pydantic error list)

* **HTTPException errors (all other 4xx/5xx you raise)** return:

  * the same `ErrorResponse` envelope fields (`success=false`, `error`, `message`, `details`)
  * plus a `detail` field that mirrors the original exception detail (string or object)

This means autogenerated clients and frontend error parsing will be wrong unless OpenAPI is updated to reflect your real runtime responses.

### Suggested OpenAPI fix (recommended)

Define a consistent error schema and use it for `4xx` / `5xx` (and `422`) responses.

**Option A (match implementation exactly)**

```yaml
components:
  schemas:
    ErrorResponse:
      type: object
      properties:
        success: { type: boolean, default: false }
        error: { type: string, description: "Machine-readable error code/name." }
        message: { type: string, description: "Human-readable error message." }
        details:
          nullable: true
          description: "Additional error context (varies)."
        detail:
          nullable: true
          description: "HTTPException detail (string or object). Present for HTTPException handler."
      required: [success, error, message]

    ValidationErrorResponse:
      allOf:
        - $ref: "#/components/schemas/ErrorResponse"
      description: "Validation error envelope (RequestValidationError)."
```

Then for endpoints that currently list `422: HTTPValidationError`, replace with:

```yaml
"422":
  description: Validation Error
  content:
    application/json:
      schema:
        $ref: "#/components/schemas/ValidationErrorResponse"
```

And for common auth/permission failures you actually emit, add:

* `400`, `401`, `403`, `404`, `409`, `429`, `502`, `503` as appropriate → `ErrorResponse`

**Option B (simplify)**
Stop overriding FastAPI’s default validation/error responses and revert to standard `HTTPValidationError`. (Less work in OpenAPI, but you lose your unified envelope.)

---

## 1) Endpoints missing a **request body schema**

### `POST /webhooks/stripe`

**Problem**

* OpenAPI defines a response schema but **does not define requestBody**.
* Webhook signature verification typically requires handling **raw body bytes**, even if the payload is JSON.

**Suggested OpenAPI fix**

```yaml
/webhooks/stripe:
  post:
    summary: Handle Stripe Webhook
    parameters:
      - in: header
        name: Stripe-Signature
        required: true
        schema: { type: string }
        description: Stripe signature header used to verify the webhook payload.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            additionalProperties: true
            description: Stripe event payload (shape varies by event type).
        application/octet-stream:
          schema:
            type: string
            format: binary
          description: Raw webhook bytes (useful for signature verification implementations).
    responses:
      "202":
        description: Accepted
        content:
          application/json:
            schema:
              type: object
              additionalProperties:
                type: boolean
```

---

## 2) Endpoints with **empty/unspecified** success response schemas

### `POST /api/v1/workflows/runs/{run_id}/cancel`

**Problem**

* OpenAPI: `202` response schema is `{}` (unspecified)
* Implementation returns `{"success": True}`

**Suggested OpenAPI fix**

```yaml
components:
  schemas:
    CancelWorkflowRunResponse:
      type: object
      properties:
        success: { type: boolean }
      required: [success]

/api/v1/workflows/runs/{run_id}/cancel:
  post:
    responses:
      "202":
        description: Cancel request accepted
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CancelWorkflowRunResponse"
```

**Alternative (standardize)**
Return `SuccessResponse` from the handler and update OpenAPI accordingly.

---

## 3) Streaming endpoints: OpenAPI declares JSON, but implementation is **SSE** (`text/event-stream`)

### `GET /api/v1/activity/stream`

**Problem**

* OpenAPI: `200` response schema is `{}` / `application/json`
* Implementation: SSE stream via `StreamingResponse(..., media_type="text/event-stream")`

**Actual stream format**

* Heartbeats: `":\n\n"`
* Events: `data: {message}\n\n` where `message` is the subscription output (often JSON, but not guaranteed unless enforced upstream).

**Suggested OpenAPI fix**

```yaml
/api/v1/activity/stream:
  get:
    summary: Stream Activity Events
    responses:
      "200":
        description: Server-sent events stream of activity updates.
        content:
          text/event-stream:
            schema:
              type: string
              description: |
                SSE stream.
                Heartbeats emitted as comments: ":\n\n"
                Events emitted as: "data: <message>\n\n"
                If <message> is JSON, document its schema explicitly (recommended).
```

> If you can guarantee JSON payloads, define `ActivityStreamEvent` (or reuse `ActivityEventItem`) and document that `data:` is JSON.

---

### `GET /api/v1/billing/stream`

**Problem**

* OpenAPI: `200` response schema is `{}` / `application/json`
* Implementation: SSE stream with heartbeats.

**Actual stream format**

* Heartbeats: `": ping\n\n"`
* Events: `data: {message}\n\n`

**Suggested OpenAPI fix**

```yaml
/api/v1/billing/stream:
  get:
    summary: Stream Billing Events
    responses:
      "200":
        description: Server-sent events stream of billing events.
        content:
          text/event-stream:
            schema:
              type: string
              description: |
                SSE stream.
                Heartbeats are emitted as comments: ": ping\n\n"
                Events emitted as: "data: <message>\n\n"
                If <message> is JSON, document its schema explicitly (recommended).
```

---

## 4) Endpoints that return **non-JSON**, but OpenAPI models as JSON / `{}`

### `GET /api/v1/openai/files/{file_id}/download`

### `GET /api/v1/openai/containers/{container_id}/files/{file_id}/download`

**Problem**

* OpenAPI declares `application/json` with `{}`.
* Implementation returns **binary bytes** with `media_type="application/octet-stream"` and sets `Content-Disposition`.

**Suggested OpenAPI fix**

```yaml
/api/v1/openai/files/{file_id}/download:
  get:
    summary: Download OpenAI File
    responses:
      "200":
        description: Binary file download.
        headers:
          Content-Disposition:
            schema: { type: string }
            description: Attachment filename hint.
          Cache-Control:
            schema: { type: string }
            description: Cache policy for downloads.
        content:
          application/octet-stream:
            schema:
              type: string
              format: binary

/api/v1/openai/containers/{container_id}/files/{file_id}/download:
  get:
    summary: Download OpenAI Container File
    responses:
      "200":
        description: Binary file download.
        headers:
          Content-Disposition:
            schema: { type: string }
        content:
          application/octet-stream:
            schema:
              type: string
              format: binary
```

---

### `GET /api/v1/status/rss`

**Problem**

* OpenAPI: `200` has no schema/content type.
* Implementation returns RSS XML: `application/rss+xml; charset=utf-8`.

**Suggested OpenAPI fix**

```yaml
/api/v1/status/rss:
  get:
    summary: Get Platform Status RSS
    responses:
      "200":
        description: RSS feed (XML).
        content:
          application/rss+xml:
            schema:
              type: string
              description: RSS XML document
```

---

## 5) Feature-flag endpoint likely to have the same “missing request schema” issue

### `POST /api/v1/logs` (only when `enable_frontend_log_ingest` is enabled)

**Problem**

* The handler reads raw request bytes and validates JSON manually (plus signature header `x-log-signature`).
* Endpoints shaped like this often end up with **missing requestBody schema** in OpenAPI unless explicitly modeled.

**Suggested OpenAPI fix**
Define the request schema (matches `FrontendLogPayload`) and document the signature header:

```yaml
/api/v1/logs:
  post:
    summary: Ingest frontend log event
    parameters:
      - in: header
        name: x-log-signature
        required: true
        schema: { type: string }
        description: HMAC signature for the raw request body.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/FrontendLogPayload"
    responses:
      "202":
        description: Accepted
        content:
          application/json:
            schema:
              type: object
              properties:
                accepted: { type: boolean }
              required: [accepted]
```

---

## 6) “Schema exists” but it’s **too loose to be useful** (DX & stability)

These aren’t strictly “missing” schemas, but for a strong contract (and resume story), they should be tightened.

### `POST /api/v1/vector-stores/{vector_store_id}/search`

**Problem**

* Response schema exists, but `VectorStoreSearchResponse.data` is `Any`.
* This prevents typed clients and forces consumers to guess structure.

**Recommendation**

* Choose and codify a stable result shape, e.g.:

```yaml
components:
  schemas:
    VectorStoreSearchMatch:
      type: object
      properties:
        file_id: { type: string }
        score: { type: number }
        text: { type: string, nullable: true }
        attributes:
          type: object
          additionalProperties: true
          nullable: true
      required: [file_id, score]

    VectorStoreSearchResponse:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: "#/components/schemas/VectorStoreSearchMatch"
      required: [data]
```

(Adjust to your actual backend shape.)

---

### `GET /api/v1/tools`

**Problem**

* Returns `dict[str, object]` (free-form), which makes clients brittle.

**Recommendation**

* If `agent_service.get_tool_information()` is stable, define a `ToolInfo` schema and return:

  * `Record<string, ToolInfo>`

---

### Success envelopes where `data` is effectively untyped

Your `SuccessResponse.data` is `Any | null`, which is fine internally, but weak for client generation.

**Recommendation**

* Optional but powerful: move to **generic typed envelopes** (or explicit dedicated responses per endpoint) so `data` becomes concrete.

  * Example: `SuccessResponse[ContactSubmissionResponse]` (or dedicated `ContactSubmissionEnvelope`)

---

## 7) Streaming “payload type” clarity (contract tightening)

Even after switching `content-type` to `text/event-stream`, you should decide what the **SSE `data:` field contains**:

* If it’s **always JSON**:

  * Document the schema (ideal).
* If it’s **opaque string**:

  * Document it as `type: string` with a clear note.

**Specific callouts**

* `activity/stream`: upstream `message` type should be defined (string vs JSON).
* `billing/stream`: same.

---

## Summary Checklist (complete set)

### Must-fix (contract correctness)

* [x] **Global errors:** OpenAPI must match `ErrorResponse` envelope (incl. validation 422).
* [x] `POST /webhooks/stripe`: add requestBody schema + document `stripe-signature` header (and raw-body option).
* [x] `GET /api/v1/activity/stream`: mark as `text/event-stream` + document SSE shape.
* [x] `GET /api/v1/billing/stream`: mark as `text/event-stream` + document SSE shape + heartbeat comments.
* [ ] `POST /api/v1/workflows/runs/{run_id}/cancel`: define response schema (or standardize to `SuccessResponse`).
* [x] `GET /api/v1/openai/*/download`: change to `application/octet-stream` with `format: binary` + document headers.
* [x] `GET /api/v1/status/rss`: declare `application/rss+xml`.

### Conditional (when feature flags enabled)

* [x] `POST /api/v1/logs`: define requestBody schema + document `x-log-signature` header.

### Strongly recommended (better DX + typed clients)

* [x] `VectorStoreSearchResponse.data`: replace `Any` with concrete model(s).
* [x] `/api/v1/tools`: define stable tool metadata schema if possible.
* [ ] Consider typed success envelopes (or per-endpoint response DTOs) so `data` isn’t `Any`.
