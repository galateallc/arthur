"""ImpulseCache — LRU cache with TTL for interpreted impulse results.

Cache key: hash(event_type + normalized_summary + personality + affinity_bucket)
TTL: 1 hour for realtime events, 4 hours for background events.
Size: LRU, 1000 entries.
"""

from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from dataclasses import dataclass

from kindalive.engine.impulse import ChemicalImpulse
from kindalive.interpreter.text_input import UserText

# TTLs in seconds
REALTIME_TTL = 3600.0      # 1 hour
BACKGROUND_TTL = 14400.0   # 4 hours
DEFAULT_MAX_SIZE = 1000

# Affinity buckets for cache key normalization
_AFFINITY_THRESHOLDS = [0.5, 1.0]  # low/med/high


def _affinity_bucket(affinity: float) -> str:
    if affinity < _AFFINITY_THRESHOLDS[0]:
        return "low"
    elif affinity < _AFFINITY_THRESHOLDS[1]:
        return "med"
    return "high"


def _cache_key(event: UserText, personality: str, affinity: float) -> str:
    """Build a deterministic cache key."""
    raw = f"{event.event_type}|{event.summary}|{personality}|{_affinity_bucket(affinity)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


@dataclass
class _CacheEntry:
    impulses: list[ChemicalImpulse]
    expires_at: float


class ImpulseCache:
    """LRU cache with TTL for impulse interpretation results."""

    def __init__(self, max_size: int = DEFAULT_MAX_SIZE) -> None:
        self._store: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(
        self,
        event: UserText,
        personality: str,
        affinity: float,
        now: float | None = None,
    ) -> list[ChemicalImpulse] | None:
        """Look up cached impulses. Returns None on miss or expired."""
        key = _cache_key(event, personality, affinity)
        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            return None

        current = now if now is not None else time.monotonic()
        if current >= entry.expires_at:
            del self._store[key]
            self._misses += 1
            return None

        # Move to end (most recently used)
        self._store.move_to_end(key)
        self._hits += 1
        return list(entry.impulses)

    def put(
        self,
        event: UserText,
        personality: str,
        affinity: float,
        impulses: list[ChemicalImpulse],
        now: float | None = None,
    ) -> None:
        """Store impulses in cache."""
        key = _cache_key(event, personality, affinity)
        current = now if now is not None else time.monotonic()

        ttl = REALTIME_TTL if event.urgency == "realtime" else BACKGROUND_TTL
        self._store[key] = _CacheEntry(
            impulses=list(impulses),
            expires_at=current + ttl,
        )
        self._store.move_to_end(key)

        # Evict LRU if over size
        while len(self._store) > self._max_size:
            self._store.popitem(last=False)

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses

    @property
    def size(self) -> int:
        return len(self._store)

    def clear(self) -> None:
        self._store.clear()
        self._hits = 0
        self._misses = 0
