from datetime import datetime, timezone

from app.domain.models import CanonicalVehicle
from app.services.arrivals import progress_on_path, upcoming_vehicles


def vehicle(vehicle_id, longitude, variant="10", speed=18):
    return CanonicalVehicle(
        source_id="test", vehicle_id=vehicle_id, operator_code="1", operator_name="Test",
        route="1", variant=variant, longitude=longitude, latitude=-34.9,
        speed_kmh=speed, received_at=datetime.now(timezone.utc),
    )


ROUTE = {"variant_id": "10", "stop_ids": ["A"], "paths": [[[-34.9, -56.2], [-34.9, -56.1]]]}
STOP = {"id": "A", "latitude": -34.9, "longitude": -56.12}


def test_progress_increases_along_path():
    first = progress_on_path((-34.9, -56.19), ROUTE["paths"][0])
    second = progress_on_path((-34.9, -56.13), ROUTE["paths"][0])
    assert first[1] < second[1]


def test_only_vehicles_before_stop_on_same_variant_are_returned():
    result = upcoming_vehicles(
        [vehicle("before", -56.18), vehicle("after", -56.11), vehicle("other", -56.18, "99")],
        [ROUTE], STOP, now=datetime(2026, 9, 14, tzinfo=timezone.utc),
    )
    assert [item["vehicle_id"] for item in result] == ["before"]


def test_arrivals_are_sorted_by_future_eta():
    result = upcoming_vehicles(
        [vehicle("far", -56.19), vehicle("near", -56.13)], [ROUTE], STOP,
        now=datetime(2026, 9, 14, tzinfo=timezone.utc),
    )
    assert [item["vehicle_id"] for item in result] == ["near", "far"]
