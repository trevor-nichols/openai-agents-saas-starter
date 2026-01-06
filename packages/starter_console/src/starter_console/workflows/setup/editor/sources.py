from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from starter_console.core import CLIContext
from starter_console.workflows.setup.choice_help import CHOICE_HELP

from .._wizard.context import WizardContext
from .._wizard.sections import (
    core,
    dev_user,
    frontend,
    integrations,
    observability,
    providers,
    secrets,
    security,
    signup,
    storage,
    usage,
)
from ..inputs import _coerce_bool
from ..schema_provider import SchemaAwareInputProvider
from ..section_specs import SECTION_SPECS
from .context import build_preview_context
from .models import FieldSpec, SectionModel

_IGNORED_PROMPTS = {
    "RUN_MIGRATIONS_NOW",
    "ROTATE_SIGNING_KEYS",
    "RUN_STRIPE_SEED",
    "STRIPE_WEBHOOK_SECRET_AUTO",
    "GEOIP_MAXMIND_DOWNLOAD",
    "SLACK_STATUS_SEND_TEST",
}

_SECTION_RUNNERS = {
    "core": core.run,
    "providers": providers.run,
    "secrets": secrets.run,
    "security": security.run,
    "storage": storage.run,
    "usage": usage.run,
    "observability": observability.run,
    "integrations": integrations.run,
    "signup": signup.run,
    "frontend": frontend.run,
    "dev_user": dev_user.run,
}


class InMemoryStateStore:
    def __init__(self) -> None:
        self._answers: dict[str, str] = {}
        self._skipped: dict[str, str] = {}

    def record_answer(self, key: str, value: str) -> None:
        self._answers[key.strip().upper()] = value
        self._skipped.pop(key.strip().upper(), None)

    def record_skip(self, key: str, reason: str) -> None:
        self._skipped[key.strip().upper()] = reason

    def snapshot(self) -> dict[str, str]:
        return dict(self._answers)

    def forget_answer(self, key: str) -> None:
        self._answers.pop(key.strip().upper(), None)


class PromptCaptureProvider:
    def __init__(
        self,
        *,
        answers: dict[str, str],
        fields: list[FieldSpec],
        descriptions: dict[str, str],
    ) -> None:
        self._answers = answers
        self._fields = fields
        self._descriptions = descriptions

    def prompt_string(self, *, key: str, prompt: str, default: str | None, required: bool) -> str:
        normalized = key.strip().upper()
        if normalized in _IGNORED_PROMPTS:
            return default or ""
        value = self._resolve_string(normalized, default)
        self._fields.append(
            FieldSpec(
                key=normalized,
                label=prompt,
                kind="string",
                required=required,
                value=value,
                default=default,
                description=self._descriptions.get(normalized),
            )
        )
        if value != "":
            self._answers[normalized] = value
        return value

    def prompt_bool(self, *, key: str, prompt: str, default: bool) -> bool:
        normalized = key.strip().upper()
        if normalized in _IGNORED_PROMPTS:
            return default
        value = self._resolve_bool(normalized, default)
        self._fields.append(
            FieldSpec(
                key=normalized,
                label=prompt,
                kind="bool",
                required=False,
                value="true" if value else "false",
                default="true" if default else "false",
                description=self._descriptions.get(normalized),
            )
        )
        self._answers[normalized] = "true" if value else "false"
        return value

    def prompt_choice(
        self,
        *,
        key: str,
        prompt: str,
        choices: Iterable[str],
        default: str | None = None,
    ) -> str:
        normalized = key.strip().upper()
        if normalized in _IGNORED_PROMPTS:
            if default is not None:
                return default
            return next(iter(choices), "")
        choice_list = tuple(choices)
        value = self._resolve_choice(normalized, choice_list, default)
        self._fields.append(
            FieldSpec(
                key=normalized,
                label=prompt,
                kind="choice",
                required=True,
                value=value,
                default=default,
                choices=choice_list,
                description=self._descriptions.get(normalized),
                choice_help=CHOICE_HELP.get(normalized, {}),
            )
        )
        self._answers[normalized] = value
        return value

    def prompt_secret(
        self,
        *,
        key: str,
        prompt: str,
        existing: str | None,
        required: bool,
    ) -> str:
        normalized = key.strip().upper()
        if normalized in _IGNORED_PROMPTS:
            return existing or ""
        value = self._resolve_secret(normalized, existing)
        self._fields.append(
            FieldSpec(
                key=normalized,
                label=prompt,
                kind="secret",
                required=required,
                value=value,
                default=existing,
                description=self._descriptions.get(normalized),
            )
        )
        if value != "":
            self._answers[normalized] = value
        return value

    def _resolve_string(self, key: str, default: str | None) -> str:
        if key in self._answers:
            return self._answers[key]
        return default or ""

    def _resolve_bool(self, key: str, default: bool) -> bool:
        if key not in self._answers:
            return default
        return _coerce_bool(self._answers[key], key)

    def _resolve_choice(
        self,
        key: str,
        choices: tuple[str, ...],
        default: str | None,
    ) -> str:
        raw = self._answers.get(key)
        if raw and raw in choices:
            return raw
        if default and default in choices:
            return default
        return choices[0] if choices else ""

    def _resolve_secret(self, key: str, existing: str | None) -> str:
        if key in self._answers:
            return self._answers[key]
        if existing:
            return existing
        return ""


def load_setting_descriptions(project_root: Path) -> dict[str, str]:
    schema_path = project_root / "docs/contracts/settings.schema.json"
    if not schema_path.exists():
        return {}
    payload = json.loads(schema_path.read_text(encoding="utf-8"))
    props = payload.get("properties", {}) if isinstance(payload, dict) else {}
    descriptions: dict[str, str] = {}
    for key, meta in props.items():
        if not isinstance(meta, dict):
            continue
        desc = meta.get("description")
        if desc:
            descriptions[key.strip().upper()] = str(desc)
    return descriptions


def collect_sections(
    ctx: CLIContext,
    *,
    profile_id: str,
    profiles_path: Path | None,
    answers: dict[str, str],
    descriptions: dict[str, str],
    dry_run: bool,
) -> tuple[list[SectionModel], WizardContext]:
    wizard_ctx = build_preview_context(
        ctx,
        profile_id=profile_id,
        profiles_path=profiles_path,
        answers=answers,
        dry_run=dry_run,
    )
    state = InMemoryStateStore()
    sections: list[SectionModel] = []
    for spec in SECTION_SPECS:
        runner = _SECTION_RUNNERS.get(spec.key)
        if runner is None:
            continue
        fields: list[FieldSpec] = []
        provider = PromptCaptureProvider(answers=answers, fields=fields, descriptions=descriptions)
        wrapped = SchemaAwareInputProvider(
            provider=provider,
            schema=wizard_ctx.schema,
            state=state,
            context=wizard_ctx,
        )
        runner(wizard_ctx, wrapped)
        sections.append(SectionModel(key=spec.key, label=spec.label, fields=fields))
    return sections, wizard_ctx


__all__ = [
    "PromptCaptureProvider",
    "InMemoryStateStore",
    "collect_sections",
    "load_setting_descriptions",
]
