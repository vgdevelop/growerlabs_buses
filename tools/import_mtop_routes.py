"""Build compact per-operator/line routes from the official MTOP KML."""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date
from pathlib import Path

SOURCE = Path("data/source/recorridos_metropolitanos.kml")
OUTPUT_DIR = Path("app/data/metropolitan_routes")
CATALOG_URL = "https://catalogodatos.gub.uy/dataset/ministerio-de-transporte-y-obras-publicas-recorridos-omnibus-suburbanos"


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Z0-9_-]", "_", value.upper())


def perpendicular_distance(point, start, end):
    if start == end:
        return ((point[0] - start[0]) ** 2 + (point[1] - start[1]) ** 2) ** 0.5
    dx, dy = end[0] - start[0], end[1] - start[1]
    return abs(dy * point[0] - dx * point[1] + end[0] * start[1] - end[1] * start[0]) / (dx * dx + dy * dy) ** 0.5


def simplify(points, tolerance=0.00008):
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


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def placemark_data(element):
    fields = {
        item.attrib.get("name"): (item.text or "").strip()
        for item in element.iter()
        if local_name(item.tag) == "SimpleData"
    }
    paths = []
    for item in element.iter():
        if local_name(item.tag) != "coordinates" or not item.text:
            continue
        points = []
        for raw in item.text.split():
            lon, lat, *_ = raw.split(",")
            points.append((float(lat), float(lon)))
        if len(points) >= 2:
            paths.append([[round(lat, 6), round(lon, 6)] for lat, lon in simplify(points)])
    return fields, paths


def load_routes():
    routes = defaultdict(list)
    for _, element in ET.iterparse(SOURCE, events=("end",)):
        if local_name(element.tag) != "Placemark":
            continue
        fields, paths = placemark_data(element)
        company = fields.get("Cod_Empres", "").strip()
        line = fields.get("Caract", "").strip().upper()
        if company and line and paths:
            routes[(company, line)].append({
                "variant_id": fields.get("Variante", ""), "kind": "metropolitano",
                "direction": fields.get("Sentido", ""), "origin": fields.get("Origen", ""),
                "destination": fields.get("Destino", ""), "description": fields.get("Recorrido", ""),
                "operator_code": company, "operator_name": fields.get("Empresa", ""),
                "stop_ids": [], "paths": paths,
            })
        element.clear()
    return routes


def main():
    routes = load_routes()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUTPUT_DIR.glob("*.json.gz"):
        old.unlink()
    metadata = {
        "publisher": "Ministerio de Transporte y Obras Públicas - División Pasajeros DNT",
        "license": "Licencia de Datos Abiertos de Uruguay", "retrieved_on": date.today().isoformat(),
        "catalog": CATALOG_URL, "crs": "EPSG:4326", "sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    }
    manifest = {"source": metadata, "lines": {}}
    for (company, line), items in sorted(routes.items()):
        filename = f"{safe_name(company)}--{safe_name(line)}.json.gz"
        with gzip.open(OUTPUT_DIR / filename, "wt", encoding="utf-8", compresslevel=9) as target:
            json.dump({"line": line, "operator_code": company, "routes": items, "schedule": {}}, target,
                      ensure_ascii=False, separators=(",", ":"))
        manifest["lines"][f"{company}:{line}"] = filename
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {len(manifest['lines'])} metropolitan indexes with {sum(map(len, routes.values()))} variants")


if __name__ == "__main__":
    main()
