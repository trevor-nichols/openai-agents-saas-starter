"""Shared pytest fixtures for anything-agents tests."""

from __future__ import annotations

import asyncio
import os
from collections import defaultdict
from collections.abc import Generator, Iterable
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ.setdefault("AUTO_RUN_MIGRATIONS", "false")
os.environ.setdefault("ENABLE_BILLING", "false")
os.environ.setdefault("ALLOW_PUBLIC_SIGNUP", "true")
os.environ.setdefault("STARTER_CLI_SKIP_ENV", "true")
os.environ.setdefault("STARTER_CLI_SKIP_VAULT_PROBE", "true")

import pytest
import sqlalchemy.ext.asyncio as sqla_async
from fakeredis.aioredis import FakeRedis
from sqlalchemy.dialects.postgresql import CITEXT, JSONB
from sqlalchemy.ext.compiler import compiles
from starter_shared import config as shared_config

from app.bootstrap import reset_container
from app.core import config as config_module
from app.domain.conversations import (
    ConversationMessage,
    ConversationMetadata,
    ConversationRecord,
    ConversationRepository,
    ConversationSessionState,
)
from app.infrastructure.openai.sessions import (
    configure_sdk_session_store,
    reset_sdk_session_store,
)
from app.services.conversation_service import conversation_service

config_module.get_settings.cache_clear()

TEST_KEYSET_PATH = Path(__file__).parent / "fixtures" / "keysets" / "test_keyset.json"


@compiles(JSONB, "sqlite")
def _compile_jsonb_to_text(element, compiler, **kwargs):
    return "TEXT"


@compiles(CITEXT, "sqlite")
def _compile_citext_to_text(element, compiler, **kwargs):
    return "TEXT"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register custom CLI flags."""

    parser.addoption(
        "--enable-stripe-replay",
        action="store_true",
        default=False,
        help=(
            "Run tests marked with @pytest.mark.stripe_replay "
            "(requires Postgres + Stripe fixtures)."
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    """Ensure markers are known to pytest."""

    config.addinivalue_line(
        "markers",
        "stripe_replay: exercises Stripe webhook replay + billing stream flows; "
        "requires external fixtures.",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip Stripe replay tests unless explicitly enabled."""

    if config.getoption("--enable-stripe-replay"):
        return

    skip_marker = pytest.mark.skip(reason="Stripe replay tests require --enable-stripe-replay.")
    for item in items:
        if "stripe_replay" in item.keywords:
            item.add_marker(skip_marker)


@pytest.fixture(autouse=True)
def _reset_application_container() -> Generator[None, None, None]:
    """Ensure each test starts with a fresh dependency container."""

    reset_container()
    yield


@pytest.fixture(scope="session", autouse=True)
def _configure_sdk_session() -> Generator[None, None, None]:
    """Configure the SDK session store for tests using an in-memory SQLite engine."""

    engine = sqla_async.create_async_engine("sqlite+aiosqlite:///:memory:")
    configure_sdk_session_store(engine, auto_create_tables=True)
    try:
        yield
    finally:
        reset_sdk_session_store()
        loop = asyncio.new_event_loop()
        loop.run_until_complete(engine.dispose())
        loop.close()


@pytest.fixture(autouse=True)
def _configure_auth_settings(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Point key storage + auth settings at deterministic test fixtures."""

    monkeypatch.setenv("AUTH_KEY_STORAGE_BACKEND", "file")
    monkeypatch.setenv("AUTH_KEY_STORAGE_PATH", str(TEST_KEYSET_PATH))
    monkeypatch.setenv("AUTH_REFRESH_TOKEN_PEPPER", "test-refresh-pepper")
    monkeypatch.setenv("AUTH_DUAL_SIGNING_ENABLED", "false")
    monkeypatch.setenv("AUTH_JWKS_ETAG_SALT", "test-jwks-salt")
    monkeypatch.setenv("AUTH_JWKS_MAX_AGE_SECONDS", "120")
    config_module.get_settings.cache_clear()
    shared_config.get_settings.cache_clear()
    try:
        yield
    finally:
        config_module.get_settings.cache_clear()
        shared_config.get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _patch_redis_client(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Route Redis clients to fakeredis to keep tests hermetic."""

    clients: dict[tuple[str, bool], FakeRedis] = {}

    def _fake_from_url(
        url: str, *, encoding: str = "utf-8", decode_responses: bool = False, **kwargs
    ):
        key = (url, decode_responses)
        client = clients.get(key)
        if client is None:
            client = FakeRedis(encoding=encoding, decode_responses=decode_responses)
            clients[key] = client
        return client

    monkeypatch.setattr("redis.asyncio.Redis.from_url", staticmethod(_fake_from_url), raising=False)
    yield


class EphemeralConversationRepository(ConversationRepository):
    """Simple, per-test repository satisfying the conversation protocol."""

    def __init__(self) -> None:
        self._messages: dict[str, list[ConversationMessage]] = defaultdict(list)
        self._metadata: dict[str, ConversationMetadata] = {}
        self._session_state: dict[str, ConversationSessionState] = {}

    async def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
        *,
        metadata: ConversationMetadata,
    ) -> None:
        self._messages[conversation_id].append(message)
        self._metadata[conversation_id] = metadata
        self._session_state[conversation_id] = ConversationSessionState(
            sdk_session_id=metadata.sdk_session_id,
            session_cursor=metadata.session_cursor,
            last_session_sync_at=metadata.last_session_sync_at,
        )

    async def get_messages(self, conversation_id: str) -> list[ConversationMessage]:
        return list(self._messages.get(conversation_id, []))

    async def list_conversation_ids(self) -> list[str]:
        return list(self._messages.keys())

    async def iter_conversations(self) -> Iterable[ConversationRecord]:
        return [
            ConversationRecord(conversation_id=cid, messages=list(messages))
            for cid, messages in self._messages.items()
        ]

    async def clear_conversation(self, conversation_id: str) -> None:
        self._messages.pop(conversation_id, None)
        self._metadata.pop(conversation_id, None)
        self._session_state.pop(conversation_id, None)

    async def get_session_state(self, conversation_id: str) -> ConversationSessionState | None:
        return self._session_state.get(conversation_id)

    async def upsert_session_state(
        self, conversation_id: str, state: ConversationSessionState
    ) -> None:
        self._session_state[conversation_id] = state


@pytest.fixture(autouse=True)
def _configure_conversation_repo(
    _reset_application_container,
) -> Generator[None, None, None]:
    """Ensure services/tests share a deterministic conversation repository."""

    repository = EphemeralConversationRepository()
    conversation_service.set_repository(repository)
    yield
