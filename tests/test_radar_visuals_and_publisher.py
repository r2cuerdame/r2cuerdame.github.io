from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KST = dt.timezone(dt.timedelta(hours=9))


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_adaptive_publisher_keeps_daily_floor_when_queue_below_target(monkeypatch):
    publisher = load_module(ROOT / "scripts" / "publish_next_radar_candidate.py", "radar_publisher_floor")
    at = dt.datetime(2026, 5, 5, 8, 25, tzinfo=KST)
    monkeypatch.setattr(publisher, "published_times", lambda: {})
    args = argparse.Namespace(mode="adaptive", max_per_day=4, min_interval_hours=2.0, ready_target=7)
    candidate = {
        "slug": "bus-stop-front-home-check",
        "title": "버스정류장 앞 집, 편한 위치인지 피곤한 위치인지 보는 10분",
        "review_ready": True,
        "target_fit": True,
        "hard_issues": [],
        "soft_issues": [],
        "published": False,
        "eligible": True,
    }

    decision = publisher.decide(args, [candidate], at)

    assert decision["status"] == "selected"
    assert decision["selected"]["slug"] == "bus-stop-front-home-check"
    assert decision["counts"]["ready_unpublished"] == 1
    assert decision["guards"]["daily_floor_open"] is True


def test_adaptive_publisher_waits_after_daily_floor_when_queue_is_low(monkeypatch):
    publisher = load_module(ROOT / "scripts" / "publish_next_radar_candidate.py", "radar_publisher_after_floor")
    at = dt.datetime(2026, 5, 5, 12, 25, tzinfo=KST)
    monkeypatch.setattr(
        publisher,
        "published_times",
        lambda: {"already-published": dt.datetime(2026, 5, 5, 8, 30, tzinfo=KST)},
    )
    args = argparse.Namespace(mode="adaptive", max_per_day=4, min_interval_hours=2.0, ready_target=7)
    candidate = {
        "slug": "window-distance-daylight-privacy-check",
        "title": "창밖이 가까운 집, 채광보다 먼저 볼 거리감 체크",
        "review_ready": True,
        "target_fit": True,
        "hard_issues": [],
        "soft_issues": [],
        "published": False,
        "eligible": True,
    }

    decision = publisher.decide(args, [candidate], at)

    assert decision["status"] == "slot_closed"
    assert decision["selected"] is None
    assert decision["guards"]["daily_floor_open"] is False
    assert any("ready_unpublished=1<=ready_target=7" in reason for reason in decision["reasons"])


def test_publisher_stages_all_generated_static_outputs():
    publisher = load_module(ROOT / "scripts" / "publish_next_radar_candidate.py", "radar_publisher_paths")

    for required in ["404.html", "main.css", "assets/search.js", "deals", "radar", "topics", "search/index.html"]:
        assert required in publisher.PUBLIC_ADD_PATHS


def test_radar_articles_have_content_matched_webp_thumbnails():
    for path in sorted((ROOT / "content" / "radar").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        image_url = str(data.get("image_url") or "")
        assert image_url.startswith("/assets/radar/thumbs/"), path.name
        assert image_url.endswith(".webp"), path.name
        asset = ROOT / image_url.lstrip("/")
        assert asset.exists(), f"missing thumbnail asset for {path.name}: {asset}"
        assert asset.stat().st_size > 20_000, f"thumbnail asset too small for {path.name}: {asset.stat().st_size}"


def test_radar_example_gallery_adds_scene_map_and_comparison_markers():
    build_site = load_module(ROOT / "scripts" / "build_site.py", "build_site_visuals")
    article = {
        "slug": "bus-stop-front-home-check",
        "section": "radar",
        "path": "/radar/bus-stop-front-home-check/",
        "title": "버스정류장 앞 집, 편한 위치인지 피곤한 위치인지 보는 10분",
        "description": "정류장 가까움이 편의인지 소음과 대기열 피로인지 확인하는 글",
        "tags": ["버스정류장", "밤길", "소음", "생활권"],
        "body_html": "<h2>정류장 앞 장점과 반례</h2><p>현장 질문으로 확인합니다.</p>",
    }

    html = build_site.radar_example_gallery(article)

    assert 'class="radar-example-gallery"' in html
    assert html.count('class="example-scene-card') >= 3
    assert 'class="radar-situation-strip"' in html
    assert "예시 장면" in html
    assert "현장 질문" in html
