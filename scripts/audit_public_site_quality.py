#!/usr/bin/env python3
"""Reader-facing quality/layout audit for the public GitHub Pages site.

This is intentionally stricter than string-only smoke checks. It catches the class
of regressions where generated decorative CSS or template changes look fine in a
build log but break deployed reader pages.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import quote, urljoin, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "https://r2cuerdame.github.io"
USER_AGENT = "R2CuerdamePublicQualityAudit/1.0"

HARD_PLACEHOLDERS = [
    "<<<<<<<",
    ">>>>>>>",
    "TODO",
    "FIXME",
    "TBD",
    "Lorem ipsum",
    "작성중",
    "임시 문구",
    "샘플 문구",
    "release_candidate",
    "final.html",
]

# Search-ad/affiliate safety has its own full audit, but keep obvious public copy
# leaks here too so the layout gate also blocks embarrassing content regressions.
PUBLIC_COPY_FORBIDDEN = [
    "tistory.com",
    "OpenClaw",
    "Hermes cron",
    "agent log",
]

MANDATORY_PATHS = [
    "/",
    "/radar/",
    "/radar/cafe-contract-risk/",
    "/topics/jeonwolse-contract-check/",
    "/topics/cafe-commercial-lease-risk/",
    "/deals/",
    "/topics/",
    "/search/",
]

SECTION_MANDATORY_PATHS = {
    "all": MANDATORY_PATHS,
    "deals": ["/", "/deals/", "/search/"],
    "radar": ["/", "/radar/", "/radar/cafe-contract-risk/", "/topics/jeonwolse-contract-check/", "/topics/cafe-commercial-lease-risk/", "/search/"],
    "topics": ["/", "/topics/", "/topics/jeonwolse-contract-check/", "/topics/cafe-commercial-lease-risk/", "/search/"],
}


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth and data:
            self.parts.append(data)


def normalize_ws(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def visible_text(page_html: str) -> str:
    parser = VisibleTextParser()
    parser.feed(page_html)
    return normalize_ws(" ".join(parser.parts))


def attr_value(tag: str, attr: str) -> str:
    match = re.search(rf"\b{re.escape(attr)}\s*=\s*(['\"])(.*?)\1", tag, flags=re.I | re.S)
    return html.unescape(match.group(2)) if match else ""


def anchor_tags(page_html: str) -> list[str]:
    return re.findall(r"<a\b[^>]*>", page_html, flags=re.I | re.S)


def anchor_class_count(page_html: str, class_name: str) -> int:
    count = 0
    for tag in anchor_tags(page_html):
        classes = attr_value(tag, "class").split()
        if class_name in classes:
            count += 1
    return count


def coupang_anchor_tags(page_html: str) -> list[str]:
    return [tag for tag in anchor_tags(page_html) if "coupang.com" in attr_value(tag, "href").lower()]


def coupang_href_has_tracking(href: str) -> bool:
    parsed = urlparse(href)
    host = parsed.netloc.lower().split("@")[-1]
    return "lptag=" in href.lower() or host == "link.coupang.com"


def extract_tag_text(page_html: str, tag: str) -> str:
    match = re.search(rf"<{tag}\b[^>]*>(.*?)</{tag}>", page_html, flags=re.I | re.S)
    if not match:
        return ""
    return normalize_ws(re.sub(r"<[^>]+>", " ", match.group(1)))


def extract_meta_description(page_html: str) -> str:
    for tag in re.findall(r"<meta\b[^>]*>", page_html, flags=re.I | re.S):
        if attr_value(tag, "name").lower() == "description":
            return normalize_ws(attr_value(tag, "content"))
    return ""


def extract_stylesheet_href(page_html: str) -> str:
    for tag in re.findall(r"<link\b[^>]*>", page_html, flags=re.I | re.S):
        if attr_value(tag, "rel").lower() == "stylesheet":
            href = attr_value(tag, "href")
            if "main.css" in href:
                return href
    return ""


def page_kind(path: str) -> str:
    clean = path.strip("/")
    if clean.startswith("radar/") and clean != "radar":
        return "radar_article"
    if clean.startswith("deals/") and clean != "deals":
        return "deal_article"
    if clean.startswith("topics/") and clean != "topics":
        return "topic"
    if clean in {"radar", "deals", "topics", "search", ""}:
        return clean or "home"
    return "page"


def section_mandatory_paths(section: str) -> list[str]:
    return list(SECTION_MANDATORY_PATHS.get(section, MANDATORY_PATHS))


def local_pages(limit_articles: int, section: str = "all") -> list[str]:
    paths = section_mandatory_paths(section)
    article_paths: list[str] = []
    root_names = ["topics", "radar", "deals"] if section == "all" else [section]
    for root_name in root_names:
        base = ROOT / root_name
        if not base.exists():
            continue
        for index in sorted(base.glob("*/index.html")):
            rel = "/" + index.parent.relative_to(ROOT).as_posix().strip("/") + "/"
            if rel not in paths:
                article_paths.append(rel)
    paths.extend(article_paths[:limit_articles])
    return paths


def live_pages(base_url: str, limit_articles: int, section: str = "all") -> list[str]:
    paths = section_mandatory_paths(section)
    allowed_prefixes = ("/topics/", "/radar/", "/deals/") if section == "all" else (f"/{section}/",)
    try:
        sitemap = fetch_url(urljoin(base_url.rstrip("/") + "/", "sitemap.xml?quality_audit=1"))
        for loc in re.findall(r"<loc>(.*?)</loc>", sitemap, flags=re.I | re.S):
            parsed = urlparse(html.unescape(loc.strip()))
            path = parsed.path or "/"
            if path.startswith(allowed_prefixes) and path not in paths:
                paths.append(path if path.endswith("/") else path + "/")
            if len(paths) >= len(section_mandatory_paths(section)) + limit_articles:
                break
    except Exception:
        # Mandatory pages still give a useful live audit if sitemap fetch is flaky.
        pass
    return paths


def local_html(path: str) -> str:
    rel = path.strip("/")
    file_path = ROOT / (rel or "index.html")
    if rel and path.endswith("/"):
        file_path = ROOT / rel / "index.html"
    return file_path.read_text(encoding="utf-8", errors="replace")


def fetch_url(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=25) as res:
        if int(getattr(res, "status", 0) or 0) != 200:
            raise RuntimeError(f"HTTP_{res.status}:{url}")
        return res.read().decode("utf-8", errors="replace")


def load_html(path: str, *, base_url: str | None) -> str:
    if base_url:
        quoted_path = quote(path.lstrip("/"), safe="/%")
        url = urljoin(base_url.rstrip("/") + "/", quoted_path)
        sep = "&" if "?" in url else "?"
        return fetch_url(f"{url}{sep}quality_audit=1")
    return local_html(path)


def load_css(first_html: str, *, base_url: str | None) -> tuple[str, str]:
    href = extract_stylesheet_href(first_html)
    if base_url:
        css_url = urljoin(base_url.rstrip("/") + "/", (href or "/main.css").lstrip("/"))
        sep = "&" if "?" in css_url else "?"
        return fetch_url(f"{css_url}{sep}quality_audit=1"), css_url
    return (ROOT / "main.css").read_text(encoding="utf-8", errors="replace"), href or "/main.css"


def split_css_rules(css: str) -> Iterable[tuple[str, str]]:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css, flags=re.S):
        yield normalize_ws(selector), normalize_ws(body)


def audit_css(css: str) -> list[str]:
    failures: list[str] = []
    if ".visual-checklist" not in css:
        failures.append("visual_checklist_class_missing")
    for marker in [".radar-example-gallery", ".example-scene-card", ".radar-situation-strip", ".photo-scan", ".scene-photo"]:
        if marker not in css:
            failures.append(f"radar_example_visual_css_missing:{marker}")
    for marker in [".seoul-density-panel", ".seoul-map-card", ".seoul-map-canvas", ".station-dot", ".density-layer-tabs", ".density-score-grid", ".density-bar", ".tool-risk-list", ".tool-link-row", ".density-compare-card", ".compare-metric-row"]:
        if marker not in css:
            failures.append(f"seoul_density_tool_css_missing:{marker}")
    for marker in [".shopping-room-card", ".room-product", ".room-photo", ".room-hit-area", ".room-preview", ".room-preview-actions", ".room-product-link"]:
        if marker not in css:
            failures.append(f"shopping_room_css_missing:{marker}")
    for marker in [".coupang-event-strip", ".coupang-event-card", ".coupang-event-link", ".event-disclosure"]:
        if marker not in css:
            failures.append(f"coupang_event_css_missing:{marker}")
    if "grid-template-columns: minmax(330px, .78fr) minmax(430px, 1.22fr)" not in css:
        failures.append("shopping_room_desktop_width_weight_guard_missing")
    if "min-height: clamp(390px, 36vw, 470px)" not in css:
        failures.append("shopping_room_large_visual_guard_missing")
    for removed_marker in [".scene-skyline", ".scene-route", ".map-route"]:
        if removed_marker in css:
            failures.append(f"radar_abstract_placeholder_css_regression:{removed_marker}")
    guard_match = re.search(r"\.article-content\s+\.checklist\s*\{([^}]*)\}", css, flags=re.S)
    guard_body = normalize_ws(guard_match.group(1)) if guard_match else ""
    if not guard_match or "width: 100%" not in guard_body or "max-width: none" not in guard_body:
        failures.append("article_checklist_width_guard_missing")

    for selector, body in split_css_rules(css):
        if ".checklist" not in selector:
            continue
        if ".visual-checklist" in selector:
            continue
        width_match = re.search(r"\bwidth\s*:\s*(\d+(?:\.\d+)?)px\b", body)
        if width_match and float(width_match.group(1)) < 160:
            failures.append(f"generic_checklist_fixed_narrow_width:{selector}:{width_match.group(1)}px")
    return failures


def audit_html(path: str, page_html: str) -> list[str]:
    failures: list[str] = []
    text = visible_text(page_html)
    kind = page_kind(path)

    if "<main" not in page_html:
        failures.append(f"{path}:main_missing")
    if 'name="viewport"' not in page_html and "name='viewport'" not in page_html:
        failures.append(f"{path}:viewport_missing")
    if "/main.css?v=" not in page_html:
        failures.append(f"{path}:versioned_main_css_missing")

    title = extract_tag_text(page_html, "title")
    if not (8 <= len(title) <= 95):
        failures.append(f"{path}:title_length_bad:{len(title)}")
    h1 = extract_tag_text(page_html, "h1")
    if not (4 <= len(h1) <= 110):
        failures.append(f"{path}:h1_missing_or_bad:{len(h1)}")
    desc = extract_meta_description(page_html)
    if not (35 <= len(desc) <= 180):
        failures.append(f"{path}:meta_description_bad:{len(desc)}")

    for marker in HARD_PLACEHOLDERS:
        if marker in page_html:
            failures.append(f"{path}:placeholder_or_conflict_marker:{marker}")
    lowered = page_html.lower()
    for marker in PUBLIC_COPY_FORBIDDEN:
        if marker.lower() in lowered:
            failures.append(f"{path}:forbidden_public_copy:{marker}")

    if path.startswith("/deals/") and 'href="/radar/"' not in page_html:
        failures.append(f"{path}:deals_to_radar_return_link_missing")
    if path.startswith("/radar/") and 'href="/deals/"' not in page_html:
        failures.append(f"{path}:radar_to_deals_link_missing")
    if kind == "home":
        required_markers = [
            'id="commercial-check-tool"',
            'data-seoul-density-tool-root',
            'class="seoul-map-card"',
            'data-density-layer="cafe"',
            'data-density-layer="population"',
            'data-station-map="hongdae"',
            'id="tool-station"',
            'id="tool-compare-station"',
            'id="tool-industry"',
            'data-density-count',
            'data-pop-density',
            'data-risk-list',
            'data-compare-panel',
            'data-compare-metrics',
            'href="/topics/cafe-commercial-lease-risk/"',
            'href="/topics/jeonwolse-contract-check/"',
            '/data/seoul-commercial-areas.json?v=',
            '/assets/commercial-check.js?v=',
        ]
        for marker in required_markers:
            if marker not in page_html:
                failures.append(f"{path}:seoul_density_tool_marker_missing:{marker}")
        if '분리 운영 중인 쇼핑픽' in page_html:
            failures.append(f"{path}:home_shopping_section_should_not_compete_with_radar")
        if page_html.find('id="commercial-check-tool"') > page_html.find('사례로 더 보기'):
            failures.append(f"{path}:seoul_density_tool_not_before_case_articles")
    if kind == "radar":
        for href in ('/topics/jeonwolse-contract-check/', '/topics/cafe-commercial-lease-risk/'):
            if f'href="{href}"' not in page_html:
                failures.append(f"{path}:contract_check_topic_route_missing:{href}")
        if 'id="contract-check-routes"' not in page_html:
            failures.append(f"{path}:contract_check_route_list_missing")
        for direct_href in ('/radar/dongne-signal-framework/', '/radar/cafe-contract-risk/'):
            if f'href="{direct_href}"' in page_html.split('id="contract-check-routes"', 1)[0]:
                failures.append(f"{path}:contract_check_hero_direct_article_link:{direct_href}")
    if kind == "topic":
        if 'topic-article-list' not in page_html:
            failures.append(f"{path}:topic_article_list_layout_marker_missing")
        if 'class="article-list mixed-list"' in page_html and 'class="list-card radar-card' in page_html:
            failures.append(f"{path}:topic_radar_cards_use_narrow_mixed_grid")
    if kind == "deals":
        room_products = page_html.count('class="room-product')
        room_product_links = anchor_class_count(page_html, "room-product-link")
        coupang_links = coupang_anchor_tags(page_html)
        if 'class="shopping-room-card"' not in page_html:
            failures.append(f"{path}:shopping_room_interactive_card_missing")
        if 'shopping-room-ai.webp' not in page_html or 'class="room-photo"' not in page_html:
            failures.append(f"{path}:shopping_room_ai_photo_missing")
        if 'class="room-hit-area"' not in page_html:
            failures.append(f"{path}:shopping_room_click_area_missing")
        if room_products < 4:
            failures.append(f"{path}:shopping_room_products_too_few:{room_products}")
        if 'shopping-room-pick-1' not in page_html or 'room-previews' not in page_html:
            failures.append(f"{path}:shopping_room_toggle_preview_missing")
        if room_product_links < min(4, room_products):
            failures.append(f"{path}:shopping_room_product_links_too_few:{room_product_links}")
        if coupang_links and "affiliate_click" not in page_html:
            failures.append(f"{path}:affiliate_click_tracking_missing")
        if any(not coupang_href_has_tracking(attr_value(tag, "href")) for tag in coupang_links):
            failures.append(f"{path}:coupang_lptag_missing")
        for tag in coupang_links:
            rel = set(attr_value(tag, "rel").split())
            if not {"sponsored", "nofollow", "noopener"}.issubset(rel) or attr_value(tag, "target") != "_blank":
                failures.append(f"{path}:coupang_anchor_policy_bad")
                break
        if 'class="coupang-event-strip"' in page_html:
            event_cards = page_html.count('class="coupang-event-card"')
            event_links = anchor_class_count(page_html, "coupang-event-link")
            if not (1 <= event_cards <= 3):
                failures.append(f"{path}:coupang_event_card_count_bad:{event_cards}")
            if event_links != event_cards:
                failures.append(f"{path}:coupang_event_links_mismatch:{event_links}:{event_cards}")
            if "쿠팡 파트너스 활동" not in text:
                failures.append(f"{path}:coupang_event_disclosure_missing")

    category_chip_links = anchor_class_count(page_html, "category-chip")
    tag_links = anchor_class_count(page_html, "tag")
    meta_links = anchor_class_count(page_html, "meta-link")
    if kind in {"home", "radar", "deals"} and category_chip_links < 5:
        failures.append(f"{path}:taxonomy_category_links_too_few:{category_chip_links}")
    if kind in {"home", "radar"} and 'class="radar-card-visual has-css-thumb' in page_html:
        failures.append(f"{path}:radar_card_ai_thumbnail_missing")
    if kind in {"home", "radar"} and 'class="radar-card-image"' not in page_html:
        failures.append(f"{path}:radar_card_ai_thumbnail_image_missing")
    if kind in {"radar_article", "deal_article"}:
        if tag_links < 2:
            failures.append(f"{path}:taxonomy_tag_links_too_few:{tag_links}")
        if meta_links < 1:
            failures.append(f"{path}:taxonomy_category_meta_link_missing")
    if kind == "radar_article" and anchor_class_count(page_html, "search-chip") < 2:
        failures.append(f"{path}:radar_related_search_chips_too_few")
    if kind == "radar_article":
        has_gallery = 'class="radar-example-gallery"' in page_html
        if not has_gallery:
            failures.append(f"{path}:radar_example_gallery_missing")
        else:
            example_cards = page_html.count('class="example-scene-card')
            scene_photo_tags = re.findall(r"<img\b[^>]*class=[\"'][^\"']*\bscene-photo\b[^\"']*[\"'][^>]*>", page_html, flags=re.I | re.S)
            scene_photos = len(scene_photo_tags)
            scene_photo_srcs = [attr_value(tag, "src") for tag in scene_photo_tags]
            unique_scene_photo_srcs = {src for src in scene_photo_srcs if src}
            for marker in ['class="radar-situation-strip"', "예시 장면", "현장 질문"]:
                if marker not in page_html:
                    failures.append(f"{path}:radar_example_visual_marker_missing:{marker}")
            if example_cards < 3:
                failures.append(f"{path}:radar_example_scene_cards_too_few:{example_cards}")
            if scene_photos < 3:
                failures.append(f"{path}:radar_example_ai_scene_photos_too_few:{scene_photos}")
            if len(unique_scene_photo_srcs) < 3:
                failures.append(f"{path}:radar_example_scene_photos_not_distinct:{len(unique_scene_photo_srcs)}")
            if any("/thumbs/" in src for src in scene_photo_srcs):
                failures.append(f"{path}:radar_example_reuses_thumbnail_asset")
        if 'class="radar-map photo-scan' not in page_html or 'class="scan-photo"' not in page_html:
            failures.append(f"{path}:radar_visual_scan_ai_photo_missing")
        if 'scene-skyline' in page_html or 'scene-route' in page_html or '<svg class="map-route"' in page_html:
            failures.append(f"{path}:radar_abstract_placeholder_visual_regression")
    if kind == "deal_article":
        quick_product_links = anchor_class_count(page_html, "quick-product-link")
        coupang_links = coupang_anchor_tags(page_html)
        if coupang_links and "affiliate_click" not in page_html:
            failures.append(f"{path}:affiliate_click_tracking_missing")
        if any(not coupang_href_has_tracking(attr_value(tag, "href")) for tag in coupang_links):
            failures.append(f"{path}:coupang_lptag_missing")
        if coupang_links and quick_product_links < min(3, len({attr_value(tag, 'href') for tag in coupang_links})):
            failures.append(f"{path}:deal_quick_product_links_too_few:{quick_product_links}")
        if quick_product_links and "쿠팡 파트너스 링크입니다" not in text:
            failures.append(f"{path}:deal_quick_product_affiliate_cue_missing")
        for tag in coupang_links:
            rel = set(attr_value(tag, "rel").split())
            if not {"sponsored", "nofollow", "noopener"}.issubset(rel) or attr_value(tag, "target") != "_blank":
                failures.append(f"{path}:coupang_anchor_policy_bad")
                break

    if kind in {"radar_article", "deal_article"}:
        if len(text) < 1800:
            failures.append(f"{path}:article_visible_text_too_short:{len(text)}")
        if 'class="article-content"' not in page_html:
            failures.append(f"{path}:article_content_wrapper_missing")
        visual_markers = sum(page_html.count(marker) for marker in [
            "callout",
            "checklist",
            "radar-map-card",
            "radar-brief-stack",
            "radar-example-gallery",
            "example-scene-card",
            "radar-situation-strip",
            "comparison",
            "deal-table",
            "table",
            "quick-take",
            "quick-facts",
            "quick-products",
            "article-product-hero",
            "score",
            "bridge-card",
        ])
        if visual_markers < 4:
            failures.append(f"{path}:reader_visual_rhythm_weak:{visual_markers}")

    if kind == "radar_article" and "계약 전" not in text and "확인" not in text:
        failures.append(f"{path}:radar_reader_action_missing")
    if kind == "deal_article" and "구매" not in text and "비교" not in text:
        failures.append(f"{path}:deal_reader_action_missing")

    return failures


def run_audit(*, base_url: str | None, limit_articles: int, section: str = "all") -> dict[str, object]:
    pages = live_pages(base_url, limit_articles, section=section) if base_url else local_pages(limit_articles, section=section)
    pages = list(dict.fromkeys(pages))
    checked: list[str] = []
    failures: list[str] = []
    css_href = ""
    css_text = ""

    for idx, path in enumerate(pages):
        try:
            page_html = load_html(path, base_url=base_url)
            checked.append(path)
            if idx == 0:
                css_text, css_href = load_css(page_html, base_url=base_url)
                failures.extend(audit_css(css_text))
            failures.extend(audit_html(path, page_html))
        except Exception as exc:
            failures.append(f"{path}:load_error:{type(exc).__name__}:{str(exc)[:160]}")

    result = {
        "ok": not failures,
        "mode": "live" if base_url else "local",
        "base_url": base_url or "local",
        "pages_checked": len(checked),
        "checked_paths": checked,
        "css_href": css_href,
        "failures": failures,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Audit the deployed GitHub Pages site")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--limit-articles", type=int, default=14)
    parser.add_argument("--section", choices=sorted(SECTION_MANDATORY_PATHS), default="all", help="Audit all public sections or a single channel")
    args = parser.parse_args()

    result = run_audit(base_url=args.base_url if args.live else None, limit_articles=args.limit_articles, section=args.section)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
