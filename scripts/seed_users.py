#!/usr/bin/env python
"""Seed a human user for local development environments."""

from __future__ import annotations

import argparse
import asyncio
import getpass
import sys
from pathlib import Path
from typing import Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure the backend package is importable when running from repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "anything-agents"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.security import PASSWORD_HASH_VERSION, get_password_hash  # noqa: E402
from app.infrastructure.db.engine import get_async_sessionmaker, init_engine  # noqa: E402
from app.infrastructure.persistence.auth.models import (  # noqa: E402
    PasswordHistory,
    TenantUserMembership,
    UserAccount,
    UserProfile,
    UserStatus,
)
from app.infrastructure.persistence.conversations.models import TenantAccount  # noqa: E402


async def _ensure_tenant(session: AsyncSession, slug: str, name: str) -> TenantAccount:
    result = await session.execute(
        select(TenantAccount).where(TenantAccount.slug == slug)
    )
    tenant = result.scalars().first()
    if tenant:
        return tenant

    tenant = TenantAccount(id=uuid4(), slug=slug, name=name)
    session.add(tenant)
    await session.flush()
    return tenant


async def _seed_user(args: argparse.Namespace) -> None:
    await init_engine(run_migrations=False)
    sessionmaker = get_async_sessionmaker()
    async with sessionmaker() as session:
        tenant = await _ensure_tenant(session, args.tenant_slug, args.tenant_name)

        normalized_email = args.email.strip().lower()
        existing = await session.execute(
            select(UserAccount).where(UserAccount.email == normalized_email)
        )
        if existing.scalars().first():
            raise SystemExit(f"User {normalized_email} already exists")

        password_hash = get_password_hash(args.password)

        user = UserAccount(
            id=uuid4(),
            email=normalized_email,
            password_hash=password_hash,
            password_pepper_version=PASSWORD_HASH_VERSION,
            status=UserStatus.ACTIVE if not args.locked else UserStatus.LOCKED,
        )
        session.add(user)
        await session.flush()

        profile = None
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

    print("\nSeeded user:")
    print(f"  Email:      {normalized_email}")
    print(f"  Tenant:     {tenant.slug} ({tenant.id})")
    print(f"  Role:       {args.role}")
    print(f"  Status:     {'locked' if args.locked else 'active'}")
    if profile:
        print(f"  Display:    {profile.display_name}")


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed a human admin user")
    parser.add_argument("--email", required=True, help="Email for the new user")
    parser.add_argument(
        "--password",
        help="Plain-text password (omit to prompt interactively)",
    )
    parser.add_argument(
        "--tenant-slug",
        default="default",
        help="Tenant slug; created automatically when missing",
    )
    parser.add_argument(
        "--tenant-name",
        default="Default Tenant",
        help="Tenant display name when provisioning a new tenant",
    )
    parser.add_argument(
        "--role",
        default="admin",
        help="Tenant role to grant (e.g. admin, member, billing-only)",
    )
    parser.add_argument(
        "--display-name",
        help="Optional display name stored in the profile table",
    )
    parser.add_argument(
        "--locked",
        action="store_true",
        help="Seed the account directly into the locked state",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv or sys.argv[1:])
    if not args.password:
        args.password = getpass.getpass("Password: ")
    if not args.password:
        raise SystemExit("Password is required")

    # Force settings to load so required env vars are validated early.
    get_settings()

    asyncio.run(_seed_user(args))


if __name__ == "__main__":
    main()
