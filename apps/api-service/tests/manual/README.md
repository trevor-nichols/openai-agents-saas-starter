# Manual streaming tests

Purpose: operator-only checks that hit a running stack with real models/tools. These are **opt-in** and never run in CI.

Current coverage
- `test_web_search_manual.py`: streams `/api/v1/chat/stream` with `researcher`; checks HTTP 200, structured SSE, `web_search_call` completion, citations present/well-formed, and text references cited URL.
- `test_code_interpreter_manual.py`: streams with `code_assistant`; checks HTTP 200, structured SSE, `code_interpreter_call` completion, outputs captured, and assistant text mentions the numeric result.
- `test_file_search_manual.py`: streams with `researcher` + file search. By default it uploads `apps/api-service/tests/utils/test.pdf` to OpenAI, ensures/creates the primary vector store, attaches the file (polling to completed), then runs. You can override the file via `FILE_SEARCH_LOCAL_FILE`. Checks HTTP 200, structured SSE, `file_search_call` completion, file citations present, and citation references the selected file.
- `test_image_generation_manual.py`: streams with `researcher` to generate an image; asserts streaming structure, `image_generation_call` completion, attachment presence, and non-empty assistant text. Uses a fast/stable prompt (“stick figure line drawing”) and defaults `MANUAL_TIMEOUT` to 180s to avoid slow-generation flakes.
- `test_function_tool_manual.py`: streams with `triage`; checks `tool.status` for a function tool call, `tool.arguments.done`, `tool.output`, and terminal invariants.
- `test_refusal_manual.py`: streams with `triage`; attempts to trigger a refusal and validates `refusal.*` events + terminal `final.status="refused"` (skips if the model does not refuse for the prompt).
- `test_reasoning_summary_manual.py`: streams with `triage`; attempts to observe `reasoning_summary.delta` events + terminal `final.reasoning_summary_text` (skips if the model does not emit reasoning summary for the run).
- `test_workflow_manual.py`: streams `/api/v1/workflows/analysis_code/run-stream`; asserts HTTP 200, workflow metadata present, both steps (`analysis`, `code`) observed, terminal event, and non-empty assistant text.

Why manual: Requires live OpenAI web search and your local auth setup; we keep it outside CI to avoid network/external dependencies.

How to run
```
cd apps/api-service
hatch run pytest tests/manual/test_web_search_manual.py \
  -m manual --run-manual --asyncio-mode=auto
```
Handy one-liner that loads `.env.local` (avoids skips for missing DEV_USER_PASSWORD/API keys):
```
starter-console util run-with-env apps/api-service/.env.local -- \
  bash -lc "cd apps/api-service && hatch run pytest tests/manual/test_web_search_manual.py -m manual --run-manual --asyncio-mode=auto"
```

Recording fixtures for CI playback
- Each manual test can write the streamed SSE events to NDJSON when `MANUAL_RECORD_STREAM_TO` is set. Example (uses the default fixture path when the env is set to an empty string):
  ```
  MANUAL_RECORD_STREAM_TO= \
  hatch run pytest tests/manual/test_web_search_manual.py -m manual --run-manual --asyncio-mode=auto
  ```
- The default destinations live under `docs/contracts/public-sse-streaming/examples/`:
  - `chat-web-search.ndjson`
  - `chat-code-interpreter.ndjson`
  - `chat-file-search.ndjson`
  - `chat-image-generation-partials.ndjson`
  - `chat-function-tool.ndjson`
  - `chat-refusal.ndjson`
  - `chat-reasoning-summary.ndjson`
  - `workflow-analysis-code.ndjson`
- After recording, the contract playback tests (`tests/contract/streams/test_stream_goldens.py`) validate the fixture deterministically in CI (no external network calls).

Current fixtures: NDJSONs can be refreshed via the manual tests and validated deterministically in CI via `tests/contract/streams/test_stream_goldens.py`.

Prereqs for file search manual test
- Provide `OPENAI_API_KEY` so the test can upload `tests/utils/test.pdf` to OpenAI Files. Without it the test will skip.
- (Optional) Override the file with `FILE_SEARCH_LOCAL_FILE=/path/to/file.pdf`.

Auth flow
- If `MANUAL_ACCESS_TOKEN` and `MANUAL_TENANT_ID` are set, those are used.
- Otherwise the test uses `DEV_USER_PASSWORD` (email defaults to `dev@example.com`). If it is not set, the test skips (no prompt).

Base URL resolution
- Uses `API_BASE_URL` if set; otherwise `http://localhost:{PORT or 8000}`.

Notes
- Keep these tests deterministic: prompts explicitly instruct the agent to perform web search before answering.
- Because they hit live services, treat them as smoke/validation checks rather than CI gatekeepers.
