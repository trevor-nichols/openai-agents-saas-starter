from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext, CLIError


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    api_parser = subparsers.add_parser("api", help="Backend API helpers.")
    api_subparsers = api_parser.add_subparsers(dest="api_command")

    openapi_parser = api_subparsers.add_parser(
        "export-openapi",
        help="Export the FastAPI OpenAPI schema with optional feature flags.",
    )
    openapi_parser.add_argument(
        "--output",
        required=True,
        help=(
            "Destination path for the JSON schema "
            "(e.g., apps/api-service/.artifacts/openapi.json)."
        ),
    )
    openapi_parser.add_argument(
        "--enable-billing",
        action="store_true",
        help="Set ENABLE_BILLING=true while generating the schema.",
    )
    openapi_parser.add_argument(
        "--enable-test-fixtures",
        action="store_true",
        help="Set USE_TEST_FIXTURES=true while generating the schema.",
    )
    openapi_parser.add_argument(
        "--title",
        help="Override OpenAPI info.title (defaults to app info.title).",
    )
    openapi_parser.add_argument(
        "--version",
        help="Override OpenAPI info.version (defaults to app info.version).",
    )
    openapi_parser.set_defaults(handler=handle_export_openapi)


def handle_export_openapi(args: argparse.Namespace, ctx: CLIContext) -> int:
    exporter = OpenAPIExporter(
        ctx=ctx,
        output=args.output,
        enable_billing=args.enable_billing,
        enable_test_fixtures=args.enable_test_fixtures,
        title=args.title,
        version=args.version,
    )
    exporter.run()
    return 0


class OpenAPIExporter:
    def __init__(
        self,
        *,
        ctx: CLIContext,
        output: str,
        enable_billing: bool,
        enable_test_fixtures: bool,
        title: str | None,
        version: str | None,
    ) -> None:
        self.ctx = ctx
        self.output = Path(output)
        self.enable_billing = enable_billing
        self.enable_test_fixtures = enable_test_fixtures
        self.title = title
        self.version = version

    def run(self) -> None:
        repo_root = self.ctx.project_root
        api_service_dir = repo_root / "apps" / "api-service"
        if not api_service_dir.exists():
            raise CLIError("apps/api-service directory not found; run from the repository root.")

        # Prefer the src/ layout used by the current repo; fall back to legacy app/.
        app_dir = api_service_dir / "src" / "app"
        main_path = api_service_dir / "src" / "main.py"
        if not app_dir.exists():
            app_dir = api_service_dir / "app"
            main_path = api_service_dir / "main.py"

        os.chdir(api_service_dir)
        sys.path.insert(0, str(app_dir.parent))  # e.g., apps/api-service/src
        sys.path.insert(1, str(api_service_dir))
        sys.path.insert(2, str(repo_root))
        self._purge_existing_app_modules()

        if self.enable_billing:
            os.environ["ENABLE_BILLING"] = "true"
        if self.enable_test_fixtures:
            os.environ["USE_TEST_FIXTURES"] = "true"

        self._load_module("app", app_dir / "__init__.py")
        main_module = self._load_module("app.main", main_path)

        create_application = getattr(main_module, "create_application", None)
        if create_application is None:
            raise CLIError("create_application not found in apps/api-service/src/main.py")

        app = create_application()
        app.openapi_schema = None
        schema: dict[str, Any] = app.openapi()

        if self.title:
            schema.setdefault("info", {})["title"] = self.title
        if self.version:
            schema.setdefault("info", {})["version"] = self.version

        destination = self.output
        if not destination.is_absolute():
            destination = (repo_root / destination).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        console.success(f"OpenAPI schema written to {destination}", topic="api")

    @staticmethod
    def _load_module(name: str, path: Path) -> Any:
        spec = importlib.util.spec_from_file_location(
            name,
            path,
            submodule_search_locations=[str(path.parent)],
        )
        if spec is None or spec.loader is None:
            raise CLIError(f"Failed to build import spec for {name}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def _purge_existing_app_modules() -> None:
        for key in list(sys.modules.keys()):
            if key == "app" or key.startswith("app."):
                sys.modules.pop(key, None)


__all__ = ["register"]
