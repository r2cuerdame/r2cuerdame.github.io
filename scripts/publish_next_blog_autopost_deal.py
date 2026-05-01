#!/usr/bin/env python3
"""Publish one quality-passed blog-autopost Coupang draft to GitHub Pages.

This is the daily bridge from the local Coupang/Tistory draft bank to
r2cuerdame.github.io/deals/. It does not touch Tistory, login, browser, or
security challenges. It only imports a draft that the hourly review already
marked as content-clean and blocked only by the Tistory/browser publish hold.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import argparse
import hashlib
import html
import json
import re
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BLOG_ROOT = Path('/mnt/c/Users/recue/.openclaw/workspace/blog-autopost')
KST = timezone(timedelta(hours=9))
BASE = 'https://r2cuerdame.github.io'

PRODUCT_TOPIC_RULES = {
    'air_purifier': {
        'pools': {'products_air_purifiers.json'},
        'phrases': {'공기청정기', '공기 청정기'},
    },
    'dehumidifier': {
        'pools': {'products_dehumidifiers.json'},
        'phrases': {'제습기'},
    },
    'robot_vacuum': {
        'pools': {'products_robot_vacuum.json'},
        'phrases': {'로봇청소기', '로봇 청소기'},
    },
    'stick_vacuum': {
        'pools': {'products_stick_vacuums.json'},
        'phrases': {'무선청소기', '스틱청소기', '스틱 청소기'},
    },
    'monitor_arm': {
        'pools': {'products_monitor_arms.json'},
        'phrases': {'모니터암', '모니터 암'},
    },
    'monitor_light': {
        'pools': {'products_monitor_lights.json'},
        'phrases': {'모니터 조명', '모니터조명', '스크린바'},
    },
    'office_chair': {
        'pools': {'products_office_chairs.json'},
        'phrases': {'사무용 의자', '오피스 의자', '허리 편한 의자'},
    },
    'keyboard': {
        'pools': {'products_keyboard.json'},
        'phrases': {'기계식 키보드', '키보드'},
    },
    'gaming_headset': {
        'pools': {'products_gaming_headsets.json'},
        'phrases': {'게이밍 헤드셋', '게임 헤드셋'},
    },
    'noise_cancel_headphones': {
        'pools': {'products_noise_cancel_headphones.json'},
        'phrases': {'anc 헤드폰', '노이즈캔슬링 헤드폰', '노캔 헤드폰'},
    },
    'wireless_earbuds': {
        'pools': {'products_wireless_earbuds.json'},
        'phrases': {'무선 이어버드', '무선이어버드', '무선 이어폰', '무선이어폰'},
    },
    'bluetooth_speaker': {
        'pools': {'products_bluetooth_speakers.json'},
        'phrases': {'블루투스 스피커'},
    },
    'kitchen_appliance': {
        'pools': {'products_kitchen_appliance_deals.json'},
        'phrases': {'주방가전'},
    },
    'personal_care_gadget': {
        'pools': {'products_personal_care_deals.json'},
        'phrases': {'뷰티 디바이스', '퍼스널 케어', '개인관리 기기'},
    },
}


def run(cmd: list[str], cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)


def windows_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run Windows Git inside the repo so the scheduled job can use Windows credentials."""
    win_root = str(ROOT).replace('/mnt/c/', 'C:\\').replace('/', '\\')
    return subprocess.run(
        ['/mnt/c/Windows/System32/cmd.exe', '/c', 'cd', '/d', win_root, '&&', 'git', *args],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def sync_remote_before_publish() -> dict[str, str]:
    """Fast-forward/rebase local main before creating a daily publish commit.

    GitHub Actions may refresh metadata shortly before the Hermes daily publisher.
    Sync first so the final push stays fast-forward without committing over stale
    generated files. Untracked local working files are ignored, but tracked edits
    fail closed.
    """
    dirty = run(['git', 'status', '--porcelain', '--untracked-files=no'], check=True).stdout.strip()
    if dirty:
        raise RuntimeError('tracked_worktree_dirty_before_publish')
    fetch = windows_git(['fetch', 'origin', 'main'], check=True)
    rebase = run(['git', 'rebase', 'origin/main'], check=True)
    return {'fetch_stderr': fetch.stderr.strip()[-500:], 'rebase_stdout': rebase.stdout.strip()[-500:], 'rebase_stderr': rebase.stderr.strip()[-500:]}


def strip_tags(value: str) -> str:
    value = re.sub(r'<script\b[^>]*>.*?</script>', ' ', value or '', flags=re.I | re.S)
    value = re.sub(r'<style\b[^>]*>.*?</style>', ' ', value, flags=re.I | re.S)
    value = re.sub(r'<[^>]+>', ' ', value)
    value = html.unescape(value)
    return re.sub(r'\s+', ' ', value).strip()


def short(value: str, limit: int = 170) -> str:
    value = strip_tags(value)
    return value if len(value) <= limit else value[: limit - 1].rstrip() + '…'


def normalized_pool(record: dict[str, Any]) -> str:
    return Path(str(record.get('products_pool') or '')).name.strip().lower()


def topic_scan_text(record: dict[str, Any]) -> str:
    """Text used to infer product topic without broad category tag false positives."""
    body = str(record.get('html') or record.get('body_html') or '')
    # Title/body catch the actual product. Category/tags can contain broad buckets
    # like "로봇청소기-가전" even for air purifier or dehumidifier posts.
    return f"{record.get('title') or ''} {strip_tags(body)[:2500]}".lower()


def infer_product_topics(record: dict[str, Any]) -> set[str]:
    pool = normalized_pool(record)
    scan = topic_scan_text(record)
    topics: set[str] = set()
    for topic, rule in PRODUCT_TOPIC_RULES.items():
        if pool and pool in rule['pools']:
            topics.add(topic)
            continue
        if any(phrase.lower() in scan for phrase in rule['phrases']):
            topics.add(topic)
    return topics


def extract_coupang_product_ids(record: dict[str, Any]) -> set[str]:
    body = str(record.get('html') or record.get('body_html') or '')
    return set(re.findall(r'coupang\.com/vp/products/(\d+)', body, flags=re.I))


def product_signature(record: dict[str, Any]) -> dict[str, Any]:
    return {
        'products_pool': normalized_pool(record),
        'topics': sorted(infer_product_topics(record)),
        'coupang_product_ids': sorted(extract_coupang_product_ids(record)),
    }


def find_similar_existing_article(candidate: dict[str, Any], existing_articles: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the first public deal that is too similar to publish beside candidate."""
    candidate_pool = normalized_pool(candidate)
    candidate_topics = infer_product_topics(candidate)
    candidate_product_ids = extract_coupang_product_ids(candidate)
    for existing in existing_articles:
        existing_title = str(existing.get('title') or '').strip()
        existing_pool = normalized_pool(existing)
        if candidate_pool and existing_pool and candidate_pool == existing_pool:
            return {
                'reason': 'same_product_pool',
                'existing_title': existing_title,
                'existing_slug': existing.get('slug'),
                'products_pool': candidate_pool,
            }
        existing_topics = infer_product_topics(existing)
        common_topics = sorted(candidate_topics & existing_topics)
        if common_topics:
            return {
                'reason': 'same_product_topic',
                'existing_title': existing_title,
                'existing_slug': existing.get('slug'),
                'topics': common_topics,
            }
        existing_product_ids = extract_coupang_product_ids(existing)
        common_product_ids = sorted(candidate_product_ids & existing_product_ids)
        if common_product_ids:
            return {
                'reason': 'same_coupang_product',
                'existing_title': existing_title,
                'existing_slug': existing.get('slug'),
                'product_ids': common_product_ids[:5],
            }
    return None


def slugify(title: str, seed: str) -> str:
    base = re.sub(r'[^0-9A-Za-z가-힣]+', '-', title).strip('-').lower()
    base = re.sub(r'-{2,}', '-', base)
    if not base:
        base = 'deal'
    digest = hashlib.sha1((seed + title).encode('utf-8')).hexdigest()[:8]
    if len(base) > 70:
        base = base[:70].strip('-')
    return f'{base}-{digest}'


def existing_keys() -> tuple[set[str], set[str]]:
    by_title: set[str] = set()
    by_source: set[str] = set()
    for path in (ROOT / 'content' / 'deals').glob('*.json'):
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            continue
        if data.get('title'):
            by_title.add(str(data['title']).strip())
        if data.get('source_post_file'):
            by_source.add(str(data['source_post_file']).replace('\\', '/'))
    return by_title, by_source


def load_existing_deal_articles() -> list[dict[str, Any]]:
    articles: list[dict[str, Any]] = []
    for path in (ROOT / 'content' / 'deals').glob('*.json'):
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            continue
        if isinstance(data, dict):
            articles.append(data)
    return articles


def load_review_candidates() -> list[dict[str, Any]]:
    path = BLOG_ROOT / 'review' / 'continuous_multi_angle_review_latest.json'
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    reviewed = data.get('reviewed') or []
    out = []
    for r in reviewed:
        post_file = str(r.get('post_file') or '').replace('\\', '/')
        if not post_file:
            continue
        score = float(r.get('publication_score') or 0)
        content_blockers = r.get('content_blockers') or []
        waiting_blockers = r.get('waiting_blockers') or []
        only_waiting = bool(r.get('only_waiting_blocks'))
        policy_ok = ((r.get('angles') or {}).get('policy_links') or {}).get('ok') is True
        if score >= 90 and not content_blockers and only_waiting and policy_ok:
            out.append({
                'post_file': post_file,
                'title': r.get('title') or '',
                'score': score,
                'waiting_blockers': waiting_blockers,
            })
    out.sort(key=lambda x: x['post_file'])
    return out


def parse_post_date(post_file: str) -> str:
    name = Path(post_file).stem
    m = re.match(r'(\d{8})-(\d{6})', name)
    if m:
        dt = datetime.strptime(''.join(m.groups()), '%Y%m%d%H%M%S').replace(tzinfo=KST)
        return dt.isoformat(timespec='seconds')
    return datetime.now(KST).isoformat(timespec='seconds')


def validate_post(post: dict[str, Any], post_file: str) -> tuple[bool, list[str]]:
    errors = []
    title = str(post.get('title') or '').strip()
    body = str(post.get('html') or '').strip()
    if not title:
        errors.append('missing_title')
    if len(body) < 6000:
        errors.append('body_too_short')
    if '<script' in body.lower():
        errors.append('script_tag')
    if str(post.get('visibility') or '').lower() not in {'public', ''}:
        errors.append('not_public_visibility')
    if '파트너스' not in body:
        errors.append('missing_affiliate_disclaimer')
    if not re.search(r'coupa\.ng|coupang\.com|coupang', body, flags=re.I):
        errors.append('missing_coupang_link_or_text')
    anchors = len(re.findall(r'<a\b', body, flags=re.I))
    if anchors < 3:
        errors.append(f'too_few_anchors:{anchors}')
    if re.search(r'관련\s*제품|placeholder|임시', body, flags=re.I):
        errors.append('placeholder_text')
    if post.get('retired_at') or post.get('source_status') == 'retired':
        errors.append('retired_source')
    return not errors, errors


def article_from_post(post: dict[str, Any], post_file: str, score: float) -> dict[str, Any]:
    title = str(post['title']).strip()
    body = str(post['html']).strip()
    tags = post.get('tags') or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',') if t.strip()]
    category = str(post.get('category') or '파트너스 픽')
    if category not in tags:
        tags = [category] + tags
    slug = slugify(title, post_file)
    article = {
        'slug': slug,
        'title': title,
        'description': short(body, 180),
        'date': parse_post_date(post_file),
        'category': category,
        'tags': tags[:10],
        'is_affiliate': True,
        'source': 'blog-autopost-daily',
        'source_post_file': post_file,
        'publication_score': score,
        'products_pool': post.get('products_pool'),
        'body_html': body,
    }
    article['product_signature'] = product_signature(article)
    return article


def import_next(dry_run: bool = False) -> dict[str, Any]:
    by_title, by_source = existing_keys()
    existing_articles = load_existing_deal_articles()
    candidates = load_review_candidates()
    skipped = []
    for c in candidates:
        post_file = c['post_file']
        if post_file in by_source:
            skipped.append({'post_file': post_file, 'reason': 'already_imported_source'})
            continue
        post_path = BLOG_ROOT / post_file
        if not post_path.exists():
            skipped.append({'post_file': post_file, 'reason': 'missing_post_file'})
            continue
        post = json.loads(post_path.read_text(encoding='utf-8-sig'))
        title = str(post.get('title') or c.get('title') or '').strip()
        if title in by_title:
            skipped.append({'post_file': post_file, 'reason': 'already_imported_title', 'title': title})
            continue
        similar = find_similar_existing_article(post, existing_articles)
        if similar:
            skipped.append({'post_file': post_file, 'reason': 'similar_existing_deal', 'title': title, 'match': similar})
            continue
        ok, errors = validate_post(post, post_file)
        if not ok:
            skipped.append({'post_file': post_file, 'reason': 'validation_failed', 'errors': errors, 'title': title})
            continue
        article = article_from_post(post, post_file, c['score'])
        out_path = ROOT / 'content' / 'deals' / f"{article['slug']}.json"
        if dry_run:
            return {'status': 'dry_run_ready', 'article': {k: article[k] for k in ['slug', 'title', 'date', 'category', 'source_post_file']}, 'skipped': skipped[:10]}
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(article, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        return {'status': 'imported', 'article': article, 'path': str(out_path.relative_to(ROOT)), 'skipped': skipped[:10]}
    return {'status': 'no_ready_candidate', 'candidate_count': len(candidates), 'skipped': skipped[:20]}


def git_publish(result: dict[str, Any], dry_run: bool = False, no_push: bool = False) -> dict[str, Any]:
    if dry_run or result.get('status') not in {'imported'}:
        return {'built': False, 'committed': False, 'pushed': False}
    # Avoid merging over local edits silently.
    status_before = run(['git', 'status', '--porcelain'], check=True).stdout.strip()
    # It is okay to have the newly written content file as a local change; pull only if clean before import is handled externally.
    build = run([sys.executable, 'scripts/build_site.py'], check=True)
    status = run(['git', 'status', '--porcelain'], check=True).stdout.strip()
    if not status:
        return {'built': True, 'build_stdout': build.stdout.strip(), 'committed': False, 'pushed': False}
    title = result['article']['title']
    run(['git', 'add', '-u'], check=True)
    content_path = ROOT / str(result.get('path', ''))
    slug = result['article'].get('slug')
    paths_to_add = []
    if content_path.exists():
        paths_to_add.append(str(content_path.relative_to(ROOT)))
    if slug:
        page_dir = ROOT / 'deals' / str(slug)
        if page_dir.exists():
            paths_to_add.append(str(page_dir.relative_to(ROOT)))
    if paths_to_add:
        run(['git', 'add', *paths_to_add], check=True)
    commit_msg = f"Publish deal article: {title[:48]}"
    run(['git', 'commit', '-m', commit_msg], check=True)
    pushed = False
    push_stdout = ''
    push_stderr = ''
    if not no_push:
        push = windows_git(['push', 'origin', 'main'], check=True)
        pushed = True
        push_stdout = push.stdout.strip()
        push_stderr = push.stderr.strip()
    return {'built': True, 'build_stdout': build.stdout.strip(), 'committed': True, 'pushed': pushed, 'push_stdout': push_stdout, 'push_stderr': push_stderr, 'status_before': status_before}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--no-push', action='store_true')
    args = ap.parse_args()
    try:
        sync = {'skipped': bool(args.dry_run)} if args.dry_run else sync_remote_before_publish()
        result = import_next(dry_run=args.dry_run)
        git_result = git_publish(result, dry_run=args.dry_run, no_push=args.no_push)
        out = {'ok': True, 'checked_at': datetime.now(KST).isoformat(timespec='seconds'), **result, 'git': git_result, 'sync': sync}
        if result.get('article'):
            article = result['article']
            out['url'] = f"{BASE}/deals/{article['slug']}/"
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    except subprocess.CalledProcessError as e:
        print(json.dumps({'ok': False, 'error': 'command_failed', 'cmd': e.cmd, 'stdout': e.stdout[-2000:], 'stderr': e.stderr[-2000:]}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    except Exception as e:
        print(json.dumps({'ok': False, 'error': type(e).__name__, 'message': str(e)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
