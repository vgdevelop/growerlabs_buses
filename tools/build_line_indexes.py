"""Build compact per-line route and timetable indexes from official STM data."""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import re
import shutil
import tempfile
import zipfile
from collections import defaultdict
from contextlib import ExitStack
from datetime import date
from pathlib import Path

import shapefile
from pyproj import Transformer

SOURCE_DIR = Path("data/source")
OUTPUT_DIR = Path("app/data/lines")
TRANSFORMER = Transformer.from_crs("EPSG:32721", "EPSG:4326", always_xy=True)


def safe_name(line: str) -> str:
    return re.sub(r"[^A-Z0-9_-]", "_", line.upper())


def open_shape(zip_path: Path) -> shapefile.Reader:
    archive = zipfile.ZipFile(zip_path)
    base = next(name[:-4] for name in archive.namelist() if name.endswith(".shp"))
    reader = shapefile.Reader(
        shp=io.BytesIO(archive.read(base + ".shp")),
        shx=io.BytesIO(archive.read(base + ".shx")),
        dbf=io.BytesIO(archive.read(base + ".dbf")),
        encoding="utf-8",
    )
    reader._source_archive = archive
    return reader


def perpendicular_distance(point, start, end):
    if start == end:
        return math.dist(point, start)
    dx, dy = end[0] - start[0], end[1] - start[1]
    return abs(dy * point[0] - dx * point[1] + end[0] * start[1] - end[1] * start[0]) / math.hypot(dx, dy)


def simplify(points, tolerance=8.0):
    if len(points) <= 2:
        return points
    start, end = points[0], points[-1]
    index, maximum = 0, 0.0
    for position, point in enumerate(points[1:-1], 1):
        distance = perpendicular_distance(point, start, end)
        if distance > maximum:
            index, maximum = position, distance
    if maximum <= tolerance:
        return [start, end]
    return simplify(points[: index + 1], tolerance)[:-1] + simplify(points[index:], tolerance)


def coordinates(shape):
    result = []
    part_starts = list(shape.parts) + [len(shape.points)]
    for start, end in zip(part_starts, part_starts[1:]):
        projected = simplify(shape.points[start:end])
        result.append([[round(lat, 6), round(lon, 6)] for lon, lat in (TRANSFORMER.transform(x, y) for x, y in projected)])
    return result


def variant_data():
    lines = {}
    stop_ordinals = defaultdict(dict)
    reader = open_shape(SOURCE_DIR / "v_uptu_paradas.zip")
    for record in reader.iterRecords():
        values = record.as_dict()
        variant = str(values["COD_VARIAN"])
        lines[variant] = str(values["DESC_LINEA"]).strip().upper()
        stop_ordinals[variant][int(values["ORDINAL"])] = str(values["COD_UBIC_P"])
    stops = {variant: [items[key] for key in sorted(items)] for variant, items in stop_ordinals.items()}
    return lines, stops


def route_items(variant_lines, variant_stops):
    by_line = defaultdict(list)
    sources = [
        ("v_uptu_lsv_destinos.zip", "principal"),
        ("uptu_variante_no_maximal.zip", "parcial"),
        ("v_uptu_variantes_circulares.zip", "circular"),
    ]
    for filename, kind in sources:
        reader = open_shape(SOURCE_DIR / filename)
        for item in reader.iterShapeRecords():
            values = item.record.as_dict()
            variant = str(values["COD_VARIAN"])
            line = str(values.get("DESC_LINEA") or variant_lines.get(variant) or "").strip().upper()
            if not line:
                continue
            by_line[line].append({
                "variant_id": variant,
                "kind": kind,
                "direction": str(values.get("DESC_VARIA") or ""),
                "origin": str(values.get("DESC_ORIGE") or "").strip(),
                "destination": str(values.get("DESC_DESTI") or "").strip(),
                "stop_ids": variant_stops.get(variant, []),
                "paths": coordinates(item.shape),
            })
    return by_line


def spool_schedules(variant_lines, temporary: Path):
    handles = {}
    with ExitStack() as stack:
        for filename in ("uptu_pasada_variante.zip", "uptu_pasada_circular.zip"):
            with zipfile.ZipFile(SOURCE_DIR / filename) as archive:
                csv_name = next(name for name in archive.namelist() if name.endswith(".csv"))
                with archive.open(csv_name) as raw:
                    text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
                    for row in csv.DictReader(text, delimiter=";"):
                        cleaned = {key.strip(): (value or "").strip() for key, value in row.items()}
                        line = variant_lines.get(cleaned.get("cod_variante", ""))
                        if not line:
                            continue
                        if line not in handles:
                            handles[line] = stack.enter_context((temporary / f"{safe_name(line)}.csv").open("w", encoding="utf-8", newline=""))
                        handles[line].write(";".join((cleaned["cod_ubic_parada"], cleaned["tipo_dia"], cleaned["hora"])) + "\n")


def schedule_for(path: Path):
    by_stop = defaultdict(lambda: defaultdict(set))
    if path.exists():
        for row in path.read_text(encoding="utf-8").splitlines():
            stop, day_type, time = row.split(";")
            by_stop[stop][day_type].add(int(time))
    return {stop: {day: sorted(times) for day, times in days.items()} for stop, days in by_stop.items()}


def checksums():
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(SOURCE_DIR.glob("*.zip"))}


def main():
    variant_lines, variant_stops = variant_data()
    routes = route_items(variant_lines, variant_stops)
    metadata = {
        "publisher": "Intendencia de Montevideo",
        "license": "Licencia de Datos Abiertos de Uruguay",
        "retrieved_on": date.today().isoformat(),
        "catalog_routes": "https://catalogodatos.gub.uy/dataset/lineas-de-omnibus-origen-y-destino",
        "catalog_schedules": "https://catalogodatos.gub.uy/dataset/horarios-de-omnibus-urbanos-por-parada-stm",
        "checksums": checksums(),
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUTPUT_DIR.glob("*.json.gz"):
        old.unlink()
    with tempfile.TemporaryDirectory() as raw_temporary:
        temporary = Path(raw_temporary)
        spool_schedules(variant_lines, temporary)
        all_lines = sorted(set(routes) | set(variant_lines.values()))
        manifest = {"source": metadata, "lines": {}}
        for line in all_lines:
            schedule_path = temporary / f"{safe_name(line)}.csv"
            payload = {"line": line, "routes": routes.get(line, []), "schedule": schedule_for(schedule_path)}
            output = OUTPUT_DIR / f"{safe_name(line)}.json.gz"
            with gzip.open(output, "wt", encoding="utf-8", compresslevel=9) as target:
                json.dump(payload, target, ensure_ascii=False, separators=(",", ":"))
            manifest["lines"][line] = output.name
        (OUTPUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {len(manifest['lines'])} line indexes")


if __name__ == "__main__":
    main()
