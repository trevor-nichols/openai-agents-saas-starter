from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn

# Ensure repo-local modules are importable when running from tools/.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "api-service" / "src"))
sys.path.insert(0, str(ROOT / "apps" / "api-service"))
sys.path.insert(0, str(ROOT))

from agents import set_tracing_disabled  # noqa: E402
from tests.utils.stub_agent_provider import build_stub_provider  # noqa: E402

import main  # noqa: E402

# Patch the OpenAI provider factory to return a deterministic stub provider.
main.build_openai_provider = lambda **_: build_stub_provider()


def create_app():
    return main.create_application()


def main_smoke() -> None:
    os.environ.setdefault("OPENAI_API_KEY", "dummy-smoke-key")
    set_tracing_disabled(True)
    host = os.getenv("SMOKE_HOST", "127.0.0.1")
    port = int(os.getenv("SMOKE_PORT", "8000"))
    log_level = os.getenv("SMOKE_LOG_LEVEL", "info")
    uvicorn.run(create_app(), host=host, port=port, log_level=log_level)


if __name__ == "__main__":
    main_smoke()
