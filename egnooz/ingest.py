from __future__ import annotations

import logging
import time
from datetime import date, datetime

from egnooz.config import Settings
from egnooz.edition import Edition, IngestLogEntry, NewsItem, empty_warnings
from egnooz.feeds import fetch_source_items
from egnooz.http import FetchError
from egnooz.places import load_place_filter
from egnooz.sources import load_sources
from egnooz.store import EditionStore
from egnooz.timeutil import isoformat, now_melbourne, today_melbourne
from egnooz.urls import canonical_url
from egnooz.vicemergency import fetch_warnings

log = logging.getLogger("egnooz.ingest")


def _merge_items(existing: list[NewsItem], incoming: list[NewsItem]) -> list[NewsItem]:
    by_url: dict[str, NewsItem] = {}
    by_id: dict[str, NewsItem] = {}
    for item in existing:
        by_id[item.id] = item
        by_url[canonical_url(item.url)] = item

    merged: list[NewsItem] = []
    seen_urls: set[str] = set()
    for item in incoming:
        url = canonical_url(item.url)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        previous = by_id.get(item.id) or by_url.get(url)
        if previous is not None:
            item.included = previous.included
        merged.append(item)

    for item in existing:
        if item.match_reason != "manual":
            continue
        url = canonical_url(item.url)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        merged.append(item)
    return merged


def _sort_items(items: list[NewsItem]) -> list[NewsItem]:
    rank = {"manual": 0, "local-source": 1, "mention": 2}

    def key(item: NewsItem) -> tuple:
        stamp = 0.0
        if item.published_at:
            try:
                stamp = datetime.fromisoformat(item.published_at).timestamp()
            except ValueError:
                stamp = 0.0
        return (
            rank.get(item.match_reason, 9),
            0 if item.published_at else 1,
            -stamp,
            item.source_name.lower(),
            item.title.lower(),
        )

    return sorted(items, key=key)


def run_ingest(
    settings: Settings,
    *,
    edition_date: date | str | None = None,
    send_email: bool = True,
    polite_delay: float = 0.4,
) -> Edition:
    settings.ensure_dirs()
    store = EditionStore(settings)
    if isinstance(edition_date, str):
        day = edition_date
    elif edition_date is None:
        day = today_melbourne().isoformat()
    else:
        day = edition_date.isoformat()

    sources = load_sources(settings.sources_path)
    places = load_place_filter(settings.places_path)
    previous = store.load_draft(day)
    editor_note = previous.editor_note if previous else ""
    previous_items = previous.items if previous else []

    incoming: list[NewsItem] = []
    log_entries: list[IngestLogEntry] = []
    warnings = empty_warnings()

    for source in sources.sources:
        if not source.enabled:
            log_entries.append(
                IngestLogEntry(
                    source_id=source.id,
                    status="disabled",
                    detail=source.notes or None,
                )
            )
            continue
        if source.ingest == "manual":
            log_entries.append(
                IngestLogEntry(
                    source_id=source.id,
                    status="manual",
                    detail="No automatic fetch. Add URLs on the review page.",
                )
            )
            continue
        if source.ingest == "none" or not source.feed_url:
            log_entries.append(
                IngestLogEntry(
                    source_id=source.id,
                    status="skipped",
                    detail=source.notes or "No public feed. Not scraping HTML.",
                )
            )
            continue
        try:
            if source.ingest == "json" and source.id == "vicemergency":
                warnings = fetch_warnings(places, sources.user_agent)
                log_entries.append(
                    IngestLogEntry(
                        source_id=source.id,
                        status="ok",
                        item_count=len(warnings.get("items") or []),
                    )
                )
            elif source.ingest == "rss":
                items = fetch_source_items(source, places, sources.user_agent)
                incoming.extend(items)
                log_entries.append(
                    IngestLogEntry(
                        source_id=source.id,
                        status="ok",
                        item_count=len(items),
                    )
                )
            else:
                log_entries.append(
                    IngestLogEntry(
                        source_id=source.id,
                        status="skipped",
                        detail=f"Unhandled ingest type {source.ingest}",
                    )
                )
        except FetchError as exc:
            log.warning("Ingest failed for %s: %s", source.id, exc)
            log_entries.append(
                IngestLogEntry(
                    source_id=source.id,
                    status="error",
                    error=str(exc),
                )
            )
        except Exception as exc:  # noqa: BLE001 — isolate one source from the rest
            log.exception("Ingest crashed for %s", source.id)
            log_entries.append(
                IngestLogEntry(
                    source_id=source.id,
                    status="error",
                    error=str(exc),
                )
            )
        if polite_delay:
            time.sleep(polite_delay)

    items = _sort_items(_merge_items(previous_items, incoming))
    edition = Edition(
        edition_date=day,
        status="draft",
        generated_at=isoformat(now_melbourne()),
        published_at=previous.published_at if previous else None,
        editor_note=editor_note,
        warnings=warnings,
        items=items,
        ingest_log=log_entries,
    )
    store.save_draft(edition)

    if send_email and settings.send_draft_ready_email:
        from egnooz.emailer import send_draft_ready

        send_draft_ready(settings, edition)
    return edition
