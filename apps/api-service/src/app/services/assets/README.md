# Asset catalog service

Tracks generated assets (images/files) separately from raw storage objects so the app can offer
“Images” and “Files” listings with links back to their source conversations/messages.

## What it owns
- Records for generated outputs in `agent_assets` (FK → `storage_objects`).
- Metadata linking assets to conversations, messages, tool calls, and responses.
- Asset-level list/get/delete and download URL operations.

## Key pieces
- `AssetService` (`service.py`): orchestration layer for asset records + storage operations.
- `SqlAlchemyAssetRepository` (`infrastructure/persistence/assets/repository.py`): Postgres CRUD and filtered listing.
- Ingestion: `AttachmentService` writes asset records after tool outputs are persisted.

## API surface
- `GET /api/v1/assets` list with filters (type, tool, conversation, agent, MIME prefix, date range).
- `GET /api/v1/assets/{id}` detail.
- `GET /api/v1/assets/{id}/download-url` presigned download.
- `DELETE /api/v1/assets/{id}` delete (also removes underlying storage object).

## Notes
- Asset deletion is implemented by deleting the storage object and soft-deleting the asset record.
- Message linkage is applied after the assistant message is persisted.
