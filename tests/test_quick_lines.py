from pathlib import Path


STATIC = Path(__file__).resolve().parents[1] / "app" / "static"


def test_t1_and_t6_can_be_selected_without_current_gps_vehicles():
    page = (STATIC / "index.html").read_text(encoding="utf-8")
    script = (STATIC / "map.js").read_text(encoding="utf-8")

    assert 'data-quick-line="T1" data-company="35" data-always-selectable="true"' in page
    assert 'data-quick-line="T6" data-always-selectable="true"' in page
    assert "[...new Set([...filters.lines,...pinned])]" in script
    assert "new Set([...filters.lines,...pinned])" in script
