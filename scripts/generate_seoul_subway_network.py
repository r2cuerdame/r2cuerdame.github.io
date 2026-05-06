#!/usr/bin/env python3
"""Generate static Seoul subway network SVG data for the Dongne Radar map.

Sources:
- OpenStreetMap Overpass build-time extraction for subway/light-rail/rail geometry
- Existing Seoul outline projection data (data/seoul-map-outline.json)

The generated JSON is checked into the static site so GitHub Pages never needs a
browser API key or live map call.
"""
from __future__ import annotations

import json
import math
import re
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
OUTLINE_PATH = ROOT / "data" / "seoul-map-outline.json"
OUT = ROOT / "data" / "seoul-subway-network.json"
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
USER_AGENT = "RecuerdameLab SeoulSubwayNetworkBuilder/1.0 (static OSM data)"

# OSM bbox intentionally covers Seoul plus the immediate metro collar so lines
# enter/exit the city naturally instead of stopping at the administrative edge.
BBOX = (37.405, 126.735, 37.715, 127.225)  # south, west, north, east

LINE_META: dict[str, dict[str, str]] = {
    "line1": {"label": "1호선", "color": "#0052A4", "short": "1"},
    "line2": {"label": "2호선", "color": "#00A84D", "short": "2"},
    "line3": {"label": "3호선", "color": "#EF7C1C", "short": "3"},
    "line4": {"label": "4호선", "color": "#00A5DE", "short": "4"},
    "line5": {"label": "5호선", "color": "#996CAC", "short": "5"},
    "line6": {"label": "6호선", "color": "#CD7C2F", "short": "6"},
    "line7": {"label": "7호선", "color": "#747F00", "short": "7"},
    "line8": {"label": "8호선", "color": "#E6186C", "short": "8"},
    "line9": {"label": "9호선", "color": "#BDB092", "short": "9"},
    "airport": {"label": "공항철도", "color": "#0090D2", "short": "A"},
    "gyeongui": {"label": "경의중앙", "color": "#77C4A3", "short": "GJ"},
    "gyeongchun": {"label": "경춘선", "color": "#0C8E72", "short": "GC"},
    "bundang": {"label": "수인분당", "color": "#F5A200", "short": "SU"},
    "sinbundang": {"label": "신분당", "color": "#D4003B", "short": "SB"},
    "ui_sinseol": {"label": "우이신설", "color": "#B0CE18", "short": "UI"},
    "sillim": {"label": "신림선", "color": "#6789CA", "short": "SL"},
    "seohae": {"label": "서해선", "color": "#8FC31F", "short": "SH"},
    "gtx_a": {"label": "GTX-A", "color": "#9A6292", "short": "GTX"},
}

# Reference-site style labels: major hubs and the user's commercial 후보역.
LABEL_PRIORITY: dict[str, dict[str, Any]] = {
    "홍대입구": {"line": "2", "dx": -92, "dy": -32, "level": "major"},
    "신촌": {"line": "2", "dx": -78, "dy": 18, "level": "major"},
    "합정": {"line": "2", "dx": -72, "dy": 28, "level": "major"},
    "여의도": {"line": "5", "dx": -82, "dy": 26, "level": "transfer"},
    "서울역": {"line": "1", "dx": -78, "dy": -28, "level": "transfer"},
    "종로3가": {"line": "1·3·5", "dx": -84, "dy": -34, "level": "transfer"},
    "왕십리": {"line": "2·5", "dx": 18, "dy": -42, "level": "transfer"},
    "성수": {"line": "2", "dx": 18, "dy": -32, "level": "major"},
    "건대입구": {"line": "2·7", "dx": 18, "dy": 14, "level": "transfer"},
    "잠실": {"line": "2·8", "dx": 20, "dy": -26, "level": "transfer"},
    "강남": {"line": "2", "dx": 22, "dy": 18, "level": "major"},
    "신사": {"line": "3·SB", "dx": 18, "dy": -36, "level": "transfer"},
    "압구정": {"line": "3", "dx": 18, "dy": -34, "level": "major"},
    "사당": {"line": "2·4", "dx": -70, "dy": 28, "level": "transfer"},
    "신림": {"line": "2", "dx": -58, "dy": 20, "level": "major"},
    "가산디지털단지": {"line": "1·7", "dx": -126, "dy": 22, "level": "transfer"},
    "문래": {"line": "2", "dx": -66, "dy": 20, "level": "major"},
    "마곡나루": {"line": "9·A", "dx": -92, "dy": -24, "level": "transfer"},
    "연신내": {"line": "3·6", "dx": -80, "dy": -28, "level": "transfer"},
    "청량리": {"line": "1", "dx": 20, "dy": -32, "level": "transfer"},
    "고속터미널": {"line": "3·7·9", "dx": 18, "dy": 22, "level": "transfer"},
}

