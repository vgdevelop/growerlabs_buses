import asyncio
import contextlib
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from app.api.routes import router
from app.config import settings
from app.services.cache import MemorySnapshotCache
from app.services.collector import RealtimeCollector
from app.services.stops import StopIndex
from app.services.lines import LineIndex

ROOT = Path(__file__).parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    cache = MemorySnapshotCache(settings.gps_stale_after_seconds)
    app.state.cache = cache
    app.state.stops = StopIndex(ROOT / "data" / "stops.json")
    app.state.lines = LineIndex(ROOT / "data" / "lines", ROOT / "data" / "metropolitan_routes")
    app.state.source_metadata = {
        "id": "stm-realtime",
        "publisher": "Intendencia de Montevideo",
        "official_url": settings.gps_source_url,
        "license_status": "pending-publisher-confirmation",
        "coverage": ["Montevideo", "Canelones", "San José", "Metropolitano"],
        "collection_enabled": settings.gps_collection_enabled,
        "historical_retention_enabled": False,
    }
    collector_task = None
    if settings.gps_collection_enabled:
        collector = RealtimeCollector(settings.gps_source_url, settings.gps_collection_interval_seconds, cache)
        collector_task = asyncio.create_task(collector.run())
    yield
    if collector_task:
        collector_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await collector_task


app = FastAPI(title="Grower Labs Transit API", version="0.1.0", lifespan=lifespan)
app.include_router(router)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/health")
async def health():
    snapshot = await app.state.cache.get()
    return {"status": "ok", "gps_collection_enabled": settings.gps_collection_enabled,
            "source_status": snapshot.freshness if snapshot else "waiting"}


@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
