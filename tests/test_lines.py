import gzip
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.lines import LineIndex, day_type


def make_index(tmp_path):
    payload = {"line": "10", "routes": [], "schedule": {"1": {"1": [900, 930]}}}
    with gzip.open(tmp_path / "10.json.gz", "wt", encoding="utf-8") as target:
        json.dump(payload, target)
    (tmp_path / "manifest.json").write_text(json.dumps({"source": {}, "lines": {"10": "10.json.gz"}}))
    return LineIndex(tmp_path)


def test_day_type():
    assert day_type(datetime(2026, 9, 14)) == "1"
    assert day_type(datetime(2026, 9, 19)) == "2"
    assert day_type(datetime(2026, 9, 20)) == "3"


def test_next_times_are_filtered_and_limited(tmp_path):
    index = make_index(tmp_path)
    now = datetime(2026, 9, 14, 9, 10, tzinfo=ZoneInfo("America/Montevideo"))
    assert index.next_times("10", ["1"], now=now) == {"1": ["2026-09-14T09:30:00-03:00", "2026-09-15T09:00:00-03:00", "2026-09-15T09:30:00-03:00"]}


def test_unknown_line_has_no_times(tmp_path):
    assert make_index(tmp_path).next_times("99", ["1"]) == {}


def test_metropolitan_routes_are_loaded_only_for_selected_company(tmp_path):
    urban, metro = tmp_path / "urban", tmp_path / "metro"
    urban.mkdir()
    metro.mkdir()
    (urban / "manifest.json").write_text(json.dumps({"source": {"publisher": "IM"}, "lines": {}}))
    with gzip.open(metro / "18--710.json.gz", "wt", encoding="utf-8") as target:
        json.dump({"line": "710", "routes": [{"variant_id": "1"}], "schedule": {}}, target)
    (metro / "manifest.json").write_text(json.dumps({
        "source": {"publisher": "MTOP"}, "lines": {"18:710": "18--710.json.gz"}}))
    index = LineIndex(urban, metro)
    assert index.details("710", "18")["routes"][0]["variant_id"] == "1"
    assert index.details("710", "35") is None
