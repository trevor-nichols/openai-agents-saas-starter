from __future__ import annotations

import pytest

from starter_cli.core import CLIError
from starter_cli.services.backend_scripts import extract_json_payload


def test_extract_json_payload_reads_last_valid_line() -> None:
    stdout = "noise\n{\"ok\": false}\n{\"result\": \"done\"}\n"
    payload = extract_json_payload(stdout, required_keys=["result"])
    assert payload["result"] == "done"


def test_extract_json_payload_requires_keys() -> None:
    with pytest.raises(CLIError):
        extract_json_payload("{\"ok\": true}", required_keys=["result"])
