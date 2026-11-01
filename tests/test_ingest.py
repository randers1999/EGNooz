from __future__ import annotations

from datetime import datetime
from pathlib import Path

from egnooz.edition import NewsItem
from egnooz.ingest import _merge_items, run_ingest
from egnooz.store import EditionStore
from egnooz.timeutil import MELBOURNE

FIXED_NOW = datetime(2026, 10, 31, 8, 0, tzinfo=MELBOURNE)

RSS = Path(__file__).resolve().parent / "fixtures" / "sample.rss.xml"
VIC = Path(__file__).resolve().parent / "fixtures" / "vicemergency.json"


def test_merge_preserves_unchecked_and_manual():
    existing = [
        NewsItem(
            id="fixture-local-aaaa",
            title="Bairnsdale market returns",
            url="https://example.test/local/bairnsdale-market",
            source_id="fixture-local",
            source_name="Fixture",
            published_at=None,
            snippet="",
            match_reason="local-source",
            included=False,
        ),
        NewsItem(
            id="manual-bbbb",
            title="ABC story Tom added",
            url="https://www.abc.net.au/news/eg-example",
            source_id="abc-gippsland",
            source_name="ABC Gippsland",
            published_at=None,
            snippet="",
            match_reason="manual",
            included=True,
        ),
    ]
    incoming = [
        NewsItem(
            id="fixture-local-aaaa",
            title="Bairnsdale market returns",
            url="https://example.test/local/bairnsdale-market",
            source_id="fixture-local",
            source_name="Fixture",
            published_at=None,
            snippet="new snippet",
            match_reason="local-source",
            included=True,
        )
    ]
    merged = _merge_items(existing, incoming)
    by_url = {item.url: item for item in merged}
    assert by_url["https://example.test/local/bairnsdale-market"].included is False
    assert any(item.match_reason == "manual" for item in merged)


def test_ingest_writes_draft_not_published(settings, monkeypatch):
    def fake_fetch(url, **kwargs):
        if "events-geojson" in url:
            return 200, VIC.read_bytes(), "application/json"
        return 200, RSS.read_bytes(), "application/rss+xml"

    monkeypatch.setattr("egnooz.feeds.fetch_bytes", fake_fetch)
    monkeypatch.setattr("egnooz.vicemergency.fetch_bytes", fake_fetch)
    monkeypatch.setattr("egnooz.feeds.now_melbourne", lambda: FIXED_NOW)
    monkeypatch.setattr("egnooz.ingest.now_melbourne", lambda: FIXED_NOW)
    monkeypatch.setattr("egnooz.timeutil.now_melbourne", lambda: FIXED_NOW)

    edition = run_ingest(
        settings,
        edition_date="2026-10-31",
        send_email=False,
        polite_delay=0,
    )
    store = EditionStore(settings)
    assert store.draft_path("2026-10-31").is_file()
    assert not store.is_published("2026-10-31")
    assert edition.status == "draft"
    assert store.load_latest() is None
    local = [item for item in edition.items if item.match_reason == "local-source"]
    mention = [item for item in edition.items if item.match_reason == "mention"]
    assert local
    assert all(item.included for item in local)
    assert all(not item.included for item in mention)
