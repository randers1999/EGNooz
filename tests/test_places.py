from pathlib import Path

from egnooz.places import load_place_filter

PLACES = Path(__file__).resolve().parent.parent / "places.yaml"


def test_sale_not_wholesale():
    places = load_place_filter(PLACES)
    assert places.in_scope("Flooding in Sale overnight")
    assert not places.in_scope("Wholesale vegetable prices rise")
    assert not places.in_scope("End of financial year sales")


def test_east_gippsland_not_unqualified():
    places = load_place_filter(PLACES)
    assert places.in_scope("East Gippsland Shire adopts budget")
    assert not places.in_scope("Gippsland in mourning after statewide loss")
    assert not places.in_scope("West and South Gippsland thunderstorm asthma")


def test_maffra_and_neighbours():
    places = load_place_filter(PLACES)
    assert places.in_scope("Maffra rec reserve lights")
    assert places.in_scope("15Km N Of Bairnsdale")
    assert not places.in_scope("Kurt St, Morwell")
    assert not places.in_scope("Fire on South Gippsland Hwy, Koo Wee Rup")
    assert places.excluded_only("Traralgon hospital waiting times")


def test_lakes_and_rivers():
    places = load_place_filter(PLACES)
    assert places.in_scope("Algae on the Gippsland Lakes near Metung")
    assert places.in_scope("Works on the Tambo River at Swan Reach")
    assert "Mallacoota" in places.matched_places("Mallacoota inlet closed to vessels")
