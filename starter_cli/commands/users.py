from __future__ import annotations

import argparse
import getpass
import secrets
from types import SimpleNamespace

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext, CLIError
from starter_cli.workflows.setup.dev_user import (
    DEFAULT_EMAIL,
    DEFAULT_NAME,
    DEFAULT_ROLE,
    DEFAULT_TENANT,
    DEFAULT_TENANT_NAME,
    DevUserConfig,
    _persist_and_announce,  # type: ignore
    seed_dev_user,
)


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    users_parser = subparsers.add_parser("users", help="User provisioning helpers.")
    users_subparsers = users_parser.add_subparsers(dest="users_command")

    ensure_parser = users_subparsers.add_parser(
        "ensure-dev",
        help="Ensure the default developer account exists (rotates password when present).",
    )
    _add_shared_user_args(ensure_parser, display_default=DEFAULT_NAME)
    ensure_parser.add_argument(
        "--no-rotate-existing",
        action="store_true",
        help="Skip password rotation when the user already exists.",
    )
    ensure_parser.set_defaults(handler=handle_ensure_dev_user)

    seed_parser = users_subparsers.add_parser(
        "seed",
        help="Seed a specific user into a tenant (fails if the user already exists unless rotation is requested).",
    )
    _add_shared_user_args(seed_parser, display_default="")
    seed_parser.add_argument(
        "--rotate-existing",
        action="store_true",
        help="Rotate the password if the user already exists.",
    )
    seed_parser.add_argument(
        "--prompt-password",
        action="store_true",
        help="Prompt for the password instead of generating one (ignored when --password is supplied).",
    )
    seed_parser.set_defaults(handler=handle_seed_user)


def _add_shared_user_args(
    parser: argparse.ArgumentParser,
    *,
    display_default: str,
) -> None:
    parser.add_argument("--email", default=DEFAULT_EMAIL, help="User email.")
    parser.add_argument(
        "--password",
        help="Plain-text password. Defaults to a securely generated value.",
    )
    parser.add_argument(
        "--tenant-slug",
        default=DEFAULT_TENANT,
        help="Tenant slug; created automatically when missing.",
    )
    parser.add_argument(
        "--tenant-name",
        default=DEFAULT_TENANT_NAME,
        help="Tenant display name for newly created tenants.",
    )
    parser.add_argument("--role", default=DEFAULT_ROLE, help="Tenant role to grant.")
    parser.add_argument(
        "--display-name",
        default=display_default,
        help="Optional display name for the profile record.",
    )
    parser.add_argument(
        "--locked",
        action="store_true",
        help="Seed the user into the locked state.",
    )
    # Rotation flags are added per subcommand to keep defaults clear.


def handle_ensure_dev_user(args: argparse.Namespace, ctx: CLIContext) -> int:
    password = args.password or secrets.token_urlsafe(20)
    config = DevUserConfig(
        email=args.email.strip().lower(),
        password=password,
        tenant_slug=args.tenant_slug.strip(),
        tenant_name=args.tenant_name.strip(),
        role=args.role.strip(),
        display_name=args.display_name.strip(),
        locked=args.locked,
        generated_password=args.password is None,
        rotate_existing=not args.no_rotate_existing,
    )
    status = _seed_and_announce(ctx, config)
    if status not in {"created", "rotated", "exists"}:
        raise CLIError(f"Unexpected dev user seed result: {status}")
    return 0


def handle_seed_user(args: argparse.Namespace, ctx: CLIContext) -> int:
    password = args.password
    if not password and args.prompt_password:
        password = getpass.getpass("Password: ")
    if not password:
        password = secrets.token_urlsafe(20)

    config = DevUserConfig(
        email=args.email.strip().lower(),
        password=password,
        tenant_slug=args.tenant_slug.strip(),
        tenant_name=args.tenant_name.strip(),
        role=args.role.strip(),
        display_name=args.display_name.strip(),
        locked=args.locked,
        generated_password=args.password is None,
        rotate_existing=args.rotate_existing,
    )
    status = _seed_and_announce(ctx, config)
    if status == "exists" and not args.rotate_existing:
        raise CLIError(
            "User already exists; rerun with --rotate-existing to rotate the password."
        )
    if status not in {"created", "rotated", "exists"}:
        raise CLIError(f"Unexpected user seed result: {status}")
    return 0


def _seed_and_announce(ctx: CLIContext, config: DevUserConfig) -> str:
    context = SimpleNamespace(cli_ctx=ctx, dev_user_config=None)
    result = seed_dev_user(context, config)
    _persist_and_announce(context, config, result)
    return result


__all__ = ["register"]
