#!/usr/bin/env python3
"""Fail-fast smoke tests for the static `/search/` experience.

This intentionally checks both the generated search data and the browser JS guard that
prevents generic section/view boosts from returning unrelated results.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


class SmokeFailure(AssertionError):
    pass


def normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()


def tokens_of(query: str) -> list[str]:
    return [t for t in normalize(query).split(" ") if t][:8]


def score_item(item: dict[str, Any], tokens: list[str]) -> float:
    title = normalize(item.get("title"))
    desc = normalize(item.get("description"))
    tags = normalize(" ".join(item.get("tags") or []))
    text = normalize(item.get("text"))
    score = 0.0
    matched = False
    matched_count = 0
    for token in tokens:
        phrase_bonus = 0.0
        if token in title:
            score += 12
            phrase_bonus += 12
        if token in tags:
            score += 7
            phrase_bonus += 7
        if token in desc:
            score += 4
            phrase_bonus += 4
        if token in text:
            score += 1
            phrase_bonus += 1
        if phrase_bonus > 0:
            matched = True
            matched_count += 1
    if not matched:
        return 0.0
    if len(tokens) > 1 and matched_count < len(tokens):
        return 0.0
    if item.get("section") == "deals":
        score += 0.5
    views = float(item.get("views") or 0)
    if views > 0:
        import math
        score += min(3, math.log10(views + 1))
    return score


def search(items: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    tokens = tokens_of(query)
    if not tokens:
        return []
    ranked = []
    for item in items:
        score = score_item(item, tokens)
        if score > 0:
            ranked.append({"score": score, "item": item})
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:24]


def load_local() -> tuple[str, str, dict[str, Any]]:
    search_page = (ROOT / "search" / "index.html").read_text(encoding="utf-8", errors="ignore")
    search_js = (ROOT / "assets" / "search.js").read_text(encoding="utf-8", errors="ignore")
    data = json.loads((ROOT / "data" / "search-index.json").read_text(encoding="utf-8-sig"))
    return search_page, search_js, data


def load_live(base_url: str) -> tuple[str, str, dict[str, Any]]:
    base = base_url.rstrip("/")
    def fetch(path: str) -> str:
        with urlopen(f"{base}{path}", timeout=20) as res:
            if res.status != 200:
                raise SmokeFailure(f"LIVE_HTTP_{path}_{res.status}")
            return res.read().decode("utf-8")
    return fetch("/search/?smoke=1"), fetch("/assets/search.js?smoke=1"), json.loads(fetch("/data/search-index.json?smoke=1"))


def assert_true(condition: Any, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def visible_titles(results: list[dict[str, Any]]) -> list[str]:
    return [str(r["item"].get("title") or "") for r in results]


def run_smoke(search_page: str, search_js: str, data: dict[str, Any], *, mode: str) -> dict[str, Any]:
    items = data.get("items")
    assert_true(isinstance(items, list) and len(items) >= 5, "search_index_items_missing")
    assert_true('class="site-search"' in search_page and "/assets/search.js?v=" in search_page, "search_page_form_or_versioned_js_missing")
    assert_true("if (!matched) return 0;" in search_js, "search_js_relevance_guard_missing")
    assert_true("matchedCount < tokens.length" in search_js, "search_js_multi_token_guard_missing")
    assert_true("score += 0.5" in search_js, "search_js_deals_tiebreak_missing")

    cases = [
        ("공기청정기", lambda titles, rows: titles and "공기청정기" in titles[0] and len(rows) <= 4),
        ("공기 청정기", lambda titles, rows: titles and "공기청정기" in titles[0] and len(rows) <= 4),
        ("제습기", lambda titles, rows: titles and "제습기" in titles[0]),
        ("헤드셋", lambda titles, rows: titles and "헤드셋" in titles[0]),
        ("계약", lambda titles, rows: len(rows) >= 2 and all((r["item"].get("section") == "radar") for r in rows[:2])),
        ("없는키워드", lambda titles, rows: len(rows) == 0),
    ]
    observed = {}
    for query, predicate in cases:
        rows = search(items, query)
        titles = visible_titles(rows)
        observed[query] = titles[:5]
        assert_true(predicate(titles, rows), f"search_case_failed:{query}:{titles[:5]}")

    # Regression: the original bug returned every /deals/ item for a single exact query
    air_rows = search(items, "공기청정기")
    unrelated = [r["item"].get("title") for r in air_rows if "공기청정기" not in str(r["item"].get("title") or "")]
    assert_true(not unrelated, f"search_unrelated_air_purifier_results:{unrelated[:5]}")

    # Regression: broad audio category tags should not make speaker pages rank for headset intent.
    headset_rows = search(items, "헤드셋")
    unrelated_audio = [
        r["item"].get("title")
        for r in headset_rows
        if not any(term in str(r["item"].get("title") or "") for term in ("헤드셋", "헤드폰", "이어폰"))
    ]
    assert_true(not unrelated_audio, f"search_unrelated_headset_results:{unrelated_audio[:5]}")

    return {
        "ok": True,
        "mode": mode,
        "items": len(items),
        "cases": observed,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", help="Optional live base URL, e.g. https://r2cuerdame.github.io")
    args = ap.parse_args()
    try:
        if args.live:
            result = run_smoke(*load_live(args.live), mode="live")
        else:
            result = run_smoke(*load_local(), mode="local")
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
