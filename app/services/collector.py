import asyncio
import logging
import random

import httpx
from prometheus_client import Counter, Gauge, Histogram

from app.services.cache import MemorySnapshotCache
from app.services.normalizer import normalize_stm_geojson

logger = logging.getLogger(__name__)
COLLECTIONS = Counter("transit_collector_requests_total", "Upstream collection attempts", ["result"])
LATENCY = Histogram("transit_collector_request_seconds", "Upstream request duration")
FRESHNESS = Gauge("transit_source_age_seconds", "Age of last good source snapshot", ["source"])
SCHEMA_WARNINGS = Counter("transit_schema_warnings_total", "Unknown upstream schema fields", ["source"])


class RealtimeCollector:
    def __init__(self, url: str, interval_seconds: int, cache: MemorySnapshotCache):
        self.url = url
        self.interval_seconds = max(interval_seconds, 10)
        self.cache = cache
        self._failures = 0

    async def run(self) -> None:
        while True:
            await self.collect_once()
            delay = min(self.interval_seconds * (2 ** min(self._failures, 4)), 300)
            await asyncio.sleep(delay + random.uniform(0, 0.75))

    async def collect_once(self) -> None:
        try:
            with LATENCY.time():
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post(self.url, json={"subsistema": "-1", "empresa": "-1"})
            if response.status_code in (403, 429):
                raise RuntimeError(f"collection disabled by upstream HTTP {response.status_code}")
            response.raise_for_status()
            snapshot = normalize_stm_geojson(response.json())
            await self.cache.store(snapshot)
            COLLECTIONS.labels(result="success").inc()
            SCHEMA_WARNINGS.labels(source=snapshot.source_id).inc(len(snapshot.schema_warnings))
            FRESHNESS.labels(source=snapshot.source_id).set(0)
            self._failures = 0
        except Exception as exc:  # the last good cache remains intact
            self._failures += 1
            COLLECTIONS.labels(result="error").inc()
            logger.warning("GPS collection failed (%s); cached payload was not replaced", type(exc).__name__)
