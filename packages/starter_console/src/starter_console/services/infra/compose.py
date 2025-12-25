from __future__ import annotations

import shutil
import subprocess


def detect_compose_command() -> tuple[str, ...] | None:
    docker = shutil.which("docker")
    if not docker:
        return None
    try:
        subprocess.run(
            [docker, "compose", "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return (docker, "compose")


__all__ = ["detect_compose_command"]
