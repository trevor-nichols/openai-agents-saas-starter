"""Shared pytest fixtures for api-service tests."""

from __future__ import annotations

import asyncio
import os
from collections import defaultdict
from collections.abc import AsyncGenerator, Generator
from datetime import datetime
from pathlib import Path

import pytest
import pytest_asyncio
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

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
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

TEST_DB_PATH = Path("test.db")
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

from app.bootstrap import get_container, reset_container
from app.core import settings as config_module
from app.domain.conversations import (
    ConversationEvent,
    ConversationMessage,
    ConversationMetadata,
    ConversationPage,
    ConversationRecord,
    ConversationRepository,
    ConversationSearchHit,
    ConversationSearchPage,
    ConversationSessionState,
)
from app.infrastructure.persistence.models.base import Base
from app.infrastructure.persistence.workflows import models as _workflow_models  # noqa: F401
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
    parser.addoption(
        "--run-manual",
        action="store_true",
        default=False,
        help="Run manual tests that hit live services (default: skip)",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Ensure markers are known to pytest."""

    register_stripe_replay_marker(config)
    config.addinivalue_line(
        "markers",
        "auto_migrations(enabled=True): toggle AUTO_RUN_MIGRATIONS for a test or module.",
    )
    config.addinivalue_line("markers", "manual: marks tests that require live services")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip Stripe replay tests unless explicitly enabled."""

    skip_stripe_replay_if_disabled(config, items)

    if not config.getoption("--run-manual"):
        skip_manual = pytest.mark.skip(reason="manual test (use --run-manual to run)")
        for item in items:
            if "manual" in item.keywords:
                item.add_marker(skip_manual)


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


@pytest_asyncio.fixture(autouse=True)
async def _configure_agent_provider(
    _reset_application_container, _provider_engine
) -> AsyncGenerator[None, None]:
    """Register the OpenAI provider against the in-memory test engine."""

    async with _provider_engine.begin() as conn:
        # Populate ORM metadata (includes workflow tables via imports above)
        await conn.run_sync(Base.metadata.create_all)

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
        self._events: dict[tuple[str, str], list[ConversationEvent]] = defaultdict(list)

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
            provider=metadata.provider,
            provider_conversation_id=metadata.provider_conversation_id,
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

    async def get_conversation(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
    ) -> ConversationRecord | None:
        tenant = self._require_tenant(tenant_id)
        key = (tenant, conversation_id)
        messages = self._messages.get(key, [])
        if not messages:
            return None
        return ConversationRecord(conversation_id=conversation_id, messages=list(messages))

    async def paginate_conversations(
        self,
        *,
        tenant_id: str,
        limit: int,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
        updated_after: datetime | None = None,
    ) -> ConversationPage:
        tenant = self._require_tenant(tenant_id)
        conversations = await self.iter_conversations(tenant_id=tenant)
        conversations = [
            c for c in conversations if (not updated_after or c.updated_at >= updated_after)
        ]
        conversations.sort(key=lambda c: (c.updated_at, c.conversation_id), reverse=True)

        start = 0
        if cursor:
            try:
                cursor_ts, cursor_id = cursor.split("::", 1)
                cursor_dt = datetime.fromisoformat(cursor_ts)
                for idx, conv in enumerate(conversations):
                    if (conv.updated_at < cursor_dt) or (
                        conv.updated_at == cursor_dt and conv.conversation_id < cursor_id
                    ):
                        start = idx
                        break
            except Exception:
                start = 0

        slice_items = conversations[start : start + limit + 1]
        next_cursor = None
        if len(slice_items) > limit:
            tail = slice_items[limit]
            next_cursor = f"{tail.updated_at.isoformat()}::{tail.conversation_id}"
            slice_items = slice_items[:limit]

        return ConversationPage(items=slice_items, next_cursor=next_cursor)

    async def search_conversations(
        self,
        *,
        tenant_id: str,
        query: str,
        limit: int,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
    ) -> ConversationSearchPage:
        tenant = self._require_tenant(tenant_id)
        normalized = query.lower()
        matches: list[ConversationSearchHit] = []
        for (current_tenant, cid), messages in self._messages.items():
            if current_tenant != tenant:
                continue
            for msg in messages:
                if normalized in msg.content.lower():
                    matches.append(
                        ConversationSearchHit(
                            record=ConversationRecord(conversation_id=cid, messages=list(messages)),
                            score=float(len(msg.content)),
                        )
                    )
                    break

        matches.sort(
            key=lambda hit: (hit.record.updated_at, hit.score, hit.record.conversation_id),
            reverse=True,
        )

        start = 0
        if cursor:
            try:
                cursor_ts, cursor_id = cursor.split("::", 1)
                cursor_dt = datetime.fromisoformat(cursor_ts)
                for idx, hit in enumerate(matches):
                    if (hit.record.updated_at < cursor_dt) or (
                        hit.record.updated_at == cursor_dt
                        and hit.record.conversation_id < cursor_id
                    ):
                        start = idx
                        break
            except Exception:
                start = 0

        slice_hits = matches[start : start + limit + 1]
        next_cursor = None
        if len(slice_hits) > limit:
            tail = slice_hits[limit].record
            next_cursor = f"{tail.updated_at.isoformat()}::{tail.conversation_id}"
            slice_hits = slice_hits[:limit]

        return ConversationSearchPage(items=slice_hits, next_cursor=next_cursor)

    async def clear_conversation(self, conversation_id: str, *, tenant_id: str) -> None:
        key = self._key(tenant_id, conversation_id)
        self._messages.pop(key, None)
        self._metadata.pop(key, None)
        self._session_state.pop(key, None)
        self._events.pop(key, None)

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

    async def add_run_events(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        events: list[ConversationEvent],
    ) -> None:
        key = self._key(tenant_id, conversation_id)
        self._events[key].extend(events)

    async def get_run_events(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        workflow_run_id: str | None = None,
    ) -> list[ConversationEvent]:
        key = self._key(tenant_id, conversation_id)
        events = list(self._events.get(key, []))
        if workflow_run_id:
            events = [ev for ev in events if ev.workflow_run_id == workflow_run_id]
        return events

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
