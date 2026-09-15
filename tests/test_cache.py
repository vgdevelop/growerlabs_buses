from datetime import datetime, timezone

import pytest

from app.services.cache import MemorySnapshotCache
from app.services.normalizer import normalize_stm_geojson


@pytest.mark.asyncio
async def test_one_cached_capture_serves_multiple_clients():
    cache = MemorySnapshotCache(45)
    payload = {"type":"FeatureCollection","features":[]}
    await cache.store(normalize_stm_geojson(payload, datetime.now(timezone.utc)))
    first, second = await cache.get(), await cache.get()
    assert first == second


@pytest.mark.asyncio
async def test_bad_capture_does_not_replace_last_good_state():
    cache = MemorySnapshotCache(45)
    await cache.store(normalize_stm_geojson({"type":"FeatureCollection","features":[]}))
    before = await cache.get()
    with pytest.raises(ValueError): normalize_stm_geojson({"type":"broken"})
    assert await cache.get() == before
