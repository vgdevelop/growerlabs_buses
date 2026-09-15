import asyncio
from datetime import datetime, timezone

from app.domain.models import LiveSnapshot

class MemorySnapshotCache:
    """Process-local last-good snapshot. Nothing is written to disk or a database."""

    def __init__(self, stale_after_seconds: int):
        self.stale_after_seconds = stale_after_seconds
        self._snapshot: LiveSnapshot | None = None
        self._lock = asyncio.Lock()

    async def store(self, snapshot: LiveSnapshot) -> None:
        async with self._lock:
            self._snapshot = snapshot.model_copy(deep=True)

    async def get(self) -> LiveSnapshot | None:
        async with self._lock:
            snapshot = self._snapshot.model_copy(deep=True) if self._snapshot else None
        if snapshot is None:
            return None
        age = (datetime.now(timezone.utc) - snapshot.received_at).total_seconds()
        if age > self.stale_after_seconds:
            snapshot.freshness = "stale"
        return snapshot
