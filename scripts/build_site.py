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
DEALS_KEYWORDS = "쇼핑픽, 구매가이드, 생활용품 추천, 상품 비교, 가격 비교, Recuerdame Lab"

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
    document.addEventListener('click', function(event) {{
      var link = event.target && event.target.closest ? event.target.closest('a[href*="coupang.com"]') : null;
      if (!link || typeof gtag !== 'function') return;
      try {{
        var url = new URL(link.href, window.location.href);
        gtag('event', 'affiliate_click', {{
          event_category: 'outbound',
          outbound_domain: url.hostname,
          link_url: url.origin + url.pathname,
          page_path: window.location.pathname,
          transport_type: 'beacon'
        }});
      }} catch (error) {{}}
    }}, true);
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
        "path": "/topics/",
        "file": "topics/index.html",
        "title": "주제별 보기 — 월세·전세·상가·생활상품 체크리스트",
        "description": "월세 계약, 전세 체크, 통근·밤길·상가 리스크와 생활상품 비교를 주제별로 묶은 Recuerdame Lab 안내 페이지입니다.",
        "priority": "0.82",
        "type": "CollectionPage",
        "section": "topics",
    },
    {
        "path": "/search/",
        "file": "search/index.html",
        "title": "사이트 검색 — Recuerdame Lab",
        "description": "동네 레이더와 쇼핑픽 글을 키워드로 빠르게 찾는 사이트 검색입니다.",
        "priority": "0.64",
        "type": "SearchResultsPage",
        "section": "search",
    },
]

NAV = [
    ("동네 레이더", "/radar/", "nav-primary"),
    ("쇼핑픽", "/deals/", "nav-primary"),
    ("검색", "/search/", "nav-action"),
]

