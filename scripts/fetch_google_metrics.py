#!/usr/bin/env python3
"""Fetch public-site page metrics for the static build.

Preferred source is GA4 Data API. The script is deliberately fail-soft: if no
Google Analytics property/API credential is configured, it writes a harmless
status file with no page counts rather than inventing numbers.

Local config options (not required):
- env GA4_PROPERTY_ID=123456789
- env GA_MEASUREMENT_ID=G-XXXX (for build-time gtag injection)
- env GOOGLE_APPLICATION_CREDENTIALS=/path/service-account.json
- env DEALS_ANALYTICS_CONFIG=/path/deals_google_metrics.json
- /root/.hermes/secrets/deals_google_metrics.json
- data/metrics/analytics_config.json

Example config JSON:
{
  "ga4_property_id": "123456789",
  "measurement_id": "G-XXXXXXX",
  "lookback_days": 30
}
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "metrics" / "page_views.json"
KST = timezone(timedelta(hours=9))
BASE = "https://r2cuerdame.github.io"
CONFIG_PATHS = [
    Path(os.environ["DEALS_ANALYTICS_CONFIG"]) if os.environ.get("DEALS_ANALYTICS_CONFIG") else None,
    Path("/root/.hermes/secrets/deals_google_metrics.json"),
    ROOT / "data" / "metrics" / "analytics_config.json",
]


def now() -> str:
    return datetime.now(KST).isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def load_config() -> dict[str, Any]:
    cfg: dict[str, Any] = {}
    for path in CONFIG_PATHS:
        if path and path.exists():
            data = load_json(path)
            if isinstance(data, dict):
                cfg.update(data)
    env_map = {
        "GA4_PROPERTY_ID": "ga4_property_id",
        "GA_MEASUREMENT_ID": "measurement_id",
        "GTAG_MEASUREMENT_ID": "measurement_id",
        "GOOGLE_APPLICATION_CREDENTIALS": "google_application_credentials",
    }
    for env, key in env_map.items():
        if os.environ.get(env):
            cfg[key] = os.environ[env]
    return cfg


def existing_pages() -> dict[str, Any]:
    if not OUT.exists():
        return {}
    data = load_json(OUT)
    pages = data.get("pages") if isinstance(data, dict) else {}
    return pages if isinstance(pages, dict) else {}


def norm_path(raw: str) -> str:
    path = str(raw or "").strip()
    if path.startswith(BASE):
        path = path[len(BASE):]
    path = path.split("#", 1)[0].split("?", 1)[0]
    if not path.startswith("/"):
        path = "/" + path
    if path.endswith("index.html"):
        path = path[: -len("index.html")]
    if path != "/" and not path.endswith("/"):
        path += "/"
    return path


def comparable(payload: dict[str, Any]) -> dict[str, Any]:
    clone = dict(payload)
    clone.pop("updated_at", None)
    return clone


def write_payload(payload: dict[str, Any]) -> dict[str, Any]:
    existing = load_json(OUT) if OUT.exists() else {}
    if isinstance(existing, dict) and comparable(existing) == comparable(payload) and existing.get("updated_at"):
        # Avoid meaningless hourly timestamp churn in the Pages repo.
        payload["updated_at"] = existing["updated_at"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return payload


def gcloud_access_token() -> str:
    if not shutil.which("gcloud"):
        return ""
    proc = subprocess.run(
        ["gcloud", "auth", "application-default", "print-access-token"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
    )
    if proc.returncode == 0:
        return proc.stdout.strip()
    return ""


def service_account_token(credentials_path: str) -> str:
    if not credentials_path:
        return ""
    try:
        from google.oauth2 import service_account  # type: ignore
        from google.auth.transport.requests import Request  # type: ignore
    except Exception:
        return ""
    scopes = ["https://www.googleapis.com/auth/analytics.readonly"]
    creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)
    creds.refresh(Request())
    return str(creds.token or "")


def run_ga4_rest(property_id: str, token: str, lookback_days: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    endpoint = f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"
    body = {
        "dateRanges": [{"startDate": f"{lookback_days}daysAgo", "endDate": "today"}],
        "dimensions": [{"name": "pagePath"}],
        "metrics": [{"name": "screenPageViews"}, {"name": "activeUsers"}],
        "limit": 1000,
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            data = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")[-500:]
        raise RuntimeError(f"ga4_http_{exc.code}: {detail}") from exc
    rows = data.get("rows") or []
    pages: dict[str, Any] = {}
    top: list[dict[str, Any]] = []
    for row in rows:
        dims = row.get("dimensionValues") or []
        mets = row.get("metricValues") or []
        if not dims:
            continue
        path = norm_path(dims[0].get("value") or "/")
        try:
            views = int((mets[0] or {}).get("value") or 0)
        except Exception:
            views = 0
        try:
            users = int((mets[1] or {}).get("value") or 0)
        except Exception:
            users = 0
        if views <= 0:
            continue
        item = {"views": views, "active_users": users}
        pages[path] = item
        top.append({"path": path, **item})
    top.sort(key=lambda x: x.get("views", 0), reverse=True)
    return pages, top[:20]


def collect(lookback_days: int) -> dict[str, Any]:
    cfg = load_config()
    property_id = str(cfg.get("ga4_property_id") or cfg.get("property_id") or "").strip()
    credentials_path = str(cfg.get("google_application_credentials") or cfg.get("credentials_path") or "").strip()
    lookback_days = int(cfg.get("lookback_days") or lookback_days)
    measurement_ready = bool(str(cfg.get("measurement_id") or os.environ.get("GA_MEASUREMENT_ID") or "").strip())
    base = {
        "updated_at": now(),
        "source": "ga4",
        "lookback_days": lookback_days,
        "pages": existing_pages(),
        "top_pages": [],
        "measurement_configured": measurement_ready,
        "property_configured": bool(property_id),
    }
    if not property_id:
        base["status"] = "not_configured"
        base["next_action"] = "connect_google_analytics"
        return base

    token = service_account_token(credentials_path) or gcloud_access_token()
    if not token:
        base["status"] = "api_credentials_missing"
        base["next_action"] = "grant_ga4_read_access"
        return base

    try:
        pages, top = run_ga4_rest(property_id, token, lookback_days)
    except Exception as exc:
        base["status"] = "fetch_failed"
        base["error"] = f"{type(exc).__name__}: {exc}"
        return base
    base.update({"status": "ok", "pages": pages, "top_pages": top})
    return base


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lookback-days", type=int, default=30)
    args = ap.parse_args()
    payload = collect(args.lookback_days)
    write_payload(payload)
    print(json.dumps({k: payload.get(k) for k in ["status", "updated_at", "lookback_days", "measurement_configured", "property_configured", "next_action"] if k in payload}, ensure_ascii=False))
    return 0 if payload.get("status") in {"ok", "not_configured", "api_credentials_missing"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
