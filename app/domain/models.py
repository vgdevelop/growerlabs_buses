from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class CanonicalVehicle(BaseModel):
    source_id: str
    vehicle_id: str
    operator_code: str
    operator_name: str
    subsystem: str | None = None
    route: str
    variant: str | None = None
    destination: str | None = None
    longitude: float
    latitude: float
    speed_kmh: float | None = Field(default=None, ge=0)
    event_time: datetime | None = None
    received_at: datetime

    @field_validator("longitude")
    @classmethod
    def longitude_is_valid(cls, value: float) -> float:
        if not -180 <= value <= 180:
            raise ValueError("longitude outside WGS84 bounds")
        return value

    @field_validator("latitude")
    @classmethod
    def latitude_is_valid(cls, value: float) -> float:
        if not -90 <= value <= 90:
            raise ValueError("latitude outside WGS84 bounds")
        return value


class LiveSnapshot(BaseModel):
    source_id: str
    coverage: list[str]
    license_status: str
    received_at: datetime
    freshness: Literal["live", "stale", "unavailable"]
    vehicles: list[CanonicalVehicle]
    schema_warnings: list[str] = []


class DatasetMetadata(BaseModel):
    source_id: str
    resource_url: str
    checksum_sha256: str
    schema_version: str
    license: str
    captured_at: datetime
    metadata: dict[str, Any] = {}
