from fastapi import APIRouter, HTTPException, Query, Request

from app.domain.models import LiveSnapshot
from app.services.arrivals import upcoming_vehicles

router = APIRouter(prefix="/api/v1")


@router.get("/sources")
async def sources(request: Request):
    return {"items": [request.app.state.source_metadata]}


@router.get("/coverage")
async def coverage():
    return {
        "country": "Uruguay",
        "gps_national": False,
        "areas": [
            {"name": "Montevideo", "source": "stm-realtime", "mode": "realtime"},
            {"name": "Canelones", "source": "stm-realtime", "mode": "realtime"},
            {"name": "San José", "source": "stm-realtime", "mode": "realtime"},
            {"name": "resto de Uruguay", "source": None, "mode": "not-available"},
        ],
    }


MAX_VISIBLE_VEHICLES = 300
MAX_VISIBLE_STOPS = 600


def filter_vehicles(snapshot: LiveSnapshot, company: str | None, line: str | None,
                    subsystem: str | None = None):
    vehicles = snapshot.vehicles
    if company:
        vehicles = [item for item in vehicles if item.operator_code.casefold() == company.casefold()]
    if line:
        vehicles = [item for item in vehicles if item.route.casefold() == line.casefold()]
    if subsystem:
        vehicles = [item for item in vehicles if (item.subsystem or "").casefold() == subsystem.casefold()]
    return vehicles


@router.get("/filters")
async def filters(request: Request):
    snapshot = await request.app.state.cache.get()
    if snapshot is None:
        return {"companies": [], "lines": [], "subsystems": []}
    return {
        "companies": [
            {"code": code, "name": name}
            for code, name in sorted(
                {(item.operator_code, item.operator_name) for item in snapshot.vehicles},
                key=lambda item: item[1].casefold(),
            )
        ],
        "lines": sorted({item.route for item in snapshot.vehicles}, key=lambda value: (len(value), value)),
        "subsystems": sorted({item.subsystem for item in snapshot.vehicles if item.subsystem}),
    }


@router.get("/vehicles/live")
async def live_vehicles(
    request: Request,
    company: str | None = Query(default=None, min_length=1, max_length=40),
    line: str | None = Query(default=None, min_length=1, max_length=40),
    subsystem: str | None = Query(default=None, min_length=1, max_length=80),
):
    if not company and not line:
        raise HTTPException(status_code=400, detail="company or line is required")
    snapshot = await request.app.state.cache.get()
    if snapshot is None:
        return {
            "source_id": "stm-realtime", "coverage": [],
            "license_status": "pending-publisher-confirmation",
            "freshness": "unavailable", "vehicles": [], "received_at": None,
        }
    matched = filter_vehicles(snapshot, company, line, subsystem)
    response = snapshot.model_dump()
    response["vehicles"] = matched[:MAX_VISIBLE_VEHICLES]
    response["total_matched"] = len(matched)
    response["truncated"] = len(matched) > MAX_VISIBLE_VEHICLES
    response["limit"] = MAX_VISIBLE_VEHICLES
    return response


@router.get("/stops")
async def stops(
    request: Request,
    company: str | None = Query(default=None, min_length=1, max_length=40),
    line: str | None = Query(default=None, min_length=1, max_length=40),
):
    if not company and not line:
        raise HTTPException(status_code=400, detail="company or line is required")
    lines = {line} if line else set()
    if company:
        snapshot = await request.app.state.cache.get()
        if snapshot:
            lines.update(
                item.route for item in snapshot.vehicles
                if item.operator_code.casefold() == company.casefold()
            )
    matched = request.app.state.stops.for_lines(lines)
    next_times = request.app.state.lines.next_times(line, [item["id"] for item in matched]) if line else {}
    visible = []
    for item in matched[:MAX_VISIBLE_STOPS]:
        stop = dict(item)
        stop["next_theoretical_times"] = next_times.get(item["id"], [])
        visible.append(stop)
    return {
        "source": request.app.state.stops.source,
        "coverage": ["Montevideo"],
        "stops": visible,
        "total_matched": len(matched),
        "truncated": len(matched) > MAX_VISIBLE_STOPS,
        "limit": MAX_VISIBLE_STOPS,
    }


@router.get("/lines/{line}")
async def line_details(request: Request, line: str, company: str | None = Query(default=None, min_length=1, max_length=40)):
    payload = request.app.state.lines.details(line, company)
    if payload is None:
        raise HTTPException(status_code=404, detail="line not found in official route data")
    stop_ids = {
        stop_id
        for route in payload["routes"]
        for stop_id in route.get("stop_ids", [])
    }
    snapshot = await request.app.state.cache.get()
    vehicles = [] if snapshot is None else [item for item in snapshot.vehicles if item.route.casefold() == line.casefold()]
    return {
        "sources": payload["sources"],
        "line": payload["line"],
        "routes": payload["routes"],
        "route_count": len(payload["routes"]),
        "stop_count": len(stop_ids),
        "live_vehicle_count": len(vehicles),
        "schedule_kind": "theoretical",
    }


@router.get("/stops/{stop_id}/arrivals")
async def stop_arrivals(request: Request, stop_id: str, line: str = Query(min_length=1, max_length=40)):
    stop = request.app.state.stops.get(stop_id)
    if stop is None:
        raise HTTPException(status_code=404, detail="stop not found")
    payload = request.app.state.lines.get(line)
    if payload is None:
        raise HTTPException(status_code=404, detail="line not found")
    snapshot = await request.app.state.cache.get()
    vehicles = [] if snapshot is None else [item for item in snapshot.vehicles if item.route.casefold() == line.casefold()]
    return {
        "stop_id": stop_id,
        "line": line,
        "freshness": snapshot.freshness if snapshot else "unavailable",
        "estimated_at": snapshot.received_at if snapshot else None,
        "arrivals": upcoming_vehicles(vehicles, payload["routes"], stop),
        "method": "gps-route-projection",
        "disclaimer": "Estimación aproximada; no es una predicción oficial de llegada.",
    }
