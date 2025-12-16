from __future__ import annotations

from typing import Any

from ..streaming import StreamNotice

_SENSITIVE_KEY_SUBSTRINGS: tuple[str, ...] = (
    "api_key",
    "apikey",
    "authorization",
    "token",
    "secret",
    "password",
    "passphrase",
    "bearer",
    "client_secret",
    "access_token",
    "refresh_token",
    "id_token",
)


def _is_sensitive_key(key: str) -> bool:
    key_lower = key.lower()
    return any(part in key_lower for part in _SENSITIVE_KEY_SUBSTRINGS)


def truncate_string(*, value: str, path: str, max_chars: int) -> tuple[str, StreamNotice | None]:
    if len(value) <= max_chars:
        return value, None
    return (
        value[:max_chars],
        StreamNotice(
            type="truncated",
            path=path,
            message="Large content was truncated for streaming stability.",
        ),
    )


def sanitize_json(obj: Any, *, path: str, max_string_chars: int) -> tuple[Any, list[StreamNotice]]:
    notices: list[StreamNotice] = []
    if isinstance(obj, dict):
        sanitized: dict[str, Any] = {}
        for key, value in obj.items():
            child_path = f"{path}.{key}" if path else key
            if _is_sensitive_key(key):
                sanitized[key] = "<redacted>"
                notices.append(
                    StreamNotice(
                        type="redacted",
                        path=child_path,
                        message="Some fields were redacted for safety.",
                    )
                )
                continue
            coerced, child_notices = sanitize_json(
                value,
                path=child_path,
                max_string_chars=max_string_chars,
            )
            sanitized[key] = coerced
            notices.extend(child_notices)
        return sanitized, notices

    if isinstance(obj, list):
        sanitized_list: list[Any] = []
        for idx, value in enumerate(obj):
            child_path = f"{path}[{idx}]"
            coerced, child_notices = sanitize_json(
                value, path=child_path, max_string_chars=max_string_chars
            )
            sanitized_list.append(coerced)
            notices.extend(child_notices)
        return sanitized_list, notices

    if isinstance(obj, str):
        truncated, notice = truncate_string(value=obj, path=path, max_chars=max_string_chars)
        if notice:
            notices.append(notice)
        return truncated, notices

    return obj, notices
