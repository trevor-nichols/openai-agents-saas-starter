from __future__ import annotations

from collections.abc import Iterable

from redis import Redis

from starter_console.ports.redis import RedisHealthPort


class RedisHealthAdapter(RedisHealthPort):
    def ping_all(self, urls: Iterable[str]) -> None:
        seen: set[str] = set()
        for url in urls:
            if not url or url in seen:
                continue
            seen.add(url)
            client = Redis.from_url(url, encoding="utf-8", decode_responses=True)
            try:
                client.ping()
            finally:
                client.close()


__all__ = ["RedisHealthAdapter"]
