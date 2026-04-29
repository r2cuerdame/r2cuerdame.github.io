#!/usr/bin/env python3
"""Build the static Recuerdame Lab GitHub Pages site.

This intentionally has zero external dependencies so GitHub Actions can run it daily.
It refreshes SEO surfaces that crawlers use: sitemap lastmod, RSS, llms.txt,
robots.txt, build-info.json, and page-level structured data.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import html
import json

ROOT = Path(__file__).resolve().parents[1]
KST = timezone(timedelta(hours=9))
NOW = datetime.now(KST)
TODAY = NOW.date().isoformat()
BASE = "https://r2cuerdame.github.io"
SITE_NAME = "Recuerdame Lab"
SITE_DESC = "동네 데이터와 생활 구매가이드를 쌓는 공개 노트. 동네 레이더와 파트너스 픽을 분리 운영합니다."
COMMON_KEYWORDS = "동네 레이더, 지역 데이터, 서울 동네 분석, 생활 가이드, 구매가이드, 쿠팡 파트너스, Recuerdame Lab"

PAGES = [
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
        "title": "파트너스 픽 — Recuerdame Lab",
        "description": "쿠팡 파트너스 추천글과 구매가이드를 일반 정보글과 분리해 운영합니다.",
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
        "description": "r2cuerdame 개인 GitHub Pages 공개 허브 소개입니다.",
        "priority": "0.4",
        "type": "AboutPage",
        "section": "about",
    },
]


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def jsonld_for(page: dict) -> str:
    path = page["path"]
    url = BASE + path
    graph = [
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
            "name": ["동네 레이더", "파트너스 픽", "생활 가이드", "소개"],
            "url": [f"{BASE}/radar/", f"{BASE}/deals/", f"{BASE}/guides/", f"{BASE}/about/"],
        },
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
        },
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))


def layout(page: dict, body: str) -> str:
    canonical = BASE + page["path"]
    title = page["title"]
    description = page["description"]
    return f'''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}" />
  <meta name="keywords" content="{esc(COMMON_KEYWORDS)}" />
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
  <meta property="og:type" content="website" />
  <meta property="og:locale" content="ko_KR" />
  <meta property="og:site_name" content="{esc(SITE_NAME)}" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(description)}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:image" content="{BASE}/assets/og-card.svg" />
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
      <a href="/radar/">동네 레이더</a>
      <a href="/deals/">파트너스 픽</a>
      <a href="/guides/">가이드</a>
      <a href="/about/">소개</a>
    </nav>
  </header>
  <main>
    {body}
  </main>
  <footer class="footer">
    <p><strong>Recuerdame Lab</strong> — 자체 데이터/편집 기준으로 운영하는 공개 콘텐츠 허브.</p>
    <p class="muted">파트너스/제휴 링크가 포함된 글은 본문에 별도 고지를 표시합니다. 게시 전 품질·정책 검수를 통과한 글만 공개합니다.</p>
    <p class="muted">마지막 사이트 갱신: <time datetime="{NOW.isoformat(timespec='seconds')}">{NOW.strftime('%Y-%m-%d %H:%M KST')}</time></p>
  </footer>
</body>
</html>
'''


BODIES = {
    "home": '''
<section class="hero">
  <p class="eyebrow">GitHub Pages 파일럿</p>
  <h1>동네 데이터와 생활 구매가이드를 한 곳에 쌓습니다.</h1>
  <p class="lead">Tistory/블로그 보안확인에 묶이지 않도록, 원본 콘텐츠는 GitHub Pages에 자동 배포하고 네이버·Tistory·쿠팡 파트너스 채널은 보조 배포면으로 분리합니다.</p>
  <div class="hero-actions">
    <a class="button primary" href="/radar/">동네 레이더 보기</a>
    <a class="button" href="/deals/">파트너스 픽 준비 현황</a>
  </div>
</section>
<section class="grid three">
  <article class="card accent-blue">
    <span class="tag">Radar</span>
    <h2>동네 레이더</h2>
    <p>지역·상권·주거 흐름을 짧고 재사용 가능한 판단 문장으로 정리합니다.</p>
    <a href="/radar/">섹션 열기 →</a>
  </article>
  <article class="card accent-amber">
    <span class="tag">Partners</span>
    <h2>파트너스 픽</h2>
    <p>쿠팡 파트너스용 추천·비교·구매가이드를 별도 카테고리로 분리합니다.</p>
    <a href="/deals/">섹션 열기 →</a>
  </article>
  <article class="card accent-green">
    <span class="tag">Guides</span>
    <h2>생활 가이드</h2>
    <p>광고성 글과 분리된 생활/부동산/동네 사용법 가이드를 보관합니다.</p>
    <a href="/guides/">섹션 열기 →</a>
  </article>
</section>
<section class="panel">
  <h2>검색 노출 기본 세팅</h2>
  <ul class="checklist">
    <li>Google, Naver, Daum 크롤러가 읽을 수 있게 robots와 sitemap을 공개합니다.</li>
    <li>AI 검색/요약 도구가 구조를 이해하도록 llms.txt와 JSON-LD를 제공합니다.</li>
    <li>제휴 글은 일반 동네 데이터 글과 URL·디자인·고지를 분리합니다.</li>
    <li>매일 자동 갱신으로 sitemap lastmod와 RSS가 살아있게 유지됩니다.</li>
  </ul>
</section>
<section class="status-strip" aria-label="현재 상태">
  <div><strong>배포</strong><span>GitHub Pages</span></div>
  <div><strong>원본 URL</strong><span>r2cuerdame.github.io</span></div>
  <div><strong>상태</strong><span>매일 자동 배포 준비</span></div>
</section>
''',
    "radar": '''
<section class="page-hero compact">
  <p class="eyebrow">Dongne Radar</p>
  <h1>동네 레이더</h1>
  <p class="lead">서울/동네/상권 신호를 사람이 바로 써먹을 수 있는 판단 카드로 정리하는 섹션입니다.</p>
</section>
<section class="article-list">
  <article class="list-card">
    <span class="tag">준비중</span>
    <h2>서울에서 2030 여성이 빠지는 구 TOP 10</h2>
    <p>현재 수동 패키지/검수 라인에 있는 글입니다. GitHub Pages 이관 후 정식 글 URL로 공개합니다.</p>
  </article>
  <article class="list-card">
    <span class="tag">운영</span>
    <h2>지역 신호 읽기 기본 프레임</h2>
    <p>인구, 전세, 거래, 상권, 생활 인프라를 함께 보는 기본 해석법을 정리할 예정입니다.</p>
  </article>
</section>
<section class="panel soft">
  <h2>검색 세팅</h2>
  <p>sitemap/RSS/canonical/schema 기반으로 네이버 Search Advisor, Google Search Console, Daum 검색 등록을 전제로 구성했습니다.</p>
</section>
''',
    "deals": '''
<section class="page-hero compact">
  <p class="eyebrow">Partners Pick</p>
  <h1>파트너스 픽</h1>
  <p class="lead">쿠팡 파트너스 추천글은 동네 레이더와 섞지 않고 이 섹션에서 따로 운영합니다.</p>
</section>
<section class="notice affiliate">
  <h2>제휴 고지</h2>
  <p>이 섹션의 일부 글은 쿠팡 파트너스 활동의 일환으로 작성될 수 있으며, 이에 따른 일정액의 수수료를 제공받을 수 있습니다. 실제 제휴 링크가 포함된 글에는 본문 상단에 별도 고지를 다시 표시합니다.</p>
</section>
<section class="grid two">
  <article class="card">
    <span class="tag">예정</span>
    <h2>구매가이드형 글</h2>
    <p>제품군별 비교 기준, 가격대, 실패 방지 체크리스트를 먼저 제공하고 CTA는 분리합니다.</p>
  </article>
  <article class="card">
    <span class="tag">예정</span>
    <h2>추천/비교형 글</h2>
    <p>검수 통과 상품 풀만 사용하고, placeholder 상품이나 약한 검색링크 글은 공개하지 않습니다.</p>
  </article>
</section>
<section class="panel soft">
  <h2>발행 기준</h2>
  <ul class="checklist">
    <li>제휴 고지 포함</li>
    <li>실제 상품 링크와 가격/재고 변동 주의문 포함</li>
    <li>모바일 가독성 검수</li>
    <li>일반 정보글과 제휴 CTA 분리</li>
  </ul>
</section>
''',
    "guides": '''
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
''',
    "about": '''
<section class="page-hero compact">
  <p class="eyebrow">About</p>
  <h1>Recuerdame Lab</h1>
  <p class="lead">반복 발행 플랫폼에 묶이지 않기 위해 만든 개인 GitHub Pages 공개 허브입니다.</p>
</section>
<section class="panel">
  <h2>무엇을 올리나</h2>
  <p>동네 레이더의 지역 데이터 글, 생활 가이드, 검수된 파트너스 추천글을 분리된 섹션에 공개합니다.</p>
  <h2>왜 GitHub Pages인가</h2>
  <p>새 도메인 없이 빠르게 열 수 있고, 원본 파일/배포 이력이 GitHub에 남으며, SEO 기본 파일을 직접 제어할 수 있기 때문입니다.</p>
</section>
''',
}

CSS = '''
:root {
  --bg: #f6f7fb;
  --ink: #101828;
  --muted: #667085;
  --line: #d8dee9;
  --card: #ffffff;
  --blue: #2563eb;
  --green: #059669;
  --amber: #d97706;
  --shadow: 0 22px 70px rgba(16, 24, 40, 0.10);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", "Segoe UI", sans-serif;
  background: radial-gradient(circle at top left, #e0ecff 0, transparent 35%), var(--bg);
  color: var(--ink);
  line-height: 1.65;
}
a { color: inherit; text-decoration: none; }
a:hover { color: var(--blue); }
.site-header {
  position: sticky; top: 0; z-index: 20;
  display: flex; align-items: center; justify-content: space-between; gap: 24px;
  padding: 18px clamp(18px, 5vw, 64px);
  background: rgba(246, 247, 251, 0.82);
  backdrop-filter: blur(18px);
  border-bottom: 1px solid rgba(216, 222, 233, 0.8);
}
.brand { display: flex; align-items: center; gap: 12px; }
.brand-mark {
  display: grid; place-items: center;
  width: 42px; height: 42px; border-radius: 14px;
  background: #101828; color: #fff; font-weight: 900;
}
.brand strong, .brand small { display: block; }
.brand small { color: var(--muted); font-size: 12px; }
.nav { display: flex; gap: 16px; flex-wrap: wrap; color: #344054; font-weight: 700; }
main { width: min(1120px, calc(100% - 32px)); margin: 0 auto; }
.hero { padding: clamp(56px, 10vw, 110px) 0 48px; }
.page-hero { padding: 64px 0 32px; }
.compact { max-width: 760px; }
.eyebrow { color: var(--blue); font-weight: 900; letter-spacing: .12em; text-transform: uppercase; font-size: 13px; }
h1 { font-size: clamp(42px, 7vw, 78px); line-height: 1.04; letter-spacing: -0.05em; margin: 10px 0 18px; }
.compact h1 { font-size: clamp(38px, 6vw, 64px); }
h2 { letter-spacing: -0.03em; line-height: 1.2; }
.lead { color: #475467; font-size: clamp(18px, 2.2vw, 23px); max-width: 840px; }
.hero-actions { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 30px; }
.button {
  display: inline-flex; align-items: center; justify-content: center;
  min-height: 48px; padding: 0 18px; border-radius: 999px;
  border: 1px solid var(--line); background: #fff; font-weight: 900;
}
.button.primary { background: var(--ink); color: #fff; border-color: var(--ink); }
.grid { display: grid; gap: 18px; margin: 28px 0; }
.grid.three { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.grid.two { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.card, .panel, .notice, .list-card {
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(216, 222, 233, .9);
  border-radius: 28px;
  padding: 26px;
  box-shadow: 0 10px 35px rgba(16, 24, 40, .06);
}
.card { min-height: 230px; display: flex; flex-direction: column; justify-content: space-between; }
.tag { display: inline-flex; align-self: flex-start; border-radius: 999px; padding: 4px 10px; background: #eef4ff; color: #1d4ed8; font-size: 12px; font-weight: 900; }
.card p, .list-card p, .panel p, .notice p { color: #475467; }
.accent-blue { border-top: 5px solid var(--blue); }
.accent-amber { border-top: 5px solid var(--amber); }
.accent-green { border-top: 5px solid var(--green); }
.panel, .notice { margin: 28px 0; }
.panel.soft { background: #f9fafb; }
.notice.affiliate { border-color: #fed7aa; background: #fff7ed; }
.checklist { padding-left: 0; list-style: none; }
.checklist li { position: relative; padding-left: 28px; margin: 10px 0; }
.checklist li::before { content: "✓"; position: absolute; left: 0; color: var(--green); font-weight: 900; }
.status-strip {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;
  margin: 32px 0 64px;
}
.status-strip div { background: #101828; color: #fff; border-radius: 22px; padding: 18px; }
.status-strip strong, .status-strip span { display: block; }
.status-strip span { color: #cbd5e1; }
.article-list { display: grid; gap: 16px; margin: 24px 0 56px; }
.footer {
  width: min(1120px, calc(100% - 32px)); margin: 56px auto 0; padding: 28px 0 40px;
  border-top: 1px solid var(--line); color: #475467;
}
.muted { color: var(--muted); font-size: 14px; }
@media (max-width: 760px) {
  .site-header { position: static; align-items: flex-start; flex-direction: column; }
  .nav { gap: 10px; font-size: 14px; }
  .grid.three, .grid.two, .status-strip { grid-template-columns: 1fr; }
  .card, .panel, .notice, .list-card { border-radius: 22px; padding: 22px; }
}
'''

LOGO = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" aria-label="Recuerdame Lab"><rect width="128" height="128" rx="34" fill="#101828"/><path d="M38 91V31h32c13 0 22 8 22 20 0 9-5 16-13 19l17 21H76L62 72h-8v19H38Zm16-33h14c6 0 10-3 10-8s-4-8-10-8H54v16Z" fill="#fff"/><circle cx="93" cy="36" r="8" fill="#60a5fa"/></svg>'''

OG = '''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630"><defs><linearGradient id="g" x1="0" x2="1"><stop stop-color="#101828"/><stop offset="1" stop-color="#1d4ed8"/></linearGradient></defs><rect width="1200" height="630" fill="url(#g)"/><circle cx="1030" cy="120" r="210" fill="#60a5fa" opacity=".22"/><circle cx="170" cy="520" r="190" fill="#f59e0b" opacity=".22"/><text x="80" y="220" fill="#fff" font-family="Arial, sans-serif" font-size="72" font-weight="800">Recuerdame Lab</text><text x="80" y="315" fill="#e5e7eb" font-family="Arial, sans-serif" font-size="38">동네 데이터 · 생활 구매가이드</text><text x="80" y="405" fill="#bfdbfe" font-family="Arial, sans-serif" font-size="30">Search and AI ready public hub</text></svg>'''


def write(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def build() -> None:
    # Pages
    by_section = {p["section"]: p for p in PAGES}
    for page in PAGES:
        write(page["file"], layout(page, BODIES[page["section"]]))
    write("404.html", layout({
        "path": "/404.html",
        "title": "페이지를 찾을 수 없습니다 — Recuerdame Lab",
        "description": "요청한 페이지를 찾을 수 없습니다.",
        "type": "WebPage",
        "section": "404",
    }, '<section class="page-hero compact"><h1>페이지를 찾을 수 없습니다.</h1><p class="lead">주소를 확인하거나 홈으로 돌아가세요.</p><a class="button primary" href="/">홈으로</a></section>'))

    # Assets and SEO files
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
    sitemap_items = "\n".join(
        f'  <url><loc>{BASE}{p["path"]}</loc><lastmod>{TODAY}</lastmod><changefreq>daily</changefreq><priority>{p["priority"]}</priority></url>'
        for p in PAGES
    )
    write("sitemap.xml", f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{sitemap_items}
</urlset>
''')
    rss_items = "\n".join(
        f'''<item><title>{esc(p["title"])}</title><link>{BASE}{p["path"]}</link><guid>{BASE}{p["path"]}</guid><pubDate>{NOW.strftime('%a, %d %b %Y %H:%M:%S +0900')}</pubDate><description>{esc(p["description"])}</description></item>'''
        for p in PAGES[:4]
    )
    write("feed.xml", f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Recuerdame Lab</title><link>{BASE}/</link><description>{esc(SITE_DESC)}</description><language>ko-KR</language><lastBuildDate>{NOW.strftime('%a, %d %b %Y %H:%M:%S +0900')}</lastBuildDate>{rss_items}</channel></rss>
''')
    write("llms.txt", f'''# Recuerdame Lab

> 동네 데이터와 생활 구매가이드를 쌓는 한국어 공개 콘텐츠 허브입니다.

Base URL: {BASE}/
Language: ko-KR
Last updated: {NOW.isoformat(timespec='seconds')}

## Sections

- 동네 레이더: {BASE}/radar/
  - 서울/동네/상권/주거 흐름을 판단 카드로 정리합니다.
- 파트너스 픽: {BASE}/deals/
  - 쿠팡 파트너스 추천글과 구매가이드를 일반 정보글과 분리합니다.
  - 제휴 링크가 포함된 글은 본문에 고지를 표시합니다.
- 생활 가이드: {BASE}/guides/
  - 생활, 지역, 부동산 기본 가이드를 모읍니다.

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
Sitemap: {BASE}/sitemap.xml
LLM guide: {BASE}/llms.txt
Language: ko-KR
Updated: {NOW.isoformat(timespec='seconds')}
''')
    write("humans.txt", f'''Recuerdame Lab
Owner: r2cuerdame
Site: {BASE}/
Language: Korean
Purpose: Dongne Radar, lifestyle guides, and separated partner/affiliate content.
Updated: {NOW.isoformat(timespec='seconds')}
''')
    write("build-info.json", json.dumps({
        "site": SITE_NAME,
        "base_url": BASE,
        "built_at": NOW.isoformat(timespec="seconds"),
        "timezone": "Asia/Seoul",
        "sections": [p["path"] for p in PAGES],
        "search_ready": ["google", "naver", "daum", "ai_search"],
        "sitemap": f"{BASE}/sitemap.xml",
        "rss": f"{BASE}/feed.xml",
        "llms": f"{BASE}/llms.txt",
    }, ensure_ascii=False, indent=2) + "\n")
    write("README.md", f'''# Recuerdame Lab — r2cuerdame.github.io

GitHub Pages public hub for Dongne Radar, 생활 가이드, and separated Coupang Partners content.

## Live URLs

- Home: {BASE}/
- Dongne Radar: {BASE}/radar/
- Partners Pick: {BASE}/deals/
- Guides: {BASE}/guides/

## Search/AI files

- `{BASE}/sitemap.xml`
- `{BASE}/robots.txt`
- `{BASE}/feed.xml`
- `{BASE}/llms.txt`
- `{BASE}/ai.txt`

## Daily deploy

`.github/workflows/daily-pages-refresh.yml` runs daily and refreshes sitemap/RSS/LLM metadata, then pushes changes to `main` so GitHub Pages rebuilds.

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
- sitemap has daily `lastmod`.
- every HTML page has canonical, description, OG, RSS, sitemap link, and JSON-LD.
- `llms.txt` and `ai.txt` exist for AI search/answer engines.
- daily GitHub Actions refresh keeps metadata current.

## Manual one-time registrations still needed

Search engines usually require owner verification before manual sitemap submission.
Do not store verification tokens in docs. Add verification meta/file only after the owner provides the token.

- Google Search Console: add property for `{BASE}/`, verify, submit `/sitemap.xml`.
- Naver Search Advisor: add site, verify, submit `/sitemap.xml` and `/robots.txt` check.
- Daum search/webmaster registration: register site URL and sitemap if the tool asks for it.

After verification, keep publishing complete reader-facing pages. Empty daily rebuilds help freshness but do not replace real content.
''')


if __name__ == "__main__":
    build()
    print(json.dumps({"built_at": NOW.isoformat(timespec="seconds"), "pages": len(PAGES), "base": BASE}, ensure_ascii=False))
