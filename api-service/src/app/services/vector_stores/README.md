# Vector Stores services

This package houses all vector-store related services:

- `service.py` — coordinates OpenAI vector store CRUD/search and local persistence.
- `limits.py` — plan-aware limit resolver (billing optional).
- `sync_worker.py` — optional background worker to refresh status/expiry.

Keep domain-specific helpers here to mirror other service domains (billing/, signup/, etc.).
