from __future__ import annotations

from collections.abc import Iterable

from textual.widgets import Tree
from textual.widgets._tree import TreeNode

from .sections import NavGroupSpec, SectionSpec


class NavTree(Tree[object]):
    def __init__(self, groups: Iterable[NavGroupSpec], **kwargs) -> None:
        super().__init__("Navigation", **kwargs)
        self.show_root = False
        self._groups = tuple(groups)
        self._node_by_key: dict[str, TreeNode[object]] = {}
        self._group_nodes: dict[str, TreeNode[object]] = {}

    def on_mount(self) -> None:
        self._build_tree()

    def select_section(self, key: str) -> None:
        node = self._node_by_key.get(key)
        if node is None:
            return
        self.select_node(node)

    def select_group(self, key: str) -> None:
        node = self._group_nodes.get(key)
        if node is None:
            return
        self.select_node(node)

    def expand_group(self, key: str) -> None:
        node = self._group_nodes.get(key)
        if node is None:
            return
        node.expand()

    def section_for_node(self, node: TreeNode[object]) -> SectionSpec | None:
        data = node.data
        return data if isinstance(data, SectionSpec) else None

    def _build_tree(self) -> None:
        root = self.root
        root.expand()
        for group in self._groups:
            group_node = root.add(group.label, expand=not group.collapsed, data=group)
            self._group_nodes[group.key] = group_node
            for section in group.items:
                item_node = group_node.add_leaf(section.label, data=section)
                self._node_by_key[section.key] = item_node


__all__ = ["NavTree"]
