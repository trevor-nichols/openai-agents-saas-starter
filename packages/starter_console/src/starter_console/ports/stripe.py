from __future__ import annotations

from typing import Protocol


class StripeWebhookCapturePort(Protocol):
    def capture_webhook_secret(self, *, forward_url: str) -> str: ...


__all__ = ["StripeWebhookCapturePort"]
