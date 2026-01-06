from __future__ import annotations

from .models import SectionModel


def missing_required(sections: list[SectionModel]) -> list[str]:
    missing: list[str] = []
    for section in sections:
        for field in section.fields:
            if field.is_missing():
                missing.append(field.key)
    return missing


def automation_ready(sections: list[SectionModel]) -> bool:
    return not missing_required(sections)


__all__ = ["automation_ready", "missing_required"]
