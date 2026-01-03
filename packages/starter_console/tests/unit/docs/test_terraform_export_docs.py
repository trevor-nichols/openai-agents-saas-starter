from __future__ import annotations

import json
import re
from pathlib import Path


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "docs").exists() and (parent / "packages").exists():
            return parent
    raise RuntimeError("Repo root not found.")


def test_terraform_export_doc_api_secrets_json() -> None:
    doc_path = _repo_root() / "docs" / "ops" / "terraform-export.md"
    contents = doc_path.read_text(encoding="utf-8")
    matches = re.findall(r"--var api_secrets='([^']+)'", contents)
    assert len(matches) == 1, "Expected a single api_secrets example in terraform-export.md"
    payload = json.loads(matches[0])
    assert payload.get("DATABASE_URL")
    assert payload.get("REDIS_URL")
