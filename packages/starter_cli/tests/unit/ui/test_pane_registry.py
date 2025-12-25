from __future__ import annotations

import pytest

from starter_cli.core import CLIContext
from starter_cli.ui.app import StarterTUI
from starter_cli.ui.panes.registry import build_panes
from starter_cli.ui.sections import NAV_GROUPS, NavGroupSpec, SectionSpec, iter_sections
from starter_cli.workflows.home.hub import HubService


def test_build_panes_raises_for_missing_factory(tmp_path) -> None:
    ctx = CLIContext(project_root=tmp_path)
    hub = HubService(ctx)
    groups = (
        NavGroupSpec(
            key="overview",
            label="Overview",
            description="Missing pane group",
            items=(
                SectionSpec(
                    key="missing-pane",
                    label="Missing Pane",
                    description="No factory for this pane.",
                    detail="Placeholder.",
                    shortcut="M",
                ),
            ),
        ),
    )
    with pytest.raises(RuntimeError, match="Missing pane factory"):
        build_panes(ctx, groups, hub=hub)


def test_section_shortcuts_are_unique_and_unreserved() -> None:
    reserved = {binding.key for binding in StarterTUI.BINDINGS}
    seen: set[str] = set()
    for section in iter_sections(NAV_GROUPS):
        key = section.shortcut.strip().lower()
        assert key, f"Missing shortcut for section '{section.key}'."
        assert key not in reserved, f"Shortcut '{key}' conflicts with reserved bindings."
        assert key not in seen, f"Duplicate shortcut '{key}' found."
        seen.add(key)
