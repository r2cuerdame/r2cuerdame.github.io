#!/usr/bin/env python3
"""Audit public Coupang/affiliate pages for Google Ads brand-keyword risk.

Allowed:
- mandatory affiliate disclosure text containing "쿠팡 파트너스" and "수수료"
- href/src URLs pointing to coupang.com / coupangcdn.com

Flagged:
- titles, descriptions, tags, search keywords, visible CTA/body copy, slugs that target
  Coupang brand terms (쿠팡/coupang/로켓배송).
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import html as html_lib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
BRAND_RE = re.compile(r"쿠팡|coupang|로켓배송", re.I)
DISCLOSURE_RE = re.compile(r"쿠팡\s*파트너스[^.。\n]*(수수료|제공받)")

class PublicTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.visible: list[str] = []
        self.meta: list[tuple[str, str]] = []
        self.in_title = False
        self.title: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_name = tag.lower()
        if tag_name in {"script", "style", "noscript"}:
            self.skip_depth += 1
            return
        if tag_name == "title":
            self.in_title = True
        if tag_name == "meta":
            attr = {k.lower(): v or "" for k, v in attrs}
            name = attr.get("name") or attr.get("property")
            content = attr.get("content") or ""
            if name and content:
                self.meta.append((name, content))

    def handle_endtag(self, tag: str) -> None:
        tag_name = tag.lower()
        if tag_name in {"script", "style", "noscript"} and self.skip_depth:
            self.skip_depth -= 1
            return
        if tag_name == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.in_title:
            self.title.append(data)
        self.visible.append(data)


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(value or "")).strip()


def looks_like_url(value: str) -> bool:
    return bool(re.match(r"^(https?:)?//", normalize(value), flags=re.I))


def offending_contexts(value: str) -> list[str]:
    text = normalize(value)
    if not text:
        return []
    contexts: list[str] = []
    for match in BRAND_RE.finditer(text):
        start = max(0, match.start() - 45)
        end = min(len(text), match.end() + 80)
        ctx = text[start:end]
        if DISCLOSURE_RE.search(ctx):
            continue
        contexts.append(ctx)
    return contexts


def audit_json(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    problems: list[str] = []
    for key in ("slug", "title", "description", "category", "meta"):
        for ctx in offending_contexts(str(data.get(key) or "")):
            problems.append(f"{path.relative_to(ROOT)}:{key}: {ctx}")
    tags = data.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    for ctx in offending_contexts(" | ".join(str(x) for x in tags)):
        problems.append(f"{path.relative_to(ROOT)}:tags: {ctx}")
    for ctx in offending_contexts(re.sub(r"<[^>]+>", " ", str(data.get("body_html") or ""))):
        problems.append(f"{path.relative_to(ROOT)}:body: {ctx}")
    return problems


def audit_html(path: Path) -> list[str]:
    parser = PublicTextParser()
    parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
    problems: list[str] = []
    for label, value in [("title", " ".join(parser.title)), ("visible", " ".join(parser.visible))]:
        for ctx in offending_contexts(value):
            problems.append(f"{path.relative_to(ROOT)}:{label}: {ctx}")
    for name, content in parser.meta:
        if looks_like_url(content):
            continue
        for ctx in offending_contexts(content):
            problems.append(f"{path.relative_to(ROOT)}:meta[{name}]: {ctx}")
    return problems


def main() -> int:
    problems: list[str] = []
    for path in sorted((ROOT / "content" / "deals").glob("*.json")):
        problems.extend(audit_json(path))
    html_roots = [ROOT / "index.html", ROOT / "deals", ROOT / "search"]
    for base in html_roots:
        if base.is_file():
            problems.extend(audit_html(base))
        elif base.exists():
            for path in sorted(base.glob("**/*.html")):
                problems.extend(audit_html(path))
    if problems:
        print("BRAND_SAFETY_FAIL")
        for item in problems:
            print("-", item)
        return 1
    print("BRAND_SAFETY_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
