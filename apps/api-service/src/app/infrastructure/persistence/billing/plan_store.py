"""Billing plan persistence helpers."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.domain.billing import BillingPlan
from app.infrastructure.persistence.billing.mappers import to_domain_plan
from app.infrastructure.persistence.billing.models import BillingPlan as ORMPlan

logger = logging.getLogger("api-service.persistence.billing")


class PlanStore:
    """Persistence adapter for billing plans."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def list_plans(self) -> list[BillingPlan]:
        async with self._session_factory() as session:
            result = await session.execute(select(ORMPlan).options(selectinload(ORMPlan.features)))
            plans = [to_domain_plan(row) for row in result.scalars()]
            logger.debug("Fetched %s billing plans from Postgres.", len(plans))
            return plans


__all__ = ["PlanStore"]
