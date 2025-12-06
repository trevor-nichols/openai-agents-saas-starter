from __future__ import annotations

import subprocess
import sys
from typing import Sequence


def _run_command(label: str, command: Sequence[str]) -> int:
    print(f"\n[Typecheck] Running {label}: {' '.join(command)}", flush=True)
    result = subprocess.run(command)
    return result.returncode


def main() -> None:
    python = sys.executable
    commands = [
        ("pyright:api-service", [python, "-m", "pyright", "--project", "apps/api-service/pyrightconfig.json"]),
        ("pyright:starter-cli", [python, "-m", "pyright", "--project", "packages/starter_cli/pyrightconfig.json"]),
        ("pyright:starter-contracts", [python, "-m", "pyright", "--project", "packages/starter_contracts/pyrightconfig.json"]),
        ("mypy:api-service", [python, "-m", "mypy", "--config-file", "apps/api-service/pyproject.toml", "apps/api-service/src", "apps/api-service/tests"]),
        ("mypy:starter-cli", [python, "-m", "mypy", "--config-file", "packages/starter_cli/pyproject.toml", "packages/starter_cli/src", "packages/starter_cli/tests"]),
        ("mypy:starter-contracts", [python, "-m", "mypy", "--config-file", "packages/starter_contracts/pyproject.toml", "packages/starter_contracts/src", "packages/starter_contracts/tests"]),
    ]

    failures: list[str] = []
    for label, command in commands:
        if _run_command(label, command) != 0:
            failures.append(label)

    if failures:
        joined = ", ".join(failures)
        print(f"\nType checking failed ({joined}).", file=sys.stderr)
        sys.exit(1)

    print("\nType checking succeeded.")


if __name__ == "__main__":
    main()
