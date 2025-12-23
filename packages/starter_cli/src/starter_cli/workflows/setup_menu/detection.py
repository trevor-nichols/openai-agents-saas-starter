from __future__ import annotations

import json
import os
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

from starter_cli.core import CLIContext
from starter_cli.telemetry import load_verification_artifacts

from .models import SetupAction, SetupItem

STALE_AFTER_DAYS = 7


def collect_setup_items(
    ctx: CLIContext, *, stale_after: timedelta | None = None
) -> list[SetupItem]:
    window = stale_after or timedelta(days=STALE_AFTER_DAYS)
    items: list[SetupItem] = []
    items.append(_wizard_item(ctx, window))
    items.append(_secrets_item(ctx, window))
    items.append(_stripe_item(ctx, window))
    items.append(_db_release_item(ctx, window))
    items.append(_usage_item(ctx, window))
    items.append(_dev_user_item(ctx, window))
    items.append(_geoip_item(ctx, window))
    return items


# ---------------------------------------------------------------------------
# Individual detectors
# ---------------------------------------------------------------------------


def _wizard_item(ctx: CLIContext, stale_after: timedelta) -> SetupItem:
    path = ctx.project_root / "var/reports/setup-summary.json"
    if not path.exists():
        return SetupItem(
            key="wizard",
            label="Setup Wizard",
            status="missing",
            detail="Run the setup wizard to generate env files.",
            progress=0.0,
            progress_label="0/10",
            actions=[_wizard_action()],
            optional=False,
        )

    milestones: Sequence[dict[str, object]] = ()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        raw_milestones = data.get("milestones", [])
        if isinstance(raw_milestones, list):
            milestones = [
                milestone
                for milestone in raw_milestones
                if isinstance(milestone, dict) and milestone.get("milestone")
            ]
    except json.JSONDecodeError:
        milestones = ()

    total = len(milestones) or 1
    ok_count = sum(1 for m in milestones if m.get("status") == "ok")
    progress = ok_count / total if total else None
    status = "done" if ok_count == total else "partial"
    detail = f"{ok_count}/{total} sections ok"

    last_run = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    if datetime.now(tz=UTC) - last_run > stale_after:
        status = "stale"
        detail = f"{detail} (stale)"

    return SetupItem(
        key="wizard",
        label="Setup Wizard",
        status=status,
        detail=detail,
        progress=progress,
        progress_label=f"{ok_count}/{total}",
        last_run=last_run,
        artifact=path,
        actions=[_wizard_action()],
        optional=False,
    )


def _secrets_item(ctx: CLIContext, stale_after: timedelta) -> SetupItem:
    path = ctx.project_root / "var/reports/verification-artifacts.json"
    artifacts = load_verification_artifacts(path)
    if not artifacts:
        return SetupItem(
            key="secrets",
            label="Secrets Provider",
            status="missing",
            detail="No verification artifacts found.",
            actions=[_secrets_action()],
        )

    latest = sorted(artifacts, key=lambda a: a.timestamp, reverse=True)[0]
    try:
        last_run = datetime.fromisoformat(latest.timestamp.replace("Z", "+00:00"))
    except Exception:
        last_run = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)

    status = "done" if latest.status.lower() == "passed" else "failed"
    if datetime.now(tz=UTC) - last_run > stale_after:
        status = "stale"
    detail = f"{latest.provider}: {latest.status}"

    return SetupItem(
        key="secrets",
        label="Secrets Provider",
        status=status,
        detail=detail,
        last_run=last_run,
        artifact=path,
        actions=[_secrets_action()],
    )


def _stripe_item(ctx: CLIContext, stale_after: timedelta) -> SetupItem:
    env = os.environ
    secret = env.get("STRIPE_SECRET_KEY")
    webhook = env.get("STRIPE_WEBHOOK_SECRET")
    prices = env.get("STRIPE_PRODUCT_PRICE_MAP")

    level = "missing"
    progress = 0.0
    if secret and prices and webhook:
        level = "done"
        progress = 1.0
    elif secret:
        level = "partial"
        progress = 0.5

    last_run = _latest_env_mtime(ctx)
    if last_run and datetime.now(tz=UTC) - last_run > stale_after:
        level = "stale"

    if level == "done":
        detail = "Keys+prices+webhook"
    elif secret:
        detail = "Keys captured"
    else:
        detail = "Not configured"
    return SetupItem(
        key="stripe",
        label="Stripe Billing",
        status=level,
        detail=detail,
        progress=progress,
        progress_label=_progress_label(progress),
        last_run=last_run,
        actions=[_stripe_action()],
    )


def _db_release_item(ctx: CLIContext, stale_after: timedelta) -> SetupItem:
    reports_dir = ctx.project_root / "var/reports"
    latest = _latest_file(reports_dir.glob("db-release-*.json"))
    if latest is None:
        return SetupItem(
            key="db_release",
            label="DB Release",
            status="missing",
            detail="No db-release report found.",
            actions=[_release_action()],
        )

    last_run = datetime.fromtimestamp(latest.stat().st_mtime, tz=UTC)
    status = "done" if datetime.now(tz=UTC) - last_run <= stale_after else "stale"
    return SetupItem(
        key="db_release",
        label="DB Release",
        status=status,
        detail="Latest db-release report present.",
        last_run=last_run,
        artifact=latest,
        actions=[_release_action()],
    )


