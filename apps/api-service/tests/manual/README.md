# Manual streaming tests

Purpose: operator-only checks that hit a running stack with real models/tools. These are **opt-in** and never run in CI.

Current coverage
- `test_web_search_manual.py`: streams `/api/v1/chat/stream` with `researcher`; checks HTTP 200, structured SSE, `web_search_call` completion, citations present/well-formed, and text references cited URL.
- `test_code_interpreter_manual.py`: streams with `code_assistant`; checks HTTP 200, structured SSE, `code_interpreter_call` completion, outputs captured, and assistant text mentions the numeric result.

Why manual: Requires live OpenAI web search and your local auth setup; we keep it outside CI to avoid network/external dependencies.

How to run
```
cd apps/api-service
hatch run pytest tests/manual/test_web_search_manual.py \
  -m manual --run-manual --asyncio-mode=auto
```

Auth flow
- If `MANUAL_ACCESS_TOKEN` and `MANUAL_TENANT_ID` are set, those are used.
- Otherwise the test prompts once for the dev user password (email defaults to `dev@example.com`). Set `DEV_USER_PASSWORD` in your shell to avoid the prompt.

Base URL resolution
- Uses `NEXT_PUBLIC_API_URL` if set; otherwise `http://localhost:{PORT or 8000}`.

Notes
- Keep these tests deterministic: prompts explicitly instruct the agent to perform web search before answering.
- Because they hit live services, treat them as smoke/validation checks rather than CI gatekeepers.
