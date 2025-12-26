from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from starter_console.ui.nav_tree import NavTree
from starter_console.ui.sections import NavGroupSpec, SectionSpec


class NavTreeApp(App[None]):
    def __init__(self, groups: tuple[NavGroupSpec, ...]) -> None:
        super().__init__()
        self._groups = groups

    def compose(self) -> ComposeResult:
        yield NavTree(self._groups)


@pytest.mark.asyncio
async def test_nav_tree_builds_groups_and_sections() -> None:
    groups = (
        NavGroupSpec(
            key="overview",
            label="Overview",
            description="Overview group",
            items=(
                SectionSpec(
                    key="home",
                    label="Home",
                    description="Home pane",
                    detail="Home detail",
                    shortcut="H",
                ),
                SectionSpec(
                    key="setup",
                    label="Setup",
                    description="Setup pane",
                    detail="Setup detail",
                    shortcut="S",
                ),
            ),
        ),
        NavGroupSpec(
            key="advanced",
            label="Advanced",
            description="Advanced group",
            items=(
                SectionSpec(
                    key="util",
                    label="Util",
                    description="Util pane",
                    detail="Util detail",
                    shortcut="U",
                ),
            ),
            collapsed=True,
        ),
    )
    app = NavTreeApp(groups)

    async with app.run_test() as pilot:
        await pilot.pause()
        tree = app.query_one(NavTree)
        root = tree.root
        assert len(root.children) == 2

        overview_node = root.children[0]
        advanced_node = root.children[1]
        assert overview_node.data == groups[0]
        assert advanced_node.data == groups[1]
        assert overview_node.is_expanded is True
        assert advanced_node.is_expanded is False
        assert len(overview_node.children) == 2
        assert len(advanced_node.children) == 1


@pytest.mark.asyncio
async def test_nav_tree_selects_section_and_group() -> None:
    groups = (
        NavGroupSpec(
            key="overview",
            label="Overview",
            description="Overview group",
            items=(
                SectionSpec(
                    key="home",
                    label="Home",
                    description="Home pane",
                    detail="Home detail",
                    shortcut="H",
                ),
            ),
        ),
    )
    app = NavTreeApp(groups)

    async with app.run_test() as pilot:
        await pilot.pause()
        tree = app.query_one(NavTree)
        tree.select_section("home")
        assert tree.cursor_node is not None
        selected = tree.section_for_node(tree.cursor_node)
        assert selected is not None
        assert selected.key == "home"

        tree.select_group("overview")
        assert tree.cursor_node is not None
        assert tree.cursor_node.data == groups[0]
