"""L1 in-memory cache — PRD Sec. 19.

Bounded (max items), TTL'd, versioned keys, no secrets, no OAuth tokens, no
full ontology, no large sensitive value sets. Backed by `cachetools.TTLCache`
so eviction is O(1) and the ceiling is enforced by the library, not by
convention.
"""
from __future__ import annotations

from typing import Any, Optional

from cachetools import TTLCache

from ..config import Settings, get_settings

_MAX_VALUE_BYTES = 32_768  # a "small, reconstructable" projection, not a dump


class L1MemoryCache:
    def __init__(self, settings: Optional[Settings] = None):
        settings = settings or get_settings()
        self._cache: TTLCache = TTLCache(
            maxsize=settings.l1_cache_max_items, ttl=settings.l1_cache_ttl_seconds
        )

    def get(self, key: str) -> Any | None:
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        # Defense in depth: refuse to cache anything that looks oversized or
        # token-shaped, even though callers should never pass such values.
        text = str(value)
        if len(text.encode("utf-8", errors="ignore")) > _MAX_VALUE_BYTES:
            return
        lowered = text.lower()
        if "oauth_token" in lowered or "access_token" in lowered or "obo_token" in lowered:
            raise ValueError("Refusing to cache a value that looks like it contains a token")
        self._cache[key] = value

    def invalidate(self, key: str) -> None:
        self._cache.pop(key, None)

    def clear(self) -> None:
        self._cache.clear()
