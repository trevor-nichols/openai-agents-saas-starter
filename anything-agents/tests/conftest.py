"""Shared pytest fixtures for anything-agents tests."""

from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import pytest
from fakeredis.aioredis import FakeRedis

from app.core import config as config_module
from app.domain.conversations import (
    ConversationMetadata,
    ConversationMessage,
    ConversationRecord,
    ConversationRepository,
)
from app.services.conversation_service import conversation_service

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ.setdefault("AUTO_RUN_MIGRATIONS", "false")
os.environ.setdefault("ENABLE_BILLING", "false")

TEST_KEYSET_PATH = Path(__file__).parent / "fixtures" / "keysets" / "test_keyset.json"


@pytest.fixture(autouse=True)
def _configure_auth_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point key storage + auth settings at deterministic test fixtures."""

    monkeypatch.setenv("AUTH_KEY_STORAGE_BACKEND", "file")
    monkeypatch.setenv("AUTH_KEY_STORAGE_PATH", str(TEST_KEYSET_PATH))
    monkeypatch.setenv("AUTH_REFRESH_TOKEN_PEPPER", "test-refresh-pepper")
    monkeypatch.setenv("AUTH_DUAL_SIGNING_ENABLED", "false")
    monkeypatch.setenv("AUTH_JWKS_ETAG_SALT", "test-jwks-salt")
    monkeypatch.setenv("AUTH_JWKS_MAX_AGE_SECONDS", "120")
    config_module.get_settings.cache_clear()
    try:
        yield
    finally:
        config_module.get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _patch_redis_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """Route Redis clients to fakeredis to keep tests hermetic."""

    clients: dict[tuple[str, bool], FakeRedis] = {}

    def _fake_from_url(url: str, *, encoding: str = "utf-8", decode_responses: bool = False, **kwargs):
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

    async def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
        *,
        metadata: ConversationMetadata,
    ) -> None:
        self._messages[conversation_id].append(message)
        self._metadata[conversation_id] = metadata

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


@pytest.fixture(autouse=True)
def _configure_conversation_repo() -> None:
    """Ensure services/tests share a deterministic conversation repository."""

    repository = EphemeralConversationRepository()
    conversation_service.set_repository(repository)
    yield
