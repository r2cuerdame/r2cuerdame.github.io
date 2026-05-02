#!/usr/bin/env python3
"""Build the static Recuerdame Lab GitHub Pages site.

Zero external dependencies. Reads article JSON from content/deals and content/radar,
then writes static section indexes, article pages, SEO files, RSS, and assets.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from email.utils import format_datetime
from pathlib import Path
import hashlib
import html
import json
import os
import re
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
KST = timezone(timedelta(hours=9))
NOW = datetime.now(KST)
TODAY = NOW.date().isoformat()
BASE = "https://r2cuerdame.github.io"
SITE_NAME = "Recuerdame Lab"
SITE_DESC = "이사·월세·전세·상가 계약 전, 동네와 상권 리스크를 먼저 걸러내는 Dongne Radar 공개 노트입니다."
COMMON_KEYWORDS = "동네 레이더, 계약 전 체크리스트, 이사 준비, 월세 계약, 전세 계약, 통근, 생활권, 현장 확인, Recuerdame Lab"
RADAR_KEYWORDS = "동네 레이더, 전월세 계약, 월세 계약, 전세 계약, 서울 동네 분석, 수도권 이사, 통근, 생활권, 현장 확인 질문, 관리비, 소음, 상권 분석, 상가 임대차, 카페 창업, 권리금, 주거 리스크"
DEALS_KEYWORDS = "구매가이드, 생활용품 추천, 상품 비교, 쇼핑픽, 가격 비교, Recuerdame Lab"

METRICS_PATH = ROOT / "data" / "metrics" / "page_views.json"
ANALYTICS_CONFIG_PATHS = [
    Path("/root/.hermes/secrets/deals_google_metrics.json"),
    ROOT / "data" / "metrics" / "analytics_config.json",
]


def normalize_public_path(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "/"
    if raw.startswith(BASE):
        raw = raw[len(BASE):]
    raw = raw.split("#", 1)[0].split("?", 1)[0]
    if not raw.startswith("/"):
        raw = "/" + raw
    if raw.endswith("index.html"):
        raw = raw[: -len("index.html")]
    if raw != "/" and not raw.endswith("/"):
        raw += "/"
    return raw


def load_page_metrics() -> dict[str, Any]:
    if not METRICS_PATH.exists():
        return {"status": "not_configured", "pages": {}}
    try:
        data = json.loads(METRICS_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return {"status": "invalid", "pages": {}}
    pages = data.get("pages") if isinstance(data, dict) else {}
    normalized: dict[str, dict[str, Any]] = {}
    if isinstance(pages, dict):
        for key, value in pages.items():
            if isinstance(value, dict):
                normalized[normalize_public_path(key)] = value
    data["pages"] = normalized
    return data


PAGE_METRICS_DATA = load_page_metrics()
PAGE_METRICS = PAGE_METRICS_DATA.get("pages") if isinstance(PAGE_METRICS_DATA.get("pages"), dict) else {}


def metric_for(path: str) -> dict[str, Any]:
    return PAGE_METRICS.get(normalize_public_path(path), {}) if isinstance(PAGE_METRICS, dict) else {}


def format_count(value: Any) -> str:
    try:
        n = int(value)
    except Exception:
        return ""
    if n <= 0:
        return ""
    return f"{n:,}"


def traffic_badge(path: str, label: str = "최근 30일") -> str:
    metric = metric_for(path)
    views = format_count(metric.get("views") or metric.get("screenPageViews") or metric.get("page_views"))
    if not views:
        return ""
    users = format_count(metric.get("active_users") or metric.get("activeUsers") or metric.get("users"))
    suffix = f" · 방문 {users}" if users else ""
    return f'<span class="traffic-badge" title="{esc(label)} 조회 데이터">👁 {esc(label)} {esc(views)}회{esc(suffix)}</span>'


def configured_analytics_id() -> str:
    candidates: list[str] = []
    env_mid = os.environ.get("GA_MEASUREMENT_ID") or os.environ.get("GTAG_MEASUREMENT_ID")
    if env_mid:
        candidates.append(env_mid)
    config_env = os.environ.get("DEALS_ANALYTICS_CONFIG")
    paths = ([Path(config_env)] if config_env else []) + ANALYTICS_CONFIG_PATHS
    for path in paths:
        if not path or not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if isinstance(data, dict):
            for key in ("measurement_id", "ga_measurement_id", "ga4_measurement_id"):
                if data.get(key):
                    candidates.append(str(data[key]))
    for raw in candidates:
        mid = str(raw or "").strip().upper()
        if re.fullmatch(r"(?:G|GT)-[A-Z0-9-]+", mid):
            return mid
    return ""


ANALYTICS_ID = configured_analytics_id()


def analytics_snippet() -> str:
    if not ANALYTICS_ID:
        return ""
    mid = esc(ANALYTICS_ID)
    return f'''  <script async src="https://www.googletagmanager.com/gtag/js?id={mid}"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', '{mid}', {{ anonymize_ip: true }});
  </script>'''

STATIC_PAGES = [
    {
        "path": "/",
        "file": "index.html",
        "title": "Recuerdame Lab — 동네 레이더와 계약 전 체크리스트",
        "description": SITE_DESC,
        "priority": "1.0",
        "type": "WebPage",
        "section": "home",
    },
    {
        "path": "/radar/",
        "file": "radar/index.html",
        "title": "동네 레이더 — 이사·월세·상가 계약 전 리스크 체크",
        "description": "이사, 월세·전세, 통근, 생활권, 상가 계약 전에 걸러야 할 동네·상권 리스크와 현장 확인 질문을 정리합니다.",
        "priority": "0.95",
        "type": "CollectionPage",
        "section": "radar",
    },
    {
        "path": "/guides/",
        "file": "guides/index.html",
        "title": "동네 레이더 읽는 순서 — 계약 전 체크 가이드",
        "description": "이사·월세·전세·상가 계약 전에 동네 레이더 글을 어떤 순서로 읽고 무엇을 현장에서 확인할지 정리합니다.",
        "priority": "0.86",
        "type": "CollectionPage",
        "section": "guides",
    },
    {
        "path": "/about/",
        "file": "about/index.html",
        "title": "소개 — Dongne Radar by Recuerdame Lab",
        "description": "동네 레이더는 이사·월세·전세·상가 계약 전 돈과 시간을 잡아먹는 리스크를 더 빨리 걸러내기 위한 공개 노트입니다.",
        "priority": "0.55",
        "type": "AboutPage",
        "section": "about",
    },
    {
        "path": "/deals/",
        "file": "deals/index.html",
        "title": "쇼핑픽 구매가이드 — 생활가전·재택근무 비교",
        "description": "생활가전, 책상 장비, 음향기기처럼 구매 직전 비교가 필요한 상품을 오늘의 추천, 카테고리, 검색으로 빠르게 찾는 쇼핑픽 랜딩입니다.",
        "priority": "0.72",
        "type": "CollectionPage",
        "section": "deals",
    },
    {
        "path": "/search/",
        "file": "search/index.html",
        "title": "사이트 검색 — Recuerdame Lab",
        "description": "동네 레이더와 구매가이드 글을 키워드로 빠르게 찾는 사이트 검색입니다.",
        "priority": "0.64",
        "type": "SearchResultsPage",
        "section": "search",
    },
]

NAV = [
    ("동네 레이더", "/radar/", "nav-primary"),
    ("구매가이드", "/deals/", "nav-primary"),
    ("검색", "/search/", "nav-action"),
    ("읽는 순서", "/guides/", "nav-secondary"),
]


class BuildError(RuntimeError):
    pass


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def asset_version(value: str) -> str:
    return hashlib.sha1(str(value or "").encode("utf-8")).hexdigest()[:10]


def nav_item_current(page_path: str, href: str) -> bool:
    if href == "/":
        return page_path == "/"
    return page_path == href or page_path.startswith(href)


def nav_html(page_path: str) -> str:
    items = []
    for index, (name, href, tone) in enumerate(NAV, start=1):
        current = ' aria-current="page"' if nav_item_current(page_path, href) else ""
        items.append(
            f'      <a class="{tone}" data-nav-order="{index}" href="{href}"{current}>'
            f'<span>{esc(name)}</span></a>'
        )
    return "\n".join(items)


def deals_nav_html(page_path: str) -> str:
    items = [
        ("동네 레이더", "/radar/", "nav-return"),
        ("쇼핑픽 홈", "/deals/", "nav-primary"),
        ("오늘 BEST", "/deals/#today-best", "nav-primary"),
        ("카테고리", "/deals/#category-blocks", "nav-secondary"),
        ("검색", "/search/", "nav-action"),
    ]
    out = []
    for index, (name, href, tone) in enumerate(items, start=1):
        current = ' aria-current="page"' if href == "/deals/" and page_path == "/deals/" else ""
        out.append(
            f'      <a class="{tone}" data-nav-order="{index}" href="{href}"{current}>'
            f'<span>{esc(name)}</span></a>'
        )
    return "\n".join(out)


def strip_tags(value: str) -> str:
    value = re.sub(r"<script\b[^>]*>.*?</script>", " ", value or "", flags=re.I | re.S)
    value = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(
        r"</?(?:p|div|section|article|header|footer|h[1-6]|li|ul|ol|br|table|thead|tbody|tr|td|th|blockquote)\b[^>]*>",
        " ",
        value,
        flags=re.I,
    )
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def short_text(value: str, limit: int = 170) -> str:
    text = strip_tags(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


IMG_SRC_RE = re.compile(r'<img\b[^>]*(?:src|data-src)=["\']([^"\']+)["\']', re.I)
HREF_RE = re.compile(r'<a\b[^>]*href=["\']([^"\']+)["\']', re.I)
PRICE_HINT_RE = re.compile(r'가격대는\s*([^<.。]+?수준)', re.I)
COUNT_HINT_RE = re.compile(r'(?:BEST|TOP)\s*(\d+)|(\d+)선', re.I)
TABLE_RE = re.compile(r'(<table\b[\s\S]*?</table>)', re.I)
TABLE_ROW_RE = re.compile(r'<tr\b[^>]*>[\s\S]*?</tr>', re.I)
TABLE_HEAD_CELL_RE = re.compile(r'<th\b[^>]*>([\s\S]*?)</th>', re.I)
TABLE_DATA_OPEN_RE = re.compile(r'<td\b([^>]*)>', re.I)
A_TAG_OPEN_RE = re.compile(r'<a\b(?P<attrs>[^>]*)>', re.I)
HREF_ATTR_RE = re.compile(r'\s+href\s*=\s*(["\'])(.*?)\1', re.I | re.S)
TARGET_REL_ATTR_RE = re.compile(r'\s+(?:target|rel)\s*=\s*(?:(["\']).*?\1|[^\s>]+)', re.I | re.S)
SOURCE_URL_TO_PATH: dict[str, str] = {}


def clean_url(value: str) -> str:
    url = html.unescape(str(value or "").strip())
    if url.startswith(("http://", "https://", "/")):
        return url
    return ""


def image_from_body(body: str) -> str:
    for url in IMG_SRC_RE.findall(body or ""):
        url = clean_url(url)
        if url:
            return url
    return ""


def coupang_url_from_body(body: str) -> str:
    links = [clean_url(url) for url in HREF_RE.findall(body or "")]
    links = [url for url in links if url]
    for url in links:
        if "coupang.com" in url and "lptag=" in url:
            return url
    for url in links:
        if "coupang.com" in url:
            return url
    return ""


def price_hint_from_body(body: str) -> str:
    text = strip_tags(body or "")
    m = PRICE_HINT_RE.search(text)
    if not m:
        return "상세가는 상품 페이지에서 확인"
    return re.sub(r"\s+", " ", m.group(1)).strip()


def item_count_hint(title: str, body: str) -> str:
    joined = f"{title} {strip_tags(body or '')[:1200]}"
    m = COUNT_HINT_RE.search(joined)
    if m:
        count = m.group(1) or m.group(2)
        return f"{count}개 후보 비교"
    product_ids = set(re.findall(r'/products/(\d+)', body or ""))
    if product_ids:
        return f"{min(len(product_ids), 5)}개 후보 비교"
    return "추천 후보 비교"


def mobile_labeled_table(table_html: str) -> str:
    labels = [short_text(strip_tags(cell), 28) for cell in TABLE_HEAD_CELL_RE.findall(table_html or "")]
    labels = [label for label in labels if label]
    if not labels:
        return table_html

    def add_row_labels(row_match: re.Match[str]) -> str:
        row = row_match.group(0)
        if re.search(r'<th\b', row, re.I):
            return row
        index = 0

        def add_cell_label(cell_match: re.Match[str]) -> str:
            nonlocal index
            attrs = cell_match.group(1) or ""
            label = labels[index] if index < len(labels) else ""
            index += 1
            if not label or re.search(r'\bdata-label\s*=', attrs, re.I):
                return cell_match.group(0)
            return f'<td{attrs} data-label="{esc(label)}">'

        return TABLE_DATA_OPEN_RE.sub(add_cell_label, row)

    return TABLE_ROW_RE.sub(add_row_labels, table_html)


def normalize_coupang_outbound_links(body: str) -> str:
    """Force paid outbound Coupang anchors to carry the required rel tokens."""
    def replace_anchor(match: re.Match[str]) -> str:
        attrs = match.group("attrs") or ""
        href_match = HREF_ATTR_RE.search(" " + attrs)
        if not href_match:
            return match.group(0)
        href = html.unescape(href_match.group(2)).strip()
        if "coupang.com" not in href.lower():
            return match.group(0)
        kept = HREF_ATTR_RE.sub("", " " + attrs)
        kept = TARGET_REL_ATTR_RE.sub("", kept)
        kept = re.sub(r"\s+", " ", kept).strip()
        kept = f" {kept}" if kept else ""
        return f'<a{kept} href="{esc(href)}" target="_blank" rel="sponsored nofollow noopener">'

    return A_TAG_OPEN_RE.sub(replace_anchor, str(body or ""))


def localize_public_body(body: str) -> str:
    out = normalize_coupang_outbound_links(body)
    for source_url, path in SOURCE_URL_TO_PATH.items():
        if source_url:
            out = out.replace(source_url, path)

    def wrap_table(match: re.Match[str]) -> str:
        table = mobile_labeled_table(match.group(1))
        before = out[max(0, match.start() - 80):match.start()]
        if 'class="table-scroll"' in before:
            return table
        return f'<div class="table-scroll" role="region" aria-label="비교표는 모바일에서 카드로 표시됩니다">{table}</div>'

    out = TABLE_RE.sub(wrap_table, out)
    return out


def parse_dt(value: str | None) -> datetime:
    if not value:
        return NOW
    raw = str(value).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=KST)
            return dt.astimezone(KST)
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KST)
        return dt.astimezone(KST)
    except ValueError:
        return NOW


def article_path(section: str, slug: str) -> str:
    slug = str(slug).strip().strip("/")
    return f"/{section}/{slug}/"


def validate_article(section: str, data: dict, path: Path) -> dict:
    slug = str(data.get("slug") or path.stem).strip().strip("/")
    title = str(data.get("title") or "").strip()
    body = str(data.get("body_html") or "").strip()
    if not slug or not title or not body:
        raise BuildError(f"{path}: slug/title/body_html required")
    if "<script" in body.lower():
        raise BuildError(f"{path}: script tags are forbidden in article bodies")
    description = str(data.get("description") or short_text(body, 170)).strip()
    date = str(data.get("date") or data.get("published_at") or TODAY)
    dt = parse_dt(date)
    tags = data.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    out = dict(data)
    out.update(
        {
            "section": section,
            "slug": slug,
            "path": article_path(section, slug),
            "file": f"{section}/{slug}/index.html",
            "title": title,
            "description": description,
            "body_html": body,
            "date": dt.isoformat(timespec="seconds"),
            "date_obj": dt,
            "category": str(data.get("category") or ("파트너스 픽" if section == "deals" else "동네 레이더")),
            "tags": tags,
            "image_url": str(data.get("image_url") or data.get("thumbnail_url") or data.get("hero_image") or image_from_body(body)),
            "primary_deal_url": str(data.get("primary_deal_url") or data.get("deal_url") or coupang_url_from_body(body)),
            "price_hint": str(data.get("price_hint") or price_hint_from_body(body)),
            "item_count_hint": str(data.get("item_count_hint") or item_count_hint(title, body)),
            "priority": str(data.get("priority") or ("0.72" if section == "radar" else "0.54")),
            "type": "BlogPosting",
            "is_affiliate": bool(data.get("is_affiliate", section == "deals")),
        }
    )
    return out


def load_articles(section: str) -> list[dict]:
    folder = ROOT / "content" / section
    if not folder.exists():
        return []
    articles: list[dict] = []
    for path in sorted(folder.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        articles.append(validate_article(section, data, path))
    articles.sort(key=lambda a: (a["date_obj"], a["slug"]), reverse=True)
    return articles


def jsonld_for(page: dict) -> str:
    path = page["path"]
    url = BASE + path
    graph: list[dict[str, Any]] = [
        {
            "@type": "WebSite",
            "@id": f"{BASE}/#website",
            "name": SITE_NAME,
            "url": f"{BASE}/",
            "inLanguage": "ko-KR",
            "description": SITE_DESC,
            "publisher": {"@id": f"{BASE}/#publisher"},
            "potentialAction": {
                "@type": "SearchAction",
                "target": f"{BASE}/search/?q={{search_term_string}}",
                "query-input": "required name=search_term_string",
            },
        },
        {
            "@type": ["Organization", "Person"],
            "@id": f"{BASE}/#publisher",
            "name": "r2cuerdame / Recuerdame Lab",
            "url": f"{BASE}/",
        },
        {
            "@type": "SiteNavigationElement",
            "name": [name for name, _, _ in NAV],
            "url": [f"{BASE}{href}" for _, href, _ in NAV],
        },
    ]
    if path != "/":
        section_label = "구매가이드" if path.startswith("/deals/") else "동네 레이더" if path.startswith("/radar/") else page.get("title", SITE_NAME)
        section_path = "/deals/" if path.startswith("/deals/") else "/radar/" if path.startswith("/radar/") else path
        items = [
            {"@type": "ListItem", "position": 1, "name": "홈", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": section_label, "item": f"{BASE}{section_path}"},
        ]
        if page.get("type") == "BlogPosting" and section_path != path:
            items.append({"@type": "ListItem", "position": 3, "name": page["title"], "item": url})
        graph.append({"@type": "BreadcrumbList", "@id": f"{url}#breadcrumb", "itemListElement": items})
    if page.get("type") == "BlogPosting":
        graph.append(
            {
                "@type": "BlogPosting",
                "@id": f"{url}#article",
                "headline": page["title"],
                "description": page["description"],
                "url": url,
                "mainEntityOfPage": {"@id": f"{url}#webpage"},
                "isPartOf": {"@id": f"{BASE}/#website"},
                "author": {"@id": f"{BASE}/#publisher"},
                "publisher": {"@id": f"{BASE}/#publisher"},
                "inLanguage": "ko-KR",
                "datePublished": page.get("date"),
                "dateModified": page.get("updated_at") or NOW.isoformat(timespec="seconds"),
                "articleSection": page.get("category"),
                "keywords": page.get("tags") or [],
                "image": page.get("image_url") or f"{BASE}/assets/og-card.svg",
            }
        )
        graph.append(
            {
                "@type": "WebPage",
                "@id": f"{url}#webpage",
                "url": url,
                "name": page["title"],
                "description": page["description"],
                "isPartOf": {"@id": f"{BASE}/#website"},
                "inLanguage": "ko-KR",
            }
        )
    else:
        graph.append(
            {
                "@type": page["type"],
                "@id": f"{url}#webpage",
                "url": url,
                "name": page["title"],
                "description": page["description"],
                "isPartOf": {"@id": f"{BASE}/#website"},
                "inLanguage": "ko-KR",
                "datePublished": "2026-04-29T21:00:00+09:00",
                "dateModified": NOW.isoformat(timespec="seconds"),
            }
        )
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))


def keyword_join(*chunks: Any) -> str:
    terms: list[str] = []
    for chunk in chunks:
        if isinstance(chunk, (list, tuple, set)):
            raw_terms = [str(x) for x in chunk]
        else:
            raw_terms = str(chunk or "").split(",")
        for raw in raw_terms:
            term = re.sub(r"\s+", " ", str(raw).strip())
            if term and term not in terms:
                terms.append(term)
    return ", ".join(terms)


def keywords_for(page: dict) -> str:
    section = page.get("section") or ""
    path = str(page.get("path") or "")
    title_desc = f"{page.get('title', '')} {page.get('description', '')} {' '.join(page.get('tags') or [])}"
    if section == "radar" or path.startswith("/radar/"):
        extras = []
        if any(token in title_desc for token in ("카페", "상가", "권리금", "창업", "상권")):
            extras.extend(["상가 계약", "상가 임대차", "카페 창업", "권리금 리스크", "상권 리스크"])
        if any(token in title_desc for token in ("월세", "전세", "이사", "통근", "생활권", "관리비")):
            extras.extend(["이사 준비", "월세 압박", "전세 체크리스트", "통근 피로", "생활권 비교"])
        return keyword_join(RADAR_KEYWORDS, page.get("tags") or [], extras)
    if section in {"home", "guides", "about"}:
        return keyword_join(COMMON_KEYWORDS, RADAR_KEYWORDS)
    if section == "search":
        return keyword_join(COMMON_KEYWORDS, RADAR_KEYWORDS, DEALS_KEYWORDS, "사이트 검색, 상품 검색, 구매가이드 검색")
    if section == "deals" or path.startswith("/deals/"):
        extras = []
        if any(token in title_desc for token in ("공기청정기", "제습기", "청소기", "로봇", "헤드셋", "키보드", "모니터")):
            extras.extend(["생활가전 추천", "가전 비교", "재택근무 장비", "인기 상품"])
        return keyword_join(DEALS_KEYWORDS, page.get("tags") or [], extras)
    return COMMON_KEYWORDS


def layout(page: dict, body: str) -> str:
    canonical = BASE + page["path"]
    title = page["title"]
    description = page["description"]
    keywords = keywords_for(page)
    og_image = page.get("image_url") or f"{BASE}/assets/og-card.svg"
    is_deals_page = page.get("section") == "deals" or str(page.get("path") or "").startswith("/deals/")
    nav = deals_nav_html(page["path"]) if is_deals_page else nav_html(page["path"])
    brand_label = "쇼핑픽" if is_deals_page else "Recuerdame Lab"
    brand_sub = "구매 전 비교" if is_deals_page else "계약 전 동네 레이더"
    body_class = "deals-site" if is_deals_page else "standard-site"
    analytics = analytics_snippet()
    return f'''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}" />
  <meta name="keywords" content="{esc(keywords)}" />
  <meta name="author" content="r2cuerdame" />
  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />
  <meta name="googlebot" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />
  <meta name="google-site-verification" content="ILhLytZTybOA7bvoSNjVcGxz7XrbDHaB9Bma0MZ3BsU" />
  <meta name="naver-site-verification" content="bb83dff028cd4b034e752644078b8cea69499c9a" />
  <meta name="Yeti" content="index,follow" />
  <meta name="Daumoa" content="index,follow" />
  <meta name="date" content="{TODAY}" />
  <link rel="canonical" href="{canonical}" />
  <link rel="sitemap" type="application/xml" href="/sitemap.xml" />
  <link rel="alternate" type="application/rss+xml" title="Recuerdame Lab RSS" href="/feed.xml" />
  <link rel="alternate" type="text/plain" title="LLMs.txt" href="/llms.txt" />
  <link rel="alternate" type="text/plain" title="AI crawler guide" href="/ai.txt" />
  <link rel="icon" href="/assets/logo.svg" type="image/svg+xml" />
  <meta property="og:type" content="{'article' if page.get('type') == 'BlogPosting' else 'website'}" />
  <meta property="og:locale" content="ko_KR" />
  <meta property="og:site_name" content="{esc(SITE_NAME)}" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(description)}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:image" content="{esc(og_image)}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="theme-color" content="#101828" />
  <link rel="stylesheet" href="/main.css?v={asset_version(CSS)}" />
{analytics}
  <script type="application/ld+json">{jsonld_for(page)}</script>
</head>
<body class="{body_class}">
  <a class="skip-link" href="#content">본문 바로가기</a>
  <header class="site-header">
    <a class="brand" href="{'/deals/' if is_deals_page else '/'}" aria-label="{esc(brand_label)} home">
      <span class="brand-mark">R</span>
      <span class="brand-copy"><strong>{esc(brand_label)}</strong><small>{esc(brand_sub)}</small></span>
    </a>
    <nav class="nav" aria-label="주요 메뉴">
{nav}
    </nav>
  </header>
  <main id="content">
    {body}
  </main>
  <footer class="footer">
    <p><strong>Recuerdame Lab</strong> — 이사·월세·전세·상가 계약 전, 동네 리스크를 먼저 거르는 공개 노트.</p>
    <p class="muted">/radar/는 동네 레이더, /deals/는 별도 구매가이드로 분리해 운영합니다.</p>
    <p class="muted">마지막 업데이트: <time datetime="{NOW.isoformat(timespec='seconds')}">{NOW.strftime('%Y-%m-%d %H:%M KST')}</time></p>
  </footer>
</body>
</html>
'''


def plain_article_card(a: dict) -> str:
    tags = " ".join(f'<span class="tag pale">{esc(t)}</span>' for t in (a.get("tags") or [])[:3])
    date = parse_dt(a.get("date")).strftime("%Y-%m-%d")
    metric = traffic_badge(a["path"])
    return f'''<article class="list-card">
  <div class="card-meta"><span class="tag">{esc(a.get('category'))}</span><time datetime="{esc(a.get('date'))}">{date}</time>{metric}</div>
  <h2><a href="{esc(a['path'])}">{esc(a['title'])}</a></h2>
  <p>{esc(short_text(a['description'], 115))}</p>
  <div class="tag-row">{tags}</div>
  <a class="text-link" href="{esc(a['path'])}">읽어보기 →</a>
</article>'''


RADAR_CARD_VISUALS = {
    "commute-fatigue-neighborhood-check": {
        "theme": "theme-commute",
        "scene": "commute",
        "badge": "출근길 함정",
        "label": "CASE 01",
        "headline": "35분→50분",
        "subline": "앱 시간 말고 몸이 기억하는 시간",
        "chips": ("앱", "환승", "마지막 도보"),
    },
    "after-work-neighborhood-check": {
        "theme": "theme-night",
        "scene": "night",
        "badge": "밤길 수사",
        "label": "CASE 02",
        "headline": "낮사진 사기",
        "subline": "방보다 귀가 장면을 먼저 본다",
        "chips": ("출구", "골목", "소음"),
    },
    "maintenance-fee-opaque-rent": {
        "theme": "theme-fee",
        "scene": "fee",
        "badge": "관리비 블랙박스",
        "label": "CASE 03",
        "headline": "+α 고정비",
        "subline": "월세 옆 빈칸을 열어 본다",
        "chips": ("월세", "공용", "계절비"),
    },
    "monthly-rent-pressure-questions": {
        "theme": "theme-pressure",
        "scene": "pressure",
        "badge": "월세 착시",
        "label": "CASE 04",
        "headline": "5만↓ 손실↑",
        "subline": "싼 숫자 뒤 생활비를 꺼낸다",
        "chips": ("보증금", "통근", "생활비"),
    },
    "dongne-signal-framework": {
        "theme": "theme-filter",
        "scene": "filter",
        "badge": "후보 필터",
        "label": "CASE 05",
        "headline": "저장 말고 삭제",
        "subline": "후보 과잉을 3곳으로 줄인다",
        "chips": ("예산", "통근", "생활권"),
    },
    "cafe-contract-risk": {
        "theme": "theme-cafe",
        "scene": "cafe",
        "badge": "상권 현장",
        "label": "CASE 06",
        "headline": "사람≠손님",
        "subline": "유동인구가 매출로 바뀌는지 본다",
        "chips": ("유동", "컵", "경쟁점"),
    },
}


def radar_card_visual(a: dict) -> dict:
    slug = a.get("slug") or (a.get("path") or "").strip("/").split("/")[-1]
    if slug in RADAR_CARD_VISUALS:
        return RADAR_CARD_VISUALS[slug]
    joined = " ".join([a.get("title") or "", a.get("description") or "", " ".join(a.get("tags") or [])])
    if any(token in joined for token in ("관리비", "교통비", "총액")):
        return {"theme": "theme-fee", "scene": "fee", "badge": "비용 추적", "label": "CASE", "headline": "숨은 고정비", "subline": "계약 전 빈칸을 확인", "chips": ("월세", "관리비", "총액")}
    if any(token in joined for token in ("카페", "상가", "권리금", "상권")):
        return {"theme": "theme-cafe", "scene": "cafe", "badge": "상권 현장", "label": "CASE", "headline": "사람≠손님", "subline": "발길이 돈이 되는지 확인", "chips": ("상권", "유동", "권리")}
    if any(token in joined for token in ("퇴근", "밤", "소음", "골목")):
        return {"theme": "theme-night", "scene": "night", "badge": "밤길 수사", "label": "CASE", "headline": "밤에 다시 보기", "subline": "낮사진을 의심", "chips": ("출구", "골목", "소음")}
    return {"theme": "theme-filter", "scene": "filter", "badge": "계약 전 신호", "label": "CASE", "headline": "후보 줄이기", "subline": "좋은 집보다 위험 신호 먼저", "chips": ("신호", "질문", "판단")}


def radar_scene_markup(scene: str, chips: tuple[str, str, str]) -> str:
    c0, c1, c2 = (esc(chip) for chip in chips)
    if scene == "commute":
        return f'''<span class="scene-art commute-art">
      <span class="time-card">35→50</span>
      <span class="rail-line"></span>
      <span class="station station-a">{c0}</span><span class="station station-b">{c1}</span><span class="station station-c">{c2}</span>
      <span class="rain-mark"></span>
    </span>'''
    if scene == "night":
        return f'''<span class="scene-art night-art">
      <span class="lamp-post"></span><span class="lamp-light"></span><span class="alley-road"></span>
      <span class="window-stack"></span><span class="noise-wave wave-one"></span><span class="noise-wave wave-two"></span>
      <span class="street-chip chip-a">{c0}</span><span class="street-chip chip-b">{c1}</span><span class="street-chip chip-c">{c2}</span>
    </span>'''
    if scene == "fee":
        return f'''<span class="scene-art fee-art">
      <span class="receipt"><b>관리비</b><i>{c0}</i><i>{c1}</i><i>{c2}</i></span>
      <span class="stamp">빈칸?</span><span class="coin coin-a"></span><span class="coin coin-b"></span>
    </span>'''
    if scene == "pressure":
        return f'''<span class="scene-art pressure-art">
      <span class="calc"><b>월세</b><i></i><i></i><i></i><i></i><i></i><i></i></span>
      <span class="loss-line">5만↓</span><span class="cost-chip chip-a">{c0}</span><span class="cost-chip chip-b">{c1}</span><span class="cost-chip chip-c">{c2}</span>
    </span>'''
    if scene == "cafe":
        return f'''<span class="scene-art cafe-art">
      <span class="awning"></span><span class="storefront"><b>CAFE?</b></span><span class="cup"></span>
      <span class="footfall dot-a"></span><span class="footfall dot-b"></span><span class="footfall dot-c"></span>
      <span class="rival-sign">경쟁</span>
    </span>'''
    return f'''<span class="scene-art filter-art">
      <span class="funnel"></span><span class="checklist"><i>{c0}</i><i>{c1}</i><i>{c2}</i></span>
      <span class="reject-card">삭제</span><span class="keep-card">보류</span>
    </span>'''


def radar_article_card(a: dict) -> str:
    tags = " ".join(f'<span class="tag pale">{esc(t)}</span>' for t in (a.get("tags") or [])[:3])
    date = parse_dt(a.get("date")).strftime("%m.%d")
    metric = traffic_badge(a["path"])
    desc = short_text(a.get("description") or "", 84)
    suspicion = short_text(a.get("radar_suspicion") or "", 58)
    visual = radar_card_visual(a)
    theme = visual["theme"]
    scene = visual["scene"]
    chips = visual["chips"]
    hook = f'<p class="radar-card-hook">오늘의 의심 · {esc(suspicion)}</p>' if suspicion else ""
    return f'''<article class="list-card radar-card {theme}">
  <a class="radar-card-visual scene-{esc(scene)}" href="{esc(a['path'])}" aria-label="{esc(a['title'])}">
    <span class="radar-thumb-label">{esc(visual['label'])}</span>
    <strong class="radar-thumb-title">{esc(visual['headline'])}</strong>
    <span class="radar-thumb-subline">{esc(visual['subline'])}</span>
    <span class="radar-thumb-art" aria-hidden="true">
      {radar_scene_markup(scene, chips)}
    </span>
    <span class="radar-card-badge">{esc(visual['badge'])}</span>
  </a>
  <div class="radar-card-body">
    <div class="card-meta"><span class="tag">{esc(a.get('category'))}</span><time datetime="{esc(a.get('date'))}">{date}</time>{metric}</div>
    <h2><a href="{esc(a['path'])}">{esc(a['title'])}</a></h2>
    {hook}
    <p>{esc(desc)}</p>
    <div class="tag-row">{tags}</div>
    <div class="radar-card-actions"><span>오늘의 의심</span><span>현장 미션</span><span>판정 기준</span></div>
    <a class="text-link" href="{esc(a['path'])}">레이더 열기 →</a>
  </div>
</article>'''


def article_headings(body_html: str, limit: int = 5) -> list[str]:
    headings = []
    for raw in re.findall(r'<h2[^>]*>(.*?)</h2>', body_html or "", flags=re.I | re.S):
        label = re.sub(r"^\s*\d+(?:-\d+)?[.)]\s*", "", strip_tags(raw))
        label = short_text(label, 42)
        if label and label not in headings:
            headings.append(label)
        if len(headings) >= limit:
            break
    return headings


def radar_experience_block(article: dict) -> str:
    target = short_text(article.get("target_audience") or "계약 전 후보 동네를 빠르게 거르고 싶은 독자", 86)
    suspicion = short_text(article.get("radar_suspicion") or article.get("description") or "", 96)
    mission = short_text(article.get("field_mission") or "표를 외우지 말고 현장에서 의심할 장면과 질문을 먼저 잡습니다.", 96)
    headings = article_headings(article.get("body_html") or "")
    toc = "".join(f'<li><span>{i:02d}</span>{esc(label)}</li>' for i, label in enumerate(headings, start=1))
    if not toc:
        toc = '<li><span>01</span>오늘의 의심을 먼저 보고 본문으로 들어갑니다.</li>'
    return f'''<section class="radar-experience-grid" aria-label="본문 전 시각 요약">
  <div class="radar-map-card">
    <p class="eyebrow">Visual Scan</p>
    <h2>계약 전 20분 수사 루프</h2>
    <p>좋은 동네를 찾는 척하지 말고, 계약 뒤 매일 반복될 불편을 먼저 잡습니다.</p>
    <div class="radar-map" aria-hidden="true">
      <svg class="map-route" viewBox="0 0 100 100" preserveAspectRatio="none" role="presentation" focusable="false">
        <defs>
          <marker id="radar-detail-route-arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto" markerUnits="strokeWidth">
            <path d="M 0 0 L 10 5 L 0 10 Z" class="map-route-arrow"></path>
          </marker>
        </defs>
        <path class="map-route-guide map-route-desktop" d="M 13 66 C 20 54 24 43 31 39 C 39 34 43 49 50 57 C 57 65 66 48 74 36 C 82 24 87 45 88 61 L 94 66"></path>
        <path class="map-route-path map-route-desktop" d="M 13 66 C 20 54 24 43 31 39 C 39 34 43 49 50 57 C 57 65 66 48 74 36 C 82 24 87 45 88 61 L 94 66" marker-end="url(#radar-detail-route-arrow)"></path>
        <path class="map-route-guide map-route-mobile" d="M 17 26 C 32 16 47 18 58 28 C 71 38 82 34 82 47 C 82 65 55 59 38 66 C 48 76 58 88 72 83 L 89 78"></path>
        <path class="map-route-path map-route-mobile" d="M 17 26 C 32 16 47 18 58 28 C 71 38 82 34 82 47 C 82 65 55 59 38 66 C 48 76 58 88 72 83 L 89 78" marker-end="url(#radar-detail-route-arrow)"></path>
      </svg>
      <span class="map-label">1→5 현장 순서</span>
      <span class="map-node node-1"><b>1</b><em>출구</em></span>
      <span class="map-node node-2"><b>2</b><em>큰길</em></span>
      <span class="map-node node-3"><b>3</b><em>골목</em></span>
      <span class="map-node node-4"><b>4</b><em>입구</em></span>
      <span class="map-node node-5"><b>5</b><em>소음</em></span>
    </div>
  </div>
  <div class="radar-brief-stack">
    <article class="brief-card hot"><span>SUSPECT</span><strong>오늘의 의심</strong><p>{esc(suspicion)}</p></article>
    <article class="brief-card"><span>WHO</span><strong>이런 사람용</strong><p>{esc(target)}</p></article>
    <article class="brief-card"><span>MISSION</span><strong>현장 미션</strong><p>{esc(mission)}</p></article>
  </div>
  <div class="radar-toc-card">
    <strong>오늘 볼 순서</strong>
    <ol>{toc}</ol>
  </div>
</section>
'''


def deal_card(a: dict, rank: int | None = None) -> str:
    img = a.get("image_url") or ""
    card_class = "deal-card" if img else "deal-card text-card"
    if rank:
        card_class += " ranked"
    date = parse_dt(a.get("date")).strftime("%m.%d")
    metric = traffic_badge(a["path"])
    deal_url = a.get("primary_deal_url") or ""
    external = ""
    if deal_url:
        external = f'<a class="deal-price-link" href="{esc(deal_url)}" target="_blank" rel="sponsored nofollow noopener">가격 확인</a>'
    rank_badge = f'<span class="deal-rank">BEST {rank}</span>' if rank else ""
    if img:
        thumb = f'''<a class="deal-thumb" href="{esc(a['path'])}" aria-label="{esc(a['title'])}">
    <img src="{esc(img)}" alt="{esc(a['title'])} 대표 상품 이미지" loading="lazy" decoding="async" />
    <span class="deal-count">{esc(a.get('item_count_hint') or '비교글')}</span>
    {rank_badge}
  </a>'''
    else:
        thumb = f'''<a class="deal-text-badge" href="{esc(a['path'])}" aria-label="{esc(a['title'])}">
    <span>{esc(a.get('item_count_hint') or '비교글')}</span>
    {rank_badge}
  </a>'''
    price_hint = esc(a.get("price_hint") or "상세가는 상품 페이지에서 확인")
    return f'''<article class="{card_class}">
  {thumb}
  <div class="deal-body">
    <div class="deal-meta"><span>{esc(a.get('category'))}</span><time datetime="{esc(a.get('date'))}">{date}</time>{metric}</div>
    <h2><a href="{esc(a['path'])}">{esc(a['title'])}</a></h2>
    <p>{esc(short_text(a.get('description') or '', 92))}</p>
    <div class="deal-price"><span>{price_hint}</span>{external}</div>
    <div class="deal-actions">
      <a class="deal-button primary" href="{esc(a['path'])}">비교글 보기</a>
    </div>
  </div>
</article>'''


def deal_cards(articles: list[dict]) -> str:
    if not articles:
        return '<article class="list-card"><span class="tag">준비중</span><h2>곧 새로운 쇼핑픽을 올릴게요.</h2><p>사진과 핵심 비교 포인트를 같이 볼 수 있게 준비 중입니다.</p></article>'
    return "\n".join(deal_card(a) for a in articles)


def best_deal_cards(articles: list[dict], limit: int = 6) -> str:
    prioritized = deals_by_growth_priority(articles)[:limit]
    if not prioritized:
        return deal_cards([])
    return "\n".join(deal_card(a, rank=index) for index, a in enumerate(prioritized, start=1))


def article_cards(articles: list[dict], empty: str) -> str:
    if not articles:
        return f'<article class="list-card"><span class="tag">준비중</span><h2>{esc(empty)}</h2><p>새 글이 올라오면 이곳에서 바로 볼 수 있습니다.</p></article>'
    cards = []
    for a in articles:
        if a.get("section") == "deals":
            cards.append(deal_card(a))
        elif a.get("section") == "radar":
            cards.append(radar_article_card(a))
        else:
            cards.append(plain_article_card(a))
    return "\n".join(cards)


def category_chips(articles: list[dict]) -> str:
    cats = []
    for a in articles:
        cat = str(a.get("category") or "").strip()
        if cat and cat not in cats:
            cats.append(cat)
    if not cats:
        return '<span class="category-chip">비교글 준비중</span>'
    return "".join(f'<a class="category-chip" href="/search/?q={quote(c)}">{esc(c)}</a>' for c in cats[:8])


def search_form(placeholder: str = "상품명, 용도, 예산, 동네 키워드로 검색") -> str:
    return f'''<form class="site-search" action="/search/" method="get" role="search">
  <label for="search-query">사이트 검색</label>
  <div class="search-row">
    <input id="search-query" name="q" type="search" placeholder="{esc(placeholder)}" autocomplete="off" />
    <button type="submit">검색</button>
  </div>
  <p class="muted">구매가이드 상품명, 생활용품 용도, 동네·계약 키워드를 같이 찾습니다.</p>
</form>'''


def search_body(deals: list[dict], radar: list[dict]) -> str:
    popular_links = "\n".join(
        f'<li><a href="{esc(a["path"])}">{esc(a["title"])}</a><span>{esc(a.get("category"))}</span></li>'
        for a in (deals[:5] + radar[:5])
    )
    return f'''
<section class="page-hero compact">
  <p class="eyebrow">Site Search</p>
  <h1>상품·동네·계약 키워드로 바로 찾기</h1>
  <p class="lead">구매가이드 상품 비교글과 동네 레이더 글을 한 번에 검색합니다. 검색 결과는 브라우저에서만 처리됩니다.</p>
</section>
<section class="panel soft search-panel">
  {search_form("예: 공기청정기, 제습기, 헤드셋, 월세, 통근, 상가")}
</section>
<section class="search-results" aria-live="polite">
  <div class="section-title"><h2>검색 결과</h2><p id="search-summary">검색어를 입력하면 관련 글을 보여줍니다.</p></div>
  <div id="search-results" class="article-list mixed-list"></div>
</section>
<section class="panel">
  <h2>많이 찾는 시작점</h2>
  <ul class="quick-links">{popular_links}</ul>
</section>
<script src="/assets/search.js?v={asset_version(SEARCH_JS)}" defer></script>
'''


def hero_pins(articles: list[dict]) -> str:
    pins = []
    for idx, a in enumerate([x for x in articles if x.get("image_url")][:3], start=1):
        pins.append(f'''<a class="hero-pin pin-{idx}" href="{esc(a['path'])}">
  <img src="{esc(a['image_url'])}" alt="{esc(a['title'])}" loading="eager" decoding="async" />
  <span>{esc(a.get('category'))}</span>
</a>''')
    return "\n".join(pins)


def article_views(article: dict) -> int:
    metric = metric_for(article.get("path") or "")
    for key in ("views", "screenPageViews", "page_views"):
        try:
            return int(metric.get(key) or 0)
        except Exception:
            continue
    return 0


def deals_by_growth_priority(deals: list[dict]) -> list[dict]:
    return sorted(
        deals,
        key=lambda a: (article_views(a), parse_dt(a.get("date")).timestamp(), str(a.get("title") or "")),
        reverse=True,
    )


def search_chip(label: str) -> str:
    return f'<a class="search-chip" href="/search/?q={quote(label)}">{esc(label)}</a>'


def matches_deal_intent(article: dict, terms: list[str]) -> bool:
    haystack = " ".join(
        [
            str(article.get("title") or ""),
            str(article.get("description") or ""),
            str(article.get("category") or ""),
            " ".join(str(t) for t in (article.get("tags") or [])),
        ]
    ).lower()
    return any(term.lower() in haystack for term in terms)


def mini_deal_links(articles: list[dict], empty_label: str = "관련 비교글 준비중") -> str:
    if not articles:
        return f'<li class="muted">{esc(empty_label)}</li>'
    return "\n".join(
        f'<li><a href="{esc(a["path"])}">{esc(short_text(a.get("title") or "", 42))}</a></li>'
        for a in articles[:3]
    )


def deal_intent_hubs(deals: list[dict]) -> str:
    intents = [
        {
            "label": "장마·습기",
            "title": "습기·공기부터 실패 줄이기",
            "description": "제습기와 공기청정기는 방 크기, 물통 관리, 필터 비용을 먼저 보면 과소비를 줄일 수 있습니다.",
            "terms": ["제습기", "공기청정기", "장마", "습기", "필터"],
            "queries": ["원룸 제습기", "공기청정기", "장마 가전"],
        },
        {
            "label": "재택·책상",
            "title": "오래 앉는 사람의 책상 셋업",
            "description": "모니터암, 모니터 조명, 의자, 키보드는 예쁜 것보다 자세·눈 피로·공간 효율 기준으로 골라야 합니다.",
            "terms": ["모니터", "의자", "키보드", "재택", "책상", "개발자"],
            "queries": ["모니터암", "사무용 의자", "모니터 조명"],
        },
        {
            "label": "몰입·이동",
            "title": "소리 장비는 사용 장소부터",
            "description": "ANC 헤드폰, 게이밍 헤드셋, 블루투스 스피커는 출퇴근·회의·캠핑처럼 쓰는 장소가 다르면 정답도 달라집니다.",
            "terms": ["헤드폰", "헤드셋", "스피커", "ANC", "블루투스", "마샬", "보스"],
            "queries": ["ANC 헤드폰", "게이밍 헤드셋", "블루투스 스피커"],
        },
        {
            "label": "선물·생활",
            "title": "선물용은 관리 부담까지 보기",
            "description": "뷰티·주방·퍼스널케어 가전은 가격보다 매일 쓰는지, 소모품과 세척 부담이 적은지를 같이 봐야 합니다.",
            "terms": ["뷰티", "퍼스널", "주방", "전동", "드라이", "선물"],
            "queries": ["전동칫솔", "드라이기", "주방가전"],
        },
    ]
    cards = []
    prioritized = deals_by_growth_priority(deals)
    for intent in intents:
        matched = [a for a in prioritized if matches_deal_intent(a, intent["terms"])]
        chips = "".join(search_chip(q) for q in intent["queries"])
        cards.append(f'''<article class="intent-card">
  <span class="tag pale">{esc(intent['label'])}</span>
  <h2>{esc(intent['title'])}</h2>
  <p>{esc(intent['description'])}</p>
  <div class="search-chip-row">{chips}</div>
  <ul class="mini-link-list">{mini_deal_links(matched)}</ul>
</article>''')
    return "\n".join(cards)


def popular_deal_list(deals: list[dict]) -> str:
    rows = []
    for index, article in enumerate(deals_by_growth_priority(deals)[:5], start=1):
        views = article_views(article)
        metric = f"최근 30일 {views}회" if views else "신규/색인 대기"
        rows.append(f'''<li>
  <span class="rank">{index}</span>
  <a href="{esc(article['path'])}">{esc(article['title'])}</a>
  <small>{esc(metric)} · {esc(article.get('category'))}</small>
</li>''')
    return "\n".join(rows) or '<li class="muted">조회 데이터 수집 중</li>'


def deal_category_hubs(deals: list[dict]) -> str:
    grouped: dict[str, list[dict]] = {}
    for article in deals:
        category = str(article.get("category") or "기타 구매가이드").strip() or "기타 구매가이드"
        grouped.setdefault(category, []).append(article)
    cards = []
    for category in sorted(grouped, key=lambda c: (-len(grouped[c]), c)):
        articles = deals_by_growth_priority(grouped[category])
        cards.append(f'''<article class="category-hub">
  <div>
    <span class="tag">{esc(category)}</span>
    <strong>{len(articles)}개 비교글</strong>
  </div>
  <ul class="mini-link-list">{mini_deal_links(articles)}</ul>
</article>''')
    return "\n".join(cards)


def deal_article_product_names(article: dict, limit: int = 5) -> list[str]:
    body = article.get("body_html") or ""
    names: list[str] = []
    skip_terms = ("서론", "결론", "마무리", "제품별", "핵심", "비교표", "구매", "추천 기준", "체크")
    for raw in re.findall(r'<h[23][^>]*>(.*?)</h[23]>', body, flags=re.I | re.S):
        name = strip_tags(raw)
        name = re.sub(r"^\s*(?:\d+\s*[.)]|[①-⑩]|BEST\s*\d+\s*[:.-]?)\s*", "", name, flags=re.I)
        name = re.sub(r"\s+(?:활용도 체크|구매 포인트|추천 이유|장단점|비교|후기).*$", "", name).strip()
        if not name or any(term in name for term in skip_terms):
            continue
        if name not in names:
            names.append(short_text(name, 46))
        if len(names) >= limit:
            break
    return names


def deal_article_quick_block(article: dict) -> str:
    products = deal_article_product_names(article)
    product_items = "".join(f"<li>{esc(name)}</li>" for name in products)
    if not product_items:
        product_items = "<li>본문에서 후보별 장단점과 가격대를 확인하세요.</li>"
    external = ""
    if article.get("primary_deal_url"):
        external = f'<a class="deal-button ghost" href="{esc(article["primary_deal_url"])}" target="_blank" rel="sponsored nofollow noopener">상품 페이지 확인</a>'
    return f'''<section class="deal-quick-box" aria-label="구매가이드 빠른 결론">
  <div class="quick-verdict">
    <span class="tag">3분 컷 비교</span>
    <h2>장바구니 넣기 전 이렇게 판단하세요</h2>
    <p>{esc(short_text(article.get('description') or '', 150))}</p>
    <p class="quick-note">사지 말아야 할 이유가 먼저 보이면 오늘은 보류해도 괜찮습니다.</p>
  </div>
  <div class="quick-facts" aria-label="핵심 정보">
    <div><strong>{esc(article.get('item_count_hint') or '비교글')}</strong><span>후보 수</span></div>
    <div><strong>{esc(article.get('price_hint') or '상세 확인')}</strong><span>가격 기준</span></div>
    <div><strong>{esc(article.get('category') or '구매가이드')}</strong><span>카테고리</span></div>
  </div>
  <div class="quick-products">
    <h3>본문에서 비교하는 후보</h3>
    <ol>{product_items}</ol>
  </div>
  <div class="deal-actions quick-actions">
    <a class="deal-button primary" href="#article-body">비교 내용 바로 보기</a>{external}
  </div>
</section>'''


def home_body(deals: list[dict], radar: list[dict]) -> str:
    radar_html = article_cards(radar[:4], "첫 동네 레이더 글 준비중")
    deal_html = article_cards(deals[:3], "구매가이드 글 준비중") if deals else ""
    return f'''
<section class="hero home-hero">
  <p class="eyebrow">Dongne Radar · Recuerdame Lab</p>
  <h1>이사·월세·상가 계약 전, 동네 리스크부터 걸러냅니다.</h1>
  <p class="lead">동네 레이더는 “여기가 좋다”가 아니라 내 계약 조건에서 피해야 할 신호와 현장에서 다시 물어볼 질문을 먼저 정리합니다.</p>
  <div class="hero-actions">
    <a class="button primary" href="/radar/">동네 레이더 먼저 보기</a>
    <a class="button" href="/guides/">읽는 순서 보기</a>
    <a class="button" href="/deals/">구매가이드 별도 보기</a>
  </div>
</section>
<section class="grid three">
  <article class="card accent-blue">
    <span class="tag">Primary</span>
    <h2>동네 레이더</h2>
    <p>월세·전세 계약, 통근 피로, 생활권, 밤길·소음·관리비, 상가 권리금 리스크를 계약 전 질문으로 바꿉니다.</p>
    <a href="/radar/">/radar/ 열기 →</a>
  </article>
  <article class="card accent-green">
    <span class="tag">Guide</span>
    <h2>처음 읽는 순서</h2>
    <p>이사 준비, 상가 계약, 생활 구매를 섞지 않고 목적별로 어떤 글을 먼저 볼지 정리합니다.</p>
    <a href="/guides/">가이드 보기 →</a>
  </article>
  <article class="card accent-orange">
    <span class="tag">Separate</span>
    <h2>구매가이드는 분리</h2>
    <p>생활 상품 비교는 /deals/에서만 다룹니다. 동네 레이더 글에는 제휴 문맥을 섞지 않습니다.</p>
    <a href="/deals/">구매가이드 보기 →</a>
  </article>
</section>
<section class="panel soft">
  <h2>동네 레이더가 보는 범위</h2>
  <div class="category-strip">
    <span class="category-chip">이사 준비</span><span class="category-chip">월세·전세 계약</span><span class="category-chip">통근 피로</span><span class="category-chip">생활권</span><span class="category-chip">밤길·소음·관리비</span><span class="category-chip">상가·권리금</span><span class="category-chip">현장 확인 질문</span>
  </div>
</section>
<section class="article-list mixed-list radar-latest-grid">
  <div class="section-title"><h2>동네 레이더 최신 글</h2><p>계약 전 리스크와 현장 질문을 먼저 확인하세요.</p></div>
  {radar_html}
</section>
<section class="article-list mixed-list">
  <div class="section-title"><h2>분리 운영 중인 구매가이드</h2><p>상품 비교가 필요할 때만 별도 섹션에서 확인합니다.</p></div>
  {deal_html}
</section>
'''

def deals_body(deals: list[dict]) -> str:
    return f'''
<section class="deal-landing-hero">
  <div class="deal-hero-copy">
    <p class="eyebrow">Shopping Picks · 쇼핑픽</p>
    <h1>구매 직전 3분 안에 후보를 좁히는 생활상품 비교</h1>
    <p class="lead">생활가전, 책상 장비, 음향기기를 화려하게 꾸미지 않고 가격대·사용환경·관리 부담 기준으로 정리합니다. 장바구니 앞에서 “이거 진짜 필요한가?” 하고 멈칫하는 시간을 줄이고, 필요하면 카테고리와 검색으로 바로 좁히세요.</p>
    <div class="playful-badges" aria-label="쇼핑픽 사용법">
      <span>장바구니 고민 줄이기</span>
      <span>사지 말아야 할 이유도 같이 보기</span>
      <span>3분 컷 비교</span>
    </div>
    <aside class="affiliate-disclosure" aria-label="제휴 고지">
      <strong>제휴 고지</strong>
      <p>쿠팡 파트너스 활동의 일환으로, 구매 시 이에 따른 일정액의 수수료를 제공받을 수 있습니다. 가격·배송·재고는 상품 페이지에서 다시 확인하세요.</p>
    </aside>
    <div class="hero-actions">
      <a class="button primary" href="#today-best">오늘의 추천 보기</a>
      <a class="button" href="#category-blocks">카테고리로 찾기</a>
      <a class="button" href="#deal-search">검색하기</a>
    </div>
    <div class="category-strip" aria-label="카테고리 빠른 이동">{category_chips(deals)}</div>
  </div>
  <aside class="deal-hero-panel" aria-label="쇼핑픽 운영 기준">
    <strong>오늘의 장바구니 작전</strong>
    <ul class="checklist">
      <li><strong>쓸 장면 먼저:</strong> 방 크기, 책상 공간, 이동·회의처럼 실제 쓰는 상황을 기준으로 봅니다.</li>
      <li><strong>사지 말아야 할 이유:</strong> 소음·공간·세척·필터처럼 싫은 포인트가 크면 과감히 보류합니다.</li>
      <li><strong>마지막 확인:</strong> 옵션·가격·재고·배송 조건은 상품 페이지에서 한 번 더 확인합니다.</li>
    </ul>
    <p class="microcopy">급할수록 “안 사도 되는 이유”를 먼저 한 줄 적어두면 장바구니가 차분해집니다.</p>
  </aside>
</section>
<section class="site-bridge-strip" aria-label="동네 레이더 이동">
  <div>
    <span class="tag pale">길 잃음 방지</span>
    <h2>쇼핑은 쇼핑픽, 동네 판단은 동네 레이더</h2>
    <p>상품 비교만 보러 온 게 아니라 이사·월세·상가 체크 중이었다면 여기서 바로 돌아가세요.</p>
  </div>
  <div class="bridge-actions">
    <a class="button primary" href="/radar/">동네 레이더로 돌아가기</a>
    <a class="button" href="/">Recuerdame Lab 홈</a>
  </div>
</section>
<section id="today-best" class="landing-section above-fold-section">
  <div class="section-title"><p class="eyebrow">Today Best</p><h2>오늘의 추천 BEST</h2><p>최근 조회와 발행일을 함께 보고, 바로 비교하기 좋은 글부터 보여줍니다.</p></div>
  <div class="deal-grid best-grid">{best_deal_cards(deals)}</div>
</section>
<section id="deal-search" class="panel soft search-panel lower-search">
  <div class="section-title"><h2>원하는 상품만 검색</h2><p>상품명, 용도, 예산, 사용 장소를 넣어 관련 비교글을 찾습니다.</p></div>
  {search_form("예: 원룸 제습기, 모니터암, 사무용 의자, 블루투스 스피커")}
</section>
<section id="category-blocks" class="landing-section">
  <div class="section-title"><h2>카테고리별 비교글 묶음</h2><p>생활가전, 재택 장비, 음향기기처럼 같은 의도끼리 묶어 빠르게 이동합니다.</p></div>
  <div class="category-hubs">{deal_category_hubs(deals)}</div>
</section>
<section class="landing-section decision-strip" aria-label="구매 전 체크">
  <div class="section-title"><h2>오늘의 장바구니 작전</h2><p>본문으로 들어가기 전 살 이유와 안 살 이유를 같이 적어두면 비교가 빨라집니다.</p></div>
  <div class="grid three">
    <article class="card"><span class="tag">1</span><h2>쓸 장면 고정</h2><p>원룸, 거실, 재택 책상, 출퇴근, 캠핑처럼 실제 사용 위치를 먼저 정합니다.</p></article>
    <article class="card"><span class="tag">2</span><h2>사지 말아야 할 이유</h2><p>소음, 공간, 눈 피로, 허리 부담, 세척·필터 비용 중 가장 싫은 실패를 고릅니다.</p></article>
    <article class="card"><span class="tag">3</span><h2>마지막 확인</h2><p>상세 가격·배송·옵션·최근 후기는 연결된 상품 페이지에서 다시 확인합니다.</p></article>
  </div>
</section>
<section id="all-deals" class="landing-section">
  <div class="section-title"><h2>전체 비교글</h2><p>이미 공개된 쇼핑픽 구매가이드 전체 목록입니다.</p></div>
  <div class="deal-grid">{deal_cards(deals)}</div>
</section>
'''

def radar_body(radar: list[dict]) -> str:
    return f'''
<section class="page-hero compact">
  <p class="eyebrow">Dongne Radar</p>
  <h1>동네 레이더: 계약 전 리스크 체크</h1>
  <p class="lead">이사, 월세·전세, 통근, 생활권, 상가 계약 전에 “좋아 보이는 동네”보다 먼저 걸러야 할 신호와 현장 확인 질문을 정리합니다.</p>
  <div class="hero-actions">
    <a class="button primary" href="/guides/">처음 읽는 순서</a>
    <a class="button" href="/radar/dongne-signal-framework/">전월세 체크</a>
    <a class="button" href="/radar/cafe-contract-risk/">상가 계약 체크</a>
  </div>
</section>
<section class="panel soft">
  <h2>현재 레이더 범위</h2>
  <div class="category-strip">
    <span class="category-chip">예산·보증금·월세</span><span class="category-chip">관리비·교통비</span><span class="category-chip">통근·대체 생활권</span><span class="category-chip">생활 상권</span><span class="category-chip">밤길·소음</span><span class="category-chip">상가 임대차·권리금</span>
  </div>
</section>
<section class="article-list">
  <div class="section-title"><h2>공개된 동네 레이더 글</h2><p>각 글은 결론보다 “계약 전 무엇을 다시 확인할지”에 맞춰 읽으면 됩니다.</p></div>
  {article_cards(radar, "첫 동네 레이더 글 준비중")}
</section>
'''

def guides_body() -> str:
    return '''
<section class="page-hero compact">
  <p class="eyebrow">Guides</p>
  <h1>동네 레이더 읽는 순서</h1>
  <p class="lead">이사·월세·전세·상가 계약 전에는 글을 많이 읽는 것보다, 내 조건에서 먼저 지워야 할 리스크를 순서대로 보는 게 중요합니다.</p>
</section>
<section class="grid three">
  <article class="card accent-blue">
    <span class="tag">1 · 이사·전월세</span>
    <h2>집 보기 전</h2>
    <p>예산 상한, 보증금·월세·관리비, 통근 피로, 생활 상권, 밤길·소음을 먼저 걸러봅니다.</p>
    <a href="/radar/dongne-signal-framework/">계약 전 체크리스트 보기 →</a>
  </article>
  <article class="card accent-green">
    <span class="tag">2 · 상가·창업</span>
    <h2>계약서 쓰기 전</h2>
    <p>유동인구 착시, 경쟁밀도, 폐업 압력, 권리금 회수 리스크를 먼저 의심합니다.</p>
    <a href="/radar/cafe-contract-risk/">카페 상권 리스크 보기 →</a>
  </article>
  <article class="card accent-orange">
    <span class="tag">3 · 별도 구매</span>
    <h2>생활 구매는 분리</h2>
    <p>상품 비교가 필요할 때만 구매가이드로 이동합니다. 동네 레이더 판단과 제휴 문맥은 섞지 않습니다.</p>
    <a href="/deals/">구매가이드 보기 →</a>
  </article>
</section>
<section class="panel">
  <h2>이사·월세 계약 루트</h2>
  <ol>
    <li><strong>돈:</strong> 보증금, 월세, 관리비, 교통비를 한 달 고정비로 합쳐 상한선을 잡습니다.</li>
    <li><strong>시간:</strong> 출퇴근, 장보기, 병원, 운동처럼 반복되는 생활 동선을 지도 밖 현장감으로 확인합니다.</li>
    <li><strong>리스크:</strong> 밤길, 소음, 공실, 관리 상태, 관리비 항목, 계약 특약을 현장에서 다시 묻습니다.</li>
    <li><strong>대안:</strong> 같은 예산으로 갈 수 있는 대체 생활권을 한 곳 이상 남겨 협상 여지를 만듭니다.</li>
  </ol>
</section>
<section class="notice compact-notice">
  <strong>섹션 구분</strong>
  <p><a href="/radar/">/radar/</a>는 동네·상권 판단 글, <a href="/deals/">/deals/</a>는 구매가이드 글입니다. 제휴 링크가 있는 글은 해당 본문 안에서 따로 고지합니다.</p>
</section>
'''



def about_body(deals_count: int, radar_count: int) -> str:
    return f'''
<section class="page-hero compact">
  <p class="eyebrow">About</p>
  <h1>Dongne Radar by Recuerdame Lab</h1>
  <p class="lead">동네 레이더는 이사, 월세·전세, 상가 계약처럼 작은 착각이 돈과 시간을 잡아먹는 결정을 더 빨리 걸러내기 위한 공개 노트입니다.</p>
</section>
<section class="grid three">
  <article class="card accent-blue">
    <span class="tag">Primary</span>
    <h2>동네 레이더</h2>
    <p>서울·수도권의 주거·상권 신호를 계약 전 체크리스트와 현장 질문으로 바꿉니다.</p>
    <a href="/radar/">동네 레이더 보기 →</a>
  </article>
  <article class="card accent-green">
    <span class="tag">Reader path</span>
    <h2>처음 읽는 법</h2>
    <p>이사 준비, 상가 계약, 생활 구매를 목적별로 나눠 첫 방문자가 헤매지 않게 합니다.</p>
    <a href="/guides/">읽는 순서 보기 →</a>
  </article>
  <article class="card accent-orange">
    <span class="tag">Separate</span>
    <h2>구매가이드</h2>
    <p>상품 비교와 제휴 가능 글은 /deals/에서만 별도 운영합니다.</p>
    <a href="/deals/">구매가이드 보기 →</a>
  </article>
</section>
<section class="panel soft">
  <h2>바로 볼 수 있는 동네 레이더</h2>
  <ul>
    <li><a href="/radar/dongne-signal-framework/">전월세·이사 계약 전 동네 신호 체크</a></li>
    <li><a href="/radar/cafe-contract-risk/">카페·상가 계약 전 상권 리스크 체크</a></li>
  </ul>
</section>
<section class="panel">
  <h2>운영 원칙</h2>
  <ul>
    <li><strong>판단 중심:</strong> 단순 순위보다 “계약 전 무엇을 걸러야 하는지”를 먼저 씁니다.</li>
    <li><strong>현장 질문:</strong> 데이터가 좋아 보여도 밤길, 소음, 관리비, 공실, 권리금 회수는 다시 묻습니다.</li>
    <li><strong>섹션 분리:</strong> 동네 레이더와 구매가이드는 URL, 고지, 독자 의도를 분리합니다.</li>
    <li><strong>검색 친화:</strong> sitemap, RSS, llms.txt, ai.txt를 유지해 검색엔진과 AI가 읽기 쉽게 둡니다.</li>
    <li><strong>계속 갱신:</strong> 공개 글은 KPI와 독자 의도에 맞춰 제목, 도입부, 체크리스트를 계속 다듬습니다.</li>
  </ul>
  <h2>현재 공개 수</h2>
  <p>동네 레이더 {radar_count}개, 구매가이드 {deals_count}개를 공개 중입니다.</p>
</section>
<section class="notice compact-notice">
  <strong>투명성</strong>
  <p>구매가이드의 일부 링크는 제휴 링크일 수 있으며, 그런 글은 본문에 별도 고지를 표시합니다. 동네 레이더 글에는 제휴 문맥을 섞지 않습니다.</p>
</section>
'''

def article_body(article: dict, related_articles: list[dict] | None = None) -> str:
    section_name = "쇼핑픽" if article["section"] == "deals" else "동네 레이더"
    section_href = f"/{article['section']}/"
    dt = parse_dt(article.get("date"))
    metric = traffic_badge(article["path"])
    tags = " ".join(f'<span class="tag pale">{esc(t)}</span>' for t in (article.get("tags") or [])[:8])
    notice = ""
    if article.get("is_affiliate"):
        notice = '<section class="notice affiliate compact-notice"><strong>제휴 고지</strong><p>쿠팡 파트너스 활동의 일환으로, 구매 시 이에 따른 일정액의 수수료를 제공받을 수 있습니다.</p></section>'
    quick_block = ""
    image_block = ""
    if article.get("section") == "deals":
        article_class = "article-page deal-article"
        quick_block = deal_article_quick_block(article)
        if article.get("image_url"):
            image_block = f'''<section class="article-product-hero">
  <img src="{esc(article['image_url'])}" alt="{esc(article['title'])} 대표 상품 이미지" loading="eager" decoding="async" />
  <div>
    <span class="tag">{esc(article.get('item_count_hint') or '비교글')}</span>
    <h2>대표 이미지와 후보를 확인한 뒤 본문에서 조건을 비교하세요.</h2>
    <p>{esc(article.get('price_hint') or '상세가는 상품 페이지에서 확인')}</p>
  </div>
</section>'''
    else:
        article_class = "article-page"
    visual_block = ""
    if article.get("section") == "radar":
        visual_block = radar_experience_block(article)
        article_class += " radar-article"

    related_block = ""
    if article.get("section") == "deals":
        related_block = f'''<section class="related-radar deal-related-search">
  <div class="deal-radar-return">
    <span class="tag pale">다시 동네 판단</span>
    <h2>쇼핑은 여기까지, 동네 판단은 동네 레이더에서</h2>
    <p>이사·월세·상가 체크가 목적이었다면 비교글에서 바로 빠져나갈 수 있어요.</p>
    <a class="button" href="/radar/">동네 레이더로 돌아가기</a>
  </div>
  <h2>다른 비교글 찾기</h2>
  {search_form("예: 같은 용도, 예산, 브랜드, 생활가전")}
</section>'''
    elif article.get("section") == "radar":
        related = related_articles or []
        links = "".join(f'<li><a href="{esc(a["path"])}">{esc(a["title"])}</a></li>' for a in related[:3])
        if not links:
            links = '<li><a href="/guides/">동네 레이더 읽는 순서</a></li>'
        related_block = f'''<section class="related-radar">
  <h2>다음에 같이 볼 글</h2>
  <ul>{links}<li><a href="/guides/">처음 온 사람을 위한 읽는 순서</a></li></ul>
</section>'''
    if article.get("section") == "deals":
        tail_links = f'''<a class="button" href="{section_href}">쇼핑픽 목록</a>
    <a class="button primary" href="/radar/">동네 레이더로 돌아가기</a>
    <a class="button" href="/search/">검색</a>'''
    else:
        tail_links = f'''<a class="button" href="{section_href}">목록으로</a>
    <a class="button" href="/guides/">읽는 순서</a>'''
    return f'''
<article class="{article_class}">
  <nav class="breadcrumb" aria-label="breadcrumb"><a href="/">홈</a><span>›</span><a href="{section_href}">{esc(section_name)}</a></nav>
  <header class="article-hero">
    <p class="eyebrow">{esc(section_name)}</p>
    <h1>{esc(article['title'])}</h1>
    <p class="lead">{esc(article['description'])}</p>
    <div class="article-meta"><span>{esc(article.get('category'))}</span><time datetime="{esc(article.get('date'))}">{dt.strftime('%Y-%m-%d %H:%M KST')}</time>{metric}</div>
    <div class="tag-row">{tags}</div>
  </header>
  {notice}
  {quick_block}
  {visual_block}
  {image_block}
  <section id="article-body" class="article-content">
    {article['body_html']}
  </section>
  {related_block}
  <footer class="article-tail">
    {tail_links}
  </footer>
</article>
'''


def search_index_item(article: dict) -> dict[str, Any]:
    metric = metric_for(article["path"])
    return {
        "title": article["title"],
        "description": short_text(article.get("description") or article.get("body_html") or "", 180),
        "path": article["path"],
        "section": article.get("section"),
        "category": article.get("category"),
        "tags": article.get("tags") or [],
        "date": article.get("date"),
        "image_url": article.get("image_url") or "",
        "price_hint": article.get("price_hint") or "",
        "item_count_hint": article.get("item_count_hint") or "",
        "views": metric.get("views") or metric.get("screenPageViews") or metric.get("page_views") or 0,
        "text": short_text(" ".join([
            article.get("title") or "",
            article.get("description") or "",
            " ".join(article.get("tags") or []),
            strip_tags(article.get("body_html") or ""),
        ]), 1200),
    }


def build_search_index(deals: list[dict], radar: list[dict]) -> dict[str, Any]:
    items = [search_index_item(a) for a in deals + radar]
    static_items = [
        {
            "title": p["title"],
            "description": p["description"],
            "path": p["path"],
            "section": p.get("section"),
            "category": "사이트",
            "tags": [],
            "date": TODAY,
            "image_url": "",
            "price_hint": "",
            "item_count_hint": "",
            "views": 0,
            "text": f"{p['title']} {p['description']}",
        }
        for p in STATIC_PAGES
        if p.get("section") != "search"
    ]
    return {
        "version": 1,
        "base_url": BASE,
        "language": "ko-KR",
        "item_count": len(items) + len(static_items),
        "items": items + static_items,
    }


CSS = '''
:root {
  --bg: #fff8f1;
  --ink: #211922;
  --muted: #6b625f;
  --line: #eadfd4;
  --card: #ffffff;
  --blue: #2563eb;
  --green: #0f8b57;
  --orange: #ff5a1f;
  --orange-dark: #d84315;
  --sand: #f4ebe2;
  --cream: #fffaf4;
  --shadow: 0 18px 45px rgba(58, 37, 20, 0.10);
}
*, *::before, *::after { box-sizing: border-box; }
html { scroll-behavior: smooth; width: 100%; overflow-x: clip; }
body {
  width: 100%;
  margin: 0;
  overflow-x: clip;
  font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", "Segoe UI", sans-serif;
  background: radial-gradient(circle at top left, #ffe4d2 0, transparent 30%), radial-gradient(circle at 85% 8%, #fff0b8 0, transparent 25%), var(--bg);
  color: var(--ink);
  line-height: 1.6;
}
a { color: inherit; text-decoration: none; }
a:hover { color: var(--orange-dark); }
img, svg, video { max-width: 100%; height: auto; }
h1, h2, h3, p, li, a { overflow-wrap: anywhere; }
.skip-link {
  position: fixed; left: 16px; top: 12px; z-index: 100;
  transform: translateY(-140%); padding: 10px 14px; border-radius: 12px;
  background: var(--ink); color: #fff; font-weight: 950; box-shadow: var(--shadow);
}
.skip-link:focus { transform: translateY(0); outline: 3px solid rgba(37, 99, 235, .35); }
.site-header {
  position: sticky; top: 0; z-index: 20;
  display: grid; grid-template-columns: minmax(220px, 1fr) auto; align-items: center; gap: 18px;
  padding: 14px clamp(18px, 5vw, 64px);
  background: rgba(255, 250, 244, 0.92);
  backdrop-filter: blur(18px);
  border-bottom: 1px solid rgba(234, 223, 212, 0.85);
}
.brand { display: flex; align-items: center; gap: 12px; min-width: 0; }
.brand-mark {
  display: grid; place-items: center; flex: 0 0 auto;
  width: 44px; height: 44px; border-radius: 15px;
  background: var(--ink); color: #fff; font-weight: 950; letter-spacing: -0.03em;
  box-shadow: 0 8px 22px rgba(33, 25, 34, .12);
}
.brand-copy { display: block; min-width: 0; }
.brand strong, .brand small { display: block; }
.brand strong { font-size: clamp(18px, 2vw, 22px); line-height: 1.12; letter-spacing: -0.045em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.brand small { color: var(--muted); font-size: 12px; font-weight: 750; }
.nav {
  display: flex; align-items: center; gap: 4px; max-width: 100%;
  padding: 5px; border: 1px solid rgba(234, 223, 212, .92); border-radius: 999px;
  background: rgba(255, 255, 255, .72); color: #4b423f; font-weight: 900;
  box-shadow: 0 10px 26px rgba(58, 37, 20, .06);
}
.nav a {
  min-height: 38px; display: inline-flex; align-items: center; justify-content: center;
  padding: 0 13px; border-radius: 999px; color: #594e49; font-size: 14px; line-height: 1;
  white-space: nowrap; transition: background .16s ease, color .16s ease, box-shadow .16s ease, transform .16s ease;
}
.nav a:hover { background: #fff4ea; color: var(--orange-dark); }
.nav a:focus-visible { outline: 3px solid rgba(37, 99, 235, .22); outline-offset: 2px; }
.nav a[aria-current="page"] { background: var(--ink); color: #fff; box-shadow: 0 8px 18px rgba(33, 25, 34, .16); }
.nav a.nav-action { background: #fff0e5; color: var(--orange-dark); }
.nav a.nav-return { background: #eef6ff; color: #1d4ed8; }
.nav a.nav-return:hover { background: #dbeafe; color: #1e40af; }
.nav a.nav-action[aria-current="page"] { background: var(--orange); color: #fff; }
main { width: min(1240px, calc(100% - 32px)); margin: 0 auto; }
.hero { padding: clamp(50px, 9vw, 96px) 0 40px; }
.page-hero { padding: 58px 0 28px; }
.compact { max-width: 860px; }
.eyebrow { color: var(--orange-dark); font-weight: 900; letter-spacing: .12em; text-transform: uppercase; font-size: 14px; }
h1 { font-size: clamp(40px, 7vw, 76px); line-height: 1.04; letter-spacing: -0.055em; margin: 10px 0 18px; }
.compact h1, .article-hero h1 { font-size: clamp(34px, 5.4vw, 60px); }
h2 { letter-spacing: -0.035em; line-height: 1.18; }
.lead { color: #5f5652; font-size: clamp(18px, 2.1vw, 23px); max-width: 850px; }
.hero-actions { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 28px; }
.button, .deal-button {
  display: inline-flex; align-items: center; justify-content: center;
  min-height: 48px; padding: 0 18px; border-radius: 16px;
  border: 1px solid var(--line); background: #fff; font-weight: 950;
}
.button.primary, .deal-button.primary { background: var(--orange); color: #fff; border-color: var(--orange); box-shadow: 0 10px 22px rgba(255, 90, 31, .22); }
.deal-button.ghost { background: #fff7ed; color: var(--orange-dark); border-color: #ffd2b8; }
.grid { display: grid; gap: 18px; margin: 28px 0; }
.grid.three { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.grid.two { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.card, .panel, .notice, .list-card {
  background: rgba(255, 255, 255, 0.90);
  border: 1px solid rgba(234, 223, 212, .95);
  border-radius: 28px;
  padding: 26px;
  box-shadow: 0 10px 30px rgba(58, 37, 20, .06);
}
.card { min-height: 220px; display: flex; flex-direction: column; justify-content: space-between; }
.tag { display: inline-flex; align-self: flex-start; border-radius: 999px; padding: 5px 11px; background: #fff0e5; color: var(--orange-dark); font-size: 12px; font-weight: 950; }
.tag.pale { background: #f4ebe2; color: #6b625f; }
.tag-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
.card p, .list-card p, .panel p, .notice p { color: #5f5652; }
.card > a:not(.button) { display: inline-flex; align-items: center; min-height: 44px; font-weight: 950; color: var(--orange-dark); }
.list-card h2, .list-card h2 a, .deal-card h2, .article-hero h1 { max-width: 100%; overflow-wrap: anywhere; word-break: normal; }
.list-card h2 a, .deal-card h2 a, .quick-links a, .related-radar a { display: inline-flex; align-items: center; min-height: 44px; }
.list-card > img { width: 100%; max-height: 260px; object-fit: contain; background: #fffaf4; border-radius: 18px; margin-bottom: 14px; }
.accent-blue { border-top: 5px solid var(--blue); }
.accent-orange, .accent-amber { border-top: 5px solid var(--orange); }
.accent-green { border-top: 5px solid var(--green); }
.panel, .notice { margin: 28px 0; }
.panel.soft { background: #fffaf4; }
.notice.affiliate { border-color: #ffd2b8; background: linear-gradient(135deg, #fff7ed, #fff); }
.compact-notice { padding: 14px 18px; }
.compact-notice p { margin: 4px 0 0; font-size: 15px; line-height: 1.65; }
.checklist { padding-left: 0; list-style: none; }
.checklist li { position: relative; padding-left: 28px; margin: 10px 0; }
.checklist li::before { content: "✓"; position: absolute; left: 0; color: var(--green); font-weight: 900; }
.status-strip, .shop-summary {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;
  margin: 24px 0 34px;
}
.status-strip div, .shop-summary div { background: var(--ink); color: #fff; border-radius: 22px; padding: 18px; }
.status-strip strong, .status-strip span, .shop-summary strong, .shop-summary span { display: block; }
.status-strip span, .shop-summary span { color: #ecd9cd; }
.article-list { display: grid; gap: 16px; margin: 24px 0 56px; }
.mixed-list { grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
.radar-card { padding: 0; overflow: hidden; display: grid; grid-template-columns: minmax(220px, 0.42fr) minmax(0, 1fr); align-items: stretch; }
.radar-card, .radar-card * { overflow-wrap: break-word; word-break: keep-all; }
.radar-card-visual { position: relative; display: block; min-height: 250px; overflow: hidden; isolation: isolate; padding: 22px; color: #fff; background: linear-gradient(135deg, #211922, #573322 58%, #ff5a1f); }
.radar-card.theme-commute .radar-card-visual { background: radial-gradient(circle at 18% 18%, rgba(147,197,253,.35), transparent 24%), linear-gradient(135deg, #0f172a, #1d4ed8 58%, #38bdf8); }
.radar-card.theme-night .radar-card-visual { background: radial-gradient(circle at 74% 18%, rgba(255,214,165,.28), transparent 25%), linear-gradient(135deg, #160f1d, #3b1f2b 55%, #ff6b2b); }
.radar-card.theme-fee .radar-card-visual { background: radial-gradient(circle at 18% 22%, rgba(255,255,255,.24), transparent 23%), linear-gradient(135deg, #2b2118, #7a4f12 56%, #ffb020); }
.radar-card.theme-pressure .radar-card-visual { background: radial-gradient(circle at 75% 18%, rgba(186,230,253,.24), transparent 24%), linear-gradient(135deg, #172033, #244973 58%, #2563eb); }
.radar-card.theme-filter .radar-card-visual { background: radial-gradient(circle at 22% 18%, rgba(187,247,208,.22), transparent 23%), linear-gradient(135deg, #15251d, #22543d 55%, #0f8b57); }
.radar-card.theme-cafe .radar-card-visual { background: radial-gradient(circle at 20% 20%, rgba(254,240,138,.23), transparent 23%), linear-gradient(135deg, #17152b, #3b2f74 55%, #0f8b57); }
.radar-card-visual::before { content: ""; position: absolute; inset: 16px; z-index: -2; border-radius: 28px; border: 1px solid rgba(255,255,255,.18); background-image: linear-gradient(rgba(255,255,255,.07) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.07) 1px, transparent 1px); background-size: 32px 32px; pointer-events: none; }
.radar-card-visual::after { content: ""; position: absolute; right: -54px; bottom: -70px; z-index: -1; width: 230px; height: 230px; border-radius: 50%; background: radial-gradient(circle, rgba(255,255,255,.24), rgba(255,255,255,.05) 48%, transparent 68%); pointer-events: none; }
.radar-thumb-label { position: relative; z-index: 3; display: inline-flex; padding: 6px 10px; border-radius: 999px; background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.24); font-size: 11px; font-weight: 950; letter-spacing: .08em; }
.radar-thumb-title { position: relative; z-index: 3; display: block; max-width: 205px; margin-top: 14px; font-size: clamp(29px, 4vw, 44px); line-height: .98; letter-spacing: -.06em; text-shadow: 0 14px 34px rgba(0,0,0,.28); }
.radar-thumb-subline { position: relative; z-index: 3; display: block; max-width: 220px; margin-top: 9px; color: rgba(255,255,255,.84); font-size: 13px; line-height: 1.35; font-weight: 850; }
.radar-thumb-art { position: absolute; z-index: 2; right: 16px; bottom: 18px; width: min(58%, 220px); height: 58%; min-height: 132px; pointer-events: none; }
.scene-art, .scene-art > * { position: absolute; display: block; box-sizing: border-box; }
.scene-art { inset: 0; }
.radar-card-badge { position: absolute; z-index: 4; left: 18px; bottom: 18px; display: inline-flex; padding: 8px 12px; border-radius: 999px; background: rgba(255,255,255,.17); border: 1px solid rgba(255,255,255,.28); backdrop-filter: blur(10px); color: #fff; font-size: 12px; font-weight: 950; }
.time-card { left: 8px; top: 4px; padding: 10px 12px; border-radius: 18px; background: #fff; color: #0f172a; font-weight: 950; font-size: 26px; box-shadow: 0 18px 34px rgba(0,0,0,.25); }
.rail-line { left: 12px; right: 10px; top: 78px; height: 7px; border-radius: 999px; background: linear-gradient(90deg, #fff, #93c5fd); box-shadow: 0 0 20px rgba(147,197,253,.7); }
.station { top: 62px; min-width: 48px; padding: 7px 8px; border-radius: 999px; background: rgba(15,23,42,.78); border: 1px solid rgba(255,255,255,.28); color: #fff; font-size: 11px; text-align: center; font-weight: 950; }
.station-a { left: 0; } .station-b { left: 47%; transform: translateX(-50%); } .station-c { right: 0; }
.rain-mark { right: 18px; top: 12px; width: 46px; height: 72px; transform: rotate(18deg); background: repeating-linear-gradient(90deg, rgba(255,255,255,.82) 0 3px, transparent 3px 12px); opacity: .55; }
.lamp-post { left: 22px; top: 18px; width: 10px; height: 92px; border-radius: 999px; background: rgba(255,255,255,.8); }
.lamp-post::before { content: ""; position: absolute; left: -16px; top: -8px; width: 46px; height: 16px; border-radius: 999px; background: #ffe2a8; box-shadow: 0 0 24px rgba(255,226,168,.9); }
.lamp-light { left: -18px; top: 18px; width: 96px; height: 104px; transform: skewX(-12deg); background: linear-gradient(120deg, rgba(255,226,168,.38), transparent 72%); clip-path: polygon(38% 0, 72% 0, 100% 100%, 0 100%); }
.alley-road { left: 42px; right: 8px; bottom: 2px; height: 56px; transform: skewX(-20deg); border-radius: 18px; background: linear-gradient(90deg, rgba(20,16,24,.92), rgba(255,255,255,.14)); }
.window-stack { right: 12px; top: 15px; width: 54px; height: 72px; border-radius: 16px; background: repeating-linear-gradient(180deg, rgba(255,238,190,.95) 0 9px, transparent 9px 20px), rgba(255,255,255,.13); border: 1px solid rgba(255,255,255,.2); }
.noise-wave { right: 70px; top: 42px; width: 42px; height: 42px; border: 2px solid rgba(255,255,255,.7); border-left-color: transparent; border-bottom-color: transparent; border-radius: 50%; transform: rotate(45deg); } .wave-two { right: 60px; top: 32px; width: 66px; height: 66px; opacity: .45; }
.street-chip, .cost-chip { padding: 6px 9px; border-radius: 999px; background: rgba(255,255,255,.9); color: #211922; font-size: 11px; font-weight: 950; box-shadow: 0 10px 20px rgba(0,0,0,.18); }
.street-chip.chip-a { left: 4px; bottom: 12px; } .street-chip.chip-b { left: 68px; bottom: 42px; } .street-chip.chip-c { right: 2px; bottom: 14px; }
.receipt { left: 16px; top: 4px; width: 126px; min-height: 132px; padding: 14px 12px 16px; border-radius: 18px 18px 8px 8px; background: #fffaf4; color: #2b2118; box-shadow: 0 18px 32px rgba(0,0,0,.22); }
.receipt::after { content: ""; position: absolute; left: 0; right: 0; bottom: -9px; height: 12px; background: repeating-linear-gradient(90deg, #fffaf4 0 12px, transparent 12px 24px); }
.receipt b, .receipt i { display: block; font-style: normal; } .receipt b { margin-bottom: 10px; font-size: 16px; } .receipt i { padding: 5px 0; border-top: 1px dashed rgba(43,33,24,.22); color: #705036; font-size: 12px; font-weight: 900; }
.stamp { right: 8px; bottom: 28px; width: 76px; height: 76px; display: grid; place-items: center; border: 4px solid rgba(255,255,255,.9); border-radius: 50%; color: #fff; font-size: 17px; font-weight: 950; transform: rotate(-13deg); }
.coin { right: 26px; top: 20px; width: 46px; height: 46px; border-radius: 50%; background: #ffd166; box-shadow: inset 0 0 0 7px rgba(255,255,255,.25), 0 12px 22px rgba(0,0,0,.22); } .coin-b { right: 2px; top: 52px; transform: scale(.72); }
.calc { left: 16px; top: 8px; width: 112px; height: 128px; padding: 13px; border-radius: 22px; background: #f8fbff; box-shadow: 0 18px 34px rgba(0,0,0,.22); display: grid; grid-template-columns: repeat(3, 1fr); gap: 7px; }
.calc b { grid-column: 1 / -1; display: block; padding: 7px 8px; border-radius: 10px; background: #172033; color: #fff; font-size: 13px; } .calc i { border-radius: 9px; background: #c7d2fe; }
.loss-line { right: 2px; top: 8px; padding: 10px 12px; border-radius: 18px; background: #fff; color: #1d4ed8; font-size: 24px; font-weight: 950; box-shadow: 0 16px 30px rgba(0,0,0,.2); }
.cost-chip.chip-a { right: 66px; bottom: 54px; } .cost-chip.chip-b { right: 10px; bottom: 36px; } .cost-chip.chip-c { right: 46px; bottom: 2px; }
.funnel { left: 18px; top: 5px; width: 112px; height: 122px; background: linear-gradient(180deg, rgba(255,255,255,.9), rgba(187,247,208,.9)); clip-path: polygon(0 0, 100% 0, 66% 52%, 66% 100%, 34% 100%, 34% 52%); filter: drop-shadow(0 18px 26px rgba(0,0,0,.22)); }
.checklist { right: 4px; top: 12px; width: 94px; padding: 10px; border-radius: 18px; background: rgba(255,255,255,.92); color: #15251d; box-shadow: 0 16px 28px rgba(0,0,0,.18); } .checklist i { display: block; padding: 5px 0 5px 18px; position: relative; font-style: normal; font-size: 12px; font-weight: 950; } .checklist i::before { content: ""; position: absolute; left: 0; top: 10px; width: 9px; height: 5px; border-left: 2px solid #0f8b57; border-bottom: 2px solid #0f8b57; transform: rotate(-45deg); }
.reject-card, .keep-card { bottom: 6px; padding: 8px 10px; border-radius: 14px; font-size: 13px; font-weight: 950; box-shadow: 0 12px 22px rgba(0,0,0,.2); } .reject-card { left: 4px; background: #2f2724; color: #fff; transform: rotate(-8deg); } .keep-card { right: 12px; background: #fff; color: #0f8b57; transform: rotate(7deg); }
.awning { left: 14px; top: 12px; width: 132px; height: 36px; border-radius: 16px 16px 6px 6px; background: repeating-linear-gradient(90deg, #fff 0 18px, #ff6b2b 18px 36px); box-shadow: 0 14px 28px rgba(0,0,0,.2); }
.storefront { left: 22px; top: 46px; width: 116px; height: 82px; border-radius: 12px 12px 20px 20px; background: rgba(255,255,255,.92); color: #17152b; display: grid; place-items: center; font-size: 17px; box-shadow: 0 16px 28px rgba(0,0,0,.18); }
.cup { right: 10px; bottom: 6px; width: 64px; height: 68px; border-radius: 12px 12px 26px 26px; background: #fffaf4; box-shadow: inset -10px 0 rgba(15,139,87,.16), 0 16px 28px rgba(0,0,0,.2); } .cup::after { content: ""; position: absolute; right: -15px; top: 18px; width: 24px; height: 24px; border: 7px solid #fffaf4; border-left: 0; border-radius: 0 18px 18px 0; }
.footfall { width: 12px; height: 12px; border-radius: 50%; background: #bbf7d0; box-shadow: 0 0 0 5px rgba(187,247,208,.18); } .dot-a { left: 0; bottom: 26px; } .dot-b { left: 26px; bottom: 2px; } .dot-c { left: 58px; bottom: 20px; }
.rival-sign { right: 4px; top: 26px; padding: 6px 8px; border-radius: 999px; background: #17152b; color: #fff; font-size: 11px; font-weight: 950; border: 1px solid rgba(255,255,255,.28); }
.radar-card-body { padding: 24px; display: flex; flex-direction: column; gap: 8px; }
.radar-card h2 { margin: 2px 0 0; font-size: clamp(22px, 3vw, 31px); }
.radar-card p { margin: 0; }
.radar-card-hook { padding: 9px 11px; border-radius: 16px; background: #fff7ed; border: 1px solid #ffd2b8; color: #9a3412; font-size: 14px; line-height: 1.45; font-weight: 950; }
.radar-card-actions { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 6px; }
.radar-card-actions span { display: inline-flex; align-items: center; min-height: 30px; padding: 0 10px; border-radius: 999px; background: #fff7ed; border: 1px solid #ffd2b8; color: var(--orange-dark); font-size: 12px; font-weight: 950; }
.radar-card .text-link { width: fit-content; min-height: 40px; margin-top: auto; padding: 0 13px; border-radius: 14px; background: var(--ink); color: #fff; text-decoration: none; box-shadow: 0 10px 22px rgba(33,25,34,.13); }
.radar-card .text-link:hover { background: var(--orange); color: #fff; }
.radar-latest-grid { grid-template-columns: repeat(auto-fit, minmax(min(100%, 320px), 1fr)); align-items: stretch; }
.radar-latest-grid .radar-card { display: flex; flex-direction: column; min-height: 100%; }
.radar-latest-grid .radar-card-visual { min-height: 210px; width: 100%; flex: 0 0 auto; }
.radar-latest-grid .radar-card-body { min-width: 0; padding: 22px; flex: 1; }
.radar-latest-grid .card-meta { gap: 8px; }
.radar-latest-grid .radar-card h2 { font-size: clamp(20px, 2vw, 25px); line-height: 1.18; letter-spacing: -.045em; }
.radar-latest-grid .radar-card p { font-size: 15px; line-height: 1.65; }
.radar-latest-grid .radar-card-actions { display: none; }
.radar-latest-grid .radar-card .text-link { margin-top: 12px; }
.section-title { grid-column: 1 / -1; }
.section-title h2 { margin-bottom: 4px; }
.section-title p { margin-top: 0; color: var(--muted); }
.list-card h2 { margin-bottom: 8px; }
.card-meta, .article-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; color: var(--muted); font-size: 14px; font-weight: 800; }
.traffic-badge { display: inline-flex; align-items: center; gap: 4px; padding: 4px 9px; border-radius: 999px; background: #eef6ff; color: #1d4ed8; font-weight: 950; font-size: 12px; white-space: nowrap; }
.text-link { color: var(--orange-dark); font-weight: 950; display: inline-flex; align-items: center; min-height: 44px; }
.deals-site { background: #f7f8fb; }
.deals-site .site-header { background: rgba(255,255,255,.96); }
.deals-site main { width: min(1180px, calc(100% - 32px)); }
.deal-landing-hero {
  display: grid; grid-template-columns: minmax(0, 1.28fr) minmax(280px, .72fr); gap: clamp(18px, 4vw, 42px);
  align-items: stretch; padding: clamp(34px, 6vw, 64px) 0 18px;
}
.deal-hero-copy, .deal-hero-panel, .affiliate-disclosure, .deal-quick-box {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 24px; box-shadow: 0 12px 30px rgba(15, 23, 42, .06);
}
.deal-hero-copy { padding: clamp(24px, 4vw, 42px); }
.deal-hero-copy h1 { max-width: 880px; font-size: clamp(36px, 5.6vw, 66px); }
.deal-hero-panel { padding: 24px; align-self: end; }
.deal-hero-panel > strong { display: block; font-size: 22px; letter-spacing: -.03em; margin-bottom: 12px; }
.deal-hero-panel .microcopy { margin: 14px 0 0; color: #5f5652; font-size: 14px; line-height: 1.6; font-weight: 850; }
.playful-badges { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
.playful-badges span { display: inline-flex; align-items: center; min-height: 34px; padding: 0 12px; border-radius: 999px; background: #eef6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-size: 13px; font-weight: 950; }
.site-bridge-strip { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 18px; margin: 8px 0 24px; padding: 20px; background: #fff; border: 1px solid #dbeafe; border-radius: 24px; box-shadow: 0 12px 30px rgba(15, 23, 42, .06); }
.site-bridge-strip h2 { margin: 8px 0 6px; font-size: clamp(24px, 3vw, 34px); }
.site-bridge-strip p { margin: 0; color: #5f5652; }
.bridge-actions { display: flex; flex-wrap: wrap; gap: 10px; justify-content: flex-end; }
.affiliate-disclosure { margin: 22px 0 0; padding: 14px 16px; background: #fff7ed; border-color: #fed7aa; }
.affiliate-disclosure strong { color: var(--orange-dark); }
.affiliate-disclosure p { margin: 4px 0 0; color: #5f5652; font-size: 14px; line-height: 1.6; }
.above-fold-section { margin-top: 18px; }
.deal-grid.best-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.deal-card.ranked { border-color: #fed7aa; }
.deal-rank { position: absolute; right: 12px; top: 12px; padding: 7px 10px; border-radius: 999px; background: #111827; color: #fff; font-size: 12px; font-weight: 950; }
.deal-text-badge { position: relative; min-height: 150px; display: flex; align-items: center; justify-content: center; padding: 18px; background: linear-gradient(135deg, #fff7ed, #ffffff); border-bottom: 1px solid var(--line); color: var(--orange-dark); font-weight: 950; text-align: center; }
.deal-price { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.deal-price-link { display: inline-flex; align-items: center; min-height: 34px; padding: 0 10px; border-radius: 999px; background: #fff7ed; border: 1px solid #fed7aa; color: var(--orange-dark); font-size: 12px; font-weight: 950; text-decoration: none; }
.lower-search { margin-top: 18px; }
.decision-strip .card { background: #fff; }
.deal-quick-box { margin: 20px 0; padding: clamp(20px, 3.5vw, 30px); display: grid; gap: 18px; }
.deal-quick-box h2 { margin: 8px 0 8px; font-size: clamp(26px, 3.4vw, 36px); }
.deal-quick-box p { margin: 0; color: #4b5563; }
.quick-note { margin-top: 8px !important; color: #6b7280 !important; font-size: 14px; font-weight: 850; }
.quick-facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.quick-facts div { padding: 14px; border-radius: 18px; background: #f9fafb; border: 1px solid #e5e7eb; }
.quick-facts strong, .quick-facts span { display: block; }
.quick-facts strong { color: #111827; font-size: 15px; }
.quick-facts span { color: #6b7280; font-size: 12px; font-weight: 900; margin-top: 3px; }
.quick-products { border-top: 1px solid #e5e7eb; padding-top: 16px; }
.quick-products h3 { margin: 0 0 8px; font-size: 19px; }
.quick-products ol { margin: 0; padding-left: 1.25em; columns: 2; }
.quick-products li { margin: 5px 0; font-weight: 850; }
.quick-actions { margin-top: 0; }
.deal-article .article-hero { padding-bottom: 8px; }
.deal-article .article-product-hero { margin-top: 16px; }
.shop-hero {
  display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(320px, .95fr); gap: clamp(20px, 5vw, 56px);
  align-items: center; padding: clamp(34px, 6vw, 66px) 0 22px;
}
.shop-hero-copy h1 { max-width: 760px; }
.category-strip { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 24px; }
.category-chip { display: inline-flex; padding: 8px 12px; border-radius: 999px; background: #fff; border: 1px solid var(--line); color: #4b423f; font-weight: 900; font-size: 13px; }
.hero-pin-stack { position: relative; min-height: 380px; }
.hero-pin { position: absolute; display: block; width: 58%; overflow: hidden; border-radius: 30px; background: #fff; box-shadow: var(--shadow); border: 8px solid #fff; }
.hero-pin img { display: block; width: 100%; aspect-ratio: 1 / 1; object-fit: cover; background: #fff; }
.hero-pin span { position: absolute; left: 12px; bottom: 12px; padding: 7px 10px; border-radius: 999px; background: rgba(33, 25, 34, .78); color: #fff; font-size: 12px; font-weight: 950; }
.hero-pin.pin-1 { right: 18%; top: 0; z-index: 3; }
.hero-pin.pin-2 { left: 0; bottom: 0; width: 48%; z-index: 2; transform: rotate(-5deg); }
.hero-pin.pin-3 { right: 0; bottom: 24px; width: 46%; z-index: 1; transform: rotate(5deg); }
.landing-section { margin: 34px 0 58px; scroll-margin-top: 96px; }
.intent-grid, .category-hubs { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }
.intent-card, .category-hub { background: #fff; border: 1px solid var(--line); border-radius: 24px; padding: 20px; box-shadow: 0 10px 30px rgba(58, 37, 20, .065); }
.intent-card h2 { margin: 8px 0 8px; font-size: clamp(21px, 2.2vw, 26px); }
.intent-card p { color: #5f5652; margin: 0 0 14px; line-height: 1.65; }
.search-chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0 14px; }
.search-chip { display: inline-flex; align-items: center; min-height: 34px; padding: 0 11px; border-radius: 999px; background: #fff7ed; border: 1px solid #ffd2b8; color: var(--orange-dark); font-size: 13px; font-weight: 950; }
.mini-link-list { display: grid; gap: 8px; margin: 12px 0 0; padding-left: 18px; }
.mini-link-list a { color: #2f2724; font-weight: 900; }
.category-hub > div { display: flex; justify-content: space-between; gap: 10px; align-items: center; margin-bottom: 10px; }
.category-hub strong { color: var(--muted); font-size: 13px; white-space: nowrap; }
.popular-panel, .decision-panel { margin: 0; }
.popular-deal-list { list-style: none; padding: 0; margin: 10px 0 0; display: grid; gap: 10px; }
.popular-deal-list li { display: grid; grid-template-columns: 34px 1fr; gap: 2px 10px; align-items: start; padding: 10px 0; border-bottom: 1px solid var(--line); }
.popular-deal-list .rank { grid-row: 1 / span 2; width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center; border-radius: 999px; background: var(--ink); color: #fff; font-weight: 950; font-size: 13px; }
.popular-deal-list a { color: #2f2724; font-weight: 950; }
.popular-deal-list small { color: var(--muted); font-weight: 800; }
.deal-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 18px; margin: 22px 0 68px; align-items: stretch; }
.deal-card { background: #fff; border: 1px solid var(--line); border-radius: 28px; overflow: hidden; box-shadow: 0 12px 35px rgba(58, 37, 20, .08); display: flex; flex-direction: column; min-height: 100%; transition: transform .18s ease, box-shadow .18s ease; }
.deal-card:hover { transform: translateY(-4px); box-shadow: 0 20px 48px rgba(58, 37, 20, .14); }
.deal-thumb { position: relative; display: block; background: #fffaf4; }
.deal-thumb img { display: block; width: 100%; aspect-ratio: 1 / 1; object-fit: cover; }
.deal-count { position: absolute; left: 12px; top: 12px; padding: 7px 10px; border-radius: 999px; background: rgba(255, 90, 31, .94); color: #fff; font-size: 12px; font-weight: 950; }
.deal-body { padding: 18px; display: flex; flex-direction: column; gap: 10px; flex: 1; }
.deal-meta { display: flex; justify-content: space-between; gap: 10px; color: var(--muted); font-size: 12px; font-weight: 900; }
.deal-card h2 { margin: 0; font-size: clamp(19px, 2vw, 23px); letter-spacing: -0.045em; }
.deal-card p { margin: 0; color: #6b625f; font-size: 14px; }
.deal-price { margin-top: auto; color: var(--orange-dark); font-weight: 950; font-size: 15px; }
.deal-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }
.deal-actions .deal-button { min-height: 46px; padding: 0 13px; font-size: 13px; flex: 1 1 auto; }
.breadcrumb { display: flex; gap: 8px; color: var(--muted); font-size: 14px; margin-top: 32px; flex-wrap: wrap; }
.breadcrumb a { min-height: 44px; min-width: 44px; display: inline-flex; align-items: center; justify-content: center; padding: 0 6px; }
.article-page { max-width: 940px; margin: 0 auto; }
.article-hero { padding: 44px 0 18px; }
.radar-article { max-width: 1120px; }
.radar-article .breadcrumb, .radar-article .article-hero, .radar-article .article-content, .radar-article .related-radar, .radar-article .article-tail { max-width: 940px; margin-left: auto; margin-right: auto; }
.radar-experience-grid { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(280px, .9fr); gap: 18px; margin: 20px 0 26px; align-items: stretch; }
.radar-map-card, .brief-card, .radar-toc-card { background: rgba(255,255,255,.94); border: 1px solid rgba(234,223,212,.95); border-radius: 30px; box-shadow: 0 16px 44px rgba(58,37,20,.09); }
.radar-map-card { position: relative; overflow: hidden; padding: 24px; min-height: 430px; background: linear-gradient(145deg, #fffaf4 0%, #ffffff 52%, #fff1e7 100%); }
.radar-map-card h2 { margin: 6px 0 8px; font-size: clamp(27px, 3.6vw, 42px); }
.radar-map-card p:not(.eyebrow) { max-width: 560px; color: #5f5652; margin-bottom: 20px; }
.radar-map { position: relative; min-height: 245px; margin-top: 12px; border-radius: 28px; overflow: hidden; background: radial-gradient(circle at 18% 24%, rgba(255,90,31,.16), transparent 20%), radial-gradient(circle at 78% 70%, rgba(37,99,235,.14), transparent 22%), #241b20; box-shadow: inset 0 0 0 1px rgba(255,255,255,.08); }
.radar-map::before { content: ""; position: absolute; inset: 0; z-index: 0; background-image: linear-gradient(rgba(255,255,255,.08) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.08) 1px, transparent 1px); background-size: 36px 36px; mask-image: radial-gradient(circle at center, #000 40%, transparent 88%); }
.map-route { position: absolute; inset: 0; z-index: 1; width: 100%; height: 100%; overflow: visible; pointer-events: none; }
.map-route-guide, .map-route-path { fill: none; vector-effect: non-scaling-stroke; stroke-linecap: round; stroke-linejoin: round; }
.map-route-mobile { display: none; }
.map-route-guide { stroke: rgba(255,255,255,.34); stroke-width: 12; }
.map-route-path { stroke: #ff5a1f; stroke-width: 4.5; filter: drop-shadow(0 0 10px rgba(255,90,31,.52)); }
.map-route-arrow { fill: #ff5a1f; }
.map-label { position: absolute; left: 18px; top: 16px; z-index: 3; padding: 8px 12px; border-radius: 999px; background: rgba(255,255,255,.17); color: #fff; border: 1px solid rgba(255,255,255,.28); font-size: 12px; font-weight: 950; backdrop-filter: blur(8px); box-shadow: 0 10px 24px rgba(0,0,0,.16); }
.map-node { position: absolute; z-index: 4; display: grid; gap: 6px; justify-items: center; color: #fff; font-size: 14px; font-weight: 950; transform: translate(-50%, -21px); }
.map-node b { display: grid; place-items: center; width: 42px; height: 42px; border-radius: 999px; background: #fff; color: #211922; border: 3px solid #ffefe8; box-shadow: 0 12px 26px rgba(0,0,0,.30), 0 0 0 5px rgba(255,90,31,.20); }
.map-node em { font-style: normal; line-height: 1; letter-spacing: 0; padding: 6px 12px; border-radius: 999px; background: rgba(21,17,22,.86); border: 1px solid rgba(255,255,255,.28); backdrop-filter: blur(8px); box-shadow: 0 8px 18px rgba(0,0,0,.22); text-shadow: 0 1px 0 rgba(0,0,0,.35); }
.node-1 { left: 13%; top: 66%; } .node-2 { left: 31%; top: 39%; } .node-3 { left: 50%; top: 57%; } .node-4 { left: 74%; top: 36%; } .node-5 { left: 88%; top: 61%; }
.radar-brief-stack { display: grid; gap: 12px; }
.brief-card { padding: 18px 20px; }
.brief-card span { display: inline-flex; margin-bottom: 8px; padding: 4px 9px; border-radius: 999px; background: #f4ebe2; color: #6b625f; font-size: 11px; font-weight: 950; letter-spacing: .08em; }
.brief-card.hot { background: linear-gradient(135deg, #211922, #4b2a1d 60%, #ff5a1f); color: #fff; border-color: rgba(255,255,255,.18); }
.brief-card.hot p { color: #ffe9df; }
.brief-card strong { display: block; font-size: 19px; letter-spacing: -.025em; }
.brief-card p { margin: 6px 0 0; color: #5f5652; line-height: 1.6; overflow-wrap: break-word; word-break: keep-all; }
.radar-toc-card { grid-column: 1 / -1; padding: 18px 20px; }
.radar-toc-card strong { display: block; margin-bottom: 10px; font-size: 18px; }
.radar-toc-card ol { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px; }
.radar-toc-card li { display: grid; grid-template-columns: 38px 1fr; align-items: center; gap: 8px; padding: 10px; border-radius: 16px; background: #fffaf4; color: #443a36; font-weight: 850; }
.radar-toc-card li span { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 999px; background: var(--ink); color: #fff; font-size: 12px; font-weight: 950; }
.article-product-hero { display: grid; grid-template-columns: minmax(220px, 330px) 1fr; gap: 24px; align-items: center; background: #fff; border: 1px solid var(--line); border-radius: 30px; padding: clamp(16px, 3vw, 28px); box-shadow: var(--shadow); margin: 22px 0; }
.article-product-hero img { width: 100%; aspect-ratio: 1 / 1; object-fit: cover; border-radius: 24px; background: #fffaf4; }
.article-product-hero h2 { margin: 12px 0 8px; }
.article-product-hero p { color: #5f5652; }
.article-content {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(234, 223, 212, .95);
  border-radius: 28px;
  padding: clamp(22px, 4vw, 42px);
  box-shadow: 0 10px 32px rgba(58, 37, 20, .07);
  overflow-wrap: break-word;
  word-break: keep-all;
  font-size: clamp(16px, 2.4vw, 18px);
  line-height: 1.75;
}
.article-content h2 { margin-top: 34px; font-size: clamp(24px, 3.4vw, 32px); }
.article-content h3 { margin-top: 26px; font-size: 22px; }
.article-content p { color: #3f3733; margin: 0 0 18px; overflow-wrap: break-word; word-break: keep-all; }
.radar-article .article-content { counter-reset: section; }
.radar-article .article-content > section > h2, .radar-article .article-content > h2 { display: grid; grid-template-columns: 42px 1fr; gap: 12px; align-items: start; }
.radar-article .article-content > section > h2::before, .radar-article .article-content > h2::before { counter-increment: section; content: counter(section); display: grid; place-items: center; width: 38px; height: 38px; border-radius: 999px; background: var(--ink); color: #fff; font-size: 14px; font-weight: 950; box-shadow: 0 10px 22px rgba(33,25,34,.14); }
.article-content figure { margin: 28px 0; padding: clamp(16px, 3vw, 24px); border-radius: 30px; border: 1px solid rgba(234,223,212,.96); background: linear-gradient(135deg, #fffaf4, #ffffff 52%, #fff0e5); box-shadow: 0 14px 38px rgba(58,37,20,.075); }
.article-content figcaption { margin-top: 12px; color: #6b625f; font-size: 14px; font-weight: 850; text-align: center; }
.article-content .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.article-content .cards .card { position: relative; min-height: auto; padding: 18px; border-radius: 22px; overflow: hidden; background: #fff; box-shadow: 0 8px 24px rgba(58,37,20,.075); border: 1px solid rgba(234,223,212,.95); }
.article-content .cards .card::before { content: ""; display: block; width: 34px; height: 5px; border-radius: 999px; margin-bottom: 12px; background: linear-gradient(90deg, var(--orange), #ffb020); }
.article-content .cards .card strong { font-size: 16px; letter-spacing: -.02em; }
.article-content .notice { background: #fffaf4; border-color: #ffd2b8; }
.article-content .callout { margin: 30px 0; padding: clamp(20px, 3vw, 28px); border-radius: 28px; background: linear-gradient(135deg, #211922, #4b2a1d 58%, #ff5a1f); color: #fff; box-shadow: 0 18px 44px rgba(58,37,20,.18); }
.article-content .callout strong { display: block; font-size: clamp(20px, 2.7vw, 28px); letter-spacing: -.03em; margin-bottom: 8px; }
.article-content .callout p { color: #ffe9df; margin-bottom: 0; }
.article-content .bar { position: relative; height: 22px; border-radius: 999px; margin: 8px 0 18px; background: linear-gradient(90deg, #0f8b57 0 34%, #ffb020 34% 68%, #ff5a1f 68% 100%); box-shadow: inset 0 0 0 1px rgba(255,255,255,.65), 0 10px 24px rgba(58,37,20,.10); }
.article-content .bar::before, .article-content .bar::after { position: absolute; top: calc(100% + 6px); color: var(--muted); font-size: 12px; font-weight: 900; }
.article-content .bar::before { content: "부담 낮음"; left: 0; }
.article-content .bar::after { content: "재검토"; right: 0; }
.article-content p[style*="font-size"] { font-size: inherit !important; line-height: inherit !important; }
.article-content ul, .article-content ol { padding-left: 1.25em; }
.article-content li { margin: 9px 0; }
.article-content li > a { display: inline-flex; align-items: center; min-height: 44px; }
.article-content img { display: block; max-width: 100%; max-height: 420px; width: auto; height: auto; margin: 14px auto; border-radius: 18px; box-shadow: 0 8px 24px rgba(58, 37, 20, .08); object-fit: contain; background: #fffaf4; }
.article-content a {
  color: var(--orange-dark);
  font-weight: 950;
  text-decoration: underline;
  text-underline-offset: 3px;
}
.article-content a[href*="coupang.com"]:not(:has(img)), .article-content p > a:only-child:not(:has(img)) {
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  min-height: 48px !important;
  width: 100% !important;
  margin: 8px 0 14px !important;
  padding: 12px 14px !important;
  border-radius: 16px !important;
  background: var(--orange) !important;
  color: #fff !important;
  text-decoration: none !important;
  font-size: 16px !important;
  line-height: 1.35;
  box-shadow: 0 10px 22px rgba(255, 90, 31, .18);
}
.article-content a[href*="coupang.com"]:has(img) {
  display: block;
  width: fit-content;
  max-width: 100%;
  margin: 14px auto;
  padding: 0;
  background: transparent;
  box-shadow: none;
  border-radius: 18px;
}
.table-scroll { width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 22px 0; border: 0; border-radius: 24px; background: #fff; box-shadow: 0 12px 32px rgba(58,37,20,.075); }
.table-scroll::before { content: "핵심 비교표 · 좌우로 밀어 보기 →"; display: block; padding: 12px 14px 0; color: var(--muted); font-size: 13px; font-weight: 950; }
.table-scroll table { min-width: 680px; width: 100%; border-collapse: collapse; overflow: hidden; }
.article-content table { width: 100%; border-collapse: collapse; }
.article-content th, .article-content td { border: 1px solid #f0e4da; padding: 12px; vertical-align: top; }
.article-content th { background: #211922; color: #fff; font-size: 14px; letter-spacing: -.01em; }
.article-content tr:nth-child(even) td { background: #fffaf4; }
.article-content td:first-child { font-weight: 900; color: #2f2724; }
.related-radar { margin: 28px 0; padding: 24px; border: 1px solid var(--line); border-radius: 24px; background: #fffaf4; }
.related-radar h2 { margin-top: 0; }
.related-radar ul { margin-bottom: 0; }
.deal-radar-return { margin: 0 0 22px; padding: 18px; border-radius: 20px; background: linear-gradient(135deg, #eff6ff, #fff 70%); border: 1px solid #bfdbfe; }
.deal-radar-return h2 { margin: 8px 0 6px; font-size: clamp(22px, 3vw, 30px); }
.deal-radar-return p { margin: 0 0 12px; color: #5f5652; }
.site-search label { display: block; font-weight: 950; margin-bottom: 8px; }
.search-row { display: flex; gap: 10px; align-items: stretch; }
.search-row input { flex: 1; min-width: 0; min-height: 48px; border: 1px solid var(--line); border-radius: 16px; padding: 0 14px; font: inherit; background: #fff; }
.search-row button { min-height: 48px; border: 0; border-radius: 16px; padding: 0 18px; background: var(--ink); color: #fff; font-weight: 950; cursor: pointer; }
.search-panel { margin-top: 12px; }
.search-result-card mark { background: #fff0b8; border-radius: 6px; padding: 0 2px; }
.search-result-card { min-width: 0; overflow: hidden; }
.search-result-card h2 { font-size: clamp(18px, 4.7vw, 22px); line-height: 1.32; }
.search-result-card h2 a { display: block; }
.search-result-card p { font-size: 15px; line-height: 1.62; }
.quick-links { display: grid; gap: 10px; padding-left: 0; list-style: none; }
.quick-links li { display: flex; justify-content: space-between; gap: 12px; border-bottom: 1px solid var(--line); padding: 10px 0; }
.quick-links span { color: var(--muted); font-size: 13px; font-weight: 800; }
.article-tail { margin: 28px 0 70px; display: flex; gap: 12px; flex-wrap: wrap; }
.footer {
  width: min(1240px, calc(100% - 32px)); margin: 56px auto 0; padding: 28px 0 40px;
  border-top: 1px solid var(--line); color: #5f5652;
}
.muted { color: var(--muted); font-size: 14px; }
@media (max-width: 860px) {
  .site-header { position: static; align-items: stretch; grid-template-columns: 1fr; gap: 10px; padding: 10px 12px 12px; }
  .brand { width: 100%; gap: 10px; }
  .brand-mark { width: 40px; height: 40px; border-radius: 14px; }
  .brand strong { font-size: 19px; }
  .brand small { font-size: 12px; }
  .nav { width: 100%; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; padding: 6px; border-radius: 22px; overflow: visible; box-shadow: 0 8px 20px rgba(58, 37, 20, .055); }
  .nav a { min-width: 0; min-height: 44px; padding: 0 8px; border: 1px solid rgba(234, 223, 212, .95); background: rgba(255, 255, 255, .88); font-size: 13px; }
  .nav a span { min-width: 0; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .nav a.nav-primary { color: #312826; font-weight: 950; }
  .nav a.nav-action { background: rgba(255, 255, 255, .88); border-color: rgba(234, 223, 212, .95); color: #594e49; }
  .nav a[aria-current="page"] { background: var(--orange); border-color: var(--orange); color: #fff; box-shadow: none; }
  main { width: min(100% - 28px, 1240px); }
  h1 { font-size: clamp(32px, 9.5vw, 46px); line-height: 1.08; letter-spacing: -0.048em; }
  .compact h1, .article-hero h1 { font-size: clamp(29px, 8.2vw, 42px); line-height: 1.12; }
  .hero, .page-hero, .shop-hero, .article-hero { padding-top: 30px; }
  .lead { font-size: 17px; line-height: 1.62; }
  .grid.three, .grid.two, .status-strip, .shop-summary, .shop-hero, .deal-landing-hero, .site-bridge-strip, .quick-facts, .article-product-hero, .radar-card, .radar-experience-grid { grid-template-columns: 1fr; }
  .bridge-actions { justify-content: flex-start; }
  .shop-hero { gap: 16px; padding-bottom: 16px; }
  .deal-landing-hero { gap: 14px; padding-top: 24px; }
  .deal-hero-copy, .deal-hero-panel, .deal-quick-box { border-radius: 22px; }
  .deal-grid.best-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .quick-products ol { columns: 1; }
  .category-strip { flex-wrap: nowrap; overflow-x: auto; padding-bottom: 4px; -webkit-overflow-scrolling: touch; }
  .category-chip { flex: 0 0 auto; }
  .hero-pin-stack { min-height: auto; display: flex; gap: 10px; overflow-x: auto; padding-bottom: 4px; -webkit-overflow-scrolling: touch; }
  .hero-pin, .hero-pin.pin-1, .hero-pin.pin-2, .hero-pin.pin-3 { position: relative; inset: auto; flex: 0 0 132px; width: 132px; transform: none; border-width: 5px; border-radius: 20px; }
  .hero-pin span { display: none; }
  .card, .panel, .notice, .list-card, .article-content, .related-radar { border-radius: 22px; padding: 22px; }
  .radar-card { padding: 0; }
  .radar-card-visual { min-height: 236px; padding: 19px; }
  .radar-thumb-title { max-width: 166px; font-size: clamp(27px, 8.1vw, 36px); }
  .radar-thumb-subline { max-width: 152px; font-size: 12px; line-height: 1.32; }
  .radar-thumb-art { width: min(45%, 168px); right: 10px; bottom: 22px; min-height: 126px; }
  .time-card { font-size: 21px; padding: 8px 10px; }
  .rail-line { top: 82px; }
  .station { min-width: 42px; padding: 6px 7px; font-size: 10px; }
  .station-c { max-width: 58px; }
  .receipt { left: 8px; width: 108px; padding: 12px 10px 14px; }
  .stamp { right: 0; bottom: 20px; width: 64px; height: 64px; font-size: 15px; }
  .calc { left: 6px; width: 96px; }
  .loss-line { right: 0; font-size: 20px; }
  .funnel { left: 8px; width: 94px; }
  .checklist { right: 0; width: 78px; }
  .awning { left: 4px; width: 112px; }
  .storefront { left: 10px; width: 102px; }
  .cup { right: 0; width: 54px; }
  .radar-map-card { min-height: auto; }
  .radar-map { min-height: 260px; }
  .map-label { left: 12px; top: 12px; font-size: 11px; }
  .map-node { font-size: 12px; transform: translate(-50%, -19px); }
  .map-node b { width: 38px; height: 38px; border-width: 2px; }
  .radar-toc-card ol { grid-template-columns: 1fr; }
  .search-row { flex-direction: column; }
  .search-row input, .search-row button { width: 100%; }
  .article-page { max-width: 100%; }
  .article-product-hero img { max-height: 320px; object-fit: contain; margin: 0 auto; }
}
@media (max-width: 560px) {
  main, .footer { width: min(100% - 24px, 1240px); }
  .nav { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .nav a { min-height: 44px; font-size: 12.5px; }
  .hero-actions, .article-tail { display: grid; grid-template-columns: 1fr; }
  .button, .deal-button { width: 100%; }
  .status-strip, .shop-summary { grid-template-columns: 1fr; gap: 8px; }
  .status-strip div, .shop-summary div { padding: 15px 16px; border-radius: 18px; }
  .deal-grid, .mixed-list { grid-template-columns: 1fr; gap: 12px; }
  .deal-grid.best-grid { grid-template-columns: 1fr; }
  .deal-hero-copy { padding: 20px; }
  .playful-badges { flex-wrap: nowrap; overflow-x: auto; padding-bottom: 4px; -webkit-overflow-scrolling: touch; }
  .playful-badges span { flex: 0 0 auto; }
  .site-bridge-strip { padding: 18px; border-radius: 22px; }
  .bridge-actions { display: grid; grid-template-columns: 1fr; }
  .affiliate-disclosure { margin-top: 16px; }
  .quick-facts { gap: 8px; }
  .deal-card { display: grid; grid-template-columns: 96px minmax(0, 1fr); border-radius: 22px; }
  .radar-map-card { padding: 18px; }
  .radar-map { min-height: 420px; border-radius: 24px; }
  .map-route-desktop { display: none; }
  .map-route-mobile { display: block; }
  .map-route-guide { stroke-width: 11; }
  .map-route-path { stroke-width: 4.25; }
  .map-label { left: 12px; top: 12px; font-size: 12px; padding: 7px 10px; }
  .node-1 { left: 17%; top: 26%; } .node-2 { left: 58%; top: 28%; } .node-3 { left: 82%; top: 47%; } .node-4 { left: 38%; top: 66%; } .node-5 { left: 72%; top: 83%; }
  .map-node { font-size: 15px; transform: translate(-50%, -21px); }
  .map-node b { width: 42px; height: 42px; }
  .map-node em { padding: 7px 13px; }
  .deal-thumb { min-height: 100%; display: flex; align-items: center; justify-content: center; }
  .deal-thumb img { height: 100%; min-height: 132px; max-height: 168px; aspect-ratio: auto; object-fit: contain; padding: 8px; }
  .deal-text-badge { min-height: 132px; padding: 10px; font-size: 12px; border-bottom: 0; border-right: 1px solid var(--line); }
  .deal-count { left: 8px; top: 8px; font-size: 11px; padding: 5px 7px; }
  .deal-body { min-width: 0; padding: 14px; gap: 8px; }
  .deal-meta { align-items: flex-start; flex-direction: column; gap: 4px; font-size: 11px; }
  .deal-card h2 { font-size: 18px; line-height: 1.32; }
  .deal-card p { font-size: 15px; line-height: 1.55; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
  .deal-actions { display: grid; grid-template-columns: 1fr; }
  .deal-actions .deal-button { width: 100%; min-height: 44px; }
  .search-result-card { padding: 16px; }
  .search-result-card:has(> img) { display: grid; grid-template-columns: 92px minmax(0, 1fr); gap: 8px 12px; align-items: start; }
  .search-result-card:has(> img) > img { grid-row: 1 / span 5; width: 92px; height: 92px; object-fit: contain; margin: 0; border-radius: 14px; }
  .search-result-card h2 { font-size: 18px; }
  .search-result-card p { font-size: 14.5px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
  .search-result-card .muted { -webkit-line-clamp: 2; }
  .quick-links li { display: block; }
  .quick-links span { display: block; margin-top: 4px; }
  .article-content { padding: 20px 18px; font-size: 16.5px; line-height: 1.78; }
  .article-content h2 { font-size: 24px; line-height: 1.25; }
  .radar-article .article-content > section > h2, .radar-article .article-content > h2 { grid-template-columns: 34px 1fr; gap: 10px; }
  .radar-article .article-content > section > h2::before, .radar-article .article-content > h2::before { width: 30px; height: 30px; font-size: 12px; }
  .article-content h3 { font-size: 20px; line-height: 1.32; }
  .article-content img { max-height: 330px; }
  .table-scroll { margin-left: 0; margin-right: 0; width: 100%; overflow-x: visible; padding: 0 0 8px; }
  .table-scroll::before { content: "핵심만 카드로 비교합니다"; padding: 10px 12px 8px; }
  .table-scroll table, .table-scroll thead, .table-scroll tbody, .table-scroll tr, .table-scroll th, .table-scroll td { display: block; width: 100%; min-width: 0; }
  .table-scroll thead { display: none; }
  .table-scroll tr { margin: 0 10px 12px; border: 1px solid var(--line); border-radius: 16px; overflow: hidden; background: #fff; }
  .table-scroll td { border: 0; border-bottom: 1px solid var(--line); padding: 10px 12px; }
  .table-scroll td:last-child { border-bottom: 0; }
  .table-scroll td::before { content: attr(data-label); display: block; margin-bottom: 4px; color: var(--muted); font-size: 12px; font-weight: 950; }
}
@media (max-width: 360px) {
  .nav { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
'''

LOGO = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" aria-label="Recuerdame Lab"><rect width="128" height="128" rx="34" fill="#101828"/><path d="M38 91V31h32c13 0 22 8 22 20 0 9-5 16-13 19l17 21H76L62 72h-8v19H38Zm16-33h14c6 0 10-3 10-8s-4-8-10-8H54v16Z" fill="#fff"/><circle cx="93" cy="36" r="8" fill="#60a5fa"/></svg>'''

OG = '''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630"><defs><linearGradient id="g" x1="0" x2="1"><stop stop-color="#101828"/><stop offset="1" stop-color="#1d4ed8"/></linearGradient></defs><rect width="1200" height="630" fill="url(#g)"/><circle cx="1030" cy="120" r="210" fill="#60a5fa" opacity=".22"/><circle cx="170" cy="520" r="190" fill="#f59e0b" opacity=".22"/><text x="80" y="220" fill="#fff" font-family="Arial, sans-serif" font-size="72" font-weight="800">Recuerdame Lab</text><text x="80" y="315" fill="#e5e7eb" font-family="Arial, sans-serif" font-size="38">계약 전 동네 레이더</text><text x="80" y="405" fill="#bfdbfe" font-family="Arial, sans-serif" font-size="30">Search and AI ready public hub</text></svg>'''

SEARCH_JS = '''(() => {
  const form = document.querySelector('.site-search');
  const input = document.querySelector('#search-query');
  const results = document.querySelector('#search-results');
  const summary = document.querySelector('#search-summary');
  if (!form || !input || !results || !summary) return;

  const esc = (value) => String(value || '').replace(/[&<>"]/g, (ch) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
  const params = new URLSearchParams(window.location.search);
  const initial = params.get('q') || '';
  input.value = initial;

  let indexItems = [];
  const normalize = (value) => String(value || '').toLowerCase().replace(/\s+/g, ' ').trim();
  const tokensOf = (query) => normalize(query).split(' ').filter(Boolean).slice(0, 8);
  const scoreItem = (item, tokens) => {
    const title = normalize(item.title);
    const desc = normalize(item.description);
    const tags = normalize((item.tags || []).join(' '));
    const text = normalize(item.text);
    let score = 0;
    let matched = false;
    let matchedCount = 0;
    for (const token of tokens) {
      let tokenScore = 0;
      if (title.includes(token)) tokenScore += 12;
      if (tags.includes(token)) tokenScore += 7;
      if (desc.includes(token)) tokenScore += 4;
      if (text.includes(token)) tokenScore += 1;
      if (tokenScore > 0) {
        matched = true;
        matchedCount += 1;
      }
      score += tokenScore;
    }
    if (!matched) return 0;
    if (tokens.length > 1 && matchedCount < tokens.length) return 0;
    if (item.section === 'deals') score += 0.5;
    const views = Number(item.views || 0);
    if (views > 0) score += Math.min(3, Math.log10(views + 1));
    return score;
  };
  const render = (query) => {
    const tokens = tokensOf(query);
    if (!tokens.length) {
      results.innerHTML = '';
      summary.textContent = '검색어를 입력하면 관련 글을 보여줍니다.';
      return;
    }
    const matches = indexItems.map((item) => ({item, score: scoreItem(item, tokens)}))
      .filter((x) => x.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 24);
    summary.textContent = matches.length ? `${matches.length}개 결과를 찾았습니다.` : '관련 결과가 아직 없습니다. 다른 키워드로 검색해보세요.';
    results.innerHTML = matches.map(({item}) => {
      const meta = [item.category, item.item_count_hint, item.price_hint].filter(Boolean).slice(0, 3).join(' · ');
      const image = item.image_url ? `<img src="${esc(item.image_url)}" alt="${esc(item.title)}" loading="lazy" decoding="async" />` : '';
      return `<article class="list-card search-result-card">${image}<div class="card-meta"><span class="tag">${esc(item.section === 'deals' ? '구매가이드' : item.section === 'radar' ? '동네 레이더' : '사이트')}</span></div><h2><a href="${esc(item.path)}">${esc(item.title)}</a></h2><p>${esc(item.description || '')}</p><p class="muted">${esc(meta)}</p><a class="text-link" href="${esc(item.path)}">열기 →</a></article>`;
    }).join('');
  };
  const updateUrl = (query) => {
    const url = new URL(window.location.href);
    if (query) url.searchParams.set('q', query); else url.searchParams.delete('q');
    window.history.replaceState({}, '', url);
  };

  fetch('/data/search-index.json', {cache: 'no-store'})
    .then((res) => res.ok ? res.json() : Promise.reject(new Error('search index missing')))
    .then((data) => {
      indexItems = Array.isArray(data.items) ? data.items : [];
      render(input.value);
    })
    .catch(() => {
      summary.textContent = '검색 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.';
    });

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const query = input.value.trim();
    updateUrl(query);
    render(query);
  });
  input.addEventListener('input', () => render(input.value));
})();
'''


def write(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if content:
        content = "\n".join(line.rstrip() for line in content.splitlines()) + ("\n" if content.endswith("\n") else "")
    path.write_text(content, encoding="utf-8", newline="\n")


def build() -> None:
    deals = load_articles("deals")
    radar = load_articles("radar")
    SOURCE_URL_TO_PATH.clear()
    for article in deals:
        source_url = str(article.get("source_url") or "").strip()
        if source_url:
            SOURCE_URL_TO_PATH[source_url] = article["path"]
    for article in deals + radar:
        article["body_html"] = localize_public_body(article["body_html"])

    bodies = {
        "home": home_body(deals, radar),
        "radar": radar_body(radar),
        "deals": deals_body(deals),
        "search": search_body(deals, radar),
        "guides": guides_body(),
        "about": about_body(len(deals), len(radar)),
    }

    for page in STATIC_PAGES:
        write(page["file"], layout(page, bodies[page["section"]]))

    for article in deals + radar:
        related = [a for a in radar if a["path"] != article["path"]][:3] if article.get("section") == "radar" else []
        write(article["file"], layout(article, article_body(article, related)))

    write("404.html", layout({
        "path": "/404.html",
        "title": "페이지를 찾을 수 없습니다 — Recuerdame Lab",
        "description": "요청한 페이지를 찾을 수 없습니다.",
        "type": "WebPage",
        "section": "404",
    }, '<section class="page-hero compact"><h1>페이지를 찾을 수 없습니다.</h1><p class="lead">주소를 확인하거나 홈으로 돌아가세요.</p><a class="button primary" href="/">홈으로</a></section>'))

    write("main.css", CSS)
    write("assets/logo.svg", LOGO)
    write("assets/og-card.svg", OG)
    write("assets/search.js", SEARCH_JS)
    write("data/search-index.json", json.dumps(build_search_index(deals, radar), ensure_ascii=False, indent=2) + "\n")
    write(".nojekyll", "")
    write("robots.txt", f'''User-agent: *
Allow: /
Allow: /llms.txt
Allow: /ai.txt

# Korean/search crawlers
User-agent: Googlebot
Allow: /
User-agent: Yeti
Allow: /
User-agent: NaverBot
Allow: /
User-agent: Daumoa
Allow: /
User-agent: Bingbot
Allow: /

# AI/search assistants: allow discovery and citation
User-agent: GPTBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Applebot
Allow: /
User-agent: Google-Extended
Allow: /

Sitemap: {BASE}/sitemap.xml
Host: r2cuerdame.github.io
''')

    all_pages = list(STATIC_PAGES) + radar + deals
    sitemap_items = "\n".join(
        f'  <url><loc>{BASE}{p["path"]}</loc><lastmod>{parse_dt(p.get("date")).date().isoformat() if p.get("type") == "BlogPosting" else TODAY}</lastmod><changefreq>{"weekly" if p.get("type") == "BlogPosting" else "daily"}</changefreq><priority>{p.get("priority", "0.64")}</priority></url>'
        for p in all_pages
    )
    write("sitemap.xml", f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{sitemap_items}
</urlset>
''')

    rss_source = (radar + deals)[:20] or STATIC_PAGES[:4]
    rss_items = "\n".join(
        f'''<item><title>{esc(p["title"])}</title><link>{BASE}{p["path"]}</link><guid>{BASE}{p["path"]}</guid><pubDate>{format_datetime(parse_dt(p.get("date")))}</pubDate><description>{esc(p["description"])}</description></item>'''
        for p in rss_source
    )
    write("feed.xml", f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Dongne Radar — Recuerdame Lab</title><link>{BASE}/radar/</link><description>{esc(SITE_DESC)}</description><language>ko-KR</language><lastBuildDate>{format_datetime(NOW)}</lastBuildDate>{rss_items}</channel></rss>
''')

    radar_article_lines = "\n".join(
        f"- {a['title']}: {BASE}{a['path']}" for a in radar[:20]
    ) or "- 아직 공개된 동네 레이더 글 없음"
    deals_article_lines = "\n".join(
        f"- {a['title']}: {BASE}{a['path']}" for a in deals[:8]
    ) or "- 공개된 구매가이드 없음"
    ai_radar_lines = "\n".join(
        f"Radar Article: {BASE}{a['path']} — {a['title']}" for a in radar[:12]
    ) or "Radar Article: none"
    ai_deals_lines = "\n".join(
        f"Separate Deals Article: {BASE}{a['path']} — {a['title']}" for a in deals[:4]
    ) or "Separate Deals Article: none"
    write("llms.txt", f'''# Recuerdame Lab / Dongne Radar

> 이사·월세·전세·상가 계약 전, 동네와 상권 리스크를 먼저 걸러내는 한국어 공개 노트입니다.

Base URL: {BASE}/
Primary scope: Dongne Radar — 이사, 전월세 계약, 통근, 생활권, 현장 확인, 상가 임대차, 권리금 리스크.
Language: ko-KR
Last updated: {NOW.isoformat(timespec='seconds')}

## Primary sections

- 동네 레이더: {BASE}/radar/
  - 계약 전 리스크, 생활권, 통근, 관리비, 소음, 상권·권리금 리스크를 판단 카드와 현장 질문으로 정리합니다.
- 읽는 순서: {BASE}/guides/
  - 첫 방문자가 이사·월세·상가 계약 전 어떤 글을 먼저 읽을지 안내합니다.
- 소개: {BASE}/about/
  - 운영 원칙, 섹션 분리, 검색/AI 공개 원칙을 설명합니다.

## Separate commercial section

- 구매가이드: {BASE}/deals/
  - 동네 레이더와 분리된 생활 상품 비교 섹션입니다.
  - 제휴 링크가 포함된 글은 본문에 고지를 표시합니다.
- 사이트 검색: {BASE}/search/
  - 동네 레이더와 구매가이드 글을 키워드로 빠르게 찾습니다.

## Dongne Radar articles

{radar_article_lines}

## Separate deals articles

{deals_article_lines}

## Crawl hints

- Canonical site: {BASE}/
- Sitemap: {BASE}/sitemap.xml
- RSS: {BASE}/feed.xml
- Robots: {BASE}/robots.txt
- AI guide: {BASE}/ai.txt

## Citation preference

When citing this site, prefer Dongne Radar pages for neighborhood, moving, rent, commute, living-area, on-site-check, commercial-lease, and store-location-risk queries. Cite the canonical page URL and use Korean summaries for Korean queries.
''')
    write("ai.txt", f'''Recuerdame Lab allows AI search crawlers and answer engines to discover, index, summarize, and cite public pages on this site.

Canonical: {BASE}/
Primary scope: Dongne Radar for moving, monthly rent, jeonse, commute, living area, on-site checks, commercial lease, cafe/store location, key money risk.
Radar: {BASE}/radar/
Guides: {BASE}/guides/
About: {BASE}/about/
Separate deals section: {BASE}/deals/
Search: {BASE}/search/
Sitemap: {BASE}/sitemap.xml
Feed: {BASE}/feed.xml
LLM guide: {BASE}/llms.txt
{ai_radar_lines}
{ai_deals_lines}
Language: ko-KR
Updated: {NOW.isoformat(timespec='seconds')}
''')
    write("humans.txt", f'''Recuerdame Lab
Owner: r2cuerdame
Site: {BASE}/
Language: Korean
Primary purpose: Dongne Radar — moving, rent, commute, living-area, on-site-check, and commercial-lease risk notes.
Separate section: /deals/ for lifestyle shopping picks and affiliate-disclosed comparisons.
Updated: {NOW.isoformat(timespec='seconds')}
''')
    write("build-info.json", json.dumps({
        "site": SITE_NAME,
        "base_url": BASE,
        "built_at": NOW.isoformat(timespec="seconds"),
        "timezone": "Asia/Seoul",
        "primary_scope": "Dongne Radar: 이사·월세·전세·통근·생활권·현장 확인·상가 계약 리스크",
        "sections": [p["path"] for p in STATIC_PAGES],
        "article_counts": {"radar": len(radar), "deals": len(deals)},
        "search_ready": ["google", "naver", "daum", "ai_search", "site_search"],
        "search_index": f"{BASE}/data/search-index.json",
        "analytics": {"tracking_ready": bool(ANALYTICS_ID), "metrics_status": PAGE_METRICS_DATA.get("status"), "metrics_updated_at": PAGE_METRICS_DATA.get("updated_at")},
        "sitemap": f"{BASE}/sitemap.xml",
        "rss": f"{BASE}/feed.xml",
        "llms": f"{BASE}/llms.txt",
        "ai": f"{BASE}/ai.txt",
        "humans": f"{BASE}/humans.txt",
    }, ensure_ascii=False, indent=2) + "\n")
    write("README.md", f'''# Recuerdame Lab — r2cuerdame.github.io

Public site for Dongne Radar, guides, and a clearly separated deals section.

## Live URLs

- Home: {BASE}/
- Dongne Radar: {BASE}/radar/
- Guides: {BASE}/guides/
- About: {BASE}/about/
- Separate Shopping Picks: {BASE}/deals/
- Site Search: {BASE}/search/

## Current content

- Dongne Radar articles: {len(radar)}
- Shopping pick articles: {len(deals)}

## Search/AI files

- `{BASE}/sitemap.xml`
- `{BASE}/robots.txt`
- `{BASE}/feed.xml`
- `{BASE}/llms.txt`
- `{BASE}/ai.txt`
- `{BASE}/humans.txt`
- `{BASE}/search/`
- `{BASE}/data/search-index.json`

## Operating scope

Dongne Radar is the primary editorial scope: 이사, 월세·전세 계약, 통근, 생활권, 현장 확인, 상가 임대차, 권리금 리스크.

## Affiliate rule

제휴 링크가 포함된 구매가이드 글에는 본문 상단에 필수 제휴 고지를 표시한다. 동네 레이더 글에는 제휴 문맥을 섞지 않는다.
''')
    write("docs/search-indexing.md", f'''# Search indexing checklist

Public URL: {BASE}/
Sitemap: {BASE}/sitemap.xml
RSS: {BASE}/feed.xml
LLM guide: {BASE}/llms.txt

## Already handled in repo

- robots allows Google, Naver/Yeti, Daumoa, Bing, and major AI/search crawlers.
- sitemap includes static sections and generated article URLs.
- every HTML page has canonical, description, OG, RSS, sitemap link, SearchAction JSON-LD, breadcrumb JSON-LD, and page/article JSON-LD.
- `/search/` and `data/search-index.json` give users a fast site/product search surface.
- `llms.txt` and `ai.txt` exist for AI search/answer engines.
- new public articles update the related feed and sitemap.

## Registration status

Search engines require owner verification before manual sitemap submission. Verification tokens are kept only as site meta tags, not as account credentials.

- Google Search Console: property verified and `/sitemap.xml` submitted.
- Naver Search Advisor: site ownership accepted; sitemap/robots are ready for crawl checks.
- Daum search/webmaster registration: register site URL and sitemap if the tool asks for it.

Keep publishing complete reader-facing pages. Empty daily rebuilds help freshness but do not replace real content.
''')


if __name__ == "__main__":
    build()
    print(json.dumps({"built_at": NOW.isoformat(timespec="seconds"), "static_pages": len(STATIC_PAGES), "base": BASE}, ensure_ascii=False))
