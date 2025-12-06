"""Resend email adapter for transactional notifications."""

from __future__ import annotations

import asyncio
import math
import time
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final, cast

import resend
from resend import exceptions as resend_exceptions
from resend.http_client_requests import RequestsClient

from app.core.settings import Settings, get_settings
from app.observability.logging import log_event
from app.observability.metrics import observe_email_delivery

_RECIPIENT_LIMIT: Final[int] = 50
_DEFAULT_TIMEOUT_SECONDS: Final[float] = 10.0


class ResendEmailError(RuntimeError):
    """Raised when Resend cannot deliver a transactional email."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


@dataclass(slots=True)
class ResendEmailRequest:
    """High-level request that maps to Resend's send-email payload."""

    to: Sequence[str] | str
    subject: str
    html_body: str | None = None
    text_body: str | None = None
    template_id: str | None = None
    template_variables: Mapping[str, Any] | None = None
    cc: Sequence[str] | str | None = None
    bcc: Sequence[str] | str | None = None
    reply_to: Sequence[str] | str | None = None
    tags: Mapping[str, str] | Sequence[tuple[str, str]] | None = None
    headers: Mapping[str, str] | None = None
    from_email: str | None = None
    category: str | None = None


@dataclass(slots=True)
class ResendEmailSendResult:
    message_id: str


class ResendEmailAdapter:
    """Async-friendly wrapper around the Resend Python SDK."""

    def __init__(
        self,
        *,
        api_key: str,
        default_from: str,
        base_url: str = "https://api.resend.com",
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        normalized_key = (api_key or "").strip()
        normalized_from = (default_from or "").strip()
        if not normalized_key:
            raise ValueError("Resend API key is required.")
        if not normalized_from:
            raise ValueError("Resend default From address is required.")
        normalized_base = (base_url or "https://api.resend.com").strip().rstrip("/")
        if not normalized_base.startswith("http"):
            raise ValueError("Resend base URL must be an HTTP(S) URL.")

        self._api_key = normalized_key
        self._default_from = normalized_from
        self._base_url = normalized_base
        self._timeout = max(timeout_seconds, 1.0)
        self._http_client = RequestsClient(timeout=math.ceil(self._timeout))
        self._configure_sdk()

    def _configure_sdk(self) -> None:
        resend.api_key = self._api_key
        resend.api_url = self._base_url
        resend.default_http_client = self._http_client

    async def send_email(
        self,
        request: ResendEmailRequest,
        *,
        idempotency_key: str | None = None,
    ) -> ResendEmailSendResult:
        payload = self._build_payload(request)
        start = time.perf_counter()
        category = (request.category or _infer_category(request)).lower()
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(self._send_sync, payload, idempotency_key),
                timeout=self._timeout,
            )
        except TimeoutError as exc:  # pragma: no cover - network flake defense
            log_event(
                "notifications.resend_send",
                result="timeout",
                subject=request.subject,
                template_id=request.template_id,
            )
            observe_email_delivery(
                category=category,
                result="timeout",
                duration_seconds=self._timeout,
            )
            raise ResendEmailError("Resend request timed out.", status_code=408) from exc
        except resend_exceptions.ResendError as exc:
            status_code = int(exc.code) if isinstance(exc.code, int | str) else None
            log_event(
                "notifications.resend_send",
                result="error",
                reason=exc.error_type,
                status_code=status_code,
            )
            observe_email_delivery(
                category=category,
                result="error",
                duration_seconds=self._timeout,
            )
            raise ResendEmailError(
                f"Resend API error: {exc.message}",
                status_code=status_code,
                error_code=str(exc.error_type),
            ) from exc
        except Exception as exc:  # pragma: no cover - defensive
            log_event(
                "notifications.resend_send",
                result="error",
                reason="unexpected",
            )
            observe_email_delivery(
                category=category,
                result="error",
                duration_seconds=self._timeout,
            )
            raise ResendEmailError("Unexpected Resend API failure.") from exc

        duration_ms = (time.perf_counter() - start) * 1000
        message_id = str(response.get("id")) if isinstance(response, Mapping) else None
        if not message_id:
            log_event(
                "notifications.resend_send",
                result="error",
                reason="missing_message_id",
            )
            observe_email_delivery(
                category=category,
                result="error",
                duration_seconds=duration_ms / 1000,
            )
            raise ResendEmailError("Resend response did not include an email id.")

        log_event(
            "notifications.resend_send",
            result="success",
            message_id=message_id,
            recipient_count=len(payload["to"]),
            template_id=request.template_id,
            duration_ms=round(duration_ms, 2),
        )
        observe_email_delivery(
            category=category,
            result="success",
            duration_seconds=duration_ms / 1000,
        )
        return ResendEmailSendResult(message_id=message_id)

    @staticmethod
    def _send_sync(
        payload: resend.Emails.SendParams,
        idempotency_key: str | None,
    ) -> Mapping[str, Any]:
        options: resend.Emails.SendOptions | None = (
            {"idempotency_key": idempotency_key} if idempotency_key else None
        )
        return resend.Emails.send(payload, options=options)

    def _build_payload(self, request: ResendEmailRequest) -> resend.Emails.SendParams:
        to = _normalize_recipients(request.to)
        if not to:
            raise ValueError("At least one recipient is required.")
        if len(to) > _RECIPIENT_LIMIT:
            raise ValueError("Resend only supports up to 50 recipients per call.")
        subject = (request.subject or "").strip()
        if not subject:
            raise ValueError("Email subject is required.")

        from_email = (request.from_email or self._default_from).strip()
        payload: dict[str, Any] = {
            "from": from_email,
            "to": to,
            "subject": subject,
        }

        cc = _normalize_recipients(request.cc)
        if cc:
            payload["cc"] = cc
        bcc = _normalize_recipients(request.bcc)
        if bcc:
            payload["bcc"] = bcc
        reply_to = _normalize_recipients(request.reply_to)
        if reply_to:
            payload["reply_to"] = reply_to if len(reply_to) > 1 else reply_to[0]

        headers = _normalize_headers(request.headers)
        if headers:
            payload["headers"] = headers

        tags = _normalize_tags(request.tags)
        if tags:
            payload["tags"] = tags

        if request.template_id:
            if request.html_body or request.text_body:
                raise ValueError("html_body/text_body cannot be provided when using a template.")
            template: dict[str, Any] = {"id": request.template_id}
            if request.template_variables:
                template["variables"] = dict(request.template_variables)
            payload["template"] = template
        else:
            if request.html_body is None and request.text_body is None:
                raise ValueError(
                    "html_body or text_body must be provided when no template is supplied."
                )
            if request.html_body is not None:
                payload["html"] = request.html_body
            if request.text_body is not None:
                payload["text"] = request.text_body

        return cast(resend.Emails.SendParams, payload)


