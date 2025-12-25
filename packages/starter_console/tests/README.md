Starter Console Tests

Structure
- Mirror `src/starter_console/**` under `tests/unit/**` so the test location tells you the layer and domain.
- Keep command behavior in `tests/unit/commands/**`, service logic in `tests/unit/services/**`,
  workflow orchestration in `tests/unit/workflows/**`, and UI/Textual tests in `tests/unit/ui/**`.
- Shared helpers belong in `tests/unit/support/**`.

Architecture checks
- Cross-cutting import boundary tests live in `tests/architecture/**`.

Guidelines
- Prefer small, focused tests; avoid cross-layer coupling.
- If a test exercises multiple layers, choose the highest-level module it targets and document intent.
