from datetime import datetime, timezone

from app.api.routes import MAX_VISIBLE_VEHICLES, filter_vehicles
from app.domain.models import CanonicalVehicle, LiveSnapshot


def vehicle(number: int, company: str = "A", line: str = "10"):
    return CanonicalVehicle(source_id="test", vehicle_id=str(number), operator_code=company,
                            operator_name=f"Company {company}", subsystem="Montevideo",
                            route=line, longitude=-56.1,
                            latitude=-34.8, received_at=datetime.now(timezone.utc))


def snapshot():
    return LiveSnapshot(source_id="test", coverage=["Montevideo"], license_status="test",
                        received_at=datetime.now(timezone.utc), freshness="live",
                        vehicles=[vehicle(1), vehicle(2, "B", "20")])


def test_company_filter_is_exact():
    assert [item.vehicle_id for item in filter_vehicles(snapshot(), "A", None)] == ["1"]


def test_line_filter_is_exact():
    assert [item.vehicle_id for item in filter_vehicles(snapshot(), None, "20")] == ["2"]


def test_defensive_result_limit_is_bounded():
    assert MAX_VISIBLE_VEHICLES == 300
