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
        ("pyright:api-service", [python, "-m", "pyright", "--project", "api-service/pyrightconfig.json"]),
        ("pyright:starter-cli", [python, "-m", "pyright", "--project", "starter_cli/pyrightconfig.json"]),
        ("pyright:starter-contracts", [python, "-m", "pyright", "--project", "starter_contracts/pyrightconfig.json"]),
        ("mypy:api-service", [python, "-m", "mypy", "--config-file", "api-service/pyproject.toml", "api-service/src", "api-service/tests"]),
        ("mypy:starter-cli", [python, "-m", "mypy", "--config-file", "starter_cli/pyproject.toml", "starter_cli/src", "starter_cli/tests"]),
        ("mypy:starter-contracts", [python, "-m", "mypy", "--config-file", "starter_contracts/pyproject.toml", "starter_contracts/src", "starter_contracts/tests"]),
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
