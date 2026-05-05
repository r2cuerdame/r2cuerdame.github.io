#!/usr/bin/env python3
"""Fail-closed GitHub Pages publisher for Dongne Radar release candidates.

This script is intentionally narrow: it only selects clean Dongne Radar release
candidates and publishes them to this GitHub Pages repository. It never touches
Tistory, browser automation, logins, ads, payments, or permissions.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RELEASE_ROOT = ROOT / "release_candidates"
CONTENT_ROOT = ROOT / "content" / "radar"
REPORT_DIR = ROOT / "reports"
REPORT_JSON = REPORT_DIR / "auto-publish-latest.json"
REPORT_MD = REPORT_DIR / "auto-publish-latest.md"
DRY_REPORT_MD = REPORT_DIR / "auto-publish-dry-run-latest.md"
RADAR_DAILY_REPORT = REPORT_DIR / "radar-daily-publish-latest.md"
REVIEW_STATE = REPORT_DIR / "candidate-review-state.json"
BASE_URL = "https://r2cuerdame.github.io"
KST = dt.timezone(dt.timedelta(hours=9))
FORBIDDEN_ACTIONS = "tistory, browser, login, captcha, ads, payment, permission"
DEFAULT_TAGS = ["동네 레이더", "이사 준비", "전월세 계약", "서울 동네 분석", "생활권", "현장 확인"]
PUBLIC_ADD_PATHS = [
    "content/radar",
    "radar",
    "deals",
    "topics",
    "assets/search.js",
    "index.html",
    "404.html",
    "main.css",
    "sitemap.xml",
    "feed.xml",
    "build-info.json",
    "data/search-index.json",
    "llms.txt",
    "ai.txt",
    "humans.txt",
    "robots.txt",
    "README.md",
    "docs/search-indexing.md",
    "search/index.html",
    "guides/index.html",
    "about/index.html",
]


def now_kst() -> dt.datetime:
    return dt.datetime.now(KST)


def parse_dt(value: Any) -> dt.datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    raw = raw.replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(raw)
    except ValueError:
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                parsed = dt.datetime.strptime(raw, fmt)
                break
            except ValueError:
                parsed = None  # type: ignore[assignment]
        else:
            return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path, default: Any = None) -> Any:
    if default is None:
        default = {}
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_command(name: str, cmd: list[str], timeout: int = 180) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "name": name,
            "cmd": cmd,
            "returncode": proc.returncode,
            "ok": proc.returncode == 0,
            "stdout": proc.stdout.strip().splitlines()[-30:],
            "stderr": proc.stderr.strip().splitlines()[-30:],
        }
    except Exception as exc:  # fail closed
        return {"name": name, "cmd": cmd, "returncode": None, "ok": False, "stdout": [], "stderr": [str(exc)]}


def run_review() -> tuple[dict[str, Any], dict[str, Any]]:
    command = run_command("candidate_review", [sys.executable, "scripts/review_maturing_candidates.py"], timeout=240)
    state = load_json(REVIEW_STATE, {})
    if not isinstance(state, dict):
        state = {}
    return command, state


def clean_visible_text(raw_html: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw_html or "", flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def short_description(raw_html: str, fallback: str = "") -> str:
    text = clean_visible_text(raw_html)
    if text.startswith(fallback):
        text = text[len(fallback) :].strip()
    if len(text) <= 165:
        return text or fallback
    return text[:164].rstrip() + "…"


def meta_path_for(final_path: Path) -> Path:
    return final_path.parent / "metadata.json"


def reviewed_candidates() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    review_command, review_state = run_review()
    content_slugs = {path.stem for path in CONTENT_ROOT.glob("*.json")} if CONTENT_ROOT.exists() else set()
    candidates: list[dict[str, Any]] = []
    for item in review_state.get("candidates") or []:
        path = ROOT / str(item.get("path") or "")
        if not path.exists() or path.name != "final.html":
            continue
        meta = load_json(meta_path_for(path), {})
        slug = str(meta.get("slug") or path.parent.name).strip()
        title = str(meta.get("title") or item.get("title") or slug).strip()
        hard = list(item.get("hard_issues") or [])
        soft = list(item.get("soft_issues") or [])
        review_ready = bool(item.get("ready"))
        target_fit = bool(item.get("target_fit"))
        published = (
            slug in content_slugs
            or str(meta.get("status") or "") == "published_to_pages"
            or bool(meta.get("pages_published_at"))
        )
        eligible = review_ready and target_fit and not hard and not soft and not published
        sort_dt = (
            parse_dt(meta.get("mature_started_at"))
            or parse_dt(meta.get("created_at"))
            or parse_dt(meta.get("date"))
            or parse_dt(meta.get("updated_at"))
            or dt.datetime.fromtimestamp(path.stat().st_mtime, KST)
        )
        candidates.append(
            {
                "path": rel(path),
                "slug": slug,
                "title": title,
                "review_ready": review_ready,
                "target_fit": target_fit,
                "target_fit_missing": item.get("target_opening_missing") or [],
                "published": published,
                "eligible": eligible,
                "hard_issues": hard,
                "soft_issues": soft,
                "visible_prose_chars": item.get("visible_prose_chars"),
                "reader_visual_count": item.get("reader_visual_count"),
                "sort_key": sort_dt.isoformat(),
            }
        )
    candidates.sort(key=lambda c: (c["sort_key"], c["slug"]))
    return review_command, review_state, candidates


def published_times() -> dict[str, dt.datetime]:
    times: dict[str, dt.datetime] = {}
    for path in sorted(CONTENT_ROOT.glob("*.json")) if CONTENT_ROOT.exists() else []:
        data = load_json(path, {})
        slug = str(data.get("slug") or path.stem)
        published_at = parse_dt(data.get("published_at")) or parse_dt(data.get("date")) or parse_dt(data.get("updated_at"))
        if published_at:
            times[slug] = published_at
    for meta_path in sorted(RELEASE_ROOT.glob("*/*/metadata.json")) if RELEASE_ROOT.exists() else []:
        meta = load_json(meta_path, {})
        slug = str(meta.get("slug") or meta_path.parent.name)
        if str(meta.get("status") or "") != "published_to_pages" and not meta.get("pages_published_at"):
            continue
        published_at = parse_dt(meta.get("pages_published_at")) or parse_dt(meta.get("published_at")) or parse_dt(meta.get("updated_at"))
        if published_at and (slug not in times or published_at > times[slug]):
            times[slug] = published_at
    return times


def decide(args: argparse.Namespace, candidates: list[dict[str, Any]], at: dt.datetime) -> dict[str, Any]:
    times = published_times()
    published_today = sum(1 for value in times.values() if value.astimezone(KST).date() == at.date())
    last_publish_at = max(times.values()) if times else None
    hours_since_last = None
    if last_publish_at:
        hours_since_last = round((at - last_publish_at).total_seconds() / 3600, 3)

    ready_clean = [c for c in candidates if c["review_ready"] and c["target_fit"] and not c["hard_issues"] and not c["soft_issues"]]
    ready_unpublished = [c for c in ready_clean if not c["published"]]
    eligible = [c for c in candidates if c["eligible"]]
    day_limit = args.max_per_day if args.mode == "adaptive" else min(args.max_per_day, 1)
    day_open = published_today < day_limit
    spacing_open = hours_since_last is None or hours_since_last >= args.min_interval_hours
    daily_floor_open = published_today == 0
    if args.mode == "adaptive":
        buffer_over_target = len(ready_unpublished) > args.ready_target
        queue_open = daily_floor_open or buffer_over_target
        queue_reason = f"queue_guard:ready_unpublished={len(ready_unpublished)}<=ready_target={args.ready_target}; daily_floor_open={daily_floor_open}"
    else:
        buffer_over_target = len(ready_unpublished) > 0
        queue_open = buffer_over_target
        queue_reason = "queue_guard:ready_unpublished=0"

    reasons: list[str] = []
    if not eligible:
        reasons.append("no_eligible_unpublished_candidate")
    if not queue_open:
        reasons.append(queue_reason)
    if not day_open:
        reasons.append(f"day_guard:published_today={published_today}>=max_per_day={day_limit}")
    if not spacing_open:
        reasons.append(f"spacing_guard:hours_since_last={hours_since_last}<min_interval_hours={args.min_interval_hours}")

    selected = None if reasons else eligible[0]
    if selected:
        status = "selected"
    elif not eligible:
        status = "no_ready_candidate"
    else:
        status = "slot_closed"

    return {
        "status": status,
        "counts": {
            "candidate_count": len(candidates),
            "ready_total": len(ready_clean),
            "ready_unpublished": len(ready_unpublished),
            "published_total": len(times),
            "published_today": published_today,
            "review_blocked": len(candidates) - len(ready_clean),
        },
        "guards": {
            "mode": args.mode,
            "max_per_day": day_limit,
            "min_interval_hours": args.min_interval_hours,
            "ready_target": args.ready_target,
            "day_open": day_open,
            "spacing_open": spacing_open,
            "queue_open": queue_open,
            "daily_floor_open": daily_floor_open,
            "buffer_over_target": buffer_over_target,
            "hours_since_last_publish": hours_since_last,
            "last_publish_at": last_publish_at.isoformat(timespec="seconds") if last_publish_at else None,
        },
        "reasons": reasons,
        "selected": selected,
    }


def extract_article_body(final_html: str) -> str:
    match = re.search(r"<article\b[^>]*>([\s\S]*?)</article>", final_html, flags=re.I)
    if not match:
        match = re.search(r"<main\b[^>]*>([\s\S]*?)</main>", final_html, flags=re.I)
    body = match.group(1).strip() if match else final_html.strip()
    body = re.sub(r"<h1\b[^>]*>[\s\S]*?</h1>", "", body, count=1, flags=re.I).strip()
    if re.search(r"<\s*script\b", body, re.I):
        raise RuntimeError("script_tag_present_in_publish_body")
    body = re.sub(r"<style\b[^>]*>[\s\S]*?</style>", "", body, flags=re.I).strip()
    return body


def first_existing_thumbnail(slug: str) -> str:
    for ext in ("webp", "svg", "png", "jpg", "jpeg"):
        path = ROOT / "assets" / "radar" / "thumbs" / f"{slug}.{ext}"
        if path.exists():
            return f"/assets/radar/thumbs/{slug}.{ext}"
    return ""


def article_json_for(selected: dict[str, Any], published_at: str) -> dict[str, Any]:
    final_path = ROOT / selected["path"]
    meta = load_json(meta_path_for(final_path), {})
    raw = final_path.read_text(encoding="utf-8", errors="replace")
    body = extract_article_body(raw)
    title = str(meta.get("title") or selected.get("title") or "").strip()
    description = str(meta.get("description") or short_description(body, title)).strip()
    tags = meta.get("tags") or DEFAULT_TAGS
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    image_url = str(meta.get("image_url") or meta.get("thumbnail_url") or first_existing_thumbnail(selected["slug"]))
    article: dict[str, Any] = {
        "slug": selected["slug"],
        "title": title,
        "description": description,
        "date": published_at,
        "category": "동네 레이더",
        "tags": tags,
        "is_affiliate": False,
        "source": "release_candidate",
        "source_release_candidate": selected["path"],
        "target_audience": meta.get("target_audience") or "서울·수도권에서 3~12개월 안에 이사·전월세 계약·거주지 비교를 해야 하는 25~39세",
        "body_html": body,
        "published_at": published_at,
        "updated_at": published_at,
    }
    if image_url:
        article["image_url"] = image_url
    for key in ("radar_suspicion", "field_mission", "editorial_positioning"):
        if meta.get(key):
            article[key] = meta[key]
    return article


def publish_selected(selected: dict[str, Any], at: dt.datetime, dry_run: bool = False, no_push: bool = False) -> dict[str, Any]:
    published_at = at.isoformat(timespec="seconds")
    final_path = ROOT / selected["path"]
    meta_path = meta_path_for(final_path)
    meta = load_json(meta_path, {})
    slug = selected["slug"]
    url = f"{BASE_URL}/radar/{slug}/"
    commands: list[dict[str, Any]] = []

    if dry_run:
        return {"status": "dry_run_selected", "slug": slug, "title": selected["title"], "url": url, "commands": commands}

    CONTENT_ROOT.mkdir(parents=True, exist_ok=True)
    article = article_json_for(selected, published_at)
    write_json(CONTENT_ROOT / f"{slug}.json", article)

    meta.update(
        {
            "status": "published_to_pages",
            "pages_published_at": published_at,
            "pages_url": url,
            "updated_at": published_at,
        }
    )
    write_json(meta_path, meta)

    commands.append(run_command("build_site", [sys.executable, "scripts/build_site.py"], timeout=240))
    if not commands[-1]["ok"]:
        return {"status": "build_failed", "slug": slug, "title": selected["title"], "url": url, "commands": commands}
    commands.append(run_command("public_site_quality_local", [sys.executable, "scripts/audit_public_site_quality.py"], timeout=240))
    if not commands[-1]["ok"]:
        return {"status": "quality_audit_failed", "slug": slug, "title": selected["title"], "url": url, "commands": commands}

    commands.append(run_command("git_fetch", ["git", "fetch", "--quiet", "origin"], timeout=180))
    commands.append(run_command("git_add", ["git", "add", *PUBLIC_ADD_PATHS, rel(meta_path)], timeout=180))
    commands.append(run_command("git_diff_cached", ["git", "diff", "--cached", "--quiet"], timeout=60))
    diff_cmd = commands[-1]
    if diff_cmd["returncode"] == 0:
        return {"status": "already_published", "slug": slug, "title": selected["title"], "url": url, "commands": commands}
    if diff_cmd["returncode"] not in (0, 1):
        return {"status": "git_diff_failed", "slug": slug, "title": selected["title"], "url": url, "commands": commands}

    commands.append(run_command("git_commit", ["git", "commit", "-m", f"Publish Dongne Radar: {slug}"], timeout=180))
    if not commands[-1]["ok"]:
        return {"status": "git_commit_failed", "slug": slug, "title": selected["title"], "url": url, "commands": commands}
    if no_push:
        return {"status": "committed_no_push", "slug": slug, "title": selected["title"], "url": url, "commands": commands}
    commands.append(run_command("git_push", ["git", "push", "origin", "HEAD"], timeout=240))
    if not commands[-1]["ok"]:
        return {"status": "git_push_failed", "slug": slug, "title": selected["title"], "url": url, "commands": commands}
    return {"status": "published_to_pages", "slug": slug, "title": selected["title"], "url": url, "commands": commands}


def write_reports(state: dict[str, Any], dry_run: bool = False) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(REPORT_JSON, state)

    decision = state.get("decision") or {}
    counts = decision.get("counts") or {}
    guards = decision.get("guards") or {}
    selected = decision.get("selected") or {}
    publish_result = state.get("publish_result") or {}
    status = state.get("status") or decision.get("status") or "unknown"
    title = publish_result.get("title") or selected.get("title") or "none"
    url = publish_result.get("url") or (f"{BASE_URL}/radar/{selected.get('slug')}/" if selected.get("slug") else "none")
    blockers = decision.get("reasons") or []
    external_executed = publish_result.get("status") in {"published_to_pages", "committed_no_push", "already_published"}

    lines = [
        "# Dongne Radar Auto Publish Latest",
        "",
        f"- checked_at: `{state['checked_at']}`",
        f"- mode: `{guards.get('mode')}`",
        f"- status: `{status}`",
        f"- external_publish_executed: `{str(external_executed).lower()}`",
        "- github_pages_only: `true`",
        f"- candidates_reviewed: {counts.get('candidate_count', 0)}",
        f"- ready_total: {counts.get('ready_total', 0)}",
        f"- ready_unpublished: {counts.get('ready_unpublished', 0)}",
        f"- published_today: {counts.get('published_today', 0)} / {guards.get('max_per_day')}",
        f"- spacing_open: `{guards.get('spacing_open')}` hours_since_last={guards.get('hours_since_last_publish')}",
        f"- queue_open: `{guards.get('queue_open')}` ready_target={guards.get('ready_target')}",
        f"- selected_public_candidate: `{selected.get('slug') or 'none'}`",
        f"- forbidden_actions: {FORBIDDEN_ACTIONS}",
        "- blockers: " + (", ".join(blockers) if blockers else "none"),
        "",
        "## Candidate summary",
    ]
    candidates = state.get("candidates") or []
    if not candidates:
        lines.append("- no release candidates found")
    for item in candidates:
        lines.append(
            f"- `{item['path']}` — eligible={item['eligible']} ready={item['review_ready']} target_fit={item['target_fit']} "
            f"published={item['published']} hard={len(item['hard_issues'])} soft={len(item['soft_issues'])}"
        )
    lines.extend(["", "## Decision"])
    if publish_result:
        lines.append(f"- {publish_result.get('status')}: {title} — {url}")
    elif blockers:
        lines.append(f"- {decision.get('status')}: slot closed or no unpublished clean candidate; fail-closed, production continues.")
    else:
        lines.append("- no action")
    text = "\n".join(lines) + "\n"
    REPORT_MD.write_text(text, encoding="utf-8")
    if dry_run:
        DRY_REPORT_MD.write_text(text.replace("# Dongne Radar Auto Publish Latest", "# Dongne Radar Auto Publish Dry Run Latest", 1), encoding="utf-8")

    daily_reason = "; ".join(blockers) if blockers else f"selected={selected.get('slug') or 'none'}"
    daily_lines = [
        "# Radar Adaptive Publish Latest",
        "",
        f"- checked_at: {state['checked_at']}",
        f"- status: {status}",
        f"- title: {title}",
        f"- url: {url if publish_result else 'none'}",
        f"- reason: ready_unpublished={counts.get('ready_unpublished', 0)}; published_today={counts.get('published_today', 0)}; {daily_reason}",
        f"- action: {'published' if publish_result.get('status') == 'published_to_pages' else 'none'}",
    ]
    RADAR_DAILY_REPORT.write_text("\n".join(daily_lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["daily", "adaptive"], default="adaptive")
    parser.add_argument("--max-per-day", type=int, default=4)
    parser.add_argument("--min-interval-hours", type=float, default=2.0)
    parser.add_argument("--ready-target", type=int, default=7)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-push", action="store_true", help="commit locally but do not push after publishing")
    parser.add_argument("--now", default=None, help="ISO timestamp override for tests")
    args = parser.parse_args()

    at = parse_dt(args.now) if args.now else now_kst()
    if at is None:
        at = now_kst()
    checked_at = at.isoformat(timespec="seconds")

    review_command, review_state, candidates = reviewed_candidates()
    decision = decide(args, candidates, at)
    publish_result: dict[str, Any] | None = None
    status = decision["status"]
    selected = decision.get("selected")
    if selected:
        publish_result = publish_selected(selected, at, dry_run=args.dry_run, no_push=args.no_push)
        status = str(publish_result.get("status") or status)

    state = {
        "checked_at": checked_at,
        "status": status,
        "decision": decision,
        "candidates": candidates,
        "review_command": review_command,
        "review_summary": {
            "candidate_count": review_state.get("candidate_count", 0),
            "ready_count": review_state.get("ready_count", 0),
            "hard_issue_count": review_state.get("hard_issue_count", 0),
            "soft_issue_count": review_state.get("soft_issue_count", 0),
        },
        "publish_result": publish_result,
        "forbidden_actions": FORBIDDEN_ACTIONS,
    }
    write_reports(state, dry_run=args.dry_run)

    title = (publish_result or {}).get("title") or (selected or {}).get("title") or "none"
    print(f"status={status} title={title} ready_unpublished={decision['counts']['ready_unpublished']} published_today={decision['counts']['published_today']}")
    return 0 if status in {"no_ready_candidate", "slot_closed", "published_to_pages", "already_published", "dry_run_selected", "committed_no_push"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
