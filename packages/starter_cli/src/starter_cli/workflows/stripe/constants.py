from __future__ import annotations

from starter_cli.services.stripe_status import REQUIRED_ENV_KEYS

AGGREGATED_KEYS = (*REQUIRED_ENV_KEYS, "DATABASE_URL")
DEFAULT_WEBHOOK_FORWARD_URL = "http://localhost:8000/api/v1/webhooks/stripe"
DISPATCH_STATUS_CHOICES = ("pending", "in_progress", "failed", "completed")

__all__ = ["AGGREGATED_KEYS", "DEFAULT_WEBHOOK_FORWARD_URL", "DISPATCH_STATUS_CHOICES"]
