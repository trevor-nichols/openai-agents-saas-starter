from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from starter_console.core import CLIContext
from starter_console.core.inventory import FRONTEND_ENV_VARS, WIZARD_PROMPTED_ENV_VARS
from starter_console.core.profiles import (
    load_frontend_env,
    load_profile_registry,
    select_profile,
    write_profile_manifest,
)
from starter_console.ports.console import ConsolePort

from .._wizard.context import WizardContext, build_env_files
from ..schema import load_schema


@dataclass(slots=True)
class SilentConsole(ConsolePort):
    stream = sys.stdout
    err_stream = sys.stderr

    def info(self, message, topic=None, *, stream=None) -> None:
        return None

    def warn(self, message, topic=None, *, stream=None) -> None:
        return None

    def error(self, message, topic=None, *, stream=None) -> None:
        return None

    def success(self, message, topic=None, *, stream=None) -> None:
        return None

    def note(self, message, topic=None) -> None:
        return None

    def section(self, title, subtitle=None, *, icon="◆") -> None:
        return None

    def step(self, prefix, message) -> None:
        return None

    def value_change(self, *, scope, key, previous, current, secret=False) -> None:
        return None

    def newline(self) -> None:
        return None

    def print(self, *renderables, **kwargs) -> None:
        return None

    def render(self, renderable, *, error=False) -> None:
        return None

    def rule(self, title) -> None:
        return None

    def ask_text(
        self,
        *,
        key,
        prompt,
        default,
        required,
        secret=False,
        command_hook=None,
    ) -> str:
        raise RuntimeError("Silent console cannot prompt.")

    def ask_bool(self, *, key, prompt, default, command_hook=None) -> bool:
        raise RuntimeError("Silent console cannot prompt.")


def build_preview_context(
    ctx: CLIContext,
    *,
    profile_id: str,
    profiles_path: Path | None,
    answers: dict[str, str],
    dry_run: bool,
) -> WizardContext:
    preview_ctx = ctx
    if dry_run:
        preview_ctx = CLIContext(
            project_root=ctx.project_root,
            env_files=ctx.env_files,
            console=SilentConsole(),
            presenter=ctx.presenter,
            skip_env=ctx.skip_env,
            quiet_env=True,
        )
        preview_ctx.load_environment(verbose=False)

    backend_env, frontend_env, frontend_path = build_env_files(preview_ctx)
    registry = load_profile_registry(project_root=ctx.project_root, override_path=profiles_path)
    selection = select_profile(registry, explicit=profile_id)
    if not dry_run:
        frontend_env_meta = load_frontend_env(project_root=ctx.project_root)
        write_profile_manifest(
            selection,
            project_root=ctx.project_root,
            frontend_env=frontend_env_meta,
        )

    wizard_ctx = WizardContext(
        cli_ctx=preview_ctx,
        profile=selection.profile.profile_id,
        profile_policy=selection.profile,
        backend_env=backend_env,
        frontend_env=frontend_env,
        frontend_path=frontend_path,
        summary_path=None,
        markdown_summary_path=None,
        schema=load_schema(),
        state_store=None,
    )
    wizard_ctx.dry_run = dry_run
    wizard_ctx.skip_external_calls = True

    for raw_key, value in answers.items():
        key = raw_key.strip().upper()
        if key in FRONTEND_ENV_VARS and frontend_env:
            frontend_env.set(key, value)
        elif key in WIZARD_PROMPTED_ENV_VARS:
            backend_env.set(key, value)

    hosting_preset = answers.get("SETUP_HOSTING_PRESET")
    cloud_provider = answers.get("SETUP_CLOUD_PROVIDER")
    if hosting_preset:
        wizard_ctx.hosting_preset = hosting_preset
        os.environ["SETUP_HOSTING_PRESET"] = hosting_preset
    if cloud_provider:
        wizard_ctx.cloud_provider = cloud_provider
        os.environ["SETUP_CLOUD_PROVIDER"] = cloud_provider
    return wizard_ctx


__all__ = ["SilentConsole", "build_preview_context"]
