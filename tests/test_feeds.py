from datetime import datetime
from pathlib import Path

from egnooz.feeds import parse_feed_bytes
from egnooz.places import load_place_filter
from egnooz.sources import Source
from egnooz.timeutil import MELBOURNE

FIXED_NOW = datetime(2026, 10, 31, 8, 0, tzinfo=MELBOURNE)

PLACES = Path(__file__).resolve().parent.parent / "places.yaml"
RSS = Path(__file__).resolve().parent / "fixtures" / "sample.rss.xml"


def test_local_source_keeps_all_recent_items(monkeypatch):
    monkeypatch.setattr("egnooz.feeds.now_melbourne", lambda: FIXED_NOW)
    places = load_place_filter(PLACES)
    source = Source(
        id="fixture-local",
        name="Fixture Advertiser",
        home="https://example.test",
        match="local",
        ingest="rss",
        enabled=True,
        lookback_hours=192,
    )
    items = parse_feed_bytes(RSS.read_bytes(), source, places)
    titles = {item.title for item in items}
    assert "Bairnsdale market returns" in titles
    assert "Morwell factory expansion" in titles
    assert all(item.included for item in items)
    assert all(item.match_reason == "local-source" for item in items)
    market = next(item for item in items if "Bairnsdale" in item.title)
    assert "Bairnsdale" in market.matched_places
    assert "<p>" not in market.snippet


def test_mention_source_requires_place(monkeypatch):
    monkeypatch.setattr("egnooz.feeds.now_melbourne", lambda: FIXED_NOW)
    places = load_place_filter(PLACES)
    source = Source(
        id="fixture-mention",
        name="Fixture Guardian",
        home="https://example.test",
        match="mention",
        ingest="rss",
        enabled=True,
        lookback_hours=192,
    )
    items = parse_feed_bytes(RSS.read_bytes(), source, places)
    titles = {item.title for item in items}
    assert titles == {"Bairnsdale market returns"}
    assert items[0].included is False
    assert items[0].match_reason == "mention"
