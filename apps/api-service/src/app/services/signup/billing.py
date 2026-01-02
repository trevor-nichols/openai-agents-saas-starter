"""Billing provisioning helpers for signup flows."""

from __future__ import annotations

from collections.abc import Callable

from app.core.settings import Settings, get_settings
from app.observability.logging import log_event
from app.services.billing.billing_service import BillingService, get_billing_service
from app.services.billing.errors import BillingError, PaymentProviderError
from app.services.signup.errors import BillingProvisioningError


class SignupBillingService:
    def __init__(
        self,
        *,
        billing_service: BillingService | None = None,
        settings_factory: Callable[[], Settings] | None = None,
    ) -> None:
        self._billing_service = billing_service
        self._settings_factory = settings_factory or get_settings

    def _get_settings(self) -> Settings:
        return self._settings_factory()

    def _get_billing_service(self) -> BillingService | None:
        if self._billing_service is None:
            try:
                self._billing_service = get_billing_service()
            except RuntimeError:
                self._billing_service = None
        return self._billing_service

    async def provision_subscription_if_needed(
        self,
        *,
        tenant_id: str,
        plan_code: str | None,
        billing_email: str,
        requested_trial_days: int | None,
    ) -> None:
        settings = self._get_settings()
        if not plan_code or not settings.enable_billing:
            log_event(
                "signup.billing_skipped",
                result="skipped",
                tenant_id=tenant_id,
                reason="billing_disabled" if not settings.enable_billing else "plan_missing",
            )
            return

        service = self._get_billing_service()
        if service is None:
            raise BillingProvisioningError("Billing service is not configured.")

        trial_days = await self._select_trial_days(
            plan_code=plan_code,
            requested_trial_days=requested_trial_days,
        )
        try:
            await service.start_subscription(
                tenant_id=tenant_id,
                plan_code=plan_code,
                billing_email=billing_email,
                auto_renew=True,
                seat_count=1,
                trial_days=trial_days,
            )
        except PaymentProviderError as exc:
            raise BillingProvisioningError(str(exc)) from exc
        except BillingError:
            raise
        else:
            log_event(
                "signup.billing_provisioned",
                result="success",
                tenant_id=tenant_id,
                plan_code=plan_code,
                trial_days=trial_days,
            )

    async def _select_trial_days(
        self,
        *,
        plan_code: str | None,
        requested_trial_days: int | None,
    ) -> int | None:
        settings = self._get_settings()
        plan_trial_days = await self._lookup_plan_trial_days(plan_code)
        if plan_trial_days is not None:
            max_allowed: int | None = plan_trial_days
        else:
            max_allowed = settings.signup_default_trial_days
        max_allowed = max_allowed if max_allowed and max_allowed > 0 else None

        if not settings.allow_signup_trial_override or requested_trial_days is None:
            return max_allowed

        cap = max_allowed if max_allowed is not None else 0
        candidate = min(requested_trial_days, cap)
        return candidate if candidate and candidate > 0 else None

    async def _lookup_plan_trial_days(self, plan_code: str | None) -> int | None:
        if not plan_code:
            return None
        service = self._get_billing_service()
        if service is None:
            return None
        try:
            plans = await service.list_plans()
        except BillingError as exc:
            log_event(
                "signup.plan_lookup_failed",
                result="error",
                plan_code=plan_code,
                error=str(exc),
            )
            return None

        for plan in plans:
            if plan.code == plan_code:
                return plan.trial_days
        return None


__all__ = ["SignupBillingService"]
