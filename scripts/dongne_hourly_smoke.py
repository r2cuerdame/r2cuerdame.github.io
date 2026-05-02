#!/usr/bin/env python3
"""Project-local hourly smoke wrapper for Dongne Radar.

Non-destructive checks only: docs/policy markers, syntax compile, candidate
review, generated local site sanity, and warning-only live Radar URL reachability.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"
REPORT_MD = REPORT_DIR / "hourly-smoke-latest.md"
REPORT_JSON = REPORT_DIR / "hourly-smoke-latest.json"
REVIEW_STATE = REPORT_DIR / "candidate-review-state.json"
KST = dt.timezone(dt.timedelta(hours=9), name="KST")

REQUIRED_FILES = [
    "README.md",
    "PUBLISHER_OPERATING_SYSTEM.md",
    "AUTO_PUBLISH_POLICY.md",
    "READER_QA_SCORECARD.md",
    "PRODUCTION_CHECKLIST.md",
    "OPERATIONS_BOARD.md",
    "ops/hourly-department-turns.md",
]

POLICY_MARKERS = {
    "PUBLISHER_OPERATING_SYSTEM.md": [
        "GitHub Pages",
        "7일/168시간은 개별 글의 발행 지연 게이트가 아니라 rolling buffer",
        "발행 막힘 처리",
    ],
    "AUTO_PUBLISH_POLICY.md": [
        "매일 1개가 floor",
        "visible body length",
        "reader-facing visual count",
        "visual rhythm",
    ],
    "READER_QA_SCORECARD.md": ["4,500자", "8개", "visual rhythm", "금칙어"],
    "PRODUCTION_CHECKLIST.md": ["70-final-html", "visual rhythm", "dedicated publisher desk"],
    "OPERATIONS_BOARD.md": ["GitHub Pages `/radar/`", "Tistory"],
    "ops/hourly-department-turns.md": ["deliver: local", "발행부 턴"],
}


def now_kst() -> str:
    return dt.datetime.now(KST).isoformat(timespec="seconds")


def short_lines(text: str, limit: int = 6) -> list[str]:
    lines = [line.rstrip() for line in (text or "").splitlines() if line.strip()]
    return lines[:limit]


def run_command(name: str, args: list[str], timeout: int = 120) -> dict:
    try:
        proc = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "name": name,
            "returncode": proc.returncode,
            "stdout_lines": short_lines(proc.stdout),
            "stderr_lines": short_lines(proc.stderr),
            "ok": proc.returncode == 0,
        }
    except Exception as exc:  # pragma: no cover - defensive smoke wrapper
        return {
            "name": name,
            "returncode": None,
            "stdout_lines": [],
            "stderr_lines": [str(exc)],
            "ok": False,
        }


def check_docs() -> dict:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    marker_misses: list[str] = []
    for rel, markers in POLICY_MARKERS.items():
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in markers:
            if marker not in text:
                marker_misses.append(f"{rel}:{marker}")
    return {"ok": not missing and not marker_misses, "missing": missing, "marker_misses": marker_misses}


def load_review_summary() -> dict:
    if not REVIEW_STATE.exists():
        return {"ok": False, "error": "candidate-review-state.json_missing"}
    try:
        data = json.loads(REVIEW_STATE.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"ok": False, "error": f"candidate-review-state.json_invalid:{exc}"}
    hard = int(data.get("hard_issue_count") or 0)
    soft = int(data.get("soft_issue_count") or 0)
    return {
        "ok": hard == 0 and soft == 0,
        "candidate_count": int(data.get("candidate_count") or 0),
        "ready_count": int(data.get("ready_count") or 0),
        "hard_issue_count": hard,
        "soft_issue_count": soft,
    }


def local_site_smoke() -> dict:
    checks = {
        "index_html": ROOT / "index.html",
        "radar_index": ROOT / "radar" / "index.html",
        "main_css": ROOT / "main.css",
        "sitemap": ROOT / "sitemap.xml",
        "robots": ROOT / "robots.txt",
        "feed": ROOT / "feed.xml",
    }
    missing = [name for name, path in checks.items() if not path.exists()]
    failures: list[str] = []
    if missing:
        failures.append("missing:" + ",".join(missing))
    try:
        radar = checks["radar_index"].read_text(encoding="utf-8", errors="replace")
        if "동네 레이더" not in radar or "/radar/" not in radar:
            failures.append("radar_index_marker_missing")
        if "radar-card-visual" not in radar or "theme-" not in radar:
            failures.append("radar_index_visual_card_missing")
        article_match = re.search(r'href="(/radar/[^"/]+/)"', radar)
        if article_match:
            article_path = ROOT / article_match.group(1).strip("/") / "index.html"
            article_html = article_path.read_text(encoding="utf-8", errors="replace")
            for marker in ["radar-experience-grid", "radar-map-card", "radar-brief-stack"]:
                if marker not in article_html:
                    failures.append(f"radar_article_visual_marker_missing:{marker}")
        else:
            failures.append("radar_article_link_missing")
    except Exception as exc:
        failures.append(f"radar_index_read_error:{exc}")
    try:
        css = checks["main_css"].read_text(encoding="utf-8", errors="replace")
        for marker in ["radar-card-visual", "radar-experience-grid", ".article-content .callout"]:
            if marker not in css:
                failures.append(f"visual_css_marker_missing:{marker}")
    except Exception as exc:
        failures.append(f"main_css_read_error:{exc}")
    try:
        sitemap = checks["sitemap"].read_text(encoding="utf-8", errors="replace")
        if "https://r2cuerdame.github.io/radar/" not in sitemap:
            failures.append("sitemap_radar_url_missing")
    except Exception as exc:
        failures.append(f"sitemap_read_error:{exc}")
    return {
        "name": "local_site_smoke",
        "returncode": 0 if not failures else 1,
        "stdout_lines": ["local static site markers ok"] if not failures else [],
        "stderr_lines": failures[:6],
        "ok": not failures,
    }


def check_live_radar() -> dict:
    url = "https://r2cuerdame.github.io/radar/?hourly_smoke=1"
    try:
        req = Request(url, headers={"User-Agent": "DongneRadarHourlySmoke/1.0"})
        with urlopen(req, timeout=20) as res:
            status = int(getattr(res, "status", 0) or 0)
            ok = 200 <= status < 400
            return {"ok": ok, "warning_only": True, "status": status, "url": url}
    except Exception as exc:
        return {"ok": False, "warning_only": True, "status": None, "url": url, "error": str(exc)}


def write_reports(state: dict) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    review = state.get("review") or {}
    live = state.get("live_radar") or {}
    failures = state.get("failures") or []
    warnings = state.get("warnings") or []
    commands = state.get("commands") or []

    lines = [
        "# Dongne Radar Hourly Smoke Latest",
        "",
        f"- checked_at: `{state['checked_at']}`",
        f"- status: `{state['status']}`",
        "- failures: " + (", ".join(failures) if failures else "none"),
        "- warnings: " + (", ".join(warnings) if warnings else "none"),
        f"- candidate_review: candidates={review.get('candidate_count', 0)} ready={review.get('ready_count', 0)} hard={review.get('hard_issue_count', 0)} soft={review.get('soft_issue_count', 0)}",
        f"- live_radar: warning_only ok={live.get('ok')} status={live.get('status')}",
        "",
        "## Checks",
        f"- docs_policy_markers: {'pass' if state.get('docs', {}).get('ok') else 'fail'}",
    ]
    for name in ["py_compile", "candidate_review", "local_site_smoke"]:
        item = next((cmd for cmd in commands if cmd.get("name") == name), None)
        lines.append(f"- {name}: {'pass' if item and item.get('ok') else 'fail'}")
    lines.append(f"- live_url_reachability: {'pass' if live.get('ok') else 'warning'}")
    lines.extend(
        [
            "",
            "## Handoff",
            "- 글 keep/발행부 슬롯 확인 + 다음 부서 작업: clean 후보는 보관하거나 adaptive 슬롯으로 공개하고, hourly는 다음 기사/다음 stage 보강을 계속한다.",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    checked_at = now_kst()
    docs = check_docs()
    commands: list[dict] = []

    py_files = [
        "scripts/dongne_hourly_smoke.py",
        "scripts/review_maturing_candidates.py",
        "scripts/publish_next_radar_candidate.py",
        "scripts/build_site.py",
    ]
    py_files.extend(str(path.relative_to(ROOT)) for path in sorted((ROOT / "scripts").glob("*.py")) if str(path.relative_to(ROOT)) not in py_files)
    commands.append(run_command("py_compile", [sys.executable, "-m", "py_compile", *py_files]))
    commands.append(run_command("candidate_review", [sys.executable, "scripts/review_maturing_candidates.py"]))
    review = load_review_summary()
    if not review.get("ok"):
        commands[-1]["ok"] = False
    commands.append(local_site_smoke())
    live = check_live_radar()

    failures: list[str] = []
    warnings: list[str] = []
    if not docs.get("ok"):
        failures.append("docs_policy_markers")
    for cmd in commands:
        if not cmd.get("ok"):
            failures.append(str(cmd.get("name") or "command"))
    if not review.get("ok") and "candidate_review" not in failures:
        failures.append("candidate_review")
    if not live.get("ok"):
        warnings.append("live_url_reachability")

    status = "fail" if failures else "pass"
    state = {
        "checked_at": checked_at,
        "status": status,
        "failures": failures,
        "warnings": warnings,
        "docs": docs,
        "commands": commands,
        "review": review,
        "live_radar": live,
        "operating_rule": "publishing blocked or delayed does not stop production; keep clean articles and continue the next department output",
    }
    write_reports(state)
    print(
        f"hourly smoke {status}; ready {review.get('ready_count', 0)}; "
        f"hard {review.get('hard_issue_count', 0)}; soft {review.get('soft_issue_count', 0)}; warnings {len(warnings)}"
    )
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
