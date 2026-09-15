"""Build a compact runtime stop index from the official Montevideo Shape."""

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

import shapefile
from pyproj import Transformer

CATALOG_URL = "https://catalogodatos.gub.uy/dataset/transporte-colectivo-paradas-puntos-de-control-y-recorridos-de-omnibus"
DOWNLOAD_URL = "http://intgis.montevideo.gub.uy/sit/php/common/datos/generar_zip2.php?nom_tab=v_uptu_paradas&tipo=gis"


def build_index(shape_path: Path, source_zip: Path) -> dict:
    transformer = Transformer.from_crs("EPSG:32721", "EPSG:4326", always_xy=True)
    stops = {}
    lines_by_stop = defaultdict(set)
    reader = shapefile.Reader(str(shape_path), encoding="utf-8")
    for item in reader.iterShapeRecords():
        record = item.record.as_dict()
        stop_id = str(record["COD_UBIC_P"])
        line = str(record.get("DESC_LINEA") or "").strip().upper()
        longitude, latitude = transformer.transform(*item.shape.points[0])
        stops.setdefault(stop_id, {
            "id": stop_id,
            "street": str(record.get("CALLE") or "").strip(),
            "corner": str(record.get("ESQUINA") or "").strip(),
            "latitude": round(latitude, 6),
            "longitude": round(longitude, 6),
        })
        if line:
            lines_by_stop[stop_id].add(line)
    result = []
    for stop_id in sorted(stops, key=int):
        stop = stops[stop_id]
        stop["lines"] = sorted(lines_by_stop[stop_id], key=lambda value: (len(value), value))
        result.append(stop)
    return {
        "source": {
            "id": "imm-official-stops",
            "publisher": "Intendencia de Montevideo",
            "catalog_url": CATALOG_URL,
            "download_url": DOWNLOAD_URL,
            "license": "Licencia de Datos Abiertos de Uruguay",
            "retrieved_on": date.today().isoformat(),
            "source_sha256": hashlib.sha256(source_zip.read_bytes()).hexdigest(),
            "crs_source": "EPSG:32721",
            "crs_runtime": "EPSG:4326",
        },
        "count": len(result),
        "stops": result,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shape", type=Path, required=True)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build_index(args.shape, args.source_zip)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {payload['count']} unique stops to {args.output}")


if __name__ == "__main__":
    main()
