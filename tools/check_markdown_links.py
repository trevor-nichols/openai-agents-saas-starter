#!/usr/bin/env python3
"""
Internal Markdown link checker (offline).

Validates that relative links and repo-relative "@path" links resolve to existing files.
This intentionally does NOT fetch or validate external URLs.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


SKIP_SCHEMES = (
    "http://",
    "https://",
    "mailto:",
    "tel:",
    "data:",
    "javascript:",
)

LINK_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)|\[[^\]]*\]\(([^)]+)\)")
FENCE_RE = re.compile(r"^\s*```")


@dataclass(frozen=True)
class LinkError:
    file: Path
    line: int
    raw_target: str
    resolved: Path
    reason: str


def iter_markdown_files(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        if p.is_file() and p.suffix.lower() == ".md":
            out.append(p)
            continue
        if p.is_dir():
            out.extend(sorted(p.rglob("*.md")))
    return out


def strip_fragment_and_query(target: str) -> str:
    # Split in URL order: query first, then fragment.
    target = target.split("?", 1)[0]
    target = target.split("#", 1)[0]
    return target


def should_skip_target(raw: str) -> bool:
    raw = raw.strip()
    if not raw:
        return True
    if raw.startswith("#"):
        return True
    lower = raw.lower()
    if lower.startswith(SKIP_SCHEMES):
        return True
    if "://" in lower:
        return True
    if lower.startswith("/"):
        # Site-root links are application-specific; do not validate offline.
        return True
    return False


def resolve_target(repo_root: Path, source_file: Path, raw_target: str) -> Path | None:
    target = raw_target.strip()
    if should_skip_target(target):
        return None

    target = strip_fragment_and_query(target)
    if not target:
        return None

    if target.startswith("@"):
        return (repo_root / target[1:]).resolve()

    return (source_file.parent / target).resolve()


def validate_file_target(resolved: Path) -> tuple[bool, Path]:
    if resolved.exists():
        return True, resolved

    # Common doc pattern: linking without ".md"
    if resolved.suffix == "" and resolved.with_suffix(".md").exists():
        return True, resolved.with_suffix(".md")

    # Another common pattern: linking to a directory page (".../foo/" -> ".../foo/README.md")
    if resolved.suffix == "" and resolved.as_posix().endswith("/"):
        candidate = resolved / "README.md"
        if candidate.exists():
            return True, candidate

    return False, resolved


def scan_file(repo_root: Path, file_path: Path) -> list[LinkError]:
    errors: list[LinkError] = []
    in_fence = False
    text = file_path.read_text(encoding="utf-8", errors="replace")
    for i, line in enumerate(text.splitlines(), start=1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        for match in LINK_RE.finditer(line):
            raw_target = (match.group(1) or match.group(2) or "").strip()
            resolved = resolve_target(repo_root, file_path, raw_target)
            if resolved is None:
                continue

            ok, canonical = validate_file_target(resolved)
            if ok:
                continue

            errors.append(
                LinkError(
                    file=file_path,
                    line=i,
                    raw_target=raw_target,
                    resolved=canonical,
                    reason="target does not exist",
                )
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline markdown link checker.")
    parser.add_argument(
        "paths",
        nargs="*",
        default=["docs", "README.md"],
        help="Files/directories to scan (default: docs README.md).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    scan_paths = [Path(p).resolve() if Path(p).is_absolute() else (repo_root / p).resolve() for p in args.paths]
    md_files = iter_markdown_files(scan_paths)

    all_errors: list[LinkError] = []
    for md in md_files:
        all_errors.extend(scan_file(repo_root, md))

    if not all_errors:
        return 0

    for err in all_errors:
        rel = err.file.resolve().relative_to(repo_root)
        print(f"{rel}:{err.line}: invalid link target {err.raw_target!r} -> {err.resolved} ({err.reason})")

    print(f"\nFound {len(all_errors)} invalid markdown link(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

