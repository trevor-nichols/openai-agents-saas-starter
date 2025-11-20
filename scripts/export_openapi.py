"""
Export the FastAPI OpenAPI schema to a JSON file with optional feature flags.

Usage examples (from repo root):
  python scripts/export_openapi.py --output api-service/.artifacts/openapi-billing.json --enable-billing
  python scripts/export_openapi.py --output api-service/.artifacts/openapi-billing-fixtures.json --enable-billing --enable-test-fixtures
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
import importlib.util


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export OpenAPI schema from FastAPI app.")
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the OpenAPI JSON (e.g., api-service/.artifacts/openapi-billing.json)",
    )
    parser.add_argument(
        "--enable-billing",
        action="store_true",
        help="Set ENABLE_BILLING=true while generating the schema.",
    )
    parser.add_argument(
        "--enable-test-fixtures",
        action="store_true",
        help="Set USE_TEST_FIXTURES=true while generating the schema.",
    )
    parser.add_argument(
        "--title",
        help="Override OpenAPI info.title (defaults to app info.title).",
    )
    parser.add_argument(
        "--version",
        help="Override OpenAPI info.version (defaults to app info.version).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    api_service_dir = repo_root / "api-service"
    os.chdir(api_service_dir)
    sys.path.insert(0, str(api_service_dir))
    sys.path.insert(1, str(repo_root))  # allow relative imports that expect repo root
    # Remove any previously imported conflicting "app" modules (common when other projects are installed)
    for key in list(sys.modules.keys()):
        if key == "app" or key.startswith("app."):
            sys.modules.pop(key, None)

    # Lazily load our local app package via importlib to avoid name clashes with other
    # installed packages named "app".
    app_pkg_path = api_service_dir / "app" / "__init__.py"
    app_spec = importlib.util.spec_from_file_location(
        "app",
        app_pkg_path,
        submodule_search_locations=[str(app_pkg_path.parent)],
    )
    if app_spec is None or app_spec.loader is None:
        raise RuntimeError("Failed to build import spec for local 'app' package.")
    app_module = importlib.util.module_from_spec(app_spec)
    sys.modules["app"] = app_module
    app_spec.loader.exec_module(app_module)

    # Apply env overrides before importing the app so get_settings() sees them.
    if args.enable_billing:
        os.environ["ENABLE_BILLING"] = "true"
    if args.enable_test_fixtures:
        os.environ["USE_TEST_FIXTURES"] = "true"

    # Load app.main using the patched package
    main_path = api_service_dir / "main.py"
    main_spec = importlib.util.spec_from_file_location("app.main", main_path)
    if main_spec is None or main_spec.loader is None:
        raise RuntimeError("Failed to build import spec for 'app.main'.")
    main_module = importlib.util.module_from_spec(main_spec)
    sys.modules["app.main"] = main_module
    main_spec.loader.exec_module(main_module)

    create_application = getattr(main_module, "create_application")
    app = create_application()

    # Ensure a fresh schema is generated
    app.openapi_schema = None
    schema: dict[str, Any] = app.openapi()

    if args.title:
        schema.setdefault("info", {})["title"] = args.title
    if args.version:
        schema.setdefault("info", {})["version"] = args.version

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = (repo_root / output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"✅ OpenAPI schema written to {output_path}")


if __name__ == "__main__":
    main()