TOPIC_HUBS = [
    {"slug": "jeonwolse-contract-check", "title": "전월세 계약 전 체크 — 집 보기 전 먼저 볼 글 목록", "description": "월세·전세 후보를 글 하나로 바로 들어가지 않고, 관리비·통근·밤길·공용부·비 오는 날 신호처럼 계약 전 확인 글을 순서대로 모았습니다.", "label": "전월세 체크", "intent": "집을 보러 가기 전 전세·월세 공통 리스크를 빠르게 훑고 싶은 독자", "keywords": ["전월세", "전월세 계약", "월세", "전세", "이사", "관리비", "통근", "밤길", "공동현관"], "queries": ["전월세 계약 전 체크", "월세 전세 체크리스트", "집 계약 전 확인"], "primary_section": "radar", "priority": "0.86"},
    {"slug": "wolse-contract-checklist", "title": "월세 계약 전 체크리스트 — 관리비·통근·생활권 먼저 보기", "description": "월세가 싸 보여도 관리비, 통근 피로, 밤길, 생활권 비용까지 합치면 더 비싸질 수 있습니다. 계약 전 확인할 글을 한곳에 묶었습니다.", "label": "월세 계약", "intent": "월세 집을 보러 가기 전, 숫자로 보이는 월세와 실제 생활비 차이를 줄이고 싶은 독자", "keywords": ["월세", "관리비", "생활권", "통근", "계약 전"], "queries": ["월세 계약 전 체크리스트", "월세 관리비 확인", "이사 전 동네 체크"], "primary_section": "radar", "priority": "0.84"},
    {"slug": "jeonse-contract-risk", "title": "전세 계약 전 동네 체크 — 보증금보다 먼저 볼 생활 리스크", "description": "전세 계약은 집 내부만 보면 부족합니다. 밤길, 공용부 관리, 통근, 비 오는 날 배수처럼 계약 전에 다시 봐야 할 동네 신호를 정리했습니다.", "label": "전세 체크", "intent": "전세 후보지를 줄이면서 집 내부보다 주변 리스크를 먼저 확인하려는 독자", "keywords": ["전세", "이사", "공동현관", "밤길", "비 오는 날"], "queries": ["전세 계약 전 체크", "전세 집 주변 확인", "동네 리스크 체크"], "primary_section": "radar", "priority": "0.82"},
    {"slug": "commute-neighborhood-check", "title": "출퇴근 동네 체크 — 지도앱 시간보다 피로를 먼저 계산", "description": "지도앱 35분과 매일 몸으로 겪는 출퇴근 피로는 다릅니다. 역에서 집까지 마지막 도보, 환승, 아침 동선을 함께 보는 글 모음입니다.", "label": "출퇴근", "intent": "이사 후보지의 출퇴근 시간이 실제로 버틸 만한지 확인하려는 독자", "keywords": ["통근", "출근", "퇴근", "역", "도보", "환승"], "queries": ["출퇴근 좋은 동네", "역에서 집까지 밤길", "통근 피로 체크"], "primary_section": "radar", "priority": "0.80"},
    {"slug": "night-noise-safety-check", "title": "밤길·소음 체크 — 낮에 본 집을 밤에 다시 보는 법", "description": "낮에는 조용해 보여도 밤 10시의 골목, 배달 동선, 창문 밖 소리는 다릅니다. 계약 전 밤길과 소음을 확인하는 글을 묶었습니다.", "label": "밤길·소음", "intent": "집을 계약하기 전 밤길 안전감과 생활소음을 놓치고 싶지 않은 독자", "keywords": ["밤길", "소음", "퇴근", "골목", "집 보기"], "queries": ["밤에 집 보러가기", "동네 소음 체크", "밤길 안전 확인"], "primary_section": "radar", "priority": "0.80"},
    {"slug": "cafe-commercial-lease-risk", "title": "카페 창업 상가 계약 체크 — 유동인구보다 먼저 볼 리스크", "description": "사람이 많은 상권이 꼭 좋은 자리는 아닙니다. 카페 창업 전 경쟁점, 권리금, 회전율, 폐업 압력을 확인하는 상가 계약 글 모음입니다.", "label": "상가 계약", "intent": "카페나 작은 매장을 준비하며 유동인구 착시와 권리금 리스크를 줄이고 싶은 예비 사장", "keywords": ["카페", "상가", "창업", "권리금", "유동인구"], "queries": ["카페 상가 계약 체크", "권리금 리스크", "상권 유동인구 확인"], "primary_section": "radar", "priority": "0.83", "include_paths": ["/radar/cafe-contract-risk/"]},
    {"slug": "rainy-season-home-appliances", "title": "장마철 생활가전 비교 — 제습기·공기청정기 먼저 고르기", "description": "장마와 습기 시즌에는 제습기, 공기청정기, 청소기처럼 관리 부담이 큰 가전부터 비교해야 합니다. 구매 전 확인할 글을 묶었습니다.", "label": "장마 가전", "intent": "장마철 습기와 공기 문제를 해결하려고 생활가전을 비교하는 구매 직전 독자", "keywords": ["제습기", "공기청정기", "장마", "습기", "청소기"], "queries": ["제습기 추천", "공기청정기 비교", "장마철 가전"], "primary_section": "deals", "priority": "0.76"},
    {"slug": "work-from-home-desk-setup", "title": "재택근무 책상 장비 비교 — 의자·모니터암·조명·키보드", "description": "재택근무 장비는 예쁜 사진보다 허리, 눈 피로, 책상 공간을 먼저 봐야 합니다. 의자, 모니터암, 조명, 키보드 비교글을 묶었습니다.", "label": "재택 장비", "intent": "재택근무 책상 셋업을 한 번에 정리하려는 구매 직전 독자", "keywords": ["재택근무", "사무용 의자", "모니터암", "모니터 조명", "키보드"], "queries": ["재택근무 의자 추천", "모니터암 추천", "모니터 조명 추천"], "primary_section": "deals", "priority": "0.75"},
    {"slug": "sound-gaming-gadgets", "title": "음향·게임 장비 비교 — 헤드셋·스피커·ANC 헤드폰", "description": "헤드셋, 블루투스 스피커, ANC 헤드폰은 가격보다 사용 장면과 착용감이 중요합니다. 구매 전 비교글을 한곳에 묶었습니다.", "label": "음향·게임", "intent": "게임, 재택회의, 음악 감상용 음향 장비를 비교하는 구매 직전 독자", "keywords": ["헤드셋", "스피커", "ANC", "헤드폰", "블루투스"], "queries": ["게이밍 헤드셋 추천", "블루투스 스피커 추천", "ANC 헤드폰 비교"], "primary_section": "deals", "priority": "0.74"},
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
        ("오늘 추천", "/deals/#today-best", "nav-primary"),
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
ANCHOR_RE = re.compile(r'<a\b(?P<attrs>[^>]*)>(?P<label>[\s\S]*?)</a>', re.I)
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


def absolute_url(value: str) -> str:
    url = clean_url(value)
    if url.startswith("/"):
        return f"{BASE}{url}"
    return url


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
        if path.startswith("/deals/"):
            section_label, section_path = "쇼핑픽", "/deals/"
        elif path.startswith("/radar/"):
            section_label, section_path = "동네 레이더", "/radar/"
        elif path.startswith("/topics/"):
            section_label, section_path = "주제별 보기", "/topics/"
        else:
            section_label, section_path = page.get("title", SITE_NAME), path
        items = [
            {"@type": "ListItem", "position": 1, "name": "홈", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": section_label, "item": f"{BASE}{section_path}"},
        ]
        if section_path != path:
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
                "image": absolute_url(page.get("image_url")) or f"{BASE}/assets/og-card.svg",
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
    if section == "topics" or path.startswith("/topics/"):
        return keyword_join(COMMON_KEYWORDS, RADAR_KEYWORDS, DEALS_KEYWORDS, page.get("tags") or [], "주제별 보기, 월세 체크리스트, 전세 체크리스트, 상가 계약 체크, 구매가이드 모음")
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
    og_image = absolute_url(page.get("image_url")) or f"{BASE}/assets/og-card.svg"
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
    <p class="muted">/radar/는 동네 레이더, /deals/는 별도 쇼핑픽으로 분리해 운영합니다.</p>
    <p class="muted">마지막 업데이트: <time datetime="{NOW.isoformat(timespec='seconds')}">{NOW.strftime('%Y-%m-%d %H:%M KST')}</time></p>
  </footer>
</body>
</html>
'''


def plain_article_card(a: dict) -> str:
    tags = taxonomy_links(a.get("tags") or [], "tag pale", limit=3)
    category = taxonomy_link(a.get("category"), "tag")
    date = parse_dt(a.get("date")).strftime("%Y-%m-%d")
    metric = traffic_badge(a["path"])
    return f'''<article class="list-card">
  <div class="card-meta">{category}<time datetime="{esc(a.get('date'))}">{date}</time>{metric}</div>
  <h2><a href="{esc(a['path'])}">{esc(a['title'])}</a></h2>
  <p>{esc(short_text(a['description'], 115))}</p>
  <div class="tag-row">{tags}</div>
  <a class="text-link" href="{esc(a['path'])}">읽어보기 →</a>
</article>'''


RADAR_CARD_VISUALS = {
    "bus-stop-front-home-check": {
        "theme": "theme-night",
        "scene": "night",
        "badge": "정류장 소음",
        "label": "CASE",
        "headline": "문앞 정류장",
        "subline": "대기열·차량 소리·시선 피로 보기",
        "chips": ("정류장", "대기열", "소음"),
    },
    "station-to-home-night-route-check": {
        "theme": "theme-night",
        "scene": "night",
        "badge": "밤길 동선",
        "label": "NEW",
        "headline": "마지막 7분",
        "subline": "역에서 집까지 밤에 다시 걷기",
        "chips": ("역", "골목", "우회"),
    },
    "shared-entrance-management-signals": {
        "theme": "theme-filter",
        "scene": "filter",
        "badge": "공용부 신호",
        "label": "CHECK",
        "headline": "현관 30초",
        "subline": "우편함·게시판·문 앞 질서 보기",
        "chips": ("현관", "우편", "게시"),
    },
    "ground-floor-home-check": {
        "theme": "theme-filter",
        "scene": "filter",
        "badge": "1층 리스크",
        "label": "CHECK",
        "headline": "창문 거리",
        "subline": "낮빛·시선·택배 동선 확인",
        "chips": ("시선", "방범", "채광"),
    },
    "stair-only-fourth-floor-villa-check": {
        "theme": "theme-commute",
        "scene": "commute",
        "badge": "계단 체력",
        "label": "CHECK",
        "headline": "4층 루틴",
        "subline": "장보기·이사 날까지 계산",
        "chips": ("계단", "짐", "반복"),
    },
    "morning-routine-neighborhood-check": {
        "theme": "theme-commute",
        "scene": "commute",
        "badge": "아침 동선",
        "label": "CHECK",
        "headline": "8시 충돌",
        "subline": "등교·차량·분리수거가 겹치는지",
        "chips": ("등교", "차량", "수거"),
    },
    "night-noise-walk-check": {
        "theme": "theme-night",
        "scene": "night",
        "badge": "밤 소음",
        "label": "CHECK",
        "headline": "22시 소리",
        "subline": "낮에 안 들리는 생활음을 잡기",
        "chips": ("창문", "배달", "골목"),
    },
    "rainy-day-viewing-neighborhood-signals": {
        "theme": "theme-commute",
        "scene": "commute",
        "badge": "비 오는 날",
        "label": "CHECK",
        "headline": "물길 확인",
        "subline": "배수·미끄럼·습기 신호 보기",
        "chips": ("배수", "습기", "진입"),
    },
    "monthly-rent-pressure-questions": {
        "theme": "theme-pressure",
        "scene": "pressure",
        "badge": "월세 착시",
        "label": "CASE",
        "headline": "5만↓ 손실↑",
        "subline": "싼 숫자 뒤 생활비를 꺼낸다",
        "chips": ("보증금", "통근", "생활비"),
    },
    "maintenance-fee-opaque-rent": {
        "theme": "theme-fee",
        "scene": "fee",
        "badge": "관리비 블랙박스",
        "label": "CASE",
        "headline": "+α 고정비",
        "subline": "월세 옆 빈칸을 열어 본다",
        "chips": ("월세", "공용", "계절비"),
    },
    "dongne-signal-framework": {
        "theme": "theme-filter",
        "scene": "filter",
        "badge": "후보 필터",
        "label": "CASE",
        "headline": "저장 말고 삭제",
        "subline": "후보 과잉을 3곳으로 줄인다",
        "chips": ("예산", "통근", "생활권"),
    },
    "commute-fatigue-neighborhood-check": {
        "theme": "theme-commute",
        "scene": "commute",
        "badge": "출근길 함정",
        "label": "CASE",
        "headline": "35분→50분",
        "subline": "앱 시간 말고 몸이 기억하는 시간",
        "chips": ("앱", "환승", "마지막 도보"),
    },
    "cafe-contract-risk": {
        "theme": "theme-cafe",
        "scene": "cafe",
        "badge": "상권 현장",
        "label": "CASE",
        "headline": "사람≠손님",
        "subline": "유동인구가 매출로 바뀌는지 본다",
        "chips": ("유동", "컵", "경쟁점"),
    },
    "after-work-neighborhood-check": {
        "theme": "theme-night",
        "scene": "night",
        "badge": "밤길 수사",
        "label": "CASE",
        "headline": "낮사진 사기",
        "subline": "방보다 귀가 장면을 먼저 본다",
        "chips": ("출구", "골목", "소음"),
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
      <span class="funnel"></span><span class="visual-checklist"><i>{c0}</i><i>{c1}</i><i>{c2}</i></span>
      <span class="reject-card">삭제</span><span class="keep-card">보류</span>
    </span>'''


def radar_article_card(a: dict) -> str:
    tags = taxonomy_links(a.get("tags") or [], "tag pale", limit=3)
    category = taxonomy_link(a.get("category"), "tag")
    date = parse_dt(a.get("date")).strftime("%m.%d")
    metric = traffic_badge(a["path"])
    desc = short_text(a.get("description") or "", 84)
    suspicion = short_text(a.get("radar_suspicion") or "", 58)
    visual = radar_card_visual(a)
    theme = visual["theme"]
    scene = visual["scene"]
    chips = visual["chips"]
    thumb = a.get("image_url") or visual.get("image_url") or visual.get("image") or ""
    thumb_class = "has-ai-thumb" if thumb else "has-css-thumb"
    thumb_img = f'<img class="radar-card-image" src="{esc(thumb)}" alt="" loading="eager" decoding="async" aria-hidden="true" />' if thumb else ""
    thumb_art = "" if thumb else f'''<span class="radar-thumb-art" aria-hidden="true">
      {radar_scene_markup(scene, chips)}
    </span>'''
    hook = f'<p class="radar-card-hook">오늘의 의심 · {esc(suspicion)}</p>' if suspicion else ""
    return f'''<article class="list-card radar-card {theme}">
  <a class="radar-card-visual {thumb_class} scene-{esc(scene)}" href="{esc(a['path'])}" aria-label="{esc(a['title'])}">
    {thumb_img}
    <span class="radar-thumb-label">{esc(visual['label'])}</span>
    <strong class="radar-thumb-title">{esc(visual['headline'])}</strong>
    <span class="radar-thumb-subline">{esc(visual['subline'])}</span>
    {thumb_art}
    <span class="radar-card-badge">{esc(visual['badge'])}</span>
  </a>
  <div class="radar-card-body">
    <div class="card-meta">{category}<time datetime="{esc(a.get('date'))}">{date}</time>{metric}</div>
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


def _radar_joined_text(article: dict) -> str:
    return " ".join([
        str(article.get("slug") or ""),
        str(article.get("title") or ""),
        str(article.get("description") or ""),
        " ".join(str(tag) for tag in (article.get("tags") or [])),
    ])


def _radar_primary_photo(article: dict) -> str:
    for item in article.get("field_examples") or []:
        if isinstance(item, dict) and item.get("image_url"):
            return str(item.get("image_url"))
    return str(article.get("image_url") or "")


def _radar_scene_profile(article: dict) -> dict[str, object]:
    joined = _radar_joined_text(article)
    slug = str(article.get("slug") or "")
    if any(token in joined for token in ("버스정류장", "정류장", "bus-stop")):
        scenes = [
            ("예시 장면 A", "아침 8시 정류장 앞 대기열이 현관·창문 쪽으로 밀려오는지 봅니다.", "아침 8시", "출근 대기열"),
            ("예시 장면 B", "밤 10시 버스 불빛·정차음·사람 시선이 집 안까지 들어오는지 상상합니다.", "밤 10시", "불빛과 소리"),
            ("예시 장면 C", "정류장 바로 앞 후보와 한 블록 안쪽 후보의 한 달 피로를 비교합니다.", "비교", "가깝지만 피곤"),
        ]
        scan_labels = ["정류장", "현관", "창문", "대기열", "소음"]
        good = "대기 공간과 생활 공간이 자연스럽게 분리되고, 창문 방향으로 시선이 오래 머물지 않습니다."
        bad = "정류장이 공공 대기실처럼 현관·창문 앞까지 밀고 들어오면 편의보다 피로가 큽니다."
    elif any(token in joined for token in ("카페", "상가", "권리", "상권", "유동", "cafe")):
        scenes = [
            ("예시 장면 A", "사람은 많지만 컵을 든 사람이 빠져나가는 길인지 봅니다.", "횡단보도 3분", "유동 ≠ 결제"),
            ("예시 장면 B", "문 앞 대기줄이 생겨도 옆 가게로 새는 동선인지 봅니다.", "입구 1분", "대기열"),
            ("예시 장면 C", "반경 50m 안 경쟁점의 메뉴·가격·좌석수를 같이 적습니다.", "경쟁점", "가격 그림자"),
        ]
        scan_labels = ["유동", "입구", "메뉴", "경쟁점", "회전"]
        good = "손님이 멈추고, 메뉴판을 보고, 다시 들어오는 장면이 반복됩니다."
        bad = "사람은 지나가지만 시선·대기·재방문 흔적이 없으면 유동인구 착시입니다."
    elif any(token in joined for token in ("관리비", "고정비", "총액", "maintenance-fee")) or "monthly-rent" in slug:
        scenes = [
            ("예시 장면 A", "월세 숫자 옆에 관리비·교통비·계절비를 한 줄로 붙입니다.", "총액", "월 고정비"),
            ("예시 장면 B", "관리비 항목표에서 공용전기·청소·수선비의 빈칸을 찾습니다.", "고지서", "빈칸"),
            ("예시 장면 C", "싼 집 후보와 가까운 집 후보의 한 달 피로비를 비교합니다.", "비교", "싸지만 먼 집"),
        ]
        scan_labels = ["월세", "관리비", "교통비", "계절비", "총액"]
        good = "가격표 밖 비용까지 적어도 감당 가능한 월 총액이 보입니다."
        bad = "월세만 싸고 관리비·교통비·계절비가 흐리면 계약 후 비용이 튑니다."
    elif any(token in joined for token in ("엘리베이터", "계단", "4층", "stair")):
        scenes = [
            ("예시 장면 A", "현관에서 4층 문 앞까지 장바구니를 든 채 올라가는 장면을 떠올립니다.", "4층", "매일 계단"),
            ("예시 장면 B", "택배·생수·이삿짐이 계단참에서 막히는 구간을 확인합니다.", "짐", "무게 피로"),
            ("예시 장면 C", "비 오는 날 미끄러운 계단과 조명 꺼진 계단참을 같이 봅니다.", "밤/비", "안전"),
        ]
        scan_labels = ["현관", "계단참", "3층", "4층", "짐"]
        good = "계단 폭·조명·난간·택배 위치가 매일 오르내릴 수 있는 수준으로 설명됩니다."
        bad = "낮에는 괜찮아 보여도 짐·비·밤이 겹치면 4층 피로가 급격히 커집니다."
    elif any(token in joined for token in ("공동현관", "우편함", "게시판", "관리 신호", "shared-entrance")):
        scenes = [
            ("예시 장면 A", "공동현관 바닥·우편함·게시판이 방치됐는지 30초 안에 봅니다.", "입구", "관리 신호"),
            ("예시 장면 B", "분리수거장과 택배가 현관 앞 동선을 막는지 확인합니다.", "동선", "쌓임"),
            ("예시 장면 C", "CCTV·조명·잠금장치가 실제로 생활 공간을 지켜 주는지 봅니다.", "보안", "안심"),
        ]
        scan_labels = ["현관", "우편함", "게시판", "택배", "조명"]
        good = "입구의 질서와 안내가 최근까지 관리된 흔적을 보여 줍니다."
        bad = "현관 앞 방치물이 일상 동선을 막으면 관리 피로가 집 안으로 들어옵니다."
    elif any(token in joined for token in ("비 오는", "비오는", "배수", "rainy")):
        scenes = [
            ("예시 장면 A", "비 오는 날 현관 앞 물고임과 배수구 방향을 봅니다.", "우천", "물길"),
            ("예시 장면 B", "우산을 접고 들어올 때 신발장·엘리베이터 앞이 젖는지 봅니다.", "현관", "젖은 동선"),
            ("예시 장면 C", "차도 물튀김과 보행자 우회 동선을 함께 비교합니다.", "보도", "튀김"),
        ]
        scan_labels = ["물길", "배수구", "현관", "보도", "튀김"]
        good = "비가 와도 물길·보행·현관 진입이 자연스럽게 분리됩니다."
        bad = "맑은 날 사진에는 안 보이던 물고임·튀김·우회가 반복되면 보류합니다."
    elif any(token in joined for token in ("1층", "반지하", "ground-floor")):
        scenes = [
            ("예시 장면 A", "보도에서 창문까지 시선 높이가 바로 맞는지 확인합니다.", "창문", "시선 거리"),
            ("예시 장면 B", "주차장·분리수거장·출입문 소리가 방 쪽으로 모이는지 듣습니다.", "소음", "생활 소리"),
            ("예시 장면 C", "환기·습기·채광을 낮과 밤 기준으로 나눠 봅니다.", "환기", "습기"),
        ]
        scan_labels = ["창문", "보도", "주차", "환기", "시선"]
        good = "시선·소리·습기가 한 방향으로 몰리지 않고 생활 공간이 분리됩니다."
        bad = "싸고 편해 보여도 창문 앞 시선과 주차 소리가 매일 반복되면 피로가 큽니다."
    elif any(token in joined for token in ("아침", "등교", "수거", "morning")):
        scenes = [
            ("예시 장면 A", "아침 8시 등교·출근·쓰레기 수거 동선이 겹치는지 봅니다.", "08시", "동선 충돌"),
            ("예시 장면 B", "엘리베이터·현관·골목에서 사람이 멈추는 병목을 찾습니다.", "병목", "기다림"),
            ("예시 장면 C", "아이들·차량·수거차가 동시에 움직일 때 소리 방향을 듣습니다.", "소음", "아침 피로"),
        ]
        scan_labels = ["등교", "수거", "출근", "현관", "소음"]
        good = "아침 혼잡이 짧게 지나가고 집 앞 병목으로 남지 않습니다."
        bad = "출근 전 20분마다 사람·차·수거 소리가 한꺼번에 겹치면 피로가 쌓입니다."
    elif any(token in joined for token in ("밤", "소음", "골목", "퇴근", "역", "night", "after-work", "station-to-home")):
        scenes = [
            ("예시 장면 A", "역 출구부터 집 문 앞까지 불 꺼지는 구간을 표시합니다.", "밤길 지도", "어두운 7분"),
            ("예시 장면 B", "창문을 열고 배달 오토바이·술집·차량 소리 방향을 듣습니다.", "22시", "소리 방향"),
            ("예시 장면 C", "낮 사진에서 안 보이는 우회길·큰길 복귀 동선을 찾습니다.", "우회", "돌아가는 길"),
        ]
        scan_labels = ["출구", "큰길", "골목", "입구", "소음"]
        good = "늦은 시간에도 큰길 복귀가 쉽고, 소리·시선·조명이 설명 가능합니다."
        bad = "낮에는 멀쩡하지만 밤에는 골목·소음·우회가 한꺼번에 늘어납니다."
    else:
        scenes = [
            ("예시 장면 A", "후보 집 앞 30초 사진처럼 현관·게시판·우편함 질서를 봅니다.", "입구", "관리 신호"),
            ("예시 장면 B", "집에서 역·편의점·분리수거장까지 매일 걸을 선을 그립니다.", "동선", "반복 루트"),
            ("예시 장면 C", "좋아 보이는 조건 옆에 계약 후 매일 겪을 반례를 붙입니다.", "비교", "좋음 vs 피곤"),
        ]
        scan_labels = ["입구", "큰길", "편의점", "분리수거", "소음"]
        good = "좋은 조건과 불편한 반복 장면을 한 화면에서 같이 설명할 수 있습니다."
        bad = "사진상 장점만 있고, 실제로 매일 부딪힐 장면이 비어 있으면 보류합니다."
    return {"scenes": scenes, "scan_labels": scan_labels, "good": good, "bad": bad}


def radar_experience_block(article: dict) -> str:
    target = short_text(article.get("target_audience") or "계약 전 후보 동네를 빠르게 거르고 싶은 독자", 86)
    suspicion = short_text(article.get("radar_suspicion") or article.get("description") or "", 96)
    mission = short_text(article.get("field_mission") or "표를 외우지 말고 현장에서 의심할 장면과 질문을 먼저 잡습니다.", 96)
    headings = article_headings(article.get("body_html") or "")
    toc = "".join(f'<li><span>{i:02d}</span>{esc(label)}</li>' for i, label in enumerate(headings, start=1))
    if not toc:
        toc = '<li><span>01</span>오늘의 의심을 먼저 보고 본문으로 들어갑니다.</li>'
    profile = _radar_scene_profile(article)
    scan_labels = list(profile["scan_labels"])[:5]
    photo = _radar_primary_photo(article)
    map_nodes = "".join(
        f'<span class="map-node node-{i}"><b>{i}</b><em>{esc(label)}</em></span>'
        for i, label in enumerate(scan_labels, start=1)
    )
    if photo:
        scan_visual = f'''<div class="radar-map photo-scan" aria-label="AI 현장 예시 이미지로 보는 확인 순서">
      <img class="scan-photo" src="{esc(photo)}" alt="{esc(article.get('title') or '동네 레이더')} AI 현장 예시 이미지" loading="eager" decoding="async" fetchpriority="high" />
      <span class="map-label">AI 현장 예시 · 1→5 확인 순서</span>
      {map_nodes}
    </div>'''
    else:
        scan_visual = f'''<div class="radar-map photo-scan missing-photo" aria-label="AI 현장 예시 이미지 필요">
      <span class="map-label">AI 현장 예시 이미지 필요</span>
      {map_nodes}
    </div>'''
    return f'''<section class="radar-experience-grid" aria-label="본문 전 시각 요약">
  <div class="radar-map-card">
    <p class="eyebrow">Visual Scan</p>
    <h2>계약 전 먼저 볼 AI 현장 장면</h2>
    <p>좋은 동네를 찾는 척하지 말고, 계약 뒤 매일 반복될 불편을 실제 장면처럼 먼저 떠올립니다.</p>
    {scan_visual}
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


def radar_example_gallery(article: dict) -> str:
    profile = _radar_scene_profile(article)
    thumbnail_photo = str(article.get("image_url") or "")
    raw_examples = article.get("field_examples") or []
    examples: list[dict[str, str]] = []
    seen_images: set[str] = set()
    for item in raw_examples:
        if not isinstance(item, dict):
            continue
        image_url = str(item.get("image_url") or "")
        if not image_url or image_url == thumbnail_photo or "/thumbs/" in image_url or image_url in seen_images:
            continue
        seen_images.add(image_url)
        examples.append({
            "label": str(item.get("label") or f"AI 현장 {chr(65 + len(examples))}"),
            "description": str(item.get("description") or "현장에서 먼저 떠올릴 반복 장면입니다."),
            "badge": str(item.get("badge") or "AI 예시"),
            "title": str(item.get("title") or item.get("punch") or "현장 장면"),
            "image_url": image_url,
            "alt": str(item.get("alt") or item.get("title") or article.get("title") or "동네 레이더 AI 예시 장면"),
        })
    if len(examples) < 3:
        return ""
    cards = []
    for idx, item in enumerate(examples[:3], start=1):
        image_url = item.get("image_url") or ""
        img_html = ""
        frame_class = "scene-frame photo-frame" if image_url else "scene-frame missing-photo"
        if image_url:
            img_html = f'<img class="scene-photo" src="{esc(image_url)}" alt="{esc(item.get("alt") or item.get("title") or "AI 예시 장면")}" loading="eager" decoding="async" />'
        cards.append(f'''<article class="example-scene-card scene-{idx}">
      <div class="{frame_class}">
        {img_html}
        <span class="scene-pin pin-a">{idx}</span>
        <span class="scene-badge">{esc(item.get('badge') or 'AI 예시')}</span>
      </div>
      <div class="scene-copy"><span>{esc(item.get('label') or f'예시 장면 {idx}')}</span><strong>{esc(item.get('title') or '현장 장면')}</strong><p>{esc(item.get('description') or '')}</p></div>
    </article>''')
    question = short_text(article.get("field_mission") or article.get("radar_suspicion") or article.get("description") or "현장에서 20분 안에 직접 확인할 장면을 먼저 정합니다.", 110)
    return f'''<section class="radar-example-gallery" aria-label="본문 예시 이미지와 현장 시각화">
  <div class="example-gallery-head">
    <p class="eyebrow">Field Examples</p>
    <h2>글을 읽기 전에 먼저 볼 AI 예시 장면</h2>
    <p>아래 이미지는 실제 매물이 아니라, 계약 뒤 매일 반복될 장면을 먼저 떠올리기 위한 AI 현장 예시입니다.</p>
  </div>
  <div class="example-scene-grid">
    {''.join(cards)}
  </div>
  <div class="radar-situation-strip">
    <article><span>좋은 신호</span><p>{esc(profile['good'])}</p></article>
    <article><span>위험한 반례</span><p>{esc(profile['bad'])}</p></article>
    <article class="field-question"><span>현장 질문</span><p>{esc(question)}</p></article>
  </div>
</section>
'''


def deal_placeholder_icon(article: dict) -> str:
    haystack = " ".join(
        str(part or "")
        for part in [
            article.get("title"),
            article.get("category"),
            article.get("description"),
            " ".join(article.get("tags") or []),
        ]
    ).lower()
    icon_rules = [
        (("제습", "습기", "장마"), "💧"),
        (("공기청정", "필터", "공기"), "🌬️"),
        (("스피커", "블루투스", "마샬", "jbl"), "🔊"),
        (("헤드셋", "헤드폰", "이어폰", "anc"), "🎧"),
        (("의자", "재택", "허리"), "🪑"),
        (("로봇청소", "청소기", "무선청소"), "🧹"),
        (("키보드", "기계식"), "⌨️"),
        (("모니터", "조명", "데스크"), "🖥️"),
        (("주방", "가전"), "🍳"),
        (("뷰티", "케어", "선물"), "✨"),
    ]
    for terms, icon in icon_rules:
        if any(term in haystack for term in terms):
            return icon
    return "🛒"


def deal_card(a: dict, rank: int | None = None) -> str:
    img = a.get("image_url") or ""
    card_class = "deal-card" if img else "deal-card text-card"
    if rank:
        card_class += " ranked"
    date = parse_dt(a.get("date")).strftime("%m.%d")
    metric = traffic_badge(a["path"])
    category = deal_category_link(a.get("category"), "meta-link")
    deal_url = a.get("primary_deal_url") or ""
    external = ""
    if deal_url:
        external = f'<a class="deal-price-link" href="{esc(deal_url)}" target="_blank" rel="sponsored nofollow noopener">가격 확인</a>'
    rank_badge = f'<span class="deal-rank">추천 {rank}</span>' if rank else ""
    if img:
        thumb = f'''<a class="deal-thumb" href="{esc(a['path'])}" aria-label="{esc(a['title'])}">
    <img src="{esc(img)}" alt="{esc(a['title'])} 대표 상품 이미지" loading="lazy" decoding="async" />
    <span class="deal-count">{esc(a.get('item_count_hint') or '비교글')}</span>
    {rank_badge}
  </a>'''
    else:
        thumb = f'''<a class="deal-text-badge" href="{esc(a['path'])}" aria-label="{esc(a['title'])}">
    <span class="deal-fallback-icon" aria-hidden="true">{esc(deal_placeholder_icon(a))}</span>
    <span class="deal-fallback-text">{esc(a.get('item_count_hint') or '비교글')}</span>
    {rank_badge}
  </a>'''
    price_hint = esc(a.get("price_hint") or "상세가는 상품 페이지에서 확인")
    return f'''<article class="{card_class}">
  {thumb}
  <div class="deal-body">
    <div class="deal-meta">{category}<time datetime="{esc(a.get('date'))}">{date}</time>{metric}</div>
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


def topic_result_card(article: dict, *, featured: bool = False) -> str:
    category = taxonomy_link(article.get("category"), "tag")
    date = parse_dt(article.get("date")).strftime("%m.%d")
    metric = traffic_badge(article["path"])
    tags = taxonomy_links(article.get("tags") or [], "tag pale", limit=2)
    desc_limit = 132 if featured else 96
    desc = short_text(article.get("description") or "", desc_limit)
    cta = "비교글 보기 →" if article.get("section") == "deals" else "레이더 열기 →"
    featured_class = " featured" if featured else ""
    return f'''<article class="topic-result-card{featured_class}">
  <div class="topic-result-meta">{category}<time datetime="{esc(article.get('date'))}">{date}</time>{metric}</div>
  <h2><a href="{esc(article['path'])}">{esc(article['title'])}</a></h2>
  <p>{esc(desc)}</p>
  <div class="tag-row">{tags}</div>
  <a class="text-link" href="{esc(article['path'])}">{esc(cta)}</a>
</article>'''


def topic_result_cards(articles: list[dict], empty: str, *, featured: bool = False, limit: int | None = None) -> str:
    selected = articles[:limit] if limit is not None else articles
    if not selected:
        return f'<article class="topic-result-card empty"><span class="tag">준비중</span><h2>{esc(empty)}</h2><p>새 글이 올라오면 이곳에서 바로 볼 수 있습니다.</p></article>'
    return "\n".join(topic_result_card(a, featured=featured) for a in selected)


def search_query_href(label: Any) -> str:
    text = str(label or "").strip()
    return f"/search/?q={quote(text, safe='')}"


def taxonomy_link(label: Any, class_name: str = "", aria_prefix: str = "검색") -> str:
    text = str(label or "").strip()
    if not text:
        return ""
    cls = f' class="{esc(class_name)}"' if class_name else ""
    aria = f' aria-label="{esc(f"{aria_prefix}: {text}")}"' if aria_prefix else ""
    return f'<a{cls} href="{esc(search_query_href(text))}"{aria}>{esc(text)}</a>'


def taxonomy_links(labels, class_name: str, *, limit: int | None = None, separator: str = " ") -> str:
    links: list[str] = []
    seen: set[str] = set()
    for raw in labels or []:
        text = str(raw or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        links.append(taxonomy_link(text, class_name))
        if limit is not None and len(links) >= limit:
            break
    return separator.join(links)


def category_strip_links(labels) -> str:
    return taxonomy_links(labels, "category-chip", separator="")


def related_search_chips(article: dict, *, limit: int = 6) -> str:
    labels: list[str] = []
    category = str(article.get("category") or "").strip()
    if category:
        labels.append(category)
    labels.extend(str(tag).strip() for tag in (article.get("tags") or []) if str(tag).strip())
    return taxonomy_links(labels, "search-chip", limit=limit)


def deal_category_chip_label(label: str) -> str:
    aliases = {
        "블루투스-스피커": "스피커",
        "게이밍-개발자-셋업": "책상·게임",
        "이어폰-헤드셋": "음향",
        "공기청정기-가전": "공기청정기",
        "로봇청소기-가전": "로봇청소기",
        "제습기-가전": "제습기",
        "오늘의딜": "오늘의 딜",
    }
    return aliases.get(label, label.replace("-가전", "").replace("-", "·"))


def deal_category_link(label: Any, class_name: str = "", aria_prefix: str = "검색") -> str:
    text = str(label or "").strip()
    if not text:
        return ""
    display = deal_category_chip_label(text)
    cls = f' class="{esc(class_name)}"' if class_name else ""
    aria = f' aria-label="{esc(f"{aria_prefix}: {text}")}"' if aria_prefix else ""
    return f'<a{cls} href="{esc(search_query_href(text))}"{aria}>{esc(display)}</a>'


def category_chips(articles: list[dict]) -> str:
    cats = []
    for a in articles:
        cat = str(a.get("category") or "").strip()
        if cat and cat not in cats:
            cats.append(cat)
    if not cats:
        return '<span class="category-chip">비교글 준비중</span>'
    links = []
    for cat in cats[:8]:
        links.append(deal_category_link(cat, "category-chip"))
    return "".join(links)


def search_form(
    placeholder: str = "상품명, 용도, 예산, 동네 키워드로 검색",
    helper: str = "쇼핑픽 상품명, 생활용품 용도, 동네·계약 키워드를 같이 찾습니다.",
) -> str:
    return f'''<form class="site-search" action="/search/" method="get" role="search">
  <label for="search-query">사이트 검색</label>
  <div class="search-row">
    <input id="search-query" name="q" type="search" placeholder="{esc(placeholder)}" autocomplete="off" />
    <button type="submit">검색</button>
  </div>
  <p class="muted">{esc(helper)}</p>
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
  <p class="lead">쇼핑픽 상품 비교글과 동네 레이더 글을 한 번에 검색합니다. 검색 결과는 브라우저에서만 처리됩니다.</p>
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


def shopping_room_kind(article: dict) -> tuple[str, str, str]:
    haystack = " ".join(
        [
            str(article.get("title") or ""),
            str(article.get("description") or ""),
            str(article.get("category") or ""),
            " ".join(str(t) for t in (article.get("tags") or [])),
        ]
    )
    cases = [
        (("제습", "공기청정", "필터", "장마", "습기"), "air", "침실 습도", "습기·필터"),
        (("모니터", "키보드", "의자", "책상", "재택", "개발자"), "desk", "책상 셋업", "자세·공간"),
        (("헤드폰", "헤드셋", "스피커", "ANC", "블루투스", "마샬", "보스"), "sound", "몰입존", "소리 장비"),
        (("청소기", "로봇", "스틱", "흡입", "먼지"), "clean", "거실 관리", "청소 루틴"),
        (("주방", "에어프라이", "전자레인지", "믹서", "밥솥"), "kitchen", "주방 코너", "생활가전"),
        (("뷰티", "퍼스널", "케어", "선물", "드라이", "칫솔"), "care", "욕실 선반", "선물·케어"),
    ]
    for terms, kind, scene, cue in cases:
        if any(term.lower() in haystack.lower() for term in terms):
            return kind, scene, cue
    return "daily", "생활 코너", "오늘 후보"


def shopping_room_title(article: dict) -> str:
    title = strip_tags(str(article.get("title") or ""))
    title = re.sub(r"^\s*2026\s*", "", title)
    title = re.sub(r"\s+[–-]\s+.*$", "", title)
    return short_text(title, 34)


def shopping_room_deals(deals: list[dict], limit: int = 6) -> list[dict]:
    prioritized = deals_by_growth_priority(deals)
    selected: list[dict] = []
    seen_kinds: set[str] = set()
    for article in prioritized:
        kind, _, _ = shopping_room_kind(article)
        if kind in seen_kinds:
            continue
        selected.append(article)
        seen_kinds.add(kind)
        if len(selected) >= limit:
            return selected
    selected_paths = {a.get("path") for a in selected}
    for article in prioritized:
        if article.get("path") in selected_paths:
            continue
        selected.append(article)
        selected_paths.add(article.get("path"))
        if len(selected) >= limit:
            break
    return selected


def shopping_room_scene(deals: list[dict]) -> str:
    items = shopping_room_deals(deals)
    if not items:
        return '''<aside class="shopping-room-card" aria-label="쇼핑픽 쇼룸">
  <div class="room-empty"><strong>쇼핑룸 준비중</strong><p>새 상품 비교글이 올라오면 이 방에 물건처럼 하나씩 붙습니다.</p></div>
</aside>'''
    toggles: list[str] = []
    markers: list[str] = []
    previews: list[str] = []
    for idx, article in enumerate(items, start=1):
        kind, scene, cue = shopping_room_kind(article)
        title = shopping_room_title(article)
        desc = short_text(article.get("description") or "", 74)
        checked = " checked" if idx == 1 else ""
        toggle_id = f"shopping-room-pick-{idx}"
        count = article.get("item_count_hint") or "비교글"
        deal_url = str(article.get("primary_deal_url") or "").strip()
        product_link = ""
        if deal_url:
            product_link = f'<a class="room-product-link" href="{esc(deal_url)}" target="_blank" rel="sponsored nofollow noopener">상품 바로가기</a>'
        toggles.append(f'<input class="room-toggle" type="radio" name="shopping-room-pick" id="{toggle_id}"{checked} />')
        markers.append(f'''<label class="room-product pos-{idx} kind-{kind}" for="{toggle_id}" aria-label="{esc(title)} 소개 보기">
      <span class="room-hit-area" aria-hidden="true"></span>
      <span class="room-pulse" aria-hidden="true"></span>
      <span class="room-pin" aria-hidden="true"></span>
      <span class="room-label"><strong>{esc(title)}</strong><small>{esc(cue)}</small></span>
    </label>''')
        previews.append(f'''<article class="room-preview preview-{idx}">
      <span class="tag pale">{esc(scene)} · {esc(count)}</span>
      <h3>{esc(title)}</h3>
      <p>{esc(desc)}</p>
      <div class="room-preview-actions">{product_link}<a class="text-link" href="{esc(article['path'])}">비교글 보기 →</a></div>
    </article>''')
    return f'''<aside class="shopping-room-card" aria-label="클릭해서 보는 쇼핑픽 룸">
  <div class="room-card-head">
    <span class="tag pale">AI 쇼핑룸</span>
    <strong>방 사진 속 상품을 눌러보세요</strong>
    <p>AI로 만든 생활공간 위에 쇼핑픽 후보 영역을 얹었습니다. 누르면 아래 비교글이 바로 바뀝니다.</p>
  </div>
  <div class="shopping-room-stage">
    {''.join(toggles)}
    <div class="room-visual">
      <img class="room-photo" src="/assets/deals/shopping-room-ai.webp" alt="쇼핑픽 후보를 고를 수 있는 생활공간 이미지" loading="eager" decoding="async" />
      {''.join(markers)}
    </div>
    <div class="room-previews" aria-live="polite">
      {''.join(previews)}
    </div>
  </div>
</aside>'''


def search_chip(label: str) -> str:
    return taxonomy_link(label, "search-chip")


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


def category_preview_links(articles: list[dict], empty_label: str = "비교글 준비중") -> str:
    if not articles:
        return f'<span class="category-hub-empty">{esc(empty_label)}</span>'
    return "\n".join(
        f'<a href="{esc(a["path"])}">{esc(short_text(a.get("title") or "", 36))}</a>'
        for a in articles[:2]
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
  <small>{esc(metric)} · {esc(deal_category_chip_label(str(article.get('category') or '')))}</small>
</li>''')
    return "\n".join(rows) or '<li class="muted">조회 데이터 수집 중</li>'


def deal_category_hubs(deals: list[dict]) -> str:
    grouped: dict[str, list[dict]] = {}
    for article in deals:
        category = str(article.get("category") or "기타 쇼핑픽").strip() or "기타 쇼핑픽"
        grouped.setdefault(category, []).append(article)
    cards = []
    for category in sorted(grouped, key=lambda c: (-len(grouped[c]), c)):
        articles = deals_by_growth_priority(grouped[category])
        count_label = f"{len(articles)}개"
        cards.append(f'''<article class="category-hub">
  <a class="category-hub-label" href="{esc(search_query_href(category))}" aria-label="{esc(f'{category} 비교글 보기')}">
    <span>{esc(deal_category_chip_label(category))}</span>
    <strong>{esc(count_label)}</strong>
  </a>
  <div class="category-hub-links">{category_preview_links(articles)}</div>
</article>''')
    return "\n".join(cards)


def topic_page_metas() -> list[dict]:
    pages: list[dict] = []
    for topic in TOPIC_HUBS:
        pages.append(
            {
                "path": f"/topics/{topic['slug']}/",
                "file": f"topics/{topic['slug']}/index.html",
                "title": topic["title"],
                "description": topic["description"],
                "priority": topic.get("priority", "0.76"),
                "type": "CollectionPage",
                "section": "topics",
                "tags": topic.get("keywords") or [],
                "topic": topic,
            }
        )
    return pages


def topic_haystack(article: dict) -> str:
    return " ".join(
        [
            str(article.get("title") or ""),
            str(article.get("description") or ""),
            str(article.get("category") or ""),
            " ".join(str(t) for t in (article.get("tags") or [])),
            strip_tags(str(article.get("body_html") or ""))[:1800],
        ]
    ).lower()


def topic_matches_article(topic: dict, article: dict) -> bool:
    haystack = topic_haystack(article)
    terms = [str(x).lower() for x in (topic.get("keywords") or []) + (topic.get("queries") or []) if str(x).strip()]
    return any(term in haystack for term in terms)


def topic_related_articles(topic: dict, deals: list[dict], radar: list[dict], *, limit: int = 8) -> list[dict]:
    articles = radar + deals
    include_paths = [str(path) for path in (topic.get("include_paths") or []) if str(path).strip()]
    if include_paths:
        by_path = {str(a.get("path") or ""): a for a in articles}
        return [by_path[path] for path in include_paths if path in by_path][:limit]
    matches = [a for a in articles if topic_matches_article(topic, a)]
    primary = topic.get("primary_section")
    if not matches and primary == "deals":
        matches = deals_by_growth_priority(deals)[:limit]
    if not matches and primary == "radar":
        matches = radar[:limit]
    return sorted(
        matches,
        key=lambda a: (
            1 if a.get("section") == primary else 0,
            article_views(a),
            parse_dt(a.get("date")).timestamp(),
        ),
        reverse=True,
    )[:limit]


def topic_list_links(articles: list[dict], empty_label: str = "관련 글 준비중") -> str:
    if not articles:
        return f'<li class="muted">{esc(empty_label)}</li>'
    return "\n".join(
        f'<li><a href="{esc(a["path"])}">{esc(short_text(a.get("title") or "", 42))}</a></li>'
        for a in articles[:3]
    )


def topic_card(topic: dict, deals: list[dict], radar: list[dict]) -> str:
    related = topic_related_articles(topic, deals, radar, limit=4)
    chips = "".join(search_chip(q) for q in topic.get("queries") or [])
    path = f"/topics/{topic['slug']}/"
    return f'''<article class="topic-card">
  <div class="topic-card-head">
    <span class="tag pale">{esc(topic['label'])}</span>
    <strong>{len(related)}개 연결 글</strong>
  </div>
  <h2><a href="{esc(path)}">{esc(topic['title'])}</a></h2>
  <p class="topic-intent">{esc(topic['intent'])}</p>
  <p>{esc(topic['description'])}</p>
  <div class="search-chip-row">{chips}</div>
  <ul class="mini-link-list">{topic_list_links(related)}</ul>
  <a class="text-link" href="{esc(path)}">주제 열기 →</a>
</article>'''


def topic_cards(deals: list[dict], radar: list[dict]) -> str:
    return "\n".join(topic_card(topic, deals, radar) for topic in TOPIC_HUBS)


CONTRACT_CHECK_ROUTES = [
    {
        "slug": "jeonwolse-contract-check",
        "label": "전월세 체크",
        "title": "전월세 계약 전 글 목록",
        "description": "월세·전세·이사 후보를 바로 개별 글로 보내지 않고, 관리비·통근·밤길·공용부·비 오는 날 신호를 먼저 훑는 입구입니다.",
        "cta": "전월세 체크 글 목록 →",
    },
    {
        "slug": "cafe-commercial-lease-risk",
        "label": "상가 계약 체크",
        "title": "상가·카페 계약 전 글 목록",
        "description": "유동인구 착시, 경쟁 밀도, 권리금 회수, 임대료 압박처럼 상가 계약 전에 따로 봐야 할 리스크 입구입니다.",
        "cta": "상가 계약 체크 글 목록 →",
    },
]


def topic_by_slug(slug: str) -> dict:
    for topic in TOPIC_HUBS:
        if topic.get("slug") == slug:
            return topic
    return {}


def contract_check_route_cards(radar: list[dict]) -> str:
    cards = []
    for index, route in enumerate(CONTRACT_CHECK_ROUTES, start=1):
        topic = topic_by_slug(route["slug"])
        count = len(topic_related_articles(topic, [], radar, limit=99)) if topic else 0
        href = f"/topics/{route['slug']}/"
        cards.append(f'''<article class="card accent-{'blue' if index == 1 else 'green'} contract-route-card">
  <span class="tag">{esc(route['label'])}</span>
  <h2><a href="{esc(href)}">{esc(route['title'])}</a></h2>
  <p>{esc(route['description'])}</p>
  <strong class="route-count">현재 {count}개 연결 글</strong>
  <a href="{esc(href)}">{esc(route['cta'])}</a>
</article>''')
    return "\n".join(cards)


def topics_body(deals: list[dict], radar: list[dict]) -> str:
    return f'''
<section class="page-hero compact">
  <p class="eyebrow">주제별 보기</p>
  <h1>월세·전세·상가·생활상품을 주제별로 보기</h1>
  <p class="lead">검색창에 뭘 쳐야 할지 애매할 때 먼저 들어오는 길입니다. 월세·전세·상가·생활상품처럼 독자가 고르는 주제로 글을 묶었습니다.</p>
  <div class="hero-actions">
    <a class="button primary" href="#topic-hubs">주제 카드 보기</a>
    <a class="button" href="/search/">직접 검색하기</a>
    <a class="button" href="/guides/">읽는 순서</a>
  </div>
</section>
<section class="panel soft search-panel">
  {search_form("예: 월세 계약 전 체크, 전세 밤길, 카페 상가 계약, 제습기")}
</section>
<section class="panel topic-test-plan">
  <span class="tag pale">Traffic Test</span>
  <h2>테스트 기준</h2>
  <ul class="topic-metrics">
    <li><strong>색인:</strong> /topics/와 {len(TOPIC_HUBS)}개 주제 페이지가 sitemap·검색 인덱스에 들어가는지 확인</li>
    <li><strong>유입:</strong> 전월세·월세·전세·상가·생활가전 주제별 노출/클릭을 주 단위로 비교</li>
    <li><strong>전환:</strong> 동네 레이더 글은 체류·다음 글 이동, 쇼핑픽은 상품 페이지 클릭을 봄</li>
  </ul>
</section>
<section id="topic-hubs" class="landing-section">
  <div class="section-title"><h2>주제별 보기 {len(TOPIC_HUBS)}개</h2><p>현재 글을 전월세·월세·전세·상가·생활상품처럼 독자가 고르는 주제별로 다시 묶었습니다.</p></div>
  <div class="topic-grid">{topic_cards(deals, radar)}</div>
</section>
'''


def topic_page_body(topic: dict, deals: list[dict], radar: list[dict]) -> str:
    articles = topic_related_articles(topic, deals, radar, limit=10)
    chips = "".join(search_chip(q) for q in topic.get("queries") or [])
    keyword_chips = category_strip_links(topic.get("keywords") or [])
    article_paths = {a.get("path") for a in articles}
    secondary = [a for a in (radar + deals) if a.get("path") not in article_paths][:4]
    secondary_html = topic_result_cards(secondary, "다음 연결 글 준비중", limit=4)
    first_query = str((topic.get("queries") or [topic.get("label") or ""])[0])
    return f'''
<section class="page-hero compact">
  <p class="eyebrow">주제별 보기 · {esc(topic['label'])}</p>
  <h1>{esc(topic['title'])}</h1>
  <p class="lead">{esc(topic['description'])}</p>
  <div class="hero-actions">
    <a class="button primary" href="#related-articles">연결 글 보기</a>
    <a class="button" href="{search_query_href(first_query)}">이 주제로 검색</a>
  </div>
</section>
<section class="panel soft topic-brief">
  <span class="tag pale">검색 의도</span>
  <h2>{esc(topic['intent'])}</h2>
  <div class="search-chip-row">{chips}</div>
  <div class="category-strip">{keyword_chips}</div>
</section>
<section id="related-articles" class="article-list topic-article-list topic-featured-list">
  <div class="section-title"><h2>먼저 볼 연결 글</h2><p>이 주제와 가장 가까운 공개 글만 넓게 보여줍니다.</p></div>
  {topic_result_cards(articles, "연결 글 준비중", featured=True, limit=3)}
</section>
<section class="panel topic-followup">
  <h2>추가로 확인할 체크포인트</h2>
  <ol>
    <li>유동인구가 실제 결제로 이어지는 시간대인지 확인</li>
    <li>권리금·임대료·경쟁점 밀도를 같은 표에서 비교</li>
    <li>계약 전 현장에서 다시 물어볼 질문을 먼저 정리</li>
  </ol>
</section>
<section class="article-list topic-article-list topic-secondary-list">
  <div class="section-title"><h2>같이 볼 만한 글</h2><p>같은 방문자가 이어서 볼 수 있는 글만 간단히 묶었습니다.</p></div>
  {secondary_html}
</section>
'''


def deal_article_product_names(article: dict, limit: int = 5) -> list[str]:
    body = article.get("body_html") or ""
    names: list[str] = []
    skip_terms = (
        "서론",
        "결론",
        "마무리",
        "제품별",
        "핵심",
        "비교표",
        "구매",
        "추천 기준",
        "선택 기준",
        "체크",
        "한눈",
        "자주 묻는",
        "FAQ",
        "후보 제외",
        "정확 매칭",
        "블로그 최신",
        "같이 볼",
        "함께 보면",
        "다음에",
    )
    for raw in re.findall(r'<h[23][^>]*>(.*?)</h[23]>', body, flags=re.I | re.S):
        name = strip_tags(raw)
        name = re.sub(r"^\s*(?:\d+\s*[.)]|[①-⑩]|BEST\s*\d+\s*[:.-]?)\s*", "", name, flags=re.I)
        name = re.sub(r"\s+(?:활용도 체크|구매 포인트|추천 이유|장단점|비교|후기).*$", "", name).strip()
        if not name or "?" in name or name.endswith(("인가요", "나요", "까요", "가요")) or any(term in name for term in skip_terms):
            continue
        if name not in names:
            names.append(short_text(name, 46))
        if len(names) >= limit:
            break
    return names


def specific_product_anchor_label(raw_label: str) -> str:
    label = strip_tags(raw_label or "")
    label = re.sub(r"^[\s🛒▶️👉]+", "", label).strip()
    label = re.sub(r"\s*(?:가격|최저가|옵션|후기)\s*(?:확인|보기|확인하기).*$", "", label).strip()
    generic = {
        "",
        "상품 페이지에서 확인",
        "상품 페이지에서 옵션·후기 확인하기",
        "상품 페이지 확인",
        "가격 확인하기",
        "자세히 보기",
    }
    if label in generic or len(label) < 3:
        return ""
    return short_text(label, 42)


def clean_product_link_label(raw_label: str, fallback: str) -> str:
    return specific_product_anchor_label(raw_label) or short_text(fallback or "후보 상품", 42)


def deal_article_product_links(article: dict, limit: int = 5) -> list[dict[str, str]]:
    """Extract de-duplicated Coupang candidate links for the above-the-fold deal path."""
    body = article.get("body_html") or ""
    fallbacks = deal_article_product_names(article, limit=limit)
    links: list[dict[str, str]] = []
    by_url: dict[str, dict[str, str]] = {}
    for match in ANCHOR_RE.finditer(body):
        href_match = HREF_ATTR_RE.search(" " + (match.group("attrs") or ""))
        if not href_match:
            continue
        url = clean_url(href_match.group(2))
        if not url or "coupang.com" not in url.lower():
            continue
        fallback = fallbacks[min(len(links), max(0, len(fallbacks) - 1))] if fallbacks else "후보 상품"
        label = clean_product_link_label(match.group("label"), fallback)
        current = by_url.get(url)
        if current:
            specific_label = specific_product_anchor_label(match.group("label"))
            if specific_label:
                current["label"] = specific_label
            continue
        item = {"label": label, "url": url}
        by_url[url] = item
        links.append(item)
        if len(links) >= limit:
            break
    return links


def deal_article_product_link_block(article: dict) -> str:
    links = deal_article_product_links(article)
    if not links:
        return ""
    items = []
    for item in links:
        items.append(
            f'<li><a class="quick-product-link" href="{esc(item["url"])}" target="_blank" rel="sponsored nofollow noopener">'
            f'<span>{esc(item["label"])}</span><strong>쿠팡에서 보기</strong></a></li>'
        )
    return f'''<div class="quick-product-links" aria-label="쿠팡 상품 페이지 바로가기">
    <h3>마음에 드는 후보는 바로 확인</h3>
    <p>쿠팡 파트너스 링크입니다. 가격·배송·후기는 쿠팡 상품 페이지에서 다시 확인하세요.</p>
    <ul>{''.join(items)}</ul>
  </div>'''


def deal_article_quick_block(article: dict) -> str:
    products = deal_article_product_names(article)
    product_items = "".join(f"<li>{esc(name)}</li>" for name in products)
    if not product_items:
        product_items = "<li>본문에서 후보별 장단점과 가격대를 확인하세요.</li>"
    product_links = deal_article_product_link_block(article)
    external = ""
    if not product_links and article.get("primary_deal_url"):
        external = f'<a class="deal-button ghost" href="{esc(article["primary_deal_url"])}" target="_blank" rel="sponsored nofollow noopener">상품 페이지 확인</a>'
    category_link = taxonomy_link(article.get("category") or "쇼핑픽", "quick-fact-link")
    return f'''<section class="deal-quick-box" aria-label="쇼핑픽 빠른 결론">
  <div class="quick-verdict">
    <span class="tag">3분 컷 비교</span>
    <h2>장바구니 넣기 전 이렇게 판단하세요</h2>
    <p>{esc(short_text(article.get('description') or '', 150))}</p>
    <p class="quick-note">사지 말아야 할 이유가 먼저 보이면 오늘은 보류해도 괜찮습니다.</p>
  </div>
  <div class="quick-facts" aria-label="핵심 정보">
    <div><strong>{esc(article.get('item_count_hint') or '비교글')}</strong><span>후보 수</span></div>
    <div><strong>{esc(article.get('price_hint') or '상세 확인')}</strong><span>가격 기준</span></div>
    <div><strong>{category_link}</strong><span>카테고리</span></div>
  </div>
  <div class="quick-products">
    <h3>본문에서 비교하는 후보</h3>
    <ol>{product_items}</ol>
  </div>
  {product_links}
  <div class="deal-actions quick-actions">
    <a class="deal-button primary" href="#article-body">비교 내용 바로 보기</a>{external}
  </div>
</section>'''


SEOUL_COMMERCIAL_AREAS = json.loads(r'''
{
  "version": "2026-05-seoul-density-mvp",
  "generated_at": "2026-05-06T02:00:00+09:00",
  "radius_m": 650,
  "source_summary": "공개 POI를 빌드 시점에 집계한 정적 데이터입니다. 인구밀도는 공식 통계 연동 전까지 구별 편집 지수로 표시하며, 비밀 키는 브라우저에 배포하지 않습니다.",
  "categories": {
    "cafe": "카페",
    "food": "음식점·주점",
    "convenience": "편의·마트",
    "beauty": "미용·뷰티",
    "clinic": "병원·약국",
    "academy": "학원·학교",
    "retail": "소매 전체",
    "population": "인구밀도"
  },
  "stations": [
    {
      "id": "magoknaru",
      "name": "마곡나루역",
      "district": "강서구",
      "dong": "마곡동",
      "lat": 37.5667,
      "lng": 126.8275,
      "population_density_index": 58,
      "population_density_label": "중간",
      "rent_pressure_index": 65,
      "radius_m": 650,
      "counts": {
        "cafe": 2,
        "food": 7,
        "convenience": 5,
        "beauty": 113,
        "clinic": 0,
        "academy": 2,
        "retail": 120
      },
      "total_poi_count": 129,
      "map_x": 13.6,
      "map_y": 17.9,
      "commercial_density_index": 8,
      "source_note": "OSM Overpass public POI 650m precompute + district density editorial index; KOSIS build-time replacement ready",
      "commercial_density_label": "낮음",
      "top_industries": [
        "retail",
        "beauty",
        "food"
      ],
      "default_take": "주변 POI가 적게 잡히는 후보지입니다. 임대료가 낮아도 유입을 직접 만들 수 있는 업종인지 확인해야 합니다."
    },
    {
      "id": "hongdae",
      "name": "홍대입구역",
      "district": "마포구",
      "dong": "서교동",
      "lat": 37.5572,
      "lng": 126.9245,
      "population_density_index": 68,
      "population_density_label": "높음",
      "rent_pressure_index": 82,
      "radius_m": 650,
      "counts": {
        "cafe": 165,
        "food": 575,
        "convenience": 59,
        "beauty": 534,
        "clinic": 7,
        "academy": 4,
        "retail": 760
      },
      "total_poi_count": 1343,
      "map_x": 41.3,
      "map_y": 25.2,
      "commercial_density_index": 93,
      "source_note": "OSM Overpass public POI 650m precompute + district density editorial index; KOSIS build-time replacement ready",
      "commercial_density_label": "과밀",
      "top_industries": [
        "retail",
        "food",
        "beauty"
      ],
      "default_take": "매장 수는 충분하지만 같은 업종끼리 고객을 나눠 갖는 구간입니다. 임대료보다 회전율과 재방문 이유를 먼저 확인하세요."
    },
    {
      "id": "sinchon",
      "name": "신촌역",
      "district": "서대문구",
      "dong": "신촌동",
      "lat": 37.5551,
      "lng": 126.9368,
      "population_density_index": 70,
      "population_density_label": "높음",
      "rent_pressure_index": 73,
      "radius_m": 650,
      "counts": {
        "cafe": 136,
        "food": 678,
        "convenience": 74,
        "beauty": 232,
        "clinic": 73,
        "academy": 17,
        "retail": 482
      },
      "total_poi_count": 1255,
      "map_x": 44.8,
      "map_y": 26.8,
      "commercial_density_index": 87,
      "source_note": "OSM Overpass public POI 650m precompute + district density editorial index; KOSIS build-time replacement ready",
      "commercial_density_label": "과밀",
      "top_industries": [
        "food",
        "retail",
        "beauty"
      ],
      "default_take": "매장 수는 충분하지만 같은 업종끼리 고객을 나눠 갖는 구간입니다. 임대료보다 회전율과 재방문 이유를 먼저 확인하세요."
    },
    {
      "id": "yeouido",
      "name": "여의도역",
      "district": "영등포구",
      "dong": "여의도동",
      "lat": 37.5216,
      "lng": 126.9242,
      "population_density_index": 61,
      "population_density_label": "중상",
      "rent_pressure_index": 86,
      "radius_m": 650,
      "counts": {
        "cafe": 14,
        "food": 727,
        "convenience": 41,
        "beauty": 85,
        "clinic": 15,
        "academy": 4,
        "retail": 272
      },
      "total_poi_count": 1018,
      "map_x": 41.2,
      "map_y": 52.6,
      "commercial_density_index": 76,
      "source_note": "OSM Overpass public POI 650m precompute + district density editorial index; KOSIS build-time replacement ready",
      "commercial_density_label": "높음",
      "top_industries": [
        "food",
        "retail",
        "beauty"
      ],
      "default_take": "기본 유입은 보이지만 업종 선택에 따라 승패가 갈립니다. 낮·퇴근·주말을 나눠 같은 자리에서 관찰하세요."
    },
    {
      "id": "mullae",
      "name": "문래역",
      "district": "영등포구",
      "dong": "문래동",
      "lat": 37.5179,
      "lng": 126.8947,
      "population_density_index": 61,
      "population_density_label": "중상",
      "rent_pressure_index": 67,
      "radius_m": 650,
      "counts": {
        "cafe": 10,
        "food": 643,
        "convenience": 55,
        "beauty": 94,
        "clinic": 6,
        "academy": 4,
        "retail": 247
      },
      "total_poi_count": 898,
      "map_x": 32.8,
      "map_y": 55.5,
      "commercial_density_index": 67,
      "source_note": "OSM Overpass public POI 650m precompute + district density editorial index; KOSIS build-time replacement ready",
      "commercial_density_label": "높음",
      "top_industries": [
        "food",
        "retail",
        "beauty"
      ],
      "default_take": "기본 유입은 보이지만 업종 선택에 따라 승패가 갈립니다. 낮·퇴근·주말을 나눠 같은 자리에서 관찰하세요."
    },
    {
      "id": "jongno3",
      "name": "종로3가역",
      "district": "종로구",
      "dong": "종로3가",
      "lat": 37.5704,
      "lng": 126.991,
      "population_density_index": 38,
      "population_density_label": "낮음",
      "rent_pressure_index": 71,
      "radius_m": 650,
      "counts": {
        "cafe": 188,
        "food": 593,
        "convenience": 87,
        "beauty": 59,
        "clinic": 14,
        "academy": 9,
        "retail": 217
      },
      "total_poi_count": 833,
      "map_x": 60.3,
      "map_y": 15.1,
      "commercial_density_index": 62,
      "source_note": "OSM Overpass public POI 650m precompute + district density editorial index; KOSIS build-time replacement ready",
      "commercial_density_label": "높음",
      "top_industries": [
        "food",
        "retail",
        "cafe"
      ],
      "default_take": "기본 유입은 보이지만 업종 선택에 따라 승패가 갈립니다. 낮·퇴근·주말을 나눠 같은 자리에서 관찰하세요."
    },
    {
      "id": "seongsu",
      "name": "성수역",
      "district": "성동구",
      "dong": "성수동",
      "lat": 37.5446,
      "lng": 127.0557,
      "population_density_index": 72,
      "population_density_label": "높음",
      "rent_pressure_index": 84,
      "radius_m": 650,
      "counts": {
        "cafe": 44,
        "food": 191,
        "convenience": 28,
        "beauty": 119,
        "clinic": 6,
        "academy": 7,
        "retail": 187
      },
      "total_poi_count": 391,
      "map_x": 78.8,
      "map_y": 34.9,
      "commercial_density_index": 27,
      "source_note": "OSM Overpass public POI 650m precompute + district density editorial index; KOSIS build-time replacement ready",
      "commercial_density_label": "낮음",
      "top_industries": [
        "food",
        "retail",
        "beauty"
      ],
      "default_take": "주변 POI가 적게 잡히는 후보지입니다. 임대료가 낮아도 유입을 직접 만들 수 있는 업종인지 확인해야 합니다."
    },
    {
      "id": "konkuk",
      "name": "건대입구역",
      "district": "광진구",
      "dong": "화양동",
      "lat": 37.5404,
      "lng": 127.0692,
      "population_density_index": 82,
      "population_density_label": "매우 높음",
      "rent_pressure_index": 75,
      "radius_m": 650,
      "counts": {
        "cafe": 39,
        "food": 315,
        "convenience": 18,
        "beauty": 191,
        "clinic": 9,
        "academy": 6,
        "retail": 246
      },
      "total_poi_count": 576,
      "map_x": 82.6,
      "map_y": 38.2,
      "source_note": "OSM Overpass public POI 600m precompute + district density editorial index; KOSIS build-time replacement ready",
      "commercial_density_index": 41,
      "commercial_density_label": "보통",
      "top_industries": [
        "food",
        "retail",
        "beauty"
      ],
      "default_take": "과밀은 덜하지만 목적 방문 이유가 약하면 공실 리스크가 커집니다. 앵커시설과 반복 동선을 먼저 보세요."
    },
    {
      "id": "gangnam",
      "name": "강남역",
      "district": "강남구",
      "dong": "역삼동",
      "lat": 37.4979,
      "lng": 127.0276,
      "population_density_index": 63,
      "population_density_label": "중상",
      "rent_pressure_index": 92,
      "radius_m": 650,
      "counts": {
        "cafe": 33,
        "food": 411,
        "convenience": 80,
        "beauty": 261,
        "clinic": 21,
        "academy": 7,
        "retail": 519
      },
      "total_poi_count": 958,
      "map_x": 70.7,
      "map_y": 70.8,
      "source_note": "OSM Overpass public POI 600m precompute + district density editorial index; KOSIS build-time replacement ready",
      "commercial_density_index": 66,
      "commercial_density_label": "높음",
      "top_industries": [
        "retail",
        "food",
        "beauty"
      ],
      "default_take": "기본 유입은 보이지만 업종 선택에 따라 승패가 갈립니다. 낮·퇴근·주말을 나눠 같은 자리에서 관찰하세요."
    },
    {
      "id": "sadang",
      "name": "사당역",
      "district": "동작구",
      "dong": "사당동",
      "lat": 37.4766,
      "lng": 126.9816,
      "population_density_index": 88,
      "population_density_label": "매우 높음",
      "rent_pressure_index": 70,
      "radius_m": 650,
      "counts": {
        "cafe": 18,
        "food": 137,
        "convenience": 34,
        "beauty": 172,
        "clinic": 5,
        "academy": 4,
        "retail": 212
      },
      "total_poi_count": 358,
      "map_x": 57.6,
      "map_y": 87.2,
      "commercial_density_index": 24,
      "source_note": "OSM Overpass public POI 650m precompute + district density editorial index; KOSIS build-time replacement ready",
      "commercial_density_label": "낮음",
      "top_industries": [
        "retail",
        "beauty",
        "food"
      ],
      "default_take": "주변 POI가 적게 잡히는 후보지입니다. 임대료가 낮아도 유입을 직접 만들 수 있는 업종인지 확인해야 합니다."
    },
    {
      "id": "sillim",
      "name": "신림역",
      "district": "관악구",
      "dong": "신림동",
      "lat": 37.4842,
      "lng": 126.9296,
      "population_density_index": 84,
      "population_density_label": "매우 높음",
      "rent_pressure_index": 66,
      "radius_m": 650,
      "counts": {
        "cafe": 8,
        "food": 103,
        "convenience": 56,
        "beauty": 269,
        "clinic": 13,
        "academy": 3,
        "retail": 437
      },
      "total_poi_count": 555,
      "map_x": 42.7,
      "map_y": 81.4,
      "commercial_density_index": 35,
      "source_note": "OSM Overpass public POI 650m precompute + district density editorial index; KOSIS build-time replacement ready",
      "commercial_density_label": "낮음",
      "top_industries": [
        "retail",
        "beauty",
        "food"
      ],
      "default_take": "주변 POI가 적게 잡히는 후보지입니다. 임대료가 낮아도 유입을 직접 만들 수 있는 업종인지 확인해야 합니다."
    },
    {
      "id": "jamsil",
      "name": "잠실역",
      "district": "송파구",
      "dong": "잠실동",
      "lat": 37.5133,
      "lng": 127.1,
      "population_density_index": 79,
      "population_density_label": "매우 높음",
      "rent_pressure_index": 80,
      "radius_m": 650,
      "counts": {
        "cafe": 41,
        "food": 111,
        "convenience": 48,
        "beauty": 114,
        "clinic": 4,
        "academy": 6,
        "retail": 488
      },
      "total_poi_count": 610,
      "map_x": 91.4,
      "map_y": 59.0,
      "commercial_density_index": 38,
      "source_note": "OSM Overpass public POI 650m precompute + district density editorial index; KOSIS build-time replacement ready",
      "commercial_density_label": "보통",
      "top_industries": [
        "retail",
        "beauty",
        "food"
      ],
      "default_take": "과밀은 덜하지만 목적 방문 이유가 약하면 공실 리스크가 커집니다. 앵커시설과 반복 동선을 먼저 보세요."
    }
  ]
}
''')


def commercial_check_tool_block() -> str:
    data_version = asset_version(json.dumps(SEOUL_COMMERCIAL_AREAS, ensure_ascii=False, sort_keys=True))
    categories = SEOUL_COMMERCIAL_AREAS["categories"]
    default_category = "cafe"
    default_station = "hongdae"
    layer_buttons = "\n".join(
        f'<button type="button" data-density-layer="{esc(key)}" aria-pressed="{str(key == default_category).lower()}">{esc(label)}</button>'
        for key, label in categories.items()
        if key in {"cafe", "food", "convenience", "beauty", "clinic", "academy", "population"}
    )
    station_buttons = "\n".join(
        f'<button type="button" class="station-dot" data-station-map="{esc(station["id"])}" style="--x: {station["map_x"]}%; --y: {station["map_y"]}%;" aria-label="{esc(station["name"])} 상권 보기"><span>{esc(station["name"])}</span><small>{esc(station["commercial_density_label"])}</small></button>'
        for station in SEOUL_COMMERCIAL_AREAS["stations"]
    )
    station_options = "\n".join(
        f'<option value="{esc(station["id"])}"{" selected" if station["id"] == default_station else ""}>{esc(station["name"])} · {esc(station["district"])} {esc(station["dong"])}</option>'
        for station in SEOUL_COMMERCIAL_AREAS["stations"]
    )
    compare_options = "\n".join(
        f'<option value="{esc(station["id"])}"{" selected" if station["id"] == "gangnam" else ""}>{esc(station["name"])} · {esc(station["district"])} {esc(station["dong"])}</option>'
        for station in SEOUL_COMMERCIAL_AREAS["stations"]
    )
    category_options = "\n".join(
        f'<option value="{esc(key)}"{" selected" if key == default_category else ""}>{esc(label)}</option>'
        for key, label in categories.items()
        if key in {"cafe", "food", "convenience", "beauty", "clinic", "academy", "retail", "population"}
    )
    return f'''
<section id="commercial-check-tool" class="seoul-density-panel" data-seoul-density-tool-root data-commercial-tool-root data-density-src="/data/seoul-commercial-areas.json?v={data_version}" aria-label="서울 역세권 업종 밀도 지도">
  <div class="seoul-tool-copy">
    <p class="eyebrow">Seoul Density Radar · 역세권 먼저 보기</p>
    <h2>서울 지도로 업종 밀도와 인구밀도를 같이 봅니다.</h2>
    <p>집·상가 후보지를 보기 전, 지하철역 주변 650m 안의 매장 수와 행정구 인구밀도 지수를 먼저 비교합니다. 키는 빌드 단계에서만 쓰고, 사이트에는 공개 정적 JSON만 배포하는 구조입니다.</p>
    <div class="tool-badges"><span>서울 주요 역 12곳</span><span>업종별 밀도</span><span>인구밀도 지수</span><span>계약 질문 3개</span></div>
  </div>
  <div class="seoul-map-card" data-seoul-map>
    <div class="map-card-head">
      <div><strong>서울 상권 밀도 지도</strong><span data-map-layer-label>카페 밀도</span></div>
      <small>역 버튼을 눌러 후보지를 바꾸세요</small>
    </div>
    <div class="density-layer-tabs" role="tablist" aria-label="업종 밀도 레이어">
      {layer_buttons}
    </div>
    <div class="seoul-map-canvas" data-map-canvas>
      <span class="han-river" aria-hidden="true">한강</span>
      <span class="metro-line metro-line-2" aria-hidden="true">2호선</span>
      <span class="metro-line metro-line-9" aria-hidden="true">9호선</span>
      <span class="metro-line metro-line-sinbundang" aria-hidden="true">신분당</span>
      {station_buttons}
    </div>
    <p class="map-source-note" data-source-note>공개 POI를 빌드 시점에 집계한 정적 데이터입니다. KOSIS 키는 브라우저에 노출하지 않습니다.</p>
  </div>
  <div class="station-inspector" data-station-inspector>
    <form class="seoul-selector-form" data-station-tool>
      <label>역·동네 선택<select id="tool-station">{station_options}</select></label>
      <label>비교 기준 역<select id="tool-compare-station">{compare_options}</select></label>
      <label>보고 싶은 업종<select id="tool-industry">{category_options}</select></label>
      <label>계약 용도<select id="tool-purpose"><option value="commercial">상가·카페 창업</option><option value="home">집·전월세 후보</option></select></label>
    </form>
    <article class="density-result-card" data-density-result>
      <div class="density-title-row">
        <div><span class="tag pale" data-station-meta>서울 주요 역</span><h3 data-station-title>홍대입구역 상권 밀도</h3></div>
        <strong data-risk-grade>주의</strong>
      </div>
      <p data-risk-summary>역을 선택하면 업종별 매장 수, 인구밀도 지수, 계약 전 질문이 같이 바뀝니다.</p>
      <div class="density-score-grid">
        <div><span>선택 업종</span><strong data-density-count>0</strong><small data-density-label>카페</small></div>
        <div><span>상권 밀도</span><strong data-commercial-density>0</strong><small>/100</small></div>
        <div><span>인구밀도</span><strong data-pop-density>0</strong><small data-pop-label>지수</small></div>
      </div>
      <div class="density-bars" data-density-bars></div>
      <ol class="tool-risk-list" data-risk-list></ol>
      <div class="tool-link-row" data-recommend-links>
        <a href="/topics/cafe-commercial-lease-risk/">상가 계약 체크 글 목록</a>
        <a href="/topics/jeonwolse-contract-check/">전월세 체크 글 목록</a>
      </div>
    </article>
    <article class="density-compare-card" data-compare-panel aria-live="polite">
      <span>바로 비교</span>
      <strong data-compare-title>홍대입구역 ↔ 강남역</strong>
      <div class="compare-metric-row" data-compare-metrics>
        <div><span>업종 차이</span><strong>0</strong></div>
        <div><span>인구밀도</span><strong>0</strong></div>
        <div><span>임대압력</span><strong>0</strong></div>
      </div>
      <p data-compare-note>다른 역과 업종·인구·임대 압력을 나란히 보고 후보지를 줄입니다.</p>
    </article>
  </div>
</section>
'''


def home_body(deals: list[dict], radar: list[dict]) -> str:
    radar_html = article_cards(radar[:4], "첫 동네 레이더 글 준비중")
    return f'''
<section class="hero home-hero product-hero">
  <p class="eyebrow">Dongne Radar · 서울 후보지 체크</p>
  <h1>블로그가 아니라, 계약 전 서울 후보지를 먼저 거르는 도구.</h1>
  <p class="lead">역세권 업종 밀도, 인구밀도, 매장 수를 보고 “집으로 볼지, 상가로 볼지, 보류할지”를 30초 안에 가릅니다.</p>
  <div class="hero-actions compact-actions">
    <a class="button primary" href="#commercial-check-tool">서울 지도에서 후보지 보기</a>
    <a class="button" href="/topics/jeonwolse-contract-check/">계약 질문 목록</a>
  </div>
</section>
{commercial_check_tool_block()}
<section class="grid three situation-grid" aria-label="오늘 볼 후보지 유형">
  <article class="card accent-blue situation-card">
    <span class="tag">집 보러 가기 전</span>
    <h2>역에서 집까지 마지막 7분</h2>
    <p>인구밀도, 밤길, 소음, 엘리베이터·공용부 피로를 보고 전월세 질문으로 바꿉니다.</p>
    <a href="/topics/jeonwolse-contract-check/">전월세 체크 보기 →</a>
  </article>
  <article class="card accent-orange situation-card">
    <span class="tag">상가·카페 계약 전</span>
    <h2>500m 안 같은 업종이 얼마나 많은가</h2>
    <p>카페·음식점·편의·병원·학원 밀도를 보고 권리금과 고정비 질문을 먼저 잡습니다.</p>
    <a href="/topics/cafe-commercial-lease-risk/">상가 계약 체크 보기 →</a>
  </article>
  <article class="card accent-green situation-card">
    <span class="tag">현장 확인</span>
    <h2>점수보다 질문 3개</h2>
    <p>좋아 보이는 동네가 아니라 계약서에 적기 전에 다시 물어볼 질문을 남깁니다.</p>
    <a href="/radar/">사례 글로 더 보기 →</a>
  </article>
</section>
<section class="panel soft density-search-strip" aria-label="바로 확인할 계약 질문">
  <h2>오늘 바로 확인할 질문</h2>
  <div class="category-strip">
    {category_strip_links(["역세권 상권", "카페 창업", "권리금", "월세 계약", "밤길·소음", "관리비", "현장 확인 질문"])}
  </div>
</section>
<section class="article-list mixed-list radar-latest-grid case-study-list">
  <div class="section-title"><h2>사례로 더 보기</h2><p>도구에서 걸린 신호를 실제 현장 질문으로 바꾼 글입니다.</p></div>
  {radar_html}
</section>
<script src="/assets/commercial-check.js?v={asset_version(COMMERCIAL_TOOL_JS)}" defer></script>
'''

def deals_body(deals: list[dict]) -> str:
    return f'''
<section class="deal-landing-hero">
  <div class="deal-hero-copy">
    <p class="eyebrow">쇼핑픽 · 구매 후보 지도</p>
    <h1>필요한 제품만 빠르게 비교</h1>
    <p class="lead">생활가전·책상 장비·음향기기를 가격대, 사용 장면, 관리 부담 기준으로 짧게 정리합니다. 오늘 살 만한 후보만 먼저 보고, 자세한 가격은 상품 페이지에서 다시 확인하세요.</p>
    <div class="hero-actions compact-actions">
      <a class="button primary" href="#today-best">오늘 추천 보기</a>
      <a class="button" href="#deal-search">상품 검색하기</a>
    </div>
    <div class="deal-flow" aria-label="쇼핑픽 이용 순서">
      <span><strong>1</strong> 용도 정하기</span>
      <span><strong>2</strong> 후보 비교</span>
      <span><strong>3</strong> 상품 확인</span>
    </div>
    <p class="affiliate-inline"><strong>제휴 고지</strong> 쿠팡 파트너스 활동의 일환으로 구매 시 일정액의 수수료를 제공받을 수 있습니다.</p>
  </div>
  {shopping_room_scene(deals)}
</section>
<section class="deal-category-rail" aria-label="카테고리 빠른 이동">
  <strong>바로가기</strong>
  <div class="category-strip">{category_chips(deals)}</div>
</section>
<section id="today-best" class="landing-section above-fold-section">
  <div class="section-title"><p class="eyebrow">오늘 추천</p><h2>지금 볼 만한 쇼핑픽</h2><p>최근 조회와 발행일을 함께 보고, 바로 비교하기 좋은 글부터 보여줍니다.</p></div>
  <div class="deal-grid best-grid">{best_deal_cards(deals)}</div>
</section>
<section id="deal-search" class="panel soft search-panel lower-search">
  <div class="section-title"><h2>원하는 상품만 검색</h2><p>상품명, 용도, 예산, 사용 장소를 넣어 관련 비교글을 찾습니다.</p></div>
  {search_form(
      "예: 원룸 제습기, 모니터암, 사무용 의자, 블루투스 스피커",
      "상품명, 용도, 예산, 사용 장소를 기준으로 쇼핑픽 비교글만 빠르게 좁혀봅니다.",
  )}
</section>
<section id="category-blocks" class="landing-section category-directory-section">
  <div class="section-title"><h2>카테고리별 빠른 이동</h2><p>카테고리명은 짧게, 대표 비교글은 2개만 보여줍니다.</p></div>
  <div class="category-hubs">{deal_category_hubs(deals)}</div>
</section>
<section class="site-bridge-strip compact-bridge" aria-label="동네 레이더 이동">
  <div>
    <span class="tag pale">상품 비교가 아니라면</span>
    <h2>이사·월세·상가는 동네 레이더</h2>
    <p>동네 리스크를 보러 온 경우에만 이동하세요.</p>
  </div>
  <div class="bridge-actions">
    <a class="button" href="/radar/">동네 레이더 보기</a>
  </div>
</section>
<section class="landing-section decision-strip" aria-label="구매 전 체크">
  <div class="section-title"><h2>구매 전 3단계</h2><p>살 이유보다 실패 이유를 먼저 고르면 비교가 빨라집니다.</p></div>
  <ol class="decision-steps">
    <li><span>1</span><strong>쓸 장면</strong><p>원룸·책상·출퇴근처럼 실제 사용 위치를 하나로 고정</p></li>
    <li><span>2</span><strong>실패 피하기</strong><p>소음·부피·세척·필터 비용 중 제일 싫은 조건 선택</p></li>
    <li><span>3</span><strong>상품 확인</strong><p>가격·배송·옵션·최근 후기는 상품 페이지에서 재확인</p></li>
  </ol>
</section>
<section id="all-deals" class="landing-section">
  <div class="section-title"><h2>전체 비교글</h2><p>이미 공개된 쇼핑픽 전체 목록입니다.</p></div>
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
    <a class="button primary" href="#contract-check-routes">계약 체크 목록</a>
    <a class="button" href="/topics/jeonwolse-contract-check/">전월세 글 목록</a>
    <a class="button" href="/topics/cafe-commercial-lease-risk/">상가 계약 글 목록</a>
  </div>
</section>
<section id="contract-check-routes" class="grid two contract-check-routes" aria-label="계약 체크 글 목록 입구">
  {contract_check_route_cards(radar)}
</section>
<section class="panel soft">
  <h2>현재 레이더 범위</h2>
  <div class="category-strip">
    {category_strip_links(["예산·보증금·월세", "관리비·교통비", "통근·대체 생활권", "생활 상권", "밤길·소음", "상가 임대차·권리금"])}
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
    <a href="/topics/jeonwolse-contract-check/">전월세 체크 글 목록 →</a>
  </article>
  <article class="card accent-green">
    <span class="tag">2 · 상가·창업</span>
    <h2>계약서 쓰기 전</h2>
    <p>유동인구 착시, 경쟁밀도, 폐업 압력, 권리금 회수 리스크를 먼저 의심합니다.</p>
    <a href="/topics/cafe-commercial-lease-risk/">상가 계약 체크 글 목록 →</a>
  </article>
  <article class="card accent-orange">
    <span class="tag">3 · 별도 구매</span>
    <h2>생활 구매는 분리</h2>
    <p>상품 비교가 필요할 때만 쇼핑픽으로 이동합니다. 동네 레이더 판단과 제휴 문맥은 섞지 않습니다.</p>
    <a href="/deals/">쇼핑픽 보기 →</a>
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
  <p><a href="/radar/">/radar/</a>는 동네·상권 판단 글, <a href="/deals/">/deals/</a>는 쇼핑픽 글입니다. 제휴 링크가 있는 글은 해당 본문 안에서 따로 고지합니다.</p>
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
    <h2>쇼핑픽</h2>
    <p>상품 비교와 제휴 가능 글은 /deals/에서만 별도 운영합니다.</p>
    <a href="/deals/">쇼핑픽 보기 →</a>
  </article>
</section>
<section class="panel soft">
  <h2>바로 볼 수 있는 동네 레이더</h2>
  <ul>
    <li><a href="/topics/jeonwolse-contract-check/">전월세 계약 전 체크 글 목록</a></li>
    <li><a href="/topics/cafe-commercial-lease-risk/">카페·상가 계약 전 체크 글 목록</a></li>
  </ul>
</section>
<section class="panel">
  <h2>운영 원칙</h2>
  <ul>
    <li><strong>판단 중심:</strong> 단순 순위보다 “계약 전 무엇을 걸러야 하는지”를 먼저 씁니다.</li>
    <li><strong>현장 질문:</strong> 데이터가 좋아 보여도 밤길, 소음, 관리비, 공실, 권리금 회수는 다시 묻습니다.</li>
    <li><strong>섹션 분리:</strong> 동네 레이더와 쇼핑픽은 URL, 고지, 독자 의도를 분리합니다.</li>
    <li><strong>검색 친화:</strong> sitemap, RSS, llms.txt, ai.txt를 유지해 검색엔진과 AI가 읽기 쉽게 둡니다.</li>
    <li><strong>계속 갱신:</strong> 공개 글은 KPI와 독자 의도에 맞춰 제목, 도입부, 체크리스트를 계속 다듬습니다.</li>
  </ul>
  <h2>현재 공개 수</h2>
  <p>동네 레이더 {radar_count}개, 쇼핑픽 {deals_count}개를 공개 중입니다.</p>
</section>
<section class="notice compact-notice">
  <strong>투명성</strong>
  <p>쇼핑픽의 일부 링크는 제휴 링크일 수 있으며, 그런 글은 본문에 별도 고지를 표시합니다. 동네 레이더 글에는 제휴 문맥을 섞지 않습니다.</p>
</section>
'''

def article_body(article: dict, related_articles: list[dict] | None = None) -> str:
    section_name = "쇼핑픽" if article["section"] == "deals" else "동네 레이더"
    section_href = f"/{article['section']}/"
    dt = parse_dt(article.get("date"))
    metric = traffic_badge(article["path"])
    tags = taxonomy_links(article.get("tags") or [], "tag pale", limit=8)
    category = taxonomy_link(article.get("category"), "meta-link")
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
    example_block = ""
    if article.get("section") == "radar":
        visual_block = radar_experience_block(article)
        example_block = radar_example_gallery(article)
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
        search_chips = related_search_chips(article)
        search_block = ""
        if search_chips:
            search_block = f'''<div class="radar-related-search">
    <h3>같은 리스크 더 찾기</h3>
    <div class="search-chip-row">{search_chips}</div>
  </div>'''
        related_block = f'''<section class="related-radar">
  <h2>다음에 같이 볼 글</h2>
  <ul>{links}<li><a href="/guides/">처음 온 사람을 위한 읽는 순서</a></li></ul>
  {search_block}
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
    <div class="article-meta">{category}<time datetime="{esc(article.get('date'))}">{dt.strftime('%Y-%m-%d %H:%M KST')}</time>{metric}</div>
    <div class="tag-row">{tags}</div>
  </header>
  {notice}
  {quick_block}
  {visual_block}
  {example_block}
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
    index_pages = list(STATIC_PAGES) + topic_page_metas()
    static_items = []
    for p in index_pages:
        if p.get("section") == "search":
            continue
        topic = p.get("topic") or {}
        topic_terms = " ".join(
            [
                str(topic.get("label") or ""),
                str(topic.get("intent") or ""),
                " ".join(str(x) for x in topic.get("keywords") or []),
                " ".join(str(x) for x in topic.get("queries") or []),
            ]
        )
        static_items.append(
            {
                "title": p["title"],
                "description": p["description"],
                "path": p["path"],
                "section": p.get("section"),
                "category": "주제별" if p.get("section") == "topics" else "사이트",
                "tags": p.get("tags") or [],
                "date": TODAY,
                "image_url": "",
                "price_hint": "",
                "item_count_hint": "주제별 페이지" if p.get("section") == "topics" else "",
                "views": 0,
                "text": f"{p['title']} {p['description']} {topic_terms}",
            }
        )
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
h1, h2, h3, p, li, a { overflow-wrap: break-word; word-break: keep-all; }
.skip-link {
  position: fixed; left: -999px; top: 12px; z-index: 100;
  width: 1px; height: 1px; overflow: hidden;
  padding: 10px 14px; border-radius: 12px;
  background: var(--ink); color: #fff; font-weight: 950; box-shadow: var(--shadow);
}
.skip-link:focus-visible { left: 16px; width: auto; height: auto; overflow: visible; outline: 3px solid rgba(37, 99, 235, .35); }
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
.product-hero { padding: clamp(20px, 3.5vw, 42px) 0 8px; }
.product-hero h1 { max-width: 920px; font-size: clamp(32px, 4.7vw, 54px); margin-bottom: 12px; }
.product-hero .lead { max-width: 760px; font-size: clamp(17px, 1.8vw, 21px); }
.product-hero .hero-actions { margin-top: 18px; }
.seoul-density-panel {
  scroll-margin-top: 92px;
  display: grid; grid-template-columns: minmax(270px, .78fr) minmax(420px, 1.12fr) minmax(320px, .82fr); gap: 18px;
  align-items: stretch; margin: 8px 0 34px; padding: clamp(18px, 3vw, 30px);
  border: 1px solid rgba(234, 223, 212, .98); border-radius: 34px;
  background: linear-gradient(135deg, rgba(255, 255, 255, .97), rgba(255, 244, 234, .95));
  box-shadow: 0 24px 68px rgba(58, 37, 20, .12);
}
.seoul-tool-copy, .seoul-map-card, .station-inspector, .density-result-card { min-width: 0; }
.seoul-tool-copy { display: flex; flex-direction: column; justify-content: center; }
.seoul-tool-copy h2 { margin: 8px 0 12px; font-size: clamp(28px, 4.2vw, 48px); line-height: 1.05; letter-spacing: -0.05em; }
.seoul-tool-copy p { color: #5f5652; font-weight: 700; }
.tool-badges { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }
.tool-badges span { padding: 7px 10px; border-radius: 999px; background: #fff; border: 1px solid var(--line); font-size: 12px; font-weight: 950; color: #594e49; }
.seoul-map-card { order: -1; align-self: start; padding: 16px; border-radius: 28px; background: #101828; color: #fff; box-shadow: inset 0 0 0 1px rgba(255,255,255,.08); }
.map-card-head { display: flex; justify-content: space-between; gap: 14px; align-items: flex-start; margin-bottom: 12px; }
.map-card-head strong, .map-card-head span { display: block; }
.map-card-head strong { font-size: 18px; letter-spacing: -.035em; }
.map-card-head span, .map-card-head small { color: #cbd5e1; font-size: 12px; font-weight: 850; }
.density-layer-tabs { display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 12px; }
.density-layer-tabs button { min-height: 34px; border: 1px solid rgba(255,255,255,.18); border-radius: 999px; padding: 0 10px; background: rgba(255,255,255,.08); color: #e5e7eb; font: inherit; font-size: 12px; font-weight: 950; cursor: pointer; }
.density-layer-tabs button[aria-pressed="true"] { background: #ff5a1f; border-color: #ff5a1f; color: #fff; box-shadow: 0 8px 18px rgba(255,90,31,.24); }
.seoul-map-canvas { position: relative; min-height: 365px; border-radius: 24px; overflow: hidden; background: radial-gradient(circle at 58% 42%, rgba(96,165,250,.22), transparent 33%), linear-gradient(145deg, #172033, #0f172a 70%); border: 1px solid rgba(255,255,255,.12); }
.seoul-map-canvas::before { content: ""; position: absolute; inset: 20px 18px 22px; border: 2px solid rgba(255,255,255,.12); border-radius: 42% 46% 45% 50%; transform: rotate(-7deg); }
.han-river { position: absolute; left: 5%; right: 4%; top: 55%; height: 34px; border-radius: 999px; background: linear-gradient(90deg, rgba(96,165,250,.18), rgba(125,211,252,.45), rgba(96,165,250,.18)); transform: rotate(-5deg); display: flex; align-items: center; justify-content: center; color: #bfdbfe; font-size: 12px; font-weight: 950; letter-spacing: .18em; }
.metro-line { position: absolute; display: inline-flex; align-items: center; justify-content: center; color: rgba(255,255,255,.7); font-size: 10px; font-weight: 950; border: 1px dashed rgba(255,255,255,.22); border-radius: 999px; }
.metro-line-2 { left: 24%; top: 24%; width: 48%; height: 47%; border-color: rgba(34,197,94,.42); color: #bbf7d0; }
.metro-line-9 { left: 19%; right: 8%; top: 55%; height: 28px; border-color: rgba(250,204,21,.42); color: #fef08a; transform: rotate(-4deg); }
.metro-line-sinbundang { left: 67%; top: 46%; width: 26px; height: 39%; border-color: rgba(239,68,68,.38); color: #fecaca; writing-mode: vertical-rl; }
.station-dot { --heat: .5; position: absolute; left: var(--x); top: var(--y); transform: translate(-50%, -50%); display: grid; place-items: center; width: clamp(38px, calc(34px + var(--heat) * 30px), 72px); height: clamp(38px, calc(34px + var(--heat) * 30px), 72px); border: 2px solid rgba(255,255,255,.9); border-radius: 999px; background: radial-gradient(circle at 30% 30%, #fff 0 10%, rgba(255,90,31,.94) 11% 66%, rgba(124,45,18,.96) 100%); color: #fff; cursor: pointer; box-shadow: 0 0 0 calc(5px + var(--heat) * 10px) rgba(255,90,31, calc(.07 + var(--heat) * .10)), 0 14px 26px rgba(0,0,0,.32); transition: transform .16s ease, box-shadow .16s ease, width .16s ease, height .16s ease; }
.station-dot:hover, .station-dot[aria-pressed="true"] { transform: translate(-50%, -50%) scale(1.08); z-index: 3; box-shadow: 0 0 0 calc(8px + var(--heat) * 13px) rgba(255,90,31,.18), 0 18px 34px rgba(0,0,0,.38); }
.station-dot span { position: absolute; left: 50%; top: calc(100% + 5px); transform: translateX(-50%); white-space: nowrap; padding: 3px 7px; border-radius: 999px; background: rgba(15,23,42,.72); color: #fff; font-size: 11px; font-weight: 950; }
.station-dot small { font-size: 10px; font-weight: 950; text-shadow: 0 1px 5px rgba(0,0,0,.42); }
.map-source-note { margin: 12px 2px 0; color: #cbd5e1; font-size: 12px; font-weight: 750; }
.station-inspector { display: grid; gap: 12px; padding-top: 14px; }
.seoul-selector-form { display: grid; grid-template-columns: 1fr; gap: 10px; padding: 16px; border-radius: 24px; background: #fff; border: 1px solid rgba(234,223,212,.95); }
.seoul-selector-form label { display: grid; gap: 6px; color: #514641; font-size: 13px; font-weight: 950; }
.seoul-selector-form select { width: 100%; min-height: 44px; border: 1px solid #e4d5c7; border-radius: 14px; padding: 0 12px; background: #fffaf4; color: var(--ink); font: inherit; font-weight: 850; }
.density-result-card { padding: 18px; border-radius: 26px; background: #fff; border: 1px solid rgba(234,223,212,.95); }
.density-title-row { display: flex; justify-content: space-between; gap: 14px; align-items: flex-start; }
.density-title-row h3 { margin: 7px 0 6px; font-size: clamp(22px, 2.6vw, 30px); line-height: 1.12; letter-spacing: -.04em; }
.density-title-row > strong { flex: 0 0 auto; padding: 7px 11px; border-radius: 999px; background: #fbbf24; color: #211922; font-size: 13px; }
[data-grade="good"] .density-title-row > strong { background: #bbf7d0; color: #14532d; }
[data-grade="hold"] .density-title-row > strong { background: #fecaca; color: #7f1d1d; }
.density-result-card p { margin: 0 0 12px; color: #5f5652; font-weight: 750; }
.density-score-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin: 12px 0; }
.density-score-grid div { min-width: 0; padding: 12px 10px; border-radius: 18px; background: #fff7ed; border: 1px solid #f7d8c4; }
.density-score-grid span, .density-score-grid small { display: block; color: #7c2d12; font-size: 11px; font-weight: 950; }
.density-score-grid strong { display: block; margin: 2px 0; font-size: clamp(25px, 4vw, 38px); line-height: 1; letter-spacing: -.055em; }
.density-bars { display: grid; gap: 8px; margin: 12px 0 14px; }
.density-bar { display: grid; grid-template-columns: 78px 1fr 42px; gap: 8px; align-items: center; font-size: 12px; font-weight: 950; color: #514641; }
.density-bar span:nth-child(2) { height: 9px; border-radius: 999px; background: #f3e3d8; overflow: hidden; }
.density-bar span:nth-child(2)::before { content: ""; display: block; width: var(--value); height: 100%; border-radius: inherit; background: linear-gradient(90deg, #60a5fa, #ff5a1f); }
.tool-risk-list { display: grid; gap: 8px; margin: 0; padding-left: 22px; }
.tool-risk-list li { padding-left: 4px; font-weight: 800; }
.tool-link-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.tool-link-row a { display: inline-flex; min-height: 36px; align-items: center; padding: 0 12px; border-radius: 999px; background: #eef6ff; color: #1d4ed8; font-size: 13px; font-weight: 950; }
.density-compare-card { padding: 16px; border-radius: 24px; background: #101828; color: #fff; border: 1px solid rgba(255,255,255,.10); box-shadow: inset 0 0 0 1px rgba(255,255,255,.05); }
.density-compare-card > span { display: inline-flex; padding: 5px 9px; border-radius: 999px; background: rgba(255,255,255,.10); color: #cbd5e1; font-size: 11px; font-weight: 950; letter-spacing: .08em; }
.density-compare-card > strong { display: block; margin: 9px 0 10px; font-size: clamp(19px, 2vw, 24px); line-height: 1.2; letter-spacing: -.035em; }
.compare-metric-row { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin: 10px 0 12px; }
.compare-metric-row div { min-width: 0; padding: 10px; border-radius: 16px; background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.10); }
.compare-metric-row span, .compare-metric-row strong { display: block; }
.compare-metric-row span { color: #cbd5e1; font-size: 11px; font-weight: 950; }
.compare-metric-row strong { margin-top: 2px; font-size: 21px; line-height: 1; letter-spacing: -.045em; color: #fff; }
.compare-metric-row .compare-up strong { color: #fde68a; }
.compare-metric-row .compare-down strong { color: #bfdbfe; }
.density-compare-card p { margin: 0; color: #dbeafe; font-size: 13px; font-weight: 800; }
.situation-grid { margin-top: 18px; }
.situation-card { min-height: 236px; }
.case-study-list { margin-top: 34px; }
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
.tag { display: inline-flex; align-self: flex-start; align-items: center; min-height: 30px; border-radius: 999px; padding: 5px 11px; background: #fff0e5; color: var(--orange-dark); font-size: 12px; font-weight: 950; text-decoration: none; }
.tag.pale { background: #f4ebe2; color: #6b625f; }
.tag[href]:hover { background: #fff7ed; color: var(--orange-dark); box-shadow: 0 6px 14px rgba(255,90,31,.10); }
.meta-link, .quick-fact-link { color: inherit; font-weight: 950; text-decoration: none; border-bottom: 1px dashed rgba(107,98,95,.55); text-underline-offset: 3px; }
.meta-link:hover, .quick-fact-link:hover { color: var(--orange-dark); border-bottom-color: currentColor; }
.tag-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
.card p, .list-card p, .panel p, .notice p { color: #5f5652; }
.card > a:not(.button) { display: inline-flex; align-items: center; min-height: 44px; font-weight: 950; color: var(--orange-dark); }
.contract-check-routes { margin-top: -4px; }
.contract-route-card { gap: 10px; justify-content: flex-start; }
.contract-route-card h2 { margin: 0; font-size: clamp(23px, 2.5vw, 30px); }
.contract-route-card h2 a { color: inherit; text-decoration: none; }
.contract-route-card h2 a:hover { color: var(--orange); }
.route-count { display: inline-flex; width: fit-content; padding: 7px 11px; border-radius: 999px; background: #fff7ed; color: var(--orange-dark); font-size: 13px; }
.contract-route-card > a:last-child { margin-top: auto; }
.list-card h2, .list-card h2 a, .deal-card h2, .article-hero h1 { max-width: 100%; overflow-wrap: break-word; word-break: keep-all; }
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
.topic-article-list { grid-template-columns: minmax(0, 1fr); }
.topic-featured-list { max-width: 940px; }
.topic-secondary-list { grid-template-columns: repeat(auto-fit, minmax(min(100%, 520px), 1fr)); }
.topic-article-list .radar-card { min-width: 0; }
.radar-card { padding: 0; overflow: hidden; display: grid; grid-template-columns: minmax(220px, 0.42fr) minmax(0, 1fr); align-items: stretch; }
.radar-card, .radar-card * { overflow-wrap: break-word; word-break: keep-all; }
.radar-card-visual { position: relative; display: block; min-height: 250px; overflow: hidden; isolation: isolate; padding: 22px; color: #fff; background: linear-gradient(135deg, #211922, #573322 58%, #ff5a1f); }
.radar-card.theme-commute .radar-card-visual { background: radial-gradient(circle at 18% 18%, rgba(147,197,253,.35), transparent 24%), linear-gradient(135deg, #0f172a, #1d4ed8 58%, #38bdf8); }
.radar-card.theme-night .radar-card-visual { background: radial-gradient(circle at 74% 18%, rgba(255,214,165,.28), transparent 25%), linear-gradient(135deg, #160f1d, #3b1f2b 55%, #ff6b2b); }
.radar-card.theme-fee .radar-card-visual { background: radial-gradient(circle at 18% 22%, rgba(255,255,255,.24), transparent 23%), linear-gradient(135deg, #2b2118, #7a4f12 56%, #ffb020); }
.radar-card.theme-pressure .radar-card-visual { background: radial-gradient(circle at 75% 18%, rgba(186,230,253,.24), transparent 24%), linear-gradient(135deg, #172033, #244973 58%, #2563eb); }
.radar-card.theme-filter .radar-card-visual { background: radial-gradient(circle at 22% 18%, rgba(187,247,208,.22), transparent 23%), linear-gradient(135deg, #15251d, #22543d 55%, #0f8b57); }
.radar-card.theme-cafe .radar-card-visual { background: radial-gradient(circle at 20% 20%, rgba(254,240,138,.23), transparent 23%), linear-gradient(135deg, #17152b, #3b2f74 55%, #0f8b57); }
.radar-card-image { position: absolute; inset: 0; z-index: 0; width: 100%; height: 100%; object-fit: cover; object-position: 64% center; transform: scale(1.012); filter: brightness(1.1) saturate(1.08) contrast(1.04); pointer-events: none; }
.radar-card-visual::before { content: ""; position: absolute; inset: 16px; z-index: -2; border-radius: 28px; border: 1px solid rgba(255,255,255,.18); background-image: linear-gradient(rgba(255,255,255,.07) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.07) 1px, transparent 1px); background-size: 32px 32px; pointer-events: none; }
.radar-card-visual::after { content: ""; position: absolute; right: -54px; bottom: -70px; z-index: -1; width: 230px; height: 230px; border-radius: 50%; background: radial-gradient(circle, rgba(255,255,255,.24), rgba(255,255,255,.05) 48%, transparent 68%); pointer-events: none; }
.radar-card-visual.has-ai-thumb { min-height: 280px; }
.radar-card-visual.has-ai-thumb::before { inset: 0; z-index: 1; border: 0; border-radius: 0; background: linear-gradient(0deg, rgba(16,12,18,.08) 0%, rgba(16,12,18,0) 42%); }
.radar-card-visual.has-ai-thumb::after { inset: 14px; z-index: 2; width: auto; height: auto; border-radius: 26px; border: 1px solid rgba(255,255,255,.18); background: transparent; box-shadow: inset 0 0 0 1px rgba(0,0,0,.06); }
.radar-card-visual.has-ai-thumb .radar-thumb-label,
.radar-card-visual.has-ai-thumb .radar-thumb-title,
.radar-card-visual.has-ai-thumb .radar-thumb-subline,
.radar-card-visual.has-ai-thumb .radar-card-badge { display: none; }
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
.visual-checklist { right: 4px; top: 12px; width: 94px; padding: 10px; border-radius: 18px; background: rgba(255,255,255,.92); color: #15251d; box-shadow: 0 16px 28px rgba(0,0,0,.18); } .visual-checklist i { display: block; padding: 5px 0 5px 18px; position: relative; font-style: normal; font-size: 12px; font-weight: 950; } .visual-checklist i::before { content: ""; position: absolute; left: 0; top: 10px; width: 9px; height: 5px; border-left: 2px solid #0f8b57; border-bottom: 2px solid #0f8b57; transform: rotate(-45deg); }
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
.deals-site { background: #f6f5f4; }
.deals-site .site-header { background: rgba(255,255,255,.96); border-bottom-color: rgba(0,0,0,.08); }
.deals-site main { width: min(1240px, calc(100% - 32px)); }
.deal-landing-hero {
  display: grid; grid-template-columns: minmax(330px, .78fr) minmax(430px, 1.22fr); gap: clamp(18px, 2.6vw, 28px);
  align-items: stretch;
  margin: clamp(20px, 3.2vw, 36px) 0 12px;
  padding: clamp(22px, 3.4vw, 34px);
  background: #fff;
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 32px;
  box-shadow: rgba(0,0,0,0.04) 0 4px 18px, rgba(0,0,0,0.027) 0 2px 8px, rgba(0,0,0,0.02) 0 .8px 3px;
}
.deal-landing-hero > *, .site-bridge-strip > *, .deal-grid > *, .grid > * { min-width: 0; }
.deal-hero-copy, .deal-hero-panel, .deal-quick-box, .affiliate-disclosure {
  min-width: 0; max-width: 100%; box-sizing: border-box;
}
.deal-hero-copy { align-self: start; padding: clamp(4px, .9vw, 10px) 0 0; background: transparent; border: 0; box-shadow: none; }
.deal-hero-copy h1 { max-width: 600px; margin-top: 8px; margin-bottom: 12px; font-size: clamp(37px, 4.15vw, 52px); letter-spacing: -.055em; }
.deal-hero-copy .lead { max-width: 590px; color: #4b5563; font-size: clamp(15.5px, 1.45vw, 18px); line-height: 1.62; }
.compact-actions { margin-top: 18px; }
.compact-actions .button { min-height: 44px; border-radius: 14px; }
.deal-flow { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; max-width: 560px; margin-top: 16px; }
.deal-flow span { display: flex; align-items: center; gap: 8px; min-height: 40px; padding: 8px 11px; border-radius: 14px; background: #f9fafb; border: 1px solid #e5e7eb; color: #374151; font-size: 13px; font-weight: 900; }
.deal-flow strong { display: grid; place-items: center; flex: 0 0 auto; width: 22px; height: 22px; border-radius: 999px; background: #111827; color: #fff; font-size: 12px; line-height: 1; }
.affiliate-inline { max-width: 590px; margin: 14px 0 0; color: #6b7280; font-size: 12.5px; line-height: 1.5; font-weight: 750; }
.affiliate-inline strong { color: #9a3412; margin-right: 6px; }
.deal-hero-panel { align-self: stretch; display: flex; flex-direction: column; justify-content: flex-start; padding: clamp(18px, 2.6vw, 24px); background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 24px; box-shadow: none; }
.deal-hero-panel > .tag { margin-bottom: 12px; }
.deal-hero-panel > strong { display: block; font-size: clamp(21px, 2.2vw, 25px); line-height: 1.2; letter-spacing: -.035em; margin-bottom: 8px; }
.deal-hero-panel .checklist { margin: 10px 0 0; display: grid; gap: 9px; }
.deal-hero-panel .checklist li { margin: 0; line-height: 1.48; overflow-wrap: break-word; word-break: keep-all; color: #374151; font-size: 14.5px; }
.deal-hero-panel .microcopy { margin: 14px 0 0; color: #5f5652; font-size: 14px; line-height: 1.6; font-weight: 850; }
.playful-badges { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
.playful-badges span { display: inline-flex; align-items: center; min-height: 34px; padding: 0 12px; border-radius: 999px; background: #eef6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-size: 13px; font-weight: 950; }
.shopping-room-card { align-self: stretch; min-width: 0; padding: clamp(14px, 1.9vw, 18px); border-radius: 28px; background: linear-gradient(145deg, #fffaf4, #fff 58%, #f7fbff); border: 1px solid rgba(234,223,212,.95); box-shadow: inset 0 1px 0 rgba(255,255,255,.85), 0 18px 42px rgba(58,37,20,.08); }
.room-card-head { display: grid; gap: 7px; }
.room-card-head > strong { display: block; color: #111827; font-size: clamp(21px, 2.1vw, 26px); line-height: 1.15; letter-spacing: -.035em; }
.room-card-head p, .room-empty p { margin: 0; color: #6b625f; font-size: 13px; line-height: 1.5; font-weight: 750; }
.shopping-room-stage { position: relative; margin-top: 12px; }
.room-toggle { position: absolute; width: 1px; height: 1px; margin: 0; opacity: .001; pointer-events: none; }
.room-visual { position: relative; min-height: clamp(390px, 36vw, 470px); overflow: hidden; border-radius: 28px; background: #f3ebe2; border: 1px solid rgba(219,205,192,.9); isolation: isolate; box-shadow: inset 0 1px 0 rgba(255,255,255,.8); }
.room-photo { position: absolute; inset: 0; z-index: 0; width: 100%; height: 100%; object-fit: cover; object-position: center; filter: saturate(.96) contrast(.98); transform: scale(1.01); }
.room-visual::after { content: ""; position: absolute; inset: 0; z-index: 1; pointer-events: none; background: linear-gradient(180deg, rgba(255,255,255,.02), rgba(17,24,39,.10)), radial-gradient(circle at 50% 50%, transparent 0 62%, rgba(255,255,255,.26) 100%); }
.room-product { position: absolute; z-index: 9; display: grid; place-items: center; width: 66px; height: 66px; border-radius: 999px; cursor: pointer; outline: none; transform: translate(-50%, -50%); }
.room-product.pos-1 { left: 18%; top: 64%; }
.room-product.pos-2 { left: 56%; top: 45%; }
.room-product.pos-3 { left: 47%; top: 80%; }
.room-product.pos-4 { left: 82%; top: 54%; }
.room-product.pos-5 { left: 13%; top: 64%; }
.room-product.pos-6 { left: 82%; top: 25%; }
.room-product.kind-air { left: 20%; top: 65%; }
.room-product.kind-desk { left: 57%; top: 45%; }
.room-product.kind-sound { left: 82%; top: 24%; }
.room-product.kind-clean { left: 48%; top: 80%; }
.room-product.kind-kitchen { left: 84%; top: 55%; }
.room-product.kind-care { left: 80%; top: 78%; }
.room-product.kind-daily { left: 66%; top: 67%; }
.room-hit-area { position: absolute; inset: 4px; border-radius: 999px; background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.72); box-shadow: 0 12px 24px rgba(17,24,39,.13), inset 0 1px 0 rgba(255,255,255,.72); opacity: .78; transform: scale(.74); transition: opacity .16s ease, transform .16s ease, border-color .16s ease, background .16s ease; }
.room-pulse { position: absolute; width: 38px; height: 38px; border-radius: 999px; background: rgba(255,90,31,.12); border: 1px solid rgba(255,90,31,.38); box-shadow: 0 0 0 0 rgba(255,90,31,.18); transition: background .16s ease, border-color .16s ease, box-shadow .16s ease, transform .16s ease; }
.room-pin { position: relative; z-index: 2; width: 15px; height: 15px; border-radius: 999px; background: #ff5a1f; border: 3px solid #fff; box-shadow: 0 8px 18px rgba(17,24,39,.24); transition: transform .16s ease; }
.room-label { position: absolute; left: 50%; bottom: calc(100% + 8px); z-index: 4; min-width: 144px; max-width: 190px; transform: translateX(-50%) translateY(6px); padding: 9px 10px; border-radius: 14px; background: rgba(17,24,39,.94); color: #fff; box-shadow: 0 14px 28px rgba(17,24,39,.22); opacity: 0; pointer-events: none; transition: opacity .16s ease, transform .16s ease; }
.room-label strong, .room-label small { display: block; }
.room-label strong { font-size: 12.5px; line-height: 1.25; word-break: keep-all; }
.room-label small { margin-top: 3px; color: #fed7aa; font-size: 11px; font-weight: 900; }
.room-product:hover .room-label, .room-product:focus .room-label, #shopping-room-pick-1:checked ~ .room-visual .pos-1 .room-label, #shopping-room-pick-2:checked ~ .room-visual .pos-2 .room-label, #shopping-room-pick-3:checked ~ .room-visual .pos-3 .room-label, #shopping-room-pick-4:checked ~ .room-visual .pos-4 .room-label, #shopping-room-pick-5:checked ~ .room-visual .pos-5 .room-label, #shopping-room-pick-6:checked ~ .room-visual .pos-6 .room-label { opacity: 1; transform: translateX(-50%) translateY(0); }
.room-product:hover .room-hit-area, .room-product:focus .room-hit-area, #shopping-room-pick-1:checked ~ .room-visual .pos-1 .room-hit-area, #shopping-room-pick-2:checked ~ .room-visual .pos-2 .room-hit-area, #shopping-room-pick-3:checked ~ .room-visual .pos-3 .room-hit-area, #shopping-room-pick-4:checked ~ .room-visual .pos-4 .room-hit-area, #shopping-room-pick-5:checked ~ .room-visual .pos-5 .room-hit-area, #shopping-room-pick-6:checked ~ .room-visual .pos-6 .room-hit-area { opacity: 1; transform: scale(1); border-color: rgba(255,90,31,.64); background: rgba(255,255,255,.24); }
#shopping-room-pick-1:checked ~ .room-visual .pos-1 .room-pulse, #shopping-room-pick-2:checked ~ .room-visual .pos-2 .room-pulse, #shopping-room-pick-3:checked ~ .room-visual .pos-3 .room-pulse, #shopping-room-pick-4:checked ~ .room-visual .pos-4 .room-pulse, #shopping-room-pick-5:checked ~ .room-visual .pos-5 .room-pulse, #shopping-room-pick-6:checked ~ .room-visual .pos-6 .room-pulse { background: rgba(255,90,31,.24); border-color: rgba(255,90,31,.78); box-shadow: 0 0 0 8px rgba(255,90,31,.10); }
#shopping-room-pick-1:checked ~ .room-visual .pos-1 .room-pin, #shopping-room-pick-2:checked ~ .room-visual .pos-2 .room-pin, #shopping-room-pick-3:checked ~ .room-visual .pos-3 .room-pin, #shopping-room-pick-4:checked ~ .room-visual .pos-4 .room-pin, #shopping-room-pick-5:checked ~ .room-visual .pos-5 .room-pin, #shopping-room-pick-6:checked ~ .room-visual .pos-6 .room-pin { transform: scale(1.18); }
.room-previews { margin-top: 10px; }
.room-preview { display: none; padding: 14px 15px; border-radius: 20px; background: #fff; border: 1px solid rgba(0,0,0,.08); box-shadow: 0 10px 24px rgba(58,37,20,.06); }
#shopping-room-pick-1:checked ~ .room-previews .preview-1, #shopping-room-pick-2:checked ~ .room-previews .preview-2, #shopping-room-pick-3:checked ~ .room-previews .preview-3, #shopping-room-pick-4:checked ~ .room-previews .preview-4, #shopping-room-pick-5:checked ~ .room-previews .preview-5, #shopping-room-pick-6:checked ~ .room-previews .preview-6 { display: block; }
.room-preview h3 { margin: 8px 0 6px; color: #111827; font-size: 18px; line-height: 1.2; letter-spacing: -.03em; }
.room-preview p { margin: 0; color: #5f5652; font-size: 13.5px; line-height: 1.55; font-weight: 750; }
.room-preview-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 10px; }
.room-product-link { display: inline-flex; align-items: center; justify-content: center; min-height: 36px; padding: 0 13px; border-radius: 999px; background: #ff5a1f; color: #fff; border: 1px solid #ff5a1f; text-decoration: none; font-size: 13px; font-weight: 950; box-shadow: 0 10px 18px rgba(255,90,31,.14); }
.room-product-link:hover { color: #fff; background: #ea580c; border-color: #ea580c; }
.room-preview .text-link { min-height: 36px; font-size: 13px; }
.room-empty { padding: 20px; border-radius: 20px; background: #fff; border: 1px dashed #d6c7bb; }
.deal-category-rail { display: flex; align-items: center; gap: 12px; margin: 0 0 18px; padding: 10px 12px; border-radius: 18px; background: rgba(255,255,255,.72); border: 1px solid rgba(0,0,0,.08); }
.deal-category-rail > strong { flex: 0 0 auto; color: #111827; font-size: 13px; font-weight: 950; }
.deal-category-rail .category-strip { margin-top: 0; }
.site-bridge-strip { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 18px; margin: 8px 0 24px; padding: 20px; background: #fff; border: 1px solid #dbeafe; border-radius: 24px; box-shadow: 0 12px 30px rgba(15, 23, 42, .06); }
.site-bridge-strip.compact-bridge { margin: 24px 0 30px; padding: 18px; border-color: #e5e7eb; background: rgba(255,255,255,.82); box-shadow: none; }
.site-bridge-strip h2 { margin: 8px 0 6px; font-size: clamp(24px, 3vw, 34px); }
.site-bridge-strip.compact-bridge h2 { font-size: clamp(20px, 2.2vw, 26px); }
.site-bridge-strip p { margin: 0; color: #5f5652; }
.bridge-actions { display: flex; flex-wrap: wrap; gap: 10px; justify-content: flex-end; }
.site-bridge-strip.compact-bridge .button { min-height: 42px; border-radius: 14px; box-shadow: none; }
.affiliate-disclosure { margin: 22px 0 0; padding: 14px 16px; background: #fff7ed; border: 1px solid #fed7aa; border-radius: 24px; box-shadow: 0 12px 30px rgba(15,23,42,.06); }
.affiliate-disclosure strong { color: var(--orange-dark); }
.affiliate-disclosure p { margin: 4px 0 0; color: #5f5652; font-size: 14px; line-height: 1.6; }
.above-fold-section { margin-top: 10px; }
.deal-grid.best-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.deal-card.ranked { border-color: #fed7aa; }
.deal-rank { position: absolute; right: 12px; top: 12px; padding: 7px 10px; border-radius: 999px; background: #111827; color: #fff; font-size: 12px; font-weight: 950; }
.deal-text-badge { position: relative; min-height: 150px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; padding: 18px; background: radial-gradient(circle at 50% 28%, rgba(255,255,255,.92) 0 28%, transparent 29%), linear-gradient(135deg, #fff7ed, #ffffff 58%, #eff6ff); border-bottom: 1px solid var(--line); color: var(--orange-dark); font-weight: 950; text-align: center; overflow: hidden; }
.deal-text-badge::after { content: ''; position: absolute; inset: auto -18% -28% auto; width: 120px; height: 120px; border-radius: 50%; background: rgba(255,90,31,.10); }
.deal-fallback-icon { position: relative; z-index: 1; display: grid; place-items: center; width: 62px; height: 62px; border-radius: 22px; background: #fff; border: 1px solid rgba(234,223,212,.95); box-shadow: 0 14px 30px rgba(58,37,20,.10); font-size: 31px; line-height: 1; }
.deal-fallback-text { position: relative; z-index: 1; display: inline-flex; align-items: center; min-height: 30px; padding: 0 12px; border-radius: 999px; background: rgba(255,255,255,.86); border: 1px solid rgba(255,90,31,.18); color: var(--orange-dark); font-size: 12px; }
.deal-price { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.deal-price-link { display: inline-flex; align-items: center; min-height: 30px; padding: 0; border-radius: 0; background: transparent; border: 0; color: #6b7280; font-size: 12px; font-weight: 900; text-decoration: underline; text-underline-offset: 3px; }
.lower-search { margin-top: 18px; }
.decision-steps { list-style: none; margin: 16px 0 0; padding: 0; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-radius: 24px; background: #fff; border: 1px solid rgba(0,0,0,.08); overflow: hidden; box-shadow: rgba(0,0,0,.03) 0 4px 18px; }
.decision-steps li { position: relative; min-width: 0; padding: 18px 18px 18px 54px; border-right: 1px solid rgba(0,0,0,.08); }
.decision-steps li:last-child { border-right: 0; }
.decision-steps span { position: absolute; left: 18px; top: 19px; display: grid; place-items: center; width: 24px; height: 24px; border-radius: 999px; background: #111827; color: #fff; font-size: 12px; font-weight: 950; line-height: 1; }
.decision-steps strong { display: block; color: #111827; font-size: 16px; line-height: 1.25; font-weight: 950; letter-spacing: -.02em; }
.decision-steps p { margin: 5px 0 0; color: #6b7280; font-size: 14px; line-height: 1.5; font-weight: 700; }
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
.quick-product-links { border-top: 1px solid #e5e7eb; padding-top: 16px; }
.quick-product-links h3 { margin: 0 0 4px; font-size: 19px; }
.quick-product-links p { margin: 0 0 10px !important; font-size: 14px; font-weight: 850; }
.quick-product-links ul { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 8px; margin: 0; padding: 0; list-style: none; }
.quick-product-link { display: grid; gap: 3px; min-height: 58px; padding: 11px 13px; border-radius: 16px; background: #fff7ed; border: 1px solid #fed7aa; color: #9a3412; text-decoration: none; }
.quick-product-link span { min-width: 0; color: #111827; font-weight: 950; font-size: 14px; line-height: 1.35; }
.quick-product-link strong { color: var(--orange-dark); font-size: 12px; font-weight: 950; }
.quick-product-link:hover { background: #ffedd5; color: var(--orange-dark); box-shadow: 0 8px 18px rgba(255,90,31,.12); }
.quick-actions { margin-top: 0; }
.deal-article .article-hero { padding-bottom: 8px; }
.deal-article .article-product-hero { margin-top: 16px; }
.shop-hero {
  display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(320px, .95fr); gap: clamp(20px, 5vw, 56px);
  align-items: center; padding: clamp(34px, 6vw, 66px) 0 22px;
}
.shop-hero-copy h1 { max-width: 760px; }
.category-strip { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 24px; }
.category-chip { display: inline-flex; align-items: center; min-height: 40px; padding: 8px 12px; border-radius: 999px; background: #fff; border: 1px solid var(--line); color: #4b423f; font-weight: 900; font-size: 13px; text-decoration: none; transition: background .16s ease, border-color .16s ease, color .16s ease, transform .16s ease; }
.category-chip[href]:hover { background: #fff7ed; border-color: #ffd2b8; color: var(--orange-dark); transform: translateY(-1px); }
.hero-pin-stack { position: relative; min-height: 380px; }
.hero-pin { position: absolute; display: block; width: 58%; overflow: hidden; border-radius: 30px; background: #fff; box-shadow: var(--shadow); border: 8px solid #fff; }
.hero-pin img { display: block; width: 100%; aspect-ratio: 1 / 1; object-fit: cover; background: #fff; }
.hero-pin span { position: absolute; left: 12px; bottom: 12px; padding: 7px 10px; border-radius: 999px; background: rgba(33, 25, 34, .78); color: #fff; font-size: 12px; font-weight: 950; }
.hero-pin.pin-1 { right: 18%; top: 0; z-index: 3; }
.hero-pin.pin-2 { left: 0; bottom: 0; width: 48%; z-index: 2; transform: rotate(-5deg); }
.hero-pin.pin-3 { right: 0; bottom: 24px; width: 46%; z-index: 1; transform: rotate(5deg); }
.landing-section { margin: 34px 0 58px; scroll-margin-top: 96px; }
.intent-grid, .topic-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }
.category-hubs { display: grid; grid-template-columns: repeat(auto-fit, minmax(270px, 1fr)); gap: 10px; margin-top: 16px; padding: 10px; border-radius: 28px; background: rgba(255,255,255,.74); border: 1px solid rgba(0,0,0,.08); box-shadow: rgba(0,0,0,.035) 0 4px 18px, rgba(0,0,0,.02) 0 1px 4px; }
.intent-card, .topic-card { background: #fff; border: 1px solid var(--line); border-radius: 24px; padding: 20px; box-shadow: 0 10px 30px rgba(58, 37, 20, .065); }
.category-hub { display: grid; grid-template-columns: minmax(92px, 120px) minmax(0, 1fr); align-items: start; gap: 12px; min-width: 0; padding: 14px 15px; border-radius: 18px; background: #fff; border: 1px solid rgba(0,0,0,.07); box-shadow: none; }
.category-hub-label { display: grid; align-content: start; gap: 5px; min-height: 44px; color: #111827; text-decoration: none; }
.category-hub-label span { font-size: 15px; line-height: 1.22; font-weight: 950; }
.category-hub-label strong { width: fit-content; padding: 3px 8px; border-radius: 999px; background: #f6f5f4; color: #6b7280; font-size: 12px; line-height: 1.2; font-weight: 900; }
.category-hub-label:hover span { color: var(--orange-dark); text-decoration: underline; text-underline-offset: 3px; }
.category-hub-links { display: grid; gap: 7px; min-width: 0; }
.category-hub-links a { color: #2f2724; font-size: 14px; line-height: 1.38; font-weight: 850; text-decoration: none; overflow-wrap: anywhere; }
.category-hub-links a:hover { color: var(--orange-dark); text-decoration: underline; text-underline-offset: 3px; }
.category-hub-empty { color: var(--muted); font-size: 13px; font-weight: 800; }
.intent-card h2, .topic-card h2 { margin: 8px 0 8px; font-size: clamp(21px, 2.2vw, 26px); }
.intent-card p, .topic-card p { color: #5f5652; margin: 0 0 14px; line-height: 1.65; }
.topic-card { display: flex; flex-direction: column; min-height: 100%; }
.topic-card .text-link { margin-top: auto; }
.topic-card-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 8px; }
.topic-card-head strong { color: var(--muted); font-size: 13px; white-space: nowrap; }
.topic-intent { padding: 12px 14px; border-radius: 18px; background: #fff7ed; border: 1px solid #ffd2b8; font-weight: 800; color: #4b423f !important; }
.topic-test-plan, .topic-brief, .topic-followup { margin: 24px 0; }
.topic-metrics { display: grid; gap: 10px; padding-left: 20px; }
.topic-followup ol { margin: 8px 0 0; padding-left: 22px; display: grid; gap: 8px; }
.topic-result-card { min-width: 0; display: flex; flex-direction: column; gap: 10px; padding: 22px; border-radius: 24px; background: rgba(255,255,255,.94); border: 1px solid rgba(234,223,212,.95); box-shadow: 0 10px 30px rgba(58,37,20,.055); }
.topic-result-card.featured { padding: 26px; border-radius: 28px; background: linear-gradient(135deg, #fffaf4, #fff 72%); }
.topic-result-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; color: var(--muted); font-size: 13px; font-weight: 850; }
.topic-result-card h2 { margin: 0; font-size: clamp(22px, 2.35vw, 31px); line-height: 1.2; letter-spacing: -.035em; }
.topic-result-card h2 a { color: #211922; text-decoration: none; overflow-wrap: anywhere; word-break: keep-all; }
.topic-result-card h2 a:hover { color: var(--orange-dark); }
.topic-result-card p { margin: 0; color: #5f5652; line-height: 1.65; }
.topic-result-card .tag-row { margin-top: 0; }
.topic-result-card .text-link { margin-top: auto; width: fit-content; }
.search-chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0 14px; }
.search-chip { display: inline-flex; align-items: center; min-height: 38px; padding: 0 12px; border-radius: 999px; background: #fff7ed; border: 1px solid #ffd2b8; color: var(--orange-dark); font-size: 13px; font-weight: 950; }
.mini-link-list { display: grid; gap: 8px; margin: 12px 0 0; padding-left: 18px; }
.mini-link-list a { color: #2f2724; font-weight: 900; }
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
.radar-article .breadcrumb, .radar-article .article-hero, .radar-article .article-content, .radar-article .related-radar, .radar-article .article-tail, .radar-article .radar-example-gallery { max-width: 940px; margin-left: auto; margin-right: auto; }
.radar-experience-grid { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(280px, .9fr); gap: 18px; margin: 20px 0 26px; align-items: stretch; }
.radar-map-card, .brief-card, .radar-toc-card { background: rgba(255,255,255,.94); border: 1px solid rgba(234,223,212,.95); border-radius: 30px; box-shadow: 0 16px 44px rgba(58,37,20,.09); }
.radar-map-card { position: relative; overflow: hidden; padding: 24px; min-height: 430px; background: linear-gradient(145deg, #fffaf4 0%, #ffffff 52%, #fff1e7 100%); }
.radar-map-card h2 { margin: 6px 0 8px; font-size: clamp(27px, 3.6vw, 42px); }
.radar-map-card p:not(.eyebrow) { max-width: 560px; color: #5f5652; margin-bottom: 20px; }
.radar-map { position: relative; min-height: 285px; margin-top: 12px; border-radius: 28px; overflow: hidden; background: #241b20; box-shadow: inset 0 0 0 1px rgba(255,255,255,.10); }
.radar-map.photo-scan::before { content: ""; position: absolute; inset: 0; z-index: 1; background: linear-gradient(180deg, rgba(20,15,18,.22), rgba(20,15,18,.08) 45%, rgba(20,15,18,.68)); pointer-events: none; }
.radar-map.photo-scan .scan-photo { position: absolute; inset: 0; z-index: 0; display: block; width: 100%; height: 100%; max-height: none; margin: 0; border-radius: 0; object-fit: cover; object-position: center; filter: brightness(1.08) saturate(1.04) contrast(1.02); box-shadow: none; background: #211922; }
.radar-map.photo-scan.missing-photo { background: linear-gradient(145deg, #211922, #3c2b34); }
.map-label { position: absolute; left: 18px; top: 16px; z-index: 3; padding: 8px 12px; border-radius: 999px; background: rgba(20,15,18,.58); color: #fff; border: 1px solid rgba(255,255,255,.32); font-size: 12px; font-weight: 950; backdrop-filter: blur(8px); box-shadow: 0 10px 24px rgba(0,0,0,.20); }
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
.radar-example-gallery { margin: 0 auto 26px; padding: clamp(20px, 3.5vw, 30px); border-radius: 30px; border: 1px solid rgba(234,223,212,.95); background: linear-gradient(135deg, #fffaf4, #ffffff 48%, #eef6ff); box-shadow: 0 16px 44px rgba(58,37,20,.085); }
.example-gallery-head h2 { margin: 4px 0 8px; font-size: clamp(25px, 3.2vw, 36px); }
.example-gallery-head p:not(.eyebrow) { margin: 0 0 18px; color: #5f5652; line-height: 1.65; }
.example-scene-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.example-scene-card { min-width: 0; overflow: hidden; border-radius: 24px; border: 1px solid rgba(234,223,212,.95); background: #fff; box-shadow: 0 10px 26px rgba(58,37,20,.07); }
.scene-frame { position: relative; display: block; min-height: 178px; aspect-ratio: 16 / 9; overflow: hidden; background: #211922; }
.scene-frame::after { content: ""; position: absolute; inset: 0; z-index: 1; background: linear-gradient(180deg, rgba(20,15,18,.12), rgba(20,15,18,.02) 45%, rgba(20,15,18,.46)); pointer-events: none; }
.scene-frame .scene-photo { position: absolute; inset: 0; z-index: 0; display: block; width: 100%; height: 100%; max-height: none; margin: 0; border-radius: 0; object-fit: cover; object-position: center; transform: scale(1.01); filter: brightness(1.13) saturate(1.06) contrast(1.03); box-shadow: none; background: #211922; }
.scene-frame.missing-photo { background: linear-gradient(145deg, #211922, #3c2b34); }
.scene-pin { position: absolute; z-index: 3; display: grid; place-items: center; width: 34px; height: 34px; border-radius: 999px; background: #fff; color: #211922; font-size: 13px; font-weight: 950; box-shadow: 0 10px 22px rgba(0,0,0,.24); }
.scene-pin.pin-a { left: 18px; top: 28px; }
.scene-badge { position: absolute; z-index: 3; left: 14px; bottom: 12px; max-width: calc(100% - 28px); padding: 7px 10px; border-radius: 999px; background: rgba(255,255,255,.92); color: #2f2724; font-size: 12px; font-weight: 950; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; box-shadow: 0 8px 20px rgba(0,0,0,.16); }
.scene-copy { padding: 15px; }
.scene-copy span { display: inline-flex; margin-bottom: 7px; color: var(--muted); font-size: 11px; font-weight: 950; letter-spacing: .06em; }
.scene-copy strong { display: block; font-size: 18px; letter-spacing: -.02em; }
.scene-copy p { margin: 6px 0 0; color: #5f5652; font-size: 14px; line-height: 1.58; overflow-wrap: break-word; word-break: keep-all; }
.radar-situation-strip { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-top: 14px; }
.radar-situation-strip article { padding: 15px; border-radius: 20px; background: rgba(255,255,255,.82); border: 1px solid rgba(234,223,212,.95); }
.radar-situation-strip span { display: block; margin-bottom: 6px; color: var(--orange-dark); font-size: 12px; font-weight: 950; }
.radar-situation-strip p { margin: 0; color: #3f3733; font-size: 14px; line-height: 1.58; overflow-wrap: break-word; word-break: keep-all; }
.radar-situation-strip .field-question { background: #211922; border-color: #211922; }
.radar-situation-strip .field-question span { color: #ffcfb8; }
.radar-situation-strip .field-question p { color: #fff3ec; }
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
.article-content .checklist { width: 100%; max-width: none; box-sizing: border-box; }
.article-content .checklist li { min-width: 0; overflow-wrap: break-word; word-break: keep-all; }
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
.radar-related-search { margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--line); }
.radar-related-search h3 { margin: 0 0 8px; font-size: 18px; }
.radar-related-search .search-chip-row { margin-bottom: 0; }
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
@media (max-width: 1120px) and (min-width: 861px) {
  .seoul-density-panel { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .station-inspector { grid-column: 1 / -1; grid-template-columns: minmax(260px, .72fr) minmax(0, 1fr); align-items: start; }
  .station-inspector .density-compare-card { grid-column: 1 / -1; }
}
@media (max-width: 860px) {
  .seoul-density-panel { grid-template-columns: 1fr; padding: 16px; border-radius: 26px; }
  .station-inspector { grid-template-columns: 1fr; }
  .station-inspector .density-compare-card { grid-column: auto; }
  .seoul-map-canvas { min-height: 330px; }
  .density-score-grid { grid-template-columns: 1fr; }
  .compare-metric-row { grid-template-columns: 1fr; }
  .density-bar { grid-template-columns: 72px 1fr 38px; }
  .station-dot span { opacity: 0; top: calc(100% + 2px); font-size: 10px; pointer-events: none; transition: opacity .14s ease; }
  .station-dot[aria-pressed="true"] span, .station-dot:focus-visible span, .station-dot:hover span { opacity: 1; z-index: 4; background: rgba(15,23,42,.92); }
  .product-hero .hero-actions { margin-top: 18px; }
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
  .grid.three, .grid.two, .status-strip, .shop-summary, .shop-hero, .deal-landing-hero, .site-bridge-strip, .quick-facts, .article-product-hero, .radar-card, .radar-experience-grid, .example-scene-grid, .radar-situation-strip { grid-template-columns: 1fr; }
  .bridge-actions { justify-content: flex-start; }
  .shop-hero { gap: 16px; padding-bottom: 16px; }
  .deal-landing-hero { gap: 18px; margin-top: 18px; padding: 22px; }
  .shopping-room-card { border-radius: 24px; }
  .room-visual { min-height: 330px; }
  .deal-category-rail { align-items: flex-start; flex-direction: column; gap: 10px; }
  .deal-category-rail .category-strip { width: 100%; }
  .deal-hero-copy, .deal-hero-panel, .deal-quick-box, .shopping-room-card { border-radius: 22px; }
  .deal-flow { grid-template-columns: 1fr; }
  .decision-steps { grid-template-columns: 1fr; }
  .decision-steps li { border-right: 0; border-bottom: 1px solid rgba(0,0,0,.08); }
  .decision-steps li:last-child { border-bottom: 0; }
  .category-hub { grid-template-columns: minmax(82px, 104px) minmax(0, 1fr); }
  .deal-grid.best-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .quick-products ol { columns: 1; }
  .category-strip { flex-wrap: wrap; overflow-x: visible; padding-bottom: 0; }
  .category-chip { flex: 0 1 auto; }
  .hero-pin-stack { min-height: auto; display: flex; gap: 10px; overflow-x: auto; padding-bottom: 4px; -webkit-overflow-scrolling: touch; }
  .hero-pin, .hero-pin.pin-1, .hero-pin.pin-2, .hero-pin.pin-3 { position: relative; inset: auto; flex: 0 0 132px; width: 132px; transform: none; border-width: 5px; border-radius: 20px; }
  .hero-pin span { display: none; }
  .card, .panel, .notice, .list-card, .article-content, .related-radar { border-radius: 22px; padding: 22px; }
  .radar-card { padding: 0; }
  .radar-card-visual { min-height: 236px; padding: 19px; }
  .radar-card-visual.has-ai-thumb { min-height: 320px; }
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
  .visual-checklist { right: 0; width: 78px; }
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
  .deal-grid, .mixed-list, .topic-secondary-list { grid-template-columns: 1fr; gap: 12px; }
  .topic-featured-list { max-width: 100%; }
  .topic-result-card, .topic-result-card.featured { padding: 18px; border-radius: 22px; }
  .deal-grid.best-grid { grid-template-columns: 1fr; }
  .deal-landing-hero { padding: 16px; }
  .deal-hero-copy { padding: 0; }
  .shopping-room-card { padding: 12px; }
  .room-card-head { gap: 5px; }
  .room-card-head p { font-size: 13px; }
  .room-visual { min-height: 292px; border-radius: 20px; }
  .room-photo { object-position: center; }
  .room-label { display: none; }
  .room-product { width: 50px; height: 50px; }
  .room-hit-area { inset: 5px; transform: scale(.68); }
  .room-pulse { width: 34px; height: 34px; }
  .room-pin { width: 13px; height: 13px; border-width: 3px; }
  .room-product.kind-air { left: 20%; top: 66%; }
  .room-product.kind-desk { left: 57%; top: 45%; }
  .room-product.kind-sound { left: 82%; top: 25%; }
  .room-product.kind-clean { left: 48%; top: 80%; }
  .room-product.kind-kitchen { left: 84%; top: 55%; }
  .room-product.kind-care { left: 80%; top: 78%; }
  .room-product.kind-daily { left: 66%; top: 67%; }
  .room-preview { padding: 13px; border-radius: 18px; }
  .room-preview-actions { display: grid; grid-template-columns: 1fr; gap: 7px; }
  .room-product-link, .room-preview .text-link { width: 100%; }
  .category-hubs { padding: 8px; border-radius: 22px; }
  .category-hub { grid-template-columns: 1fr; gap: 9px; padding: 13px; }
  .category-hub-label { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
  .playful-badges { flex-wrap: wrap; overflow-x: visible; padding-bottom: 0; }
  .playful-badges span { flex: 0 1 auto; }
  .site-bridge-strip { padding: 18px; border-radius: 22px; }
  .bridge-actions { display: grid; grid-template-columns: 1fr; }
  .affiliate-disclosure { margin-top: 16px; }
  .quick-facts { gap: 8px; }
  .deal-card { display: grid; grid-template-columns: 96px minmax(0, 1fr); border-radius: 22px; }
  .radar-example-gallery { padding: 18px; border-radius: 22px; }
  .scene-frame { min-height: 150px; }
  .scene-copy { padding: 13px; }
  .radar-situation-strip article { padding: 13px; }
  .radar-map-card { padding: 18px; }
  .radar-map { min-height: 420px; border-radius: 24px; }

  .map-label { left: 12px; top: 12px; font-size: 12px; padding: 7px 10px; }
  .node-1 { left: 17%; top: 26%; } .node-2 { left: 58%; top: 28%; } .node-3 { left: 82%; top: 47%; } .node-4 { left: 38%; top: 66%; } .node-5 { left: 72%; top: 83%; }
  .map-node { font-size: 15px; transform: translate(-50%, -21px); }
  .map-node b { width: 42px; height: 42px; }
  .map-node em { padding: 7px 13px; }
  .deal-thumb { min-height: 100%; display: flex; align-items: center; justify-content: center; }
  .deal-thumb img { height: 100%; min-height: 132px; max-height: 168px; aspect-ratio: auto; object-fit: contain; padding: 8px; }
  .deal-text-badge { min-height: 132px; padding: 10px; gap: 8px; font-size: 12px; border-bottom: 0; border-right: 1px solid var(--line); }
  .deal-fallback-icon { width: 48px; height: 48px; border-radius: 17px; font-size: 24px; }
  .deal-fallback-text { min-height: 26px; padding: 0 9px; font-size: 11px; }
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

COMMERCIAL_TOOL_JS = '''(() => {
  const root = document.querySelector('[data-seoul-density-tool-root]');
  if (!root) return;
  const stationSelect = root.querySelector('#tool-station');
  const compareSelect = root.querySelector('#tool-compare-station');
  const industrySelect = root.querySelector('#tool-industry');
  const purposeSelect = root.querySelector('#tool-purpose');
  const mapLayerLabel = root.querySelector('[data-map-layer-label]');
  const scoreRoot = root.querySelector('[data-density-result]');
  const stationMeta = root.querySelector('[data-station-meta]');
  const stationTitle = root.querySelector('[data-station-title]');
  const gradeEl = root.querySelector('[data-risk-grade]');
  const summaryEl = root.querySelector('[data-risk-summary]');
  const countEl = root.querySelector('[data-density-count]');
  const countLabelEl = root.querySelector('[data-density-label]');
  const commercialDensityEl = root.querySelector('[data-commercial-density]');
  const popDensityEl = root.querySelector('[data-pop-density]');
  const popLabelEl = root.querySelector('[data-pop-label]');
  const riskListEl = root.querySelector('[data-risk-list]');
  const barsEl = root.querySelector('[data-density-bars]');
  const linksEl = root.querySelector('[data-recommend-links]');
  const comparePanel = root.querySelector('[data-compare-panel]');
  const compareTitleEl = root.querySelector('[data-compare-title]');
  const compareMetricsEl = root.querySelector('[data-compare-metrics]');
  const compareNoteEl = root.querySelector('[data-compare-note]');
  const sourceNoteEl = root.querySelector('[data-source-note]');
  const layerButtons = Array.from(root.querySelectorAll('[data-density-layer]'));
  const stationButtons = Array.from(root.querySelectorAll('[data-station-map]'));
  if (!stationSelect || !compareSelect || !industrySelect || !purposeSelect || !stationTitle || !riskListEl || !barsEl) return;

  const esc = (value) => String(value || '').replace(/[&<>"]/g, (ch) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
  const link = (href, label) => `<a href="${href}">${esc(label)}</a>`;
  const categoryOrder = ['cafe', 'food', 'convenience', 'beauty', 'clinic', 'academy', 'retail'];
  let payload = null;

  const categoryLabel = (key) => (payload?.categories?.[key] || ({population: '인구밀도'}[key]) || key);
  const maxFor = (key) => {
    if (!payload?.stations?.length) return 1;
    if (key === 'population') return 100;
    return Math.max(1, ...payload.stations.map((station) => Number(station.counts?.[key] || 0)));
  };
  const stationById = (id) => payload?.stations?.find((station) => station.id === id) || payload?.stations?.[0];
  const valueFor = (station, industry) => industry === 'population'
    ? Number(station.population_density_index || 0)
    : Number(station.counts?.[industry] || 0);
  const signed = (value) => `${value > 0 ? '+' : ''}${value}`;
  const compareStationFor = (station) => {
    let compare = stationById(compareSelect.value);
    if (!compare || compare.id === station.id) {
      compare = payload.stations.find((candidate) => candidate.id !== station.id) || station;
      compareSelect.value = compare.id;
    }
    return compare;
  };
  const renderCompare = (station, compare, industry) => {
    if (!comparePanel || !compareTitleEl || !compareMetricsEl || !compareNoteEl) return;
    const selectedDelta = valueFor(station, industry) - valueFor(compare, industry);
    const popDelta = Number(station.population_density_index || 0) - Number(compare.population_density_index || 0);
    const rentDelta = Number(station.rent_pressure_index || 0) - Number(compare.rent_pressure_index || 0);
    const metric = (label, value) => `<div class="${value > 0 ? 'compare-up' : value < 0 ? 'compare-down' : 'compare-same'}"><span>${esc(label)}</span><strong>${signed(value)}</strong></div>`;
    compareTitleEl.textContent = `${station.name} ↔ ${compare.name}`;
    compareMetricsEl.innerHTML = [metric(categoryLabel(industry), selectedDelta), metric('인구밀도', popDelta), metric('임대압력', rentDelta)].join('');
    compareNoteEl.textContent = rentDelta > 7
      ? `${station.name}은 ${compare.name}보다 임대 압력이 높습니다. 권리금·고정비 회수 기간을 더 보수적으로 잡으세요.`
      : rentDelta < -7
        ? `${station.name}은 ${compare.name}보다 임대 압력이 낮습니다. 대신 목적 방문 이유와 반복 동선을 확인하세요.`
        : `${station.name}과 ${compare.name}은 임대 압력이 비슷합니다. 업종 밀도와 생활 동선 차이를 우선 보세요.`;
  };
  const gradeFor = (station, industry) => {
    const density = industry === 'population' ? Number(station.population_density_index || 0) : Number(station.commercial_density_index || 0);
    const rent = Number(station.rent_pressure_index || 0);
    const selectedCount = industry === 'population' ? density : Number(station.counts?.[industry] || 0);
    let score = 86 - Math.round(density * .18) - Math.round(rent * .12);
    if (selectedCount > maxFor(industry) * .72) score -= 13;
    if (selectedCount < maxFor(industry) * .16) score -= 8;
    score = Math.max(28, Math.min(92, score));
    const grade = score >= 74 ? 'good' : score >= 55 ? 'warn' : 'hold';
    return {score, grade, label: grade === 'good' ? '진행' : grade === 'warn' ? '주의' : '보류'};
  };
  const questionsFor = (station, industry, purpose) => {
    const label = categoryLabel(industry);
    if (purpose === 'home') {
      return [
        `${station.name} 주변 인구밀도가 ${station.population_density_label}입니다. 밤 10시 이후 귀가 동선과 소음 방향을 직접 걸어봤나요?`,
        `반경 ${station.radius_m || 650}m 생활 POI가 ${station.total_poi_count || 0}개 잡힙니다. 장보기·병원·운동 동선이 실제 생활 리듬과 맞나요?`,
        `관리비·교통비까지 합친 월 고정비를 같은 예산의 다른 역 후보와 비교했나요?`
      ];
    }
    return [
      industry === 'population'
        ? `인구밀도 지수 ${station.population_density_index || 0}입니다. 거주 기반 업종인지, 출퇴근 유동 기반 업종인지 먼저 나눴나요?`
        : `${label} 기준 주변 매장 ${(station.counts?.[industry] || 0)}개입니다. 같은 고객을 나눠 갖는 직접 경쟁인지 분리했나요?`,
      `${station.name}은 임대 압력 지수 ${station.rent_pressure_index || 0}입니다. 임대료·관리비·권리금 회수 기간을 보수적으로 다시 계산했나요?`,
      `평일 점심·퇴근·주말 3번을 나눠 유입을 세고, 앵커시설 없이도 재방문 이유가 있는지 확인했나요?`
    ];
  };
  const updateMapHeat = (industry) => {
    const max = maxFor(industry);
    stationButtons.forEach((button) => {
      const station = stationById(button.dataset.stationMap);
      if (!station) return;
      const raw = industry === 'population' ? Number(station.population_density_index || 0) : Number(station.counts?.[industry] || 0);
      const heat = Math.max(.18, Math.min(1, raw / max));
      button.style.setProperty('--heat', heat.toFixed(2));
      const small = button.querySelector('small');
      if (small) small.textContent = industry === 'population' ? `${station.population_density_index}` : `${raw}`;
      button.setAttribute('aria-pressed', station.id === stationSelect.value ? 'true' : 'false');
    });
    layerButtons.forEach((button) => button.setAttribute('aria-pressed', button.dataset.densityLayer === industry ? 'true' : 'false'));
    if (mapLayerLabel) mapLayerLabel.textContent = industry === 'population' ? '인구밀도' : `${categoryLabel(industry)} 밀도`;
  };
  const renderBars = (station) => {
    const maxes = Object.fromEntries(categoryOrder.map((key) => [key, maxFor(key)]));
    barsEl.innerHTML = categoryOrder.slice(0, 6).map((key) => {
      const value = Number(station.counts?.[key] || 0);
      const pct = Math.max(4, Math.round(value / maxes[key] * 100));
      return `<div class="density-bar"><b>${esc(categoryLabel(key))}</b><span style="--value:${pct}%"></span><em>${value}</em></div>`;
    }).join('');
  };
  const evaluate = () => {
    if (!payload?.stations?.length) return;
    const station = stationById(stationSelect.value) || payload.stations[0];
    const industry = industrySelect.value || 'cafe';
    const purpose = purposeSelect.value || 'commercial';
    const count = valueFor(station, industry);
    const compare = compareStationFor(station);
    const grade = gradeFor(station, industry);
    root.dataset.grade = grade.grade;
    scoreRoot && (scoreRoot.dataset.grade = grade.grade);
    stationMeta && (stationMeta.textContent = `${station.district} ${station.dong} · ${station.radius_m || 650}m`);
    stationTitle.textContent = `${station.name} ${industry === 'population' ? '인구밀도' : `${categoryLabel(industry)} 밀도`}`;
    gradeEl && (gradeEl.textContent = `${grade.label} ${grade.score}`);
    countEl && (countEl.textContent = String(count));
    countLabelEl && (countLabelEl.textContent = categoryLabel(industry));
    commercialDensityEl && (commercialDensityEl.textContent = String(station.commercial_density_index || 0));
    popDensityEl && (popDensityEl.textContent = String(station.population_density_index || 0));
    popLabelEl && (popLabelEl.textContent = station.population_density_label || '지수');
    summaryEl && (summaryEl.textContent = `${station.name}은 상권 밀도 ${station.commercial_density_label}, 인구밀도 ${station.population_density_label} 구간입니다. ${station.default_take || ''}`);
    riskListEl.innerHTML = questionsFor(station, industry, purpose).map((item) => `<li>${esc(item)}</li>`).join('');
    linksEl && (linksEl.innerHTML = purpose === 'home'
      ? [link('/topics/jeonwolse-contract-check/', '전월세 체크 글 목록'), link('/search/?q=%EB%B0%A4%EA%B8%B8%20%EC%86%8C%EC%9D%8C%20%EC%B2%B4%ED%81%AC', '밤길·소음 검색'), link('/search/?q=%EA%B4%80%EB%A6%AC%EB%B9%84%20%EC%B2%B4%ED%81%AC', '관리비 검색')].join('')
      : [link('/topics/cafe-commercial-lease-risk/', '상가 계약 체크 글 목록'), link('/search/?q=%EC%83%81%EA%B0%80%20%EA%B3%84%EC%95%BD', '상가 계약 검색'), link('/search/?q=%EA%B6%8C%EB%A6%AC%EA%B8%88%20%EB%A6%AC%EC%8A%A4%ED%81%AC', '권리금 검색')].join(''));
    renderBars(station);
    renderCompare(station, compare, industry);
    updateMapHeat(industry);
  };

  const hydrate = (data) => {
    payload = data;
    if (payload?.source_summary && sourceNoteEl) sourceNoteEl.textContent = payload.source_summary;
    evaluate();
  };
  layerButtons.forEach((button) => button.addEventListener('click', () => { industrySelect.value = button.dataset.densityLayer || 'cafe'; evaluate(); }));
  stationButtons.forEach((button) => button.addEventListener('click', () => { stationSelect.value = button.dataset.stationMap || stationSelect.value; evaluate(); }));
  stationSelect.addEventListener('change', evaluate);
  compareSelect.addEventListener('change', evaluate);
  industrySelect.addEventListener('change', evaluate);
  purposeSelect.addEventListener('change', evaluate);

  fetch(root.dataset.densitySrc || '/data/seoul-commercial-areas.json', {cache: 'no-store'})
    .then((res) => res.ok ? res.json() : Promise.reject(new Error(`density data ${res.status}`)))
    .then(hydrate)
    .catch((error) => {
      console.warn('seoul density data load failed', error);
      const embedded = window.SEOUL_COMMERCIAL_AREAS;
      if (embedded) hydrate(embedded);
    });
})();'''


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
      return `<article class="list-card search-result-card">${image}<div class="card-meta"><span class="tag">${esc(item.section === 'deals' ? '쇼핑픽' : item.section === 'radar' ? '동네 레이더' : item.section === 'topics' ? '주제별' : '사이트')}</span></div><h2><a href="${esc(item.path)}">${esc(item.title)}</a></h2><p>${esc(item.description || '')}</p><p class="muted">${esc(meta)}</p><a class="text-link" href="${esc(item.path)}">열기 →</a></article>`;
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
    topic_pages = topic_page_metas()

    bodies = {
        "home": home_body(deals, radar),
        "radar": radar_body(radar),
        "deals": deals_body(deals),
        "topics": topics_body(deals, radar),
        "search": search_body(deals, radar),
        "guides": guides_body(),
        "about": about_body(len(deals), len(radar)),
    }

    for page in STATIC_PAGES:
        write(page["file"], layout(page, bodies[page["section"]]))

    for page in topic_pages:
        write(page["file"], layout(page, topic_page_body(page["topic"], deals, radar)))

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
    write("assets/commercial-check.js", COMMERCIAL_TOOL_JS)
    write("data/seoul-commercial-areas.json", json.dumps(SEOUL_COMMERCIAL_AREAS, ensure_ascii=False, indent=2) + "\n")
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

    all_pages = list(STATIC_PAGES) + topic_pages + radar + deals
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
    ) or "- 공개된 쇼핑픽 없음"
    topic_lines = "\n".join(
        f"- {p['title']}: {BASE}{p['path']}" for p in topic_pages
    ) or "- 주제별 보기 준비중"
    ai_topic_lines = "\n".join(
        f"Topic Page: {BASE}{p['path']} — {p['title']}" for p in topic_pages
    ) or "Topic Page: none"
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
- 주제별 보기: {BASE}/topics/
  - 월세·전세·통근·밤길·상가·생활상품을 주제별로 묶은 고정 랜딩입니다.
- 소개: {BASE}/about/
  - 운영 원칙, 섹션 분리, 검색/AI 공개 원칙을 설명합니다.

## Separate commercial section

- 쇼핑픽: {BASE}/deals/
  - 동네 레이더와 분리된 생활 상품 비교 섹션입니다.
  - 제휴 링크가 포함된 글은 본문에 고지를 표시합니다.
- 사이트 검색: {BASE}/search/
  - 동네 레이더와 쇼핑픽 글을 키워드로 빠르게 찾습니다.

## Dongne Radar articles

{radar_article_lines}

## Topic hubs

{topic_lines}

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
Topic pages: {BASE}/topics/
About: {BASE}/about/
Separate deals section: {BASE}/deals/
Search: {BASE}/search/
Sitemap: {BASE}/sitemap.xml
Feed: {BASE}/feed.xml
LLM guide: {BASE}/llms.txt
{ai_topic_lines}
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
Topic pages: /topics/ groups monthly-rent, jeonse, commute, night/noise, commercial-lease, and shopping-intent pages.
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
        "topic_hubs": [p["path"] for p in topic_pages],
        "article_counts": {"radar": len(radar), "deals": len(deals), "topic_hubs": len(topic_pages)},
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
- Topic Pages: {BASE}/topics/
- About: {BASE}/about/
- Separate Shopping Picks: {BASE}/deals/
- Site Search: {BASE}/search/

## Current content

- Dongne Radar articles: {len(radar)}
- Shopping pick articles: {len(deals)}
- Search intent hubs: {len(topic_pages)}

## Search/AI files

- `{BASE}/sitemap.xml`
- `{BASE}/robots.txt`
- `{BASE}/feed.xml`
- `{BASE}/llms.txt`
- `{BASE}/ai.txt`
- `{BASE}/humans.txt`
- `{BASE}/search/`
- `{BASE}/topics/`
- `{BASE}/data/search-index.json`

## Operating scope

Dongne Radar is the primary editorial scope: 이사, 월세·전세 계약, 통근, 생활권, 현장 확인, 상가 임대차, 권리금 리스크.

## Affiliate rule

제휴 링크가 포함된 쇼핑픽 글에는 본문 상단에 필수 제휴 고지를 표시한다. 동네 레이더 글에는 제휴 문맥을 섞지 않는다.
''')
    write("docs/search-indexing.md", f'''# Search indexing checklist

Public URL: {BASE}/
Sitemap: {BASE}/sitemap.xml
RSS: {BASE}/feed.xml
LLM guide: {BASE}/llms.txt

## Already handled in repo

- robots allows Google, Naver/Yeti, Daumoa, Bing, and major AI/search crawlers.
- sitemap includes static sections, topic page URLs, and generated article URLs.
- every HTML page has canonical, description, OG, RSS, sitemap link, SearchAction JSON-LD, breadcrumb JSON-LD, and page/article JSON-LD.
- `/topics/` gives Google/Search Console fixed landing URLs for 월세·전세·상가·생활상품 intent tests.
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
