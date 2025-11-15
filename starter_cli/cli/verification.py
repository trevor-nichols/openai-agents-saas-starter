from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class VerificationArtifact:
    provider: str
    identifier: str
    status: str  # e.g., passed/failed/skipped
    detail: str | None = None
    source: str | None = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def artifacts_to_dict(artifacts: Iterable[VerificationArtifact]) -> list[dict]:
    return [asdict(artifact) for artifact in artifacts]


def load_verification_artifacts(path: Path) -> list[VerificationArtifact]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    artifacts: list[VerificationArtifact] = []
    if isinstance(payload, list):
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            artifacts.append(
                VerificationArtifact(
                    provider=str(entry.get("provider", "")),
                    identifier=str(entry.get("identifier", "")),
                    status=str(entry.get("status", "")),
                    detail=entry.get("detail"),
                    source=entry.get("source"),
                    timestamp=str(entry.get("timestamp", "")),
                )
            )
    return artifacts


def save_verification_artifacts(path: Path, artifacts: Iterable[VerificationArtifact]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifacts_to_dict(artifacts), indent=2), encoding="utf-8")


def append_verification_artifact(path: Path, artifact: VerificationArtifact) -> None:
    existing = load_verification_artifacts(path)
    existing.append(artifact)
    save_verification_artifacts(path, existing)


__all__ = [
    "VerificationArtifact",
    "artifacts_to_dict",
    "load_verification_artifacts",
    "save_verification_artifacts",
    "append_verification_artifact",
]
