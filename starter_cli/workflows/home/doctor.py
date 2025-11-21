from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext
from starter_cli.core.constants import PROJECT_ROOT, SAFE_ENVIRONMENTS
from starter_cli.core.status_models import ProbeResult, ProbeState, ServiceStatus
from starter_cli.workflows.home.probes import util
from starter_cli.workflows.home.probes.api import api_probe
from starter_cli.workflows.home.probes.db import db_probe
from starter_cli.workflows.home.probes.env import env_coverage_probe
from starter_cli.workflows.home.probes.frontend import frontend_probe
from starter_cli.workflows.home.probes.migrations import migrations_probe
from starter_cli.workflows.home.probes.ports import ports_probe
from starter_cli.workflows.home.probes.redis import redis_probe
from starter_cli.workflows.home.probes.stripe import stripe_probe
from starter_cli.workflows.home.probes.vault import vault_probe

DEFAULT_JSON_REPORT = PROJECT_ROOT / "var" / "reports" / "operator-dashboard.json"
DEFAULT_MD_REPORT = PROJECT_ROOT / "var" / "reports" / "operator-dashboard.md"


class DoctorRunner:
    def __init__(self, ctx: CLIContext, *, profile: str, strict: bool) -> None:
        self.ctx = ctx
        self.profile = profile
        self.strict = strict
        self.warn_only = (profile.lower() in SAFE_ENVIRONMENTS) and not strict

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, *, json_path: Path | None = None, markdown_path: Path | None = None) -> int:
        probes, services, summary = self.collect()
        self._print_console(summary, probes, services)
        json_out = json_path or DEFAULT_JSON_REPORT
        md_out = markdown_path or DEFAULT_MD_REPORT
        self._write_json(json_out, probes, services, summary)
        self._write_markdown(md_out, probes, summary)
        return 1 if self._has_failures(probes) else 0

    def collect(self) -> tuple[list[ProbeResult], list[ServiceStatus], dict[str, int]]:
        probes = self._run_probes()
        services = self._build_services(probes)
        summary = self._summarize(probes)
        return probes, services, summary

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _run_probes(self) -> list[ProbeResult]:
        probe_fns: list[tuple[str, Callable[[], ProbeResult]]] = [
            ("environment", env_coverage_probe),
            ("ports", ports_probe),
            ("database", db_probe),
            ("redis", redis_probe),
            ("api", api_probe),
            ("frontend", frontend_probe),
            ("migrations", migrations_probe),
            ("stripe", lambda: stripe_probe(warn_only=self.warn_only)),
            ("vault", lambda: vault_probe(warn_only=self.warn_only)),
        ]
        results: list[ProbeResult] = []
        for name, fn in probe_fns:
            results.append(util.guard_probe(name, fn))
        return results

    def _build_services(self, probes: list[ProbeResult]) -> list[ServiceStatus]:
        services: list[ServiceStatus] = []
        for key, label in (("api", "backend"), ("frontend", "frontend")):
            probe = next((p for p in probes if p.name == key), None)
            if probe is None:
                continue
            url = probe.metadata.get("url") if hasattr(probe, "metadata") else None
            endpoints = (url,) if isinstance(url, str) else ()
            services.append(
                ServiceStatus(
                    label=label,
                    state=probe.state,
                    detail=probe.detail,
                    endpoints=endpoints,
                    metadata=probe.metadata,
                )
            )
        return services

    def _summarize(self, probes: list[ProbeResult]) -> dict[str, int]:
        summary = {state.value: 0 for state in ProbeState}
        for probe in probes:
            summary[probe.state.value] = summary.get(probe.state.value, 0) + 1
        return summary

    def _has_failures(self, probes: list[ProbeResult]) -> bool:
        for probe in probes:
            if probe.state is ProbeState.ERROR:
                return True
            if self.strict and probe.state is ProbeState.WARN:
                return True
        return False

    def _print_console(
        self,
        summary: dict[str, int],
        probes: list[ProbeResult],
        services: list[ServiceStatus],
    ) -> None:
        console.rule("Doctor report")
        console.info(
            f"Profile={self.profile} strict={'yes' if self.strict else 'no'} "
            f"warn_only={self.warn_only}"
        )
        console.info(
            f"Probes: ok={summary.get('ok',0)} warn={summary.get('warn',0)} "
            f"error={summary.get('error',0)} skipped={summary.get('skipped',0)}"
        )
        for probe in sorted(probes, key=lambda p: (-p.severity_rank, p.name)):
            console.info(
                f"[{probe.state.value}] {probe.name}: {probe.detail or 'n/a'}",
            )
        for service in services:
            console.info(
                f"service {service.label}: {service.state.value} ({service.detail or 'n/a'})"
            )

    def _write_json(
        self,
        path: Path,
        probes: list[ProbeResult],
        services: list[ServiceStatus],
        summary: dict[str, int],
    ) -> None:
        payload = {
            "version": "v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "profile": self.profile,
            "strict": self.strict,
            "probes": [self._serialize_probe(p) for p in probes],
            "services": [self._serialize_service(s) for s in services],
            "summary": summary,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        console.success(f"Wrote doctor JSON report to {path}")

    def _write_markdown(
        self, path: Path, probes: list[ProbeResult], summary: dict[str, int]
    ) -> None:
        lines = ["# Starter CLI Doctor Report", ""]
        lines.append(f"Profile: {self.profile}  ")
        lines.append(f"Strict: {'yes' if self.strict else 'no'}  ")
        lines.append("")
        lines.append(
            f"Summary: ok={summary.get('ok',0)} warn={summary.get('warn',0)} "
            f"error={summary.get('error',0)} skipped={summary.get('skipped',0)}"
        )
        lines.append("")
        lines.append("| Probe | Status | Detail |")
        lines.append("| --- | --- | --- |")
        for probe in sorted(probes, key=lambda p: (-p.severity_rank, p.name)):
            detail = (probe.detail or "").replace("|", "\\|")
            lines.append(f"| {probe.name} | {probe.state.value} | {detail} |")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")
        console.success(f"Wrote doctor Markdown report to {path}")

    @staticmethod
    def _serialize_probe(probe: ProbeResult) -> dict[str, object]:
        data = asdict(probe)
        data.pop("created_at", None)  # keep JSON schema v1 contract
        # Drop None to satisfy schema optional fields
        return {k: v for k, v in data.items() if v is not None}

    @staticmethod
    def _serialize_service(service: ServiceStatus) -> dict[str, object]:
        data = asdict(service)
        data.pop("created_at", None)
        return {k: v for k, v in data.items() if v is not None}


def detect_profile() -> str:
    return os.getenv("ENVIRONMENT", "local")


__all__ = ["DoctorRunner", "detect_profile"]
