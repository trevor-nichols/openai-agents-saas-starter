# BE-012 – Tenant Attribution for Conversations

## Summary

- FastAPI conversation endpoints now refuse requests that lack a tenant UUID. The chat/conversation routers resolve `tenant_id` from JWT claims or the `X-Tenant-Id` header and map it into the agent service context.
- `ConversationMetadata` and the `ConversationRepository` contract require `tenant_id` so persistence never falls back to a shared "default" tenant. The Postgres repository enforces tenant scoping on every query and raises when an ID mismatch occurs.
- `ConversationService` APIs are tenant-aware (including search), and the built-in `search_conversations` tool now scopes itself via a request-local actor context.
- Starter Console docs call out the need to capture real tenant UUIDs after seeding users so operators know how to satisfy the new requirement in CI and staging.

## Status

- [x] Runtime enforcement shipped (FastAPI + Postgres repository)
- [x] Developer tooling and docs updated (`starter_console/README.md`)
- [x] Follow-up automation: setup wizard surfaces the seeded tenant UUID after env save (2025-11-16)

## Validation

- `hatch run lint`
- `hatch run typecheck`
- `pytest api-service/tests/contract/test_agents_api.py`
- `pytest api-service/tests/integration/test_postgres_migrations.py::test_repository_roundtrip`

## Open Questions

- Consider backfill/cleanup scripts for any existing `agent_conversations` rows tied to the deprecated default tenant slug.
