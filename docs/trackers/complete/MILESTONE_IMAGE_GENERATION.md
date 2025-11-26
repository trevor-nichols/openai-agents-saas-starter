# Milestone: Image Generation Tool Enablement (OpenAI Agents SDK)

Status: Not Started
Owner: Platform Foundations
Goal: Add first-class image generation support (OpenAI image_generation tool) with durable storage, conversation attachment semantics, and clean DX for downstream developers.
Status: Completed (backend + CLI) 2025-11-26

## Phases & Tasks

### Phase 1 — Design & Schema Foundations
- Capture requirements and defaults from SDK docs (size/quality/format/background/compression/partial_images/input_fidelity, multi-turn support, streaming partials). **Status: Completed**
- Add settings defaults/limits in `Settings` (ai.py): output size/quality/format/background/compression, max decoded MB, allowed formats. **Status: Completed**
- Migration: add `attachments` JSONB column to `agent_messages` (nullable, default []), keep text content for search; no base64 in DB. **Status: Completed**

### Phase 2 — Tool Registration & Config
- Register `ImageGenerationTool` in `initialize_tools` when `OPENAI_API_KEY` present; add category metadata. **Status: Completed**
- Extend `AgentSpec.tool_configs` handling to read `image_generation` config (validate enums; merge with settings defaults). **Status: Completed**
- Add doc snippet to agent cookbook on enabling the tool via `tool_keys` and per-agent configs. **Status: Completed**

### Phase 3 — Runtime Capture & Storage
- Enhance `OpenAIAgentRuntime.run` / `run_stream` to surface image tool outputs (run items + streaming partials) and propagate tool_call metadata. **Status: Completed**
- Implement `ImageIngestor`: decode base64, size/mime guard, checksum, store bytes via `StorageService.put_object`, persist metadata (tenant, conversation, agent_key, user_id, tool_call_id, response_id, prompt/revised_prompt, format/quality/background, size_bytes). **Status: Completed**
- Wire ingestion from `AgentService` (sync + stream): detect image tool outputs, persist to storage, attach references to assistant message and stream events; fallback to transient base64 only if storage fails (logged). **Status: Completed**

### Phase 4 — API & Conversation Model
- Extend conversation domain & API schemas (`ConversationMessage`, `AgentChatResponse`, `StreamingChatEvent`) to carry `attachments` (storage object id, filename, mime, size, presigned_url, tool_call_id). **Status: Completed**
- Update Postgres repository read/write to preserve attachments in `content` while keeping `text` for search TSV; expose attachments in SSE and REST responses. **Status: Completed**
- Add presigned download plumbing via `StorageService` for response/stream payloads (short TTL). **Status: Completed**

### Phase 5 — DX, Tests, Ops
- Update CLI/.env guidance to set image defaults + storage provider; add tracker note. **Status: Not Started**
- Tests: unit (ImageIngestor guards, tool_config validation), repo round-trip with attachments, service chat + chat_stream happy paths, SSE payload assertions. **Status: Not Started**
- Observability: log key events (tool_call_id, object_id), ensure presigned URLs redacted; metrics hook TBD (out of scope unless quick). **Status: Not Started**

## Definition of Done
- ImageGenerationTool registered; agents can opt in via `tool_keys` with validated configs.
- Images never stored as base64 in Postgres; persisted to configured storage (MinIO/GCS) with metadata linking tenant/user/agent/conversation.
- Chat and streaming APIs return attachment metadata + presigned URLs; text content remains searchable.
- Tests cover ingest guards and message attachment round-trips; CI stays green (hatch lint/typecheck, pnpm lint/type-check).
- Docs/CLI updated so a new developer can enable image generation without spelunking the code.
