from __future__ import annotations

import argparse
import datetime as dt
import hashlib
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

    for required in ["404.html", "main.css", "assets/search.js", "assets/commercial-check.js", "assets/radar", "data/seoul-commercial-areas.json", "data/seoul-map-outline.json", "data/seoul-subway-network.json", "scripts/publish_next_radar_candidate.py", "deals", "radar", "topics", "search/index.html"]:
        assert required in publisher.PUBLIC_ADD_PATHS


def test_home_has_above_fold_seoul_density_tool():
    build_site = load_module(ROOT / "scripts" / "build_site.py", "build_site_home_tool")

    html = build_site.home_body([], [])

    assert 'href="#commercial-check-tool"' in html
    assert 'id="commercial-check-tool"' in html
    assert 'data-seoul-density-tool-root' in html
    assert 'class="seoul-map-card"' in html
    assert 'class="seoul-real-map"' in html
    assert 'class="seoul-subway-map"' in html
    assert 'class="seoul-subway-line"' in html
    assert 'class="seoul-subway-stations"' in html
    assert 'data-subway-station-node=' in html
    assert 'class="subway-line-key"' in html
    assert 'data-map-viewport' in html
    assert 'data-map-toggle="districts"' in html
    assert 'data-map-toggle="subway"' in html
    assert 'data-map-toggle="labels"' in html
    assert 'data-map-zoom="in"' in html
    assert 'data-map-zoom="out"' in html
    assert '지하철·역' in html
    assert 'data-map-district="마포구"' in html
    assert '서울 25개 구 행정경계' in html
    assert 'OSM 한강' in html
    assert 'data-density-layer="cafe"' in html
    assert 'data-density-layer="population"' in html
    assert 'data-station-map="hongdae"' in html
    assert 'id="tool-station"' in html
    assert 'id="tool-compare-station"' in html
    assert 'id="tool-industry"' in html
    assert 'data-density-count' in html
    assert 'data-pop-density' in html
    assert 'data-risk-list' in html
    assert 'data-decision-question' in html
    assert '먼저 물을 질문' in html
    assert 'data-visit-plan' in html
    assert 'data-compare-panel' in html
    assert 'data-compare-metrics' in html
    assert 'class="density-data-note"' in html
    assert '데이터 기준과 한계' in html
    assert '브라우저에는 결과 JSON만 보냅니다' in html
    assert 'href="/topics/cafe-commercial-lease-risk/"' in html
    assert 'href="/topics/jeonwolse-contract-check/"' in html
    assert '/data/seoul-commercial-areas.json?v=' in html
    assert '/assets/commercial-check.js?v=' in html
    assert html.index('id="commercial-check-tool"') < html.index('사례로 더 보기')
    assert '분리 운영 중인 쇼핑픽' not in html

    assert len(build_site.SEOUL_COMMERCIAL_AREAS["stations"]) >= 12
    js = build_site.COMMERCIAL_TOOL_JS
    assert '[data-seoul-density-tool-root]' in js
    assert 'tool-compare-station' in js
    assert 'data-compare-panel' in js
    assert 'renderCompare' in js
    assert 'visitPlanFor' in js
    assert 'decisionQuestionFor' in js
    assert '[data-decision-question]' in js
    assert 'data-density-layer' in js
    assert 'data-map-toggle' in js
    assert 'data-map-zoom' in js
    assert 'setMapZoom' in js
    assert 'setMapLayerVisibility' in js
    assert 'dataset.subwayVisible' in js
    assert 'dataset.labelsVisible' in js
    assert 'districtPaths' in js
    assert 'data-map-district' in js
    assert '/data/seoul-commercial-areas.json' in js
    assert '/topics/cafe-commercial-lease-risk/' in js
    assert '/topics/jeonwolse-contract-check/' in js
    assert '/radar/cafe-contract-risk/' not in js
    assert '/radar/monthly-rent-contract-check/' not in js
    css = build_site.CSS
    assert "@media (max-width: 1120px) and (min-width: 861px)" in css
    assert ".density-data-note" in css
    assert ".seoul-map-card { grid-column: 1 / -1; min-height: 690px; }" in css
    assert ".seoul-map-canvas { min-height: 560px; }" in css
    assert ".seoul-tool-copy { grid-template-columns: 1fr; gap: 14px; }" in css

    data_text = json.dumps(build_site.SEOUL_COMMERCIAL_AREAS, ensure_ascii=False)
    assert "KOSIS_API_KEY" not in data_text
    assert "Public OSM Overpass" not in data_text
    assert "비밀 키는 브라우저에 배포하지 않습니다" in data_text

    outline = build_site.SEOUL_MAP_OUTLINE
    assert len(outline["districts"]) == 25
    assert outline["river"]["path"].startswith("M")
    assert "KOSTAT" in json.dumps(outline, ensure_ascii=False)

    network = build_site.SEOUL_SUBWAY_NETWORK
    assert network["stats"]["line_count"] >= 13
    assert network["stats"]["station_count"] >= 300
    assert network["stats"]["segment_count"] >= 250
    assert any(line["id"] == "line2" and len(line["segments"]) >= 10 for line in network["lines"])
    assert any(label["name"] == "강남" for label in network["labels"])


