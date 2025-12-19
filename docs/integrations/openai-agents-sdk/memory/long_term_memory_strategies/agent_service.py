"""NDJSON bridge for running OpenAI Agents with mocked tools.

This module exposes a tiny stdin/stdout protocol so the Next.js backend can
drive the OpenAI Agents SDK without embedding Python directly in the Node

Usage (from Node):
  echo '{"id": 1, "type": "run", ...}' | python agent_service.py

All tool backends are mocked in-memory and resettable via the `reset` command.
"""

from __future__ import annotations

from agent_service.cli import main

if __name__ == "__main__":
    main()
