from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

from tests.utils.stream_assertions import (
    assert_code_interpreter_expectations,
    assert_file_search_expectations,
    assert_image_generation_expectations,
    assert_web_search_expectations,
    load_stream_fixture,
)

BASE = Path(__file__).resolve().parent.parent.parent / "fixtures" / "streams"


@pytest.mark.contract
@pytest.mark.parametrize(
    "fixture_name,assert_fn,kwargs",
    [
        ("web_search.ndjson", assert_web_search_expectations, {}),
        ("code_interpreter.ndjson", assert_code_interpreter_expectations, {}),
        ("file_search.ndjson", assert_file_search_expectations, {"expected_store_id": "vs_primary"}),
        ("image_generation.ndjson", assert_image_generation_expectations, {}),
    ],
)
def test_stream_goldens(
    fixture_name: str, assert_fn: Callable[..., None], kwargs: dict[str, object]
):
    path = BASE / fixture_name
    if not path.exists():
        pytest.skip(f"Fixture missing: {path}")

    events = load_stream_fixture(path)
    assert_fn(events, **kwargs)
