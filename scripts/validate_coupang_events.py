#!/usr/bin/env python3
"""Validate manually copied Coupang Partners event slots.

This is intentionally offline: it never logs into Coupang, never reads cookies, and
never fabricates event copy. The JSON file is a safe manual/semi-automatic input
surface for the /deals/ landing slot.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "data" / "coupang_events.json"
SECRET_KEYWORDS = ("cookie", "token", "password", "secret", "session", "credential")


def parse_iso_date(value: Any, field: str, event_id: str) -> date:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError(f"{event_id}:{field}_required")
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{event_id}:{field}_invalid") from exc


def url_is_safe_coupang_tracking(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    host = parsed.netloc.lower().split("@")[-1]
    if parsed.scheme != "https":
        return False
    if not (host == "link.coupang.com" or host.endswith(".coupang.com")):
        return False
    return "lptag=" in url.lower() or host == "link.coupang.com"


def validate_event(raw: Any, index: int, today: date) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        raise ValueError(f"event-{index}:object_required")
    if raw.get("enabled") is False:
        return {"event_id": raw.get("event_id") or f"event-{index}", "status": "disabled"}

    key_blob = " ".join(str(key).lower() for key in raw.keys())
    if any(keyword in key_blob for keyword in SECRET_KEYWORDS):
        raise ValueError(f"event-{index}:secret_like_key_forbidden")

    event_id = str(raw.get("event_id") or raw.get("slug") or f"event-{index}").strip()
    if not event_id or not re.fullmatch(r"[A-Za-z0-9_-]{2,80}", event_id):
        raise ValueError(f"event-{index}:event_id_invalid")

    event_name = str(raw.get("event_name") or raw.get("title") or "").strip()
    if not (2 <= len(event_name) <= 90):
        raise ValueError(f"{event_id}:event_name_required")

    landing_url = str(raw.get("landing_url") or "").strip()
    if not url_is_safe_coupang_tracking(landing_url):
        raise ValueError(f"{event_id}:landing_url_not_tracked_coupang")

    start_date = parse_iso_date(raw.get("start_date"), "start_date", event_id)
    end_date = parse_iso_date(raw.get("end_date"), "end_date", event_id)
    if end_date < start_date:
        raise ValueError(f"{event_id}:end_before_start")
    if end_date < today:
        raise ValueError(f"{event_id}:expired_event_forbidden")

    image_url = str(raw.get("image_url") or "").strip()
    if image_url and not image_url.startswith("https://"):
        raise ValueError(f"{event_id}:image_url_https_required")

    tags = raw.get("tags") or []
    if isinstance(tags, str):
        tags = [part.strip() for part in tags.split(",") if part.strip()]
    if not isinstance(tags, list):
        raise ValueError(f"{event_id}:tags_must_be_list_or_comma_string")

    return {
        "event_id": event_id,
        "status": "active" if start_date <= today <= end_date else "future",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }


def validate_file(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("root_object_required")
    if any(keyword in " ".join(str(key).lower() for key in data.keys()) for keyword in SECRET_KEYWORDS):
        raise ValueError("root_secret_like_key_forbidden")
    events = data.get("events")
    if not isinstance(events, list):
        raise ValueError("events_list_required")

    today = datetime.now(timezone(timedelta(hours=9))).date()
    checked = [validate_event(raw, index, today) for index, raw in enumerate(events, start=1)]
    active_count = sum(1 for item in checked if item and item.get("status") == "active")
    return {
        "ok": True,
        "path": str(path),
        "events_checked": len(events),
        "active_events": active_count,
        "render_limit": 3,
        "publish_behavior": "render_1_to_3_cards" if active_count else "no_public_event_cards",
        "checked": checked,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=str(DEFAULT_PATH))
    args = parser.parse_args()
    path = Path(args.path)
    try:
        result = validate_file(path)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
