"""Generate dependency graphs for modules inside `app.services`."""

from __future__ import annotations

import argparse
import ast
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Mapping


DEFAULT_PREFIX = "app.services"
DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "apps" / "api-service" / "app" / "services"


def main() -> None:
    args = _parse_args()
    root = Path(args.root or DEFAULT_ROOT).resolve()
    if not root.exists():
        raise SystemExit(f"Services root not found: {root}")

    modules = _discover_modules(root, args.prefix)
    if not modules:
        raise SystemExit(f"No modules discovered under {root}")

    adjacency = {
        module: _collect_dependencies(module, path, modules, args.prefix)
        for module, path in modules.items()
    }

    if args.format == "json":
        output = _render_json(adjacency)
    elif args.format == "dot":
        output = _render_dot(adjacency)
    else:
        output = _render_markdown(adjacency)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=str,
        help="Path to the services directory (defaults to apps/api-service/src/app/services)",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default=DEFAULT_PREFIX,
        help="Module prefix to scope (defaults to app.services)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=("markdown", "json", "dot"),
        default="markdown",
        help="Render format for the dependency graph",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Optional path to write the rendered graph",
    )
    return parser.parse_args()


def _discover_modules(root: Path, prefix: str) -> Dict[str, Path]:
    modules: Dict[str, Path] = {}
    for path in root.rglob("*.py"):
        if path.name == "__pycache__":
            continue
        relative = path.relative_to(root)
        module = _module_name_from_path(relative, prefix)
        modules[module] = path
    return modules


def _module_name_from_path(relative: Path, prefix: str) -> str:
    stem = relative.with_suffix("")
    parts = [part for part in stem.parts if part != "__pycache__"]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    if parts:
        return ".".join([prefix, *parts])
    return prefix


def _collect_dependencies(
    module_name: str,
    file_path: Path,
    modules: Mapping[str, Path],
    prefix: str,
) -> set[str]:
    dependencies: set[str] = set()
    modules_set = set(modules.keys())
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                dep = alias.name
                if dep in modules_set:
                    dependencies.add(dep)
        elif isinstance(node, ast.ImportFrom):
            resolved = _resolve_import_from(node, module_name)
            wildcard = any(alias.name == "*" for alias in node.names)
            candidates: set[str] = set()
            if wildcard and resolved and resolved in modules_set:
                candidates.add(resolved)
            if resolved:
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    candidate = f"{resolved}.{alias.name}"
                    if candidate in modules_set:
                        candidates.add(candidate)
            else:
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    candidate = alias.name
                    if candidate in modules_set:
                        candidates.add(candidate)
            if not candidates and resolved and resolved in modules_set:
                candidates.add(resolved)
            for candidate in candidates:
                if candidate.startswith(prefix):
                    dependencies.add(candidate)

    dependencies.discard(module_name)
    return dependencies


def _resolve_import_from(node: ast.ImportFrom, current_module: str) -> str | None:
    if node.level == 0:
        return node.module
    current_parts = current_module.split(".")
    if node.level > len(current_parts):
        base_parts: list[str] = []
    else:
        base_parts = current_parts[: -node.level]
    if node.module:
        base_parts.extend(node.module.split("."))
    return ".".join(part for part in base_parts if part)


def _render_markdown(graph: Mapping[str, set[str]]) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    nodes = sorted(graph.keys())
    reverse = _reverse_graph(graph)

    lines = ["# Services Dependency Snapshot", f"_Generated: {timestamp}_", ""]
    lines.append("## Summary")
    lines.append(f"- Total modules scanned: {len(nodes)}")
    zero_deps = [node for node, deps in graph.items() if not deps]
    zero_rev = [node for node, deps in reverse.items() if not deps]
    lines.append(f"- Modules with no internal deps: {len(zero_deps)}")
    lines.append(f"- Modules not referenced internally: {len(zero_rev)}")

    lines.append("")
    lines.append("### Top Fan-Out (depends on most peers)")
    for module, deps in _top_k(graph.items(), key=lambda item: len(item[1])):
        lines.append(f"- `{module}` → {len(deps)} modules")

    lines.append("")
    lines.append("### Top Fan-In (referenced by most peers)")
    for module, refs in _top_k(reverse.items(), key=lambda item: len(item[1])):
        lines.append(f"- `{module}` ← {len(refs)} modules")

    lines.append("")
    lines.append("## Adjacency")
    lines.append("| Module | Internal Dependencies |")
    lines.append("| --- | --- |")
    for module in nodes:
        deps = sorted(graph[module])
        dep_value = "<br>".join(f"`{dep}`" for dep in deps) if deps else "—"
        lines.append(f"| `{module}` | {dep_value} |")

    lines.append("")
    lines.append("## Reverse References")
    lines.append("| Module | Referenced By |")
    lines.append("| --- | --- |")
    for module in nodes:
        refs = sorted(reverse[module])
        ref_value = "<br>".join(f"`{ref}`" for ref in refs) if refs else "—"
        lines.append(f"| `{module}` | {ref_value} |")

    lines.append("")
    lines.append("> Generated by `tools/moduleviz.py`.")
    return "\n".join(lines)


def _render_json(graph: Mapping[str, set[str]]) -> str:
    serializable = {module: sorted(deps) for module, deps in graph.items()}
    return json.dumps(serializable, indent=2, sort_keys=True)


def _render_dot(graph: Mapping[str, set[str]]) -> str:
    lines = ["digraph services {"]
    for module in sorted(graph.keys()):
        safe_name = module.replace(".", "_")
        lines.append(f"  {safe_name} [label=\"{module}\"]; ")
    for src, deps in graph.items():
        for dst in deps:
            lines.append(
                f"  {src.replace('.', '_')} -> {dst.replace('.', '_')};"
            )
    lines.append("}")
    return "\n".join(lines)


def _reverse_graph(graph: Mapping[str, set[str]]) -> Dict[str, set[str]]:
    reverse: Dict[str, set[str]] = {module: set() for module in graph}
    for src, deps in graph.items():
        for dst in deps:
            if dst in reverse:
                reverse[dst].add(src)
    return reverse


def _top_k(items: Iterable[tuple[str, set[str]]], key, limit: int = 5):
    sorted_items = sorted(items, key=lambda item: (key(item), item[0]), reverse=True)
    return sorted_items[:limit]


if __name__ == "__main__":
    main()
