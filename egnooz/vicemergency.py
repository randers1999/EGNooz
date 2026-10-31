from __future__ import annotations

import json
import logging
from typing import Any

from egnooz.edition import WarningItem, empty_warnings
from egnooz.http import fetch_bytes
from egnooz.places import PlaceFilter
from egnooz.snippet import make_snippet, strip_html
from egnooz.timeutil import isoformat, now_melbourne, parse_datetime

log = logging.getLogger("egnooz.vicemergency")

VICEMERGENCY_URL = "https://emergency.vic.gov.au/public/events-geojson.json"
VICEMERGENCY_PAGE = "https://www.emergency.vic.gov.au/respond/"
NOTICE_URL = (
    "https://www.emv.vic.gov.au/responsibilities/victorias-warning-system/emergency-data"
)


def _flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        return " ".join(_flatten_text(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_flatten_text(v) for v in value)
    return ""


def _feature_blob(props: dict[str, Any]) -> str:
    parts = [
        props.get("location"),
        props.get("sourceTitle"),
        props.get("webHeadline"),
        props.get("name"),
        props.get("category1"),
        props.get("category2"),
        (props.get("text") or "")[:500],
    ]
    return " ".join(strip_html(str(p)) for p in parts if p)


def in_scope_feature(props: dict[str, Any], places: PlaceFilter) -> tuple[bool, list[str]]:
    if str(props.get("statewide") or "").upper() == "Y":
        matched = places.matched_places(_feature_blob(props))
        return True, matched or ["East Gippsland"]
    blob = _feature_blob(props)
    matched = places.matched_places(blob)
    return bool(matched), matched


def _title(props: dict[str, Any]) -> str:
    web = props.get("webHeadline")
    if web:
        first_line = str(web).strip().split("\n")[0].strip()
        if first_line:
            return make_snippet(first_line, limit=160)
    cap = props.get("cap") if isinstance(props.get("cap"), dict) else {}
    event = cap.get("event") if cap else None
    bits = [
        props.get("sourceTitle") or props.get("category1") or props.get("name"),
        event or props.get("category2"),
        props.get("location"),
    ]
    label = " — ".join(str(bit).strip() for bit in bits if bit)
    return make_snippet(label or "VicEmergency incident", limit=160)


def warning_from_feature(feature: dict[str, Any], places: PlaceFilter) -> WarningItem | None:
    props = feature.get("properties") or {}
    ok, matched = in_scope_feature(props, places)
    if not ok:
        return None
    ident = str(props.get("id") or props.get("sourceId") or props.get("eventId") or "")
    if not ident:
        return None
    url = props.get("url") or VICEMERGENCY_PAGE
    updated = parse_datetime(props.get("updated") or props.get("created"))
    category_bits = [props.get("category1"), props.get("category2")]
    category = " — ".join(str(bit) for bit in category_bits if bit)
    return WarningItem(
        id=f"vicemergency-{ident}",
        title=_title(props),
        url=str(url),
        location=str(props.get("location") or ""),
        category=category,
        status=str(props.get("status") or ""),
        updated_at=isoformat(updated) if updated else None,
        feed_type=str(props.get("feedType") or "incident"),
        matched_places=matched,
    )


def parse_events(payload: bytes | dict, places: PlaceFilter, fetched_at: str | None = None) -> dict[str, Any]:
    data = json.loads(payload) if isinstance(payload, (bytes, bytearray, str)) else payload
    collection = data.get("properties") or {}
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for feature in data.get("features") or []:
        warning = warning_from_feature(feature, places)
        if warning is None or warning.id in seen:
            continue
        seen.add(warning.id)
        items.append(warning.to_dict())
    fdr = None
    tfb = None
    conditions = (collection.get("conditions") or {})
    fdr_map = conditions.get("fdr") or {}
    tfb_map = conditions.get("tfb") or {}
    if isinstance(fdr_map, dict):
        fdr = fdr_map.get("East Gippsland")
    if isinstance(tfb_map, dict):
        tfb = tfb_map.get("East Gippsland")
    last_updated = collection.get("lastUpdated")
    parsed_updated = parse_datetime(last_updated)
    warnings = empty_warnings()
    warnings.update(
        {
            "attributionUrl": NOTICE_URL,
            "feedLastUpdated": isoformat(parsed_updated) if parsed_updated else last_updated,
            "fetchedAt": fetched_at or isoformat(now_melbourne()),
            "districtFireDanger": fdr,
            "districtTotalFireBan": tfb,
            "items": items,
        }
    )
    return warnings


def fetch_warnings(places: PlaceFilter, user_agent: str) -> dict[str, Any]:
    _status, payload, _content_type = fetch_bytes(
        VICEMERGENCY_URL,
        user_agent=user_agent,
        accept="application/json",
        max_bytes=8_000_000,
        timeout=25.0,
    )
    warnings = parse_events(payload, places)
    log.info("VicEmergency: %s in-scope items", len(warnings.get("items") or []))
    return warnings
