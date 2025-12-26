from __future__ import annotations

import argparse

from starter_console.core import CLIContext
from starter_console.services.api.export import OpenApiExportConfig, export_openapi


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
    config = OpenApiExportConfig(
        output=args.output,
        enable_billing=args.enable_billing,
        enable_test_fixtures=args.enable_test_fixtures,
        title=args.title,
        version=args.version,
    )
    export_openapi(ctx, config)
    return 0


__all__ = ["register", "OpenApiExportConfig"]
