from pathlib import Path

from egnooz.sources import load_sources

ROOT = Path(__file__).resolve().parent.parent


def test_sources_yaml_loads_and_abc_is_manual():
    listing = load_sources(ROOT / "sources.yaml")
    ids = [source.id for source in listing.sources]
    assert "bairnsdale-advertiser" in ids
    assert "abc-gippsland" in ids
    abc = listing.by_id("abc-gippsland")
    assert abc is not None
    assert abc.ingest == "manual"
    assert abc.enabled
    guardian = listing.by_id("guardian-au")
    assert guardian is not None
    assert guardian.match == "mention"
    assert listing.by_id("newsapi-au").enabled is False
