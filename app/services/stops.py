"""Read-only in-memory index of official Montevideo stops."""

import json
from pathlib import Path


class StopIndex:
    def __init__(self, path: Path):
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.source = payload["source"]
        self.count = payload["count"]
        self._by_line = {}
        self._by_id = {}
        for stop in payload["stops"]:
            self._by_id[stop["id"]] = stop
            for line in stop["lines"]:
                self._by_line.setdefault(line.casefold(), []).append(stop)

    def for_lines(self, lines: set[str]) -> list[dict]:
        matched = {}
        for line in lines:
            for stop in self._by_line.get(line.casefold(), []):
                matched[stop["id"]] = stop
        return list(matched.values())

    def get(self, stop_id: str):
        return self._by_id.get(stop_id)
