from __future__ import annotations

import argparse

from starter_console.core import CLIContext
from starter_console.workflows.home.hub import HubService


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "home",
        help="Interactive home hub showing stack status and shortcuts.",
    )
    parser.add_argument(
        "--no-tui",
        action="store_true",
        help="Disable the TUI and print a concise summary instead.",
    )
    parser.set_defaults(handler=_handle_home)


def _handle_home(args: argparse.Namespace, ctx: CLIContext) -> int:
    if args.no_tui:
        snapshot = HubService(ctx).load_home()
        _render_summary(ctx, snapshot)
        return 0
    from .ui_loader import load_ui_module

    load_ui_module().StarterTUI(ctx, initial_screen="home").run()
    return 0


def _render_summary(ctx: CLIContext, snapshot) -> None:
    console = ctx.console
    console.rule("Starter Console Home")
    console.info("Probes:")
    for probe in snapshot.probes:
        console.info(f"- {probe.name}: {probe.state.value} ({probe.detail or 'pending'})")
    console.info("Services:")
    for service in snapshot.services:
        console.info(
            f"- {service.label}: {service.state.value} ({service.detail or 'pending'})"
        )


__all__ = ["register"]
