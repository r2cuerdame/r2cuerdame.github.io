#!/usr/bin/env python3
"""Review Dongne Radar release candidates without publishing anything."""
from __future__ import annotations

import argparse
import datetime as dt
import html.parser
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_ROOT = ROOT / "release_candidates"
CONTENT_ROOT = ROOT / "content" / "radar"
REPORT_DIR = ROOT / "reports"
STATE_PATH = REPORT_DIR / "candidate-review-state.json"
REPORT_PATH = REPORT_DIR / "cron-review-latest.md"

FORBIDDEN_TERMS = [
    "가격", "결제", "구독", "유료", "paywall", "쿠팡", "파트너스", "구매", "광고",
    "CTA", "Reader QA", "Gate", "publish_ready", "release_candidate",
    "title candidate", "body outline", "free report", "free complete", "free post",
    "내부 제작", "제휴",
]
REQUIRED_SIGNALS = ["반례", "한계", "현장", "질문", "사용법", "해석"]
STRATEGY_TERMS = {
    "primary_audience_context": ["이사", "전월세", "월세", "전세", "계약", "거주지", "집 보러", "살 동네", "통근", "관리비", "생활권"],
    "decision_situation": ["확인", "질문", "체크", "보류", "비교", "판단", "계약 전", "방문 전", "현장", "계속 볼"],
    "reader_tool": ["질문", "체크리스트", "표", "신호", "순서", "문장", "비교", "보류"],
}
TARGET_OPENING_TERMS = {
    "metro_market": ["서울", "수도권"],
    "age_or_life_stage": ["25~39", "직장인", "1인가구", "신혼"],
    "housing_intent": ["이사", "전월세", "월세", "전세", "계약", "거주지", "집 보러", "후보를 비교"],
    "decision_action": ["계속 볼", "보류", "확인", "질문", "체크", "비교", "판단", "계약 전", "방문 전", "현장"],
}


class VisibleTextParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.in_main = False
        self.seen_main = False
        self.main_text: list[str] = []
        self.main_text_no_svg: list[str] = []
        self.body_text: list[str] = []
        self.visuals_in_main = 0
        self.visuals_in_body = 0
        self.skip_tags = {"script", "style", "noscript"}

    def handle_starttag(self, tag: str, attrs):
        tag = tag.lower()
        self.stack.append(tag)
        if tag == "main":
            self.in_main = True
            self.seen_main = True
        if tag in {"figure", "img"}:
            if self.in_main:
                self.visuals_in_main += 1
            if "body" in self.stack:
                self.visuals_in_body += 1
        elif tag == "svg":
            # Count standalone SVG only if it is not already inside a figure.
            if "figure" not in self.stack:
                if self.in_main:
                    self.visuals_in_main += 1
                if "body" in self.stack:
                    self.visuals_in_body += 1

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        if tag == "main":
            self.in_main = False
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data: str):
        if not data or any(t in self.stack for t in self.skip_tags):
            return
        if "body" not in self.stack and not self.in_main:
            return
        text = data.strip()
        if not text:
            return
        self.body_text.append(text)
        if self.in_main:
            self.main_text.append(text)
            if "svg" not in self.stack:
                self.main_text_no_svg.append(text)


