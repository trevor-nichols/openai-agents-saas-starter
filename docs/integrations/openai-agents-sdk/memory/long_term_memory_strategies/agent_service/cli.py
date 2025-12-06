from __future__ import annotations

import asyncio
import json
import sys
from typing import Any, Dict

from .commands import handle_command
from .stores import reset_data_stores


async def _process_stream() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            payload: Dict[str, Any] = json.loads(line)
            request_id = payload.get("id")
            result = await handle_command(payload)
            envelope = {"id": request_id, "status": "ok", "result": result}
        except Exception as exc:  # pragma: no cover - defensive logging
            envelope = {
                "id": payload.get("id") if "payload" in locals() else None,
                "status": "error",
                "error": str(exc),
            }
        sys.stdout.write(json.dumps(envelope) + "\n")
        sys.stdout.flush()


def main() -> None:
    reset_data_stores()
    try:
        asyncio.run(_process_stream())
    except KeyboardInterrupt:  # pragma: no cover - allow clean exit
        pass
