"""Contact form submission service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final
from uuid import uuid4

from pydantic import EmailStr

from app.core.config import Settings, get_settings
from app.infrastructure.notifications import (
    ResendEmailAdapter,
    ResendEmailError,
    ResendEmailRequest,
    get_resend_email_adapter,
)
from app.observability.logging import log_event

MAX_MESSAGE_LENGTH: Final[int] = 2000
MAX_NAME_LENGTH: Final[int] = 120
MAX_COMPANY_LENGTH: Final[int] = 120
MAX_TOPIC_LENGTH: Final[int] = 80


class ContactSubmissionError(RuntimeError):
    """Base class for contact submission failures."""


class ContactDeliveryError(ContactSubmissionError):
    """Raised when the notification cannot be delivered."""


@dataclass(slots=True)
class ContactSubmissionResult:
    reference_id: str
    delivered: bool
    message_id: str | None = None
    suppressed: bool = False


class ContactService:
    """Routes validated contact submissions to Resend (or logs when disabled)."""

    def __init__(
        self,
        *,
        settings: Settings,
        email_adapter: ResendEmailAdapter | None,
    ) -> None:
        self._settings = settings
        self._adapter = email_adapter

    async def submit_contact(
        self,
        *,
        name: str | None,
        email: EmailStr,
        company: str | None,
        topic: str | None,
        message: str,
        ip_address: str | None,
        user_agent: str | None,
        honeypot: str | None = None,
    ) -> ContactSubmissionResult:
        reference_id = str(uuid4())
        normalized_honeypot = (honeypot or "").strip()
        if normalized_honeypot:
            log_event(
                "contact.submission.suppressed",
                reason="honeypot",
                ip_address=ip_address or "unknown",
                user_agent=(user_agent or "").strip() or "unknown",
            )
            return ContactSubmissionResult(
                reference_id=reference_id,
                delivered=False,
                message_id=None,
                suppressed=True,
            )

        submission = _normalize_submission(
            name=name,
            email=str(email),
            company=company,
            topic=topic,
            message=message,
            ip_address=ip_address,
            user_agent=user_agent,
            reference_id=reference_id,
        )

        if not self._adapter or not self._settings.enable_resend_email_delivery:
            log_event(
                "contact.submission.accepted",
                delivered=False,
                reference_id=reference_id,
                email=submission["email"],
            )
            return ContactSubmissionResult(reference_id=reference_id, delivered=False)

        request = _build_resend_request(
            submission=submission,
            settings=self._settings,
        )
        try:
            result = await self._adapter.send_email(request)
        except ResendEmailError as exc:
            log_event(
                "contact.submission.failed",
                reference_id=reference_id,
                reason=getattr(exc, "error_code", None) or "resend_error",
            )
            raise ContactDeliveryError("Failed to deliver contact email.") from exc

        log_event(
            "contact.submission.delivered",
            reference_id=reference_id,
            message_id=result.message_id,
        )
        return ContactSubmissionResult(
            reference_id=reference_id,
            delivered=True,
            message_id=result.message_id,
        )


def _normalize_submission(
    *,
    name: str | None,
    email: str,
    company: str | None,
    topic: str | None,
    message: str,
    ip_address: str | None,
    user_agent: str | None,
    reference_id: str,
) -> dict[str, str]:
    normalized_name = (name or "").strip()[:MAX_NAME_LENGTH]
    normalized_company = (company or "").strip()[:MAX_COMPANY_LENGTH]
    normalized_topic = (topic or "").strip()[:MAX_TOPIC_LENGTH]
    normalized_message = (message or "").strip()
    if len(normalized_message) > MAX_MESSAGE_LENGTH:
        normalized_message = normalized_message[:MAX_MESSAGE_LENGTH].rstrip() + "…"

    return {
        "name": normalized_name or "Anonymous",
        "email": email.strip(),
        "company": normalized_company or "—",
        "topic": normalized_topic or "General",
        "message": normalized_message,
        "ip_address": (ip_address or "unknown").strip(),
        "user_agent": (user_agent or "unknown").strip(),
        "reference_id": reference_id,
    }


def _build_resend_request(
    *,
    submission: dict[str, str],
    settings: Settings,
) -> ResendEmailRequest:
    subject_prefix = settings.contact_email_subject_prefix.strip()
    subject = f"{subject_prefix} {submission['topic']}".strip()
    text_lines = [
        f"From: {submission['name']} <{submission['email']}>",
        f"Company: {submission['company']}",
        f"Topic: {submission['topic']}",
        f"Reference: {submission['reference_id']}",
        f"IP: {submission['ip_address']}",
        f"User-Agent: {submission['user_agent']}",
        "",
        submission["message"],
    ]
    text_body = "\n".join(text_lines)

    template_id = settings.contact_email_template_id
    if template_id:
        return ResendEmailRequest(
            to=settings.contact_email_recipients,
            subject=subject,
            template_id=template_id,
            template_variables=submission,
            reply_to=[submission["email"]],
            tags={"category": "contact", "topic": submission["topic"]},
            headers={"X-Contact-Ref": submission["reference_id"]},
            category="contact",
        )

    return ResendEmailRequest(
        to=settings.contact_email_recipients,
        subject=subject,
        text_body=text_body,
        reply_to=[submission["email"]],
        tags={"category": "contact", "topic": submission["topic"]},
        headers={"X-Contact-Ref": submission["reference_id"]},
        category="contact",
    )


def build_contact_service(
    *,
    settings: Settings | None = None,
    email_adapter: ResendEmailAdapter | None = None,
) -> ContactService:
    resolved_settings = settings or get_settings()
    adapter = email_adapter
    if adapter is None and resolved_settings.enable_resend_email_delivery:
        adapter = get_resend_email_adapter(resolved_settings)
    return ContactService(settings=resolved_settings, email_adapter=adapter)


def get_contact_service() -> ContactService:
    from app.bootstrap.container import get_container

    container = get_container()
    if container.contact_service is None:
        container.contact_service = build_contact_service()
    return container.contact_service


__all__ = [
    "ContactService",
    "ContactDeliveryError",
    "ContactSubmissionError",
    "ContactSubmissionResult",
    "build_contact_service",
    "get_contact_service",
]
