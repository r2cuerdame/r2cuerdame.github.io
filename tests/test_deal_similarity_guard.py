from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "publish_next_blog_autopost_deal.py"

spec = importlib.util.spec_from_file_location("publish_next_blog_autopost_deal", SCRIPT)
publisher = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(publisher)


def test_similar_product_topic_is_blocked_even_when_title_and_slug_differ():
    existing = [
        {
            "title": "공기청정기 추천 TOP 5, 거실부터 방까지 많이 찾는 모델 정리",
            "category": "로봇청소기-가전",
            "tags": ["로봇청소기-가전", "공기청정기 추천 비교 글", "쿠팡 파트너스", "가전"],
            "body_html": "LG 퓨리케어 360 공기청정기 삼성 블루스카이 샤오미 공기청정기",
            "source_post_file": "legacy/air-purifier.json",
        }
    ]
    candidate = {
        "title": "공기청정기 뭐 살까, LG·삼성·샤오미 인기 5종 비교",
        "category": "로봇청소기-가전",
        "tags": ["공기청정기", "LG", "삼성", "샤오미", "인기", "5종", "비교"],
        "products_pool": "products_air_purifiers.json",
        "html": "LG 퓨리케어 360 공기청정기 삼성 블루스카이 샤오미 미에어 공기청정기",
    }

    match = publisher.find_similar_existing_article(candidate, existing)

    assert match is not None
    assert match["reason"] in {"same_product_topic", "same_product_pool", "similar_product_topic"}
    assert match["existing_title"] == existing[0]["title"]


def test_different_product_topic_in_same_broad_category_is_allowed():
    existing = [
        {
            "title": "공기청정기 추천 TOP 5, 거실부터 방까지 많이 찾는 모델 정리",
            "category": "로봇청소기-가전",
            "tags": ["로봇청소기-가전", "공기청정기 추천 비교 글", "가전"],
            "body_html": "LG 퓨리케어 360 공기청정기 삼성 블루스카이",
        }
    ]
    candidate = {
        "title": "로봇청소기 추천 BEST 4, 가격대별 비교",
        "category": "로봇청소기-가전",
        "tags": ["로봇청소기", "청소기", "가전", "비교"],
        "products_pool": "products_robot_vacuums.json",
        "html": "로보락 로봇청소기 드리미 로봇청소기 물걸레 청소기",
    }

    assert publisher.find_similar_existing_article(candidate, existing) is None


def test_same_products_pool_is_blocked_even_when_keywords_are_weak():
    existing = [
        {
            "title": "제습기 추천 BEST 5, 장마철 전에 많이 찾는 실속 모델",
            "category": "로봇청소기-가전",
            "tags": ["제습기 추천 비교 글", "가전"],
            "products_pool": "products_dehumidifiers.json",
            "body_html": "위닉스 뽀송 LG 휘센 위니아 제습기",
        }
    ]
    candidate = {
        "title": "습도 높은 집에서 먼저 볼 제품 5개",
        "category": "로봇청소기-가전",
        "tags": ["장마", "습도", "실속"],
        "products_pool": "products_dehumidifiers.json",
        "html": "위닉스 뽀송 LG 휘센 위니아 제습기",
    }

    match = publisher.find_similar_existing_article(candidate, existing)

    assert match is not None
    assert match["reason"] == "same_product_pool"
