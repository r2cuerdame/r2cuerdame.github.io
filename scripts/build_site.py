#!/usr/bin/env python3
"""Build the static Recuerdame Lab GitHub Pages site.

Zero external dependencies. Reads article JSON from content/deals and content/radar,
then writes static section indexes, article pages, SEO files, RSS, and assets.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from email.utils import format_datetime
from pathlib import Path
import html
import json
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
KST = timezone(timedelta(hours=9))
NOW = datetime.now(KST)
TODAY = NOW.date().isoformat()
BASE = "https://r2cuerdame.github.io"
SITE_NAME = "Recuerdame Lab"
SITE_DESC = "동네 신호와 생활 선택을 가볍게 모아두는 공개 큐레이션 노트입니다."
COMMON_KEYWORDS = "동네 레이더, 생활 가이드, Recuerdame Lab"
RADAR_KEYWORDS = "동네 레이더, 전월세 계약, 월세 계약, 서울 동네 분석, 수도권 이사, 현장 확인 질문, 주거 리스크"
DEALS_KEYWORDS = "구매가이드, 생활용품 추천, 상품 비교, 쿠팡 추천, 쇼핑픽, Recuerdame Lab"

STATIC_PAGES = [
    {
        "path": "/",
        "file": "index.html",
        "title": "Recuerdame Lab — 동네 데이터와 생활 구매가이드",
        "description": SITE_DESC,
        "priority": "1.0",
        "type": "WebPage",
        "section": "home",
    },
    {
        "path": "/radar/",
        "file": "radar/index.html",
        "title": "동네 레이더 — Recuerdame Lab",
        "description": "서울과 동네 흐름을 짧고 재사용 가능한 판단 카드로 정리합니다.",
        "priority": "0.8",
        "type": "CollectionPage",
        "section": "radar",
    },
    {
        "path": "/deals/",
        "file": "deals/index.html",
        "title": "쇼핑픽 — Recuerdame Lab",
        "description": "사진으로 먼저 훑어보는 생활 쇼핑픽과 쿠팡 추천 비교글입니다.",
        "priority": "0.8",
        "type": "CollectionPage",
        "section": "deals",
    },
    {
        "path": "/guides/",
        "file": "guides/index.html",
        "title": "생활 가이드 — Recuerdame Lab",
        "description": "생활, 지역, 부동산 기본 가이드를 모으는 섹션입니다.",
        "priority": "0.7",
        "type": "CollectionPage",
        "section": "guides",
    },
    {
        "path": "/about/",
        "file": "about/index.html",
        "title": "소개 — Recuerdame Lab",
        "description": "동네 신호와 생활 쇼핑픽을 모아두는 개인 큐레이션 노트입니다.",
        "priority": "0.4",
        "type": "AboutPage",
        "section": "about",
    },
]

NAV = [
    ("동네 레이더", "/radar/"),
    ("구매가이드", "/deals/"),
    ("가이드", "/guides/"),
    ("소개", "/about/"),
]


class BuildError(RuntimeError):
    pass


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def strip_tags(value: str) -> str:
    value = re.sub(r"<script\b[^>]*>.*?</script>", " ", value or "", flags=re.I | re.S)
    value = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
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


def localize_public_body(body: str) -> str:
    out = str(body or "")
    for source_url, path in SOURCE_URL_TO_PATH.items():
        if source_url:
            out = out.replace(source_url, path)
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
            "priority": str(data.get("priority") or "0.64"),
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
        },
        {
            "@type": ["Organization", "Person"],
            "@id": f"{BASE}/#publisher",
            "name": "r2cuerdame / Recuerdame Lab",
            "url": f"{BASE}/",
        },
        {
            "@type": "SiteNavigationElement",
            "name": [name for name, _ in NAV],
            "url": [f"{BASE}{href}" for _, href in NAV],
        },
    ]
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


def keywords_for(page: dict) -> str:
    section = page.get("section") or ""
    path = str(page.get("path") or "")
    if section == "radar" or path.startswith("/radar/"):
        return RADAR_KEYWORDS
    if section == "deals" or path.startswith("/deals/"):
        return DEALS_KEYWORDS
    return COMMON_KEYWORDS


def layout(page: dict, body: str) -> str:
    canonical = BASE + page["path"]
    title = page["title"]
    description = page["description"]
    keywords = keywords_for(page)
    og_image = page.get("image_url") or f"{BASE}/assets/og-card.svg"
    nav = "\n".join(f'      <a href="{href}">{esc(name)}</a>' for name, href in NAV)
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
  <link rel="stylesheet" href="/main.css" />
  <script type="application/ld+json">{jsonld_for(page)}</script>
</head>
<body>
  <header class="site-header">
    <a class="brand" href="/" aria-label="Recuerdame Lab home">
      <span class="brand-mark">R</span>
      <span><strong>Recuerdame Lab</strong><small>동네 데이터 · 생활 가이드</small></span>
    </a>
    <nav class="nav" aria-label="주요 메뉴">
{nav}
    </nav>
  </header>
  <main>
    {body}
  </main>
  <footer class="footer">
    <p><strong>Recuerdame Lab</strong> — 동네 흐름과 생활 선택을 가볍게 모아두는 공간.</p>
    <p class="muted">섹션별 성격이 다른 글은 본문 안에서 필요한 안내를 따로 표시합니다.</p>
    <p class="muted">마지막 업데이트: <time datetime="{NOW.isoformat(timespec='seconds')}">{NOW.strftime('%Y-%m-%d %H:%M KST')}</time></p>
  </footer>
</body>
</html>
'''


def plain_article_card(a: dict) -> str:
    tags = " ".join(f'<span class="tag pale">{esc(t)}</span>' for t in (a.get("tags") or [])[:3])
    date = parse_dt(a.get("date")).strftime("%Y-%m-%d")
    return f'''<article class="list-card">
  <div class="card-meta"><span class="tag">{esc(a.get('category'))}</span><time datetime="{esc(a.get('date'))}">{date}</time></div>
  <h2><a href="{esc(a['path'])}">{esc(a['title'])}</a></h2>
  <p>{esc(short_text(a['description'], 115))}</p>
  <div class="tag-row">{tags}</div>
  <a class="text-link" href="{esc(a['path'])}">읽어보기 →</a>
</article>'''


def deal_card(a: dict) -> str:
    img = a.get("image_url") or "/assets/og-card.svg"
    date = parse_dt(a.get("date")).strftime("%m.%d")
    deal_url = a.get("primary_deal_url") or ""
    external = ""
    if deal_url:
        external = f'<a class="deal-button ghost" href="{esc(deal_url)}" target="_blank" rel="sponsored nofollow noopener">쿠팡에서 보기</a>'
    return f'''<article class="deal-card">
  <a class="deal-thumb" href="{esc(a['path'])}" aria-label="{esc(a['title'])}">
    <img src="{esc(img)}" alt="{esc(a['title'])} 대표 상품 이미지" loading="lazy" decoding="async" />
    <span class="deal-count">{esc(a.get('item_count_hint'))}</span>
  </a>
  <div class="deal-body">
    <div class="deal-meta"><span>{esc(a.get('category'))}</span><time datetime="{esc(a.get('date'))}">{date}</time></div>
    <h2><a href="{esc(a['path'])}">{esc(a['title'])}</a></h2>
    <p>{esc(short_text(a.get('description') or '', 78))}</p>
    <div class="deal-price">{esc(a.get('price_hint'))}</div>
    <div class="deal-actions">
      <a class="deal-button primary" href="{esc(a['path'])}">비교글 보기</a>
      {external}
    </div>
  </div>
</article>'''


def deal_cards(articles: list[dict]) -> str:
    if not articles:
        return '<article class="list-card"><span class="tag">준비중</span><h2>곧 새로운 쇼핑픽을 올릴게요.</h2><p>사진과 핵심 비교 포인트를 같이 볼 수 있게 준비 중입니다.</p></article>'
    return "\n".join(deal_card(a) for a in articles)


def article_cards(articles: list[dict], empty: str) -> str:
    if not articles:
        return f'<article class="list-card"><span class="tag">준비중</span><h2>{esc(empty)}</h2><p>새 글이 올라오면 이곳에서 바로 볼 수 있습니다.</p></article>'
    cards = []
    for a in articles:
        if a.get("section") == "deals" and a.get("image_url"):
            cards.append(deal_card(a))
        else:
            cards.append(plain_article_card(a))
    return "\n".join(cards)


def category_chips(articles: list[dict]) -> str:
    cats = []
    for a in articles:
        cat = str(a.get("category") or "").strip()
        if cat and cat not in cats:
            cats.append(cat)
    return "".join(f'<span class="category-chip">{esc(c)}</span>' for c in cats[:6])


def hero_pins(articles: list[dict]) -> str:
    pins = []
    for idx, a in enumerate([x for x in articles if x.get("image_url")][:3], start=1):
        pins.append(f'''<a class="hero-pin pin-{idx}" href="{esc(a['path'])}">
  <img src="{esc(a['image_url'])}" alt="{esc(a['title'])}" loading="eager" decoding="async" />
  <span>{esc(a.get('category'))}</span>
</a>''')
    return "\n".join(pins)

def home_body(deals: list[dict], radar: list[dict]) -> str:
    latest = (deals + radar)[:6]
    latest_html = article_cards(latest, "첫 공개 글 준비중") if latest else ""
    return f'''
<section class="hero home-hero">
  <p class="eyebrow">Recuerdame Lab</p>
  <h1>오늘 살 만한 것과 동네 신호를 가볍게 모읍니다.</h1>
  <p class="lead">쇼핑픽은 사진 카드로 빠르게 훑고, 동네 레이더는 짧은 판단 카드로 읽을 수 있게 정리합니다.</p>
  <div class="hero-actions">
    <a class="button primary" href="/deals/">쇼핑픽 보기</a>
    <a class="button" href="/radar/">동네 레이더 보기</a>
  </div>
</section>
<section class="grid three">
  <article class="card accent-orange">
    <span class="tag">Shopping</span>
    <h2>이미지로 보는 쇼핑픽</h2>
    <p>대표 사진, 가격대 힌트, 비교글을 한 카드에서 먼저 확인합니다.</p>
    <a href="/deals/">섹션 열기 →</a>
  </article>
  <article class="card accent-blue">
    <span class="tag">Radar</span>
    <h2>동네 레이더</h2>
    <p>지역·상권·주거 흐름을 바로 써먹기 좋은 판단 문장으로 정리합니다.</p>
    <a href="/radar/">섹션 열기 →</a>
  </article>
  <article class="card accent-green">
    <span class="tag">Guide</span>
    <h2>생활 가이드</h2>
    <p>광고성 추천과 분리해서 읽을 생활/부동산/동네 기본기를 모읍니다.</p>
    <a href="/guides/">섹션 열기 →</a>
  </article>
</section>
<section class="article-list mixed-list">
  <div class="section-title"><h2>최근 올라온 글</h2><p>사진 카드와 짧은 설명으로 먼저 훑어보세요.</p></div>
  {latest_html}
</section>
'''

def deals_body(deals: list[dict]) -> str:
    return f'''
<section class="shop-hero">
  <div class="shop-hero-copy">
    <p class="eyebrow">Shopping Picks</p>
    <h1>사진으로 먼저 보는 오늘의 쇼핑픽</h1>
    <p class="lead">인기 상품을 이미지 카드로 훑고, 마음에 드는 글에서 후보별 장단점과 쿠팡 상품 링크를 바로 확인하세요.</p>
    <div class="category-strip">{category_chips(deals)}</div>
  </div>
  <div class="hero-pin-stack" aria-label="추천 상품 미리보기">
    {hero_pins(deals)}
  </div>
</section>
<section class="notice affiliate compact-notice">
  <strong>제휴 고지</strong>
  <p>이 페이지의 일부 링크는 쿠팡 파트너스 링크이며, 구매 시 일정액의 수수료를 받을 수 있습니다.</p>
</section>
<section class="shop-summary" aria-label="쇼핑픽 요약">
  <div><strong>{len(deals)}개</strong><span>추천글</span></div>
  <div><strong>이미지 카드</strong><span>대표 상품 먼저 보기</span></div>
  <div><strong>가격대 힌트</strong><span>상세가는 상품 페이지 확인</span></div>
</section>
<section class="deal-grid">
  {deal_cards(deals)}
</section>
'''

def radar_body(radar: list[dict]) -> str:
    return f'''
<section class="page-hero compact">
  <p class="eyebrow">Dongne Radar</p>
  <h1>동네 레이더</h1>
  <p class="lead">서울/동네/상권 신호를 바로 써먹을 수 있는 판단 카드로 정리하는 섹션입니다.</p>
</section>
<section class="article-list">
  {article_cards(radar, "서울에서 2030 여성이 빠지는 구 TOP 10")}
</section>
'''

def guides_body() -> str:
    return '''
<section class="page-hero compact">
  <p class="eyebrow">Guides</p>
  <h1>생활 가이드</h1>
  <p class="lead">광고성 추천과 분리된 생활/지역/부동산 기본 가이드를 모읍니다.</p>
</section>
<section class="article-list">
  <article class="list-card">
    <span class="tag">준비중</span>
    <h2>동네를 볼 때 먼저 확인할 5가지</h2>
    <p>인구, 교통, 상권, 전세, 학교/생활 인프라를 빠르게 보는 체크리스트.</p>
  </article>
  <article class="list-card">
    <span class="tag">준비중</span>
    <h2>구매가이드 읽는 법</h2>
    <p>파트너스 글에서 광고와 실제 판단 기준을 분리해 읽는 방법.</p>
  </article>
</section>
'''


def about_body(deals_count: int, radar_count: int) -> str:
    return f'''
<section class="page-hero compact">
  <p class="eyebrow">About</p>
  <h1>Recuerdame Lab</h1>
  <p class="lead">동네를 볼 때 필요한 신호와 생활 속 구매 후보를 가볍게 모아두는 개인 큐레이션 공간입니다.</p>
</section>
<section class="panel">
  <h2>무엇을 올리나</h2>
  <p>동네 레이더는 지역 흐름을 짧게 정리하고, 쇼핑픽은 생활에 바로 쓰는 상품 비교글을 사진 중심으로 모읍니다.</p>
  <h2>현재 공개 수</h2>
  <p>쇼핑픽 {deals_count}개, 동네 레이더 {radar_count}개를 공개 중입니다.</p>
</section>
'''

def article_body(article: dict) -> str:
    section_name = "쇼핑픽" if article["section"] == "deals" else "동네 레이더"
    section_href = f"/{article['section']}/"
    dt = parse_dt(article.get("date"))
    tags = " ".join(f'<span class="tag pale">{esc(t)}</span>' for t in (article.get("tags") or [])[:8])
    notice = ""
    if article.get("is_affiliate"):
        notice = '<section class="notice affiliate compact-notice"><strong>제휴 고지</strong><p>이 글은 쿠팡 파트너스 활동의 일환으로 작성될 수 있으며, 이에 따른 일정액의 수수료를 제공받을 수 있습니다.</p></section>'
    image_block = ""
    if article.get("section") == "deals" and article.get("image_url"):
        external = ""
        if article.get("primary_deal_url"):
            external = f'<a class="deal-button ghost" href="{esc(article["primary_deal_url"])}" target="_blank" rel="sponsored nofollow noopener">대표 상품 보기</a>'
        image_block = f'''<section class="article-product-hero">
  <img src="{esc(article['image_url'])}" alt="{esc(article['title'])} 대표 상품 이미지" loading="eager" decoding="async" />
  <div>
    <span class="tag">{esc(article.get('item_count_hint'))}</span>
    <h2>사진으로 먼저 보고, 아래에서 후보별로 비교하세요.</h2>
    <p>{esc(article.get('price_hint'))}</p>
    <div class="deal-actions"><a class="deal-button primary" href="#article-body">본문 비교 보기</a>{external}</div>
  </div>
</section>'''
    return f'''
<article class="article-page">
  <nav class="breadcrumb" aria-label="breadcrumb"><a href="/">홈</a><span>›</span><a href="{section_href}">{esc(section_name)}</a></nav>
  <header class="article-hero">
    <p class="eyebrow">{esc(section_name)}</p>
    <h1>{esc(article['title'])}</h1>
    <p class="lead">{esc(article['description'])}</p>
    <div class="article-meta"><span>{esc(article.get('category'))}</span><time datetime="{esc(article.get('date'))}">{dt.strftime('%Y-%m-%d %H:%M KST')}</time></div>
    <div class="tag-row">{tags}</div>
  </header>
  {notice}
  {image_block}
  <section id="article-body" class="article-content">
    {article['body_html']}
  </section>
  <footer class="article-tail">
    <a class="button" href="{section_href}">목록으로</a>
  </footer>
</article>
'''


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
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", "Segoe UI", sans-serif;
  background: radial-gradient(circle at top left, #ffe4d2 0, transparent 30%), radial-gradient(circle at 85% 8%, #fff0b8 0, transparent 25%), var(--bg);
  color: var(--ink);
  line-height: 1.6;
}
a { color: inherit; text-decoration: none; }
a:hover { color: var(--orange-dark); }
.site-header {
  position: sticky; top: 0; z-index: 20;
  display: flex; align-items: center; justify-content: space-between; gap: 24px;
  padding: 16px clamp(18px, 5vw, 64px);
  background: rgba(255, 250, 244, 0.88);
  backdrop-filter: blur(18px);
  border-bottom: 1px solid rgba(234, 223, 212, 0.85);
}
.brand { display: flex; align-items: center; gap: 12px; }
.brand-mark {
  display: grid; place-items: center;
  width: 42px; height: 42px; border-radius: 14px;
  background: var(--ink); color: #fff; font-weight: 900;
}
.brand strong, .brand small { display: block; }
.brand small { color: var(--muted); font-size: 12px; }
.nav { display: flex; gap: 16px; flex-wrap: wrap; color: #4b423f; font-weight: 800; }
main { width: min(1240px, calc(100% - 32px)); margin: 0 auto; }
.hero { padding: clamp(50px, 9vw, 96px) 0 40px; }
.page-hero { padding: 58px 0 28px; }
.compact { max-width: 860px; }
.eyebrow { color: var(--orange-dark); font-weight: 950; letter-spacing: .12em; text-transform: uppercase; font-size: 13px; }
h1 { font-size: clamp(40px, 7vw, 76px); line-height: 1.04; letter-spacing: -0.055em; margin: 10px 0 18px; }
.compact h1, .article-hero h1 { font-size: clamp(34px, 5.4vw, 60px); }
h2 { letter-spacing: -0.035em; line-height: 1.18; }
.lead { color: #5f5652; font-size: clamp(18px, 2.1vw, 23px); max-width: 850px; }
.hero-actions { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 28px; }
.button, .deal-button {
  display: inline-flex; align-items: center; justify-content: center;
  min-height: 46px; padding: 0 18px; border-radius: 16px;
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
.accent-blue { border-top: 5px solid var(--blue); }
.accent-orange, .accent-amber { border-top: 5px solid var(--orange); }
.accent-green { border-top: 5px solid var(--green); }
.panel, .notice { margin: 28px 0; }
.panel.soft { background: #fffaf4; }
.notice.affiliate { border-color: #ffd2b8; background: linear-gradient(135deg, #fff7ed, #fff); }
.compact-notice { padding: 18px 22px; }
.compact-notice p { margin: 4px 0 0; }
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
.section-title { grid-column: 1 / -1; }
.section-title h2 { margin-bottom: 4px; }
.section-title p { margin-top: 0; color: var(--muted); }
.list-card h2 { margin-bottom: 8px; }
.card-meta, .article-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; color: var(--muted); font-size: 14px; font-weight: 800; }
.text-link { color: var(--orange-dark); font-weight: 950; }
.shop-hero {
  display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(320px, .95fr); gap: clamp(24px, 6vw, 72px);
  align-items: center; padding: clamp(44px, 8vw, 88px) 0 28px;
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
.deal-actions .deal-button { min-height: 42px; padding: 0 13px; font-size: 13px; flex: 1 1 auto; }
.breadcrumb { display: flex; gap: 8px; color: var(--muted); font-size: 14px; margin-top: 32px; }
.article-page { max-width: 940px; margin: 0 auto; }
.article-hero { padding: 44px 0 18px; }
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
  overflow-wrap: anywhere;
  word-break: keep-all;
}
.article-content h2 { margin-top: 34px; font-size: clamp(24px, 3.4vw, 32px); }
.article-content h3 { margin-top: 26px; font-size: 22px; }
.article-content p { color: #3f3733; }
.article-content img { max-width: 100%; height: auto; border-radius: 18px; box-shadow: 0 8px 24px rgba(58, 37, 20, .08); }
.article-content a {
  color: var(--orange-dark);
  font-weight: 950;
  text-decoration: underline;
  text-underline-offset: 3px;
}
.article-content table { width: 100%; border-collapse: collapse; display: block; overflow-x: auto; }
.article-content th, .article-content td { border: 1px solid var(--line); padding: 10px; }
.article-tail { margin: 28px 0 70px; }
.footer {
  width: min(1240px, calc(100% - 32px)); margin: 56px auto 0; padding: 28px 0 40px;
  border-top: 1px solid var(--line); color: #5f5652;
}
.muted { color: var(--muted); font-size: 14px; }
@media (max-width: 860px) {
  .site-header { position: static; align-items: flex-start; flex-direction: column; }
  .nav { gap: 10px; font-size: 14px; }
  .grid.three, .grid.two, .status-strip, .shop-summary, .shop-hero, .article-product-hero { grid-template-columns: 1fr; }
  .hero-pin-stack { min-height: auto; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
  .hero-pin, .hero-pin.pin-1, .hero-pin.pin-2, .hero-pin.pin-3 { position: relative; inset: auto; width: 100%; transform: none; border-width: 5px; border-radius: 20px; }
  .hero-pin span { display: none; }
  .card, .panel, .notice, .list-card, .article-content { border-radius: 22px; padding: 22px; }
  .article-page { max-width: 100%; }
}
@media (max-width: 560px) {
  main { width: min(100% - 24px, 1240px); }
  .deal-grid, .mixed-list { grid-template-columns: 1fr; }
  .hero-pin-stack { grid-template-columns: repeat(2, 1fr); }
  .hero-pin.pin-3 { display: none; }
}
'''

LOGO = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" aria-label="Recuerdame Lab"><rect width="128" height="128" rx="34" fill="#101828"/><path d="M38 91V31h32c13 0 22 8 22 20 0 9-5 16-13 19l17 21H76L62 72h-8v19H38Zm16-33h14c6 0 10-3 10-8s-4-8-10-8H54v16Z" fill="#fff"/><circle cx="93" cy="36" r="8" fill="#60a5fa"/></svg>'''

OG = '''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630"><defs><linearGradient id="g" x1="0" x2="1"><stop stop-color="#101828"/><stop offset="1" stop-color="#1d4ed8"/></linearGradient></defs><rect width="1200" height="630" fill="url(#g)"/><circle cx="1030" cy="120" r="210" fill="#60a5fa" opacity=".22"/><circle cx="170" cy="520" r="190" fill="#f59e0b" opacity=".22"/><text x="80" y="220" fill="#fff" font-family="Arial, sans-serif" font-size="72" font-weight="800">Recuerdame Lab</text><text x="80" y="315" fill="#e5e7eb" font-family="Arial, sans-serif" font-size="38">동네 데이터 · 생활 구매가이드</text><text x="80" y="405" fill="#bfdbfe" font-family="Arial, sans-serif" font-size="30">Search and AI ready public hub</text></svg>'''


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
        "guides": guides_body(),
        "about": about_body(len(deals), len(radar)),
    }

    for page in STATIC_PAGES:
        write(page["file"], layout(page, bodies[page["section"]]))

    for article in deals + radar:
        write(article["file"], layout(article, article_body(article)))

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
    write(".nojekyll", "")
    write("robots.txt", f'''User-agent: *
Allow: /

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

    all_pages = list(STATIC_PAGES) + deals + radar
    sitemap_items = "\n".join(
        f'  <url><loc>{BASE}{p["path"]}</loc><lastmod>{parse_dt(p.get("date")).date().isoformat() if p.get("type") == "BlogPosting" else TODAY}</lastmod><changefreq>{"weekly" if p.get("type") == "BlogPosting" else "daily"}</changefreq><priority>{p.get("priority", "0.64")}</priority></url>'
        for p in all_pages
    )
    write("sitemap.xml", f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{sitemap_items}
</urlset>
''')

    rss_source = (deals + radar)[:20] or STATIC_PAGES[:4]
    rss_items = "\n".join(
        f'''<item><title>{esc(p["title"])}</title><link>{BASE}{p["path"]}</link><guid>{BASE}{p["path"]}</guid><pubDate>{format_datetime(parse_dt(p.get("date")))}</pubDate><description>{esc(p["description"])}</description></item>'''
        for p in rss_source
    )
    write("feed.xml", f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Recuerdame Lab</title><link>{BASE}/</link><description>{esc(SITE_DESC)}</description><language>ko-KR</language><lastBuildDate>{format_datetime(NOW)}</lastBuildDate>{rss_items}</channel></rss>
''')

    article_lines = "\n".join(
        f"- {a['title']}: {BASE}{a['path']}" for a in (deals + radar)[:30]
    ) or "- 아직 공개 글 없음"
    write("llms.txt", f'''# Recuerdame Lab

> 동네 신호와 생활 쇼핑픽을 모아두는 한국어 공개 큐레이션 노트입니다.

Base URL: {BASE}/
Language: ko-KR
Last updated: {NOW.isoformat(timespec='seconds')}

## Sections

- 동네 레이더: {BASE}/radar/
  - 서울/동네/상권/주거 흐름을 판단 카드로 정리합니다.
- 쇼핑픽: {BASE}/deals/
  - 생활에 바로 쓰는 쿠팡 추천과 상품 비교글을 사진 카드로 모읍니다.
  - 제휴 링크가 포함된 글은 본문에 고지를 표시합니다.
- 생활 가이드: {BASE}/guides/
  - 생활, 지역, 부동산 기본 가이드를 모읍니다.

## Latest public articles

{article_lines}

## Crawl hints

- Canonical site: {BASE}/
- Sitemap: {BASE}/sitemap.xml
- RSS: {BASE}/feed.xml
- Robots: {BASE}/robots.txt

## Citation preference

When citing this site, cite the canonical page URL and use the page title. Prefer Korean summaries for Korean queries.
''')
    write("ai.txt", f'''Recuerdame Lab allows AI search crawlers and answer engines to discover, index, summarize, and cite public pages on this site.

Canonical: {BASE}/
Radar: {BASE}/radar/
Deals: {BASE}/deals/
Guides: {BASE}/guides/
Sitemap: {BASE}/sitemap.xml
Feed: {BASE}/feed.xml
LLM guide: {BASE}/llms.txt
Language: ko-KR
Updated: {NOW.isoformat(timespec='seconds')}
''')
    write("humans.txt", f'''Recuerdame Lab
Owner: r2cuerdame
Site: {BASE}/
Language: Korean
Purpose: Dongne Radar, lifestyle guides, and Coupang shopping picks.
Updated: {NOW.isoformat(timespec='seconds')}
''')
    write("build-info.json", json.dumps({
        "site": SITE_NAME,
        "base_url": BASE,
        "built_at": NOW.isoformat(timespec="seconds"),
        "timezone": "Asia/Seoul",
        "sections": [p["path"] for p in STATIC_PAGES],
        "article_counts": {"deals": len(deals), "radar": len(radar)},
        "search_ready": ["google", "naver", "daum", "ai_search"],
        "sitemap": f"{BASE}/sitemap.xml",
        "rss": f"{BASE}/feed.xml",
        "llms": f"{BASE}/llms.txt",
    }, ensure_ascii=False, indent=2) + "\n")
    write("README.md", f'''# Recuerdame Lab — r2cuerdame.github.io

Public note for Dongne Radar, 생활 가이드, and Coupang shopping picks.

## Live URLs

- Home: {BASE}/
- Dongne Radar: {BASE}/radar/
- Shopping Picks: {BASE}/deals/
- Guides: {BASE}/guides/

## Current content

- Shopping pick articles: {len(deals)}
- Dongne Radar articles: {len(radar)}

## Search/AI files

- `{BASE}/sitemap.xml`
- `{BASE}/robots.txt`
- `{BASE}/feed.xml`
- `{BASE}/llms.txt`
- `{BASE}/ai.txt`

## Daily deploy

새 쇼핑픽은 `content/deals/`에 추가되고 정적 페이지로 공개됩니다.

## Affiliate rule

제휴 링크가 포함된 글에는 본문 상단에 쿠팡 파트너스 고지를 표시한다.
''')
    write("docs/search-indexing.md", f'''# Search indexing checklist

Public URL: {BASE}/
Sitemap: {BASE}/sitemap.xml
RSS: {BASE}/feed.xml
LLM guide: {BASE}/llms.txt

## Already handled in repo

- robots allows Google, Naver/Yeti, Daumoa, Bing, and major AI/search crawlers.
- sitemap includes static sections and generated article URLs.
- every HTML page has canonical, description, OG, RSS, sitemap link, and JSON-LD.
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
