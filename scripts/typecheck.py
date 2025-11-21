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
        ("pyright", [python, "-m", "pyright"]),
        (
            "mypy",
            [
                python,
                "-m",
                "mypy",
                "api-service",
                "starter_cli",
                "starter_contracts",
            ],
        ),
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
