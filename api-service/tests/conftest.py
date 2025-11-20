"""Shared pytest fixtures for api-service tests."""

from __future__ import annotations

import asyncio
import os
from collections import defaultdict
from collections.abc import Generator
from pathlib import Path

import pytest
import sqlalchemy.ext.asyncio as sqla_async
from fakeredis.aioredis import FakeRedis
from sqlalchemy.dialects.postgresql import CITEXT, JSONB
from sqlalchemy.ext.compiler import compiles
from starter_contracts import config as shared_config

from tests.utils.pytest_stripe import (
    configure_stripe_replay_option,
    register_stripe_replay_marker,
    skip_stripe_replay_if_disabled,
)

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ.setdefault("RATE_LIMIT_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("AUTH_CACHE_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("SECURITY_TOKEN_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("USAGE_GUARDRAIL_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("AUTO_RUN_MIGRATIONS", "false")
os.environ.setdefault("ENABLE_BILLING", "false")
os.environ.setdefault("ALLOW_PUBLIC_SIGNUP", "true")
os.environ.setdefault("STARTER_CLI_SKIP_ENV", "true")
os.environ.setdefault("STARTER_CLI_SKIP_VAULT_PROBE", "true")

from app.bootstrap import get_container, reset_container
from app.core import config as config_module
from app.domain.conversations import (
    ConversationMessage,
    ConversationMetadata,
    ConversationRecord,
    ConversationRepository,
    ConversationSessionState,
)
from app.infrastructure.persistence.models.base import Base
from app.infrastructure.providers.openai import build_openai_provider
from app.services.agents.provider_registry import get_provider_registry
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

    configure_stripe_replay_option(parser)


def pytest_configure(config: pytest.Config) -> None:
    """Ensure markers are known to pytest."""

    register_stripe_replay_marker(config)
    config.addinivalue_line(
        "markers",
        "auto_migrations(enabled=True): toggle AUTO_RUN_MIGRATIONS for a test or module.",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip Stripe replay tests unless explicitly enabled."""

    skip_stripe_replay_if_disabled(config, items)


@pytest.fixture(autouse=True)
def _reset_application_container() -> Generator[None, None, None]:
    """Ensure each test starts with a fresh dependency container."""

    container = reset_container()
    # Use in-memory conversation repository to avoid DB/migration coupling in tests
    container.conversation_service.set_repository(EphemeralConversationRepository())
    yield


@pytest.fixture(scope="session")
def _provider_engine() -> Generator[sqla_async.AsyncEngine, None, None]:
    engine = sqla_async.create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        yield engine
    finally:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(engine.dispose())
        loop.close()


@pytest.fixture(autouse=True)
def _configure_agent_provider(
    _reset_application_container, _provider_engine
) -> Generator[None, None, None]:
    """Register the OpenAI provider against the in-memory test engine."""

    async def _create_tables():
        async with _provider_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.get_event_loop().run_until_complete(_create_tables())

    registry = get_provider_registry()
    registry.clear()
    registry.register(
        build_openai_provider(
            settings_factory=config_module.get_settings,
            conversation_searcher=lambda tenant_id, query: conversation_service.search(
                tenant_id=tenant_id, query=query
            ),
            engine=_provider_engine,
            auto_create_tables=True,
        ),
        set_default=True,
    )
    # Ensure AgentService will be rebuilt against the freshly populated registry
    get_container().agent_service = None
    yield


@pytest.fixture(autouse=True)
def _configure_auto_run_migrations(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> Generator[None, None, None]:
    """Allow tests to opt into auto migrations without forcing suite-wide behavior."""

    marker = request.node.get_closest_marker("auto_migrations")
    if marker is not None:
        enabled = marker.kwargs.get("enabled", True)
        monkeypatch.setenv("AUTO_RUN_MIGRATIONS", "true" if enabled else "false")
    yield


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
        self._messages: dict[tuple[str, str], list[ConversationMessage]] = defaultdict(list)
        self._metadata: dict[tuple[str, str], ConversationMetadata] = {}
        self._session_state: dict[tuple[str, str], ConversationSessionState] = {}

    async def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
        *,
        tenant_id: str,
        metadata: ConversationMetadata,
    ) -> None:
        key = self._key(tenant_id, conversation_id)
        self._messages[key].append(message)
        self._metadata[key] = metadata
        self._session_state[key] = ConversationSessionState(
            sdk_session_id=metadata.sdk_session_id,
            session_cursor=metadata.session_cursor,
            last_session_sync_at=metadata.last_session_sync_at,
        )

    async def get_messages(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
    ) -> list[ConversationMessage]:
        key = self._key(tenant_id, conversation_id)
        return list(self._messages.get(key, []))

    async def list_conversation_ids(self, *, tenant_id: str) -> list[str]:
        tenant = self._require_tenant(tenant_id)
        return [cid for (current_tenant, cid) in self._messages.keys() if current_tenant == tenant]

    async def iter_conversations(self, *, tenant_id: str) -> list[ConversationRecord]:
        tenant = self._require_tenant(tenant_id)
        records: list[ConversationRecord] = []
        for (current_tenant, cid), messages in self._messages.items():
            if current_tenant != tenant:
                continue
            records.append(ConversationRecord(conversation_id=cid, messages=list(messages)))
        return records

    async def clear_conversation(self, conversation_id: str, *, tenant_id: str) -> None:
        key = self._key(tenant_id, conversation_id)
        self._messages.pop(key, None)
        self._metadata.pop(key, None)
        self._session_state.pop(key, None)

    async def get_session_state(
        self, conversation_id: str, *, tenant_id: str
    ) -> ConversationSessionState | None:
        key = self._key(tenant_id, conversation_id)
        return self._session_state.get(key)

    async def upsert_session_state(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        state: ConversationSessionState,
    ) -> None:
        key = self._key(tenant_id, conversation_id)
        self._session_state[key] = state

    def _key(self, tenant_id: str, conversation_id: str) -> tuple[str, str]:
        tenant = self._require_tenant(tenant_id)
        return tenant, conversation_id

    @staticmethod
    def _require_tenant(tenant_id: str) -> str:
        tenant = (tenant_id or "").strip()
        if not tenant:
            raise ValueError("tenant_id is required")
        return tenant


@pytest.fixture(autouse=True)
def _configure_conversation_repo(
    _reset_application_container,
) -> Generator[None, None, None]:
    """Ensure services/tests share a deterministic conversation repository."""

    repository = EphemeralConversationRepository()
    conversation_service.set_repository(repository)
    yield
