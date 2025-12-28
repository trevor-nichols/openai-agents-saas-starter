"""Database connectivity and billing configuration."""
from __future__ import annotations

import json
from collections.abc import Mapping

from pydantic import BaseModel, Field, field_validator

from .utils import normalize_url


class DatabaseAndBillingSettingsMixin(BaseModel):
    database_url: str | None = Field(
        default=None,
        description="Async SQLAlchemy URL for the primary Postgres database",
        alias="DATABASE_URL",
    )
    database_pool_size: int = Field(default=5, description="SQLAlchemy async pool size")
    database_max_overflow: int = Field(
        default=10,
        description="Maximum overflow connections for the SQLAlchemy pool",
    )
    database_pool_recycle: int = Field(
        default=1800,
        description="Seconds before recycling idle connections",
    )
    database_pool_timeout: float = Field(
        default=30.0,
        description="Seconds to wait for a connection from the pool",
    )
    database_health_timeout: float = Field(
        default=5.0,
        description="Timeout for database health checks (seconds)",
    )
    database_echo: bool = Field(
        default=False,
        description="Enable SQLAlchemy engine echo for debugging",
    )
    enable_billing: bool = Field(
        default=False,
        description="Expose billing features and APIs once subscriptions are implemented",
    )
    enable_billing_stream: bool = Field(
        default=False,
        description="Enable real-time billing event streaming endpoints",
        alias="ENABLE_BILLING_STREAM",
    )
    enable_billing_retry_worker: bool = Field(
        default=True,
        description="Run the Stripe dispatch retry worker inside this process",
        alias="ENABLE_BILLING_RETRY_WORKER",
    )
    enable_billing_stream_replay: bool = Field(
        default=True,
        description="Replay processed Stripe events into Redis billing streams during startup",
        alias="ENABLE_BILLING_STREAM_REPLAY",
    )
    billing_retry_deployment_mode: str = Field(
        default="inline",
        description="Documented deployment target for the Stripe retry worker (inline/dedicated).",
        alias="BILLING_RETRY_DEPLOYMENT_MODE",
    )
    auto_run_migrations: bool = Field(
        default=False,
        description="Automatically run Alembic migrations on startup (dev convenience)",
    )
    billing_events_redis_url: str | None = Field(
        default=None,
        description="Redis URL used for billing event pub/sub (defaults to REDIS_URL when unset)",
        alias="BILLING_EVENTS_REDIS_URL",
    )
    stripe_secret_key: str | None = Field(
        default=None,
        description="Stripe secret API key (sk_live_*/sk_test_*).",
        alias="STRIPE_SECRET_KEY",
    )
    stripe_webhook_secret: str | None = Field(
        default=None,
        description="Stripe webhook signing secret (whsec_*).",
        alias="STRIPE_WEBHOOK_SECRET",
    )
    stripe_portal_return_url: str | None = Field(
        default=None,
        description="Return URL for Stripe billing portal sessions.",
        alias="STRIPE_PORTAL_RETURN_URL",
    )
    stripe_product_price_map: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Mapping of billing plan codes to Stripe price IDs. Provide as JSON or comma-delimited "
            "entries such as 'starter=price_123,pro=price_456'."
        ),
        alias="STRIPE_PRODUCT_PRICE_MAP",
    )

    def resolve_billing_events_redis_url(self) -> str | None:
        redis_source = getattr(self, "redis_url", None)
        return normalize_url(self.billing_events_redis_url) or normalize_url(redis_source)

    def resolve_stripe_portal_return_url(self) -> str:
        base_url = getattr(self, "app_public_url", "http://localhost:3000")
        default_url = f"{str(base_url).rstrip('/')}/billing"
        return normalize_url(self.stripe_portal_return_url) or default_url

    def required_stripe_envs_missing(self) -> list[str]:
        missing: list[str] = []
        if not (self.stripe_secret_key and self.stripe_secret_key.strip()):
            missing.append("STRIPE_SECRET_KEY")
        if not (self.stripe_webhook_secret and self.stripe_webhook_secret.strip()):
            missing.append("STRIPE_WEBHOOK_SECRET")
        if not self.stripe_product_price_map:
            missing.append("STRIPE_PRODUCT_PRICE_MAP")
        return missing

    def stripe_configuration_summary(self) -> dict[str, object]:
        price_map = self.stripe_product_price_map or {}
        plan_codes = sorted(price_map.keys())
        redis_source = "<unset>"
        if self.billing_events_redis_url:
            redis_source = "BILLING_EVENTS_REDIS_URL"
        elif self.resolve_billing_events_redis_url():
            redis_source = "REDIS_URL"
        return {
            "stripe_secret_key": self._mask_secret(self.stripe_secret_key),
            "stripe_webhook_secret": self._mask_secret(self.stripe_webhook_secret),
            "plans_configured": plan_codes,
            "plan_count": len(plan_codes),
            "billing_stream_enabled": self.enable_billing_stream,
            "billing_stream_backend": redis_source if self.enable_billing_stream else "disabled",
            "stripe_portal_return_url": self.resolve_stripe_portal_return_url(),
        }

    @staticmethod
    def _mask_secret(value: str | None) -> str:
        if value is None:
            return "<missing>"
        cleaned = value.strip()
        if not cleaned:
            return "<missing>"
        if len(cleaned) <= 4:
            return "*" * len(cleaned)
        prefix = cleaned[:2]
        suffix = cleaned[-4:]
        middle_length = max(len(cleaned) - len(prefix) - len(suffix), 3)
        return f"{prefix}{'*' * middle_length}{suffix}"

    @field_validator("stripe_product_price_map", mode="before")
    @classmethod
    def _parse_price_map(
        cls, value: Mapping[str, str] | str | None
    ) -> dict[str, str]:
        if value is None or value == {}:
            return {}
        if isinstance(value, Mapping):
            return {str(plan): str(price) for plan, price in value.items()}
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return {}
            try:
                parsed_json = json.loads(text)
            except json.JSONDecodeError:
                return cls._parse_price_map_csv(text)
            if not isinstance(parsed_json, dict):
                raise ValueError("STRIPE_PRODUCT_PRICE_MAP JSON payload must decode to a mapping.")
            return {str(plan): str(price) for plan, price in parsed_json.items()}
        raise ValueError(
            "STRIPE_PRODUCT_PRICE_MAP must be a mapping, JSON string, or comma-delimited list."
        )

    @staticmethod
    def _parse_price_map_csv(text: str) -> dict[str, str]:
        parsed: dict[str, str] = {}
        for item in text.split(","):
            entry = item.strip()
            if not entry:
                continue
            if "=" in entry:
                key, price = entry.split("=", 1)
            elif ":" in entry:
                key, price = entry.split(":", 1)
            else:
                raise ValueError(
                    "Invalid STRIPE_PRODUCT_PRICE_MAP entry. Use key=value or JSON dict."
                )
            parsed[key] = price
        return parsed

    @field_validator("stripe_product_price_map")
    @classmethod
    def _validate_price_map(cls, value: dict[str, str]) -> dict[str, str]:
        cleaned: dict[str, str] = {}
        for plan_code, price_id in value.items():
            plan = str(plan_code).strip()
            price = str(price_id).strip()
            if not plan or not price:
                raise ValueError(
                    "Stripe product price map entries require non-empty plan codes and price IDs."
                )
            cleaned[plan] = price
        return cleaned
