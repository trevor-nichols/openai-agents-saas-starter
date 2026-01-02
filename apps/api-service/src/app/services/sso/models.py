"""SSO service DTOs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SsoStartResult:
    authorize_url: str
    state: str


__all__ = ["SsoStartResult"]
