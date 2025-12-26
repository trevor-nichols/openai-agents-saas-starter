from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export the FastAPI OpenAPI schema.")
    parser.add_argument("--output", required=True, help="Destination path for the JSON schema.")
    parser.add_argument("--repo-root", help="Repository root path for resolving relative output.")
    parser.add_argument("--enable-billing", action="store_true")
    parser.add_argument("--enable-test-fixtures", action="store_true")
    parser.add_argument("--title", help="Override OpenAPI info.title")
    parser.add_argument("--version", help="Override OpenAPI info.version")
    args = parser.parse_args(argv)

    try:
        destination = export_openapi(
            output=args.output,
            repo_root=args.repo_root,
            enable_billing=args.enable_billing,
            enable_test_fixtures=args.enable_test_fixtures,
            title=args.title,
            version=args.version,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"output": str(destination)}))
    return 0


def export_openapi(
    *,
    output: str,
    repo_root: str | None,
    enable_billing: bool,
    enable_test_fixtures: bool,
    title: str | None,
    version: str | None,
) -> Path:
    repo_path = _resolve_repo_root(repo_root)
    api_service_dir = repo_path / "apps" / "api-service"
    app_dir = api_service_dir / "src" / "app"
    main_path = api_service_dir / "src" / "main.py"
    if not app_dir.exists() or not main_path.exists():
        raise RuntimeError("apps/api-service/src layout not found; expected src/app + src/main.py.")

    sys.path.insert(0, str(api_service_dir / "src"))

    if enable_billing:
        os.environ["ENABLE_BILLING"] = "true"
    if enable_test_fixtures:
        os.environ["USE_TEST_FIXTURES"] = "true"

    from main import create_application

    app = create_application()
    app.openapi_schema = None
    schema: dict[str, Any] = app.openapi()

    if title:
        schema.setdefault("info", {})["title"] = title
    if version:
        schema.setdefault("info", {})["version"] = version

    destination = Path(output)
    if not destination.is_absolute():
        destination = (repo_path / destination).resolve()
    try:
        destination.relative_to(repo_path)
    except ValueError:
        print(
            (
                f"WARNING: Output path {destination} is outside the repository root ({repo_path}). "
                "Paths are repo-root relative; drop any leading '../' when running this command."
            ),
            file=sys.stderr,
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    return destination


def _resolve_repo_root(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    return Path(__file__).resolve().parents[3]


if __name__ == "__main__":
    raise SystemExit(main())