def test_public_audit_rejects_home_without_seoul_density_tool():
    audit = load_module(ROOT / "scripts" / "audit_public_site_quality.py", "audit_home_tool")
    html = (
        '<!doctype html><html><head><title>Recuerdame Lab 홈</title>'
        '<meta name="description" content="이사 월세 전세 상가 계약 전 동네 리스크를 확인하는 홈입니다.">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<link rel="stylesheet" href="/main.css?v=test"></head><body><main>'
        '<h1>이사·월세·상가 계약 전</h1>'
        '<section><h2>동네 레이더 최신 글</h2></section>'
        '</main></body></html>'
    )

    failures = audit.audit_html("/", html)

    assert any("seoul_density_tool_marker_missing" in failure for failure in failures)


def test_radar_contract_check_entrypoints_are_topic_lists():
    build_site = load_module(ROOT / "scripts" / "build_site.py", "build_site_contract_routes")

    slugs = [topic["slug"] for topic in build_site.TOPIC_HUBS]
    assert "jeonwolse-contract-check" in slugs
    assert "cafe-commercial-lease-risk" in slugs

    html = build_site.radar_body([])
    assert 'id="contract-check-routes"' in html
    assert 'href="/topics/jeonwolse-contract-check/"' in html
    assert 'href="/topics/cafe-commercial-lease-risk/"' in html
    assert "전월세 글 목록" in html
    assert "상가 계약 글 목록" in html
    assert 'href="/radar/dongne-signal-framework/"' not in html
    assert 'href="/radar/cafe-contract-risk/"' not in html

    cafe_topic = next(topic for topic in build_site.TOPIC_HUBS if topic["slug"] == "cafe-commercial-lease-risk")
    related = build_site.topic_related_articles(cafe_topic, [], [{"path": "/radar/cafe-contract-risk/"}, {"path": "/radar/dongne-signal-framework/", "body_html": "상권 유동인구"}], limit=10)
    assert [article["path"] for article in related] == ["/radar/cafe-contract-risk/"]


def test_topic_pages_do_not_put_radar_cards_in_narrow_mixed_grid():
    build_site = load_module(ROOT / "scripts" / "build_site.py", "build_site_topic_layout")
    cafe_topic = next(topic for topic in build_site.TOPIC_HUBS if topic["slug"] == "cafe-commercial-lease-risk")
    radar = [
        {
            "section": "radar",
            "path": "/radar/cafe-contract-risk/",
            "title": "사람 많은 상권이 꼭 좋은 자리는 아닙니다: 카페 계약 전 5개 의심",
            "description": "오늘의 의심 · 유동인구 착시: 사람이 많은 것과 내 카페에 돈을 쓰는 것은 다르다.",
            "category": "동네 레이더",
            "tags": ["카페 창업", "상권 분석"],
            "date": "2026-05-01T09:00:00+09:00",
            "image_url": "/assets/radar/thumbs/cafe-contract-risk.webp",
            "body_html": "카페 상가 권리금 유동인구",
        }
    ]

    html = build_site.topic_page_body(cafe_topic, [], radar)

    assert 'id="related-articles" class="article-list topic-article-list topic-featured-list"' in html
    assert 'class="article-list topic-article-list topic-secondary-list"' in html
    assert 'class="article-list mixed-list"' not in html


def test_public_audit_rejects_topic_radar_cards_in_mixed_grid():
    audit = load_module(ROOT / "scripts" / "audit_public_site_quality.py", "audit_topic_layout")
    html = '''<!doctype html><html><head><title>상가 계약 체크 페이지</title><meta name="description" content="카페 창업 전 상가 계약 체크 글을 모아 보는 페이지입니다."><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="/main.css?v=test"></head><body><main><h1>상가 계약 체크 페이지</h1><section class="article-list mixed-list"><article class="list-card radar-card"><h2>카페 계약 전 체크</h2></article></section></main></body></html>'''

    failures = audit.audit_html("/topics/cafe-commercial-lease-risk/", html)

    assert "/topics/cafe-commercial-lease-risk/:topic_article_list_layout_marker_missing" in failures
    assert "/topics/cafe-commercial-lease-risk/:topic_radar_cards_use_narrow_mixed_grid" in failures