TRANSFER_NAMES = {name for name, meta in LABEL_PRIORITY.items() if meta.get("level") == "transfer"}


def fetch_json(url: str, data: bytes | None = None, timeout: int = 120) -> Any:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def normalize_line(tags: dict[str, Any]) -> str | None:
    text = " ".join(str(tags.get(k, "")) for k in ["name", "name:ko", "name:en", "ref", "line", "alt_name"])
    checks = [
        ("line1", r"서울\s*지하철\s*1호선|\b1호선\b|\bLine\s*1\b|\b1\b"),
        ("line2", r"2호선|성수지선|신정지선|\bLine\s*2\b|\b2\b"),
        ("line3", r"3호선|일산선|\bLine\s*3\b|\b3\b"),
        ("line4", r"4호선|과천선|진접선|\bLine\s*4\b|\b4\b"),
        ("line5", r"5호선|마천지선|하남선|\bLine\s*5\b|\b5\b"),
        ("line6", r"6호선|\bLine\s*6\b|\b6\b"),
        ("line7", r"7호선|\bLine\s*7\b|\b7\b"),
        ("line8", r"8호선|별내선|\bLine\s*8\b|\b8\b"),
        ("line9", r"9호선|\bLine\s*9\b|\b9\b"),
        ("airport", r"공항철도|공항선|인천국제공항선|AREX|Airport"),
        ("sinbundang", r"신분당|Sinbundang"),
        ("gyeongui", r"경의|중앙선|용산선|Gyeongui|Jungang"),
        ("gyeongchun", r"경춘|Gyeongchun"),
        ("bundang", r"분당|수인|Suin|Bundang"),
        ("ui_sinseol", r"우이신설|Ui"),
        ("sillim", r"신림선|Sillim"),
        ("seohae", r"서해선|Seohae"),
        ("gtx_a", r"GTX|수도권광역급행철도에이"),
    ]
    for line_id, pattern in checks:
        if re.search(pattern, text, re.I):
            return line_id
    return None


def load_projection() -> tuple[dict[str, Any], Any]:
    outline = json.loads(OUTLINE_PATH.read_text(encoding="utf-8-sig"))
    bounds = outline["bounds"]
    padding = outline.get("padding", {"x": 46, "y": 44})
    width = float(outline.get("width") or 1000)
    height = float(outline.get("height") or 680)
    pad_x = float(padding.get("x", 46))
    pad_y = float(padding.get("y", 44))
    min_lon = float(bounds["min_lon"])
    max_lon = float(bounds["max_lon"])
    min_lat = float(bounds["min_lat"])
    max_lat = float(bounds["max_lat"])

    def project(lon: float, lat: float) -> tuple[float, float]:
        x = pad_x + (lon - min_lon) / (max_lon - min_lon) * (width - pad_x * 2)
        y = pad_y + (max_lat - lat) / (max_lat - min_lat) * (height - pad_y * 2)
        return x, y

    return outline, project


def path_from_geometry(points: Iterable[dict[str, float]], project) -> str:
    parts: list[str] = []
    last: tuple[float, float] | None = None
    for item in points:
        lon = float(item["lon"])
        lat = float(item["lat"])
        x, y = project(lon, lat)
        # Keep a little outside the viewBox; SVG clipping/canvas hides excess but
        # line entrances remain continuous near the boundary.
        if x < -90 or x > 1090 or y < -90 or y > 770:
            continue
        if last and math.hypot(x - last[0], y - last[1]) < 1.6:
            continue
        parts.append(("M" if not parts else "L") + f"{x:.1f},{y:.1f}")
        last = (x, y)
    return " ".join(parts)


def fetch_overpass() -> dict[str, Any]:
    south, west, north, east = BBOX
    query = f"""[out:json][timeout:90];
(
  way["railway"~"subway|light_rail|rail"]({south},{west},{north},{east});
  node["railway"="station"]["station"~"subway|light_rail"]({south},{west},{north},{east});
  node["public_transport"="station"]["station"~"subway|light_rail"]({south},{west},{north},{east});
);
out tags geom;"""
    encoded = urllib.parse.urlencode({"data": query}).encode()
    last_error: Exception | None = None
    for url in OVERPASS_URLS:
        try:
            return fetch_json(url, data=encoded, timeout=150)
        except Exception as exc:  # pragma: no cover - network fallback
            last_error = exc
            time.sleep(1.5)
    raise SystemExit(f"Overpass subway network fetch failed: {last_error}")


