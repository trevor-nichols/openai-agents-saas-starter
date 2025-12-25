from __future__ import annotations

from dataclasses import dataclass

from starter_cli.core import CLIContext, CLIError
from starter_cli.services.infra.backend_scripts import extract_json_payload, run_backend_script


@dataclass(frozen=True, slots=True)
class OpenApiExportConfig:
    output: str
    enable_billing: bool
    enable_test_fixtures: bool
    title: str | None
    version: str | None


class OpenAPIExporter:
    def __init__(self, *, ctx: CLIContext, config: OpenApiExportConfig) -> None:
        self.ctx = ctx
        self.console = ctx.console
        self.config = config

    def run(self) -> None:
        args = [
            "--output",
            self.config.output,
            "--repo-root",
            str(self.ctx.project_root),
        ]
        if self.config.enable_billing:
            args.append("--enable-billing")
        if self.config.enable_test_fixtures:
            args.append("--enable-test-fixtures")
        if self.config.title:
            args.extend(["--title", self.config.title])
        if self.config.version:
            args.extend(["--version", self.config.version])

        result = run_backend_script(
            project_root=self.ctx.project_root,
            script_name="export_openapi.py",
            args=args,
            ctx=self.ctx,
        )
        if result.stdout:
            payload = extract_json_payload(result.stdout, required_keys=("output",))
            output_path = payload.get("output")
            if output_path:
                self.console.info(f"OpenAPI schema written to {output_path}", topic="api")
        if result.stderr:
            for line in result.stderr.splitlines():
                if line.strip():
                    self.console.warn(line, topic="api")
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "Unknown error."
            raise CLIError(f"OpenAPI export failed: {detail}")


def export_openapi(ctx: CLIContext, config: OpenApiExportConfig) -> None:
    exporter = OpenAPIExporter(ctx=ctx, config=config)
    exporter.run()


__all__ = ["OpenAPIExporter", "OpenApiExportConfig", "export_openapi"]
