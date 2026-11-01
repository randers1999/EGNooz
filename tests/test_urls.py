from egnooz.urls import canonical_url, item_id


def test_canonical_drops_utm_and_slash():
    assert canonical_url("https://BairnsdaleAdvertiser.com.au/story/?utm_source=x&fbclid=1") == (
        "https://bairnsdaleadvertiser.com.au/story"
    )


def test_item_id_stable():
    first = item_id("brhs", "https://brhs.com.au/news/hello/")
    second = item_id("brhs", "https://brhs.com.au/news/hello")
    assert first == second
    assert first.startswith("brhs-")
