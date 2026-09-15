import json

from app.services.stops import StopIndex


def write_index(tmp_path, stops):
    path = tmp_path / "stops.json"
    path.write_text(json.dumps({"source": {}, "count": len(stops), "stops": stops}))
    return StopIndex(path)


def test_stop_index_deduplicates_shared_stops(tmp_path):
    index = write_index(tmp_path, [
        {"id": "1", "lines": ["10", "20"]},
        {"id": "2", "lines": ["20"]},
    ])
    assert {item["id"] for item in index.for_lines({"10", "20"})} == {"1", "2"}


def test_stop_index_matches_lines_case_insensitively(tmp_path):
    index = write_index(tmp_path, [{"id": "1", "lines": ["D10"]}])
    assert index.for_lines({"d10"})[0]["id"] == "1"
