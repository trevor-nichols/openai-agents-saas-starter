# Milestone: Workflow Parallelization (OpenAI Agents SDK)

Goal: Add stage-based workflow orchestration with parallel fan-out/reduce while staying aligned with the OpenAI Agents SDK. Deliver clean, auditable implementation that showcases professional architecture and tracing.

## Status Legend
- [ ] Not started
- [~] In progress
- [x] Done

## Plan & Checkpoints

1. **Spec model extension** – Add `WorkflowStage` (mode: sequential/parallel, reducer hook) and extend `WorkflowSpec` to accept stages while preserving backward compatibility with existing `steps`. Update registry validation. Status: [x]
2. **Runner (sync) upgrade** – Wrap workflow run in `agents.trace`; execute sequential stages as today; execute parallel stages via `asyncio.gather`, record branch metadata, apply reducer to produce next input. Status: [x]
3. **Runner (streaming) upgrade** – Multiplex branch streams with tagged events (`parallel_group`, `branch_index`), aggregate terminal reducer output, preserve SSE ordering guarantees. Status: [x]
4. **Persistence & API schema** – Add columns to workflow_run_steps (`stage_name`, `parallel_group`, `branch_index`), expose in response/stream schemas, update repositories/models/migration. Status: [x]
5. **Sample parallel workflow spec** – Add exemplar spec (e.g., parallel translation vote) to demonstrate declarative usage and reducer hook. Status: [x]
6. **Tests** – Unit coverage for sequential + parallel stages (sync/stream), reducer errors, guard/map interplay, API contract updates. Status: [x]
7. **Docs** – Update `docs/openai-agents-sdk` integration notes and `AGENTS.md`/workflows section with the new stage model and examples. Status: [x]
8. **Sign-off & cleanup** – Ensure lint/typecheck pass (`hatch run lint`, `hatch run typecheck`), review tracker, and mark steps complete. Status: [x]

## Notes
- Keep implementation aligned with Agents SDK (use `Runner.run` / `Runner.run_streamed`, `trace`).
- Maintain deterministic reducers; fail fast on branch errors.
- Backward compatible: existing linear workflows run unchanged.
