"""Ephemeral, approximate stop arrivals derived from current GPS positions."""

import math
from datetime import datetime, timedelta, timezone

EARTH_METERS_PER_DEGREE = 111_320.0
MAX_DISTANCE_FROM_ROUTE_METERS = 250.0


def xy(point, reference_latitude):
    latitude, longitude = point
    return (
        longitude * EARTH_METERS_PER_DEGREE * math.cos(math.radians(reference_latitude)),
        latitude * EARTH_METERS_PER_DEGREE,
    )


def progress_on_path(point, path):
    if len(path) < 2:
        return None
    reference_latitude = point[0]
    target_x, target_y = xy(point, reference_latitude)
    progress = 0.0
    best = None
    for start, end in zip(path, path[1:]):
        start_x, start_y = xy(start, reference_latitude)
        end_x, end_y = xy(end, reference_latitude)
        dx, dy = end_x - start_x, end_y - start_y
        length_squared = dx * dx + dy * dy
        ratio = 0.0 if not length_squared else max(0.0, min(1.0, ((target_x - start_x) * dx + (target_y - start_y) * dy) / length_squared))
        projected_x, projected_y = start_x + ratio * dx, start_y + ratio * dy
        offset = math.hypot(target_x - projected_x, target_y - projected_y)
        segment_length = math.sqrt(length_squared)
        candidate = (offset, progress + ratio * segment_length)
        if best is None or candidate[0] < best[0]:
            best = candidate
        progress += segment_length
    return best


def upcoming_vehicles(vehicles, routes, stop, now=None, limit=8):
    current = now or datetime.now(timezone.utc)
    routes_by_variant = {str(route["variant_id"]): route for route in routes}
    stop_point = (stop["latitude"], stop["longitude"])
    arrivals = []
    for vehicle in vehicles:
        route = routes_by_variant.get(str(vehicle.variant or ""))
        if not route or stop["id"] not in route.get("stop_ids", []):
            continue
        path = [point for part in route["paths"] for point in part]
        vehicle_projection = progress_on_path((vehicle.latitude, vehicle.longitude), path)
        stop_projection = progress_on_path(stop_point, path)
        if not vehicle_projection or not stop_projection or vehicle_projection[0] > MAX_DISTANCE_FROM_ROUTE_METERS:
            continue
        remaining = stop_projection[1] - vehicle_projection[1]
        if remaining < -25:
            continue
        speed = vehicle.speed_kmh if vehicle.speed_kmh and vehicle.speed_kmh >= 8 else 18.0
        speed = min(speed, 40.0)
        minutes = max(1, math.ceil(max(0.0, remaining) / 1000 / speed * 60))
        arrivals.append({
            "vehicle_id": vehicle.vehicle_id,
            "operator_name": vehicle.operator_name,
            "destination": vehicle.destination,
            "variant": vehicle.variant,
            "distance_meters": round(max(0.0, remaining)),
            "eta_minutes": minutes,
            "estimated_arrival": (current + timedelta(minutes=minutes)).isoformat(),
            "method": "gps-route-projection",
        })
    return sorted(arrivals, key=lambda item: (item["eta_minutes"], item["distance_meters"]))[:limit]
