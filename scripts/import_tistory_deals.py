#!/usr/bin/env python3
"""Import already-published Tistory Coupang posts into content/deals/*.json.

The output is static-site source data; the build script generates GitHub Pages.
This script only reads public Tistory pages and local published_posts.json metadata.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import argparse
import html
import json
import re
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
KST = timezone(timedelta(hours=9))
DEFAULT_PUBLISHED = Path('/mnt/c/Users/recue/.openclaw/workspace/blog-autopost/published_posts.json')
USER_AGENT = 'Mozilla/5.0 (compatible; RecuerdameLabImporter/1.0; +https://r2cuerdame.github.io/)'

SLUG_OVERRIDES = {
    'https://recuerdame.tistory.com/5': '2026-mechanical-keyboard-top5',
    'https://recuerdame.tistory.com/6': '2026-robot-vacuum-best4',
    'https://recuerdame.tistory.com/7': '2026-monitor-arm-top5',
    'https://recuerdame.tistory.com/9': 'air-purifier-top5',
    'https://recuerdame.tistory.com/10': 'gaming-headset-best5',
    'https://recuerdame.tistory.com/11': 'today-desk-gadget-deals',
    'https://recuerdame.tistory.com/12': 'dehumidifier-best5',
    'https://recuerdame.tistory.com/13': '2026-anc-headphones-top5',
    'https://recuerdame.tistory.com/15': 'beauty-personal-care-gadgets-top5',
}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        if r.status != 200:
            raise RuntimeError(f'{url}: HTTP {r.status}')
        return r.read().decode('utf-8', 'replace')


def first_match(pattern: str, text: str, default: str = '') -> str:
    m = re.search(pattern, text, flags=re.I | re.S)
    return html.unescape(m.group(1).strip()) if m else default


def strip_tags(value: str) -> str:
    value = re.sub(r'<script\b[^>]*>.*?</script>', ' ', value or '', flags=re.I | re.S)
    value = re.sub(r'<style\b[^>]*>.*?</style>', ' ', value, flags=re.I | re.S)
    value = re.sub(r'<[^>]+>', ' ', value)
    value = html.unescape(value)
    return re.sub(r'\s+', ' ', value).strip()


def short(value: str, limit: int = 170) -> str:
    value = strip_tags(value)
    return value if len(value) <= limit else value[: limit - 1].rstrip() + '…'


def parse_tistory_date(raw: str) -> str:
    raw = html.unescape(raw or '').strip()
    # Example: 2026. 4. 21. 01:44
    m = re.search(r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{1,2}):(\d{2})', raw)
    if m:
        y, mo, d, h, mi = map(int, m.groups())
        return datetime(y, mo, d, h, mi, tzinfo=KST).isoformat(timespec='seconds')
    return datetime.now(KST).isoformat(timespec='seconds')


def extract_body(page: str, url: str) -> str:
    start = '<div class="tt_article_useless_p_margin contents_style">'
    i = page.find(start)
    j = page.find('<div class="container_postbtn', i)
    if i < 0 or j < 0:
        raise RuntimeError(f'{url}: article body marker not found')
    body = page[i + len(start):j]
    body = re.sub(r'</div>\s*<!-- System - START -->.*$', '', body, flags=re.S).strip()
    body = re.sub(r'<script\b[^>]*>.*?</script>', '', body, flags=re.I | re.S)
    body = re.sub(r'<iframe\b[^>]*>.*?</iframe>', '', body, flags=re.I | re.S)
    body = re.sub(r'\s+data-ke-[a-z-]+="[^"]*"', '', body)
    body = re.sub(r'\s+data-og-[a-z-]+="[^"]*"', '', body)
    return body.strip()


def import_one(item: dict) -> dict:
    url = item['url']
    page = fetch(url)
    body = extract_body(page, url)
    title = first_match(r'<meta\s+property="og:title"\s+content="([^"]+)"\s*/?>', page)
    if not title:
        title = first_match(r'<title[^>]*>(.*?)</title>', page)
    category = first_match(r'<p\s+class="category">(.*?)</p>', page, item.get('category', '파트너스 픽'))
    date_raw = first_match(r'<span\s+class="date">(.*?)</span>', page)
    date_iso = parse_tistory_date(date_raw)
    desc = first_match(r'<meta\s+name="description"\s+content="([^"]*)"\s*/?>', page)
    if not desc:
        desc = item.get('hook') or short(body)
    tags = [category, item.get('link_title', ''), '쿠팡 파트너스']
    tags.extend(str(item.get('category', '')).split('-'))
    tags = [t.strip() for t in tags if t and t.strip()]
    seen = set(); uniq_tags = []
    for t in tags:
        if t not in seen:
            uniq_tags.append(t); seen.add(t)
    if '파트너스' not in body:
        raise RuntimeError(f'{url}: affiliate disclaimer not found in body')
    if not re.search(r'coupa\.ng|coupang\.com|coupang', body, flags=re.I):
        raise RuntimeError(f'{url}: Coupang link/text not found in body')
    return {
        'slug': SLUG_OVERRIDES.get(url) or re.sub(r'[^0-9A-Za-z가-힣]+', '-', title).strip('-').lower(),
        'title': title,
        'description': desc[:220],
        'date': date_iso,
        'category': category,
        'tags': uniq_tags[:10],
        'is_affiliate': True,
        'source': 'tistory-migration',
        'source_url': url,
        'source_title': item.get('title'),
        'body_html': body,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--published-json', type=Path, default=DEFAULT_PUBLISHED)
    ap.add_argument('--out-dir', type=Path, default=ROOT / 'content' / 'deals')
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()
    items = json.loads(args.published_json.read_text(encoding='utf-8'))
    if args.limit:
        items = items[: args.limit]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for item in items:
        article = import_one(item)
        path = args.out_dir / f"{article['slug']}.json"
        path.write_text(json.dumps(article, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        written.append({'slug': article['slug'], 'title': article['title'], 'path': str(path.relative_to(ROOT))})
    print(json.dumps({'ok': True, 'imported': len(written), 'written': written}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
