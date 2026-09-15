import json
from pathlib import Path

import pytest

from app.services.normalizer import normalize_stm_geojson

FIXTURES = Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIXTURES / name).read_text())


def test_valid_feature_collection_becomes_canonical():
    result = normalize_stm_geojson(load("stm_valid.geojson"))
    assert len(result.vehicles) == 2
    assert result.vehicles[0].event_time is None
    assert result.license_status == "pending-publisher-confirmation"


def test_invalid_coordinates_are_rejected():
    with pytest.raises(ValueError):
        normalize_stm_geojson(load("stm_invalid.geojson"))


def test_invalid_feature_does_not_discard_valid_vehicles():
    payload = load("stm_valid.geojson")
    payload["features"].extend(load("stm_invalid.geojson")["features"])
    result = normalize_stm_geojson(payload)
    assert len(result.vehicles) == 2
    assert "invalid features skipped: 1" in result.schema_warnings


def test_wgs84_placeholder_outside_stm_coverage_is_rejected():
    payload = load("stm_valid.geojson")
    payload["features"][0]["geometry"]["coordinates"] = [0, 0]
    result = normalize_stm_geojson(payload)
    assert len(result.vehicles) == 1
    assert "invalid features skipped: 1" in result.schema_warnings


def test_stm_is_not_presented_as_national_gps():
    result = normalize_stm_geojson(load("stm_valid.geojson"))
    assert "Uruguay" not in result.coverage
