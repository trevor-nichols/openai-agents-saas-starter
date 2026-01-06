from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.password_policy import PasswordPolicyError, validate_password_strength
from app.core.security import PASSWORD_HASH_VERSION, get_password_hash
from app.infrastructure.db import dispose_engine
from app.infrastructure.db.engine import get_async_sessionmaker, init_engine
from app.infrastructure.persistence.auth.models import (
    PasswordHistory,
    TenantUserMembership,
    UserAccount,
    UserProfile,
    UserStatus,
)
from app.infrastructure.persistence.tenants.models import TenantAccount

# Import related models to ensure SQLAlchemy relationship registration.
from app.infrastructure.persistence.billing import models as _billing_models  # noqa: F401
from app.infrastructure.persistence.tenants import models as _tenant_models  # noqa: F401


@dataclass(slots=True)
class SeedDevUserArgs:
    email: str
    password: str
    tenant_slug: str
    tenant_name: str
    role: str
    display_name: str
    locked: bool
    rotate_existing: bool


async def _seed_dev_user(args: SeedDevUserArgs) -> str:
    await init_engine(run_migrations=False)
    sessionmaker = get_async_sessionmaker()

    async with sessionmaker() as session:
        assert isinstance(session, AsyncSession)

        result = await session.execute(select(UserAccount).where(UserAccount.email == args.email))
        existing = result.scalars().first()

        try:
            validate_password_strength(args.password, user_inputs=[args.email])
        except PasswordPolicyError as exc:
            raise RuntimeError(str(exc)) from exc

        if existing:
            if not args.rotate_existing:
                return "exists"

            password_hash = get_password_hash(args.password)
            existing.password_hash = password_hash
            existing.password_pepper_version = PASSWORD_HASH_VERSION
            existing.status = UserStatus.LOCKED if args.locked else UserStatus.ACTIVE

            history = PasswordHistory(
                id=uuid4(),
                user_id=existing.id,
                password_hash=password_hash,
                password_pepper_version=PASSWORD_HASH_VERSION,
            )
            session.add(history)
            await session.commit()
            return "rotated"

        tenant_result = await session.execute(
            select(TenantAccount).where(TenantAccount.slug == args.tenant_slug)
        )
        tenant = tenant_result.scalars().first()
        if tenant is None:
            tenant = TenantAccount(
                id=uuid4(),
                slug=args.tenant_slug,
                name=args.tenant_name,
            )
            session.add(tenant)
            await session.flush()

        password_hash = get_password_hash(args.password)
        user = UserAccount(
            id=uuid4(),
            email=args.email,
            password_hash=password_hash,
            password_pepper_version=PASSWORD_HASH_VERSION,
            status=UserStatus.LOCKED if args.locked else UserStatus.ACTIVE,
        )
        session.add(user)
        await session.flush()

        if args.display_name:
            profile = UserProfile(
                id=uuid4(),
                user_id=user.id,
                display_name=args.display_name,
            )
            session.add(profile)

        membership = TenantUserMembership(
            id=uuid4(),
            user_id=user.id,
            tenant_id=tenant.id,
            role=args.role,
        )
        session.add(membership)

        history = PasswordHistory(
            id=uuid4(),
            user_id=user.id,
            password_hash=password_hash,
            password_pepper_version=PASSWORD_HASH_VERSION,
        )
        session.add(history)

        await session.commit()
        return "created"


async def _run_seed(args: SeedDevUserArgs) -> str:
    try:
        return await _seed_dev_user(args)
    finally:
        await dispose_engine()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed or rotate the local dev user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--tenant-slug", required=True)
    parser.add_argument("--tenant-name", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--display-name", default="")
    parser.add_argument("--locked", action="store_true")
    parser.add_argument("--no-rotate-existing", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    ns = parser.parse_args(argv)

    # This script is used by the operator CLI and must produce machine-readable JSON.
    # Disable SQLAlchemy echo even if enabled in the developer's env to avoid polluting stdout.
    os.environ["DATABASE_ECHO"] = "false"

    args = SeedDevUserArgs(
        email=str(ns.email).strip().lower(),
        password=str(ns.password),
        tenant_slug=str(ns.tenant_slug).strip(),
        tenant_name=str(ns.tenant_name).strip(),
        role=str(ns.role).strip(),
        display_name=str(ns.display_name).strip(),
        locked=bool(ns.locked),
        rotate_existing=not bool(ns.no_rotate_existing),
    )

    result = asyncio.run(_run_seed(args))

    print(json.dumps({"result": result}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
