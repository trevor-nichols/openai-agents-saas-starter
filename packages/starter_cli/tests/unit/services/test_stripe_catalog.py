from __future__ import annotations

import pytest

from starter_cli.core import CLIError
from starter_cli.services.stripe.catalog import parse_plan_overrides


def test_parse_plan_overrides_requires_all() -> None:
    with pytest.raises(CLIError):
        parse_plan_overrides(["starter=2000"], require_all=True)
