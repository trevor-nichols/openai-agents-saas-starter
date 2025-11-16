# Milestone: Backend Typecheck Convergence

## Objective
- Drive the unified `hatch run typecheck` (Pyright + Mypy) command to zero errors and keep it there with CI gating.
- Eliminate stale `# type: ignore` usage, tighten generics on cache/persistence layers, and fix real typing bugs (bytes/str, Literal checks, mis-modeled SDK calls).
- Establish lightweight documentation + guardrails so contributors know how to keep the suite passing.

## Scope / Non-Goals
- **In scope:** Anything under `anything-agents`, `starter_cli`, and `starter_shared` that executes during `hatch run typecheck`.
- **Out of scope (for now):** Frontend TypeScript checks (`pnpm type-check`), runtime refactors unrelated to typing, or relaxing strictness flags.

## Current Status (2025-11-16)
- Command: `hatch run typecheck`
- Result: **0 errors (Pyright + Mypy clean)** as of `/tmp/mypy.log`

### Error Buckets
| Category | Count | Examples |
|----------|-------|----------|
| Missing type params (`type-arg`) | 0 | – |
| Stale/unused ignores (`unused-ignore`) | 0 | – |
| Argument/type mismatches (`arg-type`, `assignment`, `attr-defined`) | 0 | – |
| Invalid typing patterns (`valid-type`, Literal comparison, union-attr) | 0 | – |
| Missing annotations (`var-annotated`) | 0 | – |
| Other (dict item shape, coroutine override, etc.) | 0 | – |

Total errors: 0 (Pyright + Mypy).

## Work Breakdown

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| TC-001 | Hygiene | Remove/justify `# type: ignore` occurrences. Replace with explicit typing or targeted suppressions (`type: ignore[arg-type]`) only when unavoidable. | – | In Progress |
| TC-002 | Generics | Add concrete type params for `dict`, `Redis`, `CursorResult`, `TypeDecorator`, and helper DTOs. Extract shared aliases where needed. | – | Not Started |
| TC-003 | Real Defects | Fix bytes/str mismatches in `core.security` and dependent tests, ensure literal enums match, address incorrect assumptions in service/account flows. | – | Not Started |
| TC-004 | Test Fixtures | Annotate pytest fixtures/utilities (`tests/conftest.py`, billing/email/password tests) so overrides match repository interfaces. | – | Not Started |
| TC-005 | CLI Typings | Cleanup `starter_cli` (common auth, verification, stripe commands) to use precise `TypedDict`/dataclasses for prompts and azure credential lists. | – | Not Started |
| TC-006 | Enforcement | Add CI job (or extend existing) to run `hatch run typecheck`, update AGENTS.md/README with expectations, and document how to regenerate counts. | – | Not Started |

## Execution Notes
- Prioritize TC-001 + TC-002 first to uncover any hidden issues before tackling logic changes.
- Treat Redis repositories as `Redis[str, str]` (or stricter) consistently; consider a `type RedisClient = Redis[str, str]` alias under `app.infrastructure.security.types`.
- When removing ignores reveals third-party typing gaps, prefer local Protocols/stubs over reintroducing blanket ignores.
- Track progress by re-running `hatch run typecheck` after each batch, updating the bucket counts in this file.

## Next Checkpoints
1. **Checkpoint A (<= 40 errors):** Finish TC-001 + TC-002 sweeps, update bucket table with new counts.
2. **Checkpoint B (<= 10 errors):** Resolve bytes/str + literal mismatches, ensure remaining issues have owners.
3. **Completion:** Zero errors, CI wired, add note to AGENTS.md summarizing the guardrail.

Log updates here (dates, remaining counts, notable blockers) as you progress.

- **2025-11-16:** Finished Redis/client alias sweep, tightened service + CLI typings, annotated fixtures/tests, and resolved the final signup trial calculation issue. `hatch run typecheck` now passes (0 errors).
