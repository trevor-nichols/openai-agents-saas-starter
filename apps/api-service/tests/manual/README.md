# Manual streaming tests

Purpose: operator-only checks that hit a running stack with real models/tools. These are **opt-in** and never run in CI.

Current coverage
- `test_web_search_manual.py`: streams `/api/v1/chat/stream` with `researcher`; checks HTTP 200, structured SSE, `web_search_call` completion, citations present/well-formed, and text references cited URL.
- `test_code_interpreter_manual.py`: streams with `code_assistant`; checks HTTP 200, structured SSE, `code_interpreter_call` completion, outputs captured, and assistant text mentions the numeric result.
- `test_file_search_manual.py`: streams with `researcher` + file search. By default it uploads `apps/api-service/tests/utils/test.pdf` to OpenAI, ensures/creates the primary vector store, attaches the file (polling to completed), then runs. You can override the file via `FILE_SEARCH_LOCAL_FILE`. Checks HTTP 200, structured SSE, `file_search_call` completion, file citations present, and citation references the selected file.

Why manual: Requires live OpenAI web search and your local auth setup; we keep it outside CI to avoid network/external dependencies.

How to run
```
cd apps/api-service
hatch run pytest tests/manual/test_web_search_manual.py \
  -m manual --run-manual --asyncio-mode=auto
```
Handy one-liner that loads `.env.local` (avoids skips for missing DEV_USER_PASSWORD/API keys):
```
python -m starter_cli.app util run-with-env apps/api-service/.env.local -- \
  bash -lc "cd apps/api-service && hatch run pytest tests/manual/test_web_search_manual.py -m manual --run-manual --asyncio-mode=auto"
```

Prereqs for file search manual test
- Provide `OPENAI_API_KEY` so the test can upload `tests/utils/test.pdf` to OpenAI Files. Without it the test will skip.
- (Optional) Override the file with `FILE_SEARCH_LOCAL_FILE=/path/to/file.pdf`.

Auth flow
- If `MANUAL_ACCESS_TOKEN` and `MANUAL_TENANT_ID` are set, those are used.
- Otherwise the test uses `DEV_USER_PASSWORD` (email defaults to `dev@example.com`). If it is not set, the test skips (no prompt).

Base URL resolution
- Uses `NEXT_PUBLIC_API_URL` if set; otherwise `http://localhost:{PORT or 8000}`.

Notes
- Keep these tests deterministic: prompts explicitly instruct the agent to perform web search before answering.
- Because they hit live services, treat them as smoke/validation checks rather than CI gatekeepers.