def _usage_item(ctx: CLIContext, stale_after: timedelta) -> SetupItem:
    reports_dir = ctx.project_root / "var/reports"
    latest = _latest_file(
        [
            reports_dir / "usage-dashboard.json",
            reports_dir / "usage-dashboard.csv",
        ]
    )
    if latest is None or not latest.exists():
        return SetupItem(
            key="usage",
            label="Usage Reports",
            status="missing",
            detail="No usage dashboard artifacts found.",
            actions=[_usage_action()],
        )

    last_run = datetime.fromtimestamp(latest.stat().st_mtime, tz=UTC)
    status = "done" if datetime.now(tz=UTC) - last_run <= stale_after else "stale"
    return SetupItem(
        key="usage",
        label="Usage Reports",
        status=status,
        detail="Usage dashboard exported.",
        last_run=last_run,
        artifact=latest,
        actions=[_usage_action()],
    )


def _dev_user_item(ctx: CLIContext, stale_after: timedelta) -> SetupItem:
    path = ctx.project_root / "var/reports/dev-user-credentials.json"
    if not path.exists():
        return SetupItem(
            key="dev_user",
            label="Dev Admin User",
            status="missing",
            detail="Seed a demo dev admin account.",
            progress=0.0,
            progress_label=_progress_label(0.0),
            actions=[_dev_user_action()],
        )
    last_run = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    status = "done" if datetime.now(tz=UTC) - last_run <= stale_after else "stale"
    return SetupItem(
        key="dev_user",
        label="Dev Admin User",
        status=status,
        detail="Dev admin credentials recorded.",
        last_run=last_run,
        artifact=path,
        progress=1.0,
        progress_label=_progress_label(1.0),
        actions=[_dev_user_action()],
    )


def _geoip_item(ctx: CLIContext, stale_after: timedelta) -> SetupItem:
    provider = os.environ.get("GEOIP_PROVIDER", "none").lower()
    db_path_str = os.environ.get("GEOIP_MAXMIND_DB_PATH") or "var/geoip/GeoLite2-City.mmdb"
    db_path = (ctx.project_root / db_path_str).resolve()

    if provider == "none":
        return SetupItem(
            key="geoip",
            label="GeoIP",
            status="missing",
            detail="Provider not configured (optional).",
            optional=True,
            actions=[_wizard_action()],
        )

    if provider in {"maxmind_db", "ip2location_db"}:
        if db_path.exists():
            last_run = datetime.fromtimestamp(db_path.stat().st_mtime, tz=UTC)
            status = "done" if datetime.now(tz=UTC) - last_run <= stale_after else "stale"
            return SetupItem(
                key="geoip",
                label="GeoIP",
                status=status,
                detail=f"{provider} database present",
                last_run=last_run,
                artifact=db_path,
                optional=True,
                actions=[_wizard_action()],
            )
        return SetupItem(
            key="geoip",
            label="GeoIP",
            status="missing",
            detail=f"{provider} selected but database missing at {db_path}",
            optional=True,
            actions=[_wizard_action()],
        )

    # SaaS providers: rely on env presence only
    return SetupItem(
        key="geoip",
        label="GeoIP",
        status="partial",
        detail=f"{provider} configured (validate keys via setup wizard if needed).",
        optional=True,
        actions=[_wizard_action()],
    )


# ---------------------------------------------------------------------------
# Action factories
# ---------------------------------------------------------------------------


def _wizard_action() -> SetupAction:
    return SetupAction(
        key="wizard",
        label="Run setup wizard",
        command=["python", "-m", "starter_cli.app", "setup", "wizard"],
        route="wizard",
        warn_overwrite=True,
    )


def _secrets_action() -> SetupAction:
    return SetupAction(
        key="secrets_onboard",
        label="Run secrets onboard",
        command=["python", "-m", "starter_cli.app", "secrets", "onboard"],
    )


def _stripe_action() -> SetupAction:
    return SetupAction(
        key="stripe_setup",
        label="Run stripe setup",
        command=["python", "-m", "starter_cli.app", "stripe", "setup"],
        warn_overwrite=True,
    )


def _release_action() -> SetupAction:
    return SetupAction(
        key="release_db",
        label="Run db release",
        command=["python", "-m", "starter_cli.app", "release", "db"],
    )


def _usage_action() -> SetupAction:
    return SetupAction(
        key="usage_export",
        label="Export usage report",
        command=["python", "-m", "starter_cli.app", "usage", "export-report"],
    )


def _dev_user_action() -> SetupAction:
    return SetupAction(
        key="dev_user",
        label="Ensure dev user",
        command=["python", "-m", "starter_cli.app", "users", "ensure-dev"],
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _latest_env_mtime(ctx: CLIContext) -> datetime | None:
    mtimes: list[float] = []
    for env_file in ctx.loaded_env_files:
        if env_file.exists():
            mtimes.append(env_file.stat().st_mtime)
    if not mtimes:
        return None
    return datetime.fromtimestamp(max(mtimes), tz=UTC)


def _latest_file(paths: Iterable[Path]) -> Path | None:
    candidates = [path for path in paths if path and path.exists()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _progress_label(progress: float | None) -> str | None:
    if progress is None:
        return None
    if progress >= 1:
        return "100%"
    if progress <= 0:
        return "0%"
    return f"{round(progress * 100)}%"


__all__ = ["collect_setup_items", "STALE_AFTER_DAYS"]
