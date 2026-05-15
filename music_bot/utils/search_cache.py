from __future__ import annotations

import logging
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)


class SearchCache:
    def __init__(self, ttl: int = 300) -> None:
        self._ttl = ttl
        self._store: dict[int, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def set(self, user_id: int, tracks: list[dict]) -> None:
        with self._lock:
            self._store[user_id] = {
                'tracks': tracks,
                'expires_at': time.monotonic() + self._ttl,
            }
        logger.debug('Cache SET user=%d tracks=%d', user_id, len(tracks))

    def get(self, user_id: int) -> list[dict] | None:
        with self._lock:
            entry = self._store.get(user_id)
            if entry is None:
                return None
            if time.monotonic() > entry['expires_at']:
                del self._store[user_id]
                logger.debug('Cache EXPIRED user=%d', user_id)
                return None
            return entry['tracks']

    def clear(self, user_id: int) -> None:
        with self._lock:
            removed = self._store.pop(user_id, None)
        if removed is not None:
            logger.debug('Cache CLEAR user=%d', user_id)

    def size(self) -> int:
        with self._lock:
            return len(self._store)


cache = SearchCache(ttl=300)
