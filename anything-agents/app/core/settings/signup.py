"""Tenant signup and onboarding policies."""
from __future__ import annotations

import os

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

from .base import SignupAccessPolicyLiteral, signup_policy_logger


class SignupSettingsMixin(BaseModel):
    signup_access_policy: SignupAccessPolicyLiteral = Field(
        default="invite_only",
        description="Signup exposure posture: public, invite_only, or approval.",
        alias="SIGNUP_ACCESS_POLICY",
    )
    allow_public_signup: bool = Field(
        default=True,
        description=(
            "Allow unauthenticated tenants to self-register via /auth/register. Derived from "
            "SIGNUP_ACCESS_POLICY."
        ),
        alias="ALLOW_PUBLIC_SIGNUP",
    )
    allow_signup_trial_override: bool = Field(
        default=False,
        description=(
            "Permit /auth/register callers to request trial periods up to the plan/default cap."
        ),
    )
    signup_rate_limit_per_hour: int = Field(
        default=20,
        description="Maximum signup attempts permitted per IP address each hour.",
        alias="SIGNUP_RATE_LIMIT_PER_HOUR",
    )
    signup_rate_limit_per_day: int = Field(
        default=100,
        description="Maximum signup attempts permitted per IP address each day.",
        alias="SIGNUP_RATE_LIMIT_PER_IP_DAY",
    )
    signup_rate_limit_per_email_day: int = Field(
        default=3,
        description="Maximum signup attempts permitted per email address each day.",
        alias="SIGNUP_RATE_LIMIT_PER_EMAIL_DAY",
    )
    signup_rate_limit_per_domain_day: int = Field(
        default=20,
        description="Maximum signup attempts permitted per email domain each day.",
        alias="SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY",
    )
    signup_concurrent_requests_limit: int = Field(
        default=3,
        description="Maximum pending signup requests allowed per IP before operators respond.",
        alias="SIGNUP_CONCURRENT_REQUESTS_LIMIT",
    )
    signup_default_plan_code: str | None = Field(
        default="starter",
        description="Plan code automatically provisioned for new tenants when billing is enabled.",
    )
    signup_default_trial_days: int = Field(
        default=14,
        description=(
            "Fallback trial length (days) for tenants when processor metadata is unavailable."
        ),
    )
    signup_invite_reservation_ttl_seconds: int = Field(
        default=15 * 60,
        description=(
            "How long (seconds) a reserved invite remains valid while signup provisioning runs."
        ),
        alias="SIGNUP_INVITE_RESERVATION_TTL_SECONDS",
    )
    tenant_default_slug: str = Field(
        default="default",
        description="Tenant slug recorded by the CLI when seeding the initial org.",
        alias="TENANT_DEFAULT_SLUG",
    )

    @model_validator(mode="after")
    def _synchronize_signup_policy(self) -> SignupSettingsMixin:
        env_policy = os.getenv("SIGNUP_ACCESS_POLICY")
        env_allow = os.getenv("ALLOW_PUBLIC_SIGNUP")

        if env_policy:
            normalized = env_policy.strip().lower()
            if normalized in {"public", "invite_only", "approval"}:
                self.signup_access_policy = normalized  # type: ignore[assignment]
        elif env_allow is not None:
            allow_bool = env_allow.strip().lower() in {"1", "true", "yes", "y"}
            self.signup_access_policy = "public" if allow_bool else "invite_only"

        derived_allow = self.signup_access_policy == "public"

        if env_policy and env_allow is not None:
            env_allow_bool = env_allow.strip().lower() in {"1", "true", "yes", "y"}
            if env_allow_bool != derived_allow:
                signup_policy_logger.warning(
                    "ALLOW_PUBLIC_SIGNUP (%s) conflicts with SIGNUP_ACCESS_POLICY=%s; "
                    "using policy to derive final value.",
                    env_allow,
                    self.signup_access_policy,
                )

        self.allow_public_signup = derived_allow
        return self

    @field_validator(
        "signup_rate_limit_per_hour",
        "signup_rate_limit_per_day",
        "signup_rate_limit_per_email_day",
        "signup_rate_limit_per_domain_day",
        "signup_concurrent_requests_limit",
        "signup_default_trial_days",
        "signup_invite_reservation_ttl_seconds",
    )
    @classmethod
    def _validate_signup_ints(cls, value: int, info: ValidationInfo) -> int:
        if value < 0:
            raise ValueError(f"{info.field_name} must be greater than or equal to zero.")
        return value
