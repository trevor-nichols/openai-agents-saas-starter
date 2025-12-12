"""Pydantic schemas for contact form submissions."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.api.models.common import SuccessResponse
from app.services.contact_service import MAX_MESSAGE_LENGTH


class ContactSubmissionRequest(BaseModel):
    name: str | None = Field(
        default=None,
        max_length=120,
        description="Full name of the submitter.",
    )
    email: EmailStr = Field(description="Reply-to email address for the requester.")
    company: str | None = Field(
        default=None,
        max_length=120,
        description="Company or organization (optional).",
    )
    topic: str | None = Field(
        default=None,
        max_length=80,
        description="Optional topic or subject to aid routing.",
    )
    message: str = Field(
        description="The body of the request.",
        min_length=10,
        max_length=MAX_MESSAGE_LENGTH,
    )
    honeypot: str | None = Field(
        default=None,
        max_length=64,
        description="Spam trap field; should remain empty.",
    )


class ContactSubmissionResponse(BaseModel):
    reference_id: str = Field(description="Correlation identifier for the submission.")
    delivered: bool = Field(description="Whether the email was delivered via Resend.")
    message_id: str | None = Field(
        default=None,
        description="Resend message id when available.",
    )
    suppressed: bool = Field(
        default=False,
        description="True when the submission was accepted but intentionally skipped (honeypot).",
    )


class ContactSubmissionSuccessResponse(SuccessResponse):
    data: ContactSubmissionResponse | None = Field(
        default=None,
        description="Contact submission result payload.",
    )
