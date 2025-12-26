"""Shared helpers for pytest stripe_replay markers and console flags."""

from __future__ import annotations

import pytest

_STRIPE_SKIP_REASON = "Stripe replay tests require --enable-stripe-replay."


def configure_stripe_replay_option(parser: pytest.Parser) -> None:
    """Register the opt-in flag for replay suites."""

    parser.addoption(
        "--enable-stripe-replay",
        action="store_true",
        default=False,
        help=(
            "Run tests marked with @pytest.mark.stripe_replay "
            "(requires Postgres/Stripe fixtures)."
        ),
    )


def register_stripe_replay_marker(config: pytest.Config) -> None:
    """Make pytest aware of the custom marker regardless of test location."""

    config.addinivalue_line(
        "markers",
        "stripe_replay: exercises Stripe webhook replay + billing stream flows; "
        "requires external fixtures.",
    )


def skip_stripe_replay_if_disabled(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip tests unless --enable-stripe-replay was provided."""

    if config.getoption("--enable-stripe-replay"):
        return

    skip_marker = pytest.mark.skip(reason=_STRIPE_SKIP_REASON)
    for item in items:
        if "stripe_replay" in item.keywords:
            item.add_marker(skip_marker)
