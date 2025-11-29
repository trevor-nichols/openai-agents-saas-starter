from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext
from starter_cli.core.constants import PROJECT_ROOT, SAFE_ENVIRONMENTS
from starter_cli.core.status_models import ProbeResult, ProbeState, ServiceStatus
from starter_cli.workflows.home.probes import util
from starter_cli.workflows.home.probes.registry import PROBE_SPECS, ProbeContext, ProbeSpec

DEFAULT_JSON_REPORT = PROJECT_ROOT / "var" / "reports" / "operator-dashboard.json"
DEFAULT_MD_REPORT = PROJECT_ROOT / "var" / "reports" / "operator-dashboard.md"


class DoctorRunner:
    def __init__(self, ctx: CLIContext, *, profile: str, strict: bool) -> None:
        self.ctx = ctx
        self.profile = profile
        self.strict = strict
        self.warn_only = (profile.lower() in SAFE_ENVIRONMENTS) and not strict
        self.expect_down = _detect_expect_down(dict(os.environ))

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

    def collect(
        self, *, log_suppressed: bool = False
    ) -> tuple[list[ProbeResult], list[ServiceStatus], dict[str, int]]:
        try:
            probes = self._run_probes(log_suppressed=log_suppressed)
        except TypeError:
            # compatibility for test stubs that don't accept kwargs
            probes = self._run_probes()
        services = self._build_services(probes)
        summary = self._summarize(probes)
        return probes, services, summary

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _run_probes(self, *, log_suppressed: bool = False) -> list[ProbeResult]:
        ctx = ProbeContext(
            env=os.environ,
            settings=self.ctx.optional_settings(),
            profile=self.profile,
            strict=self.strict,
            warn_only=self.warn_only,
        )
        if log_suppressed and self.expect_down:
            console.info(
                "Suppressed probes via EXPECT_*_DOWN: " + ", ".join(sorted(self.expect_down)),
                topic="probes",
            )
        results: list[ProbeResult] = []
        for spec in PROBE_SPECS:
            def _runner(spec: object = spec) -> ProbeResult:
                assert isinstance(spec, ProbeSpec)
                return spec.factory(ctx)

            result = util.guard_probe(
                spec.name,
                _runner,
                force_skip=spec.name in self.expect_down,
                skip_reason="suppressed by EXPECT_*_DOWN",
            )
            results.append(self._with_category(result, spec.category))
        return results

    def _build_services(self, probes: list[ProbeResult]) -> list[ServiceStatus]:
        services: list[ServiceStatus] = []
        stack_probe = next((p for p in probes if p.name == "stack"), None)
        if stack_probe:
            services.append(
                ServiceStatus(
                    label="stack",
                    state=stack_probe.state,
                    detail=stack_probe.detail,
                    metadata=stack_probe.metadata,
                )
            )
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
        return _prune_duplicate_services(services, probes)

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

    @staticmethod
    def _with_category(result: ProbeResult, category: str) -> ProbeResult:
        metadata = dict(result.metadata) if result.metadata else {}
        metadata.setdefault("category", category)
        return ProbeResult(
            name=result.name,
            state=result.state,
            detail=result.detail,
            remediation=result.remediation,
            duration_ms=result.duration_ms,
            metadata=metadata,
            created_at=result.created_at,
        )


def _prune_duplicate_services(
    services: list[ServiceStatus], probes: list[ProbeResult]
) -> list[ServiceStatus]:
    if not services:
        return services
    probe_names = {p.name for p in probes}
    filtered: list[ServiceStatus] = []
    for svc in services:
        # Drop services that just mirror probes (backend/api, frontend/frontend)
        if svc.label == "backend" and "api" in probe_names:
            continue
        if svc.label == "frontend" and "frontend" in probe_names:
            continue
        filtered.append(svc)
    return filtered


def _detect_expect_down(env: Mapping[str, str]) -> set[str]:
    expect_flags = {
        "api": "EXPECT_API_DOWN",
        "frontend": "EXPECT_FRONTEND_DOWN",
        "database": "EXPECT_DB_DOWN",
        "redis": "EXPECT_REDIS_DOWN",
    }
    lowered = {k: v.lower() for k, v in env.items() if isinstance(v, str)}
    return {
        name
        for name, flag in expect_flags.items()
        if lowered.get(flag, "") in {"1", "true", "yes"}
    }


def detect_profile() -> str:
    return os.getenv("ENVIRONMENT", "local")


__all__ = ["DoctorRunner", "detect_profile"]
