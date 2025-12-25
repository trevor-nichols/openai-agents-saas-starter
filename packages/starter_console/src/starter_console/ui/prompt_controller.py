from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from textual.widget import Widget
from textual.widgets import Input, OptionList, Static

from starter_console.ui.prompting import PromptChannel, PromptRequest


@dataclass(slots=True)
class PromptState:
    current: PromptRequest | None = None
    choices: tuple[str, ...] = ()


class PromptController:
    def __init__(
        self,
        root: Widget,
        *,
        prefix: str,
        channel: PromptChannel | None = None,
    ) -> None:
        self._root = root
        self._prefix = prefix
        self._channel = channel
        self.state = PromptState()

    def set_channel(self, channel: PromptChannel | None) -> None:
        self._channel = channel

    def poll(self) -> None:
        if self._channel is None:
            return
        request = self._channel.poll()
        if request is None:
            return
        self.state.current = request
        self.state.choices = request.choices
        self._set_status("")
        self._render_prompt(request)

    def submit_current(self) -> None:
        request = self.state.current
        if request is None:
            return
        if request.kind in {"string", "secret"}:
            input_field = self._input()
            value = input_field.value.strip()
            if not value and request.default:
                value = request.default
            if request.required and not value:
                self._set_status("Value is required.")
                return
            self._submit_value(value)
            return
        option_list = self._options()
        index = option_list.highlighted
        if index is None or index < 0 or index >= len(self.state.choices):
            if request.default:
                self._submit_value(request.default)
                return
            self._set_status("Choose an option.")
            return
        self._submit_value(self.state.choices[index])

    def submit_choice(self, index: int) -> None:
        if index < 0 or index >= len(self.state.choices):
            return
        self._submit_value(self.state.choices[index])

    def set_visibility(self, visible: bool, *, show_input: bool = True) -> None:
        input_field = self._input()
        option_list = self._options()
        input_field.display = visible and show_input
        option_list.display = visible and not show_input

    def clear_input(self) -> None:
        self._input().value = ""
        self._set_status("")

    def set_status(self, message: str) -> None:
        self._set_status(message)

    def submit_value(self, value: str) -> None:
        if not self._channel:
            return
        self._submit_value(value)

    def _render_prompt(self, request: PromptRequest) -> None:
        label = f"{request.prompt} [{request.key}]"
        self._label().update(label)
        detail = "Required" if request.required else "Optional"
        if request.default:
            detail += f" | Default: {request.default}"
        self._detail().update(detail)
        input_field = self._input()
        option_list = self._options()
        if request.kind in {"string", "secret"}:
            input_field.password = request.kind == "secret"
            input_field.value = request.default or ""
            option_list.clear_options()
            self.set_visibility(True, show_input=True)
            input_field.focus()
        else:
            input_field.value = ""
            option_list.clear_options()
            for choice in request.choices:
                option_list.add_option(choice)
            if request.default and request.default in request.choices:
                option_list.highlighted = request.choices.index(request.default)
            self.set_visibility(True, show_input=False)
            option_list.focus()

    def _submit_value(self, value: str) -> None:
        if self._channel is None:
            return
        self._channel.submit(value)
        self.state.current = None
        self.state.choices = ()
        self.set_visibility(False)
        self._set_status("Awaiting next prompt...")

    def _label(self) -> Static:
        return cast(Static, self._root.query_one(f"#{self._prefix}-prompt-label", Static))

    def _detail(self) -> Static:
        return cast(Static, self._root.query_one(f"#{self._prefix}-prompt-detail", Static))

    def _input(self) -> Input:
        return cast(Input, self._root.query_one(f"#{self._prefix}-input", Input))

    def _options(self) -> OptionList:
        return cast(OptionList, self._root.query_one(f"#{self._prefix}-options", OptionList))

    def _status(self) -> Static:
        return cast(Static, self._root.query_one(f"#{self._prefix}-prompt-status", Static))

    def _set_status(self, message: str) -> None:
        self._status().update(message)


__all__ = ["PromptController", "PromptState"]