def test_radar_articles_have_content_matched_webp_thumbnails():
    for path in sorted((ROOT / "content" / "radar").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        image_url = str(data.get("image_url") or "")
        assert image_url.startswith("/assets/radar/thumbs/"), path.name
        assert image_url.endswith(".webp"), path.name
        asset = ROOT / image_url.lstrip("/")
        assert asset.exists(), f"missing thumbnail asset for {path.name}: {asset}"
        assert asset.stat().st_size > 20_000, f"thumbnail asset too small for {path.name}: {asset.stat().st_size}"
        thumb_hash = hashlib.sha256(asset.read_bytes()).hexdigest()
        examples = data.get("field_examples") or []
        assert len(examples) >= 3, f"radar article needs 3 field examples: {path.name}"
        example_hashes: set[str] = set()
        for example in examples:
            assert str(example.get("label") or "").strip(), f"field example label missing for {path.name}"
            assert str(example.get("title") or "").strip(), f"field example title missing for {path.name}"
            assert str(example.get("description") or "").strip(), f"field example description missing for {path.name}"
            example_url = str(example.get("image_url") or "")
            assert example_url.startswith("/assets/radar/"), f"bad field example path for {path.name}: {example_url}"
            assert example_url.endswith(".webp"), f"field example must be webp for {path.name}: {example_url}"
            assert example_url != image_url, f"field example reuses thumbnail url for {path.name}: {example_url}"
            assert "/thumbs/" not in example_url, f"field example must not point at thumbnail folder for {path.name}: {example_url}"
            example_asset = ROOT / example_url.lstrip("/")
            assert example_asset.exists(), f"missing field example asset for {path.name}: {example_asset}"
            assert example_asset.stat().st_size > 20_000, f"field example asset too small for {path.name}: {example_asset.stat().st_size}"
            example_hash = hashlib.sha256(example_asset.read_bytes()).hexdigest()
            assert example_hash != thumb_hash, f"field example asset duplicates thumbnail bytes for {path.name}: {example_url}"
            assert example_hash not in example_hashes, f"field examples duplicate each other for {path.name}: {example_url}"
            example_hashes.add(example_hash)


def test_radar_example_gallery_adds_scene_map_and_comparison_markers():
    build_site = load_module(ROOT / "scripts" / "build_site.py", "build_site_visuals")
    article = {
        "slug": "bus-stop-front-home-check",
        "section": "radar",
        "path": "/radar/bus-stop-front-home-check/",
        "title": "버스정류장 앞 집, 편한 위치인지 피곤한 위치인지 보는 10분",
        "description": "정류장 가까움이 편의인지 소음과 대기열 피로인지 확인하는 글",
        "tags": ["버스정류장", "밤길", "소음", "생활권"],
        "image_url": "/assets/radar/thumbs/bus-stop-front-home-check.webp",
        "body_html": "<h2>정류장 앞 장점과 반례</h2><p>현장 질문으로 확인합니다.</p>",
        "field_examples": [
            {
                "label": "아침 대기열 장면",
                "title": "출근 대기열",
                "badge": "아침 8시",
                "description": "정류장 앞 줄이 현관·창문 쪽으로 밀려오는지 봅니다.",
                "image_url": "/assets/radar/bus-stop-front-home-check/examples/bus-stop-front-home-check-morning-queue-v2.webp",
            },
            {
                "label": "밤 창문 장면",
                "title": "불빛과 소리",
                "badge": "밤 10시",
                "description": "버스 불빛과 정차음이 집 안까지 들어오는지 봅니다.",
                "image_url": "/assets/radar/bus-stop-front-home-check/examples/bus-stop-front-home-check-night-window-v2.webp",
            },
            {
                "label": "한 블록 비교 장면",
                "title": "가깝지만 피곤",
                "badge": "비교",
                "description": "정류장 바로 앞 후보와 한 블록 안쪽 후보를 비교합니다.",
                "image_url": "/assets/radar/bus-stop-front-home-check/examples/bus-stop-front-home-check-one-block-compare-v2.webp",
            },
        ],
    }

    html = build_site.radar_example_gallery(article)
    scan_html = build_site.radar_experience_block(article)

    assert 'class="radar-example-gallery"' in html
    assert html.count('class="example-scene-card') >= 3
    assert html.count('class="scene-photo"') >= 3
    assert 'class="radar-situation-strip"' in html
    assert 'class="radar-map photo-scan"' in scan_html
    assert 'class="scan-photo"' in scan_html
    assert "월 고정비" not in html
    assert "출근 대기열" in html
    assert "예시 장면" in html
    assert "예시 장면 A" not in html
    assert "/thumbs/" not in html
    assert "bus-stop-front-home-check-scene-a.webp" not in html
    assert "현장 질문" in html
    assert "scene-skyline" not in html
    assert "scene-route" not in html
