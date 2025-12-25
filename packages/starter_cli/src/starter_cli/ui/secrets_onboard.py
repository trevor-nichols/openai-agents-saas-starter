from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, OptionList, RadioButton, RadioSet, Static

from starter_cli.core import CLIContext
from starter_cli.ports.presentation import NotifyPort
from starter_cli.presenters import PresenterConsoleAdapter, build_textual_presenter
from starter_cli.services.secrets.onboard import execute_secrets_onboard
from starter_cli.ui.context import derive_presenter_context
from starter_cli.ui.prompting import PromptChannel, PromptRequest, TextualPromptPort
from starter_cli.workflows.secrets import registry
from starter_cli.workflows.setup.inputs import ParsedAnswers


@dataclass(slots=True)
class SecretsOnboardSnapshot:
    events: list[str]
    status: str
    done: bool
    error: str | None


class SecretsOnboardState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: deque[str] = deque(maxlen=10)
        self._status = "Select a provider and start onboarding."
        self._done = False
        self._error: str | None = None

    def log(self, message: str) -> None:
        with self._lock:
            self._events.appendleft(message)

    def set_status(self, message: str) -> None:
        with self._lock:
            self._status = message

    def mark_done(self, *, error: str | None = None) -> None:
        with self._lock:
            self._done = True
            self._error = error

    def snapshot(self) -> SecretsOnboardSnapshot:
        with self._lock:
            return SecretsOnboardSnapshot(
                events=list(self._events),
                status=self._status,
                done=self._done,
                error=self._error,
            )


class SecretsNotifyPort(NotifyPort):
    def __init__(self, state: SecretsOnboardState) -> None:
        self._state = state

    def info(self, message: str, topic: str | None = None, *, stream=None) -> None:
        self._log("INFO", message, topic)

    def warn(self, message: str, topic: str | None = None, *, stream=None) -> None:
        self._log("WARN", message, topic)

    def error(self, message: str, topic: str | None = None, *, stream=None) -> None:
        self._log("ERROR", message, topic)

    def success(self, message: str, topic: str | None = None, *, stream=None) -> None:
        self._log("SUCCESS", message, topic)

    def note(self, message: str, topic: str | None = None) -> None:
        self._log("NOTE", message, topic)

    def section(self, title: str, subtitle: str | None = None, *, icon: str = "*") -> None:
        line = f"{icon} {title}"
        if subtitle:
            line += f" - {subtitle}"
        self._state.log(line)

    def step(self, prefix: str, message: str) -> None:
        self._state.log(f"{prefix} {message}")

    def value_change(
        self,
        *,
        scope: str | None,
        key: str,
        previous: str | None,
        current: str,
        secret: bool = False,
    ) -> None:
        scope_label = f"[{scope}] " if scope else ""
        prev_display = "<unset>" if previous is None else ("***" if secret else previous)
        next_display = "***" if secret else current
        self._state.log(f"{scope_label}{key}: {prev_display} -> {next_display}")

    def newline(self) -> None:
        self._state.log("")

    def print(self, *renderables, **kwargs) -> None:
        joined = " ".join(str(item) for item in renderables)
        self._state.log(joined)

    def render(self, renderable, *, error: bool = False) -> None:
        self._state.log(str(renderable))

    def rule(self, title: str) -> None:
        self._state.log(f"---- {title} ----")

    def _log(self, level: str, message: str, topic: str | None) -> None:
        topic_label = f"[{topic}]" if topic else ""
        self._state.log(f"[{level}]{topic_label} {message}")


class SecretsOnboardSession:
    def __init__(
        self,
        ctx: CLIContext,
        *,
        provider: str | None,
        answers: ParsedAnswers,
        skip_automation: bool,
    ) -> None:
        self._ctx = ctx
        self._provider = provider
        self._answers = answers
        self._skip_automation = skip_automation
        self._prompt_channel = PromptChannel()
        self._state = SecretsOnboardState()
        self._thread: threading.Thread | None = None

    @property
    def state(self) -> SecretsOnboardState:
        return self._state

    @property
    def prompt_channel(self) -> PromptChannel:
        return self._prompt_channel

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        try:
            notify = SecretsNotifyPort(self._state)
            prompt = TextualPromptPort(prefill=self._answers, channel=self._prompt_channel)
            presenter = build_textual_presenter(prompt=prompt, notify=notify)
            console = PresenterConsoleAdapter(presenter)
            run_ctx = derive_presenter_context(self._ctx, console=console, presenter=presenter)
            self._state.set_status("Running secrets onboarding...")
            execute_secrets_onboard(
                run_ctx,
                provider=self._provider,
                non_interactive=False,
                input_provider=prompt,
                skip_automation=self._skip_automation,
            )
            self._state.set_status("Secrets onboarding complete.")
        except Exception as exc:  # pragma: no cover - defensive
            self._state.mark_done(error=str(exc))
            self._state.set_status("Secrets onboarding failed.")
        else:
            self._state.mark_done()