def station_key(name: str, lat: float, lon: float) -> str:
    # Prefer a clean name key. If OSM contains duplicate nodes for different
    # platforms, keeping one label is better than drawing a stack of identical dots.
    clean = re.sub(r"역$", "", name.strip())
    if clean == "서울":
        clean = "서울역"
    return clean or f"{lat:.4f},{lon:.4f}"


def main() -> None:
    outline, project = load_projection()
    data = fetch_overpass()
    line_segments: dict[str, list[str]] = defaultdict(list)
    way_counts: Counter[str] = Counter()
    raw_station_points: dict[str, dict[str, Any]] = {}
    duplicate_names: Counter[str] = Counter()

    for element in data.get("elements", []):
        if element.get("type") != "way":
            continue
        tags = element.get("tags") or {}
        service = str(tags.get("service", ""))
        if service in {"yard", "crossover", "siding", "spur"}:
            continue
        line_id = normalize_line(tags)
        if not line_id:
            continue
        # Avoid ordinary long-distance railways unless they are part of the metro
        # system we intentionally render.
        if tags.get("railway") == "rail" and line_id not in {"airport", "gyeongui", "gyeongchun", "bundang", "sinbundang", "gtx_a", "line1", "line3", "line4", "seohae"}:
            continue
        d = path_from_geometry(element.get("geometry") or [], project)
        if d.count("L") < 1:
            continue
        line_segments[line_id].append(d)
        way_counts[line_id] += 1

    for element in data.get("elements", []):
        if element.get("type") != "node":
            continue
        tags = element.get("tags") or {}
        name = str(tags.get("name:ko") or tags.get("name") or "").strip()
        if not name:
            continue
        clean_name = station_key(name, float(element.get("lat")), float(element.get("lon")))
        x, y = project(float(element.get("lon")), float(element.get("lat")))
        if x < -35 or x > 1035 or y < -35 or y > 715:
            continue
        duplicate_names[clean_name] += 1
        existing = raw_station_points.get(clean_name)
        station = {
            "id": re.sub(r"[^0-9A-Za-z가-힣]+", "-", clean_name).strip("-").lower(),
            "name": clean_name,
            "lat": round(float(element.get("lat")), 7),
            "lng": round(float(element.get("lon")), 7),
            "x": round(x, 1),
            "y": round(y, 1),
            "major": clean_name in LABEL_PRIORITY,
            "transfer": clean_name in TRANSFER_NAMES,
        }
        if not existing or station["major"]:
            raw_station_points[clean_name] = station

    for name, count in duplicate_names.items():
        if count >= 2 and name in raw_station_points:
            raw_station_points[name]["transfer"] = True

    labels = []
    for name, meta in LABEL_PRIORITY.items():
        station = raw_station_points.get(name)
        if not station:
            continue
        labels.append({
            "name": name,
            "x": station["x"],
            "y": station["y"],
            "line": meta["line"],
            "dx": meta["dx"],
            "dy": meta["dy"],
            "level": meta["level"],
        })
        station["major"] = True
        station["transfer"] = station["transfer"] or meta["level"] == "transfer"

    ordered_lines = []
    for line_id in ["line1", "line2", "line3", "line4", "line5", "line6", "line7", "line8", "line9", "airport", "gyeongui", "gyeongchun", "bundang", "sinbundang", "ui_sinseol", "sillim", "seohae", "gtx_a"]:
        segments = line_segments.get(line_id) or []
        if not segments:
            continue
        meta = LINE_META[line_id]
        ordered_lines.append({
            "id": line_id,
            "label": meta["label"],
            "short": meta["short"],
            "color": meta["color"],
            "segments": segments,
            "segment_count": len(segments),
        })

    stations = sorted(raw_station_points.values(), key=lambda s: (not s.get("major"), s["name"]))
    payload = {
        "version": "2026-05-seoul-subway-osm-network-v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "view_box": outline.get("view_box", "0 0 1000 680"),
        "width": outline.get("width", 1000),
        "height": outline.get("height", 680),
        "bounds": outline.get("bounds", {}),
        "source": {
            "name": "OpenStreetMap Overpass",
            "url": "https://www.openstreetmap.org/",
            "scope": "Seoul metro rail/subway/light-rail geometry and station nodes, build-time static extraction",
        },
        "lines": ordered_lines,
        "stations": stations,
        "labels": labels,
        "stats": {
            "line_count": len(ordered_lines),
            "segment_count": sum(len(line["segments"]) for line in ordered_lines),
            "station_count": len(stations),
            "label_count": len(labels),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        f"wrote {OUT.relative_to(ROOT)} with {payload['stats']['line_count']} lines, "
        f"{payload['stats']['segment_count']} segments, {payload['stats']['station_count']} stations, "
        f"{payload['stats']['label_count']} labels"
    )


if __name__ == "__main__":
    main()
