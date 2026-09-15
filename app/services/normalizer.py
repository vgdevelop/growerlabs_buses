from datetime import datetime, timezone
from typing import Any

from app.domain.models import CanonicalVehicle, LiveSnapshot
from app.domain.operators import operator_name

REQUIRED_PROPERTIES = {"codigoBus", "codigoEmpresa", "linea"}
KNOWN_PROPERTIES = REQUIRED_PROPERTIES | {
    "destino", "destinoDesc", "frecuencia", "id", "sublinea", "subsistema",
    "subsistemaDesc", "tipoLinea", "tipoLineaDesc", "variante", "velocidad", "version",
}


def normalize_stm_geojson(payload: dict[str, Any], received_at: datetime | None = None) -> LiveSnapshot:
    if payload.get("type") != "FeatureCollection" or not isinstance(payload.get("features"), list):
        raise ValueError("expected GeoJSON FeatureCollection")
    timestamp = received_at or datetime.now(timezone.utc)
    vehicles: list[CanonicalVehicle] = []
    unknown: set[str] = set()
    invalid_features = 0
    for feature in payload["features"]:
        try:
            geometry = feature.get("geometry") or {}
            properties = feature.get("properties") or {}
            if geometry.get("type") != "Point" or len(geometry.get("coordinates", [])) < 2:
                raise ValueError("feature does not contain a GeoJSON Point")
            missing = REQUIRED_PROPERTIES - properties.keys()
            if missing:
                raise ValueError("feature is missing required properties")
            unknown.update(properties.keys() - KNOWN_PROPERTIES)
            longitude, latitude = geometry["coordinates"][:2]
            longitude, latitude = float(longitude), float(latitude)
            if not (-58.0 <= longitude <= -54.0 and -35.5 <= latitude <= -33.0):
                raise ValueError("position outside declared STM coverage")
            speed = properties.get("velocidad")
            company_code = str(properties["codigoEmpresa"])
            vehicles.append(CanonicalVehicle(
                source_id="stm-realtime",
                vehicle_id=str(properties["codigoBus"]),
                operator_code=company_code,
                operator_name=operator_name(company_code),
                subsystem=_optional_text(properties.get("subsistemaDesc") or properties.get("subsistema")),
                route=str(properties["linea"]),
                variant=_optional_text(properties.get("variante")),
                destination=_optional_text(properties.get("destinoDesc") or properties.get("destino")),
                longitude=longitude, latitude=latitude,
                speed_kmh=float(speed) if speed not in (None, "") else None,
                event_time=None, received_at=timestamp,
            ))
        except (KeyError, TypeError, ValueError):
            invalid_features += 1
    if payload["features"] and not vehicles:
        raise ValueError("FeatureCollection contains no valid vehicle positions")
    warnings = [f"unknown property: {name}" for name in sorted(unknown)]
    if invalid_features:
        warnings.append(f"invalid features skipped: {invalid_features}")
    return LiveSnapshot(
        source_id="stm-realtime",
        coverage=["Montevideo", "Canelones", "San José", "Metropolitano"],
        license_status="pending-publisher-confirmation",
        received_at=timestamp,
        freshness="live",
        vehicles=vehicles,
        schema_warnings=warnings,
    )


def _optional_text(value: Any) -> str | None:
    return None if value in (None, "") else str(value)