def _normalize_recipients(value: Sequence[str] | str | None) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        candidates = [value]
    else:
        candidates = list(value)
    normalized: list[str] = []
    for item in candidates:
        text = str(item).strip()
        if text:
            normalized.append(text)
    return normalized or None


def _normalize_headers(headers: Mapping[str, str] | None) -> dict[str, str] | None:
    if not headers:
        return None
    normalized: dict[str, str] = {}
    for key, value in headers.items():
        key_str = str(key).strip()
        if not key_str:
            continue
        normalized[key_str] = str(value)
    return normalized or None


def _normalize_tags(
    tags: Mapping[str, str] | Sequence[tuple[str, str]] | None,
) -> list[dict[str, str]] | None:
    if not tags:
        return None
    pairs: Iterable[tuple[str, str]]
    if isinstance(tags, Mapping):
        pairs = tags.items()
    else:
        pairs = tags
    normalized: list[dict[str, str]] = []
    for name, value in pairs:
        name_str = str(name).strip()
        value_str = str(value).strip()
        if not name_str or not value_str:
            continue
        normalized.append({"name": name_str, "value": value_str})
    return normalized or None


def _infer_category(request: ResendEmailRequest) -> str:
    if request.tags:
        if isinstance(request.tags, Mapping):
            return str(request.tags.get("category", "unknown"))
        for name, value in request.tags:
            if name == "category":
                return str(value)
    return "unknown"


_ADAPTER_CACHE: dict[tuple[str, str, str], ResendEmailAdapter] = {}


def get_resend_email_adapter(settings: Settings | None = None) -> ResendEmailAdapter:
    settings = settings or get_settings()
    if not settings.resend_api_key:
        raise RuntimeError("RESEND_API_KEY is required to build the Resend adapter.")
    if not settings.resend_default_from:
        raise RuntimeError("RESEND_DEFAULT_FROM is required to build the Resend adapter.")

    cache_key = (
        settings.resend_api_key.strip(),
        settings.resend_default_from.strip(),
        settings.resend_base_url.strip(),
    )
    cached = _ADAPTER_CACHE.get(cache_key)
    if cached:
        return cached

    adapter = ResendEmailAdapter(
        api_key=settings.resend_api_key,
        default_from=settings.resend_default_from,
        base_url=settings.resend_base_url,
    )
    _ADAPTER_CACHE[cache_key] = adapter
    return adapter


__all__: Final = [
    "ResendEmailAdapter",
    "ResendEmailError",
    "ResendEmailRequest",
    "ResendEmailSendResult",
    "get_resend_email_adapter",
]
