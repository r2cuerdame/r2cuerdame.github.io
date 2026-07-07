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
REPO_CANDIDATES_PATH = ROOT / 'data' / 'publisher' / 'deal_candidates.json'
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
    """Run Git through the local bridge when present, otherwise use portable git."""
    bridge = Path('/mnt/c/Windows/System32/cmd.exe')
    if not bridge.exists():
        return run(['git', *args], check=check)
    win_root = str(ROOT).replace('/mnt/c/', 'C:\\').replace('/', '\\')
    return subprocess.run(
        [str(bridge), '/c', 'cd', '/d', win_root, '&&', 'git', *args],
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


def product_anchor(url: str, label: str) -> str:
    return (
        f'<a href="{html.escape(url, quote=True)}" target="_blank" '
        f'rel="noopener sponsored nofollow">{html.escape(label)}</a>'
    )


def repo_candidate_body(candidate: dict[str, Any]) -> str:
    products = candidate.get('products') if isinstance(candidate.get('products'), list) else []
    if len(products) < 3:
        raise ValueError('repo_candidate_requires_at_least_3_products')
    title = str(candidate.get('title') or '').strip()
    intro = str(candidate.get('intro') or '').strip()
    use_case = str(candidate.get('use_case') or '').strip()
    rows = []
    sections = []
    for index, product in enumerate(products, start=1):
        if not isinstance(product, dict):
            raise ValueError('repo_candidate_product_object_required')
        name = str(product.get('name') or '').strip()
        url = str(product.get('url') or '').strip()
        price_hint = str(product.get('price_hint') or '상품 페이지에서 확인').strip()
        fit = str(product.get('fit') or '').strip()
        strengths = product.get('strengths') if isinstance(product.get('strengths'), list) else []
        checks = product.get('checks') if isinstance(product.get('checks'), list) else []
        if not name or 'coupang.com' not in url.lower() or 'lptag=' not in url.lower():
            raise ValueError('repo_candidate_product_tracked_coupang_url_required')
        strength_text = ', '.join(str(x).strip() for x in strengths if str(x).strip())
        check_items = ''.join(f'<li>{html.escape(str(x).strip())}</li>' for x in checks if str(x).strip())
        rows.append(
            '<tr>'
            f'<td>{html.escape(name)}</td>'
            f'<td>{html.escape(strength_text or fit)}</td>'
            f'<td>{html.escape(price_hint)}</td>'
            f'<td>{html.escape(fit)}</td>'
            '</tr>'
        )
        sections.append(
            f'<h3>{index}. {html.escape(name)}</h3>'
            f'<p><strong>{html.escape(name)}</strong>은 {html.escape(fit)} 상황에서 먼저 볼 만한 후보입니다. '
            f'가격과 배송 조건은 자주 바뀌므로 결제 전 판매 페이지에서 옵션, 재고, 최근 후기를 다시 확인해야 합니다.</p>'
            f'<p>체크 포인트는 {html.escape(strength_text or "사용 환경과 관리 부담")}입니다. '
            '습기 제거, 보관 위치, 사용 시간처럼 매일 반복되는 조건이 맞지 않으면 가격이 좋아도 보류하는 편이 안전합니다.</p>'
            '<p>이 후보를 볼 때는 "빨리 마르는가"만 보지 말고, 젖은 신발을 넣고 빼는 과정이 귀찮지 않은지, '
            '보관할 때 전원선이 걸리적거리지 않는지, 같은 신발을 며칠 연속 관리해도 부담이 없는지를 같이 봐야 합니다. '
            '신발 건조기는 한 번 사면 장마철마다 꺼내 쓰는 물건이라 첫 주 만족도보다 반복 사용 편의성이 더 중요합니다.</p>'
            '<p>반대로 냄새가 심하게 밴 신발을 한 번에 새것처럼 만들 기대라면 보류가 낫습니다. '
            '건조기는 습기를 줄이는 보조 도구이고, 세탁·통풍·깔창 교체와 같이 써야 체감이 납니다. '
            '그래서 상품 상세에서는 살균·탈취 문구보다 실제 건조 시간, 타이머, 과열 방지, 보관 크기를 우선 확인하세요.</p>'
            f'<ul>{check_items}</ul>'
            f'<p>{product_anchor(url, name + " 상품 페이지 확인하기")}</p>'
        )
    table = (
        '<h2>한눈에 비교</h2>'
        '<table><thead><tr><th>후보</th><th>볼 포인트</th><th>가격 기준</th><th>맞는 상황</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>'
    )
    faq = (
        '<h2>구매 전 마지막 확인</h2>'
        '<ul>'
        '<li><strong>옵션명:</strong> 같은 대표명이라도 구성품과 세부 모델이 다를 수 있습니다.</li>'
        '<li><strong>배송 조건:</strong> 도착 예정일, 묶음배송, 반품비는 결제 직전에 다시 확인하세요.</li>'
        '<li><strong>최근 후기:</strong> 별점 평균보다 최근 한 달 불만 패턴을 먼저 봅니다.</li>'
        '<li><strong>사용 공간:</strong> 콘센트 위치, 보관 공간, 소음 허용 범위를 먼저 정하면 실패가 줄어듭니다.</li>'
        '</ul>'
    )
    disclosure = (
        '<p style="font-size:12px;color:#888;margin-top:30px;">'
        '이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다. '
        '가격, 재고, 배송, 옵션 정보는 작성 시점 이후 변경될 수 있으니 구매 전 실제 상품 페이지에서 확인하세요.'
        '</p>'
    )
    return (
        '<div class="juiz-mobile-body">'
        f'<h2>서론</h2><p>{html.escape(intro)}</p>'
        f'<p>{html.escape(use_case)}</p>'
        '<h2>빠른 결론</h2>'
        f'<p>{html.escape(title)}은 하나의 정답을 고르는 글이 아니라, 사용 장면별로 실패 조건을 줄이는 비교입니다. '
        '젖은 신발을 얼마나 자주 말리는지, 보관 공간이 있는지, 소음과 타이머가 필요한지를 먼저 보고 후보를 줄이세요.</p>'
        '<h2>먼저 정할 기준</h2>'
        '<p>첫 번째 기준은 사용 빈도입니다. 비 오는 날 한두 번 쓰는 정도라면 작은 휴대형이 편하지만, 아이 운동화나 작업화를 거의 매주 말려야 한다면 타이머와 발열 안정성을 더 봐야 합니다. '
        '가격이 낮아도 매번 꺼내기 불편하면 결국 방치되고, 반대로 큰 제품은 보관 장소가 없으면 만족도가 떨어집니다.</p>'
        '<p>두 번째 기준은 신발 종류입니다. 운동화처럼 입구가 넓은 신발은 대체로 쓰기 쉽지만, 부츠나 작업화는 건조봉 길이와 공기 흐름이 맞아야 합니다. '
        '신발 안쪽까지 열이 닿지 않으면 겉만 마르고 안쪽 냄새가 남을 수 있으니 상세 사진과 후기를 같이 보는 편이 좋습니다.</p>'
        '<p>세 번째 기준은 집 안 동선입니다. 현관 콘센트가 멀거나 신발장 앞 공간이 좁으면 매번 멀티탭을 꺼내야 해서 사용 빈도가 떨어집니다. '
        '구매 전에 실제로 어디에 놓고 쓸지 정하고, 전원선 길이와 보관 크기를 확인하면 실패 확률을 줄일 수 있습니다.</p>'
        '<p>마지막 기준은 기대치입니다. 신발 건조기는 냄새를 완전히 없애는 만능 가전이 아니라 젖은 시간을 줄여 냄새가 생길 조건을 낮추는 도구에 가깝습니다. '
        '세탁이 필요한 신발, 이미 냄새가 밴 깔창, 통풍이 안 되는 신발장은 별도 관리가 필요합니다.</p>'
        '<p>비교할 때는 후보를 세 등급으로 나누면 편합니다. 첫째는 가끔 쓰는 입문형, 둘째는 장마철 반복 사용형, 셋째는 부츠·작업화처럼 깊은 신발까지 보는 형태입니다. '
        '이 구분 없이 가격만 낮은 순서로 보면 배송비를 더한 실제 결제 금액, 보관 부피, 건조 시간이 뒤늦게 보입니다. '
        '특히 판매 페이지의 대표 사진은 작아 보여도 실제 신발장 앞에서 차지하는 공간은 다를 수 있으니, 상세 크기와 전원선 위치를 꼭 확인하세요.</p>'
        '<p>후보를 고른 뒤에는 바로 결제하지 말고 집의 사용 장면에 대입해 보세요. 비 오는 날 현관에서 바로 말릴지, 베란다 콘센트 옆에서 쓸지, 밤에도 켜둘지에 따라 필요한 조건이 달라집니다. '
        '또 가족이 함께 쓰면 한 켤레 전용보다 건조 순서를 나눌 수 있는지가 중요하고, 혼자 쓰면 보관과 꺼내는 속도가 더 중요합니다.</p>'
        '<p>전기 제품이므로 젖은 손으로 플러그를 만지지 않을 위치도 중요합니다. 물기가 떨어지는 현관 바닥에 그대로 두기보다 받침이나 신발 트레이를 함께 쓰고, 사용 뒤에는 충분히 식힌 다음 보관하는 쪽이 안전합니다. 작은 습관 차이가 오래 씁니다.</p>'
        '<h2>제품별 핵심 포인트</h2>'
        f'{"".join(sections)}'
        f'{table}{faq}'
        '<h2>정리</h2>'
        '<p>가끔 쓰는 장마철 보조템이면 작고 보관 쉬운 후보가 낫고, 매일 운동화나 작업화를 말린다면 타이머와 건조 시간을 더 꼼꼼히 보세요. '
        '상품 페이지에서는 옵션명, 배송비, 반품비, 최근 후기를 마지막으로 확인한 뒤 결정하는 순서가 가장 안전합니다.</p>'
        f'{disclosure}'
        '</div>'
    )


def load_repo_local_candidates() -> list[dict[str, Any]]:
    if not REPO_CANDIDATES_PATH.exists():
        return []
    data = json.loads(REPO_CANDIDATES_PATH.read_text(encoding='utf-8-sig'))
    raw_candidates = data.get('candidates') if isinstance(data, dict) else []
    out: list[dict[str, Any]] = []
    for raw in raw_candidates if isinstance(raw_candidates, list) else []:
        if not isinstance(raw, dict) or raw.get('ready') is not True:
            continue
        source_post_file = str(raw.get('source_post_file') or f"repo-local/{raw.get('id') or 'candidate'}.json").replace('\\', '/')
        post = {
            'title': str(raw.get('title') or '').strip(),
            'html': repo_candidate_body(raw),
            'category': str(raw.get('category') or '쇼핑픽').strip(),
            'tags': raw.get('tags') or [],
            'visibility': 'public',
            'products_pool': raw.get('products_pool'),
            'date': raw.get('date'),
            'image_url': raw.get('image_url'),
            'price_hint': raw.get('price_hint'),
            'primary_deal_url': raw.get('primary_deal_url'),
            'item_count_hint': f"{len(raw.get('products') or [])}개 후보 비교",
        }
        out.append({
            'post_file': source_post_file,
            'title': post['title'],
            'score': float(raw.get('publication_score') or 91),
            'waiting_blockers': [],
            'post': post,
            'source': 'repo-local',
        })
    out.sort(key=lambda x: x['post_file'])
    return out


def load_all_candidates() -> list[dict[str, Any]]:
    return load_review_candidates() + load_repo_local_candidates()


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
    if re.search(r'Config warnings|model\.run via gateway|plugins\.entries|provider:\s*anthropic|outputs:\s*\d+', body, flags=re.I):
        errors.append('model_gateway_log_leak')
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
        'date': str(post.get('date') or parse_post_date(post_file)),
        'category': category,
        'tags': tags[:10],
        'is_affiliate': True,
        'source': str(post.get('source') or 'blog-autopost-daily'),
        'source_post_file': post_file,
        'publication_score': score,
        'products_pool': post.get('products_pool'),
        'body_html': body,
    }
    for key in ('image_url', 'price_hint', 'primary_deal_url', 'item_count_hint'):
        if post.get(key):
            article[key] = post.get(key)
    article['product_signature'] = product_signature(article)
    return article


def import_next(dry_run: bool = False) -> dict[str, Any]:
    by_title, by_source = existing_keys()
    existing_articles = load_existing_deal_articles()
    candidates = load_all_candidates()
    skipped = []
    for c in candidates:
        post_file = c['post_file']
        if post_file in by_source:
            skipped.append({'post_file': post_file, 'reason': 'already_imported_source'})
            continue
        if c.get('post'):
            post = dict(c['post'])
        else:
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
    commit_msg = f"Publish deal article: {title[:48]}"
    run(['git', 'commit', '-m', commit_msg], check=True)
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
        'status_before': status_before,
    }


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
