from __future__ import annotations

import threading
import time

from starter_cli.ui.prompting import PromptChannel, PromptRequest, TextualPromptPort


def test_textual_prompt_port_prefill_string() -> None:
    channel = PromptChannel()
    prompt = TextualPromptPort(prefill={"FOO": "bar"}, channel=channel)

    value = prompt.prompt_string(key="foo", prompt="Label", default=None, required=True)

    assert value == "bar"


def test_prompt_channel_roundtrip() -> None:
    channel = PromptChannel()
    results: list[str] = []

    def worker() -> None:
        results.append(
            channel.request(
                PromptRequest(
                    kind="string",
                    key="COLOR",
                    prompt="Favorite color",
                    default=None,
                    required=True,
                )
            )
        )

    thread = threading.Thread(target=worker)
    thread.start()

    request = None
    for _ in range(50):
        request = channel.poll()
        if request is not None:
            break
        time.sleep(0.01)

    assert request is not None
    channel.submit("blue")
    thread.join(timeout=1)

    assert results == ["blue"]
