"""Redis-backed stream backend for activity events."""

from __future__ import annotations

from collections import deque
from typing import Any

from app.infrastructure.redis_types import RedisBytesClient
from app.services.activity import ActivityStreamBackend


class RedisActivityEventStream:
    def __init__(
        self,
        redis: RedisBytesClient,
        stream_key: str,
        *,
        backlog_batch_size: int = 128,
        default_block_seconds: float = 1.0,
    ) -> None:
        self._redis = redis
        self._stream_key = stream_key
        self._backlog_batch_size = backlog_batch_size
        self._default_block_seconds = default_block_seconds
        self._buffer: deque[str] = deque()
        self._last_id = "0-0"
        self._backlog_exhausted = False
        self._closed = False

    async def next_message(self, timeout: float | None = None) -> str | None:
        if self._closed:
            return None
        if self._buffer:
            return self._buffer.popleft()
        if not self._backlog_exhausted:
            await self._load_backlog_batch()
            if self._buffer:
                return self._buffer.popleft()
        block_ms = self._to_block_milliseconds(timeout)
        entries = await self._read_new_entries(block_ms)
        if not entries:
            return None
        for entry_id, fields in entries:
            payload = self._decode_entry(fields)
            if payload is None:
                continue
            self._last_id = entry_id
            self._buffer.append(payload)
        if self._buffer:
            return self._buffer.popleft()
        return None

    async def close(self) -> None:
        self._closed = True

    async def _load_backlog_batch(self) -> None:
        if self._backlog_exhausted:
            return
        start = "-" if self._last_id == "0-0" else f"({self._last_id}"
        entries = await self._redis.xrange(
            self._stream_key,
            min=start,
            max="+",
            count=self._backlog_batch_size,
        )
        if not entries:
            self._backlog_exhausted = True
            return
        for entry_id, fields in entries:
            payload = self._decode_entry(fields)
            if payload is None:
                continue
            self._last_id = entry_id
            self._buffer.append(payload)
        if len(entries) < self._backlog_batch_size:
            self._backlog_exhausted = True

    async def _read_new_entries(
        self, block_ms: int | None
    ) -> list[tuple[str, dict[str | bytes, Any]]]:
        streams = await self._redis.xread(
            {self._stream_key: self._last_id},
            count=1,
            block=block_ms,
        )
        if not streams:
            return []
        _, entries = streams[0]
        return entries

    def _decode_entry(self, fields: dict[str | bytes, Any]) -> str | None:
        data = fields.get("data") or fields.get(b"data")
        if data is None:
            return None
        if isinstance(data, bytes):
            return data.decode("utf-8")
        return str(data)

    def _to_block_milliseconds(self, timeout: float | None) -> int | None:
        interval = timeout if timeout is not None else self._default_block_seconds
        if interval is None:
            return None
        interval = max(interval, 0.01)
        return int(interval * 1000)


class RedisActivityEventBackend(ActivityStreamBackend):
    def __init__(
        self,
        redis: RedisBytesClient,
        *,
        stream_max_length: int = 1024,
        stream_ttl_seconds: int = 86_400,
        backlog_batch_size: int = 128,
        owns_client: bool = True,
    ) -> None:
        self._redis = redis
        self._owns_client = owns_client
        self._stream_max_length = stream_max_length
        self._stream_ttl_seconds = stream_ttl_seconds
        self._backlog_batch_size = backlog_batch_size

    async def publish(self, channel: str, message: str) -> None:
        await self._redis.xadd(
            channel,
            {"data": message},
            maxlen=self._stream_max_length,
            approximate=False,
        )
        if self._stream_ttl_seconds > 0:
            await self._redis.expire(channel, self._stream_ttl_seconds)

    async def subscribe(self, channel: str) -> RedisActivityEventStream:
        return RedisActivityEventStream(
            self._redis,
            channel,
            backlog_batch_size=self._backlog_batch_size,
        )

    async def close(self) -> None:
        if self._owns_client:
            await self._redis.close()


__all__ = ["RedisActivityEventBackend", "RedisActivityEventStream"]
