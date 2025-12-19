# Vector Stores & File Search in Agents

Last updated: November 25, 2025

## What this covers
- How to let an agent use OpenAI file_search with tenant-specific vector stores.
- How to resolve the correct vector store at runtime (tenant default vs static IDs).
- Minimal code changes for a new agent spec.

## TL;DR
1) Ensure a vector store exists for the tenant (we auto-provision a "primary" store via `ensure_primary_store`; disable with `AUTO_CREATE_VECTOR_STORE_FOR_FILE_SEARCH=false`).
2) Add the `file_search` tool to your agent's `tool_keys`.
3) In the AgentSpec, declare how to bind vector stores:
   - Tenant default (recommended): resolved at request-time to the tenant's primary store.
   - Static IDs: provide specific OpenAI vector store IDs.

## AgentSpec pattern

```python
# app/agents/my_agent/spec.py
from app.agents._shared.specs import AgentSpec


def get_agent_spec() -> AgentSpec:
    return AgentSpec(
        key="my_agent",
        display_name="My Agent",
        description="Answers using your uploaded docs.",
        tool_keys=("file_search",),
        # Bindings: choose one of the two below
        vector_store_binding="tenant_default",  # resolves to tenant's primary store
        # vector_store_binding="static",
        # vector_store_ids=("vs_abc123",),
        file_search_options={
            "max_num_results": 5,
            # Optional filters/ranking options go here
        },
    )
```

Notes:
- `vector_store_binding="tenant_default"` will call `ensure_primary_store` at runtime and inject that store ID into the FileSearchTool. This is the fastest path for multi-tenant setups.
- If you must pin to a specific OpenAI store, set `vector_store_binding="static"` and list `vector_store_ids`.
- `file_search_options` are passed through to the tool (e.g., `filters`, `ranking_options`, `max_num_results`, `include_results`).

## Runtime resolution (what happens under the hood)
- The OpenAI provider registry builds tools per request. When it sees the file_search tool and a `tenant_default` binding, it:
  1) Ensures the tenant has a primary vector store (creates one if missing).
  2) Attaches that store's OpenAI ID to the FileSearchTool before sending the run to OpenAI.

## API workflow reminder
- Before agents can search, tenants must upload files to a vector store and wait for status `completed`.
  - If you already have an OpenAI `file_id`, attach via `/api/v1/vector-stores/{id}/files`.
  - If you have a storage object in this service, promote + attach via `/api/v1/vector-stores/{id}/files/upload`.
- Search can also be invoked directly via `/api/v1/vector-stores/{id}/search` if you want pre- or post-agent retrieval.

## Common options
- Limit results: set `max_num_results` in `file_search_options`.
- Filters: attach `attributes` to files and pass `filters` in `file_search_options` (see OpenAI retrieval guide).
- Include results in response: `include_results=True` (incurs more tokens).

## API quickstart (tenant-scoped)
1) Create store
   ```bash
   curl -X POST "$API_URL/api/v1/vector-stores" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name":"primary"}'
   ```
2) Attach a file (after uploading via Files API and obtaining file_id)
   ```bash
   curl -X POST "$API_URL/api/v1/vector-stores/$STORE_ID/files" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"file_id":"$FILE_ID","poll":true}'
   ```
2b) Attach a file from storage (upload to storage first, then promote)
   ```bash
   curl -X POST "$API_URL/api/v1/vector-stores/$STORE_ID/files/upload" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"object_id":"$OBJECT_ID","agent_key":"$AGENT_KEY","poll":true}'
   ```
3) Search
   ```bash
   curl -X POST "$API_URL/api/v1/vector-stores/$STORE_ID/search" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"query":"how do refunds work?","max_num_results":5}'
   ```

Notes: Endpoints are tenant-gated; viewer can read/search, admin/owner can create/delete/attach.

## Guardrails already applied
- MIME allowlist, max file size, per-store file count, tenant byte cap, duplicate name conflict → handled server-side. Errors surface as 400/403/409.

### Plan-based overrides (optional)
- If billing + usage guardrails are enabled and plan entitlements define any of the following feature keys, they override the defaults above per tenant:
  - `vector.max_file_bytes` (bytes)
  - `vector.total_bytes_per_tenant` (bytes)
  - `vector.files_per_store` (count)
  - `vector.stores_per_tenant` (count)
- The starter CLI wizard can add these to `usage-entitlements.json`; otherwise defaults from settings are used.

### Background sync worker (default ON)
- Enabled by default (`ENABLE_VECTOR_STORE_SYNC_WORKER=true`) to refresh store/file status and apply expirations.
- Settings:
  - `VECTOR_STORE_SYNC_POLL_SECONDS` (default 60s)
  - `VECTOR_STORE_SYNC_BATCH_SIZE` (default 20)
  - `AUTO_PURGE_EXPIRED_VECTOR_STORES` (default false) — when true, expired stores are deleted remotely and soft-deleted locally.
- For constrained local dev, set `ENABLE_VECTOR_STORE_SYNC_WORKER=false` to disable.

## Gotchas
- If you use static IDs, ensure they belong to the same tenant; cross-tenant access is blocked.
- file_search cannot auto-create vector stores; provisioning happens via our service (tenant-default) or explicit API calls.
