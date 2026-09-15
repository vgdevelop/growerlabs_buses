"""On-demand access to compressed official route and timetable indexes."""

import gzip
import json
from datetime import datetime, time, timedelta
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

MONTEVIDEO = ZoneInfo("America/Montevideo")


def day_type(value) -> str:
    return "1" if value.weekday() < 5 else "2" if value.weekday() == 5 else "3"


class LineIndex:
    def __init__(self, directory: Path, metropolitan_directory: Path | None = None):
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        self.source = manifest["source"]
        self._directory = directory
        self._files = {line.casefold(): filename for line, filename in manifest["lines"].items()}
        self._metropolitan_directory = metropolitan_directory
        self._metropolitan_source = None
        self._metropolitan_files = {}
        if metropolitan_directory and (metropolitan_directory / "manifest.json").exists():
            metropolitan = json.loads((metropolitan_directory / "manifest.json").read_text(encoding="utf-8"))
            self._metropolitan_source = metropolitan["source"]
            self._metropolitan_files = {key.casefold(): filename for key, filename in metropolitan["lines"].items()}

    @lru_cache(maxsize=1)
    def get(self, line: str):
        filename = self._files.get(line.casefold())
        if not filename:
            return None
        with gzip.open(self._directory / filename, "rt", encoding="utf-8") as source:
            return json.load(source)

    @lru_cache(maxsize=1)
    def get_metropolitan(self, company: str, line: str):
        filename = self._metropolitan_files.get(f"{company}:{line}".casefold())
        if not filename or not self._metropolitan_directory:
            return None
        with gzip.open(self._metropolitan_directory / filename, "rt", encoding="utf-8") as source:
            return json.load(source)

    def details(self, line: str, company: str | None = None):
        urban = self.get(line)
        metropolitan = self.get_metropolitan(company, line) if company else None
        if not urban and not metropolitan:
            return None
        routes, schedule, sources = [], {}, []
        if urban:
            routes.extend(urban["routes"])
            schedule = urban["schedule"]
            sources.append(self.source)
        if metropolitan:
            routes.extend(metropolitan["routes"])
            sources.append(self._metropolitan_source)
        return {"line": line.upper(), "routes": routes, "schedule": schedule, "sources": sources}

    def next_times(self, line: str, stop_ids: list[str], now: datetime | None = None, limit: int = 3):
        payload = self.get(line)
        if not payload:
            return {}
        current = now.astimezone(MONTEVIDEO) if now else datetime.now(MONTEVIDEO)
        result = {}
        for stop_id in stop_ids:
            candidates = []
            schedule = payload["schedule"].get(stop_id, {})
            for offset in range(3):
                service_date = current.date() + timedelta(days=offset)
                for raw in schedule.get(day_type(service_date), []):
                    hour, minute = raw // 100, raw % 100
                    if hour > 23 or minute > 59:
                        continue
                    moment = datetime.combine(service_date, time(hour, minute), MONTEVIDEO)
                    if moment >= current:
                        candidates.append(moment)
            if candidates:
                result[stop_id] = [moment.isoformat() for moment in sorted(set(candidates))[:limit]]
        return result
