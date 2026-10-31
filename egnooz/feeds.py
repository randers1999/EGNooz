from __future__ import annotations

import logging
from datetime import timedelta

import feedparser

from egnooz.edition import NewsItem
from egnooz.http import FetchError, fetch_bytes
from egnooz.places import PlaceFilter
from egnooz.snippet import make_snippet
from egnooz.sources import Source
from egnooz.timeutil import isoformat, now_melbourne, parse_datetime
from egnooz.urls import canonical_url, item_id

log = logging.getLogger("egnooz.feeds")


def _entry_link(entry: object) -> str:
    link = getattr(entry, "link", None) or ""
    if link:
        return canonical_url(str(link))
    links = getattr(entry, "links", None) or []
    for candidate in links:
        href = candidate.get("href") if isinstance(candidate, dict) else None
        if href:
            return canonical_url(str(href))
    return ""


def _entry_summary(entry: object) -> str:
    summary = getattr(entry, "summary", None) or getattr(entry, "description", None) or ""
    return make_snippet(str(summary))


def _entry_published(entry: object) -> str | None:
    for attr in ("published", "updated", "created"):
        value = getattr(entry, attr, None)
        parsed = parse_datetime(value)
        if parsed is not None:
            return isoformat(parsed)
    parsed_struct = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if parsed_struct:
        try:
            import time as time_mod
            from datetime import datetime, timezone

            ts = time_mod.mktime(parsed_struct)
            return isoformat(datetime.fromtimestamp(ts, tz=timezone.utc))
        except (OverflowError, ValueError, OSError):
            return None
    return None


def parse_feed_bytes(payload: bytes, source: Source, places: PlaceFilter) -> list[NewsItem]:
    parsed = feedparser.parse(payload)
    items: list[NewsItem] = []
    cutoff = now_melbourne() - timedelta(hours=source.lookback_hours)
    for entry in parsed.entries:
        url = _entry_link(entry)
        if not url:
            continue
        title = make_snippet(str(getattr(entry, "title", "") or ""), limit=180)
        if not title:
            continue
        snippet = _entry_summary(entry)
        published_at = _entry_published(entry)
        published_dt = parse_datetime(published_at)
        if published_dt is not None and published_dt < cutoff:
            continue
        matched = places.matched_places(title, snippet, url)
        if source.match == "mention" and not matched:
            continue
        match_reason = "local-source" if source.match == "local" else "mention"
        included = source.default_included
        items.append(
            NewsItem(
                id=item_id(source.id, url),
                title=title,
                url=url,
                source_id=source.id,
                source_name=source.name,
                published_at=published_at,
                snippet=snippet,
                match_reason=match_reason,
                matched_places=matched,
                included=included,
            )
        )
    return items


def fetch_source_items(
    source: Source,
    places: PlaceFilter,
    user_agent: str,
) -> list[NewsItem]:
    if not source.feed_url:
        return []
    _status, payload, _content_type = fetch_bytes(
        source.feed_url,
        user_agent=user_agent,
        accept="application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
    )
    items = parse_feed_bytes(payload, source, places)
    log.info("%s: %s items after filter", source.id, len(items))
    return items
