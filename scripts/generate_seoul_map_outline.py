#!/usr/bin/env python3
"""Generate static Seoul map outline data for the Dongne Radar home widget.

Sources:
- South Korea municipality GeoJSON (KOSTAT-derived, public GitHub mirror)
- OpenStreetMap Overpass geometry for the Han River centerline

The site consumes the generated JSON at build time, so GitHub Pages users do not
need any API key and the browser does not fetch live map services.
"""
from __future__ import annotations

import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterable, Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "seoul-map-outline.json"
MUNICIPALITIES_URL = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_municipalities_geo_simple.json"
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
SEOUL_PREFIX = "11"
WIDTH = 1000
HEIGHT = 680
PAD_X = 46
PAD_Y = 44
USER_AGENT = "RecuerdameLab SeoulOutlineBuilder/1.0 (static public data)"


def fetch_json(url: str, data: bytes | None = None, timeout: int = 60) -> Any:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def iter_positions(geometry: dict[str, Any]) -> Iterable[tuple[float, float]]:
    kind = geometry.get("type")
    coords = geometry.get("coordinates") or []
    if kind == "Polygon":
        for ring in coords:
            for lon, lat in ring:
                yield float(lon), float(lat)
    elif kind == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                for lon, lat in ring:
                    yield float(lon), float(lat)


def iter_rings(geometry: dict[str, Any]) -> Iterable[list[tuple[float, float]]]:
    kind = geometry.get("type")
    coords = geometry.get("coordinates") or []
    if kind == "Polygon":
        for ring in coords:
            yield [(float(lon), float(lat)) for lon, lat in ring]
    elif kind == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                yield [(float(lon), float(lat)) for lon, lat in ring]


def make_projector(points: list[tuple[float, float]]):
    mean_lat = sum(lat for _, lat in points) / max(1, len(points))
    cos_lat = math.cos(math.radians(mean_lat))

    def raw(lon: float, lat: float) -> tuple[float, float]:
        return lon * cos_lat, lat

    raw_points = [raw(lon, lat) for lon, lat in points]
    min_x = min(x for x, _ in raw_points)
    max_x = max(x for x, _ in raw_points)
    min_y = min(y for _, y in raw_points)
    max_y = max(y for _, y in raw_points)

    def project(lon: float, lat: float) -> tuple[float, float]:
        x, y = raw(lon, lat)
        px = PAD_X + (x - min_x) / (max_x - min_x) * (WIDTH - PAD_X * 2)
        py = PAD_Y + (max_y - y) / (max_y - min_y) * (HEIGHT - PAD_Y * 2)
        return px, py

    return project, {
        "min_lon": min(lon for lon, _ in points),
        "min_lat": min(lat for _, lat in points),
        "max_lon": max(lon for lon, _ in points),
        "max_lat": max(lat for _, lat in points),
        "mean_lat": mean_lat,
        "projection": "equirectangular_cos_mean_lat",
    }


def path_from_ring(ring: list[tuple[float, float]], project) -> str:
    if not ring:
        return ""
    parts: list[str] = []
    for i, (lon, lat) in enumerate(ring):
        x, y = project(lon, lat)
        cmd = "M" if i == 0 else "L"
        parts.append(f"{cmd}{x:.1f},{y:.1f}")
    return " ".join(parts) + " Z"


def line_path(points: list[tuple[float, float]], project) -> str:
    parts: list[str] = []
    for i, (lon, lat) in enumerate(points):
        x, y = project(lon, lat)
        cmd = "M" if i == 0 else "L"
        parts.append(f"{cmd}{x:.1f},{y:.1f}")
    return " ".join(parts)


def fetch_han_river() -> list[tuple[float, float]]:
    query = """[out:json][timeout:30];
(
  way["waterway"="river"]["name"~"한강|Han River"](37.42,126.75,37.70,127.20);
);
out geom;"""
    encoded = urllib.parse.urlencode({"data": query}).encode()
    last_error: Exception | None = None
    for url in OVERPASS_URLS:
        try:
            data = fetch_json(url, data=encoded, timeout=50)
            ways = [el for el in data.get("elements", []) if el.get("type") == "way" and el.get("geometry")]
            if not ways:
                continue
            # Longest geometry is the main through-Seoul river segment.
            geometry = max(ways, key=lambda el: len(el.get("geometry", []))).get("geometry", [])
            return [(float(p["lon"]), float(p["lat"])) for p in geometry]
        except Exception as exc:  # pragma: no cover - network fallback
            last_error = exc
            time.sleep(1)
    # Conservative fallback: actual lon/lat guide points through Seoul, used only
    # if Overpass mirrors are unavailable while refreshing the checked-in JSON.
    if last_error:
        print(f"warning: Overpass Han River fetch failed: {last_error}")
    return [
        (126.782, 37.585), (126.835, 37.565), (126.890, 37.535),
        (126.945, 37.523), (126.995, 37.520), (127.045, 37.525),
        (127.095, 37.525), (127.145, 37.545), (127.177, 37.565),
    ]


def main() -> None:
    municipalities = fetch_json(MUNICIPALITIES_URL)
    districts = [
        feature for feature in municipalities.get("features", [])
        if str(feature.get("properties", {}).get("code", "")).startswith(SEOUL_PREFIX)
    ]
    if len(districts) != 25:
        raise SystemExit(f"expected 25 Seoul districts, got {len(districts)}")

    all_points: list[tuple[float, float]] = []
    for district in districts:
        all_points.extend(iter_positions(district["geometry"]))
    project, bounds = make_projector(all_points)

    rendered = []
    for feature in sorted(districts, key=lambda f: f["properties"]["code"]):
        rings = [path_from_ring(ring, project) for ring in iter_rings(feature["geometry"])]
        ring_points = list(iter_positions(feature["geometry"]))
        cx = sum(project(lon, lat)[0] for lon, lat in ring_points) / max(1, len(ring_points))
        cy = sum(project(lon, lat)[1] for lon, lat in ring_points) / max(1, len(ring_points))
        rendered.append({
            "code": feature["properties"]["code"],
            "name": feature["properties"]["name"],
            "name_eng": feature["properties"].get("name_eng", ""),
            "path": " ".join(rings),
            "label_x": round(cx, 1),
            "label_y": round(cy, 1),
        })

    river_points = fetch_han_river()
    min_lon, max_lon = bounds["min_lon"] - 0.015, bounds["max_lon"] + 0.015
    min_lat, max_lat = bounds["min_lat"] - 0.015, bounds["max_lat"] + 0.015
    river_points = [(lon, lat) for lon, lat in river_points if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat] or river_points
    payload = {
        "version": "2026-05-seoul-outline-osm-kostat-v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "view_box": f"0 0 {WIDTH} {HEIGHT}",
        "width": WIDTH,
        "height": HEIGHT,
        "padding": {"x": PAD_X, "y": PAD_Y},
        "bounds": bounds,
        "sources": [
            {
                "name": "KOSTAT administrative district GeoJSON mirror",
                "url": MUNICIPALITIES_URL,
                "scope": "서울특별시 25개 자치구 행정경계 outline",
            },
            {
                "name": "OpenStreetMap Overpass",
                "url": "https://www.openstreetmap.org/",
                "scope": "한강 river geometry, build-time static extraction",
            },
        ],
        "districts": rendered,
        "river": {
            "name": "한강",
            "path": line_path(river_points, project),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)} with {len(rendered)} districts")


if __name__ == "__main__":
    main()
