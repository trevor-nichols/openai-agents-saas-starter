# Vector Stores services

End-to-end vector store orchestration (OpenAI Vector Stores) plus agent bindings and search.

## What lives here
- `service.py` — façade wiring OpenAI gateway + repositories for stores, files, bindings, search.
- `stores.py` / `files.py` — CRUD for stores and file attachments (OpenAI Vector Store API + DB mirror).
- `bindings.py` — bind/unbind agents to stores (per-tenant), lookup bindings.
- `search.py` — executes vector store search via gateway with instrumentation.
- `policy.py` / `limits.py` — plan-aware quota/limit checks.
- `sync_worker.py` — optional background sync for status/expiry.

## AgentSpec integration (file_search)
- Specs expose `vector_store_binding` (`tenant_default` | `static` | `required`) and optional `vector_store_ids` plus `file_search_options`.
- Resolution precedence (in `InteractionContextBuilder._resolve_vector_store_ids`):
  1) Request override (`vector_store_ids`/`vector_store_id` on the chat request) if provided and exists.
  2) Agent-to-store binding from DB (`vector_store_service.get_agent_binding`).
  3) Spec config:
     - `static` → must supply `vector_store_ids` on the spec.
     - `required` → requires an existing “primary” store; errors if missing.
     - `tenant_default` (default) → uses primary store; can auto-create it when enabled.
- The resolved OpenAI store IDs are injected into `file_search` context so the FileSearch tool in the agent spec can run queries with those store IDs; per-agent `file_search_options` are passed through to the tool.

## Binding API
- Bind an agent to a store per tenant: `bind_agent_to_store(tenant_id, agent_key, vector_store_id)`.
- Retrieve or remove bindings: `get_agent_binding`, `unbind_agent_from_store`.
- Bindings are used automatically during file_search resolution before falling back to spec or tenant defaults.

## Store/File/Search flows
- Stores: create/list/get/delete, ensure primary store per tenant.
- Files: attach/list/get/delete OpenAI files in a store; chunking/attributes are forwarded to the OpenAI Vector Store API.
- Search: `search()` wraps the OpenAI Vector Store search with filters, max results, and ranking options; metadata is instrumented for observability.

## Quick checklist (using file_search in an agent)
- Set `vector_store_binding="tenant_default"` on the AgentSpec (preferred) or `static` with explicit IDs.
- Ensure the tenant has a primary store (auto-create enabled by default) or bind the agent to a store via bindings API.
- Provide `file_search_options` on the AgentSpec if you need filters/max results/ranking options.
- If callers need to override, allow `vector_store_ids` in the request; they take precedence over bindings/spec.
