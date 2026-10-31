from pathlib import Path

from egnooz.places import load_place_filter
from egnooz.vicemergency import parse_events

PLACES = Path(__file__).resolve().parent.parent / "places.yaml"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "vicemergency.json"


def test_filters_to_east_gippsland_and_sale():
    places = load_place_filter(PLACES)
    warnings = parse_events(FIXTURE.read_bytes(), places, fetched_at="2026-10-31T05:00:00+11:00")
    ids = {item["id"] for item in warnings["items"]}
    advice = next(item for item in warnings["items"] if item["id"] == "vicemergency-eg-1")
    assert "East Gippsland" in advice["title"]
    assert "vicemergency-eg-1" in ids
    assert "vicemergency-sale-1" in ids
    assert "vicemergency-morwell-1" not in ids
    assert "vicemergency-wsg-1" not in ids
    assert warnings["districtFireDanger"] == "MODERATE"
    assert "State of Victoria" in warnings["attribution"]
    assert "not an emergency service" in warnings["disclaimer"]
    assert warnings["license"] == "CC BY 3.0 AU"