class SecretsOnboardScreen(ModalScreen[None]):
    BINDINGS: ClassVar = [
        Binding("escape", "close", "Close", show=False),
    ]

    DEFAULT_CSS: ClassVar[str] = """
    SecretsOnboardScreen {
        align: center middle;
    }

    #secrets-panel {
        width: 90%;
        max-width: 100;
        background: $panel;
        border: tall $primary;
        padding: 1 2;
    }

    #secrets-log {
        height: 8;
        color: $text-muted;
        border: tall $panel-darken-1;
        padding: 1;
    }

    #secrets-prompt {
        margin-top: 1;
        padding-top: 1;
        border-top: solid $panel-darken-1;
    }

    #secrets-prompt-actions {
        height: auto;
        padding-top: 1;
    }
    """

    def __init__(
        self,
        ctx: CLIContext,
        *,
        answers: ParsedAnswers | None = None,
        skip_automation: bool = False,
    ) -> None:
        super().__init__()
        self._ctx = ctx
        self._answers = answers or {}
        self._skip_automation = skip_automation
        self._options = list(registry.provider_options())
        self._session: SecretsOnboardSession | None = None
        self._current_prompt: PromptRequest | None = None
        self._choice_values: tuple[str, ...] = ()

    def compose(self) -> ComposeResult:
        with Vertical(id="secrets-panel"):
            yield Static("Secrets Onboarding", id="secrets-title")
            yield Static(
                "Select a provider, then follow the prompts to configure signing secrets.",
                id="secrets-subtitle",
            )
            yield RadioSet(
                *[
                    RadioButton(option.label, id=f"provider-{option.literal.value}")
                    for option in self._options
                ],
                id="secrets-providers",
            )
            yield Static("", id="secrets-provider-detail")
            with Horizontal(id="secrets-actions"):
                yield Button("Start", id="secrets-start", variant="primary")
                yield Button("Close", id="secrets-close")
            yield Static("", id="secrets-status")
            yield Static("", id="secrets-log")
            with Vertical(id="secrets-prompt"):
                yield Static("", id="secrets-prompt-label")
                yield Static("", id="secrets-prompt-detail")
                yield Input(id="secrets-input")
                yield OptionList(id="secrets-options")
                with Horizontal(id="secrets-prompt-actions"):
                    yield Button("Submit", id="secrets-submit", variant="primary")
                    yield Button("Clear", id="secrets-clear")
                yield Static("", id="secrets-prompt-status")

    def on_mount(self) -> None:
        self._configure_provider()
        self._set_prompt_visibility(False)
        self.set_interval(0.5, self._refresh_view)
        self.set_interval(0.2, self._poll_prompt)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "secrets-start":
            self._start_session()
        elif event.button.id == "secrets-close":
            self.dismiss()
        elif event.button.id == "secrets-submit":
            self._submit_prompt()
        elif event.button.id == "secrets-clear":
            self.query_one("#secrets-input", Input).value = ""

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "secrets-input":
            self._submit_prompt()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id != "secrets-options":
            return
        if not self._choice_values:
            return
        if event.option_index >= len(self._choice_values):
            return
        self._submit_value(self._choice_values[event.option_index])

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id == "secrets-providers":
            self._update_provider_detail()

    def action_close(self) -> None:
        self.dismiss()

    def _start_session(self) -> None:
        if self._session:
            return
        provider = self._selected_provider()
        if not provider:
            self.query_one("#secrets-status", Static).update("Choose a provider first.")
            return
        self._session = SecretsOnboardSession(
            self._ctx,
            provider=provider,
            answers=self._answers,
            skip_automation=self._skip_automation,
        )
        self._session.start()
        self.query_one("#secrets-status", Static).update("Secrets onboarding running...")

    def _selected_provider(self) -> str | None:
        radio = self.query_one("#secrets-providers", RadioSet)
        selected = radio.pressed_button
        if not selected:
            return None
        return (selected.id or "").replace("provider-", "")

    def _configure_provider(self) -> None:
        if not self._options:
            return
        default_id = f"provider-{self._options[0].literal.value}"
        button = self.query_one(f"#{default_id}", RadioButton)
        button.value = True
        self._update_provider_detail()

    def _update_provider_detail(self) -> None:
        detail = ""
        selected = self._selected_provider()
        for option in self._options:
            if option.literal.value == selected:
                detail = option.description
                break
        self.query_one("#secrets-provider-detail", Static).update(detail)

    def _refresh_view(self) -> None:
        if not self._session:
            return
        snapshot = self._session.state.snapshot()
        status = snapshot.status
        if snapshot.error:
            status = f"{status} ({snapshot.error})"
        self.query_one("#secrets-status", Static).update(status)
        self.query_one("#secrets-log", Static).update("\n".join(snapshot.events))

    def _poll_prompt(self) -> None:
        if not self._session:
            return
        request = self._session.prompt_channel.poll()
        if request is None:
            return
        self._current_prompt = request
        self._choice_values = request.choices
        self._set_prompt_status("")
        self._render_prompt(request)

    def _render_prompt(self, request: PromptRequest) -> None:
        label = f"{request.prompt} [{request.key}]"
        self.query_one("#secrets-prompt-label", Static).update(label)
        detail = "Required" if request.required else "Optional"
        if request.default:
            detail += f" | Default: {request.default}"
        self.query_one("#secrets-prompt-detail", Static).update(detail)
        input_field = self.query_one("#secrets-input", Input)
        option_list = self.query_one("#secrets-options", OptionList)
        if request.kind in {"string", "secret"}:
            input_field.password = request.kind == "secret"
            input_field.value = request.default or ""
            option_list.clear_options()
            self._set_prompt_visibility(True, show_input=True)
            input_field.focus()
        else:
            input_field.value = ""
            option_list.clear_options()
            for choice in request.choices:
                option_list.add_option(choice)
            if request.default and request.default in request.choices:
                option_list.highlighted = request.choices.index(request.default)
            self._set_prompt_visibility(True, show_input=False)
            option_list.focus()

    def _submit_prompt(self) -> None:
        if not self._current_prompt:
            return
        if self._current_prompt.kind in {"string", "secret"}:
            input_field = self.query_one("#secrets-input", Input)
            value = input_field.value.strip()
            if not value and self._current_prompt.default:
                value = self._current_prompt.default
            if self._current_prompt.required and not value:
                self._set_prompt_status("Value is required.")
                return
            self._submit_value(value)
            return
        option_list = self.query_one("#secrets-options", OptionList)
        index = option_list.highlighted
        if index is None or index < 0 or index >= len(self._choice_values):
            if self._current_prompt.default:
                self._submit_value(self._current_prompt.default)
                return
            self._set_prompt_status("Choose an option.")
            return
        self._submit_value(self._choice_values[index])

    def _submit_value(self, value: str) -> None:
        if not self._session:
            return
        self._session.prompt_channel.submit(value)
        self._current_prompt = None
        self._choice_values = ()
        self._set_prompt_visibility(False)
        self._set_prompt_status("Awaiting next prompt...")

    def submit_current_prompt(self, value: str | None = None) -> None:
        if not self._current_prompt:
            return
        if value is not None and self._current_prompt.kind in {"string", "secret"}:
            input_field = self.query_one("#secrets-input", Input)
            input_field.value = value
        self._submit_prompt()

    def _set_prompt_visibility(self, visible: bool, *, show_input: bool = True) -> None:
        input_field = self.query_one("#secrets-input", Input)
        option_list = self.query_one("#secrets-options", OptionList)
        input_field.display = visible and show_input
        option_list.display = visible and not show_input

    def _set_prompt_status(self, message: str) -> None:
        self.query_one("#secrets-prompt-status", Static).update(message)


__all__ = ["SecretsOnboardScreen"]