def collapse(parts: list[str]) -> str:
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def visible_char_count(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def radar_repo_webp_exists(public_url: str) -> bool:
    url = str(public_url or "").strip()
    return bool(url.startswith("/assets/radar/") and url.endswith(".webp") and (ROOT / url.lstrip("/")).exists())


def radar_media_blockers(meta: dict, slug: str) -> list[str]:
    image_url = str(meta.get("image_url") or meta.get("thumbnail_url") or "").strip()
    blockers: list[str] = []
    if not image_url:
        blockers.append("ai_thumbnail_missing")
    elif not (image_url.startswith("/assets/radar/thumbs/") and radar_repo_webp_exists(image_url)):
        blockers.append("ai_thumbnail_must_be_repo_webp")

    examples = meta.get("field_examples") if isinstance(meta.get("field_examples"), list) else []
    valid_examples: list[str] = []
    for item in examples:
        if not isinstance(item, dict):
            continue
        example_url = str(item.get("image_url") or "").strip()
        if (
            example_url.startswith(f"/assets/radar/{slug}/examples/")
            and "/thumbs/" not in example_url
            and radar_repo_webp_exists(example_url)
        ):
            valid_examples.append(example_url)
    if len(set(valid_examples)) < 3:
        blockers.append("three_ai_field_example_webps_required")
    return blockers


def review_file(path: Path, now: str, content_slugs: set[str] | None = None) -> dict:
    raw = path.read_text(encoding="utf-8", errors="replace")
    parser = VisibleTextParser()
    parser.feed(raw)
    main_text = collapse(parser.main_text if parser.seen_main else parser.body_text)
    prose_text = collapse(parser.main_text_no_svg if parser.seen_main else parser.body_text)
    all_visible = main_text or prose_text
    chars = visible_char_count(prose_text)
    visual_count = parser.visuals_in_main if parser.seen_main else parser.visuals_in_body
    meta = load_json(path.parent / "metadata.json")
    slug = str(meta.get("slug") or path.parent.name)
    content_slugs = content_slugs or set()
    published = slug in content_slugs or str(meta.get("status") or "") == "published_to_pages" or bool(meta.get("pages_published_at"))
    media_blockers = radar_media_blockers(meta, slug)

    hard: list[str] = []
    soft: list[str] = []
    observations: list[str] = []

    if re.search(r"<\s*script\b", raw, re.IGNORECASE):
        hard.append("script_tag_present")
    pictogram_svg_present = bool(
        re.search(r"\b(?:field-visual|visual-figure)\b", raw, re.IGNORECASE)
        or re.search(r"<\s*svg\b", raw, re.IGNORECASE)
        or re.search(r"\.svg(?:[\"'?#\s>]|$)", raw, re.IGNORECASE)
    )
    if pictogram_svg_present:
        issue = "pictogram_svg_visual_present"
        if published:
            observations.append(issue)
        else:
            hard.append(issue)
    if media_blockers:
        issue = "media_blockers:" + ",".join(media_blockers)
        if published:
            observations.append(issue)
        else:
            hard.append(issue)
    if chars < 3200:
        hard.append(f"body_too_short:{chars}<3200")
    elif chars < 4500:
        soft.append(f"body_below_target:{chars}<4500")
    elif chars > 7000:
        observations.append(f"body_above_editorial_target:{chars}>7000")

    if visual_count < 6:
        hard.append(f"visuals_too_few:{visual_count}<6")
    elif visual_count < 8:
        soft.append(f"visuals_below_target:{visual_count}<8")

    field_scene_ok = any(term in all_visible for term in ["예시 장면", "현장 예시", "장면", "사진처럼", "직접 본"])
    map_or_route_ok = any(term in all_visible for term in ["지도", "동선", "루트", "거리", "반경", "출구", "역", "골목"])
    comparison_ok = any(term in all_visible for term in ["비교", "반례", "위험한 반례", "좋은 신호", "보류", "체크리스트"])
    missing_visual_diversity = []
    if not field_scene_ok:
        missing_visual_diversity.append("field_example_scene")
    if not map_or_route_ok:
        missing_visual_diversity.append("map_or_route_visual")
    if not comparison_ok:
        missing_visual_diversity.append("comparison_or_counterexample_card")
    if missing_visual_diversity:
        issue = "missing_visual_diversity:" + ",".join(missing_visual_diversity)
        if published:
            observations.append(issue)
        else:
            hard.append(issue)

    forbidden_hits = []
    for term in FORBIDDEN_TERMS:
        if term.lower() in all_visible.lower():
            forbidden_hits.append(term)
    if forbidden_hits:
        hard.append("forbidden_visible_terms:" + ",".join(sorted(set(forbidden_hits))))

    missing = [term for term in REQUIRED_SIGNALS if term not in all_visible]
    if missing:
        hard.append("missing_magazine_signals:" + ",".join(missing))

    missing_strategy = []
    for group, terms in STRATEGY_TERMS.items():
        if not any(term in all_visible for term in terms):
            missing_strategy.append(group)
    if missing_strategy:
        hard.append("missing_strategy_fit:" + ",".join(missing_strategy))

    opening_text = all_visible[:600]
    missing_target_opening = []
    for group, terms in TARGET_OPENING_TERMS.items():
        if not any(term in opening_text for term in terms):
            missing_target_opening.append(group)
    if missing_target_opening:
        hard.append("missing_target_fit_opening:" + ",".join(missing_target_opening))

    title_match = re.search(r"<h1[^>]*>(.*?)</h1>", raw, re.IGNORECASE | re.DOTALL)
    title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else path.parent.name

    rel = path.relative_to(ROOT).as_posix()
    target_fit = not missing_strategy and not missing_target_opening
    return {
        "path": rel,
        "title": title,
        "reviewed_at": now,
        "visible_prose_chars": chars,
        "reader_visual_count": visual_count,
        "target_fit": target_fit,
        "target_opening_missing": missing_target_opening,
        "published": published,
        "hard_issues": hard,
        "soft_issues": soft,
        "media_blockers": media_blockers,
        "observations": observations,
        "ready": not hard and not soft,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--now", default=None, help="ISO timestamp override")
    args = parser.parse_args()
    now = args.now or dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    candidates = sorted(RELEASE_ROOT.glob("*/*/final.html")) if RELEASE_ROOT.exists() else []
    content_slugs = {path.stem for path in CONTENT_ROOT.glob("*.json")} if CONTENT_ROOT.exists() else set()
    results = [review_file(path, now, content_slugs) for path in candidates]
    ready_count = sum(1 for r in results if r["ready"])
    hard_count = sum(len(r["hard_issues"]) for r in results)
    soft_count = sum(len(r["soft_issues"]) for r in results)

    state = {
        "reviewed_at": now,
        "candidate_count": len(results),
        "ready_count": ready_count,
        "hard_issue_count": hard_count,
        "soft_issue_count": soft_count,
        "candidates": results,
    }
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Dongne Radar Candidate Review Latest",
        "",
        f"- reviewed_at: `{now}`",
        f"- candidates: {len(results)}",
        f"- ready: {ready_count}",
        f"- hard_issues: {hard_count}",
        f"- soft_issues: {soft_count}",
        "",
        "## Candidate summary",
    ]
    if not results:
        lines.append("- no release candidates found")
    for item in results:
        lines.append(
            f"- `{item['path']}` — ready={item['ready']} published={item.get('published')} target_fit={item.get('target_fit')} chars={item['visible_prose_chars']} "
            f"visuals={item['reader_visual_count']} hard={len(item['hard_issues'])} soft={len(item['soft_issues'])} media_blockers={len(item.get('media_blockers') or [])}"
        )
        if item.get("media_blockers"):
            lines.append("  - media_blockers: " + "; ".join(item["media_blockers"]))
        if item["hard_issues"]:
            lines.append("  - hard: " + "; ".join(item["hard_issues"]))
        if item["soft_issues"]:
            lines.append("  - soft: " + "; ".join(item["soft_issues"]))
        if item["observations"]:
            lines.append("  - observations: " + "; ".join(item["observations"]))
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"reviewed {len(results)} candidates; ready {ready_count}; hard {hard_count}; soft {soft_count}; wrote reports")
    return 0 if hard_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
