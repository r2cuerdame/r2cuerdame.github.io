#!/usr/bin/env python3
"""Publish one repo-local shorts shopping pick to GitHub Pages.

This is the short-form companion publisher for LoopOffice. It does not use
browser sessions, local private draft banks, or account secrets. Candidate
inputs live in data/publisher/shorts_candidates.json and must contain tracked
public product links plus the affiliate disclosure.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import argparse
import html
import json
import re
import subprocess
import sys
from typing import Any

from publish_next_blog_autopost_deal import (
    BASE,
    KST,
    ROOT,
    existing_keys,
    product_signature,
    run,
    slugify,
    windows_git,
)

SHORTS_CANDIDATES_PATH = ROOT / 'data' / 'publisher' / 'shorts_candidates.json'


def product_anchor(url: str, label: str) -> str:
    return (
        f'<a href="{html.escape(url, quote=True)}" target="_blank" '
        f'rel="noopener sponsored nofollow">{html.escape(label)}</a>'
    )


def short_body(candidate: dict[str, Any]) -> str:
    products = candidate.get('products') if isinstance(candidate.get('products'), list) else []
    if len(products) < 3:
        raise ValueError('shorts_candidate_requires_at_least_3_products')
    title = str(candidate.get('title') or '').strip()
    hook = str(candidate.get('hook') or '').strip()
    verdict = str(candidate.get('verdict') or '').strip()
    checks = candidate.get('checks') if isinstance(candidate.get('checks'), list) else []
    check_items = ''.join(f'<li>{html.escape(str(x).strip())}</li>' for x in checks if str(x).strip())
    product_items = []
    quick_rows = []
    for index, product in enumerate(products, start=1):
        if not isinstance(product, dict):
            raise ValueError('shorts_candidate_product_object_required')
        name = str(product.get('name') or '').strip()
        url = str(product.get('url') or '').strip()
        one_liner = str(product.get('one_liner') or '').strip()
        caution = str(product.get('caution') or '').strip()
        if not name or 'coupang.com' not in url.lower() or 'lptag=' not in url.lower():
            raise ValueError('shorts_candidate_product_tracked_coupang_url_required')
        quick_rows.append(
            '<tr>'
            f'<td>{html.escape(str(index))}</td>'
            f'<td>{html.escape(name)}</td>'
            f'<td>{html.escape(one_liner)}</td>'
            f'<td>{html.escape(caution)}</td>'
            '</tr>'
        )
        product_items.append(
            f'<li><strong>{html.escape(name)}</strong> — {html.escape(one_liner)} '
            f'{product_anchor(url, "상품 페이지 확인")}</li>'
        )
    return (
        '<div class="juiz-mobile-body shorts-shopping-pick">'
        f'<p>{html.escape(hook)}</p>'
        '<h2>30초 결론</h2>'
        f'<p><strong>{html.escape(verdict)}</strong></p>'
        '<p>숏츠 쇼핑픽은 길게 읽는 비교글이 아니라, 상품 페이지에 들어가기 전 걸러야 할 조건만 빠르게 정리합니다. '
        '가격, 배송, 옵션명은 계속 바뀌므로 아래 기준으로 후보를 줄인 뒤 실제 상품 페이지에서 마지막 확인을 해야 합니다.</p>'
        '<h2>바로 볼 3가지</h2>'
        f'<ol>{check_items}</ol>'
        '<p>첫째, 사용 빈도를 정하세요. 비 오는 날 한두 번 쓰는 보조템인지, 매주 운동화와 작업화를 말릴 도구인지에 따라 필요한 체급이 달라집니다. '
        '둘째, 보관 위치를 정하세요. 현관 콘센트 옆에 둘 수 없으면 매번 꺼내기 번거로워 사용 빈도가 떨어집니다. '
        '셋째, 기대치를 낮추세요. 건조기는 냄새를 한 번에 지우는 물건이 아니라 젖은 시간을 줄여 냄새가 생길 조건을 낮추는 도구입니다.</p>'
        '<h2>후보 3개 빠른 비교</h2>'
        '<table><thead><tr><th>#</th><th>후보</th><th>맞는 경우</th><th>주의</th></tr></thead>'
        f'<tbody>{"".join(quick_rows)}</tbody></table>'
        '<h2>상품 페이지로 넘어가기 전</h2>'
        f'<ul>{"".join(product_items)}</ul>'
        '<p>상품 페이지에서는 대표 이미지보다 상세 크기, 전원선 길이, 타이머, 배송비, 반품비를 먼저 보세요. '
        '젖은 신발을 현관에서 바로 말릴지, 베란다에서 말릴지, 밤에도 켜둘지에 따라 소음과 발열 후기가 중요해집니다.</p>'
        '<p>가족이 함께 쓰면 한 켤레 전용보다 건조 순서를 어떻게 나눌지가 중요하고, 혼자 쓰면 보관 부담이 더 중요합니다. '
        '부츠나 작업화처럼 깊은 신발은 건조봉 길이와 공기 흐름을 확인해야 겉만 마르는 일을 줄일 수 있습니다.</p>'
        '<p>전기 제품은 젖은 바닥에서 바로 쓰지 않는 것도 중요합니다. 신발 트레이나 받침을 두고, 사용 뒤에는 열이 식은 다음 보관하세요. '
        '짧은 체크 글이라도 안전 위치와 보관 습관까지 맞아야 계속 쓰게 됩니다. 사용 위치가 정해지지 않았다면 구매를 하루 미루는 편이 낫습니다. 실패를 줄이는 기준입니다.</p>'
        '<h2>한 줄 정리</h2>'
        f'<p>{html.escape(title)}은 가격보다 사용 빈도, 보관 위치, 신발 종류가 먼저입니다. '
        '세 조건이 맞는 후보만 상품 페이지에서 최신 가격과 후기를 확인하세요.</p>'
        '<p style="font-size:12px;color:#888;margin-top:30px;">'
        '이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다. '
        '가격, 재고, 배송, 옵션 정보는 작성 시점 이후 변경될 수 있으니 구매 전 실제 상품 페이지에서 확인하세요.'
        '</p>'
        '</div>'
    )


def load_candidates() -> list[dict[str, Any]]:
    if not SHORTS_CANDIDATES_PATH.exists():
        return []
    data = json.loads(SHORTS_CANDIDATES_PATH.read_text(encoding='utf-8-sig'))
    raw_candidates = data.get('candidates') if isinstance(data, dict) else []
    out: list[dict[str, Any]] = []
    for raw in raw_candidates if isinstance(raw_candidates, list) else []:
        if not isinstance(raw, dict) or raw.get('ready') is not True:
            continue
        source_post_file = str(raw.get('source_post_file') or f"repo-local/shorts-{raw.get('id') or 'candidate'}.json").replace('\\', '/')
        body = short_body(raw)
        out.append({
            'post_file': source_post_file,
            'score': float(raw.get('publication_score') or 90),
            'post': {
                'title': str(raw.get('title') or '').strip(),
                'description': str(raw.get('description') or '').strip(),
                'date': str(raw.get('date') or datetime.now(KST).isoformat(timespec='seconds')),
                'category': '숏츠 쇼핑픽',
                'tags': raw.get('tags') or ['숏츠 쇼핑픽', '쇼핑픽'],
                'visibility': 'public',
                'products_pool': raw.get('products_pool'),
                'price_hint': raw.get('price_hint'),
                'primary_deal_url': raw.get('primary_deal_url'),
                'item_count_hint': f"{len(raw.get('products') or [])}개 후보 30초 체크",
                'html': body,
            },
        })
    out.sort(key=lambda x: x['post_file'])
    return out


def validate_post(post: dict[str, Any]) -> tuple[bool, list[str]]:
    errors = []
    title = str(post.get('title') or '').strip()
    body = str(post.get('html') or '').strip()
    if not title:
        errors.append('missing_title')
    if len(re.sub(r'<[^>]+>', ' ', body)) < 1800:
        errors.append('visible_text_too_short')
    if '<script' in body.lower():
        errors.append('script_tag')
    if '파트너스' not in body:
        errors.append('missing_affiliate_disclaimer')
    anchors = len(re.findall(r'<a\b', body, flags=re.I))
    if anchors < 3:
        errors.append(f'too_few_anchors:{anchors}')
    if any('lptag=' not in url.lower() for url in re.findall(r'href="([^"]+)"', body, flags=re.I) if 'coupang.com' in url.lower()):
        errors.append('coupang_lptag_missing')
    return not errors, errors


def article_from_post(post: dict[str, Any], post_file: str, score: float) -> dict[str, Any]:
    title = str(post['title']).strip()
    body = str(post['html']).strip()
    tags = post.get('tags') or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',') if t.strip()]
    if '숏츠 쇼핑픽' not in tags:
        tags = ['숏츠 쇼핑픽'] + tags
    article = {
        'slug': slugify(title, post_file),
        'title': title,
        'description': str(post.get('description') or re.sub(r'<[^>]+>', ' ', body).strip()[:170]),
        'date': str(post.get('date') or datetime.now(KST).isoformat(timespec='seconds')),
        'category': '숏츠 쇼핑픽',
        'tags': tags[:10],
        'is_affiliate': True,
        'source': 'repo-local-shorts-daily',
        'source_post_file': post_file,
        'publication_score': score,
        'products_pool': post.get('products_pool'),
        'body_html': body,
    }
    for key in ('price_hint', 'primary_deal_url', 'item_count_hint'):
        if post.get(key):
            article[key] = post.get(key)
    article['product_signature'] = product_signature(article)
    return article


def import_next(dry_run: bool = False) -> dict[str, Any]:
    by_title, by_source = existing_keys()
    skipped = []
    for candidate in load_candidates():
        post_file = candidate['post_file']
        post = dict(candidate['post'])
        title = str(post.get('title') or '').strip()
        if post_file in by_source:
            skipped.append({'post_file': post_file, 'reason': 'already_imported_source'})
            continue
        if title in by_title:
            skipped.append({'post_file': post_file, 'reason': 'already_imported_title', 'title': title})
            continue
        ok, errors = validate_post(post)
        if not ok:
            skipped.append({'post_file': post_file, 'reason': 'validation_failed', 'errors': errors, 'title': title})
            continue
        article = article_from_post(post, post_file, candidate['score'])
        out_path = ROOT / 'content' / 'deals' / f"{article['slug']}.json"
        if dry_run:
            return {'status': 'dry_run_ready', 'article': {k: article[k] for k in ['slug', 'title', 'date', 'category', 'source_post_file']}, 'skipped': skipped[:10]}
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(article, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        return {'status': 'imported', 'article': article, 'path': str(out_path.relative_to(ROOT)), 'skipped': skipped[:10]}
    return {'status': 'no_ready_candidate', 'candidate_count': len(load_candidates()), 'skipped': skipped[:20]}


def git_publish(result: dict[str, Any], dry_run: bool = False, no_push: bool = False) -> dict[str, Any]:
    if dry_run or result.get('status') not in {'imported'}:
        return {'built': False, 'committed': False, 'pushed': False}
    build = run([sys.executable, 'scripts/build_site.py'], check=True)
    quality_local = run([sys.executable, 'scripts/audit_public_site_quality.py'], check=True)
    status = run(['git', 'status', '--porcelain'], check=True).stdout.strip()
    if not status:
        return {'built': True, 'build_stdout': build.stdout.strip(), 'quality_local_stdout': quality_local.stdout.strip()[-1200:], 'committed': False, 'pushed': False}
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
    run(['git', 'commit', '-m', f"Publish shorts shopping pick: {title[:42]}"], check=True)
    pushed = False
    push_stdout = ''
    push_stderr = ''
    quality_live_stdout = ''
    if not no_push:
        push = windows_git(['push', 'origin', 'main'], check=True)
        pushed = True
        push_stdout = push.stdout.strip()
        push_stderr = push.stderr.strip()
        live = run([sys.executable, 'scripts/audit_public_site_quality.py', '--live'], check=True)
        quality_live_stdout = live.stdout.strip()[-1200:]
    return {
        'built': True,
        'build_stdout': build.stdout.strip(),
        'quality_local_stdout': quality_local.stdout.strip()[-1200:],
        'committed': True,
        'pushed': pushed,
        'push_stdout': push_stdout,
        'push_stderr': push_stderr,
        'quality_live_stdout': quality_live_stdout,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--no-push', action='store_true')
    args = parser.parse_args()
    try:
        result = import_next(dry_run=args.dry_run)
        git_result = git_publish(result, dry_run=args.dry_run, no_push=args.no_push)
        out = {'ok': True, 'checked_at': datetime.now(KST).isoformat(timespec='seconds'), **result, 'git': git_result}
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
